from __future__ import annotations

from pathlib import Path
from typing import Optional
from datetime import datetime
from google.genai import types
from core.config import get_settings, Settings

settings: Settings = get_settings()
DEFAULT_RESPONSE_MODALITIES: tuple[types.Modality, ...] = (types.Modality.AUDIO,)
SYSTEM_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "domains"
    / "agents"
    / "prompts"
    / "system.md"
)


def get_default_model() -> str:
    return settings.COGNITO_MODEL


def get_default_voice_name() -> str:
    return settings.DEFAULT_VOICE_NAME


def resolve_voice_name(voice_name: Optional[str]) -> str:
    if voice_name:
        return voice_name
    return get_default_voice_name()


def get_default_response_modalities() -> list[types.Modality]:
    return list(DEFAULT_RESPONSE_MODALITIES)


def get_system_instruction() -> str:
    prompt_template = SYSTEM_PROMPT_PATH.read_text()
    current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    return prompt_template.format(current_datetime=current_datetime)
