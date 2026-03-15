from typing import Dict, Optional
from fastapi import WebSocket

_active_sessions: Dict[int, str] = {}

def register(ws: WebSocket, session_id: str) -> None:
    _active_sessions[id(ws)] = session_id

def deregister(ws: WebSocket) -> None:
    _active_sessions.pop(id(ws), None)

def get_session_id(ws: WebSocket) -> Optional[str]:
    return _active_sessions.get(id(ws))
