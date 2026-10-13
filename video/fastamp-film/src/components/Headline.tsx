import React from "react";
import { useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { prog } from "./anim";

export type Line = { text: string; at: number; color?: string };

type Props = {
  lines: Line[];
  size: number;
  color?: string;
  align?: "left" | "center";
  style?: React.CSSProperties;
  /** Sortie commune de toutes les lignes. */
  outAt?: number;
};

// Titres : sans-serif très gras, silhouette compacte, interlettrage resserré.
// Chaque ligne monte derrière un masque, puis reste immobile pour la lecture.
export const Headline: React.FC<Props> = ({ lines, size, color = C.paper, align = "left", style, outAt }) => {
  const frame = useCurrentFrame();
  const out = outAt === undefined ? 0 : prog(frame, outAt, 12);
  return (
    <div
      style={{
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1.04,
        letterSpacing: "-0.035em",
        color,
        textAlign: align,
        opacity: 1 - out,
        translate: `0px ${-out * 30}px`,
        ...style,
      }}
    >
      {lines.map((l) => {
        const p = prog(frame, l.at, 18);
        return (
          <div key={l.text} style={{ overflow: "hidden", paddingBottom: size * 0.08, marginBottom: -size * 0.08 }}>
            <div
              style={{
                translate: `0px ${(1 - p) * size * 1.1}px`,
                rotate: `${(1 - p) * 2.5}deg`,
                transformOrigin: "left bottom",
                color: l.color ?? color,
                whiteSpace: "pre",
              }}
            >
              {l.text}
            </div>
          </div>
        );
      })}
    </div>
  );
};

type SubProps = {
  text: string;
  at: number;
  size: number;
  color?: string;
  style?: React.CSSProperties;
  weight?: number;
};

export const Sub: React.FC<SubProps> = ({ text, at, size, color = C.paper, style, weight = 400 }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, at, 16);
  return (
    <div
      style={{
        fontFamily: FONT,
        fontSize: size,
        fontWeight: weight,
        lineHeight: 1.3,
        color,
        opacity: p,
        translate: `0px ${(1 - p) * 18}px`,
        ...style,
      }}
    >
      {text}
    </div>
  );
};

/** Étiquette de section (Fastamp Signals, etc.) avec un petit anneau en repère. */
export const Kicker: React.FC<SubProps & { ringColor?: string }> = ({ text, at, size, color = C.lavender, style, ringColor }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, at, 14);
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: size * 0.5,
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: size,
        letterSpacing: "0.02em",
        color,
        opacity: p,
        translate: `${(1 - p) * -20}px 0px`,
        ...style,
      }}
    >
      <svg width={size * 1.1} height={size * 1.1} viewBox="-30 -30 60 60">
        <circle r={20} fill="none" stroke={ringColor ?? color} strokeWidth={11} />
      </svg>
      {text}
    </div>
  );
};
