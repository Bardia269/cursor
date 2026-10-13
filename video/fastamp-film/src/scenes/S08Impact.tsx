import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Glass, Hud, Obj, RingLight, Space, Void, camAt } from "../components/Space";
import { Sweep } from "../components/Sweep";
import { Headline, Kicker } from "../components/Headline";
import { Note } from "../components/Note";
import { Sfx } from "../components/Sfx";
import { prog, stampOpacity, stampScale } from "../components/anim";
import { useLayout } from "../components/layout";
import { PremiumBadge, Toggle } from "../components/ui";
import { C, FONT } from "../theme";

const T = { panel: 22, dots: 54, control: 168 };

// Positions déterministes (0 = début de la période, 0.3 = campagne). Illustration sans chiffres.
const VISITS = [0.04, 0.12, 0.2, 0.27, 0.36, 0.44, 0.52, 0.6, 0.69, 0.77, 0.86, 0.94];
const REWARDS = [0.12, 0.27, 0.42, 0.58, 0.75, 0.9];
const CONTROL_V = [0.06, 0.15, 0.24, 0.38, 0.5, 0.63, 0.74, 0.88];
const CONTROL_R = [0.2, 0.5, 0.8];

const Track: React.FC<{ dots: number[]; at: number; w: number; color: string; size: number; hollow?: boolean }> = ({ dots, at, w, color, size, hollow }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ position: "relative", height: size * 1.6 }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: size * 0.8, height: 2, background: "rgba(24,23,26,0.12)" }} />
      {dots.map((x, i) => {
        const f = at + i * 4;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x * w,
              top: size * 0.8,
              width: size,
              height: size,
              translate: "-50% -50%",
              borderRadius: "50%",
              background: hollow ? "transparent" : color,
              border: `${size * 0.2}px solid ${color}`,
              scale: String(stampScale(frame, f)),
              opacity: stampOpacity(frame, f),
            }}
          />
        );
      })}
    </div>
  );
};

const Tile: React.FC<{ title: string; w: number; k: number; main: number[]; control: number[]; at: number }> = ({ title, w, k, main, control, at }) => {
  const frame = useCurrentFrame();
  const inner = w - 56 * k;
  const ctl = prog(frame, T.control + 6, 14);
  return (
    <div style={{ width: w, padding: 28 * k, fontFamily: FONT, color: C.ink }}>
      <div style={{ fontSize: 30 * k, fontWeight: 700, letterSpacing: "-0.01em", marginBottom: 22 * k }}>{title}</div>
      <div style={{ position: "relative" }}>
        {/* Repère de campagne */}
        <div style={{ position: "absolute", left: 0.3 * inner, top: -10 * k, bottom: -10 * k, width: 2, background: C.deep }} />
        <div style={{ position: "absolute", left: 0.3 * inner + 10 * k, top: -14 * k, fontSize: 18 * k, fontWeight: 700, color: C.deep }}>Campagne</div>
        <div style={{ paddingTop: 22 * k }}>
          <div style={{ fontSize: 18 * k, color: "rgba(24,23,26,0.6)", fontWeight: 700 }}>Clients ciblés</div>
          <Track dots={main} at={at} w={inner} color={C.deep} size={26 * k} />
          <div style={{ opacity: ctl, marginTop: 10 * k }}>
            <div style={{ fontSize: 18 * k, color: "rgba(24,23,26,0.6)", fontWeight: 700 }}>Groupe témoin</div>
            <Track dots={control} at={T.control + 10} w={inner} color="#9C98A8" size={26 * k} hollow />
          </div>
        </div>
      </div>
    </div>
  );
};

