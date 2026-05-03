import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from domains.live_session.envelope import make_envelope
from domains.mentor.repository import (
    append_distraction_event,
    append_quiz,
    create_session,
    get_session,
    record_quiz_answer,
    resume_session,
    update_session,
)


async def initialize_live_session(requested_session_id: Optional[str]) -> Dict[str, Any]:
    active_session_id: Optional[str] = None
    is_reconnect = False

    if requested_session_id:
        existing = await get_session(requested_session_id)
        if existing:
            if existing.get("status") == "completed":
                active_session_id = await resume_session(requested_session_id)
            else:
                active_session_id = requested_session_id
            is_reconnect = True
        else:
            active_session_id = await create_session()
    else:
        active_session_id = await create_session()

    return {
        "session_id": active_session_id,
        "is_reconnect": is_reconnect,
        "session_snapshot": await get_session(active_session_id),
    }


async def confirm_session_goal(
    session_id: str,
    goal: str,
    time_limit_minutes: int,
) -> Dict[str, Any]:
    time_limit_seconds = int(time_limit_minutes) * 60
    start_time = datetime.now(timezone.utc).isoformat()

    await update_session(
        session_id,
        {
            "goal": goal,
            "time_limit_seconds": time_limit_seconds,
            "start_time": start_time,
            "status": "active",
            "state.session_phase": "working",
        },
    )

    return {
        "session_id": session_id,
        "status": "active",
        "goal": goal,
        "time_limit_seconds": time_limit_seconds,
        "start_time": start_time,
    }


async def get_session_timer(session_id: str) -> Dict[str, Any]:
    session = await get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    start_time_str = session.get("start_time")
    total_seconds = session.get("time_limit_seconds", 1800)

    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str)
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    else:
        elapsed = 0

    remaining = max(0, total_seconds - elapsed)
    percent = (elapsed / total_seconds * 100) if total_seconds > 0 else 0
    phase = (
        "wrap_up"
        if total_seconds > 0 and (remaining / total_seconds) < 0.10
        else "working"
    )

    return {
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "total_seconds": total_seconds,
        "percent_complete": percent,
        "phase": phase,
    }


async def render_quiz_component(
    session_id: str,
    component_type: str,
    question: str,
    options: Optional[list[str]] = None,
    correct_answer: Optional[str] = None,
    hint: Optional[str] = None,
) -> Dict[str, Any]:
    comp_id = str(uuid.uuid4())
    options = options or []

    session = await get_session(session_id)
    if session:
        state = session.get("state", {})
        if correct_answer is not None:
            state["correct_answer"] = correct_answer
        state["last_component_id"] = comp_id
        await update_session(session_id, {"state": state})

    result = {
        "status": "rendered",
        "component_type": component_type,
        "component_id": comp_id,
        "question": question,
        "options": options,
        "hint": hint,
    }

    await append_quiz(session_id, result)
    return result


async def submit_quiz_answer(
    session_id: str,
    component_id: str,
    answer: str,
) -> Dict[str, Any]:
    session = await get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    state = session.get("state", {})
    correct_answer = state.get("correct_answer")
    is_correct = False
    if correct_answer is not None:
        is_correct = answer.strip().lower() == str(correct_answer).strip().lower()

    await record_quiz_answer(session_id, component_id, answer, is_correct)

    return {
        "component_id": component_id,
        "answer": answer,
        "is_correct": is_correct,
        "correct_answer": correct_answer,
    }


async def update_flow_meter(
    session_id: str,
    signal_type: str,
    delta: int,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    session = await get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    current_score = session.get("flow_score", 100)
    new_score = max(0, min(100, current_score + int(delta)))

    await update_session(
        session_id,
        {
            "flow_score": new_score,
            "state.last_flow_signal": {
                "signal_type": signal_type,
                "delta": int(delta),
                "note": note,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )

    return {
        "status": "updated",
        "new_flow_score": new_score,
    }


def compute_flow_delta(signal_data: Dict[str, Any]) -> int:
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


async def apply_flow_signal(
    session_id: str,
    signal_data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    session = await get_session(session_id)
    if not session:
        return None

    delta = compute_flow_delta(signal_data)
    if delta == 0:
        return None

    current_score = session.get("flow_score", 100)
    new_score = max(0, min(100, current_score + delta))
    event_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": signal_data.get("signal"),
        "duration_seconds": signal_data.get("duration_seconds", 0),
    }

    await update_session(session_id, {"flow_score": new_score})
    await append_distraction_event(session_id, event_record)

    return make_envelope(
        "flow_update",
        {"flow_score": new_score, "delta": delta},
    )

