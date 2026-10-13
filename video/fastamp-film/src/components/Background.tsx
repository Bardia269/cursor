import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { C, HERO_GRADIENT } from "../theme";

type Props = {
  tone: "night" | "paper";
  /** Zone où le motif s'efface pour ne jamais passer sous les textes (en % de la largeur/hauteur). */
  clearAt?: string;
  patternOpacity?: number;
};

// Motif distinctif : trame d'anneaux de tampons en légère rotation diagonale (rappel du hero).
export const Background: React.FC<Props> = ({ tone, clearAt = "22% 40%", patternOpacity }) => {
  const frame = useCurrentFrame();
  const night = tone === "night";
  const stroke = night ? C.lavender : C.deep;
  const opacity = patternOpacity ?? (night ? 0.1 : 0.06);
  const drift = (frame * 0.35) % 120;
  return (
    <AbsoluteFill style={{ background: night ? HERO_GRADIENT : C.paper }}>
      <AbsoluteFill
        style={{
          opacity,
          WebkitMaskImage: `radial-gradient(ellipse 60% 55% at ${clearAt}, transparent 35%, black 85%)`,
          maskImage: `radial-gradient(ellipse 60% 55% at ${clearAt}, transparent 35%, black 85%)`,
        }}
      >
        <svg width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
          <defs>
            <pattern
              id={`rings-${tone}`}
              width={120}
              height={120}
              patternUnits="userSpaceOnUse"
              patternTransform={`rotate(-18) translate(${drift} ${drift * 0.4})`}
            >
              <circle cx={60} cy={60} r={26} fill="none" stroke={stroke} strokeWidth={5} />
              <circle cx={60} cy={60} r={15} fill="none" stroke={stroke} strokeWidth={2} />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill={`url(#rings-${tone})`} />
        </svg>
      </AbsoluteFill>
      {night ? (
        <AbsoluteFill
          style={{ background: "radial-gradient(ellipse 80% 70% at 50% 50%, transparent 55%, rgba(8,4,20,0.55) 100%)" }}
        />
      ) : null}
    </AbsoluteFill>
  );
};
