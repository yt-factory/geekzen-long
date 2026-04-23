import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { InkBackground } from "./components/InkBackground";
import { Seal } from "./components/Seal";
import { Slide, SlideType } from "./components/Slide";
import { SubtitleLayer } from "./components/SubtitleLayer";

export interface SlideData {
  text: string;
  type: SlideType;
  start: number;
  end: number;
  duration: number;
  paragraph_index?: number;
}

export interface SubtitleEntry {
  start: number;
  end: number;
  text: string;
}

export interface GeekZenVideoProps {
  slides: SlideData[];
  audioSrc: string;
  subtitles: SubtitleEntry[];
}

// Fade duration per slide type (in frames at 30fps)
const FADE_IN_FRAMES = 9;   // ~0.3s
const FADE_OUT_FRAMES = 6;  // ~0.2s
const PAUSE_FADE_FRAMES = 24; // ~0.8s for pause slides

interface FadedSlideProps {
  slide: SlideData;
  durationInFrames: number;
}

const FadedSlide: React.FC<FadedSlideProps> = ({ slide, durationInFrames }) => {
  const frame = useCurrentFrame();
  const isPause = slide.type === "pause";

  const rawFadeIn = isPause ? PAUSE_FADE_FRAMES : FADE_IN_FRAMES;
  const rawFadeOut = isPause ? PAUSE_FADE_FRAMES : FADE_OUT_FRAMES;

  const fadeInEnd = Math.min(rawFadeIn, Math.floor(durationInFrames / 2));
  const fadeOutStart = durationInFrames - Math.min(rawFadeOut, durationInFrames - fadeInEnd);

  // When fadeInEnd === fadeOutStart (very short slide), use 3-point bell curve
  const opacity =
    fadeInEnd < fadeOutStart
      ? interpolate(frame, [0, fadeInEnd, fadeOutStart, durationInFrames], [0, 1, 1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : interpolate(frame, [0, fadeInEnd, durationInFrames], [0, 1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

  return (
    <AbsoluteFill style={{ opacity }}>
      <Slide text={slide.text} type={slide.type} />
    </AbsoluteFill>
  );
};

export const GeekZenVideo: React.FC<GeekZenVideoProps> = ({
  slides,
  audioSrc,
  subtitles,
}) => {
  const { fps, width, height } = useVideoConfig();
  const frame = useCurrentFrame();
  const currentTimeMs = (frame / fps) * 1000;

  return (
    <AbsoluteFill style={{ background: "#080808", width, height }}>
      <InkBackground />

      {/* Audio track */}
      <Audio src={audioSrc.startsWith("http") ? audioSrc : staticFile(audioSrc)} />

      {/* Slide sequences with per-slide fade */}
      {slides.map((slide, i) => {
        const startFrame = Math.round(slide.start * fps);
        const durationInFrames = Math.max(Math.round(slide.duration * fps), 1);

        return (
          <Sequence
            key={i}
            from={startFrame}
            durationInFrames={durationInFrames}
            layout="none"
          >
            <FadedSlide slide={slide} durationInFrames={durationInFrames} />
          </Sequence>
        );
      })}

      {/* Seal — always visible */}
      <Seal />

      {/* Subtitle overlay */}
      <SubtitleLayer subtitles={subtitles} currentTimeMs={currentTimeMs} />
    </AbsoluteFill>
  );
};
