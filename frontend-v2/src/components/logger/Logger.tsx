import { memo, ReactNode } from "react";
import { useLoggerStore } from "../../lib/store-logger";
import SyntaxHighlighter from "react-syntax-highlighter";
import { vs } from "react-syntax-highlighter/dist/esm/styles/hljs";
import {
  ClientContentLog as ClientContentLogType,
  StreamingLog,
} from "../../types";
import {
  Content,
  LiveClientToolResponse,
  LiveServerContent,
  LiveServerToolCall,
  LiveServerToolCallCancellation,
  Part,
} from "@google/genai";

const formatTime = (d: Date) => d.toLocaleTimeString().slice(0, -3);

// ─── Leaf renderers ────────────────────────────────────────────────────────────

function tryParseCodeExecutionResult(output: string) {
  try { return JSON.stringify(JSON.parse(output), null, 2); } catch { return output; }
}

const RenderPart = memo(({ part }: { part: Part }) => {
  if (part.text?.length) return <span style={{ whiteSpace: "pre-wrap" }}>{part.text}</span>;
  if (part.executableCode) return (
    <div>
      <small style={{ opacity: 0.6 }}>executableCode · {part.executableCode.language}</small>
      <SyntaxHighlighter language={part.executableCode.language!.toLowerCase()} style={vs}>
        {part.executableCode.code!}
      </SyntaxHighlighter>
    </div>
  );
  if (part.codeExecutionResult) return (
    <div>
      <small style={{ opacity: 0.6 }}>result · {part.codeExecutionResult.outcome}</small>
      <SyntaxHighlighter language="json" style={vs}>
        {tryParseCodeExecutionResult(part.codeExecutionResult.output!)}
      </SyntaxHighlighter>
    </div>
  );
  if (part.inlineData) return <small style={{ opacity: 0.6 }}>[ inline data: {part.inlineData.mimeType} ]</small>;
  return null;
});

// ─── Message-level renderers ───────────────────────────────────────────────────

type Msg = { message: StreamingLog["message"] };

const PlainText = ({ message }: Msg) => (
  <span style={{ opacity: 0.65, fontStyle: "italic", fontSize: "0.8rem" }}>{message as string}</span>
);

const ClientContent = memo(({ message }: Msg) => {
  const { turns } = message as ClientContentLogType;
  const parts = turns.filter(p => p.text !== "\n");
  if (!parts.length) return null;
  return (
    <div>
      {parts.map((p, i) => <RenderPart part={p} key={i} />)}
    </div>
  );
});

const ModelTurn = ({ message }: Msg) => {
  const { serverContent } = message as { serverContent: LiveServerContent };
  const { modelTurn } = serverContent as { modelTurn: Content };
  const parts = modelTurn?.parts?.filter(p => p.text !== "\n") ?? [];
  if (!parts.length) return null;
  return <div>{parts.map((p, i) => <RenderPart part={p} key={i} />)}</div>;
};

const ToolCallMsg = memo(({ message }: Msg) => {
  const { toolCall } = message as { toolCall: LiveServerToolCall };
  return (
    <div>
      {toolCall.functionCalls?.map(fc => (
        <div key={fc.id}>
          <small style={{ fontWeight: 700 }}>fn: {fc.name}</small>
          <SyntaxHighlighter language="json" style={vs}>{JSON.stringify(fc.args, null, 2)}</SyntaxHighlighter>
        </div>
      ))}
    </div>
  );
});

const ToolResponse = memo(({ message }: Msg) => (
  <div>
    {(message as LiveClientToolResponse).functionResponses?.map(fc => (
      <div key={fc.id}>
        <small style={{ fontWeight: 700 }}>response: {fc.id}</small>
        <SyntaxHighlighter language="json" style={vs}>{JSON.stringify(fc.response, null, 2)}</SyntaxHighlighter>
      </div>
    ))}
  </div>
));

const ToolCancellation = ({ message }: Msg) => {
  const ids = (message as { toolCallCancellation: LiveServerToolCallCancellation }).toolCallCancellation.ids;
  return <small style={{ opacity: 0.65 }}>cancelled: {ids?.join(", ")}</small>;
};

const AnyMsg = ({ message }: Msg) => (
  <pre style={{ fontSize: "0.7rem", opacity: 0.6, margin: 0 }}>{JSON.stringify(message, null, 2)}</pre>
);

// ─── Dispatch ──────────────────────────────────────────────────────────────────

type MsgComp = (props: { message: StreamingLog["message"] }) => ReactNode;

function resolveComponent(log: StreamingLog): MsgComp {
  if (typeof log.message === "string") return PlainText;
  const m = log.message;
  if ("turns" in m && "turnComplete" in m) return ClientContent;
  if ("toolCall" in m) return ToolCallMsg;
  if ("toolCallCancellation" in m) return ToolCancellation;
  if ("functionResponses" in m) return ToolResponse;
  if ("serverContent" in m) {
    const sc = m.serverContent;
    if (sc?.interrupted) return () => <PlainText message="interrupted" />;
    if (sc?.turnComplete) return () => <PlainText message="turn complete" />;
    if (sc && "modelTurn" in sc) return ModelTurn;
  }
  return AnyMsg;
}

// ─── Log Entry ─────────────────────────────────────────────────────────────────

const SEND_COLOR = "#000";
const RECV_COLOR = "var(--color-gray-800)";

const LogEntry = memo(({ log }: { log: StreamingLog }) => {
  const Comp = resolveComponent(log);
  const isSend = log.type.includes("send");
  const isConversation = (typeof log.message === "object" && log.message !== null) &&
    (("turns" in log.message) || ("serverContent" in log.message));

  return (
    <div style={{
      borderLeft: `3px solid ${isSend ? SEND_COLOR : RECV_COLOR}`,
      paddingLeft: "10px",
      marginBottom: "12px",
      fontSize: "0.82rem",
    }}>
      <div style={{ display: "flex", gap: "8px", marginBottom: "4px", opacity: 0.5, fontSize: "0.7rem" }}>
        <span>{formatTime(log.date)}</span>
        <span style={{ fontWeight: 700 }}>{log.type}</span>
        {log.count && <span>×{log.count}</span>}
      </div>
      <div style={{ fontFamily: "var(--font-primary)" }}>
        <Comp message={log.message} />
      </div>
    </div>
  );
});

// ─── Public API ────────────────────────────────────────────────────────────────

export type LoggerFilterType = "conversations" | "tools" | "none";
export type LoggerProps = { filter: LoggerFilterType };

const filters: Record<LoggerFilterType, (log: StreamingLog) => boolean> = {
  tools: (log) =>
    typeof log.message === "object" && log.message !== null &&
    ("toolCall" in log.message || "functionResponses" in log.message || "toolCallCancellation" in log.message),
  conversations: (log) =>
    typeof log.message === "object" && log.message !== null &&
    (("turns" in log.message && "turnComplete" in log.message) || "serverContent" in log.message),
  none: () => true,
};

export default function Logger({ filter = "none" }: LoggerProps) {
  const { logs } = useLoggerStore();
  return (
    <div style={{ padding: "0.5rem" }}>
      {logs.filter(filters[filter]).map((log, i) => (
        <LogEntry log={log} key={i} />
      ))}
    </div>
  );
}
