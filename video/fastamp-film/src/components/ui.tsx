import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import qr from "../data/qr.json";
import { C, FONT } from "../theme";
import { prog } from "./anim";

type QrKey = keyof typeof qr;

/** QR calculé par scripts/make-qr.mjs (jamais dessiné à la main). */
export const Qr: React.FC<{ id: QrKey; size: number; fg?: string; bg?: string; reveal?: number }> = ({
  id,
  size,
  fg = C.ink,
  bg = "#FFFFFF",
  reveal = 1,
}) => {
  const m = qr[id];
  const quiet = 2;
  const n = m.size + quiet * 2;
  let d = "";
  m.rows.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      if (row[x] === "1") d += `M${x + quiet} ${y + quiet}h1v1h-1z`;
    }
  });
  return (
    <svg width={size} height={size} viewBox={`0 0 ${n} ${n}`} shapeRendering="crispEdges" style={{ display: "block" }}>
      <rect width={n} height={n} fill={bg} />
      <defs>
        <clipPath id={`qr-reveal-${id}`}>
          <rect width={n} height={n * reveal} />
        </clipPath>
      </defs>
      <path d={d} fill={fg} clipPath={`url(#qr-reveal-${id})`} />
    </svg>
  );
};

export const Check: React.FC<{ size: number; color?: string; draw?: number; stroke?: number }> = ({
  size,
  color = C.deep,
  draw = 1,
  stroke = 3.2,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{ display: "block", flex: "none" }}>
    <path
      d="M4.5 12.5l4.8 4.8L19.5 7"
      fill="none"
      stroke={color}
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      pathLength={1}
      strokeDasharray={1}
      strokeDashoffset={1 - draw}
    />
  </svg>
);

/** Étoile à quatre branches du logo : accent ponctuel. */
export const Star: React.FC<{ size: number; color?: string; style?: React.CSSProperties }> = ({ size, color = C.lavender, style }) => (
  <svg width={size} height={size} viewBox="1201 137 108 108" style={{ display: "block", flex: "none", ...style }}>
    <path d="M1255 137L1270 176L1309 191L1270 206L1255 245L1240 206L1201 191L1240 176L1255 137Z" fill={color} />
  </svg>
);

type ButtonProps = {
  label: string;
  /** frame de l'appui (compression + changement d'état) */
  pressAt?: number;
  pressedLabel?: string;
  size?: number;
  tone?: "lavender" | "deep" | "ghost";
  style?: React.CSSProperties;
};

// Boutons éditoriaux du site : coins ~2 px, ombre décalée légère.
export const Button: React.FC<ButtonProps> = ({ label, pressAt, pressedLabel, size = 30, tone = "lavender", style }) => {
  const frame = useCurrentFrame();
  const pressed = pressAt !== undefined && frame >= pressAt;
  const squish =
    pressAt === undefined
      ? 1
      : interpolate(frame, [pressAt - 2, pressAt + 2, pressAt + 8], [1, 0.95, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
  const done = pressAt === undefined ? 0 : prog(frame, pressAt + 2, 10);
  const bg = tone === "lavender" ? C.lavender : tone === "deep" ? C.deep : "transparent";
  const fg = tone === "lavender" ? C.deep : tone === "deep" ? C.paper : C.deep;
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: size * 0.4,
        padding: `${size * 0.55}px ${size * 0.95}px`,
        borderRadius: 2,
        background: bg,
        color: fg,
        border: tone === "ghost" ? `2px solid ${C.deep}` : "none",
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: size,
        letterSpacing: "-0.01em",
        boxShadow: pressed ? `2px 2px 0 ${C.ink}33` : `5px 5px 0 ${C.ink}40`,
        scale: String(squish),
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {pressed && pressedLabel ? (
        <>
          <Check size={size * 1.1} color={fg} draw={done} />
          {pressedLabel}
        </>
      ) : (
        label
      )}
    </div>
  );
};

export const PremiumBadge: React.FC<{ size?: number; at?: number; style?: React.CSSProperties }> = ({ size = 24, at = 0, style }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, at, 12);
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: size * 0.4,
        padding: `${size * 0.3}px ${size * 0.6}px`,
        borderRadius: 2,
        background: C.deep,
        color: C.paper,
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: size,
        letterSpacing: "0.04em",
        opacity: p,
        scale: String(0.9 + 0.1 * p),
        ...style,
      }}
    >
      <Star size={size * 0.9} />
      Premium
    </div>
  );
};

/** Indicateur de toucher : un anneau qui se contracte, pas un curseur fantôme. */
export const Tap: React.FC<{ at: number; x: number; y: number; color?: string }> = ({ at, x, y, color = C.deep }) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < -10 || t > 18) return null;
  const approach = interpolate(t, [-10, 0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ripple = interpolate(t, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0, pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: -28,
          top: -28,
          width: 56,
          height: 56,
          borderRadius: "50%",
          background: `${color}33`,
          border: `3px solid ${color}`,
          opacity: approach * (1 - ripple),
          scale: String(t < 0 ? 1.4 - approach * 0.4 : 1 - ripple * 0.25),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: -28,
          top: -28,
          width: 56,
          height: 56,
          borderRadius: "50%",
          border: `2px solid ${color}`,
          opacity: t >= 0 ? 1 - ripple : 0,
          scale: String(1 + ripple * 1.6),
        }}
      />
    </div>
  );
};

/** Panneau éditorial : coins presque droits, bordure fine, ombre décalée légère. */
export const Panel: React.FC<{
  children: React.ReactNode;
  tone?: "light" | "dark";
  style?: React.CSSProperties;
}> = ({ children, tone = "light", style }) => (
  <div
    style={{
      background: tone === "light" ? "#FFFFFF" : C.graphite,
      color: tone === "light" ? C.ink : C.paper,
      border: `1.5px solid ${tone === "light" ? "rgba(35,10,92,0.16)" : "rgba(199,185,232,0.22)"}`,
      borderRadius: 2,
      boxShadow: tone === "light" ? `10px 10px 0 rgba(35,10,92,0.10)` : `10px 10px 0 rgba(0,0,0,0.35)`,
      fontFamily: FONT,
      ...style,
    }}
  >
    {children}
  </div>
);

export const Toggle: React.FC<{ onAt?: number; size?: number; color?: string }> = ({ onAt, size = 30, color = C.deep }) => {
  const frame = useCurrentFrame();
  const on = onAt === undefined ? 1 : prog(frame, onAt, 8);
  return (
    <div
      style={{
        width: size * 1.8,
        height: size,
        borderRadius: size,
        background: on > 0.5 ? color : "rgba(24,23,26,0.18)",
        position: "relative",
        flex: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: size * 0.12,
          left: size * 0.12 + on * size * 0.8,
          width: size * 0.76,
          height: size * 0.76,
          borderRadius: "50%",
          background: "#FFFFFF",
        }}
      />
    </div>
  );
};
