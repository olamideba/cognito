import {
  LiveClientToolResponse,
  LiveConnectConfig,
  LiveServerContent,
  LiveServerMessage,
  LiveServerToolCall,
  LiveServerToolCallCancellation,
  Part,
} from "@google/genai";

import { EventEmitter } from "eventemitter3";
import { difference } from "lodash";
import { LiveClientOptions, StreamingLog } from "../types";
import { base64ToArrayBuffer } from "./utils";

export interface LiveClientEventTypes {
  audio: (data: ArrayBuffer) => void;
  close: (event: CloseEvent) => void;
  content: (data: LiveServerContent) => void;
  error: (error: ErrorEvent) => void;
  interrupted: () => void;
  log: (log: StreamingLog) => void;
  open: () => void;
  setupcomplete: () => void;
  toolcall: (toolCall: LiveServerToolCall) => void;
  toolcallcancellation: (
    toolcallCancellation: LiveServerToolCallCancellation
  ) => void;
  turncomplete: () => void;
}

export class GenAILiveClient extends EventEmitter<LiveClientEventTypes> {
  private _url: string;
  private _ws: WebSocket | null = null;

  private _status: "connected" | "disconnected" | "connecting" = "disconnected";
  public get status() {
    return this._status;
  }

  private _model: string | null = null;
  public get model() {
    return this._model;
  }

  protected config: LiveConnectConfig | null = null;
  public getConfig() {
    return { ...this.config };
  }

  constructor(options: LiveClientOptions) {
    super();
    this._url = options.url;
  }

  async connect(model: string, config: LiveConnectConfig): Promise<boolean> {
    if (this._status !== "disconnected") return false;

    this._status = "connecting";
    this._model = model;
    this.config = config;

    return new Promise<boolean>((resolve) => {
      const ws = new WebSocket(this._url);
      this._ws = ws;

      ws.onopen = () => {
        this.log("client.open", "Connected to proxy");
      };

      ws.onmessage = (event: MessageEvent) => {
        let data: LiveServerMessage;
        try {
          data = JSON.parse(event.data as string) as LiveServerMessage;
        } catch {
          console.warn("[proxy-client] unparseable message", event.data);
          return;
        }

        // First message after opening is always setupComplete
        if (data.setupComplete !== undefined) {
          this._status = "connected";
          this.log("server.send", "setupComplete");
          this.emit("setupcomplete");
          this.emit("open");
          resolve(true);
          return;
        }

        this.onmessage(data);
      };

      ws.onerror = (e) => {
        const ev = e as ErrorEvent;
        this.log("server.error", ev.message ?? "WebSocket error");
        this.emit("error", ev);
        if (this._status === "connecting") {
          this._status = "disconnected";
          resolve(false);
        }
      };

      ws.onclose = (e: CloseEvent) => {
        this._status = "disconnected";
        this._ws = null;
        this.log(
          "server.close",
          `disconnected${e.reason ? ` with reason: ${e.reason}` : ""}`
        );
        this.emit("close", e);
      };
    });
  }

  public disconnect() {
    if (!this._ws) return false;
    this._ws.close();
    this._ws = null;
    this._status = "disconnected";
    this.log("client.close", "Disconnected");
    return true;
  }

  protected log(type: string, message: StreamingLog["message"]) {
    this.emit("log", { date: new Date(), type, message });
  }

  protected onmessage(message: LiveServerMessage) {
    if (message.toolCall) {
      this.log("server.toolCall", message);
      this.emit("toolcall", message.toolCall);
      return;
    }

    if (message.toolCallCancellation) {
      this.log("server.toolCallCancellation", message);
      this.emit("toolcallcancellation", message.toolCallCancellation);
      return;
    }

    if (message.serverContent) {
      const { serverContent } = message;

      if ("interrupted" in serverContent) {
        this.log("server.content", "interrupted");
        this.emit("interrupted");
        return;
      }

      if ("turnComplete" in serverContent) {
        this.log("server.content", "turnComplete");
        this.emit("turncomplete");
      }

      if ("modelTurn" in serverContent) {
        let parts: Part[] = serverContent.modelTurn?.parts || [];

        const audioParts = parts.filter(
          (p) => p.inlineData && p.inlineData.mimeType?.startsWith("audio/pcm")
        );
        const base64s = audioParts.map((p) => p.inlineData?.data);
        const otherParts = difference(parts, audioParts);

        base64s.forEach((b64) => {
          if (b64) {
            const data = base64ToArrayBuffer(b64);
            this.emit("audio", data);
            this.log("server.audio", `buffer (${data.byteLength})`);
          }
        });

        if (!otherParts.length) return;

        parts = otherParts;
        this.emit("content", { modelTurn: { parts } });
        this.log("server.content", message);
      }
    } else {
      console.log("[proxy-client] unmatched message", message);
    }
  }

  private _send(payload: object) {
    if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
      console.warn("[proxy-client] attempted send on closed socket");
      return;
    }
    this._ws.send(JSON.stringify(payload));
  }

  sendRealtimeInput(chunks: Array<{ mimeType: string; data: string }>) {
    let hasAudio = false;
    let hasVideo = false;

    for (const ch of chunks) {
      this._send({
        realtimeInput: {
          mediaChunks: [{ mimeType: ch.mimeType, data: ch.data }],
        },
      });
      if (ch.mimeType.includes("audio")) hasAudio = true;
      if (ch.mimeType.includes("image")) hasVideo = true;
    }

    const label =
      hasAudio && hasVideo
        ? "audio + video"
        : hasAudio
        ? "audio"
        : hasVideo
        ? "video"
        : "unknown";
    this.log("client.realtimeInput", label);
  }


  sendToolResponse(toolResponse: LiveClientToolResponse) {
    if (toolResponse.functionResponses?.length) {
      this._send({
        toolResponse: {
          functionResponses: toolResponse.functionResponses,
        },
      });
      this.log("client.toolResponse", toolResponse);
    }
  }


  send(parts: Part | Part[], turnComplete = true) {
    const turns = Array.isArray(parts) ? parts : [parts];
    this._send({
      clientContent: { turns: [{ role: "user", parts: turns }], turnComplete },
    });
    this.log("client.send", { turns, turnComplete });
  }
}
