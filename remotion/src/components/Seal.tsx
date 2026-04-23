import React from "react";
import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

export const Seal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = spring({
    frame,
    fps,
    config: { damping: 80, stiffness: 60, mass: 1 },
    durationInFrames: 30,
  });

  const scale = interpolate(opacity, [0, 1], [0.85, 1]);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 64,
        right: 88,
        opacity: opacity * 0.35,
        transform: `scale(${scale})`,
        transformOrigin: "bottom right",
      }}
    >
      <Img
        src={staticFile("seal.png")}
        style={{ width: 80, height: 80, objectFit: "contain" }}
      />
    </div>
  );
};
