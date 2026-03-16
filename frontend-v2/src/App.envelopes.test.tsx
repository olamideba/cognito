import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const { fetchLiveConfigMock, mockClient } = vi.hoisted(() => {
  const handlers = new Map<string, Set<(payload: unknown) => void>>();

  const client = {
    on(event: string, handler: (payload: unknown) => void) {
      if (!handlers.has(event)) handlers.set(event, new Set());
      handlers.get(event)!.add(handler);
      return this;
    },
    off(event: string, handler: (payload: unknown) => void) {
      handlers.get(event)?.delete(handler);
      return this;
    },
    emit(event: string, payload: unknown) {
      handlers.get(event)?.forEach((h) => h(payload));
    },
    reset() {
      handlers.clear();
    },
  };

  return {
    fetchLiveConfigMock: vi.fn(),
    mockClient: client,
  };
});

vi.mock("./api", () => ({
  fetchLiveConfig: fetchLiveConfigMock,
}));

vi.mock("./hooks/use-live-api", () => ({
  useLiveAPI: () => ({
    client: mockClient,
    setConfig: vi.fn(),
    config: {},
    model: "models/test",
    setModel: vi.fn(),
    connected: true,
    connect: vi.fn(),
    disconnect: vi.fn(),
    volume: 0,
  }),
}));

vi.mock("./components/side-panel/SidePanel", () => ({
  default: () => <div data-testid="side-panel" />,
}));

vi.mock("./components/control-tray/ControlTray", () => ({
  default: () => <div data-testid="control-tray" />,
}));

describe("App envelope handling", () => {
  beforeEach(() => {
    mockClient.reset();
    fetchLiveConfigMock.mockReset();
    fetchLiveConfigMock.mockResolvedValue({});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders analogy whiteboard entry when analogy_generated envelope arrives", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/GOAL:/)).toBeInTheDocument();
    });

    act(() => {
      mockClient.emit("envelope", {
        type: "analogy_generated",
        payload: {
          concept_label: "Recursion Stack",
          image_url: "data:image/png;base64,abc",
          timestamp: "2026-03-16T12:00:00.000Z",
        },
      });
    });

    expect(screen.getByText("Recursion Stack")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Recursion Stack" })).toHaveAttribute(
      "src",
      "data:image/png;base64,abc"
    );
  });

  it("submits quiz answers using session id from session_created envelope", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      json: async () => ({ is_correct: true, feedback: "Correct!" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/GOAL:/)).toBeInTheDocument();
    });

    act(() => {
      mockClient.emit("envelope", {
        type: "session_created",
        payload: { session_id: "sess-42" },
      });
      mockClient.emit("envelope", {
        type: "quiz_component",
        payload: {
          component_id: "quiz-1",
          component_type: "multiple_choice",
          question: "Which structure is LIFO?",
          options: ["Queue", "Stack"],
        },
      });
    });

    fireEvent.click(await screen.findByRole("button", { name: /Stack/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/session/sess-42/quiz_answer");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(String(init.body))).toEqual({
      component_id: "quiz-1",
      answer: "Stack",
    });
  });
});
