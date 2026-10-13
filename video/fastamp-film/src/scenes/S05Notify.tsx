import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Phone } from "../components/Devices";
import { Headline, Sub } from "../components/Headline";
import { Note } from "../components/Note";
import { Sfx } from "../components/Sfx";
import { Glass, Hud, Obj, RingLight, Space, Void, camAt } from "../components/Space";
import { WalletCard } from "../components/WalletCard";
import { prog, typed } from "../components/anim";
import { useLayout } from "../components/layout";
import { Button, Toggle } from "../components/ui";
import { C, FONT } from "../theme";

const T = { panel: 18, title: 44, msg: 72, audience: 104, send: 132, travel: 136, alert: 172 };
const TITLE = "La carte d'automne est arrivée";
const MSG = "Passez nous voir à la Maison Centrale.";

type V3 = [number, number, number];
const bez = (a: V3, c: V3, b: V3, t: number): V3 => [0, 1, 2].map((i) => (1 - t) * (1 - t) * a[i] + 2 * (1 - t) * t * c[i] + t * t * b[i]) as V3;

// 05 — Garder le lien : l'annonce se détache de l'écran et traverse l'espace
// jusqu'à la carte Wallet ; la caméra la suit.
export const S05Notify: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const pw = pick(760, 860);
  const pk = pw / 760;
  const panel = { x: pick(520, 0), y: pick(110, -60), z: 0 };
  const phoneW = pick(340, 380);
  const phone = { x: pick(1560, 60), y: pick(-40, 1050), z: pick(-900, -700) };
  const start: V3 = [panel.x + pw / 2 - 90 * pk, panel.y + 160 * pk, 30];
  const end: V3 = [phone.x, phone.y - phoneW * 0.75, phone.z + 40];
  const ctrl: V3 = pick<V3>([1150, -420, -200], [520, 420, -200]);
  const travel = prog(frame, T.travel, 34, [0.55, 0, 0.3, 1]);
  const pos = bez(start, ctrl, end, travel);
  const alert = prog(frame, T.alert, 16);
  const cam = camAt(frame, [
    { f: 0, x: pick(240, 0), y: pick(40, -120), z: -260, ry: 10, rx: -4 },
    { f: T.panel + 30, x: pick(330, 0), y: pick(60, -100), z: 100, ry: 2, rx: -2 },
    { f: T.send, x: pick(340, 0), y: pick(60, -90), z: 130, ry: 0 },
    { f: T.alert + 8, x: pick(1130, 60), y: pick(-60, 900), z: pick(980, 980), ry: -10, rx: -2, ease: [0.55, 0, 0.25, 1] },
    { f: 255, x: pick(1110, 60), y: pick(-60, 900), z: pick(1010, 1010), ry: -8, rx: -2 },
  ]);
  const focus = interpolate(frame, [T.send, T.alert], [0, phone.z], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
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
  const panelIn = prog(frame, T.panel, 22);
  return (
    <AbsoluteFill>
      <Void glowX={pick(70, 50)} glowY={pick(40, 70)} />
      <Space cam={cam} focus={focus} floor={pick(520, 1500)} dof={0.009}>
        <Obj x={phone.x + pick(380, 260)} y={phone.y - pick(520, 560)} z={phone.z - 1200} sharp>
          <RingLight size={320} intensity={0.85} />
        </Obj>

        <Obj x={panel.x} y={panel.y + (1 - panelIn) * 120} z={panel.z} ry={pick(10, 0)}>
          <Glass light radius={6} style={{ width: pw, padding: 32 * pk, fontFamily: FONT, opacity: panelIn * (1 - prog(frame, T.travel + 6, 14)) }}>
            <div style={{ fontSize: 30 * pk, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 22 * pk }}>Notifications · Nouvelle annonce</div>
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
          </Glass>
        </Obj>

        {/* Capsule de l'annonce en vol */}
        {travel > 0 && travel < 1 ? (
          <Obj x={pos[0]} y={pos[1]} z={pos[2]} ry={-20 * travel} rz={-6 + 6 * travel} sharp>
            <Glass radius={14} style={{ padding: "14px 20px", fontFamily: FONT, boxShadow: "0 0 40px rgba(199,185,232,0.7), 0 0 0 1.5px rgba(199,185,232,0.8)" }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: C.lavender, letterSpacing: "0.1em" }}>ANNONCE</div>
              <div style={{ fontSize: 22, fontWeight: 700, marginTop: 4, whiteSpace: "nowrap" }}>{TITLE}</div>
            </Glass>
          </Obj>
        ) : null}
        {/* Traînée lumineuse */}
        {[0.06, 0.12, 0.18, 0.24].map((d, i) => {
          const t = travel - d;
          if (t <= 0 || travel >= 1) return null;
          const p = bez(start, ctrl, end, t);
          return (
            <Obj key={i} x={p[0]} y={p[1]} z={p[2]} sharp>
              <div style={{ width: 26 - i * 5, height: 26 - i * 5, borderRadius: "50%", background: C.lavender, opacity: 0.55 - i * 0.12, boxShadow: `0 0 20px ${C.lavender}` }} />
            </Obj>
          );
        })}

        <Obj x={phone.x} y={phone.y} z={phone.z} ry={-14} rx={3}>
          <Phone width={phoneW} screen="#0F0E13">
            <div style={{ position: "absolute", top: 120, left: (phoneW * 0.93 - phoneW * 0.86) / 2 }}>
              <WalletCard width={phoneW * 0.86} filled={7} />
            </div>
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
                background: "rgba(250,249,252,0.95)",
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
        </Obj>
      </Space>

      <Hud cam={cam} amount={0.5}>
        <div style={{ position: "absolute", left: pick(140, 90), top: pick(120, 170) }}>
          <Headline size={pick(92, 96)} lines={[{ text: "Gardez le contact.", at: 14 }]} />
          <Sub at={40} size={pick(40, 42)} weight={700} color={C.lavender} text="Avec les clients qui l'ont accepté." style={{ marginTop: 18 }} />
        </div>
      </Hud>
      <Note tone="night" at={50} text="Affichage et réception selon le Wallet et les réglages du téléphone" style={{ left: pick(140, 90), bottom: pick(60, 60), maxWidth: pick(1600, 900) }} />

      {Array.from({ length: 14 }).map((_, i) => (
        <Sfx key={i} name="tick" at={T.title + i * 4} volume={0.22} />
      ))}
      <Sfx name="click" at={T.audience + 4} volume={0.5} />
      <Sfx name="click" at={T.send} volume={0.8} />
      <Sfx name="whoosh" at={T.travel} volume={0.7} />
      <Sfx name="chime" at={T.alert} volume={0.7} />
    </AbsoluteFill>
  );
};
