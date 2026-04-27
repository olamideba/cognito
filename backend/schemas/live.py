from __future__ import annotations
from pydantic import BaseModel
from typing import Any, Optional, List, Dict

class LiveToolConfig(BaseModel):
    type: str
    googleSearch: Optional[Dict[str, Any]] = None
    functionDeclarations: Optional[List[Dict[str, Any]]] = None


class LiveConfigResponse(BaseModel):
    model: str
    systemInstruction: str
    tools: List[LiveToolConfig]
    responseModalities: List[str]
    voiceName: str
