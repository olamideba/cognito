import asyncio
import json
import os
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
from interceptor import intercept
from tools.registry import TOOL_DECLARATIONS

from agent import agent
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions import InMemorySessionService
from google.adk.agents.live_request_queue import LiveRequestQueue

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
    if session_id:
        existing = await get_session(session_id)
        if existing:
            if existing.get("status") == "completed":
                active_session_id = await resume_session(session_id)
            else:
                active_session_id = session_id
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
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=os.getenv("COGNITO_VOICE_NAME", "Aoede")
                    )
                )
            )
        )

        await session_service.create_session(
            app_name="cognito",
            user_id=active_session_id,
            session_id=active_session_id
        )

        live_request_queue = LiveRequestQueue()

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
                await ws.send_json({"setupComplete": {}})
                
                async for event in runner.run_live(
                    user_id=active_session_id,session_id=active_session_id,
                    run_config=run_config,
                    live_request_queue=live_request_queue
                ):
                    event_json_str = serialize_event(event)
                    if event_json_str:
                        async def send_to_upstream(response_str: str):
                            response_data = json.loads(response_str)
                            if "toolResponse" in response_data:
                                function_responses = response_data["toolResponse"].get("functionResponses", [])
                                adk_parts = []
                                for resp in function_responses:
                                    adk_parts.append(types.Part(
                                        function_response=types.FunctionResponse(
                                            name=resp.get("name"),
                                            id=resp.get("id"),
                                            response=resp.get("response")
                                        )
                                    ))
                                if adk_parts:
                                    live_request_queue.send_content(types.Content(parts=adk_parts))

                        was_intercepted = await intercept(event_json_str, send_to_upstream, ws, active_session_id)
                        if not was_intercepted:
                            # Send unmodified to frontend
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
        print("[proxy] Session ended")
        