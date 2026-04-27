import base64
import logging
import os

from fastapi import APIRouter
from google import genai
from google.genai import types

from schemas.generate import (
    IMAGE_MODEL,
    FALLBACK_SVG,
    AnalogyRequest,
    AnalogyResponse,
    ImageGenerationResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generate")


async def generate_image_result(
    concept_label: str, image_prompt: str
) -> ImageGenerationResult:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    full_prompt = (
        f"Create a clear, educational visual diagram or analogy illustration for: {concept_label}. "
        f"{image_prompt} "
        "Style: clean, minimal, flat design with clear labels. White background. No text unless specified in the prompt."
    )

    try:
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=[full_prompt],
            config=types.GenerateContentConfig(
                response_modalities=["Image"],
            ),
        )

        candidates = response.candidates or []
        if candidates and candidates[0].content and candidates[0].content.parts:
            for part in candidates[0].content.parts:
                if part.inline_data is not None:
                    mime_type = part.inline_data.mime_type or "image/png"
                    b64_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                    return ImageGenerationResult(
                        image_url=f"data:{mime_type};base64,{b64_data}",
                        status="generated",
                        message="Analogy image generated successfully.",
                        model=IMAGE_MODEL,
                    )

        logger.warning("No image part found in Gemini response for '%s'", concept_label)
        return ImageGenerationResult(
            image_url=FALLBACK_SVG,
            status="failed",
            message="Image generation did not return an image; fallback visual provided.",
            model=IMAGE_MODEL,
            used_fallback=True,
            error="No image part returned by the image model.",
        )

    except Exception as exc:
        logger.exception("Image generation failed for '%s'", concept_label)
        return ImageGenerationResult(
            image_url=FALLBACK_SVG,
            status="failed",
            message="Image generation failed; fallback visual provided.",
            model=IMAGE_MODEL,
            used_fallback=True,
            error=str(exc),
        )


async def generate_image(concept_label: str, image_prompt: str) -> str:
    result = await generate_image_result(concept_label, image_prompt)
    return result.image_url


@router.post("/analogy", response_model=AnalogyResponse)
async def generate_analogy(req: AnalogyRequest) -> AnalogyResponse:
    image_url = await generate_image(req.concept_label, req.image_prompt)
    return AnalogyResponse(image_url=image_url, concept_label=req.concept_label)
