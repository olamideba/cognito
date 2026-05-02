import logging
from datetime import datetime, timezone
from typing import Any, Optional
from google.cloud import firestore, storage
from google.cloud.storage import Bucket, Blob
from core.config import get_settings, Settings

logger = logging.getLogger(__name__)
settings: Settings = get_settings()
_db: Optional[firestore.AsyncClient] = None
_storage: Optional[storage.Client] = None

def get_db() -> firestore.AsyncClient:
    global _db
    if _db is None:
        _db = firestore.AsyncClient(
            project=settings.GCP_PROJECT_ID,
            database=settings.GCP_DATABASE_ID
        )
    return _db

SESSIONS_COLLECTION = "cognito_sessions"
MEMORIES_COLLECTION = "cognito_memories"

def get_storage_bucket(bucket_name: str) -> Bucket:
    _storage = storage.Client(project=settings.GCP_PROJECT_ID)
    bucket: Bucket = _storage.bucket(bucket_name)
    return bucket

def session_document_ref(session_id: str):
    return get_db().collection(SESSIONS_COLLECTION).document(session_id)


def memory_document_ref(browser_token: str):
    return get_db().collection(MEMORIES_COLLECTION).document(browser_token)


def session_seed_document(
    session_id: str,
    *,
    goal: Optional[str] = None,
    analogy_history: Optional[list[dict[str, Any]]] = None,
    prior_session_id: Optional[str] = None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "initializing",
        "goal": goal,
        "time_limit_seconds": None,
        "start_time": None,
        "flow_score": 100,
        "distraction_events": [],
        "tab_switch_count": 0,
        "inactivity_streak_seconds": 0,
        "analogy_history": analogy_history or [],
        "state": {
            "socratic_hint_depth": 0,
            "last_tool_called": None,
            "session_phase": "goal_setting"
        },
    }
    if prior_session_id is not None:
        doc["prior_session_id"] = prior_session_id
    return doc


def memory_document(browser_token: str) -> dict[str, Any]:
    return {
        "browser_token": browser_token,
        "session_count": 0,
        "prior_goals": [],
        "concepts_struggled_with": [],
        "user_profile_context": {
            "expertise_level": "Beginner",
            "preferred_analogy_type": "Visual",
        },
    }


async def upload_png(image_bytes: bytes, destination_blob_name: str) -> str:
    try:
        bucket: Bucket = get_storage_bucket(bucket_name=settings.GCP_IMAGE_BUCKET)
        blob: Blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(data=image_bytes, content_type="image/png")
        logger.info(f"Image uploaded to gs://{settings.GCP_IMAGE_BUCKET}/{destination_blob_name}")
        return blob.public_url
    except Exception as e:
        logger.error(f"Failed to upload image to bucket: {e}")
        raise
