import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from google.cloud import firestore

_db: Optional[firestore.AsyncClient] = None

def get_db() -> firestore.AsyncClient:
    global _db
    if _db is None:
        _db = firestore.AsyncClient(
            project=os.getenv("GCP_PROJECT_ID"),
            database=os.getenv("GCP_DATABASE_ID", "cognito-db")
        )
    return _db

SESSIONS_COLLECTION = "cognito_sessions"
MEMORIES_COLLECTION = "cognito_memories"

async def create_session() -> str:
    session_id = str(uuid.uuid4())
    doc = {
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "initializing",
        "goal": None,
        "time_limit_seconds": None,
        "start_time": None,
        "flow_score": 100,
        "distraction_events": [],
        "tab_switch_count": 0,
        "inactivity_streak_seconds": 0,
        "analogy_history": [],
        "state": {
            "socratic_hint_depth": 0,
            "last_tool_called": None,
            "session_phase": "goal_setting"
        }
    }
    await get_db().collection(SESSIONS_COLLECTION).document(session_id).set(doc)
    return session_id

async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    doc_ref = get_db().collection(SESSIONS_COLLECTION).document(session_id)
    doc = await doc_ref.get()
    return doc.to_dict() if doc.exists else None

async def update_session(session_id: str, updates: Dict[str, Any]) -> None:
    await get_db().collection(SESSIONS_COLLECTION).document(session_id).update(updates)

async def append_distraction_event(session_id: str, event: Dict[str, Any]) -> None:
    await get_db().collection(SESSIONS_COLLECTION).document(session_id).update({
        "distraction_events": firestore.ArrayUnion([event])
    })

async def append_analogy(session_id: str, concept: str, image_url: str) -> None:
    entry = {
        "concept": concept, 
        "image_url": image_url, 
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await get_db().collection(SESSIONS_COLLECTION).document(session_id).update({
        "analogy_history": firestore.ArrayUnion([entry])
    })

async def resume_session(prior_session_id: str) -> str:
    prior_session = await get_session(prior_session_id)
    if not prior_session:
        return await create_session()
    
    session_id = str(uuid.uuid4())
    doc = {
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "initializing",
        "goal": prior_session.get("goal"),
        "time_limit_seconds": None,
        "start_time": None,
        "flow_score": 100,
        "distraction_events": [],
        "tab_switch_count": 0,
        "inactivity_streak_seconds": 0,
        "analogy_history": prior_session.get("analogy_history", []),
        "prior_session_id": prior_session_id,
        "state": {
            "socratic_hint_depth": 0,
            "last_tool_called": None,
            "session_phase": "goal_setting"
        }
    }
    await get_db().collection(SESSIONS_COLLECTION).document(session_id).set(doc)
    return session_id

async def get_memory(browser_token: str) -> Optional[Dict[str, Any]]:
    doc_ref = get_db().collection(MEMORIES_COLLECTION).document(browser_token)
    doc = await doc_ref.get()
    return doc.to_dict() if doc.exists else None

async def update_memory(browser_token: str, updates: Dict[str, Any]) -> None:
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    doc_ref = get_db().collection(MEMORIES_COLLECTION).document(browser_token)
    doc = await doc_ref.get()
    if doc.exists:
        await doc_ref.update(updates)
    else:
        full_doc = {
            "browser_token": browser_token,
            "session_count": 0,
            "prior_goals": [],
            "concepts_struggled_with": [],
            "user_profile_context": {
                "expertise_level": "Beginner",
                "preferred_analogy_type": "Visual"
            }
        }
        full_doc.update(updates)
        await doc_ref.set(full_doc)
