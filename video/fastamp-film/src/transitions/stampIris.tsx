import React from "react";
import { AbsoluteFill, interpolate } from "remotion";
import type { TransitionPresentation, TransitionPresentationComponentProps } from "@remotion/transitions";
import { C } from "../theme";

type IrisProps = {
  /** origine de l'iris, en fraction de la largeur / hauteur */
  x: number;
  y: number;
  width: number;
  height: number;
  ringColor?: string;
};

// Transition signature : un anneau de tampon s'ouvre et laisse voir la scène suivante.
// Le double contour reprend les proportions du symbole (trait épais + trait fin).
const StampIris: React.FC<TransitionPresentationComponentProps<IrisProps>> = ({
  children,
  presentationDirection,
  presentationProgress: p,
  passedProps,
}) => {
  const { x, y, width, height, ringColor = C.lavender } = passedProps;
  const cx = x * width;
  const cy = y * height;
  const maxR = Math.hypot(Math.max(cx, width - cx), Math.max(cy, height - cy)) + 80;

  if (presentationDirection === "exiting") {
    return (
      <AbsoluteFill
        style={{
          scale: String(interpolate(p, [0, 1], [1, 0.94])),
          transformOrigin: `${cx}px ${cy}px`,
          filter: `brightness(${interpolate(p, [0, 1], [1, 0.75])})`,
        }}
      >
        {children}
      </AbsoluteFill>
    );
  }

  const r = interpolate(p, [0, 1], [0, maxR]);
  const thick = interpolate(p, [0, 0.15, 0.85, 1], [0, 34, 34, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          clipPath: `circle(${r}px at ${cx}px ${cy}px)`,
          scale: String(interpolate(p, [0, 1], [1.08, 1])),
          transformOrigin: `${cx}px ${cy}px`,
        }}
      >
        {children}
      </AbsoluteFill>
      {p < 1 ? (
        <svg width={width} height={height} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
          <circle cx={cx} cy={cy} r={r + thick / 2} fill="none" stroke={ringColor} strokeWidth={thick} />
          <circle cx={cx} cy={cy} r={r + thick + 26} fill="none" stroke={ringColor} strokeWidth={thick * 0.3} opacity={0.9} />
        </svg>
      ) : null}
    </AbsoluteFill>
  );
};

export const stampIris = (props: IrisProps): TransitionPresentation<IrisProps> => ({
  component: StampIris,
  props,
});
