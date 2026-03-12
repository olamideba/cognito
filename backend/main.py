import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

load_dotenv()

class LiveToolConfig(BaseModel):
    type: str
    googleSearch: Optional[Dict[str, Any]] = None
    functionDeclarations: Optional[List[Dict[str, Any]]] = None


class LiveConfigResponse(BaseModel):
    model: str
    systemInstruction: str
    tools: List[LiveToolConfig]
    responseModalities: List[str]
    voiceName: str
    apiKey: Optional[str] = None


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


@app.get("/")
def root() -> Dict[str, str]:
    return {"name": "cognito-backend", "version": app.version}


@app.post("/api/live/config", response_model=LiveConfigResponse)
def get_live_config() -> LiveConfigResponse:
    api_key = os.getenv("GEMINI_API_KEY")

    model = os.getenv(
        "COGNITO_MODEL",
        "models/gemini-2.5-flash-native-audio-preview-12-2025",
    )

    system_instruction = os.getenv(
        "COGNITO_SYSTEM_PROMPT",
        (
            "You are Cognito, a flow-state mentor. "
            "Use a Socratic style: ask short, clarifying questions and avoid "
            "dumping full solutions too quickly. "
            "Prioritize keeping the user in a productive flow."
        ),
    )

    tools: List[LiveToolConfig] = [
        LiveToolConfig(type="googleSearch", googleSearch={}),
        LiveToolConfig(
            type="functionDeclarations",
            functionDeclarations=[
                {
                    "name": "render_altair",
                    "description": (
                        "Displays an Altair graph in JSON format in the Cognito console."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "json_graph": {
                                "type": "string",
                                "description": (
                                    "JSON STRING representation of the graph to render. "
                                    "Must be a string, not a JSON object."
                                ),
                            }
                        },
                        "required": ["json_graph"],
                    },
                }
            ],
        ),
    ]

    return LiveConfigResponse(
        model=model,
        systemInstruction=system_instruction,
        tools=tools,
        responseModalities=["AUDIO"],
        voiceName=os.getenv("COGNITO_VOICE_NAME", "Aoede"),
        apiKey=api_key,
    )


def get_genai_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=api_key)

