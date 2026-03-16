import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from fastapi import WebSocket
from google.adk.tools import ToolContext

from core.db import append_analogy, get_session, update_session

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


def _get_live_context() -> Tuple[Optional[str], Optional[WebSocket]]:
    return _CURRENT_SESSION_ID.get(), _CURRENT_CLIENT_WS.get()


async def _send_ui_envelope(envelope: Dict[str, Any]) -> None:
    _, client_ws = _get_live_context()
    if client_ws is None:
        return
    try:
        await client_ws.send_json(envelope)
    except Exception:
        # Best-effort UI update; tool result still returns to the model.
        return


def _require_session_id() -> Optional[str]:
    session_id, _ = _get_live_context()
    return session_id


async def confirm_session_goal(
    goal: str,
    time_limit_minutes: int,
    tool_context: ToolContext | None = None,
) -> Dict[str, Any]:
    """Saves the user's stated goal and time limit to begin the session. Call this exactly once, after the user has verbally confirmed both their goal and their available time. Do not call this until both values are known."""
    session_id = _require_session_id()
    if not session_id:
        return {"error": "Session context not available"}

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

    result = {
        "session_id": session_id,
        "status": "active",
        "goal": goal,
        "time_limit_seconds": time_limit_seconds,
        "start_time": start_time,
    }

    await _send_ui_envelope({"type": "session_initialized", "payload": result})
    return result


async def get_session_timer(
    tool_context: ToolContext | None = None,
) -> Dict[str, Any]:
    """Returns the current elapsed time and remaining time for the session. Call this to check how much time is left before the session ends, particularly when deciding whether to prompt a wrap-up."""
    session_id = _require_session_id()
    if not session_id:
        return {"error": "Session context not available"}

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
    phase = "wrap_up" if total_seconds > 0 and (remaining / total_seconds) < 0.10 else "working"

    return {
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "total_seconds": total_seconds,
        "percent_complete": percent,
        "phase": phase,
    }


async def generate_analogy_visual(
    concept_label: str,
    image_prompt: str,
    tool_context: ToolContext | None = None,
) -> Dict[str, Any]:
    """Generates a visual diagram or analogy image to help the user understand a concept they are struggling with. Call this after two Socratic prompts have not resolved the user's confusion. Provide a short concept label and a detailed prompt describing the visual."""
    session_id = _require_session_id()
    if not session_id:
        return {"error": "Session context not available"}

    from routers.generate import generate_image

    image_url = await generate_image(concept_label, image_prompt)
    timestamp = datetime.now(timezone.utc).isoformat()

    await append_analogy(session_id, concept_label, image_url, timestamp)

    result = {
        "session_id": session_id,
        "status": "generated",
        "concept_label": concept_label,
        "image_url": image_url,
        "timestamp": timestamp,
    }

    await _send_ui_envelope({"type": "analogy_generated", "payload": result})
    return result


async def render_quiz_component(
    component_type: str,
    question: str,
    options: Optional[list[str]] = None,
    correct_answer: Optional[str] = None,
    hint: Optional[str] = None,
    tool_context: ToolContext | None = None,
) -> Dict[str, Any]:
    """Renders an interactive quiz component in the Socratic Quiz tab. Use this to check the user's understanding after an explanation or when they are stuck. The component type determines the interaction format."""
    session_id = _require_session_id()
    if not session_id:
        return {"error": "Session context not available"}

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
    }

    await _send_ui_envelope(
        {
            "type": "quiz_component",
            "payload": {
                "component_id": comp_id,
                "component_type": component_type,
                "question": question,
                "options": options,
                "hint": hint,
            },
        }
    )
    return result


async def submit_quiz_answer(
    component_id: str,
    answer: str,
    tool_context: ToolContext | None = None,
) -> Dict[str, Any]:
    """Submit a user's answer to a rendered quiz component for validation."""
    session_id = _require_session_id()
    if not session_id:
        return {"error": "Session context not available"}

    session = await get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    state = session.get("state", {})
    correct_answer = state.get("correct_answer")
    is_correct = False
    if correct_answer is not None:
        is_correct = answer.strip().lower() == str(correct_answer).strip().lower()

    result = {
        "component_id": component_id,
        "answer": answer,
        "is_correct": is_correct,
        "correct_answer": correct_answer,
    }

    await _send_ui_envelope(
        {
            "type": "quiz_answer_result",
            "payload": {
                "component_id": component_id,
                "is_correct": is_correct,
            },
        }
    )
    return result


async def update_flow_meter(
    signal_type: str,
    delta: int,
    note: Optional[str] = None,
    tool_context: ToolContext | None = None,
) -> Dict[str, Any]:
    """Updates the session's flow score based on an observed signal. Call this when you detect a significant behavioral pattern — such as the user being stuck, expressing frustration, or returning to focus. Do not call this more than once per minute."""
    session_id = _require_session_id()
    if not session_id:
        return {"error": "Session context not available"}

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

    result = {
        "status": "updated",
        "new_flow_score": new_score,
    }

    await _send_ui_envelope(
        {
            "type": "flow_update",
            "payload": {
                "flow_score": new_score,
                "delta": int(delta),
            },
        }
    )
    return result


handle_confirm_session_goal = confirm_session_goal
handle_get_session_timer = get_session_timer
handle_generate_analogy_visual = generate_analogy_visual
handle_render_quiz_component = render_quiz_component
handle_submit_quiz_answer = submit_quiz_answer
handle_update_flow_meter = update_flow_meter
