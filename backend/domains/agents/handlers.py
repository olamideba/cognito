from typing import Optional

from google.adk.tools import ToolContext

from domains.analogy.module import generate_analogy_record
from domains.live_session.context import require_session_id, send_ui_envelope, set_live_context
from domains.mentor.module import (
    confirm_session_goal as confirm_session_goal_module,
    get_session_timer as get_session_timer_module,
    render_quiz_component as render_quiz_component_module,
    submit_quiz_answer as submit_quiz_answer_module,
    update_flow_meter as update_flow_meter_module,
)


async def confirm_session_goal(
    goal: str,
    time_limit_minutes: int,
    tool_context: ToolContext | None = None,
) -> dict:
    session_id = require_session_id()
    if not session_id:
        return {"error": "Session context not available"}
    result = await confirm_session_goal_module(session_id, goal, time_limit_minutes)
    await send_ui_envelope({"type": "session_initialized", "payload": result})
    return result


async def get_session_timer(
    tool_context: ToolContext | None = None,
) -> dict:
    session_id = require_session_id()
    if not session_id:
        return {"error": "Session context not available"}
    return await get_session_timer_module(session_id)


async def generate_analogy_visual(
    concept_label: str,
    image_prompt: str,
    tool_context: ToolContext | None = None,
) -> dict:
    session_id = require_session_id()
    if not session_id:
        return {"error": "Session context not available"}
    result = await generate_analogy_record(session_id, concept_label, image_prompt)
    await send_ui_envelope({"type": "analogy_generated", "payload": result})
    return result


async def render_quiz_component(
    component_type: str,
    question: str,
    options: Optional[list[str]] = None,
    correct_answer: Optional[str] = None,
    hint: Optional[str] = None,
    tool_context: ToolContext | None = None,
) -> dict:
    session_id = require_session_id()
    if not session_id:
        return {"error": "Session context not available"}
    result = await render_quiz_component_module(
        session_id=session_id,
        component_type=component_type,
        question=question,
        options=options,
        correct_answer=correct_answer,
        hint=hint,
    )
    await send_ui_envelope(
        {
            "type": "quiz_component",
            "payload": {
                "component_id": result["component_id"],
                "component_type": result["component_type"],
                "question": result["question"],
                "options": result["options"],
                "hint": result["hint"],
            },
        }
    )
    return result


async def submit_quiz_answer(
    component_id: str,
    answer: str,
    tool_context: ToolContext | None = None,
) -> dict:
    session_id = require_session_id()
    if not session_id:
        return {"error": "Session context not available"}
    result = await submit_quiz_answer_module(session_id, component_id, answer)
    await send_ui_envelope(
        {
            "type": "quiz_answer_result",
            "payload": {
                "component_id": component_id,
                "is_correct": result.get("is_correct", False),
            },
        }
    )
    return result


async def update_flow_meter(
    signal_type: str,
    delta: int,
    note: Optional[str] = None,
    tool_context: ToolContext | None = None,
) -> dict:
    session_id = require_session_id()
    if not session_id:
        return {"error": "Session context not available"}
    result = await update_flow_meter_module(session_id, signal_type, delta, note)
    await send_ui_envelope(
        {
            "type": "flow_update",
            "payload": {
                "flow_score": result.get("new_flow_score"),
                "delta": int(delta),
            },
        }
    )
    return result
