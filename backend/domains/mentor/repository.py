import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.cloud import firestore

from core.db import session_document_ref, session_seed_document, upload_png


async def create_session() -> str:
    session_id = str(uuid.uuid4())
    await session_document_ref(session_id).set(session_seed_document(session_id))
    return session_id


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    doc = await session_document_ref(session_id).get()
    return doc.to_dict() if doc.exists else None


async def update_session(session_id: str, updates: Dict[str, Any]) -> None:
    await session_document_ref(session_id).update(updates)


async def append_distraction_event(session_id: str, event: Dict[str, Any]) -> None:
    await session_document_ref(session_id).update(
        {
            "distraction_events": firestore.ArrayUnion([event]),
        }
    )


async def append_analogy(
    session_id: str,
    concept: str,
    base64_string: str,
    timestamp: Optional[str] = None,
) -> str:
    image_bytes = base64_string.encode("utf-8")
    try:
        import base64 as b64

        image_bytes = b64.b64decode(base64_string)
    except Exception:
        pass

    image_url = await upload_png(
        image_bytes=image_bytes,
        destination_blob_name=f"analogies/{session_id}/{concept}.png",
    )
    entry = {
        "concept": concept,
        "image_url": image_url,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }
    await session_document_ref(session_id).update(
        {
            "analogy_history": firestore.ArrayUnion([entry]),
        }
    )
    return image_url


async def resume_session(prior_session_id: str) -> str:
    prior_session = await get_session(prior_session_id)
    if not prior_session:
        return await create_session()

    session_id = str(uuid.uuid4())
    await session_document_ref(session_id).set(
        session_seed_document(
            session_id,
            goal=prior_session.get("goal"),
            analogy_history=prior_session.get("analogy_history", []),
            quiz_history=prior_session.get("quiz_history", []),
            prior_session_id=prior_session_id,
        )
    )
    return session_id


async def append_quiz(session_id: str, quiz_data: Dict[str, Any]) -> None:
    entry = {
        **quiz_data,
        "user_answer": None,
        "is_correct": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await session_document_ref(session_id).update(
        {
            "quiz_history": firestore.ArrayUnion([entry]),
        }
    )


async def record_quiz_answer(
    session_id: str, component_id: str, answer: str, is_correct: bool
) -> None:
    session = await get_session(session_id)
    if not session:
        return

    history = session.get("quiz_history", [])
    updated = False
    for quiz in history:
        if quiz.get("component_id") == component_id:
            quiz["user_answer"] = answer
            quiz["is_correct"] = is_correct
            updated = True
            break

    if updated:
        await update_session(session_id, {"quiz_history": history})
