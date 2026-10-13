import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Glass, Hud, Obj, RingLight, Space, Void, camAt } from "../components/Space";
import { Sweep } from "../components/Sweep";
import { Headline, Kicker, Sub } from "../components/Headline";
import { Note } from "../components/Note";
import { PilotHeader } from "../components/PilotHeader";
import { Ring } from "../components/Ring";
import { Sfx } from "../components/Sfx";
import { prog, typed } from "../components/anim";
import { useLayout } from "../components/layout";
import { Button } from "../components/ui";
import { C, FONT } from "../theme";

const T = { panel: 20, row1: 40, row2: 50, focus: 72, prepare: 92, draft: 100, type: 108, validate: 172, press: 204 };
const DRAFT = "Plus qu'un passage avant votre boisson offerte. À très vite à la Maison Centrale !";

// 06 — Signals recommande : des signaux issus des données, un brouillon, une validation humaine.
export const S06Signals: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const pw = pick(900, 880);
  const k = pw / 900;
  const panelIn = prog(frame, T.panel, 22);
  const focus = prog(frame, T.focus, 12);
  const draftIn = prog(frame, T.draft, 14);
  const row = (title: string, detail: string, highlight: number, children?: React.ReactNode) => (
    <Glass light radius={6} style={{ width: pw, display: "flex", alignItems: "center", gap: 18 * k, padding: `${20 * k}px ${24 * k}px`, fontFamily: FONT, ...(highlight > 0.5 ? { background: "linear-gradient(160deg, #F1ECFC, #E3DAF7)", border: `2px solid ${C.deep}` } : {}) }}>
      <Ring size={46 * k} variant="accent" color={C.deep} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 28 * k, fontWeight: 700 }}>{title}</div>
        <div style={{ fontSize: 21 * k, color: "rgba(24,23,26,0.62)", marginTop: 4 * k }}>{detail}</div>
      </div>
      {children}
    </Glass>
  );
  const cx = pick(770, 0);
  const cy = pick(70, 380);
  const cam = camAt(frame, [
    { f: 0, x: pick(330, 0), y: pick(-20, 120), z: -340, ry: 26, rx: -8 },
    { f: T.focus + 10, x: pick(380, 0), y: pick(60, 130), z: 80, ry: 14, rx: -5 },
    { f: T.validate, x: pick(400, 0), y: pick(110, 190), z: 100, ry: 8, rx: -3 },
    { f: 255, x: pick(400, 0), y: pick(110, 200), z: 120, ry: 5, rx: -2 },
  ]);
  const in1 = prog(frame, T.row1, 18, [0.2, 0.7, 0.1, 1]);
  const in2 = prog(frame, T.row2, 18, [0.2, 0.7, 0.1, 1]);
  const draftZ = (1 - draftIn) * 700;
  return (
    <AbsoluteFill>
      <Void glowX={pick(65, 50)} glowY={pick(42, 62)} />
      <Space cam={cam} focus={60} floor={pick(420, 900)} dof={0.009}>
        <Obj x={cx + pick(420, 200)} y={cy - pick(520, 640)} z={-1700} sharp>
          <RingLight size={300} intensity={0.85} />
        </Obj>
        <Obj x={cx} y={cy - 250 * k} z={-240} ry={-6}>
          <Glass radius={6} style={{ width: pw, padding: `${18 * k}px ${24 * k}px`, fontFamily: FONT, opacity: panelIn }}>
            <PilotHeader module="Signals" k={k} dark badgeAt={T.panel + 6} />
            <div style={{ fontSize: 20 * k, color: "rgba(250,249,252,0.6)", marginTop: -8 }}>Signaux issus des visites enregistrées</div>
          </Glass>
        </Obj>
        <Obj x={cx} y={cy - 80 * k} z={-120 + (1 - in1) * 600 + focus * 140} ry={-6 + focus * 4}>
          <div style={{ opacity: in1 }}>
            {row(
              "Clients proches d'une récompense",
              "Il leur manque 1 tampon",
              focus,
              <div style={{ opacity: prog(frame, T.focus + 4, 10) }}>
                <Button label="Préparer une notification" pressAt={T.prepare} size={20 * k} />
              </div>,
            )}
          </div>
        </Obj>
        <Obj x={cx} y={cy + 50 * k} z={-120 + (1 - in2) * 600} ry={-6}>
          <div style={{ opacity: in2 * (1 - focus * 0.45) }}>{row("Clients sans deuxième visite", "Venus une seule fois", 0)}</div>
        </Obj>
        <Obj x={cx} y={cy + 250 * k} z={60 + draftZ} ry={-4}>
          <Glass radius={6} style={{ width: pw, padding: 24 * k, fontFamily: FONT, opacity: draftIn, border: `1.5px dashed ${C.lavender}`, boxShadow: "0 0 40px rgba(199,185,232,0.35), 0 40px 80px rgba(0,0,0,0.5)" }}>
            <div style={{ fontSize: 19 * k, fontWeight: 700, letterSpacing: "0.04em", color: C.lavender }}>Brouillon assisté par IA · à relire</div>
            <div style={{ fontSize: 28 * k, lineHeight: 1.35, marginTop: 10 * k, minHeight: 76 * k }}>{typed(DRAFT, frame, T.type, 42)}</div>
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 14 * k, opacity: prog(frame, T.validate, 10) }}>
              <Button label="Valider avant envoi" pressedLabel="Validé par vous" pressAt={T.press} size={22 * k} />
            </div>
          </Glass>
        </Obj>
        <Sweep from={cx - pw / 2 - 100} to={cx + pw / 2 + 100} y={cy} z={-60} at={T.row2 + 6} dur={34} height={560} ry={-6} />
      </Space>

      <Hud cam={cam} amount={0.5}>
        <div style={{ position: "absolute", left: pick(140, 90), top: pick(300, 170), width: pick(620, 900) }}>
          <Kicker text="Fastamp Signals" at={8} size={34} />
          <Headline
            size={pick(92, 92)}
            style={{ marginTop: 26 }}
            lines={[
              { text: "Des données", at: 16 },
              { text: "aux actions.", at: 22, color: C.lavender },
            ]}
          />
          <Sub at={T.validate} size={pick(34, 38)} color="rgba(250,249,252,0.82)" text="L'assistance IA prépare. Vous validez avant l'envoi." style={{ marginTop: 30, maxWidth: pick(560, 900) }} />
        </div>
      </Hud>
      <Note tone="night" at={40} text="Données de démonstration · suggestions issues des visites enregistrées" style={{ left: pick(140, 90), bottom: pick(60, 70), maxWidth: pick(1600, 900) }} />

      <Sfx name="whoosh" at={T.row1 - 4} volume={0.35} />
      <Sfx name="pop" at={T.row1 + 14} volume={0.4} />
      <Sfx name="pop" at={T.row2 + 14} volume={0.35} />
      <Sfx name="scan" at={T.row2 + 6} volume={0.4} />
      <Sfx name="click" at={T.prepare} volume={0.7} />
      <Sfx name="whoosh" at={T.draft - 4} volume={0.4} />
      {Array.from({ length: 16 }).map((_, i) => (
        <Sfx key={i} name="tick" at={T.type + i * 4} volume={0.2} />
      ))}
      <Sfx name="click" at={T.press} volume={0.8} />
    </AbsoluteFill>
  );
};
