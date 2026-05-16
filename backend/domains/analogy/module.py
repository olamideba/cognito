import base64
import logging
from datetime import datetime, timezone

from google import genai
from google.genai import types

from core.config import Settings, get_settings
from domains.mentor.repository import append_analogy
from schemas.generate import (
    FALLBACK_SVG,
    IMAGE_MODEL,
    AnalogyResponse,
    ImageGenerationResult,
)

settings: Settings = get_settings()
logger = logging.getLogger(__name__)


def _build_prompt(concept_label: str, image_prompt: str) -> str:
    return (
        f"Create a clear, educational visual diagram or analogy illustration for: {concept_label}. "
        f"{image_prompt} "
        "Style: clean, minimal, flat design with clear labels. White background. No text unless specified in the prompt."
    )


async def generate_image_result(
    concept_label: str, image_prompt: str
) -> ImageGenerationResult:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    try:
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=[_build_prompt(concept_label, image_prompt)],
            config=types.GenerateContentConfig(
                response_modalities=["Image"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9", image_size="2K"
                ),
            ),
        )

        candidates = response.candidates or []
        if candidates and candidates[0].content and candidates[0].content.parts:
            for part in candidates[0].content.parts:
                if part.inline_data is not None:
                    b64_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                    return ImageGenerationResult(
                        base64_string=b64_data,
                        status="generated",
                        message="Analogy image generated successfully.",
                        model=IMAGE_MODEL,
                    )

        logger.warning("No image part found in Gemini response for '%s'", concept_label)
        return ImageGenerationResult(
            base64_string=FALLBACK_SVG,
            status="failed",
            message="Image generation did not return an image; fallback visual provided.",
            model=IMAGE_MODEL,
            used_fallback=True,
            error="No image part returned by the image model.",
        )

    except Exception as exc:
        logger.exception("Image generation failed for '%s'", concept_label)
        return ImageGenerationResult(
            base64_string=FALLBACK_SVG,
            status="failed",
            message="Image generation failed; fallback visual provided.",
            model=IMAGE_MODEL,
            used_fallback=True,
            error=str(exc),
        )


async def generate_analogy_record(
    session_id: str,
    concept_label: str,
    image_prompt: str,
) -> dict:
    generation = await generate_image_result(concept_label, image_prompt)
    timestamp = datetime.now(timezone.utc).isoformat()
    image_url = await append_analogy(
        session_id,
        concept_label,
        generation.base64_string,
        timestamp,
    )

    result = {
        "session_id": session_id,
        "status": generation.status,
        "concept_label": concept_label,
        "image_url": image_url,
        "timestamp": timestamp,
        "message": generation.message,
        "model": generation.model,
        "used_fallback": generation.used_fallback,
    }
    if generation.error:
        result["error"] = generation.error
    return result


async def generate_analogy_response(
    concept_label: str, image_prompt: str
) -> AnalogyResponse:
    result = await generate_image_result(concept_label, image_prompt)
    return AnalogyResponse(
        image_url=result.base64_string,
        concept_label=concept_label,
    )
