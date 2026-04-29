from __future__ import annotations
from typing import Optional
import base64
from pydantic import BaseModel
from core.config import get_settings, Settings

settings: Settings = get_settings()

IMAGE_MODEL = settings.COGNITO_IMAGE_MODEL

FALLBACK_SVG = (
    "data:image/svg+xml;base64,"
    + base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
        b'<rect width="512" height="512" fill="#f0f0f0"/>'
        b'<text x="256" y="240" text-anchor="middle" font-family="monospace" font-size="18" fill="#666">'
        b"Image generation</text>"
        b'<text x="256" y="270" text-anchor="middle" font-family="monospace" font-size="18" fill="#666">'
        b"unavailable</text></svg>"
    ).decode()
)


class AnalogyRequest(BaseModel):
    concept_label: str
    image_prompt: str


class AnalogyResponse(BaseModel):
    image_url: str
    concept_label: str


class ImageGenerationResult(BaseModel):
    image_url: str
    status: str
    message: str
    model: str
    used_fallback: bool = False
    error: Optional[str] = None
