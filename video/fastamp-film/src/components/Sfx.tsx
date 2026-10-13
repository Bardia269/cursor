import React from "react";
import { Audio } from "@remotion/media";
import { Sequence, staticFile, useVideoConfig } from "remotion";

export type SfxName = "stamp" | "pop" | "click" | "whoosh" | "chime" | "tick" | "scan" | "swipe";

/** Effet sonore placé à une frame de la scène. Sons synthétisés par scripts/make-audio.py. */
export const Sfx: React.FC<{ name: SfxName; at: number; volume?: number }> = ({ name, at, volume = 1 }) => {
  const { fps } = useVideoConfig();
  return (
    <Sequence from={at} durationInFrames={3 * fps} name={`sfx ${name}`} layout="none">
      <Audio src={staticFile(`audio/${name}.wav`)} volume={volume} />
    </Sequence>
  );
};
