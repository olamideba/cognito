import { useEffect, useRef, useState } from "react";
import "./session-header.css";

type SessionHeaderProps = {
  status: "idle" | "active" | "complete";
  goal: string | null;
  totalSeconds: number | null;
  startTime: string | null;
};

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export default function SessionHeader({
  status,
  goal,
  totalSeconds,
  startTime,
}: SessionHeaderProps) {
  const [remaining, setRemaining] = useState<number | null>(null);
  const [goalExpanded, setGoalExpanded] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (status !== "active" || !startTime || !totalSeconds) {
      setRemaining(null);
      return;
    }

    const tick = () => {
      const start = new Date(startTime).getTime();
      const elapsed = Math.floor((Date.now() - start) / 1000);
      const left = Math.max(0, totalSeconds - elapsed);
      setRemaining(left);
    };

    tick();
    intervalRef.current = setInterval(tick, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [status, startTime, totalSeconds]);

  if (
    status === "complete" ||
    (remaining !== null && remaining <= 0 && status === "active")
  ) {
    return (
      <nav className="session-header">
        <span className="session-header__label">SESSION COMPLETE</span>
      </nav>
    );
  }

  const isWarning =
    remaining !== null &&
    totalSeconds !== null &&
    totalSeconds > 0 &&
    remaining / totalSeconds <= 0.1;

  const displayGoal =
    goal && !goalExpanded && goal.length > 40
      ? goal.slice(0, 40) + "…"
      : goal ?? "--";

  const displayTimer =
    status === "active" && remaining !== null
      ? formatTime(remaining)
      : "--:--:--";

  return (
    <nav className="session-header">
      <span
        className={`session-header__goal${goalExpanded ? " expanded" : ""}`}
        onClick={() => setGoalExpanded((v) => !v)}
        title={goal ?? "Awaiting session goal"}
      >
        SESSION GOAL: {displayGoal}
      </span>
      <span className={`session-header__timer${isWarning ? " warning" : ""}`}>
        {displayTimer}
      </span>
    </nav>
  );
}
