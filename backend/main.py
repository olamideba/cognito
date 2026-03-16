import asyncio
import inspect
import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pathlib import Path

from routers import session as session_router
from routers import memory as memory_router
from core.session import register, deregister
from core.db import create_session, get_session, resume_session, get_memory
from tools.registry import TOOL_DECLARATIONS
from tools.handlers import set_live_context

from agent import agent
from google.adk import telemetry as adk_telemetry
from google.adk.flows.llm_flows import functions as adk_functions
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions import InMemorySessionService
from google.adk.agents.live_request_queue import LiveRequestQueue

def _patch_adk_trace_tool_call() -> None:
    signature = inspect.signature(adk_telemetry.trace_tool_call)
    if "response_event_id" in signature.parameters:
        return

    original = adk_telemetry.trace_tool_call

    def trace_tool_call_compat(
        *,
        tool=None,
        args=None,
        function_response_event=None,
        **kwargs,
    ):
        if function_response_event is not None:
            return original(
                tool=tool,
                args=args or {},
                function_response_event=function_response_event,
            )
        # Newer ADK call signature; telemetry only, safe to skip.
        return None

    adk_telemetry.trace_tool_call = trace_tool_call_compat
    adk_functions.trace_tool_call = trace_tool_call_compat


_patch_adk_trace_tool_call()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

session_service = InMemorySessionService()
runner = Runner(app_name="cognito", agent=agent, session_service=session_service)

load_dotenv()

class LiveToolConfig(BaseModel):
    type: str
    googleSearch: Optional[Dict[str, Any]] = None
    functionDeclarations: Optional[List[Dict[str, Any]]] = None


class LiveConfigResponse(BaseModel):
    model: str
    systemInstruction: str
    tools: List[LiveToolConfig]
    responseModalities: List[str]
    voiceName: str


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


@app.get("/")
def root() -> Dict[str, str]:
    return {"name": "cognito-backend", "version": app.version}


@app.post("/api/live/config", response_model=LiveConfigResponse)
def get_live_config() -> LiveConfigResponse:
    model = os.getenv(
        "COGNITO_MODEL",
        "gemini-2.5-flash-native-audio-preview-12-2025",
    )

    system_instruction = Path("SYSTEM_PROMPT.md").read_text()

    tools: List[LiveToolConfig] = [
        LiveToolConfig(type="googleSearch", googleSearch={}),
        LiveToolConfig(
            type="functionDeclarations",
            functionDeclarations=TOOL_DECLARATIONS,
        ),
    ]

    return LiveConfigResponse(
        model=model,
        systemInstruction=system_instruction,
        tools=tools,
        responseModalities=["AUDIO"],
        voiceName=os.getenv("COGNITO_VOICE_NAME", "Aoede"),
    )



import base64

def serialize_event(event) -> Optional[str]:
    if getattr(event, "interrupted", False):
        return json.dumps({"serverContent": {"interrupted": True}})
    
    if getattr(event, "turn_complete", False):
        return json.dumps({"serverContent": {"turnComplete": True}})
    
    if hasattr(event, "actions") and getattr(event, "actions", None) and getattr(event.actions, "function_calls", None):
        function_calls = []
        for call in event.actions.function_calls:
            function_calls.append({
                "id": getattr(call, "id", None),
                "name": call.name,
                "args": getattr(call, "args", {}),
            })
        if function_calls:
            return json.dumps({"toolCall": {"functionCalls": function_calls}})
    
    if getattr(event, "content", None) and getattr(event.content, "parts", None):
        parts = []
        for part in event.content.parts:
            if getattr(part, "inline_data", None):
                b64_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                parts.append({
                    "inlineData": {
                        "mimeType": part.inline_data.mime_type,
                        "data": b64_data
                    }
                })
            elif getattr(part, "text", None):
                parts.append({"text": part.text})
        if parts:
            return json.dumps({
                "serverContent": {
                    "modelTurn": {
                        "parts": parts
                    }
                }
            })
            
    return None


@app.websocket("/ws")
async def websocket_proxy(ws: WebSocket, 
session_id: Optional[str] = None, browser_token: Optional[str] = None
):
    """
    WebSocket proxy: React frontend <-> proxy server <-> Google Gemini Live API.
    """
    await ws.accept()
    print("[proxy] Client Connected")

    active_session_id = None
    memory: Optional[Dict[str, Any]] = None
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
    await ws.send_json({"type": "session_created", "session_id": active_session_id})

    if browser_token:
        memory = await get_memory(browser_token)

    # api_key = os.getenv("GEMINI_API_KEY")
    # if not api_key:
    #     await ws.close(code=1008, reason="GEMINI_API_KEY not configured")
    #     print("[proxy] ERROR: GEMINI_API_KEY not set, closing client")
    #     return


    try:
        run_config = RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=[types.Modality.AUDIO],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=os.getenv("COGNITO_VOICE_NAME", "Aoede")
                    )
                )
            )
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
        if is_reconnect and session_snapshot:
            goal = session_snapshot.get("goal")
            time_limit_seconds = session_snapshot.get("time_limit_seconds")
            start_time = session_snapshot.get("start_time")
            remaining_minutes = None
            if time_limit_seconds and start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                    elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
                    remaining_seconds = max(0, time_limit_seconds - elapsed)
                    remaining_minutes = max(0, int(remaining_seconds // 60))
                except Exception:
                    remaining_minutes = None
            if goal or time_limit_seconds or remaining_minutes is not None:
                parts = []
                if goal:
                    parts.append(f"Goal: {goal}.")
                if remaining_minutes is not None:
                    parts.append(f"Remaining time: {remaining_minutes} minutes.")
                elif time_limit_seconds:
                    minutes = int(time_limit_seconds) // 60
                    parts.append(f"Time limit: {minutes} minutes.")
                parts.append("Continue without re-asking for any already-known fields.")
                live_request_queue.send_content(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=" ".join(parts))],
                    )
                )

        async def upstream_task():
            """Client WebSocket → LiveRequestQueue"""
            try:
                while True:
                    raw_msg = await ws.receive_text()
                    data = json.loads(raw_msg)
                    
                    if data.get("type") == "flow_signal":
                        # Handled client side later
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
                                live_request_queue.send_content(types.Content(role=role, parts=adk_parts))

            except WebSocketDisconnect:
                print("[proxy] Client disconnected")
            except Exception as e:
                print(f"[proxy] upstream_task error: {e}")

        async def downstream_task():
            """runner.run_live() events → Client WebSocket"""
            try:
                set_live_context(active_session_id, ws)
                await ws.send_json({"setupComplete": {}})
                
                async for event in runner.run_live(
                    user_id=active_session_id,session_id=active_session_id,
                    run_config=run_config,
                    live_request_queue=live_request_queue
                ):
                    event_json_str = serialize_event(event)
                    if event_json_str:
                        await ws.send_text(event_json_str)

            except Exception as e:
                print(f"[proxy] downstream_task error: {e}")

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
        
