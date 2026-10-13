import React, { createContext, useContext } from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { C } from "../theme";

// Moteur 3D CSS : caméra animée, objets positionnés en espace, profondeur de champ,
// sol réfléchissant. Tout est piloté par la frame (rendu déterministe).

export type Cam = { x: number; y: number; z: number; rx: number; ry: number; rz: number };
export type CamKey = Partial<Cam> & { f: number; ease?: readonly number[] };

const ZERO: Cam = { x: 0, y: 0, z: 0, rx: 0, ry: 0, rz: 0 };
export const PERSPECTIVE = 1600;

/** Interpole une trajectoire de caméra entre images clés (easing par segment). */
export const camAt = (frame: number, keys: CamKey[]): Cam => {
  const full: (Cam & { f: number; ease?: readonly number[] })[] = [];
  let prev: Cam = ZERO;
  for (const k of keys) {
    const c = { ...prev, ...k } as Cam & { f: number; ease?: readonly number[] };
    full.push(c);
    prev = c;
  }
  if (frame <= full[0].f) return full[0];
  for (let i = 0; i < full.length - 1; i++) {
    const a = full[i];
    const b = full[i + 1];
    if (frame <= b.f) {
      const e = b.ease ?? [0.65, 0, 0.35, 1];
      const t = interpolate(frame, [a.f, b.f], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: Easing.bezier(e[0], e[1], e[2], e[3]),
      });
      const m = (k: keyof Cam) => a[k] + (b[k] - a[k]) * t;
      return { x: m("x"), y: m("y"), z: m("z"), rx: m("rx"), ry: m("ry"), rz: m("rz") };
    }
  }
  return full[full.length - 1];
};

type SpaceCtx = { cam: Cam; focus: number; dof: number };
const Ctx = createContext<SpaceCtx>({ cam: ZERO, focus: 0, dof: 0.012 });

type SpaceProps = {
  cam: Cam;
  children: React.ReactNode;
  /** profondeur nette (z monde) ; par défaut le plan z = -cam.z */
  focus?: number;
  /** intensité du flou de profondeur */
  dof?: number;
  /** hauteur (y monde) du sol réfléchissant ; null = pas de sol */
  floor?: number | null;
  style?: React.CSSProperties;
};

export const Space: React.FC<SpaceProps> = ({ cam, children, focus, dof = 0.012, floor = null, style }) => {
  const { width, height } = useVideoConfig();
  const worldTransform = `rotateZ(${cam.rz}deg) rotateX(${cam.rx}deg) rotateY(${cam.ry}deg) translate3d(${-cam.x}px, ${-cam.y}px, ${cam.z}px)`;
  const world = (mirror: boolean) => (
    <div
      style={{
        position: "absolute",
        left: width / 2,
        top: height / 2,
        width: 0,
        height: 0,
        transformStyle: "preserve-3d",
        transform: worldTransform,
      }}
    >
      {mirror && floor !== null ? (
        <div style={{ position: "absolute", transformStyle: "preserve-3d", transform: `translate3d(0px, ${2 * floor}px, 0px) scale3d(1, -1, 1)` }}>
          {children}
        </div>
      ) : (
        <>
          {floor !== null ? <FloorPlane y={floor} /> : null}
          {children}
        </>
      )}
    </div>
  );
  return (
    <Ctx.Provider value={{ cam, focus: focus ?? -cam.z, dof }}>
      {floor !== null ? (
        <AbsoluteFill
          style={{
            perspective: PERSPECTIVE,
            opacity: 0.28,
            filter: "blur(2.5px)",
            WebkitMaskImage: "linear-gradient(to bottom, transparent 35%, black 70%, rgba(0,0,0,0.4) 100%)",
          }}
        >
          {world(true)}
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{ perspective: PERSPECTIVE, perspectiveOrigin: "50% 50%", ...style }}>{world(false)}</AbsoluteFill>
    </Ctx.Provider>
  );
};

/** Sol sombre et brillant (plan horizontal à y monde). */
const FloorPlane: React.FC<{ y: number }> = ({ y }) => (
  <div
    style={{
      position: "absolute",
      left: -4000,
      top: -4000,
      width: 8000,
      height: 8000,
      transform: `translate3d(0px, ${y}px, 0px) rotateX(90deg)`,
      background: "radial-gradient(circle at 50% 50%, rgba(120,90,210,0.16) 0%, rgba(40,20,90,0.10) 18%, rgba(7,3,15,0) 45%)",
    }}
  />
);

type ObjProps = {
  x?: number;
  y?: number;
  z?: number;
  rx?: number;
  ry?: number;
  rz?: number;
  scale?: number;
  children: React.ReactNode;
  /** désactive la profondeur de champ pour cet objet */
  sharp?: boolean;
  style?: React.CSSProperties;
};

/** Objet placé dans l'espace (centré sur sa position). Flou selon l'écart au plan net. */
export const Obj: React.FC<ObjProps> = ({ x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, scale = 1, children, sharp, style }) => {
  const { focus, dof } = useContext(Ctx);
  const blur = sharp ? 0 : Math.min(14, Math.max(0, Math.abs(z - focus) - 120) * dof);
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        top: 0,
        transformStyle: "preserve-3d",
        transform: `translate3d(${x}px, ${y}px, ${z}px) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg) scale(${scale})`,
      }}
    >
      <div style={{ translate: "-50% -50%", filter: blur > 0.3 ? `blur(${blur.toFixed(2)}px)` : undefined, ...style }}>{children}</div>
    </div>
  );
};

