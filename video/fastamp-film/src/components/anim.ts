import { Easing, interpolate } from "remotion";
import { EASE_IN_OUT, EASE_OUT } from "../theme";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0 → 1 entre `start` et `start + dur`, easing "out" doux. */
export const prog = (frame: number, start: number, dur: number, ease: readonly number[] = EASE_OUT) =>
  interpolate(frame, [start, start + dur], [0, 1], {
    ...clamp,
    easing: Easing.bezier(ease[0], ease[1], ease[2], ease[3]),
  });

export const progInOut = (frame: number, start: number, dur: number) => prog(frame, start, dur, EASE_IN_OUT);

export const mix = (a: number, b: number, t: number) => a + (b - a) * t;

/**
 * Tampon : expansion courte puis légère compression 100 % → 96 % → 100 %.
 * Pas de rebond de jouet.
 */
export const stampScale = (frame: number, at: number) => {
  if (frame < at) return 0;
  return interpolate(frame, [at, at + 5, at + 9, at + 15], [1.18, 1, 0.96, 1], {
    ...clamp,
    easing: Easing.bezier(0.33, 0, 0.2, 1),
  });
};

export const stampOpacity = (frame: number, at: number) =>
  interpolate(frame, [at, at + 3], [0, 1], clamp);

/** Flottement de la carte du site : cycle de 9 s, ~10 px, rotations de quelques degrés. */
export const float = (frame: number, fps: number, phase = 0) => {
  const t = ((frame / fps) * 2 * Math.PI) / 9 + phase;
  return {
    y: Math.sin(t) * 10,
    rx: Math.sin(t + 1.1) * 3,
    ry: Math.cos(t) * 5 - 6,
  };
};

export const typed = (text: string, frame: number, start: number, cps = 32, fps = 30) => {
  const n = Math.floor(((frame - start) / fps) * cps);
  return text.slice(0, Math.max(0, Math.min(text.length, n)));
};
