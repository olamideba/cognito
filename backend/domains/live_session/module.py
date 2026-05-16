import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from core.live_defaults import get_default_response_modalities, resolve_voice_name
from domains.agents.module import agent
from core.session import deregister, register
from domains.live_session.events import build_reconnect_message, serialize_event
from domains.live_session.context import set_live_context
from domains.mentor.module import (
    apply_flow_signal,
    initialize_live_session,
)
from scripts.adk_patch import patch_adk_trace_tool_call

logger = logging.getLogger(__name__)
APP_NAME = "cognito"

patch_adk_trace_tool_call()
session_service = InMemorySessionService()
runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)


@dataclass
class LiveSessionState:
    session_id: str
    is_reconnect: bool
    session_snapshot: Optional[dict]


async def run_live_session(
    ws: WebSocket,
    session_id: Optional[str] = None,
    browser_token: Optional[str] = None,
    voice_name: Optional[str] = None,
) -> None:
    del browser_token
    await ws.accept()
    logger.info("Client connected to live session")

    state = await _initialize_session_state(session_id)
    register(ws, state.session_id)
    await ws.send_json(
        {
            "type": "session_created",
            "payload": {"session_id": state.session_id},
        }
    )

    try:
        live_request_queue = LiveRequestQueue()
        await _ensure_adk_session(state.session_id)

        await asyncio.gather(
            _forward_client_messages(ws, state.session_id, live_request_queue),
            _forward_runner_events(
                ws=ws,
                state=state,
                live_request_queue=live_request_queue,
                run_config=_build_run_config(voice_name),
            ),
        )
    except Exception as exc:
        logger.exception("Unexpected live session error")
        try:
            await ws.close(code=1011, reason=str(exc)[:120])
        except Exception:
            pass
    finally:
        deregister(ws)
        await _delete_adk_session(state.session_id)
        logger.info("Live session ended")


async def _initialize_session_state(requested_session_id: Optional[str]) -> LiveSessionState:
    initialized = await initialize_live_session(requested_session_id)
    return LiveSessionState(
        session_id=initialized["session_id"],
        is_reconnect=initialized["is_reconnect"],
        session_snapshot=initialized["session_snapshot"],
    )


def _build_run_config(voice_name: Optional[str]) -> RunConfig:
    resolved_voice_name = resolve_voice_name(voice_name)
    return RunConfig(
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


async def _ensure_adk_session(session_id: str) -> None:
    existing_adk_session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )
    if not existing_adk_session:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=session_id,
            session_id=session_id,
        )


async def _delete_adk_session(session_id: str) -> None:
    try:
        await session_service.delete_session(
            app_name=APP_NAME,
            user_id=session_id,
            session_id=session_id,
        )
    except Exception:
        pass


async def _forward_client_messages(
    ws: WebSocket,
    session_id: str,
    live_request_queue: LiveRequestQueue,
) -> None:
    try:
        while True:
            raw_msg = await ws.receive_text()
            data = json.loads(raw_msg)

            if data.get("type") == "flow_signal":
                asyncio.create_task(_handle_flow_signal(ws, session_id, data))
                continue

            if "realtimeInput" in data:
                for chunk in data["realtimeInput"].get("mediaChunks", []):
                    b_data = base64.b64decode(chunk["data"])
                    live_request_queue.send_realtime(
                        types.Blob(data=b_data, mime_type=chunk["mimeType"])
                    )
                continue

            if "clientContent" in data:
                for turn in data["clientContent"].get("turns", []):
                    content = _build_turn_content(turn)
                    if content is not None:
                        live_request_queue.send_content(content)

    except WebSocketDisconnect:
        logger.info("Client disconnected from live session")
    except Exception:
        logger.exception("Error while forwarding client messages")


def _build_turn_content(turn: dict) -> Optional[types.Content]:
    role = turn.get("role", "user")
    parts = []
    for part in turn.get("parts", []):
        if "text" in part:
            parts.append(types.Part(text=part["text"]))
    if not parts:
        return None
    return types.Content(role=role, parts=parts)


async def _handle_flow_signal(ws: WebSocket, session_id: str, signal_data: dict) -> None:
    envelope = await apply_flow_signal(session_id, signal_data)
    if envelope is None:
        return
    try:
        await ws.send_json(envelope)
    except Exception:
        pass


async def _forward_runner_events(
    ws: WebSocket,
    state: LiveSessionState,
    live_request_queue: LiveRequestQueue,
    run_config: RunConfig,
) -> None:
    try:
        set_live_context(state.session_id, ws)
        await ws.send_json({"setupComplete": {}})

        if state.session_snapshot:
            await _hydrate_client_workspace(ws, state.session_snapshot)

        if state.is_reconnect and state.session_snapshot:
            content = build_reconnect_message(state.session_snapshot)
            if content is not None:
                live_request_queue.send_content(content)

        async for event in runner.run_live(
            user_id=state.session_id,
            session_id=state.session_id,
            run_config=run_config,
            live_request_queue=live_request_queue,
        ):
            event_json_str = serialize_event(event)
            if event_json_str:
                try:
                    await ws.send_text(event_json_str)
                except Exception:
                    # Connection likely closed by client already
                    break
    except Exception:
        logger.exception("Error while forwarding runner events")


async def _hydrate_client_workspace(ws: WebSocket, session_snapshot: dict) -> None:
    analogy_history = session_snapshot.get("analogy_history", [])
    # Align Firestore 'concept' with frontend 'concept_label'
    hydrated_analogies = []
    for item in analogy_history:
        hydrated_analogies.append({
            "concept_label": item.get("concept", item.get("concept_label")),
            "image_url": item.get("image_url"),
            "timestamp": item.get("timestamp")
        })

    quiz_history = session_snapshot.get("quiz_history", [])

    if hydrated_analogies or quiz_history:
        try:
            await ws.send_json({
                "type": "workspace_hydrated",
                "payload": {
                    "analogy_history": hydrated_analogies,
                    "quiz_history": quiz_history,
                }
            })
        except Exception:
            logger.error("Failed to send workspace hydration")
