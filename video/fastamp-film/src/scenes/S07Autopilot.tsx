import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Headline, Kicker } from "../components/Headline";
import { Note } from "../components/Note";
import { PilotHeader } from "../components/PilotHeader";
import { Ring } from "../components/Ring";
import { Sfx } from "../components/Sfx";
import { Glass, Hud, Obj, RingLight, Space, Void, camAt } from "../components/Space";
import { prog, stampOpacity, stampScale } from "../components/anim";
import { useLayout } from "../components/layout";
import { C, FONT } from "../theme";

const VISITS = [0, 260, 520, 780, 1040];
const RELANCE = 1980;
const T = { header: 14, visits: 30, gap: 84, relance: 132, chips: 150, log: 186 };

const Label: React.FC<{ text: string; at: number; color?: string; size?: number }> = ({ text, at, color = C.paper, size = 30 }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, at, 12);
  return (
    <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: size, color, whiteSpace: "nowrap", opacity: p, translate: `0px ${(1 - p) * 14}px`, textShadow: "0 2px 18px rgba(0,0,0,0.6)" }}>
      {text}
    </div>
  );
};

// 07 — Autopilot relance : travelling le long d'une piste de visites posées au sol ;
// le rythme s'interrompt, l'analyse quotidienne propose une relance, dans vos limites.
export const S07Autopilot: React.FC = () => {
  const frame = useCurrentFrame();
  const { v, pick } = useLayout();
  const Y = 120; // hauteur de la piste
  const cam = camAt(frame, [
    { f: 0, x: pick(-260, 200), y: pick(-60, -360), z: pick(-120, -480), ry: -26, rx: -10 },
    { f: T.gap, x: pick(560, 700), y: pick(-40, -340), z: pick(60, -280), ry: -20, rx: -9, ease: [0.45, 0, 0.55, 1] },
    { f: T.relance + 8, x: pick(1540, 1700), y: pick(-60, -360), z: pick(60, -260), ry: -14, rx: -8, ease: [0.45, 0, 0.4, 1] },
    { f: 255, x: pick(1660, 1820), y: pick(-60, -360), z: pick(100, -220), ry: -10, rx: -7, ease: [0.3, 0, 0.3, 1] },
  ]);
  const gapP = prog(frame, T.gap, 40, [0.4, 0, 0.6, 1]);
  const lastX = VISITS[VISITS.length - 1];
  const dashLen = (RELANCE - lastX - 140) * gapP;
  return (
    <AbsoluteFill>
      <Void glowX={pick(68, 55)} glowY={pick(45, 60)} />
      <Space cam={cam} focus={0} floor={Y + 40} dof={0.006}>
        <Obj x={RELANCE + 300} y={-520} z={-1500} sharp>
          <RingLight size={300} intensity={0.5 + 0.5 * prog(frame, T.relance, 20)} />
        </Obj>
        <Obj x={pick(160, 300)} y={-220} z={-420} ry={-8}>
          <Glass radius={6} style={{ width: 760, padding: "18px 24px", fontFamily: FONT, opacity: prog(frame, T.header, 18) }}>
            <PilotHeader module="Autopilot" k={1} dark badgeAt={T.header + 6} />
            <div style={{ fontSize: 22, color: "rgba(250,249,252,0.65)", marginTop: -8 }}>Camille — Démo · visites enregistrées</div>
          </Glass>
        </Obj>

        {/* Ligne de piste */}
        <Obj x={(lastX + 0) / 2} y={Y} z={0}>
          <div style={{ width: lastX + 200, height: 3, background: "rgba(250,249,252,0.35)", opacity: prog(frame, T.visits - 6, 12) }} />
        </Obj>
        {VISITS.map((x, i) => (
          <Obj key={i} x={x} y={Y - 60} z={0}>
            <div style={{ scale: String(stampScale(frame, T.visits + i * 7)), opacity: stampOpacity(frame, T.visits + i * 7) }}>
              <Ring size={110} color={C.paper} />
            </div>
          </Obj>
        ))}
        <Obj x={VISITS[2]} y={Y + 70} z={0}>
          <Label text="Un passage toutes les deux semaines environ" at={T.visits + 30} size={28} color="rgba(250,249,252,0.8)" />
        </Obj>

        {/* L'absence */}
        <Obj x={lastX + 70 + dashLen / 2} y={Y} z={0} sharp>
          <div style={{ width: Math.max(1, dashLen), height: 6, backgroundImage: `repeating-linear-gradient(90deg, ${C.lavender} 0 22px, transparent 22px 40px)`, filter: `drop-shadow(0 0 8px ${C.lavender})` }} />
        </Obj>
        <Obj x={(lastX + RELANCE) / 2} y={Y - 120} z={0}>
          <Label text={v ? "Absence inhabituelle" : "Absence plus longue que son rythme habituel"} at={T.gap + 18} color={C.lavender} size={34} />
        </Obj>

        {/* Relance proposée */}
        <Obj x={RELANCE} y={Y - 60} z={0} sharp>
          <div style={{ scale: String(stampScale(frame, T.relance)), opacity: stampOpacity(frame, T.relance) }}>
            <RingLight size={120} />
          </div>
        </Obj>
        <Obj x={RELANCE} y={Y + 80} z={0}>
          <Label text="Relance proposée" at={T.relance + 6} size={34} />
        </Obj>

        {/* Réglages et journal */}
        <Obj x={RELANCE + pick(-40, 0)} y={-210} z={-260} ry={-6}>
          <Glass radius={6} style={{ padding: "20px 24px", fontFamily: FONT, opacity: prog(frame, T.chips, 14) }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: "rgba(250,249,252,0.65)", marginBottom: 14 }}>Vos réglages</div>
            <div style={{ display: "flex", gap: 12 }}>
              {["Clients consentants", "Historique suffisant", "1 relance max. par mois"].map((c, i) => (
                <div
                  key={c}
                  style={{
                    padding: "10px 16px",
                    border: `2px solid ${C.lavender}`,
                    borderRadius: 2,
                    fontSize: 23,
                    fontWeight: 700,
                    whiteSpace: "nowrap",
                    opacity: prog(frame, T.chips + 4 + i * 7, 10),
                  }}
                >
                  {c}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 18, paddingTop: 14, borderTop: "1.5px solid rgba(199,185,232,0.2)", fontSize: 22, color: "rgba(250,249,252,0.85)", opacity: prog(frame, T.log, 12) }}>
              Journal · analyse quotidienne — 1 relance de démonstration préparée
            </div>
          </Glass>
        </Obj>
      </Space>

      <Hud cam={cam} amount={0.4}>
        <div style={{ position: "absolute", left: pick(140, 90), top: pick(110, 170) }}>
          <Kicker text="Fastamp Autopilot" at={8} size={34} />
          <Headline
            size={84}
            style={{ marginTop: 24 }}
            lines={
              v
                ? [
                    { text: "Des relances", at: 16 },
                    { text: "selon le rythme", at: 22, color: C.lavender },
                    { text: "de visite.", at: 28, color: C.lavender },
                  ]
                : [
                    { text: "Des relances selon", at: 16 },
                    { text: "le rythme de visite.", at: 22, color: C.lavender },
                  ]
            }
          />
        </div>
      </Hud>
      <Note tone="night" at={50} text="Analyse périodique des visites enregistrées, pas une surveillance en temps réel" style={{ left: pick(140, 90), bottom: pick(50, 70), maxWidth: pick(1600, 900) }} />

      {VISITS.map((_, i) => (
        <Sfx key={i} name="stamp" at={T.visits + i * 7} volume={0.4} />
      ))}
      <Sfx name="whoosh" at={T.gap} volume={0.5} />
      <Sfx name="pop" at={T.relance} volume={0.9} />
      <Sfx name="click" at={T.chips + 4} volume={0.35} />
      <Sfx name="click" at={T.chips + 11} volume={0.35} />
      <Sfx name="click" at={T.chips + 18} volume={0.35} />
    </AbsoluteFill>
  );
};
