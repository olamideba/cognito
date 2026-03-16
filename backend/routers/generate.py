import base64
import os
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generate")

IMAGE_MODEL = os.getenv("COGNITO_IMAGE_MODEL", "gemini-2.5-flash-preview-image-generation")

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


async def generate_image(concept_label: str, image_prompt: str) -> str:
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        full_prompt = (
            f"Create a clear, educational visual diagram or analogy illustration for: {concept_label}. "
            f"{image_prompt} "
            "Style: clean, minimal, flat design with clear labels. White background. No text unless specified in the prompt."
        )

        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=[full_prompt],
            config=types.GenerateContentConfig(
                response_modalities=["Image"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                mime_type = part.inline_data.mime_type or "image/png"
                b64_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                return f"data:{mime_type};base64,{b64_data}"

        logger.warning("No image part found in Gemini response for '%s'", concept_label)
        return FALLBACK_SVG

    except Exception:
        logger.exception("Image generation failed for '%s'", concept_label)
        return FALLBACK_SVG


@router.post("/analogy", response_model=AnalogyResponse)
async def generate_analogy(req: AnalogyRequest) -> AnalogyResponse:
    image_url = await generate_image(req.concept_label, req.image_prompt)
    return AnalogyResponse(image_url=image_url, concept_label=req.concept_label)
