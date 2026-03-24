import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SessionHeader from "./SessionHeader";

describe("SessionHeader", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-03-16T12:00:00.000Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders placeholder header in idle state", () => {
    render(
      <SessionHeader
        status="idle"
        goal={null}
        totalSeconds={null}
        startTime={null}
      />
    );

    expect(screen.getByText(/GOAL:/)).toBeInTheDocument();
    expect(screen.getByText("--:--")).toBeInTheDocument();
  });

  it("renders goal and active countdown", () => {
    render(
      <SessionHeader
        status="active"
        goal="Implement binary search"
        totalSeconds={120}
        startTime="2026-03-16T11:58:30.000Z"
      />
    );

    expect(screen.getByText(/Implement binary search/)).toBeInTheDocument();
    expect(screen.getByText("00:30")).toBeInTheDocument();
  });

  it("applies warning class when remaining time is below 10 percent", () => {
    render(
      <SessionHeader
        status="active"
        goal="Study graphs"
        totalSeconds={100}
        startTime="2026-03-16T11:58:21.000Z"
      />
    );

    expect(screen.getByText("00:01")).toHaveClass("warning");
  });

  it("shows completion state when timer reaches zero", () => {
    render(
      <SessionHeader
        status="active"
        goal="Finish quiz"
        totalSeconds={60}
        startTime="2026-03-16T11:58:00.000Z"
      />
    );

    expect(screen.getByText("SESSION COMPLETE")).toBeInTheDocument();
  });
});
