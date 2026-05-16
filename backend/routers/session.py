from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from domains.agents.handlers import submit_quiz_answer
from domains.live_session.context import set_session_id
from domains.mentor.repository import get_session

router = APIRouter(prefix="/api/session")

class QuizAnswerRequest(BaseModel):
    component_id: str
    answer: str

@router.get("/{session_id}")
async def read_session(session_id: str):
    data = await get_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data

@router.post("/{session_id}/quiz_answer")
async def post_quiz_answer(session_id: str, req: QuizAnswerRequest):
    set_session_id(session_id)
    result = await submit_quiz_answer(
        component_id=req.component_id,
        answer=req.answer,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "correct": result.get("is_correct", False),
        "is_correct": result.get("is_correct", False),
        "feedback": "Correct!" if result.get("is_correct") else "Incorrect",
        "component_id": req.component_id,
    }
