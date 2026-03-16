from fastapi import APIRouter, HTTPException
from core.db import get_memory

router = APIRouter(prefix="/api/memory")

@router.get("/{browser_token}")
async def read_memory(browser_token: str):
    data = await get_memory(browser_token)
    if not data:
        raise HTTPException(status_code=404, detail="Memory not found")
    return data
