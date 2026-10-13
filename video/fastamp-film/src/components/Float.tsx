import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { float } from "./anim";

/** Profondeur 2,5D modérée : perspective 1400 px, flottement lent (cycle 9 s). */
export const Float: React.FC<{ children: React.ReactNode; phase?: number; amount?: number; style?: React.CSSProperties }> = ({
  children,
  phase = 0,
  amount = 1,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const f = float(frame, fps, phase);
  return (
    <div style={{ perspective: 1400, ...style }}>
      <div
        style={{
          transform: `translateY(${f.y * amount}px) rotateX(${f.rx * amount}deg) rotateY(${f.ry * amount}deg)`,
          transformStyle: "preserve-3d",
        }}
      >
        {children}
      </div>
    </div>
  );
};

/** Place un élément par son centre. */
export const At: React.FC<{ x: number; y: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ x, y, children, style }) => (
  <div style={{ position: "absolute", left: x, top: y, translate: "-50% -50%", ...style }}>{children}</div>
);
