import { useState, useRef, useCallback, useEffect } from "react";
import { Expand, X, RotateCcw } from "lucide-react";
import "./analogy-whiteboard.css";

export type AnalogyEntry = {
  concept_label: string;
  image_url: string;
  timestamp: string;
};

type AnalogyWhiteboardProps = {
  entries: AnalogyEntry[];
};

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}



// ── Lightbox ─────────────────────────────────────────────────────────────────
type LightboxProps = {
  entry: AnalogyEntry;
  onClose: () => void;
};

function Lightbox({ entry, onClose }: LightboxProps) {
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const lastPointer = useRef({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Wheel zoom centred on cursor
  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 1.1 : 0.9;
    setScale((s) => Math.min(10, Math.max(0.5, s * delta)));
  }, []);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    dragging.current = true;
    lastPointer.current = { x: e.clientX, y: e.clientY };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragging.current) return;
    const dx = e.clientX - lastPointer.current.x;
    const dy = e.clientY - lastPointer.current.y;
    lastPointer.current = { x: e.clientX, y: e.clientY };
    setOffset((o) => ({ x: o.x + dx, y: o.y + dy }));
  }, []);

  const onPointerUp = useCallback(() => {
    dragging.current = false;
  }, []);

  const resetView = useCallback(() => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  }, []);

  // Pinch-to-zoom via touch
  const lastPinchDist = useRef<number | null>(null);
  const onTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      const dist = Math.hypot(dx, dy);
      if (lastPinchDist.current !== null) {
        const delta = dist / lastPinchDist.current;
        setScale((s) => Math.min(10, Math.max(0.5, s * delta)));
      }
      lastPinchDist.current = dist;
    }
  }, []);
  const onTouchEnd = useCallback(() => {
    lastPinchDist.current = null;
  }, []);

  return (
    <div
      className="lb-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      {/* toolbar */}
      <div className="lb-toolbar">
        <span className="lb-title">{entry.concept_label}</span>
        <div className="lb-actions">
          <button className="lb-btn lb-btn--icon" onClick={resetView} title="Reset view">
            <RotateCcw size={14} />
          </button>
          <button className="lb-btn lb-btn--close lb-btn--icon" onClick={onClose} title="Close (Esc)">
            <X size={16} />
          </button>
        </div>
      </div>

      {/* zoom hint */}
      <div className="lb-hint">Scroll to zoom · Drag to pan · Pinch on touch</div>

      {/* image stage */}
      <div
        ref={containerRef}
        className="lb-stage"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
        style={{ cursor: dragging.current ? "grabbing" : "grab" }}
      >
        <img
          className="lb-image"
          src={entry.image_url}
          alt={entry.concept_label}
          draggable={false}
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
          }}
        />
      </div>

      {/* zoom indicator */}
      <div className="lb-zoom-indicator">{Math.round(scale * 100)}%</div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function AnalogyWhiteboard({ entries }: AnalogyWhiteboardProps) {
  const [lightboxEntry, setLightboxEntry] = useState<AnalogyEntry | null>(null);

  if (entries.length === 0) {
    return (
      <div className="whiteboard__empty">
        <p style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.2em", color: "#777", marginBottom: "16px" }}>
          Analogies
        </p>
        <p style={{ fontSize: "12px", textTransform: "uppercase", color: "rgba(119,119,119,0.5)", fontStyle: "italic" }}>
          Analogy will appear when needed
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="whiteboard">
        {entries.map((entry, i) => (
          <div className="whiteboard__card" key={`${entry.timestamp}-${i}`}>
            <div className="whiteboard__card-header">
              <span className="whiteboard__card-label">{entry.concept_label}</span>
              <span className="whiteboard__card-time">{formatTimestamp(entry.timestamp)}</span>
            </div>

            {/* image wrapper */}
            <div
              className="whiteboard__image-wrap"
              onClick={() => setLightboxEntry(entry)}
              title="Click to inspect"
            >
              <img
                className="whiteboard__card-image"
                src={entry.image_url}
                alt={entry.concept_label}
                draggable={false}
              />
              <button
                className="whiteboard__expand-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setLightboxEntry(entry);
                }}
                aria-label="Expand image"
                title="Expand"
              >
                <Expand size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {lightboxEntry && (
        <Lightbox entry={lightboxEntry} onClose={() => setLightboxEntry(null)} />
      )}
    </>
  );
}
