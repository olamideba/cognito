import { useEffect, useRef, useState } from "react";
import "./Brutalist.css";
import { LiveAPIProvider } from "./contexts/LiveAPIContext";
import SidePanel from "./components/side-panel/SidePanel";
import SessionHeader from "./components/session-header/SessionHeader";
import AnalogyWhiteboard from "./components/analogy-whiteboard/AnalogyWhiteboard";
import type { AnalogyEntry } from "./components/analogy-whiteboard/AnalogyWhiteboard";
import QuizRenderer from "./components/quiz-renderer/QuizRenderer";
import ControlTray from "./components/control-tray/ControlTray";
import cn from "classnames";
// import type { LiveClientOptions } from "./types";
import { fetchLiveConfig } from "./api";
import type {
  CognitoEnvelope,
  SessionInitializedPayload,
  AnalogyGeneratedPayload,
  QuizComponentPayload,
  FlowUpdatePayload,
} from "./lib/ws-envelope";
import { useLiveAPIContext } from "./contexts/LiveAPIContext";
import type { Part } from "@google/genai";

const BACKEND_BASE =
  import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";
const WS_URL = BACKEND_BASE.replace(/^http/, "ws") + "/ws";

const BROWSER_TOKEN_KEY = "cognito_browser_token";
const SESSION_ID_KEY = "cognito_session_id";

function getOrCreateBrowserToken(): string {
  try {
    const existing = localStorage.getItem(BROWSER_TOKEN_KEY);
    if (existing) return existing;
    const created =
      (globalThis.crypto as Crypto | undefined)?.randomUUID?.() ??
      `bt_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
    localStorage.setItem(BROWSER_TOKEN_KEY, created);
    return created;
  } catch {
    return `bt_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
  }
}

function getStoredSessionId(): string | null {
  try {
    return localStorage.getItem(SESSION_ID_KEY);
  } catch {
    return null;
  }
}

function buildWsUrl(): string {
  const url = new URL(WS_URL);
  const browserToken = getOrCreateBrowserToken();
  url.searchParams.set("browser_token", browserToken);
  const sessionId = getStoredSessionId();
  if (sessionId) {
    url.searchParams.set("session_id", sessionId);
  }
  return url.toString();
}

type BackendState = "loading" | "ready" | "error";

