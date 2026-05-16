from fastapi import APIRouter
from domains.analogy.module import generate_analogy_response, generate_image_result

from schemas.generate import (
    AnalogyRequest,
    AnalogyResponse,
    ImageGenerationResult,
)

router = APIRouter(prefix="/api/generate")


async def generate_image(concept_label: str, image_prompt: str) -> str:
    result = await generate_image_result(concept_label, image_prompt)
    return result.base64_string


@router.post("/analogy", response_model=AnalogyResponse)
async def generate_analogy(req: AnalogyRequest) -> AnalogyResponse:
    image_url = await generate_image(req.concept_label, req.image_prompt)
    return AnalogyResponse(image_url=image_url, concept_label=req.concept_label)
