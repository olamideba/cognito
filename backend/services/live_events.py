import base64
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from google.genai import types


def serialize_event(event) -> Optional[str]:
    if getattr(event, "interrupted", False):
        return json.dumps({"serverContent": {"interrupted": True}})
    
    if getattr(event, "turn_complete", False):
        return json.dumps({"serverContent": {"turnComplete": True}})
    
    if hasattr(event, "actions") and getattr(event, "actions", None) and getattr(event.actions, "function_calls", None):
        function_calls = []
        for call in event.actions.function_calls:
            function_calls.append({
                "id": getattr(call, "id", None),
                "name": call.name,
                "args": getattr(call, "args", {}),
            })
        if function_calls:
            return json.dumps({"toolCall": {"functionCalls": function_calls}})
    
    if getattr(event, "content", None) and getattr(event.content, "parts", None):
        parts = []
        for part in event.content.parts:
            if getattr(part, "inline_data", None):
                b64_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                parts.append({
                    "inlineData": {
                        "mimeType": part.inline_data.mime_type,
                        "data": b64_data
                    }
                })
            elif getattr(part, "text", None):
                parts.append({"text": part.text})
        if parts:
            return json.dumps({
                "serverContent": {
                    "modelTurn": {
                        "parts": parts
                    }
                }
            })
            
    return None

def build_reconnect_message(session_snapshot: Dict[str, Any]) -> Optional[types.Content]:
    goal = session_snapshot.get("goal")
    time_limit_seconds = session_snapshot.get("time_limit_seconds")
    start_time = session_snapshot.get("start_time")
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
    if goal or time_limit_seconds or remaining_minutes is not None:
        parts = []
        if goal:
            parts.append(f"Goal: {goal}.")
        if remaining_minutes is not None:
            parts.append(f"Remaining time: {remaining_minutes} minutes.")
        elif time_limit_seconds:
            minutes = int(time_limit_seconds) // 60
            parts.append(f"Time limit: {minutes} minutes.")
        parts.append("Continue without re-asking for any already-known fields.")  
        
        return types.Content(
                role="user",
                parts=[types.Part(text=" ".join(parts))],
            )