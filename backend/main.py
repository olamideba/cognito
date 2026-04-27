import asyncio
import json
import os
import base64
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google.genai import types

from routers import session as session_router
from routers import memory as memory_router
from routers import generate as generate_router
from routers import live as live_router

from core.session import register, deregister
from core.db import (
    create_session,
    get_session,
    resume_session,
    get_memory, # noqa: F401, F841
)  
from core.live_defaults import (
    get_default_response_modalities,
    resolve_voice_name,
)
from tools.handlers import set_live_context
from flow import handle_flow_signal

from services.live_events import serialize_event, build_reconnect_message
from scripts.adk_patch import patch_adk_trace_tool_call
from agent import agent
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions import InMemorySessionService
from google.adk.agents.live_request_queue import LiveRequestQueue

patch_adk_trace_tool_call()



logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

session_service = InMemorySessionService()
runner = Runner(app_name="cognito", agent=agent, session_service=session_service)

load_dotenv()

app = FastAPI(title="Cognito Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


app.include_router(session_router.router)
app.include_router(memory_router.router)
app.include_router(generate_router.router)
app.include_router(live_router.router)


@app.get("/")
def root() -> Dict[str, str]:
    return {"name": "cognito-backend", "version": app.version}


@app.websocket("/ws")
async def websocket_proxy(
    ws: WebSocket, session_id: Optional[str] = None, browser_token: Optional[str] = None, voice_name: Optional[str] = None
):
    """
    WebSocket proxy: React frontend <-> proxy server <-> Google Gemini Live API.
    """
    await ws.accept()
    print("[proxy] Client Connected")

    active_session_id = None
    memory: Optional[Dict[str, Any]] = None  # noqa: F841
    is_reconnect = False
    if session_id:
        existing = await get_session(session_id)
        if existing:
            if existing.get("status") == "completed":
                active_session_id = await resume_session(session_id)
            else:
                active_session_id = session_id
            is_reconnect = True
        else:
            active_session_id = await create_session()
    else:
        active_session_id = await create_session()

    register(ws, active_session_id)
    await ws.send_json(
        {
            "type": "session_created",
            "payload": {"session_id": active_session_id},
        }
    )

    # if browser_token:
    # memory = await get_memory(browser_token)

    # api_key = os.getenv("GEMINI_API_KEY")
    # if not api_key:
    #     await ws.close(code=1008, reason="GEMINI_API_KEY not configured")
    #     print("[proxy] ERROR: GEMINI_API_KEY not set, closing client")
    #     return

    try:
        resolved_voice_name = resolve_voice_name(voice_name)
        run_config = RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=get_default_response_modalities(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=resolved_voice_name
                    )
                )
            ),
        )

        existing_adk_session = await session_service.get_session(
            app_name="cognito",
            user_id=active_session_id,
            session_id=active_session_id,
        )
        if not existing_adk_session:
            await session_service.create_session(
                app_name="cognito",
                user_id=active_session_id,
                session_id=active_session_id,
            )

        live_request_queue = LiveRequestQueue()

        session_snapshot = await get_session(active_session_id)

        async def upstream_task():
            """Client WebSocket → LiveRequestQueue"""
            try:
                while True:
                    raw_msg = await ws.receive_text()
                    data = json.loads(raw_msg)

                    if data.get("type") == "flow_signal":
                        asyncio.create_task(
                            handle_flow_signal(data, active_session_id, ws)
                        )
                        continue

                    if "realtimeInput" in data:
                        media_chunks = data["realtimeInput"].get("mediaChunks", [])
                        for chunk in media_chunks:
                            b_data = base64.b64decode(chunk["data"])
                            live_request_queue.send_realtime(
                                types.Blob(data=b_data, mime_type=chunk["mimeType"])
                            )
                    elif "clientContent" in data:
                        turns = data["clientContent"].get("turns", [])
                        for turn in turns:
                            role = turn.get("role", "user")
                            parts_data = turn.get("parts", [])
                            adk_parts = []
                            for p in parts_data:
                                if "text" in p:
                                    adk_parts.append(types.Part(text=p["text"]))
                            if adk_parts:
                                live_request_queue.send_content(
                                    types.Content(role=role, parts=adk_parts)
                                )

            except WebSocketDisconnect:
                print("[proxy] Client disconnected")
            except Exception as e:
                print(f"[proxy] upstream_task error: {e}")

        async def downstream_task():
            """runner.run_live() events → Client WebSocket"""
            try:
                set_live_context(active_session_id, ws)
                await ws.send_json({"setupComplete": {}})

                if is_reconnect and session_snapshot:
                    content = build_reconnect_message(session_snapshot)
                    if content is not None:
                        live_request_queue.send_content(content)

                async for event in runner.run_live(
                    user_id=active_session_id,
                    session_id=active_session_id,
                    run_config=run_config,
                    live_request_queue=live_request_queue,
                ):
                    event_json_str = serialize_event(event)
                    if event_json_str:
                        await ws.send_text(event_json_str)

            except Exception as e:
                import traceback
                print(f"[proxy] downstream_task error: {e}")
                traceback.print_exc()

        await asyncio.gather(upstream_task(), downstream_task())

    except Exception as e:
        print(f"[proxy] Unexpected error: {e}")
        try:
            await ws.close(code=1011, reason=str(e)[:120])
        except Exception:
            pass
    finally:
        deregister(ws)
        if active_session_id:
            try:
                await session_service.delete_session(
                    app_name="cognito",
                    user_id=active_session_id,
                    session_id=active_session_id,
                )
            except Exception:
                pass
        print("[proxy] Session ended")
