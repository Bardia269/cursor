import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Background } from "../components/Background";
import { At, Float } from "../components/Float";
import { Headline, Sub } from "../components/Headline";
import { useLayout } from "../components/layout";
import { LOGO_SYMBOL_CENTER, LogoReveal } from "../components/LogoReveal";
import { Sfx } from "../components/Sfx";
import { WalletCard } from "../components/WalletCard";
import { prog } from "../components/anim";
import { C } from "../theme";

// 01 — La promesse. Les anneaux se posent un à un en gros plan, forment le symbole,
// la caméra recule sur le logo officiel, puis la carte arrive avec la promesse.
export const S01Promise: React.FC = () => {
  const frame = useCurrentFrame();
  const { W, H, pick } = useLayout();

  const AT = 10;
  const GAP = 7;
  // Logo : plan large centré, puis rangé en tête de composition.
  const Lw = pick(860, 860);
  const Lh = (Lw * 310) / 1100;
  const zoom = interpolate(frame, [AT + GAP * 5, AT + GAP * 6 + 34], [4.6, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.65, 0, 0.2, 1),
  });
  const zt = (4.6 - zoom) / 3.6; // 0 → 1 pendant le recul
  const sx = Lw * LOGO_SYMBOL_CENTER.x;
  const sy = Lh * LOGO_SYMBOL_CENTER.y;
  const left0 = (W - Lw) / 2;
  const top0 = (H - Lh) / 2;
  const dx0 = W / 2 - (left0 + sx);
  const dy0 = H / 2 - (top0 + sy);

  // Plongée dans l'anneau lavande : le logo s'efface et laisse place à la promesse.
  const dive = prog(frame, 116, 26, [0.7, 0, 0.84, 0]);
  const ax = Lw * ((393 - 225) / 1100);
  const ay = Lh * ((334 - 125) / 310);
  const left = left0;
  const top = top0;
  const cardIn = prog(frame, 128, 34);
  return (
    <AbsoluteFill>
      <Background tone="night" clearAt={pick("25% 50%", "50% 35%")} patternOpacity={0.1 * prog(frame, 100, 30)} />

      <div
        style={{
          position: "absolute",
          left,
          top,
          width: Lw,
          height: Lh,
          transformOrigin: `${ax}px ${ay}px`,
          scale: String(1 + dive * 14),
          opacity: 1 - prog(frame, 128, 12),
        }}
      >
        <div
          style={{
            width: Lw,
            height: Lh,
            transformOrigin: `${sx}px ${sy}px`,
            transform: `translate(${dx0 * (1 - zt)}px, ${dy0 * (1 - zt)}px) scale(${zoom})`,
          }}
        >
          <LogoReveal width={Lw} at={AT} gap={GAP} wipeAt={AT + GAP * 6 + 14} />
        </div>
      </div>

      <At
        x={pick(1390, W / 2)}
        y={pick(600, 1390) + (1 - cardIn) * 500}
        style={{ opacity: cardIn }}
      >
        <Float>
          <WalletCard width={pick(640, 820)} filled={6} />
        </Float>
      </At>

      <div style={{ position: "absolute", left: pick(140, 90), top: pick(330, 400), width: pick(860, 900) }}>
        <Headline
          size={pick(98, 96)}
          lines={[
            { text: "Une carte dans", at: 134 },
            { text: "leur téléphone.", at: 140 },
            { text: "Une raison", at: 178, color: C.lavender },
            { text: "de revenir.", at: 184, color: C.lavender },
          ]}
        />
        <Sub
          at={228}
          size={pick(38, 40)}
          text="Fastamp, la fidélité pensée pour les commerces indépendants."
          style={{ marginTop: 40, maxWidth: pick(700, 860), color: "rgba(250,249,252,0.86)" }}
        />
      </div>

      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Sfx key={i} name="stamp" at={AT + i * GAP} volume={0.55 + i * 0.05} />
      ))}
      <Sfx name="pop" at={AT + GAP * 6} volume={0.9} />
      <Sfx name="whoosh" at={AT + GAP * 5} volume={0.5} />
      <Sfx name="whoosh" at={114} volume={0.6} />
      <Sfx name="swipe" at={128} volume={0.5} />
    </AbsoluteFill>
  );
};
