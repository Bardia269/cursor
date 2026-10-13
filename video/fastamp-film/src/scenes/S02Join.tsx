import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Phone } from "../components/Devices";
import { Glass, Hud, Obj, RingLight, Space, Void, camAt } from "../components/Space";
import { Headline, Sub } from "../components/Headline";
import { Note } from "../components/Note";
import { Sfx } from "../components/Sfx";
import { WalletCard } from "../components/WalletCard";
import { prog, typed } from "../components/anim";
import { useLayout } from "../components/layout";
import { Check, Qr, Tap } from "../components/ui";
import { C, FONT } from "../theme";

const T = { phoneIn: 14, lock: 50, flash: 74, name: 86, email: 106, consent: 128, buttons: 134, tap: 160, card: 166 };

/** Écran du téléphone client : caméra → formulaire → carte ajoutée. */
const PhoneScreen: React.FC<{ w: number }> = ({ w }) => {
  const frame = useCurrentFrame();
  const k = w / 330;
  const inner = w * 0.93;
  const lock = prog(frame, T.lock - 14, 16);
  const scanY = interpolate(frame, [30, 70], [0.15, 0.85], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const flash = interpolate(frame, [T.flash, T.flash + 3, T.flash + 12], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const formIn = prog(frame, T.flash + 2, 12);
  const cardUp = prog(frame, T.card, 26);
  const field = (label: string, value: string, at: number) => (
    <div style={{ marginBottom: 16 * k }}>
      <div style={{ fontSize: 14 * k, color: "rgba(24,23,26,0.6)", marginBottom: 6 * k, fontWeight: 700 }}>{label}</div>
      <div
        style={{
          height: 44 * k,
          border: `1.5px solid ${frame >= at && frame < at + 22 ? C.deep : "rgba(24,23,26,0.2)"}`,
          borderRadius: 4 * k,
          display: "flex",
          alignItems: "center",
          padding: `0 ${12 * k}px`,
          fontSize: 18 * k,
          color: C.ink,
        }}
      >
        {typed(value, frame, at, 26)}
      </div>
    </div>
  );
  return (
    <>
      {/* Caméra */}
      <AbsoluteFill style={{ background: "#2A2830", alignItems: "center", justifyContent: "center", opacity: 1 - formIn }}>
        <div style={{ filter: `blur(${(1 - lock) * 3}px)`, opacity: 0.9, scale: String(1 + lock * 0.08) }}>
          <Qr id="demoJoin" size={170 * k} />
        </div>
        {[0, 1, 2, 3].map((i) => {
          const s = (230 - lock * 30) * k;
          const sx = i % 2 === 0 ? -1 : 1;
          const sy = i < 2 ? -1 : 1;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                width: 34 * k,
                height: 34 * k,
                translate: `${(sx * s) / 2 - (sx > 0 ? 34 * k : 0)}px ${(sy * s) / 2 - (sy > 0 ? 34 * k : 0)}px`,
                borderColor: lock > 0.95 ? C.lavender : C.paper,
                borderStyle: "solid",
                borderWidth: 0,
                borderTopWidth: sy < 0 ? 5 * k : 0,
                borderBottomWidth: sy > 0 ? 5 * k : 0,
                borderLeftWidth: sx < 0 ? 5 * k : 0,
                borderRightWidth: sx > 0 ? 5 * k : 0,
              }}
            />
          );
        })}
        <div
          style={{
            position: "absolute",
            left: "18%",
            right: "18%",
            top: `${scanY * 100}%`,
            height: 3 * k,
            background: C.lavender,
            boxShadow: `0 0 ${14 * k}px ${C.lavender}`,
            opacity: frame < 72 ? 0.9 : 0,
          }}
        />
        <div style={{ position: "absolute", bottom: 40 * k, color: C.paper, fontSize: 16 * k, fontWeight: 700, opacity: 0.85 }}>
          Scanner le QR du commerce
        </div>
      </AbsoluteFill>

      {/* Formulaire d'inscription simplifié */}
      <AbsoluteFill style={{ background: C.paper, opacity: formIn, padding: `${64 * k}px ${22 * k}px`, color: C.ink }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 * k, marginBottom: 20 * k }}>
          <div
            style={{
              width: 40 * k,
              height: 40 * k,
              borderRadius: "50%",
              background: C.cardBlue,
              color: C.paper,
              fontWeight: 700,
              fontSize: 15 * k,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            MC
          </div>
          <div style={{ fontWeight: 700, fontSize: 20 * k }}>Maison Centrale</div>
        </div>
        <div style={{ fontWeight: 700, fontSize: 26 * k, letterSpacing: "-0.02em", marginBottom: 18 * k, lineHeight: 1.1 }}>
          Rejoindre la fidélité
        </div>
        {field("Nom", "Camille — Démo", T.name)}
        {field("Email", "camille@example.com", T.email)}
        <div style={{ display: "flex", gap: 10 * k, alignItems: "center", fontSize: 14 * k, opacity: prog(frame, T.consent, 8), marginBottom: 18 * k }}>
          <div style={{ width: 22 * k, height: 22 * k, borderRadius: 3 * k, background: C.deep, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Check size={18 * k} color={C.paper} draw={prog(frame, T.consent + 2, 8)} />
          </div>
          J'accepte de recevoir les annonces
        </div>
        {["Ajouter à Apple Wallet", "Ajouter à Google Wallet"].map((l, i) => (
          <div
            key={l}
            style={{
              height: 50 * k,
              borderRadius: 10 * k,
              background: i === 0 ? "#000" : "#fff",
              color: i === 0 ? "#fff" : "#000",
              border: i === 0 ? "none" : "1.5px solid #000",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: 16 * k,
              marginBottom: 10 * k,
              opacity: prog(frame, T.buttons + i * 4, 10),
              scale: String(i === 0 ? interpolate(frame, [T.tap - 2, T.tap + 2, T.tap + 8], [1, 0.95, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1),
            }}
          >
            {l}
          </div>
        ))}
      </AbsoluteFill>

      {/* Carte ajoutée */}
      <AbsoluteFill style={{ background: "#0F0E13", opacity: cardUp > 0 ? 1 : 0, translate: `0px ${(1 - cardUp) * 100}%` }}>
        <div style={{ position: "absolute", top: 70 * k, left: (w * 0.93 - inner * 0.92) / 2 }}>
          <WalletCard width={inner * 0.92} filled={0} showQr />
        </div>
        <div
          style={{
            position: "absolute",
            top: 70 * k + inner * 0.92 * 0.63 + 30 * k,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: 8 * k,
            color: C.paper,
            fontSize: 18 * k,
            fontWeight: 700,
            opacity: prog(frame, T.card + 24, 10),
          }}
        >
          <Check size={22 * k} color={C.lavender} draw={prog(frame, T.card + 26, 10)} />
          Carte ajoutée au Wallet
        </div>
        <div
          style={{
            position: "absolute",
            left: 24 * k,
            right: 24 * k,
            top: 70 * k + inner * 0.92 * 0.63 + 80 * k,
            color: "rgba(250,249,252,0.6)",
            fontSize: 15 * k,
            lineHeight: 1.4,
            textAlign: "center",
            opacity: prog(frame, T.card + 34, 10),
          }}
        >
          Elle se présente à chaque passage, comme n'importe quelle carte du Wallet.
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
    </>
  );
};

// 02 — Rejoindre le programme. Caméra en orbite autour du comptoir, poussée sur l'écran au scan.
export const S02Join: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const phoneW = pick(340, 420);
  const k = phoneW / 330;
  const phone = { x: pick(600, 180), y: pick(30, 230), z: 0 };
  const cam = camAt(frame, [
    { f: 0, x: pick(260, 100), y: pick(-60, 0), z: -420, ry: -20, rx: 4 },
    { f: 64, x: pick(330, 190), y: pick(20, 200), z: pick(480, 330), ry: -6, rx: 0 },
    { f: 150, x: pick(320, 185), y: pick(30, 190), z: pick(440, 300), ry: -4 },
    { f: 205, x: pick(170, 150), y: pick(0, 130), z: pick(190, 120), ry: 3, rx: -1 },
    { f: 240, x: pick(160, 150), y: pick(0, 130), z: pick(210, 140), ry: 4 },
  ]);
  const focus = interpolate(frame, [0, 64, 150, 200], [-250, 0, 0, 0], { extrapolateRight: "clamp" });
  const phoneIn = prog(frame, T.phoneIn, 28);
  const standIn = prog(frame, 4, 24);
  return (
    <AbsoluteFill>
      <Void glowX={pick(65, 50)} glowY={40} />
      <Space cam={cam} focus={focus} floor={pick(380, 800)}>
        <Obj x={pick(-700, -260)} y={pick(-520, -420)} z={-2200} sharp>
          <RingLight size={260} intensity={0.85} />
        </Obj>
        {/* Chevalet de comptoir de « Maison Centrale » (commerce fictif) */}
        <Obj x={pick(980, -230)} y={pick(70, 360) + (1 - standIn) * 80} z={-520} ry={pick(-24, 16)}>
          <Glass light style={{ width: pick(330, 330), padding: 26, textAlign: "center", fontFamily: FONT, opacity: standIn }}>
            <div style={{ fontWeight: 700, fontSize: 26, letterSpacing: "-0.02em" }}>Maison Centrale</div>
            <div style={{ fontSize: 19, color: "rgba(24,23,26,0.7)", margin: "8px 0 18px" }}>Rejoignez notre fidélité</div>
            <div style={{ display: "flex", justifyContent: "center" }}>
              <Qr id="demoJoin" size={230} />
            </div>
            <div style={{ fontSize: 15, marginTop: 14, color: "rgba(24,23,26,0.6)", fontWeight: 700 }}>QR de démonstration</div>
          </Glass>
        </Obj>

        <Obj x={phone.x} y={phone.y + (1 - phoneIn) * 500} z={phone.z} ry={-14 + (1 - phoneIn) * 30} rx={(1 - phoneIn) * -20}>
          <div style={{ position: "relative" }}>
            <Phone width={phoneW}>
              <PhoneScreen w={phoneW * 0.93} />
            </Phone>
            <Tap at={T.tap} x={phoneW / 2} y={phoneW * 0.035 + (64 + 40 + 20 + 26 * 1.1 + 18 + 2 * (14 + 6 + 44 + 16) + 22 + 18 + 25) * k * 0.93} />
          </div>
        </Obj>
      </Space>
      <Hud cam={cam}>
        <div style={{ position: "absolute", left: pick(140, 90), top: pick(320, 170), width: pick(780, 900) }}>
          <Headline
            size={pick(96, 92)}
            lines={[
              { text: "Le client scanne.", at: 20 },
              { text: "Il ajoute sa carte.", at: 118, color: C.lavender },
            ]}
          />
          <Sub
            at={150}
            size={pick(36, 38)}
            color="rgba(250,249,252,0.82)"
            text="Dans Apple Wallet ou Google Wallet, sans application Fastamp à télécharger."
            style={{ marginTop: 36, maxWidth: pick(640, 860) }}
          />
        </div>
      </Hud>

      <Note tone="night" at={30} text="QR et commerce de démonstration" style={{ left: pick(140, 90), bottom: pick(60, 90) }} />

      <Sfx name="swipe" at={T.phoneIn} volume={0.45} />
      <Sfx name="scan" at={40} volume={0.5} />
      <Sfx name="click" at={T.flash} volume={0.7} />
      {Array.from({ length: 10 }).map((_, i) => (
        <Sfx key={i} name="tick" at={T.name + i * 4} volume={0.25} />
      ))}
      <Sfx name="click" at={T.consent} volume={0.5} />
      <Sfx name="click" at={T.tap} volume={0.8} />
      <Sfx name="whoosh" at={T.card - 4} volume={0.35} />
      <Sfx name="pop" at={T.card + 22} volume={0.7} />
    </AbsoluteFill>
  );
};
