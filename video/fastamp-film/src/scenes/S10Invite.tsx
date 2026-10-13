import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background } from "../components/Background";
import { At, Float } from "../components/Float";
import { Headline, Sub } from "../components/Headline";
import { LogoReveal } from "../components/LogoReveal";
import { Note } from "../components/Note";
import { Sfx } from "../components/Sfx";
import { WalletCard } from "../components/WalletCard";
import { prog } from "../components/anim";
import { useLayout } from "../components/layout";
import { Button, Qr } from "../components/ui";
import { C, FONT } from "../theme";

const T = { logo: 18, gap: 6, title: 70, cta: 108, url: 118, qr: 126, card: 40 };

// 10 — Invitation. Composition parfaitement stable à partir de ~5 s avant la fin.
export const S10Invite: React.FC = () => {
  const frame = useCurrentFrame();
  const { v, W, pick } = useLayout();
  const logoW = pick(680, 760);
  const qrIn = prog(frame, T.qr, 16);
  const cardIn = prog(frame, T.card, 30);
  return (
    <AbsoluteFill>
      <Background tone="night" clearAt={pick("25% 50%", "50% 30%")} />
      <div style={{ position: "absolute", left: pick(140, (W - logoW) / 2), top: pick(150, 170) }}>
        <LogoReveal width={logoW} at={T.logo} gap={T.gap} />
      </div>

      <div style={{ position: "absolute", left: pick(140, 0), right: pick(undefined, 0), top: pick(420, 470), textAlign: v ? "center" : "left" }}>
        <Headline
          size={pick(92, 92)}
          align={v ? "center" : "left"}
          lines={[
            { text: "Une fidélité", at: T.title },
            { text: "à votre image.", at: T.title + 6, color: C.lavender },
          ]}
        />
        <div style={{ marginTop: pick(48, 40), opacity: prog(frame, T.cta, 12), translate: `0px ${(1 - prog(frame, T.cta, 12)) * 20}px` }}>
          <Button label="Demandez une démonstration" size={pick(38, 40)} />
        </div>
        <Sub at={T.url} size={pick(38, 40)} weight={700} color={C.paper} text="fastamp.vercel.app" style={{ marginTop: 28, letterSpacing: "0.01em" }} />
      </div>

      <At x={pick(1440, W / 2)} y={pick(330, 1290) + (1 - cardIn) * 200} style={{ opacity: cardIn * pick(1, 1) }}>
        <Float>
          <WalletCard width={pick(560, 600)} filled={7} />
        </Float>
      </At>

      <div
        style={{
          position: "absolute",
          left: pick(1440, W / 2),
          top: pick(640, 1580),
          translate: "-50% 0",
          display: "flex",
          alignItems: "center",
          gap: 22,
          opacity: qrIn,
          fontFamily: FONT,
          color: C.paper,
        }}
      >
        <div style={{ padding: 10, background: "#fff", borderRadius: 4 }}>
          <Qr id="cta" size={pick(200, 190)} />
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, lineHeight: 1.3, width: 230 }}>
          Scannez pour demander une démo
        </div>
      </div>

      <Note tone="night" at={150} text="Besoins sur mesure : étudiés avec Fastamp, sans engagement de réalisation" style={{ left: pick(140, 90), bottom: pick(50, 70), maxWidth: pick(1600, 900) }} size={26} />

      <Sfx name="whoosh" at={0} volume={0.55} />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Sfx key={i} name="stamp" at={T.logo + i * T.gap} volume={0.45} />
      ))}
      <Sfx name="pop" at={T.logo + T.gap * 6} volume={0.8} />
      <Sfx name="swipe" at={T.card} volume={0.35} />
      <Sfx name="chime" at={T.cta} volume={0.5} />
    </AbsoluteFill>
  );
};
