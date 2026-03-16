import cn from "classnames";

import { memo, type ReactNode, type RefObject, useEffect, useRef, useState } from "react";
import {
  Camera,
  CameraOff,
  Mic,
  MicOff,
  MonitorStop,
  MonitorUp,
  Pause,
  Play,
} from "lucide-react";
import { useLiveAPIContext } from "../../contexts/LiveAPIContext";
import { UseMediaStreamResult } from "../../hooks/use-media-stream-mux";
import { useScreenCapture } from "../../hooks/use-screen-capture";
import { useWebcam } from "../../hooks/use-webcam";
import { AudioRecorder } from "../../lib/audio-recorder";
import SettingsDialog from "../settings-dialog/SettingsDialog";

export type ControlTrayProps = {
  videoRef: RefObject<HTMLVideoElement | null>;
  children?: ReactNode;
  supportsVideo: boolean;
  onVideoStreamChange?: (stream: MediaStream | null) => void;
  enableEditingSettings?: boolean;
};

function ControlTray({
  videoRef,
  children,
  onVideoStreamChange = () => {},
  supportsVideo,
  enableEditingSettings,
}: ControlTrayProps) {
  const videoStreams = [useWebcam(), useScreenCapture()];
  const [activeVideoStream, setActiveVideoStream] =
    useState<MediaStream | null>(null);
  const [webcam, screenCapture] = videoStreams;
  const [inVolume, setInVolume] = useState(0);
  const [audioRecorder] = useState(() => new AudioRecorder());
  const [muted, setMuted] = useState(false);
  const renderCanvasRef = useRef<HTMLCanvasElement>(null);
  const connectButtonRef = useRef<HTMLButtonElement>(null);

  const { client, connected, connect, disconnect } =
    useLiveAPIContext();

  useEffect(() => {
    if (!connected && connectButtonRef.current) {
      connectButtonRef.current.focus();
    }
  }, [connected]);
  useEffect(() => {
    document.documentElement.style.setProperty(
      "--volume",
      `${Math.max(5, Math.min(inVolume * 200, 8))}px`
    );
  }, [inVolume]);

  useEffect(() => {
    const onData = (base64: string) => {
      client.sendRealtimeInput([
        {
          mimeType: "audio/pcm;rate=16000",
          data: base64,
        },
      ]);
    };
    if (connected && !muted && audioRecorder) {
      audioRecorder.on("data", onData).on("volume", setInVolume).start();
    } else {
      audioRecorder.stop();
    }
    return () => {
      audioRecorder.off("data", onData).off("volume", setInVolume);
    };
  }, [connected, client, muted, audioRecorder]);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.srcObject = activeVideoStream;
    }

    let timeoutId = -1;

    function sendVideoFrame() {
      const video = videoRef.current;
      const canvas = renderCanvasRef.current;

      if (!video || !canvas) {
        return;
      }

      const ctx = canvas.getContext("2d")!;
      canvas.width = video.videoWidth * 0.25;
      canvas.height = video.videoHeight * 0.25;
      if (canvas.width + canvas.height > 0 && videoRef.current) {
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const base64 = canvas.toDataURL("image/jpeg", 1.0);
        const data = base64.slice(base64.indexOf(",") + 1, Infinity);
        client.sendRealtimeInput([{ mimeType: "image/jpeg", data }]);
      }
      if (connected) {
        timeoutId = window.setTimeout(sendVideoFrame, 1000 / 0.5);
      }
    }
    if (connected && activeVideoStream !== null) {
      requestAnimationFrame(sendVideoFrame);
    }
    return () => {
      clearTimeout(timeoutId);
    };
  }, [connected, activeVideoStream, client, videoRef]);

  //handler for swapping from one video-stream to the next
  const changeStreams = (next?: UseMediaStreamResult) => async () => {
    if (next) {
      const mediaStream = await next.start();
      setActiveVideoStream(mediaStream);
      onVideoStreamChange(mediaStream);
    } else {
      setActiveVideoStream(null);
      onVideoStreamChange(null);
    }

    videoStreams.filter((msr) => msr !== next).forEach((msr) => msr.stop());
  };

  return (
    <section className="control-tray-brutalist" style={{ display: "flex", width: "100%", justifyContent: "space-between", alignItems: "center" }}>
      <canvas style={{ display: "none" }} ref={renderCanvasRef} />
      <nav className={cn("control-bar-left", { disabled: !connected })} style={{ display: "flex", gap: "1rem" }}>
        {/* Connection Button */}
        <button
          ref={connectButtonRef}
          className={cn("brutalist-btn", "control-tray-btn", {
            connected,
          })}
          onClick={connected ? disconnect : connect}
          title={connected ? "Disconnect mentor" : "Connect mentor"}
          aria-label={connected ? "Disconnect mentor" : "Connect mentor"}
        >
          {connected ? <Pause size={22} /> : <Play size={22} />}
        </button>

        {/* Mic Button */}
        <button
          className={cn("brutalist-btn", "control-tray-btn")}
          onClick={() => setMuted(!muted)}
          title={!muted ? "Mic on" : "Mic off"}
          aria-label={!muted ? "Mic on" : "Mic off"}
        >
          {!muted ? <Mic size={22} /> : <MicOff size={22} />}
        </button>

        {supportsVideo && (
          <>
            <button
              className={cn("brutalist-btn", "control-tray-btn")}
              onClick={
                screenCapture.isStreaming
                  ? changeStreams()
                  : changeStreams(screenCapture)
              }
              title={
                screenCapture.isStreaming ? "Stop screen share" : "Share screen"
              }
              aria-label={
                screenCapture.isStreaming ? "Stop screen share" : "Share screen"
              }
            >
              {screenCapture.isStreaming ? (
                <MonitorStop size={22} />
              ) : (
                <MonitorUp size={22} />
              )}
            </button>
            <button
              className={cn("brutalist-btn", "control-tray-btn")}
              onClick={
                webcam.isStreaming ? changeStreams() : changeStreams(webcam)
              }
              title={webcam.isStreaming ? "Camera off" : "Camera on"}
              aria-label={webcam.isStreaming ? "Camera off" : "Camera on"}
            >
              {webcam.isStreaming ? <CameraOff size={22} /> : <Camera size={22} />}
            </button>
          </>
        )}
        {children}
      </nav>

      <div className="control-bar-right" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span className="brutalist-body" style={{ fontWeight: "bold" }}>FLOW STATE:</span>
          <div style={{ display: "flex", gap: "4px", height: "30px", alignItems: "flex-end" }}>
            <div style={{ width: "12px", height: "10px", backgroundColor: "black" }}></div>
            <div style={{ width: "12px", height: "15px", backgroundColor: "black" }}></div>
            <div style={{ width: "12px", height: "20px", backgroundColor: "black" }}></div>
            <div style={{ width: "12px", height: "25px", border: "3px solid black" }}></div>
            <div style={{ width: "12px", height: "30px", border: "3px solid black" }}></div>
          </div>
        </div>
      </div>
      {enableEditingSettings ? <SettingsDialog /> : ""}
    </section>
  );
}

export default memo(ControlTray);
