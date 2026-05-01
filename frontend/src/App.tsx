import { useEffect, useRef, useState, useSyncExternalStore, useCallback } from "react";
import "./Brutalist.css";
import { LiveAPIProvider } from "./contexts/LiveAPIContext";
import Logger from "./components/logger/Logger";
import SettingsDialog from "./components/settings-dialog/SettingsDialog";
import SessionHeader from "./components/session-header/SessionHeader";
import AnalogyWhiteboard from "./components/analogy-whiteboard/AnalogyWhiteboard";
import type { AnalogyEntry } from "./components/analogy-whiteboard/AnalogyWhiteboard";
import QuizRenderer from "./components/quiz-renderer/QuizRenderer";
import ControlTray from "./components/control-tray/ControlTray";
import LandingPage from "./components/landing-page/LandingPage";
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
import { useLoggerStore } from "./lib/store-logger";
import type { Part } from "@google/genai";
import {
  ArrowUp,
  AudioLines,
  Square,
  PanelLeftClose,
  PanelRightClose,
  Mic,
  Monitor,
  Camera,
  X,
} from "lucide-react";
import { useWebcam } from "./hooks/use-webcam";
import { useScreenCapture } from "./hooks/use-screen-capture";
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

  // Logger / transcript state (lifted from old SidePanel)
  const loggerRef = useRef<HTMLDivElement>(null);
  const loggerLastHeightRef = useRef<number>(-1);
  const { log, logs } = useLoggerStore();
  const [textInput, setTextInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
  const [isConnecting, setIsConnecting] = useState(false);
  const [activeDrawer, setActiveDrawer] = useState<'none' | 'analogy' | 'quiz'>('none');
  const [hasNewAnalogy, setHasNewAnalogy] = useState(false);
  const [hasNewQuiz, setHasNewQuiz] = useState(false);

  const webcam = useWebcam();
  const screenCapture = useScreenCapture();
  const [muted, setMuted] = useState(false);

  const { client, connected, connect, disconnect } = useLiveAPIContext();
  const transcriptPlaceholder = connected
    ? "Optionally send a message ..."
    : "Connect voice to enable chat";
  const hasTextInput = textInput.trim().length > 0;

  useEffect(() => {
    if (connected) {
      setIsConnecting(false);
    }
  }, [connected]);

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
          setHasNewAnalogy(true);
          setActiveDrawer("analogy");
          break;
        }

        case "quiz_component": {
          const q = envelope.payload as QuizComponentPayload;
          setQuizEntries((prev) => [q, ...prev]);
          setHasNewQuiz(true);
          setActiveDrawer("quiz");
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

  // Auto-scroll logger
  useEffect(() => {
    if (loggerRef.current) {
      const el = loggerRef.current;
      const scrollHeight = el.scrollHeight;
      if (scrollHeight !== loggerLastHeightRef.current) {
        el.scrollTop = scrollHeight;
        loggerLastHeightRef.current = scrollHeight;
      }
    }
  }, [logs]);

  // Subscribe to logger events
  useEffect(() => {
    client.on("log", log);
    return () => {
      client.off("log", log);
    };
  }, [client, log]);

  // Text input handler
  const handleSubmit = () => {
    if (!textInput.trim()) return;
    client.send([{ text: textInput }]);
    setTextInput("");
  };

  const handleVoiceConnect = async () => {
    try {
      setIsConnecting(true);
      await connect();
    } catch (error) {
      setIsConnecting(false);
      throw error;
    }
  };

  const handleInputAction = async () => {
    if (!connected) {
      await handleVoiceConnect();
      return;
    }

    if (hasTextInput) {
      handleSubmit();
      return;
    }

    await disconnect();
  };

  const openDrawer = (drawer: 'analogy' | 'quiz') => {
    setActiveDrawer(drawer);
    if (drawer === 'analogy') setHasNewAnalogy(false);
    if (drawer === 'quiz') setHasNewQuiz(false);
  };

  return (
    <div className="app-layout">
      {/* ─── Top Header ─── */}
      <header className="top-header">
        <div className="top-header__brand">
          <a href="/" style={{ color: 'inherit', textDecoration: 'none' }}>COGNITO</a>
        </div>
        <SessionHeader
          status={sessionStatus}
          goal={sessionGoal}
          totalSeconds={sessionTotalSeconds}
          startTime={sessionStartTime}
        />
        <div className="top-header__actions">
          <SettingsDialog />
        </div>
      </header>

      {/* ─── Main 3-Column Area ─── */}
      <main className={`session-main state-${activeDrawer}`}>
        {/* Left Drawer: Analogies */}
        <aside className="session-drawer session-drawer--left">
          {activeDrawer === 'analogy' ? (
            <>
              <button 
                className="drawer-collapse-btn drawer-collapse-btn--left" 
                onClick={() => setActiveDrawer('none')}
                title="Collapse Analogy Window"
              >
                <PanelLeftClose size={22} />
              </button>
              <AnalogyWhiteboard entries={analogyEntries} />
            </>
          ) : (
            <div className="drawer-handle" onClick={() => openDrawer('analogy')}>
              <span>ANALOGIES</span>
            </div>
          )}
        </aside>

        {/* Center Workspace */}
        <section className="session-center">
          <div className="feed-status">
            <span className="feed-status__label">FEED STATUS</span>
            <div className="feed-status__sensors">
              {/* VOICE */}
              <div className={cn("sensor-indicator", { active: connected && !muted })}>
                <span className="sensor-status-dot" aria-hidden="true" />
                <Mic size={16} aria-hidden="true" />
                <span className="sensor-label">VOICE</span>
              </div>
              {/* SCREEN */}
              <div className={cn("sensor-indicator", { active: screenCapture.isStreaming })}>
                <span className="sensor-status-dot" aria-hidden="true" />
                <Monitor size={16} aria-hidden="true" />
                <span className="sensor-label">SCREEN</span>
              </div>
              {/* CAMERA */}
              <div className={cn("sensor-indicator", { active: webcam.isStreaming })}>
                <span className="sensor-status-dot" aria-hidden="true" />
                <Camera size={16} aria-hidden="true" />
                <span className="sensor-label">CAMERA</span>
              </div>
            </div>
          </div>

          {/* Transcript Card */}
          <div className="transcript-card">
            <div className="transcript-card__accent" />
            <header className="transcript-card__header">
              <div>
                <span className="transcript-card__tag">Agent</span>
                <h1 className="transcript-card__title">Session Transcript</h1>
              </div>
            </header>
            <div className="transcript-card__body" ref={loggerRef}>
              <Logger filter="none" />
            </div>

            {/* Text Input */}
            <div
              className={cn("transcript-card__input", {
                disconnected: !connected,
              })}
            >
              <textarea
                ref={inputRef}
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                placeholder={transcriptPlaceholder}
                disabled={!connected}
              />
              <button
                className={cn("transcript-card__action", {
                  connecting: isConnecting && !connected,
                })}
                onClick={() => {
                  void handleInputAction();
                }}
                title={
                  !connected
                    ? isConnecting
                      ? "Connecting voice"
                      : "Connect voice"
                    : hasTextInput
                      ? "Send message"
                      : "Disconnect"
                }
                aria-label={
                  !connected
                    ? isConnecting
                      ? "Connecting voice"
                      : "Connect voice"
                    : hasTextInput
                      ? "Send message"
                      : "Disconnect"
                }
              >
                {!connected ? (
                  <AudioLines size={20} />
                ) : hasTextInput ? (
                  <ArrowUp size={20} />
                ) : (
                  <Square size={18} fill="currentColor" />
                )}
              </button>
            </div>
          </div>

          {/* Video (always rendered for ref, hidden when not capturing) */}
          <video
            className={cn("stream")}
            ref={videoRef}
            autoPlay
            playsInline
            style={{ display: "none" }}
          />
        </section>

        {/* Right Drawer: Quiz */}
        <aside className="session-drawer session-drawer--right">
          {activeDrawer === 'quiz' ? (
            <>
              <button 
                className="drawer-collapse-btn drawer-collapse-btn--right" 
                onClick={() => setActiveDrawer('none')}
                title="Collapse Quiz Window"
              >
                <PanelRightClose size={22} />
              </button>
              <QuizRenderer
                quizzes={quizEntries}
                sessionId={sessionId}
                onAnswerSubmitted={handleQuizAnswerSubmitted}
              />
            </>
          ) : (
            <div className="drawer-handle" onClick={() => openDrawer('quiz')}>
              <span>SOCRATIC QUIZ</span>
            </div>
          )}
        </aside>
      </main>

      {/* ─── Mobile Artifact Triggers (visible <768px) ─── */}
      <div className="mobile-artifact-triggers" role="group" aria-label="Artifacts">
        <button
          type="button"
          className={cn("artifact-trigger", { active: activeDrawer === "analogy" })}
          onClick={() => openDrawer("analogy")}
          aria-label="Open Analogies"
        >
          <span className={cn("artifact-trigger__dot", { on: hasNewAnalogy })} aria-hidden="true" />
          ANALOGIES
        </button>
        <button
          type="button"
          className={cn("artifact-trigger", { active: activeDrawer === "quiz" })}
          onClick={() => openDrawer("quiz")}
          aria-label="Open Socratic Check-in"
        >
          <span className={cn("artifact-trigger__dot", { on: hasNewQuiz })} aria-hidden="true" />
          SOCRATIC CHECKIN
        </button>
      </div>

      {/* ─── Mobile Slide-Up Sheet (visible <768px) ─── */}
      <section
        className={cn("artifact-sheet", { open: activeDrawer !== "none" })}
        aria-hidden={activeDrawer === "none"}
      >
        {activeDrawer !== "none" ? (
          <>
            <header className="artifact-sheet__header">
              <div className="artifact-sheet__title">
                {activeDrawer === "analogy"
                  ? "ANALOGIES"
                  : activeDrawer === "quiz"
                    ? "SOCRATIC CHECKIN"
                    : ""}
              </div>
              <button
                type="button"
                className="artifact-sheet__close"
                onClick={() => setActiveDrawer("none")}
                aria-label="Close"
                title="Close"
              >
                <X size={20} aria-hidden="true" />
              </button>
            </header>
            <div className="artifact-sheet__body">
              {activeDrawer === "analogy" ? (
                <AnalogyWhiteboard entries={analogyEntries} />
              ) : (
                <QuizRenderer
                  quizzes={quizEntries}
                  sessionId={sessionId}
                  onAnswerSubmitted={handleQuizAnswerSubmitted}
                />
              )}
            </div>
          </>
        ) : null}
      </section>

      {/* ─── Control Bar ─── */}
      <div className="control-bar">
        <ControlTray
          videoRef={videoRef}
          supportsVideo={true}
          onVideoStreamChange={setVideoStream}
          enableEditingSettings={false}
          flowScore={flowScore}
          webcam={webcam}
          screenCapture={screenCapture}
          muted={muted}
          setMuted={setMuted}
        />
      </div>
    </div>
  );
}

/* ─── Lightweight path router (no extra dependency) ─── */
function subscribeToLocation(cb: () => void) {
  window.addEventListener("popstate", cb);
  return () => window.removeEventListener("popstate", cb);
}

function getLocationPath() {
  return window.location.pathname;
}

function useLocationPath() {
  return useSyncExternalStore(subscribeToLocation, getLocationPath);
}

function App() {
  const pathname = useLocationPath();
  const [backendState, setBackendState] = useState<BackendState>("loading");
  const [errorMessage, setErrorMessage] = useState("");

  const checkBackend = useCallback(() => {
    setBackendState("loading");
    fetchLiveConfig()
      .then(() => setBackendState("ready"))
      .catch((err) => {
        setErrorMessage(err?.message ?? "Cannot connect to backend.");
        setBackendState("error");
      });
  }, []);

  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  /* ── Landing page (no backend dependency) ── */
  if (pathname === "/" || (!pathname.startsWith("/workspace"))) {
    return (
      <div className="App">
        <LandingPage />
      </div>
    );
  }

  /* ── Workspace: needs backend ── */
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
            onClick={checkBackend}
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
