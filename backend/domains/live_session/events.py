import base64
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.genai import types


def serialize_event(event) -> Optional[str]:
    if getattr(event, "interrupted", False):
        return json.dumps({"serverContent": {"interrupted": True}})

    if getattr(event, "turn_complete", False):
        return json.dumps({"serverContent": {"turnComplete": True}})

    if (
        hasattr(event, "actions")
        and getattr(event, "actions", None)
        and getattr(event.actions, "function_calls", None)
    ):
        function_calls = []
        for call in event.actions.function_calls:
            function_calls.append(
                {
                    "id": getattr(call, "id", None),
                    "name": call.name,
                    "args": getattr(call, "args", {}),
                }
            )
        if function_calls:
            return json.dumps({"toolCall": {"functionCalls": function_calls}})

    if getattr(event, "content", None) and getattr(event.content, "parts", None):
        parts = []
        for part in event.content.parts:
            if getattr(part, "inline_data", None):
                b64_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                parts.append(
                    {
                        "inlineData": {
                            "mimeType": part.inline_data.mime_type,
                            "data": b64_data,
                        }
                    }
                )
            elif getattr(part, "text", None):
                parts.append({"text": part.text})
        if parts:
            return json.dumps(
                {
                    "serverContent": {
                        "modelTurn": {
                            "parts": parts,
                        }
                    }
                }
            )

    return None


def build_reconnect_message(
    session_snapshot: Dict[str, Any],
) -> Optional[types.Content]:
    goal = session_snapshot.get("goal")
    time_limit_seconds = session_snapshot.get("time_limit_seconds")
    start_time = session_snapshot.get("start_time")
    flow_score = session_snapshot.get("flow_score", 100)
    session_phase = session_snapshot.get("state", {}).get("session_phase", "working")
    analogy_history = session_snapshot.get("analogy_history", [])
    quiz_history = session_snapshot.get("quiz_history", [])

    if not any([goal, time_limit_seconds, analogy_history, quiz_history]):
        return None

    remaining_minutes = None
    if time_limit_seconds and start_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
            remaining_seconds = max(0, time_limit_seconds - elapsed)
            remaining_minutes = max(0, int(remaining_seconds // 60))
        except Exception:
            remaining_minutes = None

    parts = ["You are resuming an active session. Do not re-introduce yourself or ask for information you already have."]

    if goal:
        parts.append(f"The user's goal is: {goal}.")

    if remaining_minutes is not None:
        parts.append(f"There are approximately {remaining_minutes} minutes remaining.")
    elif time_limit_seconds:
        parts.append(f"The session time limit is {int(time_limit_seconds) // 60} minutes.")

    parts.append(f"The user's current flow score is {flow_score}/100 and the session phase is '{session_phase}'.")

    if analogy_history:
        labels = [item.get("concept", item.get("concept_label", "")) for item in analogy_history if item.get("concept") or item.get("concept_label")]
        if labels:
            label_list = ", ".join(f'"{l}"' for l in labels)
            parts.append(f"The following analogy images have already been shown to the user — do not regenerate them: {label_list}.")

    if quiz_history:
        correct = sum(1 for q in quiz_history if q.get("is_correct") is True)
        incorrect = sum(1 for q in quiz_history if q.get("is_correct") is False)
        unanswered = sum(1 for q in quiz_history if q.get("is_correct") is None)
        last_quiz = next(
            (q for q in reversed(quiz_history) if q.get("question")), None
        )
        summary = f"Quiz history: {correct} correct, {incorrect} incorrect, {unanswered} unanswered."
        if last_quiz:
            summary += f" The last question asked was: \"{last_quiz['question']}\""
            if last_quiz.get("is_correct") is True:
                summary += " — answered correctly."
            elif last_quiz.get("is_correct") is False:
                summary += " — answered incorrectly."
            else:
                summary += " — not yet answered."
        parts.append(summary)

    parts.append("Pick up naturally from where the session left off. Welcome the user with a terse summary of the last session.")

    return types.Content(
        role="user",
        parts=[types.Part(text=" ".join(parts))],
    )