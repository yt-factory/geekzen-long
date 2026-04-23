import React from "react";

interface SubtitleEntry {
  start: number;
  end: number;
  text: string;
}

interface SubtitleLayerProps {
  subtitles: SubtitleEntry[];
  currentTimeMs: number;
}

export const SubtitleLayer: React.FC<SubtitleLayerProps> = ({ subtitles, currentTimeMs }) => {
  const currentSub = subtitles.find(
    (s) => currentTimeMs >= s.start && currentTimeMs < s.end
  );

  if (!currentSub?.text?.trim()) return null;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          fontFamily: "'Noto Serif CJK TC', 'Noto Serif CJK SC', serif",
          fontSize: 42,
          fontWeight: 300,
          color: "#F0EBE1",
          textAlign: "center",
          maxWidth: 1400,
          letterSpacing: "0.06em",
          textShadow: "0 2px 12px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.6)",
          padding: "8px 24px",
        }}
      >
        {currentSub.text}
      </div>
    </div>
  );
};
