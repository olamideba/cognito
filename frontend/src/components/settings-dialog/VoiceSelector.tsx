import { useCallback, useEffect, useRef, useState } from "react";
import Select from "react-select";
import { useLiveAPIContext } from "../../contexts/LiveAPIContext";

const voiceOptions = [
  { value: "Puck", label: "Puck" },
  { value: "Charon", label: "Charon" },
  { value: "Kore", label: "Kore" },
  { value: "Fenrir", label: "Fenrir" },
  { value: "Aoede", label: "Aoede" },
];

export default function VoiceSelector() {
  const { config, setConfig } = useLiveAPIContext();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [menuPortalTarget, setMenuPortalTarget] = useState<HTMLElement | null>(
    null
  );

  useEffect(() => {
    const voiceName =
      config.speechConfig?.voiceConfig?.prebuiltVoiceConfig?.voiceName ||
      "Atari02";
    const voiceOption = { value: voiceName, label: voiceName };
    setSelectedOption(voiceOption);
  }, [config]);

  useEffect(() => {
    setMenuPortalTarget(containerRef.current?.closest("dialog") ?? null);
  }, []);

  const [selectedOption, setSelectedOption] = useState<{
    value: string;
    label: string;
  } | null>(voiceOptions[0]);

  const updateConfig = useCallback(
    (voiceName: string) => {
      setConfig({
        ...config,
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: {
              voiceName: voiceName,
            },
          },
        },
      });
    },
    [config, setConfig]
  );

  return (
    <div className="select-group" ref={containerRef}>
      <label htmlFor="voice-selector">Voice</label>
      <Select
        id="voice-selector"
        className="react-select-brutalist"
        classNamePrefix="react-select"
        value={selectedOption}
        defaultValue={selectedOption}
        options={voiceOptions}
        maxMenuHeight={240}
        menuPlacement="auto"
        menuPosition="fixed"
        menuPortalTarget={menuPortalTarget}
        styles={{
          menuPortal: (base) => ({
            ...base,
            zIndex: 1000,
          }),
        }}
        onChange={(e) => {
          setSelectedOption(e);
          if (e) {
            updateConfig(e.value);
          }
        }}
      />
    </div>
  );
}
