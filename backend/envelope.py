from typing import Any, Dict


def make_envelope(type_: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": type_, "payload": payload}
