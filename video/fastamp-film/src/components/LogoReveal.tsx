import React from "react";
import { Img, interpolate, staticFile, useCurrentFrame, Easing } from "remotion";
import { C } from "../theme";
import { stampOpacity, stampScale } from "./anim";

// Anneaux du symbole officiel, coordonnées du viewBox "225 125 1100 310" de fastamp-logo-inverse.svg.
const STAMPS: [number, number][] = [
  [273, 270],
  [333, 270],
  [393, 270],
  [273, 334],
  [333, 334],
  [273, 398],
];
const ACCENT: [number, number] = [393, 334];

type Props = {
  width: number;
  /** frame du premier tampon */
  at: number;
  /** intervalle entre deux tampons */
  gap?: number;
  /** début du balayage révélant « ASTAMP », la signature et l'étoile (PNG officiel) */
  wipeAt?: number;
  inverse?: boolean;
  style?: React.CSSProperties;
};

/**
 * Le logo officiel n'est jamais redessiné : les anneaux sont posés sur la géométrie exacte
 * du SVG fourni, puis le PNG officiel est révélé par balayage. À la fin, seul le PNG reste.
 */
export const LogoReveal: React.FC<Props> = ({ width, at, gap = 5, wipeAt, inverse = true, style }) => {
  const frame = useCurrentFrame();
  const height = (width * 310) / 1100;
  const wStart = wipeAt ?? at + gap * 7 + 6;
  const wipe = interpolate(frame, [wStart, wStart + 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.65, 0, 0.35, 1),
  });
  const ringsDone = frame >= at + gap * 6 + 16;
  const ink = inverse ? C.paper : C.ink;
  // Les anneaux occupent x ∈ [225, 430] dans le viewBox ; le texte commence à 450.
  const symbolFrac = (432 - 225) / 1100;
  const visibleFrac = symbolFrac + (1 - symbolFrac) * wipe;
  return (
    <div style={{ width, height, position: "relative", ...style }}>
      <Img
        src={staticFile(inverse ? "brand/fastamp-logo-inverse.png" : "brand/fastamp-logo.png")}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          clipPath: ringsDone
            ? `inset(0 ${(1 - visibleFrac) * 100}% 0 0)`
            : `inset(0 ${(1 - visibleFrac) * 100}% 0 ${symbolFrac * 100}%)`,
        }}
      />
      {!ringsDone ? (
        <svg viewBox="225 125 1100 310" width={width} height={height} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
          {STAMPS.map(([x, y], i) => {
            const f = at + i * gap;
            return (
              <g key={i} transform={`translate(${x} ${y}) scale(${stampScale(frame, f)})`} opacity={stampOpacity(frame, f)}>
                <circle r={23} fill="none" stroke={ink} strokeWidth={7} />
                <circle r={13.5} fill="none" stroke={ink} strokeWidth={3} />
              </g>
            );
          })}
          <g
            transform={`translate(${ACCENT[0]} ${ACCENT[1]}) scale(${stampScale(frame, at + gap * 6)})`}
            opacity={stampOpacity(frame, at + gap * 6)}
          >
            <circle r={20} fill="none" stroke={C.lavender} strokeWidth={11} />
          </g>
        </svg>
      ) : null}
    </div>
  );
};

/** Position (en fraction de la largeur/hauteur du logo) du centre du symbole, pour cadrer un zoom. */
export const LOGO_SYMBOL_CENTER = { x: (333 - 225) / 1100, y: (334 - 125) / 310 };
