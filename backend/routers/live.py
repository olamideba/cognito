from __future__ import annotations
from typing import List

from schemas.live import LiveConfigResponse, LiveToolConfig
from fastapi import APIRouter
from core.live_defaults import (
    get_default_model,
    get_default_response_modalities,
    get_default_voice_name,
    get_system_instruction,
)
from tools.registry import TOOL_DECLARATIONS

router = APIRouter(prefix="/api/live")

@router.post("/config", response_model=LiveConfigResponse)
def get_live_config() -> LiveConfigResponse:
    tools: List[LiveToolConfig] = [
        LiveToolConfig(type="googleSearch", googleSearch={}),
        LiveToolConfig(
            type="functionDeclarations",
            functionDeclarations=TOOL_DECLARATIONS,
        ),
    ]

    return LiveConfigResponse(
        model=get_default_model(),
        systemInstruction=get_system_instruction(),
        tools=tools,
        responseModalities=get_default_response_modalities(),
        voiceName=get_default_voice_name(),
    )
