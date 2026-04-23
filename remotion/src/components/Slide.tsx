import React from "react";
import { AbsoluteFill } from "remotion";

export type SlideType = "single_char" | "phrase" | "sentence" | "pause";

interface SlideProps {
  text: string;
  type: SlideType;
}

const FONT_SIZE: Record<SlideType, number> = {
  single_char: 380,
  phrase: 130,
  sentence: 72,
  pause: 0,
};

const LETTER_SPACING: Record<SlideType, string> = {
  single_char: "-0.02em",
  phrase: "0.08em",
  sentence: "0.05em",
  pause: "0",
};

const LINE_HEIGHT: Record<SlideType, number> = {
  single_char: 1,
  phrase: 1.3,
  sentence: 1.6,
  pause: 1,
};

export const Slide: React.FC<SlideProps> = ({ text, type }) => {
  if (type === "pause") return null;

  return (
    <AbsoluteFill
      style={{ alignItems: "center", justifyContent: "center", padding: "0 160px" }}
    >
      <div
        style={{
          fontFamily: "'Noto Serif CJK TC', 'Noto Serif CJK SC', 'SimSun', serif",
          fontSize: FONT_SIZE[type],
          fontWeight: 300,
          lineHeight: LINE_HEIGHT[type],
          color: "#F0EBE1",
          letterSpacing: LETTER_SPACING[type],
          whiteSpace: "pre-wrap",
          textAlign: "center",
          maxWidth: type === "sentence" ? 1400 : type === "phrase" ? 1600 : "unset",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
