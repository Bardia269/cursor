import React from "react";
import { AbsoluteFill, interpolate } from "remotion";
import type { TransitionPresentation, TransitionPresentationComponentProps } from "@remotion/transitions";

type Props = { x: number; y: number; width: number; height: number };

// Transition immersive : la caméra fonce vers l'avant à travers un anneau de lumière lavande
// (l'anneau du logo). La scène sortante grossit et se floute, la suivante arrive de la profondeur.
const FlyThrough: React.FC<TransitionPresentationComponentProps<Props>> = ({ children, presentationDirection, presentationProgress: p, passedProps }) => {
  const { x, y, width, height } = passedProps;
  const ox = x * width;
  const oy = y * height;
  if (presentationDirection === "exiting") {
    const s = interpolate(p, [0, 1], [1, 2.4], { easing: (t) => t * t });
    return (
      <AbsoluteFill
        style={{
          scale: String(s),
          transformOrigin: `${ox}px ${oy}px`,
          opacity: interpolate(p, [0, 0.55, 0.85], [1, 1, 0], { extrapolateRight: "clamp" }),
          filter: `blur(${interpolate(p, [0, 1], [0, 18])}px) brightness(${interpolate(p, [0, 0.6, 1], [1, 1.35, 1.6])})`,
        }}
      >
        {children}
      </AbsoluteFill>
    );
  }
  const ringScale = interpolate(p, [0, 1], [0.15, 9], { easing: (t) => t * t * t });
  const ringOpacity = interpolate(p, [0, 0.15, 0.7, 1], [0, 1, 0.8, 0]);
  const d = Math.min(width, height) * 0.4;
  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          scale: String(interpolate(p, [0, 1], [0.72, 1], { easing: (t) => 1 - Math.pow(1 - t, 3) })),
          transformOrigin: `${ox}px ${oy}px`,
          opacity: interpolate(p, [0.25, 0.75], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          filter: `blur(${interpolate(p, [0.2, 1], [14, 0], { extrapolateLeft: "clamp" })}px)`,
        }}
      >
        {children}
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: ox - d / 2,
          top: oy - d / 2,
          width: d,
          height: d,
          borderRadius: "50%",
          border: `${d * 0.12}px solid #EDE6FF`,
          boxShadow: `0 0 ${d * 0.2}px ${d * 0.05}px rgba(199,185,232,0.9), inset 0 0 ${d * 0.15}px ${d * 0.03}px rgba(199,185,232,0.8)`,
          scale: String(ringScale),
          opacity: ringOpacity,
        }}
      />
    </AbsoluteFill>
  );
};

export const flyThrough = (props: Props): TransitionPresentation<Props> => ({ component: FlyThrough, props });
