export type SessionCreatedPayload = {
  session_id: string;
};

export type SessionInitializedPayload = {
  session_id: string;
  goal: string;
  time_limit_seconds: number;
  start_time: string;
};

export type AnalogyGeneratedPayload = {
  concept_label: string;
  image_url: string;
  timestamp: string;
};

export type QuizComponentPayload = {
  component_id: string;
  component_type:
    | "multiple_choice"
    | "true_false"
    | "fill_in_blank"
    | "reflection_prompt";
  question: string;
  options?: string[];
  hint?: string;
};

export type FlowUpdatePayload = {
  flow_score: number;
  delta: number;
};

export type TimerTickPayload = {
  elapsed_seconds: number;
  remaining_seconds: number;
  percent_complete: number;
};

export type QuizAnswerResultPayload = {
  component_id: string;
  is_correct: boolean;
};

export type CognitoEnvelope =
  | { type: "session_created"; payload: SessionCreatedPayload }
  | { type: "session_initialized"; payload: SessionInitializedPayload }
  | { type: "analogy_generated"; payload: AnalogyGeneratedPayload }
  | { type: "quiz_component"; payload: QuizComponentPayload }
  | { type: "flow_update"; payload: FlowUpdatePayload }
  | { type: "timer_tick"; payload: TimerTickPayload }
  | { type: "quiz_answer_result"; payload: QuizAnswerResultPayload };

export type CognitoEnvelopeType = CognitoEnvelope["type"];

export type EnvelopeHandlers = {
  [K in CognitoEnvelopeType]?: (
    payload: Extract<CognitoEnvelope, { type: K }>["payload"]
  ) => void;
};

const ENVELOPE_TYPES = new Set<string>([
  "session_created",
  "session_initialized",
  "analogy_generated",
  "quiz_component",
  "flow_update",
  "timer_tick",
  "quiz_answer_result",
]);

export function isCognitoEnvelope(data: unknown): data is CognitoEnvelope {
  if (typeof data !== "object" || data === null) return false;
  const obj = data as Record<string, unknown>;
  return (
    typeof obj.type === "string" &&
    ENVELOPE_TYPES.has(obj.type) &&
    "payload" in obj
  );
}

export function dispatchEnvelope(
  envelope: CognitoEnvelope,
  handlers: EnvelopeHandlers
): void {
  const handler = handlers[envelope.type] as
    | ((payload: unknown) => void)
    | undefined;
  if (handler) handler(envelope.payload);
}
