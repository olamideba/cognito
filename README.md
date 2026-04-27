# Cognito - Live Agentic Flow-State Mentor

A real-time multimodal learning coach built with a React frontend and a FastAPI backend using Google ADK + Gemini Live. The app helps users stay in flow while learning by combining live voice interaction, screen/webcam context, Socratic quiz checks, and visual analogy generation.

## Overview

This project delivers an end-to-end agentic tutoring experience:

1. **Real-time session start**: Frontend connects to backend WebSocket and receives a persistent `session_id`
2. **Multimodal streaming**: User audio + optional screen/webcam frames stream to backend in real time
3. **Agentic guidance loop**: ADK agent uses tools to set goals, track time, assess understanding, and coach flow state
4. **Interactive UI updates**: Backend sends envelope events (`session_initialized`, `quiz_component`, `analogy_generated`, `flow_update`) to render components live
5. **Persistent memory/state**: Session and user memory are stored in Google Cloud Firestore

## Features

- **Live bidirectional mentor session** over WebSocket (`/ws`)
- **Voice-first interaction** with Gemini native audio model
- **Socratic quiz components** (multiple choice, true/false, fill-in, reflection)
- **Analogy whiteboard generation** (image generation endpoint + UI rendering)
- **Flow-state meter** updated from user behavioral signals
- **Session timer + goal tracking** with reconnect/resume support
- **Google Search tool integration** via ADK tool-enabled agent

## Architecture

```text
┌────────────────────────────┐
│        Frontend (Vite)     │
│ React + TS + audio/video   │
└──────────────┬─────────────┘
               │ HTTP + WS
               ▼
┌────────────────────────────┐
│      Backend (FastAPI)     │
│ /api/live/config, /ws,     │
│ /api/session, /api/generate│
└──────────────┬─────────────┘
               │
     ┌─────────┴─────────┐
     ▼                   ▼
┌───────────────┐   ┌──────────────────┐
│ Google ADK +  │   │ Firestore        │
│ Gemini Live   │   │ sessions/memory  │
│ (tools/agent) │   │ persistence      │
└───────────────┘   └──────────────────┘
```

## Tech Stack

- **Frontend**: React 19, TypeScript, Vite, Sass, Vitest
- **Backend**: FastAPI, Uvicorn, Google ADK, Google GenAI SDK
- **Cloud/Data**: Google Cloud Firestore
- **AI Models**:
  - Live voice: `gemini-2.5-flash-native-audio-preview-12-2025`
  - Image generation: `gemini-2.5-flash-preview-image-generation`

## Data Sources Used

- User-provided multimodal input:
  - Microphone audio
  - Screen-share and webcam frames
  - User quiz answers and goals
- Google Search tool results from ADK tool calls
- Firestore-stored session state and memory documents

## Project Structure

```text
.
├── backend/
│   ├── main.py
│   ├── agent.py
│   ├── routers/
│   ├── core/
│   └── tools/
├── frontend/
│   ├── src/
│   └── package.json
└── README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- `uv` (recommended for backend dependency management)
- Google Cloud project with Firestore enabled
- Gemini API key

## Setup

### 1. Backend

```bash
cd backend
uv sync
```

Create `backend/.env`:

```bash
# Required
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GCP_PROJECT_ID=YOUR_GCP_PROJECT_ID

# Optional
GCP_DATABASE_ID=cognito-db
COGNITO_MODEL=gemini-2.5-flash-native-audio-preview-12-2025
COGNITO_IMAGE_MODEL=gemini-2.5-flash-preview-image-generation
COGNITO_VOICE_NAME=Aoede
LOG_LEVEL=INFO
```

Run backend:

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/healthz
```

### 2. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```bash
VITE_BACKEND_URL=http://localhost:8000
```

Run frontend:

```bash
npm run dev
```

Open the app URL shown by Vite (typically `http://localhost:5173`).

## API Surface (Backend)

- `POST /api/live/config` - returns model/system/tools config for client setup
- `GET /healthz` - health check
- `GET /api/session/{session_id}` - fetch session state
- `POST /api/session/{session_id}/quiz_answer` - submit quiz answers
- `GET /api/memory/{browser_token}` - fetch browser memory profile
- `POST /api/generate/analogy` - generate an analogy image
- `WS /ws` - real-time streaming endpoint

## License

Apache 2.0 - See [LICENSE](/home/mujeeb-gh/repos/cognito/LICENSE).