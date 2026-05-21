/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GenAILiveClient, LiveClientCloseEvent } from "../lib/genai-live-client";
import { LiveClientOptions } from "../types";
import { AudioStreamer } from "../lib/audio-streamer";
import { audioContext } from "../lib/utils";
import VolMeterWorket from "../lib/worklets/vol-meter";
import { LiveConnectConfig } from "@google/genai";

const SESSION_ID_KEY = "cognito_session_id";
const MAX_AUTO_RECONNECT_ATTEMPTS = 3;
const AUTO_RECONNECT_DELAY_MS = 1500;

export type UseLiveAPIResults = {
  client: GenAILiveClient;
  setConfig: (config: LiveConnectConfig) => void;
  config: LiveConnectConfig;
  model: string;
  setModel: (model: string) => void;
  connected: boolean;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  volume: number;
  isReconnecting: boolean;
};

export function useLiveAPI(options: LiveClientOptions): UseLiveAPIResults {
  const client = useMemo(() => new GenAILiveClient(options), [options]);
  const audioStreamerRef = useRef<AudioStreamer | null>(null);

  const [model, setModel] = useState<string>(
    "models/gemini-2.5-flash-native-audio-preview-12-2025"
  );
  const [config, setConfig] = useState<LiveConnectConfig>({});
  const [connected, setConnected] = useState(false);
  const [volume, setVolume] = useState(0);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<number | null>(null);
  const autoReconnectEnabledRef = useRef(false);
  const modelRef = useRef(model);
  const configRef = useRef(config);

  useEffect(() => {
    modelRef.current = model;
  }, [model]);

  useEffect(() => {
    configRef.current = config;
  }, [config]);

  // Wire up the audio-out streamer once.
  useEffect(() => {
    if (!audioStreamerRef.current) {
      audioContext({ id: "audio-out" }).then((audioCtx: AudioContext) => {
        audioStreamerRef.current = new AudioStreamer(audioCtx);
        audioStreamerRef.current
          .addWorklet<any>("vumeter-out", VolMeterWorket, (ev: any) => {
            setVolume(ev.data.volume);
          })
          .then(() => {
            // worklet added
          });
      });
    }
  }, [audioStreamerRef]);

  // Subscribe to client events.
  useEffect(() => {
    const clearReconnectTimer = () => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };

    const resetReconnectState = () => {
      clearReconnectTimer();
      reconnectAttemptsRef.current = 0;
      setIsReconnecting(false);
    };

    const scheduleReconnect = () => {
      if (!autoReconnectEnabledRef.current) {
        resetReconnectState();
        return;
      }

      if (reconnectAttemptsRef.current >= MAX_AUTO_RECONNECT_ATTEMPTS) {
        setIsReconnecting(false);
        return;
      }

      reconnectAttemptsRef.current += 1;
      setIsReconnecting(true);
      clearReconnectTimer();

      reconnectTimerRef.current = window.setTimeout(async () => {
        const success = await client.connect(modelRef.current, configRef.current);
        if (!success) {
          scheduleReconnect();
        }
      }, AUTO_RECONNECT_DELAY_MS);
    };

    const onOpen = () => {
      setConnected(true);
      resetReconnectState();
    };
    const onClose = ({ intentional }: LiveClientCloseEvent) => {
      setConnected(false);
      audioStreamerRef.current?.stop();
      if (intentional) {
        resetReconnectState();
        return;
      }
      scheduleReconnect();
    };
    const onError = (error: ErrorEvent) => console.error("error", error);
    const onSessionCreated = (sessionId: string) => {
      try {
        localStorage.setItem(SESSION_ID_KEY, sessionId);
      } catch {
        // ignore storage errors
      }
    };
    const stopAudioStreamer = () => audioStreamerRef.current?.stop();
    const onAudio = (data: ArrayBuffer) =>
      audioStreamerRef.current?.addPCM16(new Uint8Array(data));

    client
      .on("error", onError)
      .on("open", onOpen)
      .on("close", onClose)
      .on("sessioncreated", onSessionCreated)
      .on("interrupted", stopAudioStreamer)
      .on("audio", onAudio);

    return () => {
      autoReconnectEnabledRef.current = false;
      resetReconnectState();
      client
        .off("error", onError)
        .off("open", onOpen)
        .off("close", onClose)
        .off("sessioncreated", onSessionCreated)
        .off("interrupted", stopAudioStreamer)
        .off("audio", onAudio)
        .disconnect();
    };
  }, [client]);

  const connect = useCallback(async () => {
    autoReconnectEnabledRef.current = true;
    if (reconnectTimerRef.current !== null) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    reconnectAttemptsRef.current = 0;
    setIsReconnecting(false);
    client.disconnect();
    // model/config params are accepted by the client for API compat but the
    // proxy already owns the real config; pass them through anyway.
    await client.connect(model, config);
  }, [client, config, model]);

  const disconnect = useCallback(async () => {
    autoReconnectEnabledRef.current = false;
    if (reconnectTimerRef.current !== null) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    reconnectAttemptsRef.current = 0;
    setIsReconnecting(false);
    audioStreamerRef.current?.stop();
    client.disconnect();
    setConnected(false);
  }, [client]);

  return {
    client,
    config,
    setConfig,
    model,
    setModel,
    connected,
    connect,
    disconnect,
    volume,
    isReconnecting,
  };
}
