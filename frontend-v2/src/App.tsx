import { useEffect, useRef, useState } from "react";
import "./Brutalist.css";
import { LiveAPIProvider } from "./contexts/LiveAPIContext";
import SidePanel from "./components/side-panel/SidePanel";
import { Altair } from "./components/altair/Altair";
import ControlTray from "./components/control-tray/ControlTray";
import cn from "classnames";
import type { LiveClientOptions } from "./types";
import { fetchLiveConfig } from "./api";

const BACKEND_BASE =
  import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";
const WS_URL = BACKEND_BASE.replace(/^http/, "ws") + "/ws";

const apiOptions: LiveClientOptions = { url: WS_URL };

type BackendState = "loading" | "ready" | "error";

function App() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [videoStream, setVideoStream] = useState<MediaStream | null>(null);
  const [activeTab, setActiveTab] = useState<"screen" | "whiteboard" | "quiz">("whiteboard");
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
      <div className="App" style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "#fff" }}>
        <div style={{ border: "4px solid #000", padding: "2rem 3rem", textAlign: "center" }}>
          <p className="brutalist-h2" style={{ margin: 0 }}>CONNECTING TO BACKEND...</p>
        </div>
      </div>
    );
  }

  if (backendState === "error") {
    return (
      <div className="App" style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "#fff" }}>
        <div style={{ border: "4px solid #000", padding: "2rem 3rem", textAlign: "center", maxWidth: "500px" }}>
          <span className="material-symbols-outlined" style={{ fontSize: "3rem" }}>error</span>
          <p className="brutalist-h2" style={{ marginTop: "1rem" }}>BACKEND UNAVAILABLE</p>
          <p className="brutalist-body" style={{ marginTop: "0.5rem", fontSize: "0.875rem" }}>{errorMessage}</p>
          <button className="brutalist-btn" style={{ marginTop: "1.5rem" }} onClick={() => { setBackendState("loading"); fetchLiveConfig().then(() => setBackendState("ready")).catch((e) => { setErrorMessage(e?.message ?? "Error"); setBackendState("error"); }); }}>RETRY</button>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <LiveAPIProvider options={apiOptions}>
        <div className="app-layout">
          <main className="app-main">
            <SidePanel />
            <div className="workspace">
              <div className="context-tabs">
                <button
                  className={cn("context-tab", { active: activeTab === "screen" })}
                  onClick={() => setActiveTab("screen")}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: "1rem", verticalAlign: "middle", marginRight: "6px" }}>present_to_all</span>
                  Screen View
                </button>
                <button
                  className={cn("context-tab", { active: activeTab === "whiteboard" })}
                  onClick={() => setActiveTab("whiteboard")}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: "1rem", verticalAlign: "middle", marginRight: "6px" }}>analytics</span>
                  Analogy Whiteboard
                </button>
                <button
                  className={cn("context-tab", { active: activeTab === "quiz" })}
                  onClick={() => setActiveTab("quiz")}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: "1rem", verticalAlign: "middle", marginRight: "6px" }}>quiz</span>
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
                {activeTab === "whiteboard" && <Altair />}
                {activeTab === "quiz" && (
                  <div className="brutalist-h2" style={{ textAlign: "center", width: "100%", opacity: 0.4 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: "3rem", display: "block", marginBottom: "1rem" }}>psychology</span>
                    Socratic Quiz — Coming Soon
                  </div>
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
            />
          </div>
        </div>
      </LiveAPIProvider>
    </div>
  );
}

export default App;
