import uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, Tuple, Optional
from core.db import get_session, update_session, append_analogy

async def handle_tool_call(name: str, args: Dict[str, Any], session_id: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
    if name == "confirm_session_goal":
        goal = args.get("goal")
        time_limit = args.get("time_limit_minutes", 30)
        time_limit_seconds = time_limit * 60
        start_time = datetime.now(timezone.utc).isoformat()
        
        await update_session(session_id, {
            "goal": goal,
            "time_limit_seconds": time_limit_seconds,
            "start_time": start_time,
            "status": "active",
            "state.session_phase": "working"
        })
        
        result = {
            "status": "active",
            "goal": goal,
            "time_limit_seconds": time_limit_seconds,
            "start_time": start_time
        }
        
        envelope = {
            "type": "session_initialized",
            "payload": result
        }
        return result, envelope

    elif name == "get_session_timer":
        session = await get_session(session_id)
        if not session:
            return {"error": "Session not found"}, None
            
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
        
        result = {
            "elapsed_seconds": int(elapsed),
            "remaining_seconds": int(remaining),
            "total_seconds": total_seconds,
            "percent_complete": percent,
            "phase": phase
        }
        return result, None

    elif name == "generate_analogy_visual":
        concept = args.get("concept_label", "")
        
        image_url = f"https://placeholder.com/analogy/{uuid.uuid4()}"
        
        await append_analogy(session_id, concept, image_url)
        
        result = {
            "status": "generated",
            "concept_label": concept,
            "image_url": image_url
        }
        
        envelope = {
            "type": "analogy_generated",
            "payload": result
        }
        return result, envelope

    elif name == "render_quiz_component":
        comp_type = args.get("component_type")
        question = args.get("question")
        options = args.get("options", [])
        correct_answer = args.get("correct_answer")
        hint = args.get("hint")
        
        comp_id = str(uuid.uuid4())
        
        session = await get_session(session_id)
        if session:
            state = session.get("state", {})
            state["correct_answer"] = correct_answer
            await update_session(session_id, {"state": state})
        
        result = {
            "status": "rendered",
            "component_type": comp_type,
            "component_id": comp_id
        }
        
        envelope = {
            "type": "quiz_component",
            "payload": {
                "component_id": comp_id,
                "component_type": comp_type,
                "question": question,
                "options": options,
                "hint": hint
            }
        }
        return result, envelope

    elif name == "update_flow_meter":
        signal_type = args.get("signal_type")
        delta = args.get("delta", 0)
        
        session = await get_session(session_id)
        if not session:
            return {"error": "Session not found"}, None
            
        current_score = session.get("flow_score", 100)
        new_score = max(0, min(100, current_score + delta))
        
        await update_session(session_id, {"flow_score": new_score})
        
        result = {
            "status": "updated",
            "new_flow_score": new_score
        }
        
        envelope = {
            "type": "flow_update",
            "payload": {
                "flow_score": new_score,
                "delta": delta
            }
        }
        return result, envelope
        
    return {"error": f"Unknown tool: {name}"}, None
