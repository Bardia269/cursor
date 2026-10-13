import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Headline, Sub } from "../components/Headline";
import { LOGO_RINGS_LANDED, Logo3D } from "../components/Logo3D";
import { Note } from "../components/Note";
import { Sfx } from "../components/Sfx";
import { Hud, Obj, RingLight, Space, Void, camAt } from "../components/Space";
import { WalletCard } from "../components/WalletCard";
import { float, prog } from "../components/anim";
import { useLayout } from "../components/layout";
import { Button, Qr } from "../components/ui";
import { C, FONT } from "../theme";

const T = { logo: 10, title: 84, cta: 112, url: 122, qr: 130, card: 46, settle: 140 };

// 10 — Invitation. Le logo se reforme dans l'espace, puis la caméra s'immobilise :
// composition parfaitement stable pendant les 5 dernières secondes.
export const S10Invite: React.FC = () => {
  const frame = useCurrentFrame();
  const { v, W, pick } = useLayout();
  const logoW = pick(700, 800);
  const cam = camAt(frame, [
    { f: 0, x: pick(-320, 0), y: pick(-120, -300), z: -560, ry: 20, rx: 6 },
    { f: LOGO_RINGS_LANDED(T.logo) + 6, x: pick(-40, 0), y: pick(-20, -40), z: -60, ry: 3, rx: 1, ease: [0.25, 0.1, 0.25, 1] },
    { f: T.settle, x: 0, y: 0, z: 0, ry: 0, rx: 0, ease: [0.3, 0, 0.2, 1] },
  ]);
  const cardIn = prog(frame, T.card, 34);
  // le flottement de la carte s'éteint avant la composition finale
  const fl = float(frame, 30);
  const still = 1 - prog(frame, T.settle - 20, 30);
  const qrIn = prog(frame, T.qr, 16);
  return (
    <AbsoluteFill>
      <Void glowX={pick(72, 50)} glowY={pick(36, 62)} />
      <Space cam={cam} focus={0} floor={pick(470, 980)} dof={0.008}>
        <Obj x={pick(560, 220)} y={pick(-470, 140)} z={-1700} sharp>
          <RingLight size={320} intensity={0.85} />
        </Obj>
        <Logo3D cx={pick(-470, 0)} cy={pick(-300, -640)} cz={0} width={logoW} at={T.logo} />
        <Obj x={pick(470, 0)} y={pick(-150, 340) + fl.y * still + (1 - cardIn) * 260} z={-60} ry={pick(-12, -6) + fl.ry * still} rx={4 + fl.rx * still}>
          <div style={{ opacity: cardIn }}>
            <WalletCard width={pick(560, 640)} filled={7} />
          </div>
        </Obj>
      </Space>

      <Hud cam={cam} amount={0.3} scrim={0}>
        <div style={{ position: "absolute", left: pick(140, 0), right: pick(undefined, 0), top: pick(440, 470), textAlign: v ? "center" : "left" }}>
          <Headline
            size={92}
            align={v ? "center" : "left"}
            lines={[
              { text: "Une fidélité", at: T.title },
              { text: "à votre image.", at: T.title + 6, color: C.lavender },
            ]}
          />
          <div style={{ marginTop: pick(46, 40), opacity: prog(frame, T.cta, 12), translate: `0px ${(1 - prog(frame, T.cta, 12)) * 20}px` }}>
            <Button label="Demandez une démonstration" size={pick(38, 40)} style={{ boxShadow: "0 0 40px rgba(199,185,232,0.45), 5px 5px 0 rgba(0,0,0,0.4)" }} />
          </div>
          <Sub at={T.url} size={pick(38, 40)} weight={700} color={C.paper} text="fastamp.vercel.app" style={{ marginTop: 28, letterSpacing: "0.01em" }} />
        </div>
        <div
          style={{
            position: "absolute",
            left: pick(1440, W / 2),
            top: pick(660, 1560),
            translate: "-50% 0",
            display: "flex",
            alignItems: "center",
            gap: 22,
            opacity: qrIn,
            fontFamily: FONT,
            color: C.paper,
          }}
        >
          <div style={{ padding: 10, background: "#fff", borderRadius: 6, boxShadow: "0 0 50px rgba(199,185,232,0.35)" }}>
            <Qr id="cta" size={pick(200, 190)} />
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, lineHeight: 1.3, width: 230 }}>Scannez pour demander une démo</div>
        </div>
      </Hud>

      <Note tone="night" at={150} text="Besoins sur mesure : étudiés avec Fastamp, sans engagement de réalisation" style={{ left: pick(140, 90), bottom: pick(50, 70), maxWidth: pick(1600, 900) }} size={26} />

      <Sfx name="whoosh" at={0} volume={0.4} />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Sfx key={i} name="stamp" at={T.logo + i * 6 + 34} volume={0.45} />
      ))}
      <Sfx name="pop" at={LOGO_RINGS_LANDED(T.logo)} volume={0.8} />
      <Sfx name="swipe" at={T.card} volume={0.35} />
      <Sfx name="chime" at={T.cta} volume={0.5} />
    </AbsoluteFill>
  );
};
