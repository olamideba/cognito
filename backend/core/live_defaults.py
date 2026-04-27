from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from google.genai import types


DEFAULT_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
DEFAULT_VOICE_NAME = "Puck"
DEFAULT_RESPONSE_MODALITIES: tuple[types.Modality, ...] = (types.Modality.AUDIO,)
SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "SYSTEM_PROMPT.md"


def get_default_model() -> str:
    return os.getenv("COGNITO_MODEL", DEFAULT_MODEL)


def get_default_voice_name() -> str:
    return os.getenv("COGNITO_VOICE_NAME", DEFAULT_VOICE_NAME)


def resolve_voice_name(voice_name: Optional[str]) -> str:
    if voice_name:
        return voice_name
    return get_default_voice_name()


def get_default_response_modalities() -> list[types.Modality]:
    return list(DEFAULT_RESPONSE_MODALITIES)


def get_system_instruction() -> str:
    return SYSTEM_PROMPT_PATH.read_text()