/** Source lumineuse : sphère lavande avec halo (lumière principale de la mise en scène). */
export const Orb: React.FC<{ size: number; intensity?: number; color?: string; core?: string; style?: React.CSSProperties }> = ({
  size,
  intensity = 1,
  color = "#8F6BE8",
  core = "#F3EEFF",
  style,
}) => (
  <div style={{ position: "relative", width: size, height: size, ...style }}>
    <div
      style={{
        position: "absolute",
        inset: -size * 1.6,
        borderRadius: "50%",
        background: `radial-gradient(circle, ${color}55 0%, ${color}22 25%, transparent 60%)`,
        opacity: intensity,
      }}
    />
    <div
      style={{
        position: "absolute",
        inset: 0,
        borderRadius: "50%",
        background: `radial-gradient(circle at 50% 50%, ${core} 0%, ${C.lavender} 28%, ${color} 55%, transparent 72%)`,
        boxShadow: `0 0 ${size * 0.6}px ${size * 0.2}px ${color}88`,
        opacity: intensity,
      }}
    />
  </div>
);

/** Reflet allongé façon optique (flare horizontal), discret. */
export const Streak: React.FC<{ width: number; opacity?: number }> = ({ width, opacity = 0.6 }) => (
  <div
    style={{
      width,
      height: 3,
      borderRadius: 3,
      background: `linear-gradient(90deg, transparent, ${C.lavender} 35%, #FFFFFF 50%, ${C.lavender} 65%, transparent)`,
      boxShadow: `0 0 18px 4px ${C.lavender}66`,
      opacity,
    }}
  />
);

