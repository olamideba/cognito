import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import session as session_router
from routers import memory as memory_router
from routers import generate as generate_router
from routers import live as live_router

from core.config import get_settings, Settings

settings: Settings = get_settings()

log_file_handler = RotatingFileHandler(
    filename="app.log",
    maxBytes=5*1024*1024, # 5mb
    backupCount=2
)
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[log_file_handler, logging.StreamHandler()],
)

load_dotenv()

app = FastAPI(title="Cognito Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


app.include_router(session_router.router)
app.include_router(memory_router.router)
app.include_router(generate_router.router)
app.include_router(live_router.router)


@app.get("/")
def root() -> Dict[str, str]:
    return {"name": "cognito-backend", "version": app.version}


@app.websocket("/ws")
async def websocket_proxy(
    ws: WebSocket, session_id: Optional[str] = None, browser_token: Optional[str] = None, voice_name: Optional[str] = None
):
    from domains.live_session.module import run_live_session

    await run_live_session(
        ws=ws,
        session_id=session_id,
        browser_token=browser_token,
        voice_name=voice_name,
    )
