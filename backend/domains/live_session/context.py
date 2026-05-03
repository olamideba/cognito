from contextvars import ContextVar
from typing import Any, Dict, Optional, Tuple

from fastapi import WebSocket

_CURRENT_SESSION_ID: ContextVar[Optional[str]] = ContextVar(
    "current_session_id",
    default=None,
)
_CURRENT_CLIENT_WS: ContextVar[Optional[WebSocket]] = ContextVar(
    "current_client_ws",
    default=None,
)


def set_live_context(session_id: str, client_ws: WebSocket) -> None:
    _CURRENT_SESSION_ID.set(session_id)
    _CURRENT_CLIENT_WS.set(client_ws)


def set_session_id(session_id: str) -> None:
    _CURRENT_SESSION_ID.set(session_id)


def get_live_context() -> Tuple[Optional[str], Optional[WebSocket]]:
    return _CURRENT_SESSION_ID.get(), _CURRENT_CLIENT_WS.get()


def require_session_id() -> Optional[str]:
    session_id, _ = get_live_context()
    return session_id


async def send_ui_envelope(envelope: Dict[str, Any]) -> None:
    _, client_ws = get_live_context()
    if client_ws is None:
        return
    try:
        await client_ws.send_json(envelope)
    except Exception:
        return