/** Fond de l'espace : nuit profonde, halo de la source lumineuse, vignettage. */
export const Void: React.FC<{ glowX?: number; glowY?: number; glow?: number }> = ({ glowX = 50, glowY = 40, glow = 1 }) => {
  const frame = useCurrentFrame();
  const breathe = 1 + Math.sin(frame / 22) * 0.03;
  return (
    <AbsoluteFill style={{ background: "#07030F" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse ${55 * breathe}% ${45 * breathe}% at ${glowX}% ${glowY}%, rgba(91,52,190,${0.42 * glow}) 0%, rgba(35,10,92,${0.35 * glow}) 35%, transparent 70%)`,
        }}
      />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 80% at 50% 50%, transparent 50%, rgba(0,0,0,0.7) 100%)" }} />
    </AbsoluteFill>
  );
};

/** Panneau de verre : surface sombre translucide, arête lumineuse, épaisseur suggérée. */
export const Glass: React.FC<{ children: React.ReactNode; style?: React.CSSProperties; radius?: number; light?: boolean }> = ({
  children,
  style,
  radius = 14,
  light,
}) => (
  <div
    style={{
      position: "relative",
      borderRadius: radius,
      background: light
        ? "linear-gradient(160deg, rgba(250,249,252,0.97), rgba(232,227,244,0.94))"
        : "linear-gradient(160deg, rgba(40,26,78,0.72), rgba(14,8,30,0.82))",
      border: `1.5px solid ${light ? "rgba(255,255,255,0.9)" : "rgba(199,185,232,0.38)"}`,
      boxShadow: [
        "inset 0 1.5px 0 rgba(255,255,255,0.35)",
        "inset 0 -20px 40px rgba(0,0,0,0.25)",
        "0 0 0 1px rgba(10,4,30,0.6)",
        "0 6px 0 -1px rgba(60,40,120,0.55)",
        "0 40px 80px rgba(0,0,0,0.55)",
      ].join(", "),
      color: light ? C.ink : C.paper,
      ...style,
    }}
  >
    {children}
  </div>
);

/**
 * Anneau de lumière : l'anneau lavande du logo devient la source lumineuse du film.
 * Rendu en dégradés (pas de particules), bloom doux.
 */
export const RingLight: React.FC<{ size: number; intensity?: number; style?: React.CSSProperties }> = ({ size, intensity = 1, style }) => {
  const frame = useCurrentFrame();
  const pulse = 1 + Math.sin(frame / 18) * 0.04;
  const t = size * 0.16; // épaisseur de l'anneau
  return (
    <div style={{ position: "relative", width: size * 3.4, height: size * 3.4, opacity: intensity, ...style }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(143,107,232,0.38) 0%, rgba(91,52,190,0.18) 30%, transparent 62%)",
          scale: String(pulse),
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: size * 1.2,
          borderRadius: "50%",
          border: `${t}px solid #EDE6FF`,
          boxShadow: `0 0 ${size * 0.25}px ${size * 0.06}px rgba(199,185,232,0.9), inset 0 0 ${size * 0.2}px ${size * 0.04}px rgba(199,185,232,0.85)`,
        }}
      />
    </div>
  );
};

/**
 * Calque de titres : toujours lisible, mais légèrement entraîné par la caméra
 * (parallaxe + inclinaison réduites) pour rester « dans » l'espace.
 */
export const Hud: React.FC<{ cam: Cam; children: React.ReactNode; amount?: number; scrim?: number }> = ({ cam, children, amount = 1, scrim = 0.7 }) => {
  const { width, height } = useVideoConfig();
  const vertical = height > width;
  return (
  <AbsoluteFill style={{ perspective: PERSPECTIVE }}>
    {/* voile sombre derrière les titres : lisibilité quel que soit le décor */}
    <AbsoluteFill
      style={{
        background: vertical
          ? `linear-gradient(180deg, rgba(7,3,15,${scrim}) 0%, rgba(7,3,15,${scrim * 0.6}) 22%, transparent 36%)`
          : `linear-gradient(90deg, rgba(7,3,15,${scrim}) 0%, rgba(7,3,15,${scrim * 0.6}) 30%, transparent 48%)`,
      }}
    />
    <AbsoluteFill
      style={{
        transform: `rotateY(${cam.ry * 0.3 * amount}deg) rotateX(${cam.rx * 0.3 * amount}deg) translate3d(${-cam.x * 0.03 * amount}px, ${-cam.y * 0.03 * amount}px, 0px)`,
        transformOrigin: "50% 50%",
      }}
    >
      {children}
    </AbsoluteFill>
  </AbsoluteFill>
  );
};
