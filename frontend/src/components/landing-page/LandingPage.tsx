import { useEffect } from "react";
import "./LandingPage.css";
import {
  CircleHelp,
  Wrench,
  Target,
  Focus,
  Zap,
  BookOpen,
  Cpu,
  Eye,
  Activity,
  Github,
  Linkedin,
  Mail,
  ArrowRight
} from "lucide-react";
import { FaXTwitter } from "react-icons/fa6";

export default function LandingPage() {
  useEffect(() => {
    const { documentElement, body } = document;
    const prevHtmlOverflow = documentElement.style.overflow;
    const prevHtmlScrollBehavior = documentElement.style.scrollBehavior;
    const prevBodyOverflow = body.style.overflow;
    const prevBodyScrollBehavior = body.style.scrollBehavior;

    documentElement.style.overflow = "auto";
    documentElement.style.scrollBehavior = "smooth";
    body.style.overflow = "auto";
    body.style.scrollBehavior = "smooth";

    return () => {
      documentElement.style.overflow = prevHtmlOverflow;
      documentElement.style.scrollBehavior = prevHtmlScrollBehavior;
      body.style.overflow = prevBodyOverflow;
      body.style.scrollBehavior = prevBodyScrollBehavior;
    };
  }, []);

  return (
    <div className="landing">
      {/* Grid overlay */}
      <div className="landing__grid" />

      {/* Left accent bar */}
      <div className="landing__accent-bar" />

      {/* ─── 0. Navigation Bar (Sticky Header) ─── */}
      <header className="landing__header">
        <a href="/" className="landing__brand">COGNITO</a>
        <nav className="landing__nav-links">
          <a href="#how-it-works">How it Works</a>
          <a href="#demo">Demo</a>
          <a href="#specs">Specs</a>
          <a href="https://github.com/olamideba/cognito" target="_blank" rel="noreferrer">GitHub</a>
        </nav>
        <div className="landing__header-right">
          <a href="/workspace" className="landing__header-cta">
            TRY IT
          </a>
        </div>
      </header>

      <main className="landing__main">
        {/* ─── 1. Hero Section (The Hook) ─── */}
        <section className="landing__hero">


          <div className="landing__content">
            {/* FLOW watermark */}
            <div className="landing__watermark">
              <span className="landing__watermark-text">FLOW</span>
            </div>
            {/* Structural divider */}
            <div className="landing__divider" />

            {/* Headline */}
            <h1 className="landing__headline">
              ENTER FLOW WITH{" "}
              <span className="landing__headline-highlight">COGNITO</span>
            </h1>

            {/* Sub-headline */}
            <p className="landing__sub-headline">
              A multimodal mentor that watches your back so you can stay in the zone.
            </p>

            {/* CTAs */}
            <div className="landing__hero-actions">
              <div className="landing__cta-wrapper">
                <a
                  id="start-session-btn"
                  className="landing__cta"
                  href="/workspace"
                >
                  TRY IT
                </a>
                <div className="landing__cta-outline" />
              </div>
              <a href="#demo" className="landing__cta landing__cta--secondary">
                WATCH DEMO
              </a>
            </div>
          </div>
        </section>

        {/* ─── 2 & 3. Problem & Solution ─── */}
        <section className="landing__section" id="problem-solution">
          <div className="landing__section-header">
            <div className="landing__section-kicker">Problem / Solution</div>
            <h2 className="landing__section-title landing__section-title--sentence">
              Information is cheap. Focus is expensive.
            </h2>
            <p className="landing__section-copy">
              Cognito is built for the moments where minor confusion turns into
              lost momentum.
            </p>
          </div>
          <div className="landing__grid-container landing__grid-2">
            <div className="landing__card">
              <div className="landing__card-icon">
                <CircleHelp size={32} strokeWidth={1.5} />
              </div>
              <h3 className="landing__card-title">THE PROBLEM</h3>
              <p className="landing__card-body">
                Information is cheap. Focus is expensive. Learning complex
                systems is often derailed by "micro-stalls"—minor confusions
                that lead to tab-switching and flow-breaking distractions.
              </p>
            </div>

            <div className="landing__card">
              <div className="landing__card-icon">
                <Wrench size={32} strokeWidth={1.5} />
              </div>
              <h3 className="landing__card-title">THE FIX</h3>
              <p className="landing__card-body">
                An AI Companion, Not a Chatbox. Cognito doesn't just answer
                questions; it monitors your learning state. It provides
                scaffolding when you stumble and silence when you're soaring.
              </p>
            </div>
          </div>
        </section>

        {/* ─── 4. Demo Section ─── */}
        <section className="landing__section" id="demo">
          <div className="landing__section-header">
            <div className="landing__section-kicker">Demo</div>
            <h2 className="landing__section-title landing__section-title--sentence">
              See the system at work.
            </h2>
          </div>
          <div className="landing__demo-placeholder">
            <iframe
              src="https://www.loom.com/embed/3cf7f8e72b494589a3e872a08f19e154"
              allowFullScreen
              style={{ width: "100%", height: "100%", border: "none" }}
              title="Cognito Demo"
            />
          </div>
        </section>

        {/* ─── 5. How It Works: The Flow Cycle ─── */}
        <section className="landing__section" id="how-it-works">
          <div className="landing__watermark">
            <span className="landing__watermark-text">FLOW</span>
          </div>
          <div className="landing__section-header">
            <div className="landing__section-kicker">How It Works</div>
            <h2 className="landing__section-title">THE FLOW CYCLE</h2>
            <p className="landing__section-copy">
              A structured sequence designed to preserve momentum and intervene
              only when needed.
            </p>
          </div>
          <div className="landing__grid-container landing__grid-4">
            {/* Step 1 */}
            <div className="landing__card landing__flow-step">
              <div className="landing__card-icon">
                <Target size={32} strokeWidth={1.5} />
              </div>
              <h3 className="landing__card-title">1. Set Perimeter</h3>
              <p className="landing__card-body">
                Define your goal and timer. Cognito locks the session to your
                specific objective.
              </p>
              <ArrowRight className="landing__flow-arrow" size={24} />
            </div>

            {/* Step 2 */}
            <div className="landing__card landing__flow-step">
              <div className="landing__card-icon">
                <Focus size={32} strokeWidth={1.5} />
              </div>
              <h3 className="landing__card-title">2. Shared Context</h3>
              <p className="landing__card-body">
                Enable optional screen and camera sharing to let Cognito "read
                over your shoulder."
              </p>
              <ArrowRight className="landing__flow-arrow" size={24} />
            </div>

            {/* Step 3 */}
            <div className="landing__card landing__flow-step">
              <div className="landing__card-icon">
                <Activity size={32} strokeWidth={1.5} />
              </div>
              <h3 className="landing__card-title">3. Intervention</h3>
              <p className="landing__card-body">
                Visual aids or Socratic quizzes appear dynamically—only when
                your momentum drops.
              </p>
              <ArrowRight className="landing__flow-arrow" size={24} />
            </div>

            {/* Step 4 */}
            <div className="landing__card landing__flow-step">
              <div className="landing__card-icon">
                <BookOpen size={32} strokeWidth={1.5} />
              </div>
              <h3 className="landing__card-title">4. Synthesis</h3>
              <p className="landing__card-body">
                Wrap up with structured logs of your breakthroughs and saved
                artifacts.
              </p>
            </div>
          </div>
        </section>

        {/* ─── 6. Technical Breakdown ─── */}
        <section className="landing__section" id="specs">
          <div className="landing__section-header">
            <div className="landing__section-kicker">Specs</div>
            <h2 className="landing__section-title">TECHNICAL BREAKDOWN</h2>
            <p className="landing__section-copy">
              Low-latency voice, live vision context, and adaptive artifacts
              working together in one learning loop.
            </p>
          </div>
          <div className="landing__grid-container landing__grid-3">
            <div className="landing__card">
              <div className="landing__card-icon">
                <Zap size={32} strokeWidth={1.5} />
              </div>
              <h3 className="landing__card-title">MULTIMODAL LATENCY</h3>
              <p className="landing__card-body">
                Low-latency voice interaction via the Gemini Live API for
                natural, hands-free learning.
              </p>
            </div>

            <div className="landing__card">
              <div className="landing__card-icon">
                <Eye size={32} strokeWidth={1.5} />
              </div>
              <h3 className="landing__card-title">VISION ENGINE</h3>
              <p className="landing__card-body">
                Real-time processing of screen share and optional camera data to
                gauge focus and context.
              </p>
            </div>

            <div className="landing__card">
              <div className="landing__card-icon">
                <Cpu size={32} strokeWidth={1.5} />
              </div>
              <h3 className="landing__card-title">ADAPTIVE ARTIFACTS</h3>
              <p className="landing__card-body">
                Dynamic generation of visual analogies and Socratic quizzes,
                triggered seamlessly to break through learning walls.
              </p>
            </div>
          </div>
        </section>

        {/* ─── 7. Contact ─── */}
        <section className="landing__section" id="contact">
          <div className="landing__watermark">
            <span className="landing__watermark-text">FLOW</span>
          </div>
          <div className="landing__contact-shell">
            <div className="landing__section-header landing__contact-header">
              <div className="landing__section-kicker landing__contact-kicker">Contact</div>
              <h2 className="landing__section-title landing__section-title--sentence landing__contact-title">Say hi to Olamide.</h2>
              <p className="landing__section-copy landing__contact-copy">
                AI engineer building practical, intelligent systems. Open to
                feedback, bug reports, and collaboration.
              </p>
            </div>

            <div className="landing__contact-grid">
              <a
                className="landing__contact-link"
                href="mailto:olamideba174@gmail.com"
              >
                <span className="landing__contact-link-icon" aria-hidden="true">
                  <Mail size={22} />
                </span>
                <span className="landing__contact-link-copy">
                  <span className="landing__contact-link-label">Email</span>
                  <span className="landing__contact-link-value">
                    olamideba174@gmail.com
                  </span>
                </span>
                <span className="landing__contact-link-arrow" aria-hidden="true">
                  <ArrowRight size={20} />
                </span>
              </a>

              <a
                className="landing__contact-link"
                href="https://www.linkedin.com/olamideba"
                target="_blank"
                rel="noreferrer"
              >
                <span className="landing__contact-link-icon" aria-hidden="true">
                  <Linkedin size={22} />
                </span>
                <span className="landing__contact-link-copy">
                  <span className="landing__contact-link-label">LinkedIn</span>
                  <span className="landing__contact-link-value">@olamideba</span>
                </span>
                <span className="landing__contact-link-arrow" aria-hidden="true">
                  <ArrowRight size={20} />
                </span>
              </a>

              <a
                className="landing__contact-link"
                href="https://github.com/olamideba"
                target="_blank"
                rel="noreferrer"
              >
                <span className="landing__contact-link-icon" aria-hidden="true">
                  <Github size={22} />
                </span>
                <span className="landing__contact-link-copy">
                  <span className="landing__contact-link-label">GitHub</span>
                  <span className="landing__contact-link-value">@olamideba</span>
                </span>
                <span className="landing__contact-link-arrow" aria-hidden="true">
                  <ArrowRight size={20} />
                </span>
              </a>

              <a
                className="landing__contact-link"
                href="https://x.com/nenja_mj"
                target="_blank"
                rel="noreferrer"
              >
                <span className="landing__contact-link-icon" aria-hidden="true">
                  <FaXTwitter size={20} />
                </span>
                <span className="landing__contact-link-copy">
                  <span className="landing__contact-link-label">X</span>
                  <span className="landing__contact-link-value">@nenja_mj</span>
                </span>
                <span className="landing__contact-link-arrow" aria-hidden="true">
                  <ArrowRight size={20} />
                </span>
              </a>
            </div>
          </div>
        </section>

        {/* ─── 8. Final CTA Section ─── */}
        <section className="landing__section h-auto">
          <h2 className="landing__section-title" style={{ marginBottom: "2rem" }}>
            Master your focus.
          </h2>
          <div className="landing__hero-actions" style={{ marginBottom: "0" }}>
            <div className="landing__cta-wrapper">
              <a className="landing__cta" href="/workspace">
                TRY IT
              </a>
              <div className="landing__cta-outline" />
            </div>
            <a
              href="https://github.com/olamideba/cognito"
              target="_blank"
              rel="noreferrer"
              className="landing__cta landing__cta--secondary"
            >
              STAR ON GITHUB
            </a>
          </div>
        </section>
      </main>

      {/* ─── 9. Footer ─── */}
      <footer className="landing__footer">
        <div className="landing__footer-left">
          <div className="landing__footer-brand">COGNITO</div>
          <div className="landing__footer-sub">BY OLAMIDE BALOGUN</div>
        </div>
        <div className="landing__footer-right">
          <p>© 2026</p>
        </div>
      </footer>
    </div>
  );
}
