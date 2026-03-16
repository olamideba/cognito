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

export default function AnalogyWhiteboard({ entries }: AnalogyWhiteboardProps) {
  if (entries.length === 0) {
    return (
      <div className="whiteboard__empty">
        <span
          className="material-symbols-outlined"
          style={{ fontSize: "3rem" }}
        >
          analytics
        </span>
        NO ANALOGIES YET
      </div>
    );
  }

  return (
    <div className="whiteboard">
      {entries.map((entry, i) => (
        <div className="whiteboard__card" key={`${entry.timestamp}-${i}`}>
          <div className="whiteboard__card-header">
            <span className="whiteboard__card-label">
              {entry.concept_label}
            </span>
            <span className="whiteboard__card-time">
              {formatTimestamp(entry.timestamp)}
            </span>
          </div>
          <img
            className="whiteboard__card-image"
            src={entry.image_url}
            alt={entry.concept_label}
          />
        </div>
      ))}
    </div>
  );
}
