import React from "react";
import { AbsoluteFill, interpolateColors, useCurrentFrame } from "remotion";
import { Background } from "../components/Background";
import { At, Float } from "../components/Float";
import { Headline } from "../components/Headline";
import { Note } from "../components/Note";
import { Sfx } from "../components/Sfx";
import { WalletCard } from "../components/WalletCard";
import { prog, stampScale } from "../components/anim";
import { useLayout } from "../components/layout";
import { C, FONT } from "../theme";

const T = { base: 8, logo: 32, color: 80, plum: 106, coral: 122, back: 140, banner: 152, stamps: 166 };

/** Annotation façon outil de design : pastille + filet lavande. */
const Callout: React.FC<{ at: number; label: string; x: number; y: number; dx: number; dy: number }> = ({ at, label, x, y, dx, dy }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, at, 14);
  const len = Math.hypot(dx, dy);
  const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
  return (
    <div style={{ position: "absolute", left: x, top: y, opacity: p }}>
      <div style={{ position: "absolute", width: 14, height: 14, borderRadius: "50%", background: C.lavender, left: -7, top: -7 }} />
      <div
        style={{
          position: "absolute",
          width: len * p,
          height: 2,
          background: C.lavender,
          transformOrigin: "0 50%",
          rotate: `${angle}deg`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: dx,
          top: dy,
          translate: `${dx < 0 ? "-100%" : "0"} -50%`,
          padding: "8px 16px",
          border: `2px solid ${C.lavender}`,
          borderRadius: 2,
          background: C.night,
          color: C.lavender,
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 28,
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </div>
    </div>
  );
};

// 03 — L'identité du commerce : logo, couleur, bannière se posent en couches.
export const S03Identity: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const cw = pick(720, 880);
  const ch = (cw * 404) / 640;
  const k = cw / 640;
  const color = interpolateColors(
    frame,
    [T.plum - 4, T.plum + 4, T.coral - 4, T.coral + 4, T.back - 4, T.back + 4],
    [C.cardBlue, C.cardPlum, C.cardPlum, C.cardCoral, C.cardCoral, C.cardBlue],
  );
  const layers = {
    logo: stampScale(frame, T.logo),
    color: prog(frame, T.color, 22),
    banner: prog(frame, T.banner, 18),
    stamps: prog(frame, T.stamps, 16),
  };
  const baseIn = prog(frame, T.base, 24);
  const cx = pick(1300, 540);
  const cy = pick(560, 1240);
  const left = cx - cw / 2;
  const top = cy - ch / 2;
  return (
    <AbsoluteFill>
      <Background tone="night" clearAt={pick("22% 45%", "50% 22%")} />
      <div style={{ position: "absolute", left: pick(140, 90), top: pick(330, 200) }}>
        <Headline
          size={pick(96, 96)}
          lines={[
            { text: "Votre logo.", at: T.logo - 4 },
            { text: "Vos couleurs.", at: T.color },
            { text: "Votre fidélité.", at: T.banner, color: C.lavender },
          ]}
        />
      </div>

      <At x={cx} y={cy + (1 - baseIn) * 80} style={{ opacity: baseIn }}>
        <Float amount={0.7}>
          <WalletCard width={cw} color={color} filled={6} layers={layers} />
        </Float>
      </At>

      <Callout at={T.logo + 4} label="Logo" x={left + (30 + 28) * k} y={top + (30 + 28) * k} dx={pick(-40, 10)} dy={-120 * k - 40} />
      <Callout at={T.color + 6} label="Couleur" x={left + cw - 70 * k} y={top + 140 * k} dx={pick(70, -60)} dy={pick(-190, -250) * k} />
      <Callout at={T.banner + 4} label="Bannière" x={left + 120 * k} y={top + (30 + 72 + 80) * k} dx={pick(-60, 40)} dy={pick(260, 330) * k} />

      <Note tone="night" at={40} text="Illustration — rendu variable selon le Wallet" style={{ left: pick(140, 90), bottom: pick(70, 110) }} />

      <Sfx name="whoosh" at={0} volume={0.55} />
      <Sfx name="stamp" at={T.logo} volume={0.8} />
      <Sfx name="swipe" at={T.color} volume={0.5} />
      <Sfx name="click" at={T.plum} volume={0.45} />
      <Sfx name="click" at={T.coral} volume={0.45} />
      <Sfx name="click" at={T.back} volume={0.45} />
      <Sfx name="swipe" at={T.banner} volume={0.45} />
      <Sfx name="pop" at={T.stamps} volume={0.5} />
    </AbsoluteFill>
  );
};
