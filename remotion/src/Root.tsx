import React from "react";
import { Composition, registerRoot } from "remotion";
import { GeekZenVideo, GeekZenVideoProps } from "./GeekZenVideo";

const DEFAULT_SLIDES = [
  { text: "极客禅", type: "phrase" as const, start: 0, duration: 3, end: 3 },
];

const defaultProps: GeekZenVideoProps = {
  slides: DEFAULT_SLIDES,
  audioSrc: "audio_tw.mp3",
  subtitles: [],
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="GeekZenVideo"
      component={GeekZenVideo}
      durationInFrames={1800}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={defaultProps}
      calculateMetadata={async ({ props }) => {
        const totalDuration = props.slides.reduce((max, s) => Math.max(max, s.end), 0);
        return {
          durationInFrames: Math.max(Math.ceil(totalDuration * 30), 30),
          fps: 30,
          width: 1920,
          height: 1080,
        };
      }}
    />
  );
};

registerRoot(RemotionRoot);
