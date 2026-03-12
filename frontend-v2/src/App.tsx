import { useEffect, useRef, useState } from "react";
import "./App.scss";
import { LiveAPIProvider } from "./contexts/LiveAPIContext";
import SidePanel from "./components/side-panel/SidePanel";
import { Altair } from "./components/altair/Altair";
import ControlTray from "./components/control-tray/ControlTray";
import cn from "classnames";
import type { LiveClientOptions } from "./types";
import { fetchLiveConfig } from "./api";

function App() {
  const [apiOptions, setApiOptions] = useState<LiveClientOptions | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [videoStream, setVideoStream] = useState<MediaStream | null>(null);

  useEffect(() => {
    fetchLiveConfig()
      .then((cfg) => {
        if (!cfg.apiKey) {
          throw new Error("Backend did not return an API key");
        }
        setApiOptions({ apiKey: cfg.apiKey });
      })
      .catch((err: unknown) => {
        setConfigError(
          err instanceof Error ? err.message : "Failed to load backend config",
        );
      });
  }, []);

  return (
    <div className="App">
      {configError && (
        <div className="config-error">
          Failed to load backend configuration: {configError}
        </div>
      )}
      {apiOptions && (
        <LiveAPIProvider options={apiOptions}>
        <div className="streaming-console">
          <SidePanel />
          <main>
            <div className="main-app-area">
              <Altair />
              <video
                className={cn("stream", {
                  hidden: !videoRef.current || !videoStream,
                })}
                ref={videoRef}
                autoPlay
                playsInline
              />
            </div>
            <ControlTray
              videoRef={videoRef}
              supportsVideo={true}
              onVideoStreamChange={setVideoStream}
              enableEditingSettings={true}
            >
              {/* custom control buttons can go here */}
            </ControlTray>
          </main>
        </div>
      </LiveAPIProvider>
      )}
    </div>
  );
}

export default App;
