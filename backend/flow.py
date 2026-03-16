import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

from core.db import get_session, update_session, append_distraction_event
from envelope import make_envelope


def compute_delta(signal_data: Dict[str, Any]) -> int:
    signal = signal_data.get("signal")
    if signal == "screen_inactive":
        duration = signal_data.get("duration_seconds", 0)
        if duration > 120:
            return -10
        if duration > 60:
            return -5
        return 0
    if signal == "tab_switch":
        return -8
    if signal == "cam_event":
        event = signal_data.get("event")
        if event == "frustration_detected":
            return -7
        if event == "eye_away":
            return -3
        if event == "look_return":
            return 2
    return 0


async def handle_flow_signal(signal_data: Dict[str, Any], session_id: str, client_ws) -> None:
    session = await get_session(session_id)
    if not session:
        return

    delta = compute_delta(signal_data)
    if delta == 0:
        return

    current_score = session.get("flow_score", 100)
    new_score = max(0, min(100, current_score + delta))

    event_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": signal_data.get("signal"),
        "duration_seconds": signal_data.get("duration_seconds", 0),
    }

    await update_session(session_id, {"flow_score": new_score})
    await append_distraction_event(session_id, event_record)

    envelope = make_envelope("flow_update", {"flow_score": new_score, "delta": delta})
    try:
        await client_ws.send_json(envelope)
    except Exception:
        pass
