from __future__ import annotations
from typing import List

from schemas.live import LiveConfigResponse, LiveToolConfig
from fastapi import APIRouter
from tools.registry import TOOL_DECLARATIONS
import os
from pathlib import Path

router = APIRouter(prefix="/api/live")

@router.post("/config", response_model=LiveConfigResponse)
def get_live_config() -> LiveConfigResponse:
    model = os.getenv(
        "COGNITO_MODEL",
        "gemini-2.5-flash-native-audio-preview-12-2025",
    )

    system_instruction = Path("SYSTEM_PROMPT.md").read_text()

    tools: List[LiveToolConfig] = [
        LiveToolConfig(type="googleSearch", googleSearch={}),
        LiveToolConfig(
            type="functionDeclarations",
            functionDeclarations=TOOL_DECLARATIONS,
        ),
    ]

    return LiveConfigResponse(
        model=model,
        systemInstruction=system_instruction,
        tools=tools,
        responseModalities=["AUDIO"],
        voiceName=os.getenv("COGNITO_VOICE_NAME", "Aoede"),
    )
