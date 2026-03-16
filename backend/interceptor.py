import json
from typing import Any, Dict, Callable
from fastapi import WebSocket
from tools.handlers import handle_tool_call

async def intercept(
    raw_msg: str,
    send_to_upstream: Callable,
    client_ws: WebSocket,
    session_id: str
) -> bool:
    data = json.loads(raw_msg)
    if "toolCall" not in data:
        return False

    tool_calls = data["toolCall"].get("functionCalls", [])
    responses = []

    for call in tool_calls:
        name = call["name"]
        args = call.get("args", {})
        call_id = call["id"]

        result, ui_envelope = await handle_tool_call(
            name=name,
            args=args,
            session_id=session_id
        )

        responses.append({
            "id": call_id,
            "name": name,
            "response": {"output": result}
        })

        if ui_envelope:
            await client_ws.send_json(ui_envelope)

    tool_response_msg = {
        "toolResponse": {
            "functionResponses": responses
        }
    }
    await send_to_upstream(json.dumps(tool_response_msg))
    return True
