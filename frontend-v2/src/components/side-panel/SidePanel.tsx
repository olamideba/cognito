import cn from "classnames";
import { useEffect, useRef, useState } from "react";
import { useLiveAPIContext } from "../../contexts/LiveAPIContext";
import { useLoggerStore } from "../../lib/store-logger";
import Logger from "../logger/Logger";

export default function SidePanel() {
  const { connected, client } = useLiveAPIContext();
  const loggerRef = useRef<HTMLDivElement>(null);
  const loggerLastHeightRef = useRef<number>(-1);
  const { log, logs } = useLoggerStore();

  const [textInput, setTextInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new logs
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

  useEffect(() => {
    client.on("log", log);
    return () => {
      client.off("log", log);
    };
  }, [client, log]);

  const handleSubmit = () => {
    client.send([{ text: textInput }]);
    setTextInput("");
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">Cognito</div>
        <div className="sidebar-title">
          <span className="material-symbols-outlined">chat</span>
          Mentor Transcript
          <span
            className={cn("connection-badge", { connected })}
            style={{
              marginLeft: "auto",
              fontSize: "0.65rem",
              padding: "2px 8px",
              border: "2px solid #000",
              background: connected ? "#000" : "transparent",
              color: connected ? "#fff" : "#000",
            }}
          >
            {connected ? "● LIVE" : "○ IDLE"}
          </span>
        </div>
      </div>

      <div className="sidebar-bottom" ref={loggerRef}>
        <Logger filter="none" />
      </div>

      {/* Text input to send messages */}
      <div className={cn("sidebar-input", { disabled: !connected })}>
        <textarea
          style={{
            flex: 1,
            resize: "none",
            height: "60px",
            fontFamily: "var(--font-primary)",
            border: "none",
            outline: "none",
            background: "transparent",
            fontSize: "0.875rem",
            padding: "0.5rem",
          }}
          ref={inputRef}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          onChange={(e) => setTextInput(e.target.value)}
          value={textInput}
          placeholder="Send a message..."
        />
        <button
          onClick={handleSubmit}
          style={{
            background: "#000",
            color: "#fff",
            border: "none",
            padding: "0 1rem",
            cursor: "pointer",
            fontFamily: "var(--font-primary)",
            fontWeight: 700,
            textTransform: "uppercase",
            fontSize: "0.75rem",
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: "1.2rem" }}>send</span>
        </button>
      </div>
    </div>
  );
}
