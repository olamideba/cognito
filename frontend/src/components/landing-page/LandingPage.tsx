import "./LandingPage.css";

interface LandingPageProps {
  /**
   * Called when the user clicks START SESSION.
   * Wire this to the existing session-start / WebSocket handshake flow.
   */
  onStartSession: () => void;
}

export default function LandingPage({ onStartSession }: LandingPageProps) {
  return (
    <div className="landing">
      {/* Grid overlay */}
      <div className="landing__grid" />

      {/* Left accent bar */}
      <div className="landing__accent-bar" />

      {/* ─── Header ─── */}
      <header className="landing__header">
        <div className="landing__brand">COGNITO</div>
        <div className="landing__meta-header">
          <span>VER: 0.0.1_STABLE</span>
        </div>
      </header>

      {/* ─── Main canvas ─── */}
      <main className="landing__main">
        {/* FLOW watermark */}
        <div className="landing__watermark">
          <span className="landing__watermark-text">FLOW</span>
        </div>

        {/* Content */}
        <div className="landing__content">
          {/* Structural divider */}
          <div className="landing__divider" />

          {/* Headline */}
          <h1 className="landing__headline">
            ACHIEVE{" "}
            <span className="landing__headline-break">FLOW STATE</span>
            {" "}WITH COGNITO
          </h1>

          {/* Primary CTA */}
          <div className="landing__cta-wrapper">
            <button
              id="start-session-btn"
              className="landing__cta"
              onClick={onStartSession}
            >
              START SESSION
            </button>
            <div className="landing__cta-outline" />
          </div>

          {/* Technical metadata */}
          <div className="landing__meta-cluster">
            <div className="landing__meta-item">
              <span className="material-symbols-outlined">
                precision_manufacturing
              </span>
              <span>COGNITIVE_CALIBRATION_READY</span>
            </div>
            <div className="landing__meta-item">
              <span className="material-symbols-outlined">memory</span>
              <span>LOW LATENCY</span>
            </div>
            <div className="landing__meta-item">
              <span className="material-symbols-outlined">terminal</span>
              <span>CORE: ACTIVE</span>
            </div>
          </div>
        </div>
      </main>

      {/* ─── Footer ─── */}
      <footer className="landing__footer">
        <div className="landing__footer-left">
          <div className="landing__footer-brand">COGNITO</div>
          <div className="landing__footer-sub">
            by OLAMIDE BALOGUN
          </div>
        </div>
        <div className="landing__footer-right">
          <p>© 2026</p>
        </div>
      </footer>
    </div>
  );
}
