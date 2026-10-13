import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background } from "../components/Background";
import { Headline, Kicker } from "../components/Headline";
import { Note } from "../components/Note";
import { PilotHeader } from "../components/PilotHeader";
import { Ring } from "../components/Ring";
import { Sfx } from "../components/Sfx";
import { prog, stampOpacity, stampScale } from "../components/anim";
import { useLayout } from "../components/layout";
import { Panel } from "../components/ui";
import { C } from "../theme";

const VISITS = [0.04, 0.15, 0.26, 0.37, 0.48];
const T = { panel: 24, visits: 44, gap: 86, relance: 128, chips: 150, log: 186 };

// 07 — Autopilot relance : rythme de visite, absence inhabituelle, réglages et limites.
export const S07Autopilot: React.FC = () => {
  const frame = useCurrentFrame();
  const { v, pick } = useLayout();
  const pw = pick(1640, 900);
  const k = pick(1, 0.9);
  const panel = { left: pick(140, 90), top: pick(440, 760) };
  const panelIn = prog(frame, T.panel, 22);
  const lineW = pw - 60 * k - 60;
  const lastX = VISITS[VISITS.length - 1] * lineW;
  const relX = 0.86 * lineW;
  const gapP = prog(frame, T.gap, 30);
  const chip = (i: number, label: string) => {
    const p = prog(frame, T.chips + i * 7, 12);
    return (
      <div
        key={label}
        style={{
          padding: `${10 * k}px ${18 * k}px`,
          border: `2px solid ${C.lavender}`,
          borderRadius: 2,
          color: C.paper,
          fontSize: 23 * k,
          fontWeight: 700,
          opacity: p,
          translate: `0px ${(1 - p) * 14}px`,
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </div>
    );
  };
  return (
    <AbsoluteFill>
      <Background tone="night" clearAt={pick("30% 20%", "50% 15%")} />
      <div style={{ position: "absolute", left: pick(140, 90), top: pick(110, 170) }}>
        <Kicker text="Fastamp Autopilot" at={8} size={34} />
        <Headline
          size={pick(84, 84)}
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

      <div style={{ position: "absolute", left: panel.left, top: panel.top, opacity: panelIn, translate: `0px ${(1 - panelIn) * 40}px` }}>
        <Panel tone="dark" style={{ width: pw, padding: 30 * k }}>
          <PilotHeader module="Autopilot" k={k} dark badgeAt={T.panel + 6} />
          <div style={{ fontSize: 22 * k, fontWeight: 700, color: "rgba(250,249,252,0.65)", marginBottom: 30 * k }}>
            Camille — Démo · visites enregistrées
          </div>
          {/* Chronologie des visites */}
          <div style={{ position: "relative", height: 130 * k, marginLeft: 30, marginTop: 50 * k }}>
            <div style={{ position: "absolute", left: 0, right: 0, top: 30 * k, height: 2, background: "rgba(250,249,252,0.25)" }} />
            {VISITS.map((x, i) => (
              <div key={i} style={{ position: "absolute", left: x * lineW, top: 30 * k, translate: "-50% -50%" }}>
                <Ring
                  size={50 * k}
                  color={C.paper}
                  style={{ scale: String(stampScale(frame, T.visits + i * 6)), opacity: stampOpacity(frame, T.visits + i * 6) }}
                />
              </div>
            ))}
            {/* Absence plus longue que d'habitude */}
            <svg style={{ position: "absolute", left: lastX + 34 * k, top: 30 * k - 2, overflow: "visible" }} width={1} height={1}>
              <line x1={0} y1={2} x2={(relX - lastX - 68 * k) * gapP} y2={2} stroke={C.lavender} strokeWidth={4} strokeDasharray="10 9" />
            </svg>
            <div
              style={{
                position: "absolute",
                left: (lastX + relX) / 2,
                top: -24 * k,
                translate: "-50% -100%",
                color: C.lavender,
                fontSize: 23 * k,
                fontWeight: 700,
                opacity: prog(frame, T.gap + 16, 12),
                whiteSpace: "nowrap",
              }}
            >
              {v ? "Absence inhabituelle" : "Absence plus longue que son rythme habituel"}
            </div>
            <div style={{ position: "absolute", left: relX, top: 30 * k, translate: "-50% -50%" }}>
              <Ring size={56 * k} variant="accent" color={C.lavender} style={{ scale: String(stampScale(frame, T.relance)), opacity: stampOpacity(frame, T.relance) }} />
            </div>
            <div
              style={{
                position: "absolute",
                left: relX,
                top: 72 * k,
                translate: v ? "-80% 0" : "-50% 0",
                color: C.paper,
                fontSize: 23 * k,
                fontWeight: 700,
                opacity: prog(frame, T.relance + 4, 12),
                whiteSpace: "nowrap",
                display: v ? "none" : "block",
              }}
            >
              Relance proposée
            </div>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 14 * k, marginTop: 20 * k, alignItems: "center" }}>
            <div style={{ fontSize: 22 * k, color: "rgba(250,249,252,0.6)", fontWeight: 700, marginRight: 6, opacity: prog(frame, T.chips, 10) }}>Vos réglages</div>
            {chip(0, "Clients consentants")}
            {chip(1, "Historique suffisant")}
            {chip(2, "1 relance max. par mois")}
          </div>
          <div
            style={{
              marginTop: 24 * k,
              paddingTop: 18 * k,
              borderTop: "1.5px solid rgba(199,185,232,0.2)",
              fontSize: 22 * k,
              color: "rgba(250,249,252,0.8)",
              opacity: prog(frame, T.log, 12),
            }}
          >
            Journal · analyse quotidienne — 1 relance de démonstration préparée
          </div>
        </Panel>
      </div>

      <Note tone="night" at={50} text="Analyse périodique des visites enregistrées, pas une surveillance en temps réel" style={{ left: pick(140, 90), bottom: pick(50, 90), maxWidth: pick(1600, 900) }} />

      <Sfx name="whoosh" at={0} volume={0.55} />
      {VISITS.map((_, i) => (
        <Sfx key={i} name="stamp" at={T.visits + i * 6} volume={0.35} />
      ))}
      <Sfx name="swipe" at={T.gap} volume={0.35} />
      <Sfx name="pop" at={T.relance} volume={0.8} />
      <Sfx name="click" at={T.chips} volume={0.35} />
      <Sfx name="click" at={T.chips + 7} volume={0.35} />
      <Sfx name="click" at={T.chips + 14} volume={0.35} />
    </AbsoluteFill>
  );
};
