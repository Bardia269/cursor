import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Phone, Tablet } from "../components/Devices";
import { Hud, Obj, RingLight, Space, Void, camAt } from "../components/Space";
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

/** Faisceau lumineux entre deux points du plan horizontal (lecture du QR). */
const Beam: React.FC<{ a: [number, number, number]; b: [number, number, number]; p: number }> = ({ a, b, p }) => {
  const dx = b[0] - a[0];
  const dz = b[2] - a[2];
  const len = Math.hypot(dx, dz);
  const ang = (Math.atan2(dz, dx) * 180) / Math.PI;
  return (
    <Obj x={(a[0] + b[0]) / 2} y={(a[1] + b[1]) / 2} z={(a[2] + b[2]) / 2} ry={-ang} sharp>
      <div
        style={{
          width: len,
          height: 6,
          borderRadius: 6,
          opacity: p,
          background: `linear-gradient(90deg, transparent, ${C.lavender} 20%, #FFFFFF 50%, ${C.lavender} 80%, transparent)`,
          boxShadow: `0 0 24px 6px rgba(199,185,232,0.55)`,
        }}
      />
    </Obj>
  );
};

// 04 — Le passage au commerce : deux appareils face à face sur le comptoir,
// un faisceau relie la carte du client au scanner de l'équipe, puis le tampon tombe.
export const S04Visit: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const phoneW = pick(310, 300);
  const tabW = pick(600, 700);
  const inP = prog(frame, T.devices, 26);
  const tab = { x: pick(520, -40), y: pick(-10, -40), z: -160 };
  const phone = { x: pick(980, 230), y: pick(40, 560), z: 80 };
  const cam = camAt(frame, [
    { f: 0, x: pick(420, 60), y: pick(60, 120), z: -380, ry: 12, rx: -6 },
    { f: T.found, x: pick(330, 40), y: pick(20, 60), z: 60, ry: 2, rx: -3 },
    { f: T.press + 4, x: pick(330, 40), y: pick(10, 60), z: 110, ry: -2, rx: -2 },
    { f: T.stamp + 4, x: pick(650, 180), y: pick(-20, 700), z: pick(480, 300), ry: -8, rx: 0, ease: [0.6, 0, 0.2, 1] },
    { f: 270, x: pick(560, 170), y: pick(-10, 640), z: pick(330, 220), ry: -5, rx: -2, ease: [0.3, 0, 0.3, 1] },
  ]);
  const focus = interpolate(frame, [T.press, T.stamp], [-120, 80], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const recede = prog(frame, T.stamp - 6, 24);
  const beam = prog(frame, T.scan - 10, 12) * (1 - prog(frame, T.found + 6, 10));
  const burst = interpolate(frame, [T.stamp, T.stamp + 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const inner = phoneW * 0.93;
  const cardW = inner * 0.92;
  const ck = cardW / 640;
  const pk = phoneW / 330;
  const stampLocal = {
    x: phoneW * 0.035 + (inner - cardW) / 2 + (30 + 6 * ((580 - 52 * 8) / 7 + 52) + 26) * ck,
    y: phoneW * 0.035 + 90 * pk + (30 + 186 + 26) * ck,
  };
  return (
    <AbsoluteFill>
      <Void glowX={pick(60, 50)} glowY={pick(40, 55)} />
      <Space cam={cam} focus={focus} floor={pick(420, 1000)} dof={0.01}>
        <Obj x={pick(560, 100)} y={pick(-520, -300)} z={-1900} sharp>
          <RingLight size={300} intensity={0.8} />
        </Obj>
        <Obj x={tab.x} y={tab.y + (1 - inP) * 200} z={tab.z - recede * 500} ry={pick(14, 8)}>
          <div style={{ position: "relative", opacity: inP * (1 - recede * 0.7) }}>
            <Tablet width={tabW}>
              <TabletScreen w={tabW * 0.94} />
            </Tablet>
            <Tap at={T.press} x={tabW * 0.03 + tabW * 0.94 * (28 + 150) / 600} y={tabW * 0.03 + tabW * 0.085 + (28 + 17 + 46 + 30 + 20 + 44 + 28 + 26) * ((tabW * 0.94) / 600)} />
          </div>
        </Obj>
        <Obj x={phone.x} y={phone.y + (1 - inP) * 260} z={phone.z} ry={pick(-26, -12)} rx={4}>
          <div style={{ position: "relative", opacity: inP }}>
            <Phone width={phoneW} screen="#0F0E13">
              <div style={{ position: "absolute", top: 90 * pk, left: (inner - cardW) / 2 }}>
                <WalletCard width={cardW} filled={7} stampAt={T.stamp} />
              </div>
              <div style={{ position: "absolute", top: 90 * pk + cardW * 0.63 + 30, width: "100%", display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
                <div style={{ padding: 12, background: "#fff", borderRadius: 12, boxShadow: beam > 0.1 ? `0 0 30px rgba(199,185,232,${0.8 * beam})` : undefined }}>
                  <Qr id="demoCard" size={phoneW * 0.46} />
                </div>
                <div style={{ color: "rgba(250,249,252,0.75)", fontSize: 15, fontWeight: 700 }}>Présentez la carte en caisse</div>
              </div>
            </Phone>
            {/* Onde de confirmation du 7e tampon */}
            <div style={{ position: "absolute", left: stampLocal.x, top: stampLocal.y, width: 0, height: 0, opacity: burst > 0 && burst < 1 ? 1 - burst : 0 }}>
              <div style={{ position: "absolute", left: -16, top: -16, width: 32, height: 32, borderRadius: "50%", border: `4px solid ${C.lavender}`, boxShadow: `0 0 20px ${C.lavender}`, scale: String(1 + burst * 6) }} />
            </div>
          </div>
        </Obj>
        <Beam a={[phone.x - 20, phone.y + phoneW * 0.42, phone.z]} b={[tab.x + 60, tab.y, tab.z]} p={beam} />
      </Space>

      <Hud cam={cam} amount={0.6}>
        <div style={{ position: "absolute", left: pick(140, 90), top: pick(280, 170) }}>
          <Headline
            size={92}
            lines={[
              { text: "Scannez.", at: 22 },
              { text: "Confirmez.", at: T.press - 4 },
              { text: "La fidélité", at: T.stamp + 10, color: C.lavender },
              { text: "avance.", at: T.stamp + 16, color: C.lavender },
            ]}
          />
        </div>
      </Hud>
      <Note tone="night" at={40} text="L'équipe confirme dans Fastamp — pas de crédit automatique depuis la caisse" style={{ left: pick(140, 90), bottom: pick(60, 70), maxWidth: pick(1600, 900) }} />

      <Sfx name="swipe" at={T.devices} volume={0.4} />
      <Sfx name="scan" at={T.scan - 8} volume={0.5} />
      <Sfx name="pop" at={T.found} volume={0.5} />
      <Sfx name="click" at={T.press} volume={0.8} />
      <Sfx name="whoosh" at={T.stamp - 12} volume={0.45} />
      <Sfx name="stamp" at={T.stamp} volume={1} />
    </AbsoluteFill>
  );
};
