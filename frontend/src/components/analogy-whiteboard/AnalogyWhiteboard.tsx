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
        <p style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.2em', color: '#777', marginBottom: '16px' }}>Analogies</p>
        <p style={{ fontSize: '12px', textTransform: 'uppercase', color: 'rgba(119,119,119,0.5)', fontStyle: 'italic' }}>Analogy will appear when needed</p>
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
