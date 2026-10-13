import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { C } from "../theme";
import { Obj } from "./Space";

/** Barre de lumière verticale qui balaie les panneaux (comme un scanner). */
export const Sweep: React.FC<{ from: number; to: number; y: number; z: number; at: number; dur: number; height: number; ry?: number }> = ({
  from,
  to,
  y,
  z,
  at,
  dur,
  height,
  ry = 0,
}) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [at, at + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (t <= 0 || t >= 1) return null;
  const o = Math.sin(t * Math.PI);
  return (
    <Obj x={from + (to - from) * t} y={y} z={z} ry={ry} sharp>
      <div style={{ position: "relative", width: 160, height, opacity: o }}>
        <div style={{ position: "absolute", left: 74, top: 0, width: 12, height, borderRadius: 12, background: "#FFFFFF", boxShadow: `0 0 30px 10px ${C.lavender}, 0 0 90px 30px rgba(143,107,232,0.6)` }} />
      </div>
    </Obj>
  );
};
