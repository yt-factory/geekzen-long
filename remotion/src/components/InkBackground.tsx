import React from "react";
import { AbsoluteFill } from "remotion";

export const InkBackground: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(ellipse at 30% 40%, #0e0e0e 0%, #080808 60%, #050505 100%)",
      }}
    >
      {/* subtle vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.5) 100%)",
        }}
      />
      {/* thin border inset */}
      <div
        style={{
          position: "absolute",
          inset: 48,
          border: "1px solid rgba(240,235,225,0.06)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
