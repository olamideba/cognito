import { useEffect, useRef, useState } from "react";
import "./settings-dialog.scss";
import { useLiveAPIContext } from "../../contexts/LiveAPIContext";
import VoiceSelector from "./VoiceSelector";

export default function SettingsDialog() {
  const [open, setOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const { connected } = useLiveAPIContext();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    if (open) {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else if (dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <div className="settings-dialog">
      <button
        className="action-button material-symbols-outlined"
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-controls="settings-dialog"
      >
        settings
      </button>
      <dialog
        id="settings-dialog"
        className="dialog"
        ref={dialogRef}
        onClose={() => setOpen(false)}
        onCancel={(event) => {
          setOpen(false);
          event.preventDefault();
        }}
      >
        <div className={`dialog-container ${connected ? "disabled" : ""}`}>
          <div className="dialog-header">
            <div className="dialog-title">Settings</div>
            <button
              className="dialog-close material-symbols-outlined"
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close settings"
            >
              close
            </button>
          </div>
          {connected && (
            <div className="connected-indicator">
              <p>Voice can only be changed before connecting.</p>
            </div>
          )}
          <div className="mode-selectors">
            <VoiceSelector />
          </div>
        </div>
      </dialog>
    </div>
  );
}
