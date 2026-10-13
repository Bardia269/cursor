import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Background } from "../components/Background";
import { Phone, Tablet } from "../components/Devices";
import { At } from "../components/Float";
import { Headline } from "../components/Headline";
import { Note } from "../components/Note";
import { Ring } from "../components/Ring";
import { Sfx } from "../components/Sfx";
import { WalletCard } from "../components/WalletCard";
import { prog, stampOpacity, stampScale } from "../components/anim";
import { useLayout } from "../components/layout";
import { Button, Qr, Tap } from "../components/ui";
import { C } from "../theme";

const T = { devices: 10, scan: 52, found: 78, button: 92, press: 122, stamp: 136 };

const TabletScreen: React.FC<{ w: number }> = ({ w }) => {
  const frame = useCurrentFrame();
  const k = w / 600;
  const found = prog(frame, T.found, 12);
  const scanY = interpolate(frame, [T.scan - 14, T.found], [0.1, 0.9], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const after = frame >= T.stamp;
  return (
    <div style={{ position: "absolute", inset: 0, top: w * 0.085, padding: 28 * k }}>
      {/* Viseur */}
      <div
        style={{
          position: "absolute",
          left: 28 * k,
          right: 28 * k,
          top: 28 * k,
          bottom: 28 * k,
          background: "#2A2830",
          borderRadius: 6 * k,
          opacity: 1 - found,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: C.paper,
          fontWeight: 700,
          fontSize: 22 * k,
        }}
      >
        <div style={{ width: 170 * k, height: 170 * k, border: `4px solid ${C.lavender}`, borderRadius: 6 * k }} />
        <div style={{ position: "absolute", left: "30%", right: "30%", top: `${scanY * 100}%`, height: 3, background: C.lavender, boxShadow: `0 0 12px ${C.lavender}` }} />
        <div style={{ position: "absolute", bottom: 18 * k }}>Scanner la carte du client</div>
      </div>
      {/* Carte reconnue */}
      <div style={{ opacity: found, translate: `0px ${(1 - found) * 20}px` }}>
        <div style={{ fontSize: 17 * k, fontWeight: 700, letterSpacing: "0.1em", color: "rgba(24,23,26,0.55)" }}>CARTE RECONNUE</div>
        <div style={{ fontSize: 40 * k, fontWeight: 700, letterSpacing: "-0.02em", marginTop: 6 * k }}>Camille — Démo</div>
        <div style={{ fontSize: 22 * k, color: "rgba(24,23,26,0.7)", marginTop: 4 * k }}>
          Maison Centrale · {after ? 7 : 6}/8 tampons
        </div>
        <div style={{ display: "flex", gap: 10 * k, marginTop: 20 * k }}>
          {Array.from({ length: 8 }).map((_, i) => {
            if (i === 6) {
              return (
                <div key={i} style={{ position: "relative", width: 44 * k, height: 44 * k }}>
                  <Ring size={44 * k} variant="empty" color={C.deep} style={{ position: "absolute", opacity: after ? 0 : 1 }} />
                  <Ring size={44 * k} variant="stamp" color={C.deep} style={{ position: "absolute", scale: String(stampScale(frame, T.stamp)), opacity: stampOpacity(frame, T.stamp) }} />
                </div>
              );
            }
            return <Ring key={i} size={44 * k} variant={i < 6 ? "stamp" : "empty"} color={C.deep} />;
          })}
        </div>
        <div style={{ marginTop: 28 * k, opacity: prog(frame, T.button, 10) }}>
          <Button label="Ajouter 1 tampon" pressedLabel="Tampon ajouté" pressAt={T.press} size={26 * k} />
        </div>
      </div>
    </div>
  );
};

// 04 — Le passage au commerce : deux appareils distincts, confirmation par l'équipe.
export const S04Visit: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const phoneW = pick(320, 330);
  const tabW = pick(640, 780);
  const inP = prog(frame, T.devices, 26);
  const phone = { x: pick(1010, 790), y: pick(600, 1390) };
  const tab = { x: pick(1500, 480), y: pick(560, 1030) };
  const beam = prog(frame, T.scan - 10, 14) * (1 - prog(frame, T.found + 4, 10));
  const burst = interpolate(frame, [T.stamp, T.stamp + 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const inner = phoneW * 0.93;
  const cardW = inner * 0.92;
  const ck = cardW / 640;
  // Centre du 7e tampon sur la carte du téléphone (repère pour l'onde de confirmation).
  const stampX = phone.x - cardW / 2 + (30 + 6 * ((580 - 52 * 8) / 7 + 52) + 26) * ck;
  const stampY = phone.y - phoneW * 1.025 + phoneW * 0.035 + 90 * (phoneW / 330) + (30 + 186 + 26) * ck;
  return (
    <AbsoluteFill>
      <Background tone="paper" clearAt={pick("22% 40%", "50% 18%")} />
      <div style={{ position: "absolute", left: pick(140, 90), top: pick(300, 180) }}>
        <Headline
          size={pick(92, 92)}
          color={C.ink}
          lines={[
            { text: "Scannez.", at: 22 },
            { text: "Confirmez.", at: T.press - 4 },
            { text: "La fidélité", at: T.stamp + 10, color: C.deep },
            { text: "avance.", at: T.stamp + 16, color: C.deep },
          ]}
        />
      </div>

      <At x={tab.x} y={tab.y + (1 - inP) * 120} style={{ opacity: inP }}>
        <Tablet width={tabW}>
          <TabletScreen w={tabW * 0.94} />
        </Tablet>
        <Tap at={T.press} x={tabW * 0.03 + tabW * 0.94 * (28 + 150) / 600} y={tabW * 0.03 + tabW * 0.085 + (28 + 17 + 46 + 30 + 20 + 44 + 28 + 26) * ((tabW * 0.94) / 600)} />
      </At>

      <At x={phone.x} y={phone.y + (1 - inP) * 160} style={{ opacity: inP, rotate: "-4deg" }}>
        <Phone width={phoneW} screen="#0F0E13">
          <div style={{ position: "absolute", top: 90 * (phoneW / 330), left: (inner - cardW) / 2 }}>
            <WalletCard width={cardW} filled={7} stampAt={T.stamp} />
          </div>
          <div style={{ position: "absolute", top: 90 * (phoneW / 330) + cardW * 0.63 + 30, width: "100%", display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
            <div style={{ padding: 12, background: "#fff", borderRadius: 12 }}>
              <Qr id="demoCard" size={phoneW * 0.46} />
            </div>
            <div style={{ color: "rgba(250,249,252,0.75)", fontSize: 15, fontWeight: 700 }}>Présentez la carte en caisse</div>
          </div>
        </Phone>
      </At>

      {/* Lecture du QR de la carte par la tablette */}
      <svg width="100%" height="100%" style={{ position: "absolute", inset: 0, opacity: beam }}>
        <line x1={phone.x} y1={phone.y + phoneW * 0.42} x2={tab.x} y2={tab.y} stroke={C.deep} strokeWidth={3} strokeDasharray="10 10" strokeDashoffset={-frame * 2} />
      </svg>

      {/* Onde de confirmation du tampon */}
      <div
        style={{
          position: "absolute",
          left: stampX,
          top: stampY,
          width: 0,
          height: 0,
          opacity: burst > 0 && burst < 1 ? 1 - burst : 0,
        }}
      >
        <div style={{ position: "absolute", left: -20, top: -20, width: 40, height: 40, borderRadius: "50%", border: `4px solid ${C.lavender}`, scale: String(1 + burst * 5) }} />
      </div>

      <Note tone="paper" at={40} text="L'équipe confirme dans Fastamp — pas de crédit automatique depuis la caisse" style={{ left: pick(140, 90), bottom: pick(70, 90), maxWidth: pick(1600, 900) }} />

      <Sfx name="whoosh" at={0} volume={0.55} />
      <Sfx name="swipe" at={T.devices} volume={0.4} />
      <Sfx name="scan" at={T.scan - 8} volume={0.5} />
      <Sfx name="pop" at={T.found} volume={0.5} />
      <Sfx name="click" at={T.press} volume={0.8} />
      <Sfx name="stamp" at={T.stamp} volume={1} />
    </AbsoluteFill>
  );
};
