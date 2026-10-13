import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background } from "../components/Background";
import { Headline, Kicker } from "../components/Headline";
import { Note } from "../components/Note";
import { PilotHeader } from "../components/PilotHeader";
import { Sfx } from "../components/Sfx";
import { prog, stampOpacity, stampScale } from "../components/anim";
import { useLayout } from "../components/layout";
import { Panel, Toggle } from "../components/ui";
import { C } from "../theme";

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
    <div style={{ width: w, padding: 28 * k, border: "1.5px solid rgba(35,10,92,0.14)", borderRadius: 2, background: "#fff" }}>
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

// 08 — Impact observe : visites et récompenses après campagne, groupe témoin optionnel.
export const S08Impact: React.FC = () => {
  const frame = useCurrentFrame();
  const { v, pick } = useLayout();
  const pw = pick(1640, 900);
  const k = pick(1, 0.95);
  const panel = { left: pick(140, 90), top: pick(420, 600) };
  const panelIn = prog(frame, T.panel, 22);
  const tileW = v ? pw - 60 * k : (pw - 60 * k - 30) / 2;
  return (
    <AbsoluteFill>
      <Background tone="paper" clearAt={pick("30% 20%", "50% 15%")} />
      <div style={{ position: "absolute", left: pick(140, 90), top: pick(100, 170) }}>
        <Kicker text="Fastamp Impact" at={8} size={34} color={C.deep} />
        <Headline
          size={pick(84, 84)}
          color={C.ink}
          style={{ marginTop: 24 }}
          lines={
            v
              ? [
                  { text: "Observez", at: 16 },
                  { text: "les retours après", at: 22, color: C.deep },
                  { text: "campagne.", at: 28, color: C.deep },
                ]
              : [
                  { text: "Observez les retours", at: 16 },
                  { text: "après campagne.", at: 22, color: C.deep },
                ]
          }
        />
      </div>
      <div style={{ position: "absolute", left: panel.left, top: panel.top, opacity: panelIn, translate: `0px ${(1 - panelIn) * 40}px` }}>
        <Panel style={{ width: pw, padding: 30 * k, background: "#F6F4FA" }}>
          <PilotHeader module="Impact" k={k} badgeAt={T.panel + 6} />
          <div style={{ display: "flex", flexDirection: v ? "column" : "row", gap: 30 }}>
            <Tile title="Visites après campagne" w={tileW} k={k} main={VISITS} control={CONTROL_V} at={T.dots} />
            <Tile title="Récompenses utilisées" w={tileW} k={k} main={REWARDS} control={CONTROL_R} at={T.dots + 20} />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 24 * k, fontSize: 24 * k, fontWeight: 700, opacity: prog(frame, T.control - 20, 12) }}>
            <Toggle onAt={T.control} size={30 * k} />
            Comparer avec un groupe témoin (optionnel)
          </div>
        </Panel>
      </div>

      <Note
        tone="paper"
        at={60}
        text="Un retour observé n'est pas une vente supplémentaire prouvée · Données de démonstration"
        style={{ left: pick(140, 90), bottom: pick(50, 90), maxWidth: pick(1640, 900) }}
      />

      <Sfx name="whoosh" at={0} volume={0.55} />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Sfx key={i} name="tick" at={T.dots + i * 8} volume={0.3} />
      ))}
      <Sfx name="click" at={T.control} volume={0.6} />
    </AbsoluteFill>
  );
};