// 08 — Impact observe : deux panneaux de verre en V, les visites apparaissent comme des perles,
// le groupe témoin optionnel sort de la profondeur pour comparer.
export const S08Impact: React.FC = () => {
  const frame = useCurrentFrame();
  const { v, pick } = useLayout();
  const tileW = pick(740, 860);
  const k = 1;
  const cam = camAt(frame, [
    { f: 0, x: pick(860, 0), y: pick(180, 330), z: -380, ry: pick(-16, 0), rx: -10 },
    { f: 120, x: pick(880, 0), y: pick(150, 330), z: -20, ry: pick(-4, 0), rx: -6 },
    { f: 255, x: pick(880, 0), y: pick(150, 330), z: 70, ry: pick(4, 0), rx: -5 },
  ]);
  const in1 = prog(frame, T.panel, 22, [0.2, 0.7, 0.1, 1]);
  const in2 = prog(frame, T.panel + 10, 22, [0.2, 0.7, 0.1, 1]);
  const tiles = v
    ? [
        { x: 0, y: 180, z: 0, ry: 0, inP: in1 },
        { x: 0, y: 600, z: 0, ry: 0, inP: in2 },
      ]
    : [
        { x: 470, y: 280, z: -60, ry: 16, inP: in1 },
        { x: 1290, y: 280, z: -60, ry: -16, inP: in2 },
      ];
  return (
    <AbsoluteFill>
      <Void glowX={50} glowY={pick(48, 60)} />
      <Space cam={cam} focus={-40} floor={pick(560, 900)} dof={0.008}>
        <Obj x={pick(1500, 260)} y={pick(-460, -120)} z={-1800} sharp>
          <RingLight size={320} intensity={0.75} />
        </Obj>
        {[0, 1].map((i) => (
          <Obj key={i} x={tiles[i].x} y={tiles[i].y + (1 - tiles[i].inP) * 160} z={tiles[i].z - (1 - tiles[i].inP) * 500} ry={tiles[i].ry}>
            <div style={{ opacity: tiles[i].inP }}>
              <Glass light radius={8} style={{ padding: 0, overflow: "hidden" }}>
                <div style={{ padding: "14px 28px 0", fontFamily: FONT }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 18, fontWeight: 700, color: "rgba(24,23,26,0.5)" }}>
                    Pilotage › Impact
                    <PremiumBadge size={17} at={T.panel + 6} />
                  </div>
                </div>
                <Tile
                  title={i === 0 ? "Visites après campagne" : "Récompenses utilisées"}
                  w={tileW}
                  k={k}
                  main={i === 0 ? VISITS : REWARDS}
                  control={i === 0 ? CONTROL_V : CONTROL_R}
                  at={T.dots + i * 20}
                />
              </Glass>
            </div>
          </Obj>
        ))}
        <Obj x={pick(880, 0)} y={pick(510, 900)} z={60}>
          <Glass radius={30} style={{ display: "flex", alignItems: "center", gap: 16, padding: "14px 26px", fontSize: 26, fontWeight: 700, fontFamily: FONT, opacity: prog(frame, T.control - 20, 12), whiteSpace: "nowrap" }}>
            <Toggle onAt={T.control} size={30} color={C.lavender} />
            Comparer avec un groupe témoin (optionnel)
          </Glass>
        </Obj>
        <Sweep from={pick(0, -500)} to={pick(1760, 500)} y={pick(280, 380)} z={40} at={T.dots + 50} dur={44} height={pick(460, 900)} />
      </Space>

      <Hud cam={cam} amount={0.4}>
        <div style={{ position: "absolute", left: pick(140, 90), top: pick(90, 170) }}>
          <Kicker text="Fastamp Impact" at={8} size={34} />
          <Headline
            size={84}
            style={{ marginTop: 24 }}
            lines={
              v
                ? [
                    { text: "Observez", at: 16 },
                    { text: "les retours après", at: 22, color: C.lavender },
                    { text: "campagne.", at: 28, color: C.lavender },
                  ]
                : [
                    { text: "Observez les retours", at: 16 },
                    { text: "après campagne.", at: 22, color: C.lavender },
                  ]
            }
          />
        </div>
      </Hud>
      <Note
        tone="night"
        at={60}
        text="Un retour observé n'est pas une vente supplémentaire prouvée · Données de démonstration"
        style={{ left: pick(140, 90), bottom: pick(50, 70), maxWidth: pick(1640, 900) }}
      />

      <Sfx name="whoosh" at={T.panel - 4} volume={0.4} />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Sfx key={i} name="tick" at={T.dots + i * 8} volume={0.3} />
      ))}
      <Sfx name="scan" at={T.dots + 50} volume={0.35} />
      <Sfx name="click" at={T.control} volume={0.6} />
      <Sfx name="swipe" at={T.control + 8} volume={0.35} />
    </AbsoluteFill>
  );
};
