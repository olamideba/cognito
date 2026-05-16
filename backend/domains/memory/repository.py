from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.db import memory_document, memory_document_ref


async def get_memory(browser_token: str) -> Optional[Dict[str, Any]]:
    doc = await memory_document_ref(browser_token).get()
    return doc.to_dict() if doc.exists else None


async def update_memory(browser_token: str, updates: Dict[str, Any]) -> None:
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    doc_ref = memory_document_ref(browser_token)
    doc = await doc_ref.get()
    if doc.exists:
        await doc_ref.update(updates)
        return

    full_doc = memory_document(browser_token)
    full_doc.update(updates)
    await doc_ref.set(full_doc)

