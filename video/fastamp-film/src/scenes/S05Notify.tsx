import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background } from "../components/Background";
import { Phone } from "../components/Devices";
import { At } from "../components/Float";
import { Headline, Sub } from "../components/Headline";
import { Note } from "../components/Note";
import { Sfx } from "../components/Sfx";
import { WalletCard } from "../components/WalletCard";
import { prog, typed } from "../components/anim";
import { useLayout } from "../components/layout";
import { Button, Panel, Tap, Toggle } from "../components/ui";
import { C } from "../theme";

const T = { panel: 26, title: 52, msg: 80, audience: 112, send: 140, travel: 144, alert: 172 };
const TITLE = "La carte d'automne est arrivée";
const MSG = "Passez nous voir à la Maison Centrale.";

// 05 — Garder le lien : une annonce, envoyée aux clients qui l'ont acceptée, via la carte Wallet.
export const S05Notify: React.FC = () => {
  const frame = useCurrentFrame();
  const { v, pick } = useLayout();
  const pw = pick(760, 900);
  const pk = pw / 760;
  const panelIn = prog(frame, T.panel, 20);
  const panel = { left: pick(140, 90), top: pick(470, 560) };
  const phoneW = pick(340, 380);
  const phone = { x: pick(1500, 540), y: pick(560, 1400) };
  const travel = prog(frame, T.travel, 28, [0.65, 0, 0.35, 1]);
  const alert = prog(frame, T.alert, 16);
  // Départ : bouton « Envoyer » ; arrivée : téléphone.
  const sx = panel.left + pw - 60 * pk;
  const sy = panel.top + 400 * pk;
  const ex = phone.x;
  const ey = phone.y - phoneW * 0.6;
  const cx1 = v ? sx : (sx + ex) / 2;
  const cy1 = v ? sy + 260 : sy + 180;
  const path = `M ${sx} ${sy} Q ${cx1} ${cy1} ${ex} ${ey}`;
  const pt = (t: number) => ({
    x: (1 - t) * (1 - t) * sx + 2 * (1 - t) * t * cx1 + t * t * ex,
    y: (1 - t) * (1 - t) * sy + 2 * (1 - t) * t * cy1 + t * t * ey,
  });
  const dot = pt(travel);
  const field = (label: string, value: string, at: number) => (
    <div style={{ marginBottom: 22 * pk }}>
      <div style={{ fontSize: 20 * pk, fontWeight: 700, color: "rgba(24,23,26,0.55)", marginBottom: 8 * pk }}>{label}</div>
      <div
        style={{
          minHeight: 58 * pk,
          border: `1.5px solid ${frame >= at && frame < at + 30 ? C.deep : "rgba(24,23,26,0.2)"}`,
          borderRadius: 2,
          padding: `${12 * pk}px ${16 * pk}px`,
          fontSize: 26 * pk,
          color: C.ink,
        }}
      >
        {typed(value, frame, at, 40)}
      </div>
    </div>
  );
  return (
    <AbsoluteFill>
      <Background tone="night" clearAt={pick("25% 35%", "50% 20%")} />
      <div style={{ position: "absolute", left: pick(140, 90), top: pick(130, 170) }}>
        <Headline size={pick(92, 96)} lines={[{ text: "Gardez le contact.", at: 16 }]} />
        <Sub at={44} size={pick(40, 42)} weight={700} color={C.lavender} text="Avec les clients qui l'ont accepté." style={{ marginTop: 18 }} />
      </div>

      <div style={{ position: "absolute", left: panel.left, top: panel.top, opacity: panelIn, translate: `0px ${(1 - panelIn) * 40}px` }}>
        <Panel style={{ width: pw, padding: 32 * pk }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 22 * pk }}>
            <div style={{ fontSize: 30 * pk, fontWeight: 700, letterSpacing: "-0.02em" }}>Notifications · Nouvelle annonce</div>
          </div>
          {field("Titre", TITLE, T.title)}
          {field("Message", MSG, T.msg)}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14 * pk, fontSize: 22 * pk, opacity: prog(frame, T.audience, 10) }}>
              <Toggle onAt={T.audience + 4} size={28 * pk} />
              Clients ayant accepté les communications
            </div>
            <div style={{ opacity: prog(frame, T.audience + 8, 10) }}>
              <Button label="Envoyer" pressedLabel="Envoyée" pressAt={T.send} size={24 * pk} tone="deep" />
            </div>
          </div>
        </Panel>
      </div>
      <Tap at={T.send} x={sx} y={sy - 24 * pk} color={C.lavender} />

      {/* Trajet de l'annonce vers la carte */}
      <svg width="100%" height="100%" style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        <path d={path} fill="none" stroke={C.lavender} strokeWidth={3} strokeDasharray="1" pathLength={1} strokeDashoffset={1 - travel} opacity={1 - prog(frame, T.alert + 20, 20)} />
        {travel > 0 && travel < 1 ? (
          <g transform={`translate(${dot.x} ${dot.y})`}>
            <circle r={16} fill="none" stroke={C.lavender} strokeWidth={6} />
          </g>
        ) : null}
      </svg>

      <At x={phone.x} y={phone.y} style={{ opacity: prog(frame, 20, 20) }}>
        <Phone width={phoneW} screen="#0F0E13">
          <div style={{ position: "absolute", top: 120, left: (phoneW * 0.93 - phoneW * 0.86) / 2 }}>
            <WalletCard width={phoneW * 0.86} filled={7} />
          </div>
          {/* L'annonce visible sur la carte */}
          <div
            style={{
              position: "absolute",
              left: (phoneW * 0.93 - phoneW * 0.86) / 2,
              width: phoneW * 0.86,
              top: 120 + phoneW * 0.86 * 0.63 + 22,
              padding: 18,
              borderRadius: 16,
              background: "#1E1C24",
              color: C.paper,
              opacity: prog(frame, T.alert + 14, 14),
              translate: `0px ${(1 - prog(frame, T.alert + 14, 14)) * 20}px`,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: "0.12em", color: C.lavender }}>DERNIÈRE ANNONCE</div>
            <div style={{ fontSize: 17, fontWeight: 700, marginTop: 8 }}>{TITLE}</div>
            <div style={{ fontSize: 15, marginTop: 4, color: "rgba(250,249,252,0.75)", lineHeight: 1.35 }}>{MSG}</div>
          </div>
          {/* Alerte stylisée — illustration, pas un écran système garanti */}
          <div
            style={{
              position: "absolute",
              left: 12,
              right: 12,
              top: 50,
              padding: "14px 16px",
              borderRadius: 18,
              background: "rgba(250,249,252,0.94)",
              color: C.ink,
              translate: `0px ${(1 - alert) * -160}px`,
              opacity: alert,
              boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 700, color: "rgba(24,23,26,0.6)" }}>
              <div style={{ width: 22, height: 22, borderRadius: 6, background: C.cardBlue, color: C.paper, fontSize: 9, display: "flex", alignItems: "center", justifyContent: "center" }}>MC</div>
              Maison Centrale
            </div>
            <div style={{ fontSize: 17, fontWeight: 700, marginTop: 6 }}>{TITLE}</div>
            <div style={{ fontSize: 15, marginTop: 2, color: "rgba(24,23,26,0.75)" }}>{MSG}</div>
          </div>
        </Phone>
      </At>

      <Note tone="night" at={50} text="Affichage et réception selon le Wallet et les réglages du téléphone" style={{ left: pick(140, 90), bottom: pick(60, 50), maxWidth: pick(1600, 900) }} />

      <Sfx name="whoosh" at={0} volume={0.55} />
      {Array.from({ length: 14 }).map((_, i) => (
        <Sfx key={i} name="tick" at={T.title + i * 4} volume={0.22} />
      ))}
      <Sfx name="click" at={T.audience + 4} volume={0.5} />
      <Sfx name="click" at={T.send} volume={0.8} />
      <Sfx name="swipe" at={T.travel} volume={0.5} />
      <Sfx name="chime" at={T.alert} volume={0.7} />
    </AbsoluteFill>
  );
};
