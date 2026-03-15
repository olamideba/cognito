from fastapi import APIRouter, HTTPException
from core.db import get_session

router = APIRouter(prefix="/api/session")

@router.get("/{session_id}")
async def read_session(session_id: str):
    data = await get_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data
