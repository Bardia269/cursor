import React from "react";
import { Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C } from "../theme";
import { Ring } from "./Ring";
import { Obj } from "./Space";
import { stampScale } from "./anim";

// Géométrie exacte du symbole officiel (viewBox 225 125 1100 310 de fastamp-logo-inverse.svg).
const RINGS: { x: number; y: number; accent?: boolean }[] = [
  { x: 273, y: 270 },
  { x: 333, y: 270 },
  { x: 393, y: 270 },
  { x: 273, y: 334 },
  { x: 333, y: 334 },
  { x: 273, y: 398 },
  { x: 393, y: 334, accent: true },
];
// Points de départ dispersés dans l'espace (déterministes).
const SCATTER = [
  [-820, -380, -900, 40],
  [620, -460, -1400, -60],
  [980, 120, -600, 80],
  [-1100, 260, -1200, -30],
  [300, 520, -300, 50],
  [-520, 600, -1700, -70],
  [140, -120, -2200, 0],
];

type Props = {
  cx: number;
  cy: number;
  cz: number;
  width: number;
  /** frame de départ du vol des anneaux */
  at: number;
  /** durée du vol de chaque anneau */
  fly?: number;
  gap?: number;
  wipeAt?: number;
  opacity?: number;
};

/**
 * Logo officiel assemblé en 3D : les anneaux arrivent de la profondeur et se posent
 * exactement sur la géométrie du SVG fourni, puis le PNG officiel prend le relais.
 */
export const Logo3D: React.FC<Props> = ({ cx, cy, cz, width, at, fly = 34, gap = 6, wipeAt, opacity = 1 }) => {
  const frame = useCurrentFrame();
  const k = width / 1100;
  const height = 310 * k;
  const landed = (i: number) => at + i * gap + fly;
  const allLanded = landed(RINGS.length - 1) + 6;
  const wStart = wipeAt ?? allLanded;
  const wipe = interpolate(frame, [wStart, wStart + 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.65, 0, 0.35, 1),
  });
  const symbolFrac = (432 - 225) / 1100;
  const visible = symbolFrac + (1 - symbolFrac) * wipe;
  const done = frame >= allLanded;
  return (
    <>
      <Obj x={cx} y={cy} z={cz} sharp>
        <div style={{ width, height, opacity }}>
          <Img
            src={staticFile("brand/fastamp-logo-inverse.png")}
            style={{
              width,
              height,
              display: "block",
              clipPath: done ? `inset(0 ${(1 - visible) * 100}% 0 0)` : `inset(0 ${(1 - visible) * 100}% 0 ${symbolFrac * 100}%)`,
            }}
          />
        </div>
      </Obj>
      {done
        ? null
        : RINGS.map((r, i) => {
            const t = interpolate(frame, [at + i * gap, landed(i)], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.2, 0.7, 0.1, 1),
            });
            const [sx, sy, sz, srot] = SCATTER[i];
            const fx = cx + (r.x - 775) * k;
            const fy = cy + (r.y - 280) * k;
            const s = frame >= landed(i) ? stampScale(frame, landed(i)) : 1;
            const glow = 1 - interpolate(frame, [landed(i) - 4, landed(i) + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (
              <Obj
                key={i}
                x={fx + sx * (1 - t)}
                y={fy + sy * (1 - t)}
                z={cz + sz * (1 - t)}
                ry={srot * (1 - t)}
                rx={-srot * 0.6 * (1 - t)}
                sharp
              >
                <div
                  style={{
                    opacity: interpolate(frame, [at + i * gap, at + i * gap + 6], [0, opacity], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                    filter: glow > 0.02 ? `drop-shadow(0 0 ${14 * glow}px ${C.lavender})` : undefined,
                    scale: String(s),
                  }}
                >
                  <Ring size={60 * k} variant={r.accent ? "accent" : "stamp"} color={r.accent ? C.lavender : C.paper} />
                </div>
              </Obj>
            );
          })}
    </>
  );
};

export const LOGO_RINGS_LANDED = (at: number, fly = 34, gap = 6) => at + 6 * gap + fly;
/** Position de l'anneau lavande par rapport au centre du logo (pour y plonger). */
export const accentOffset = (width: number) => ({ x: (393 - 775) * (width / 1100), y: (334 - 280) * (width / 1100) });
