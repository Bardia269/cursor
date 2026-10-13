import React from "react";
import { useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { prog } from "./anim";

type Props = { text: string; at: number; tone: "night" | "paper"; style?: React.CSSProperties; size?: number };

// Mentions obligatoires : lisibles (≥ 26 px), discrètes, jamais en mouvement pendant la lecture.
export const Note: React.FC<Props> = ({ text, at, tone, style, size = 27 }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, at, 14);
  const color = tone === "night" ? "rgba(250,249,252,0.72)" : "rgba(24,23,26,0.66)";
  return (
    <div
      style={{
        position: "absolute",
        display: "flex",
        alignItems: "center",
        gap: 14,
        fontFamily: FONT,
        fontSize: size,
        color,
        opacity: p,
        ...style,
      }}
    >
      <span
        style={{
          width: size * 0.55,
          height: size * 0.55,
          borderRadius: "50%",
          border: `3px solid ${tone === "night" ? C.lavender : C.deep}`,
          flex: "none",
        }}
      />
      {text}
    </div>
  );
};
