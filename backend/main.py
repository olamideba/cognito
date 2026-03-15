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
from pathlib import Path

from routers import session as session_router
from routers import memory as memory_router
from core.session import register, deregister
from core.db import create_session, get_session, resume_session

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
        "models/gemini-2.5-flash-native-audio-preview-12-2025",
    )

    system_instruction = Path("SYSTEM_PROMPT.md").read_text()

    tools: List[LiveToolConfig] = [
        LiveToolConfig(type="googleSearch", googleSearch={}),
        LiveToolConfig(
            type="functionDeclarations",
            functionDeclarations=[
                {
                    "name": "render_altair",
                    "description": (
                        "Displays an Altair graph in JSON format in the Cognito console."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "json_graph": {
                                "type": "string",
                                "description": (
                                    "JSON STRING representation of the graph to render. "
                                    "Must be a string, not a JSON object."
                                ),
                            }
                        },
                        "required": ["json_graph"],
                    },
                }
            ],
        ),
    ]

    return LiveConfigResponse(
        model=model,
        systemInstruction=system_instruction,
        tools=tools,
        responseModalities=["AUDIO"],
        voiceName=os.getenv("COGNITO_VOICE_NAME", "Aoede"),
    )



GEMINI_WS_URL = (
    "wss://generativelanguage.googleapis.com/ws/"
    "google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"
)


def _build_setup_message() -> dict:
    """Build the initial setup JSON frame from the live config."""
    cfg = get_live_config()

    def serialize_tools(tools: List[LiveToolConfig]) -> List[Dict[str, Any]]:
        serialized: List[Dict[str, Any]] = []
        for tool in tools:
            if tool.type == "googleSearch":
                serialized.append({"googleSearch": tool.googleSearch or {}})
            elif tool.type == "functionDeclarations":
                serialized.append(
                    {"functionDeclarations": tool.functionDeclarations or []}
                )
            else:
                raise ValueError(f"Unsupported tool type: {tool.type}")
        return serialized

    return {
        "setup": {
            "model": cfg.model,
            "generationConfig": {
                "responseModalities": [m.upper() for m in cfg.responseModalities],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": cfg.voiceName}
                    }
                },
            },
            "systemInstruction": {
                "parts": [{"text": cfg.systemInstruction}]
            },
            "tools": serialize_tools(cfg.tools),
        }
    }


@app.websocket("/ws")
async def websocket_proxy(ws: WebSocket, session_id: Optional[str] = None, browser_token: Optional[str] = None):
    """
    WebSocket proxy: React frontend <-> proxy server <-> Google Gemini Live API.
    """
    await ws.accept()
    print("[proxy] Client Connected")

    active_session_id = None
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

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        await ws.close(code=1008, reason="GEMINI_API_KEY not configured")
        print("[proxy] ERROR: GEMINI_API_KEY not set, closing client")
        return

    upstream_url = f"{GEMINI_WS_URL}?key={api_key}"

    try:
        async with websockets.connect(
            upstream_url,
            ping_interval=None,
            ping_timeout=None,
        ) as google_ws:
            print("[proxy] Google Connected")

            setup_msg = _build_setup_message()
            await google_ws.send(json.dumps(setup_msg))
            print("[proxy] Setup Sent")

            setup_confirmed = False
            while not setup_confirmed:
                raw = await google_ws.recv()
                data = json.loads(raw) if isinstance(raw, str) else json.loads(raw.decode())
                if data.get("setupComplete") is not None:
                    setup_confirmed = True
                    print("[proxy] Setup Confirmed")
                    await ws.send_json(data)
                else:
                    await ws.send_json(data)

            async def forward_to_google():
                """Receive from React client → forward to Google."""
                try:
                    while True:
                        raw_msg = await ws.receive_text()
                        data = json.loads(raw_msg)

                        # Log audio relay specifically
                        if "realtimeInput" in data:
                            print("[proxy] Relaying Audio → Google")
                        else:
                            msg_type = next(iter(data.keys()), "unknown")
                            print(f"[proxy] Relaying {msg_type} → Google")

                        await google_ws.send(raw_msg)
                except WebSocketDisconnect:
                    print("[proxy] Client disconnected")
                except Exception as e:
                    print(f"[proxy] forward_to_google error: {e}")

            async def receive_from_google():
                """Receive from Google → forward to React client."""
                try:
                    async for raw_msg in google_ws:
                        text = raw_msg if isinstance(raw_msg, str) else raw_msg.decode()
                        data = json.loads(text)

                        # Log the type of message being relayed back
                        if "serverContent" in data:
                            sc = data["serverContent"]
                            if sc.get("interrupted"):
                                print("[proxy] Relaying interrupted ← Google")
                            elif sc.get("turnComplete"):
                                print("[proxy] Relaying turnComplete ← Google")
                            else:
                                print("[proxy] Relaying audio/content ← Google")
                        elif "toolCall" in data:
                            print("[proxy] Relaying toolCall ← Google")
                        else:
                            msg_type = next(iter(data.keys()), "unknown")
                            print(f"[proxy] Relaying {msg_type} ← Google")

                        await ws.send_text(text)
                except websockets.exceptions.ConnectionClosed:
                    print("[proxy] Google connection closed")
                except Exception as e:
                    print(f"[proxy] receive_from_google error: {e}")

            await asyncio.gather(forward_to_google(), receive_from_google())

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"[proxy] Google rejected connection: {e}")
        await ws.close(code=1011, reason="Upstream connection refused")
    except Exception as e:
        print(f"[proxy] Unexpected error: {e}")
        try:
            await ws.close(code=1011, reason=str(e)[:120])
        except Exception:
            pass
    finally:
        deregister(ws)
        print("[proxy] Session ended")
