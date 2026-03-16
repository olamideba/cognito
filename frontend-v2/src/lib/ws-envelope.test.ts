import { describe, expect, it, vi } from "vitest";

import { dispatchEnvelope, isCognitoEnvelope } from "./ws-envelope";

describe("ws-envelope contract", () => {
  it("recognizes backend envelope format for session_created", () => {
    expect(
      isCognitoEnvelope({
        type: "session_created",
        payload: { session_id: "sess-1" },
      })
    ).toBe(true);
  });

  it("dispatches payload to matching handler", () => {
    const handler = vi.fn();
    dispatchEnvelope(
      {
        type: "quiz_component",
        payload: {
          component_id: "quiz-1",
          component_type: "multiple_choice",
          question: "Q?",
          options: ["A", "B"],
        },
      },
      { quiz_component: handler }
    );

    expect(handler).toHaveBeenCalledWith({
      component_id: "quiz-1",
      component_type: "multiple_choice",
      question: "Q?",
      options: ["A", "B"],
    });
  });
});