// Inner component that has access to LiveAPIContext
export function AppInner() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [_videoStream, setVideoStream] = useState<MediaStream | null>(null);
  const [activeTab, setActiveTab] = useState<"screen" | "whiteboard" | "quiz">(
    "whiteboard"
  );

  // -- Lifted state from envelopes --
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<
    "idle" | "active" | "complete"
  >("idle");
  const [sessionGoal, setSessionGoal] = useState<string | null>(null);
  const [sessionTotalSeconds, setSessionTotalSeconds] = useState<number | null>(
    null
  );
  const [sessionStartTime, setSessionStartTime] = useState<string | null>(null);
  const [analogyEntries, setAnalogyEntries] = useState<AnalogyEntry[]>([]);
  const [quizEntries, setQuizEntries] = useState<QuizComponentPayload[]>([]);
  const [flowScore, setFlowScore] = useState(100);

  const { client } = useLiveAPIContext();

  const handleQuizAnswerSubmitted = (
    quiz: QuizComponentPayload,
    result: {
      answer: string;
      isCorrect: boolean;
      feedback: string;
      status: "validated" | "submission_failed";
    }
  ) => {
    const parts: Part[] = [
      {
        text:
          result.status === "validated"
            ? [
                `The user answered the quiz question: "${quiz.question}"`,
                `Selected answer: "${result.answer}".`,
                `Correct: ${result.isCorrect ? "yes" : "no"}.`,
                `Feedback: ${result.feedback}.`,
                "Respond briefly to the user's selection.",
              ].join(" ")
            : [
                `The user tried to answer the quiz question: "${quiz.question}"`,
                `Selected answer: "${result.answer}".`,
                "The answer submission could not be validated by the backend.",
                "Acknowledge that briefly and continue helping.",
              ].join(" "),
      },
    ];
    client.send(parts, true);
  };

  // Subscribe to envelope events
  useEffect(() => {
    const onEnvelope = (envelope: CognitoEnvelope) => {
      switch (envelope.type) {
        case "session_created":
          setSessionId(envelope.payload.session_id);
          break;

        case "session_initialized": {
          const p = envelope.payload as SessionInitializedPayload;
          setSessionGoal(p.goal);
          setSessionTotalSeconds(p.time_limit_seconds);
          setSessionStartTime(p.start_time);
          setSessionStatus("active");
          break;
        }

        case "analogy_generated": {
          const a = envelope.payload as AnalogyGeneratedPayload;
          setAnalogyEntries((prev) => [
            {
              concept_label: a.concept_label,
              image_url: a.image_url,
              timestamp: a.timestamp,
            },
            ...prev,
          ]);
          setActiveTab("whiteboard");
          break;
        }

        case "quiz_component": {
          const q = envelope.payload as QuizComponentPayload;
          setQuizEntries((prev) => [q, ...prev]);
          setActiveTab("quiz");
          break;
        }

        case "flow_update": {
          const f = envelope.payload as FlowUpdatePayload;
          setFlowScore(f.flow_score);
          break;
        }

        default:
          break;
      }
    };

    client.on("envelope", onEnvelope);
    return () => {
      client.off("envelope", onEnvelope);
    };
  }, [client]);

  return (
    <div className="app-layout">
      <main className="app-main">
        <SidePanel />
        <div className="workspace">
          <SessionHeader
            status={sessionStatus}
            goal={sessionGoal}
            totalSeconds={sessionTotalSeconds}
            startTime={sessionStartTime}
          />
          <div className="context-tabs">
            <button
              className={cn("context-tab", { active: activeTab === "screen" })}
              onClick={() => setActiveTab("screen")}
            >
              <span
                className="material-symbols-outlined"
                style={{
                  fontSize: "1rem",
                  verticalAlign: "middle",
                  marginRight: "6px",
                }}
              >
                present_to_all
              </span>
              Screen View
            </button>
            <button
              className={cn("context-tab", {
                active: activeTab === "whiteboard",
              })}
              onClick={() => setActiveTab("whiteboard")}
            >
              <span
                className="material-symbols-outlined"
                style={{
                  fontSize: "1rem",
                  verticalAlign: "middle",
                  marginRight: "6px",
                }}
              >
                analytics
              </span>
              Analogy Whiteboard
            </button>
            <button
              className={cn("context-tab", { active: activeTab === "quiz" })}
              onClick={() => setActiveTab("quiz")}
            >
              <span
                className="material-symbols-outlined"
                style={{
                  fontSize: "1rem",
                  verticalAlign: "middle",
                  marginRight: "6px",
                }}
              >
                quiz
              </span>
              Socratic Quiz
            </button>
          </div>
          <div className="workspace-content">
            {/* Screen video is always rendered but hidden when not active, so videoRef stays attached */}
            <video
              className={cn("stream")}
              ref={videoRef}
              autoPlay
              playsInline
              style={{
                display: activeTab === "screen" ? "block" : "none",
                width: "100%",
                height: "100%",
                objectFit: "contain",
                border: "3px solid #000",
              }}
            />
            {activeTab === "whiteboard" && (
              <AnalogyWhiteboard entries={analogyEntries} />
            )}
            {activeTab === "quiz" && (
              <QuizRenderer
                quizzes={quizEntries}
                sessionId={sessionId}
                onAnswerSubmitted={handleQuizAnswerSubmitted}
              />
            )}
          </div>
        </div>
      </main>
      <div className="control-bar">
        <ControlTray
          videoRef={videoRef}
          supportsVideo={true}
          onVideoStreamChange={setVideoStream}
          enableEditingSettings={true}
          flowScore={flowScore}
        />
      </div>
    </div>
  );
}

function App() {
  const [backendState, setBackendState] = useState<BackendState>("loading");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    fetchLiveConfig()
      .then(() => setBackendState("ready"))
      .catch((err) => {
        setErrorMessage(err?.message ?? "Cannot connect to backend.");
        setBackendState("error");
      });
  }, []);

  if (backendState === "loading") {
    return (
      <div
        className="App"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          background: "#fff",
        }}
      >
        <div
          style={{
            border: "4px solid #000",
            padding: "2rem 3rem",
            textAlign: "center",
          }}
        >
          <p className="brutalist-h2" style={{ margin: 0 }}>
            CONNECTING TO BACKEND...
          </p>
        </div>
      </div>
    );
  }

  if (backendState === "error") {
    return (
      <div
        className="App"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          background: "#fff",
        }}
      >
        <div
          style={{
            border: "4px solid #000",
            padding: "2rem 3rem",
            textAlign: "center",
            maxWidth: "500px",
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: "3rem" }}
          >
            error
          </span>
          <p className="brutalist-h2" style={{ marginTop: "1rem" }}>
            BACKEND UNAVAILABLE
          </p>
          <p
            className="brutalist-body"
            style={{ marginTop: "0.5rem", fontSize: "0.875rem" }}
          >
            {errorMessage}
          </p>
          <button
            className="brutalist-btn"
            style={{ marginTop: "1.5rem" }}
            onClick={() => {
              setBackendState("loading");
              fetchLiveConfig()
                .then(() => setBackendState("ready"))
                .catch((e) => {
                  setErrorMessage(e?.message ?? "Error");
                  setBackendState("error");
                });
            }}
          >
            RETRY
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <LiveAPIProvider options={{ url: buildWsUrl() }}>
        <AppInner />
      </LiveAPIProvider>
    </div>
  );
}

export default App;
