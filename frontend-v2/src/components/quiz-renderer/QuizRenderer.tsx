import { useState } from "react";
import type { QuizComponentPayload } from "../../lib/ws-envelope";
import "./quiz-renderer.css";

const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

const OPTION_LETTERS = ["A", "B", "C", "D", "E", "F"];

type Feedback = { correct: boolean; message: string } | null;

type QuizRendererProps = {
  quizzes: QuizComponentPayload[];
  sessionId: string | null;
};

function QuizCard({
  quiz,
  sessionId,
  isActive,
}: {
  quiz: QuizComponentPayload;
  sessionId: string | null;
  isActive: boolean;
}) {
  const [submitted, setSubmitted] = useState(false);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [textValue, setTextValue] = useState("");
  const [feedback, setFeedback] = useState<Feedback>(null);

  const submitAnswer = async (answer: string) => {
    if (!sessionId || submitted) return;
    setSubmitted(true);

    try {
      const res = await fetch(
        `${BACKEND_URL}/api/session/${sessionId}/quiz_answer`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            component_id: quiz.component_id,
            answer,
          }),
        }
      );
      const data = await res.json();
      setFeedback({
        correct: data.correct ?? data.is_correct ?? false,
        message: data.feedback ?? (data.is_correct ? "Correct!" : "Incorrect"),
      });
    } catch {
      setFeedback({ correct: false, message: "Failed to submit answer" });
    }
  };

  const handleOptionClick = (option: string) => {
    if (submitted || !isActive) return;
    setSelectedOption(option);
    submitAnswer(option);
  };

  const handleTextSubmit = () => {
    if (submitted || !isActive || !textValue.trim()) return;
    submitAnswer(textValue.trim());
  };

  const handleReflectionDone = () => {
    if (submitted || !isActive) return;
    submitAnswer(textValue.trim() || "(reflected)");
  };

  return (
    <div className={`quiz-card${!isActive ? " collapsed" : ""}`}>
      <div className="quiz-card__header">
        <span>{quiz.component_type.replace(/_/g, " ")}</span>
      </div>
      <div className="quiz-card__body">
        <div className="quiz-card__question">{quiz.question}</div>

        {quiz.hint && isActive && !submitted && (
          <div className="quiz-card__hint">💡 {quiz.hint}</div>
        )}

        {/* Multiple choice */}
        {quiz.component_type === "multiple_choice" && quiz.options && (
          <div className="quiz-card__options">
            {quiz.options.map((opt, i) => (
              <button
                key={i}
                className={`quiz-card__option-btn${
                  selectedOption === opt ? " selected" : ""
                }`}
                disabled={submitted || !isActive}
                onClick={() => handleOptionClick(opt)}
              >
                <span className="quiz-card__option-letter">
                  {OPTION_LETTERS[i] ?? i + 1}
                </span>
                {opt}
              </button>
            ))}
          </div>
        )}

        {/* True/False */}
        {quiz.component_type === "true_false" && (
          <div className="quiz-card__options">
            {["TRUE", "FALSE"].map((opt) => (
              <button
                key={opt}
                className={`quiz-card__option-btn${
                  selectedOption === opt ? " selected" : ""
                }`}
                disabled={submitted || !isActive}
                onClick={() => handleOptionClick(opt)}
              >
                {opt}
              </button>
            ))}
          </div>
        )}

        {/* Fill in blank */}
        {quiz.component_type === "fill_in_blank" && (
          <div className="quiz-card__input-row">
            <input
              className="quiz-card__text-input"
              type="text"
              placeholder="Type your answer..."
              value={textValue}
              onChange={(e) => setTextValue(e.target.value)}
              disabled={submitted || !isActive}
              onKeyDown={(e) => e.key === "Enter" && handleTextSubmit()}
            />
            <button
              className="quiz-card__submit-btn"
              disabled={submitted || !isActive || !textValue.trim()}
              onClick={handleTextSubmit}
            >
              SUBMIT
            </button>
          </div>
        )}

        {/* Reflection prompt */}
        {quiz.component_type === "reflection_prompt" && (
          <>
            <textarea
              className="quiz-card__textarea"
              placeholder="Write your reflection..."
              value={textValue}
              onChange={(e) => setTextValue(e.target.value)}
              disabled={submitted || !isActive}
            />
            <button
              className="quiz-card__submit-btn"
              disabled={submitted || !isActive}
              onClick={handleReflectionDone}
            >
              DONE — I'VE REFLECTED
            </button>
          </>
        )}

        {/* Feedback */}
        {feedback && (
          <div
            className={`quiz-card__feedback ${
              feedback.correct ? "correct" : "incorrect"
            }`}
          >
            {feedback.correct ? "✓ " : "✗ "}
            {feedback.message}
          </div>
        )}
      </div>
    </div>
  );
}

export default function QuizRenderer({ quizzes, sessionId }: QuizRendererProps) {
  if (quizzes.length === 0) {
    return (
      <div className="quiz-renderer__empty">
        <span
          className="material-symbols-outlined"
          style={{ fontSize: "3rem" }}
        >
          psychology
        </span>
        SOCRATIC QUIZ — WAITING FOR QUESTIONS
      </div>
    );
  }

  return (
    <div className="quiz-renderer">
      {quizzes.map((quiz, i) => (
        <QuizCard
          key={quiz.component_id}
          quiz={quiz}
          sessionId={sessionId}
          isActive={i === 0}
        />
      ))}
    </div>
  );
}
