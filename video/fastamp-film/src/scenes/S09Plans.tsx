import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from "remotion";
import { Hud, Obj, RingLight, Space, Void, camAt } from "../components/Space";
import { Headline } from "../components/Headline";
import { Ring } from "../components/Ring";
import { Sfx } from "../components/Sfx";
import { prog } from "../components/anim";
import { useLayout } from "../components/layout";
import { Star } from "../components/ui";
import { C, FONT } from "../theme";

const T = { flipA: 14, flipB: 26, flipDur: 32, title1: 64, title2: 92 };

const PlanCard: React.FC<{
  flipAt: number;
  w: number;
  h: number;
  premium?: boolean;
  title: string;
  lead?: string;
  items: string[];
}> = ({ flipAt, w, h, premium, title, lead, items }) => {
  const frame = useCurrentFrame();
  // Retournement de 180° autour de l'axe vertical, puis arrêt net face caméra.
  const rot = interpolate(frame, [flipAt, flipAt + T.flipDur], [180, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.65, 0, 0.25, 1),
  });
  const appear = prog(frame, flipAt - 10, 12);
  const face: React.CSSProperties = {
    position: "absolute",
    inset: 0,
    borderRadius: 22,
    backfaceVisibility: "hidden",
    WebkitBackfaceVisibility: "hidden",
    overflow: "hidden",
  };
  const fg = premium ? C.paper : C.ink;
  return (
    <div style={{ width: w, height: h, opacity: appear, transformStyle: "preserve-3d" }}>
      <div style={{ width: w, height: h, position: "relative", transformStyle: "preserve-3d", transform: `rotateY(${rot}deg)` }}>
        <div
          style={{
            ...face,
            background: premium ? C.deep : C.paper,
            border: premium ? `2px solid ${C.lavender}` : "none",
            boxShadow: "0 30px 60px rgba(0,0,0,0.35)",
            padding: 40,
            fontFamily: FONT,
            color: fg,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {premium ? <Star size={40} /> : <Ring size={40} variant="accent" color={C.deep} />}
            <div style={{ fontSize: 50, fontWeight: 700, letterSpacing: "-0.03em" }}>{title}</div>
          </div>
          {lead ? <div style={{ fontSize: 28, marginTop: 18, color: C.lavender, fontWeight: 700 }}>{lead}</div> : null}
          <div style={{ marginTop: lead ? 12 : 30, display: "flex", flexDirection: "column", gap: 12 }}>
            {items.map((it) => (
              <div key={it} style={{ fontSize: 32, display: "flex", alignItems: "center", gap: 14 }}>
                <span style={{ width: 12, height: 12, borderRadius: "50%", background: premium ? C.lavender : C.deep, flex: "none" }} />
                {it}
              </div>
            ))}
          </div>
        </div>
        {/* Dos de la carte : motif d'anneaux */}
        <div style={{ ...face, transform: "rotateY(180deg)", background: premium ? C.transit : "#E4DEF2", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Ring size={140} color={premium ? C.lavender : C.deep} />
        </div>
      </div>
    </div>
  );
};

// 09 — Choisir son niveau. Les deux offres se retournent dans l'espace, au-dessus du sol. Pas de prix.
export const S09Plans: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const w = pick(720, 860);
  const h = pick(440, 420);
  const cam = camAt(frame, [
    { f: 0, x: pick(-160, 0), y: pick(60, 140), z: -420, ry: 22, rx: -10 },
    { f: 80, x: 0, y: pick(90, 160), z: -60, ry: 4, rx: -6, ease: [0.3, 0, 0.3, 1] },
    { f: 210, x: pick(20, 0), y: pick(90, 160), z: 0, ry: -2, rx: -5 },
  ]);
  return (
    <AbsoluteFill>
      <Void glowX={50} glowY={pick(40, 45)} />
      <Space cam={cam} focus={0} floor={pick(430, 900)} dof={0.008}>
        <Obj x={pick(0, 0)} y={pick(-80, 300)} z={-2400} sharp>
          <RingLight size={340} intensity={0.8} />
        </Obj>
        <Obj x={pick(-400, 0)} y={pick(150, 40)} z={0} ry={pick(6, 0)} sharp>
          <PlanCard flipAt={T.flipA} w={w} h={h} title="Essentielle" items={["Cartes Wallet personnalisées", "Points ou tampons", "Scanner mobile", "Annonces globales"]} />
        </Obj>
        <Obj x={pick(400, 0)} y={pick(150, 520)} z={0} ry={pick(-6, 0)} sharp>
          <PlanCard flipAt={T.flipB} w={w} h={h} premium title="Premium" lead="Tout Essentielle, plus :" items={["Campagnes ciblées", "Signals", "Autopilot", "Impact"]} />
        </Obj>
      </Space>
      <Hud cam={cam} amount={0.3} scrim={0}>
        <div style={{ position: "absolute", top: pick(80, 170), left: 0, right: 0, display: "flex", justifyContent: "center" }}>
          <Headline
            size={pick(80, 88)}
            align="center"
            lines={[
              { text: "Commencer simplement.", at: T.title1 },
              { text: "Aller plus loin.", at: T.title2, color: C.lavender },
            ]}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", textShadow: "0 4px 30px rgba(7,3,15,0.9)" }}
          />
        </div>
      </Hud>
      <Sfx name="whoosh" at={T.flipA - 6} volume={0.4} />
      <Sfx name="swipe" at={T.flipA} volume={0.5} />
      <Sfx name="swipe" at={T.flipB} volume={0.5} />
      <Sfx name="click" at={T.flipA + T.flipDur} volume={0.4} />
      <Sfx name="click" at={T.flipB + T.flipDur} volume={0.4} />
          </AbsoluteFill>
  );
};
