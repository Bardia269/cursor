import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background } from "../components/Background";
import { Headline, Kicker, Sub } from "../components/Headline";
import { Note } from "../components/Note";
import { PilotHeader } from "../components/PilotHeader";
import { Ring } from "../components/Ring";
import { Sfx } from "../components/Sfx";
import { prog, typed } from "../components/anim";
import { useLayout } from "../components/layout";
import { Button, Panel, Tap } from "../components/ui";
import { C } from "../theme";

const T = { panel: 20, row1: 40, row2: 50, focus: 72, prepare: 92, draft: 100, type: 108, validate: 172, press: 204 };
const DRAFT = "Plus qu'un passage avant votre boisson offerte. À très vite à la Maison Centrale !";

// 06 — Signals recommande : des signaux issus des données, un brouillon, une validation humaine.
export const S06Signals: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const pw = pick(900, 900);
  const k = pw / 900;
  const panel = { left: pick(880, 90), top: pick(220, 720) };
  const panelIn = prog(frame, T.panel, 22);
  const focus = prog(frame, T.focus, 12);
  const draftIn = prog(frame, T.draft, 14);
  const row = (at: number, title: string, detail: string, highlight: number, children?: React.ReactNode) => {
    const p = prog(frame, at, 14);
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 18 * k,
          padding: `${18 * k}px ${20 * k}px`,
          marginBottom: 14 * k,
          borderRadius: 2,
          border: `1.5px solid ${highlight > 0.5 ? C.deep : "rgba(35,10,92,0.12)"}`,
          background: `rgba(199,185,232,${0.35 * highlight})`,
          opacity: p,
          translate: `${(1 - p) * 30}px 0px`,
        }}
      >
        <Ring size={44 * k} variant="accent" color={C.deep} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 27 * k, fontWeight: 700 }}>{title}</div>
          <div style={{ fontSize: 21 * k, color: "rgba(24,23,26,0.62)", marginTop: 4 * k }}>{detail}</div>
        </div>
        {children}
      </div>
    );
  };
  return (
    <AbsoluteFill>
      <Background tone="paper" clearAt={pick("20% 45%", "50% 18%")} />
      <div style={{ position: "absolute", left: pick(140, 90), top: pick(300, 170), width: pick(680, 900) }}>
        <Kicker text="Fastamp Signals" at={8} size={34} color={C.deep} />
        <Headline
          size={pick(92, 92)}
          color={C.ink}
          style={{ marginTop: 26 }}
          lines={[
            { text: "Des données", at: 16 },
            { text: "aux actions.", at: 22, color: C.deep },
          ]}
        />
        <Sub at={T.validate} size={pick(36, 38)} color="rgba(24,23,26,0.78)" text="L'assistance IA prépare. Vous validez avant l'envoi." style={{ marginTop: 30, maxWidth: pick(600, 900) }} />
      </div>

      <div style={{ position: "absolute", left: panel.left, top: panel.top, opacity: panelIn, translate: `0px ${(1 - panelIn) * 40}px` }}>
        <Panel style={{ width: pw, padding: 30 * k }}>
          <PilotHeader module="Signals" k={k} badgeAt={T.panel + 6} />
          {row(
            T.row1,
            "Clients proches d'une récompense",
            "Il leur manque 1 tampon",
            focus,
            <div style={{ opacity: prog(frame, T.focus + 4, 10) }}>
              <Button label="Préparer une notification" pressAt={T.prepare} size={20 * k} />
            </div>,
          )}
          {row(T.row2, "Clients sans deuxième visite", "Venus une seule fois", 0)}
          <div
            style={{
              marginTop: 18 * k,
              padding: 22 * k,
              border: `1.5px dashed ${C.deep}`,
              borderRadius: 2,
              opacity: draftIn,
              translate: `0px ${(1 - draftIn) * 20}px`,
            }}
          >
            <div style={{ fontSize: 19 * k, fontWeight: 700, letterSpacing: "0.04em", color: C.deep }}>Brouillon assisté par IA · à relire</div>
            <div style={{ fontSize: 27 * k, lineHeight: 1.35, marginTop: 10 * k, minHeight: 74 * k }}>{typed(DRAFT, frame, T.type, 42)}</div>
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 14 * k, opacity: prog(frame, T.validate, 10) }}>
              <Button label="Valider avant envoi" pressedLabel="Validé par vous" pressAt={T.press} size={22 * k} tone="deep" />
            </div>
          </div>
        </Panel>
      </div>
      <Tap at={T.prepare} x={panel.left + pw - 190 * k} y={panel.top + (30 + 62 + 22 + 50) * k} />
      <Tap at={T.press} x={panel.left + pw - 160 * k} y={panel.top + pick(625, 625) * k} color={C.lavender} />

      <Note tone="paper" at={40} text="Données de démonstration · suggestions issues des visites enregistrées" style={{ left: pick(140, 90), bottom: pick(60, 90), maxWidth: pick(1600, 900) }} />

      <Sfx name="whoosh" at={0} volume={0.55} />
      <Sfx name="pop" at={T.row1} volume={0.4} />
      <Sfx name="pop" at={T.row2} volume={0.35} />
      <Sfx name="click" at={T.prepare} volume={0.7} />
      {Array.from({ length: 16 }).map((_, i) => (
        <Sfx key={i} name="tick" at={T.type + i * 4} volume={0.2} />
      ))}
      <Sfx name="click" at={T.press} volume={0.8} />
    </AbsoluteFill>
  );
};
