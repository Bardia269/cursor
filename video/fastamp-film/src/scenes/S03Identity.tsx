import React from "react";
import { AbsoluteFill, interpolate, interpolateColors, useCurrentFrame } from "remotion";
import { Headline } from "../components/Headline";
import { Note } from "../components/Note";
import { Ring } from "../components/Ring";
import { Sfx } from "../components/Sfx";
import { Hud, Obj, RingLight, Space, Void, camAt } from "../components/Space";
import { prog, stampScale } from "../components/anim";
import { useLayout } from "../components/layout";
import { Qr } from "../components/ui";
import { C, FONT } from "../theme";

const T = { base: 6, logo: 30, color: 76, plum: 104, coral: 120, back: 138, banner: 150, stamps: 162, collapse: 186 };

// 03 — L'identité du commerce en vue éclatée : chaque couche de la carte flotte
// à sa profondeur, la caméra tourne autour, puis tout se referme en une seule carte.
export const S03Identity: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const cw = pick(700, 760);
  const k = cw / 640;
  const ch = 404 * k;
  const pad = 30 * k;
  const cx = pick(380, 0);
  const cy = pick(0, 260);
  const color = interpolateColors(
    frame,
    [T.plum - 4, T.plum + 4, T.coral - 4, T.coral + 4, T.back - 4, T.back + 4],
    [C.cardBlue, C.cardPlum, C.cardPlum, C.cardCoral, C.cardCoral, C.cardBlue],
  );
  const cam = camAt(frame, [
    { f: 0, x: cx - 260, y: cy - 60, z: -260, ry: 38, rx: -12 },
    { f: T.collapse - 10, x: cx - 200, y: cy - 40, z: -60, ry: 24, rx: -8, ease: [0.4, 0, 0.6, 1] },
    { f: T.collapse + 30, x: pick(cx - 380, 0), y: pick(cy - 10, cy - 240), z: 80, ry: pick(-4, 0), rx: -2 },
    { f: 240, x: pick(cx - 390, 0), y: pick(cy - 10, cy - 240), z: 110, ry: pick(-6, -2), rx: -2 },
  ]);
  const SEP = 150;
  const collapse = prog(frame, T.collapse, 26, [0.65, 0, 0.35, 1]);
  // profondeur de chaque couche : arrive de l'avant, se place, puis se referme
  const layerZ = (i: number, at: number) => {
    const arrive = prog(frame, at, 22, [0.2, 0.7, 0.1, 1]);
    const spread = i * SEP * (1 - collapse) + i * 1.5;
    return spread + (1 - arrive) * 900;
  };
  const layerOpacity = (at: number) => interpolate(frame, [at, at + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const plate: React.CSSProperties = { width: cw, height: ch, borderRadius: 30 * k, position: "relative", overflow: "hidden", fontFamily: FONT };
  const label = (text: string, i: number, at: number, dx: number) => (
    <Obj x={cx - cw / 2 + dx} y={cy - ch / 2 - 46} z={layerZ(i, at)}>
      <div
        style={{
          opacity: layerOpacity(at + 6) * (1 - collapse),
          padding: "10px 20px",
          border: `2px solid ${C.lavender}`,
          borderRadius: 2,
          background: "rgba(18,9,39,0.85)",
          color: C.lavender,
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 30,
          whiteSpace: "nowrap",
          boxShadow: `0 0 24px rgba(199,185,232,0.35)`,
        }}
      >
        {text}
      </div>
    </Obj>
  );
  return (
    <AbsoluteFill>
      <Void glowX={pick(62, 50)} glowY={pick(45, 60)} />
      <Space cam={cam} focus={60} floor={pick(330, 620)} dof={0.008}>
        <Obj x={cx + 300} y={cy - 420} z={-1600} sharp>
          <RingLight size={280} intensity={0.8} />
        </Obj>
        {/* 0 — support */}
        <Obj x={cx} y={cy} z={0}>
          <div style={{ ...plate, background: "#E9E5F1", opacity: layerOpacity(T.base), boxShadow: "0 30px 60px rgba(0,0,0,0.45)" }} />
        </Obj>
        {/* 1 — couleur */}
        <Obj x={cx} y={cy} z={layerZ(1, T.color)}>
          <div
            style={{
              ...plate,
              opacity: layerOpacity(T.color) * (0.82 + 0.18 * collapse),
              background: `linear-gradient(140deg, ${color} 0%, ${color} 55%, color-mix(in srgb, ${color} 78%, #000) 100%)`,
              boxShadow: `0 0 0 1.5px rgba(255,255,255,0.35), 0 0 40px ${color}55`,
            }}
          />
        </Obj>
        {/* 2 — bannière */}
        <Obj x={cx} y={cy} z={layerZ(2, T.banner)}>
          <div style={{ ...plate, overflow: "visible", opacity: layerOpacity(T.banner) }}>
            <svg width={cw} height={96 * k} viewBox="0 0 640 96" preserveAspectRatio="none" style={{ position: "absolute", top: pad + 72 * k }}>
              <rect width={640} height={96} fill="rgba(0,0,0,0.18)" />
              <circle cx={470} cy={96} r={80} fill="rgba(255,255,255,0.16)" />
              <circle cx={560} cy={30} r={44} fill="rgba(255,255,255,0.14)" />
              <rect x={0} y={60} width={640} height={2} fill="rgba(255,255,255,0.25)" />
              <text x={30} y={46} fill="rgba(255,255,255,0.95)" fontFamily={FONT} fontWeight={700} fontSize={26}>
                Café · Pâtisserie
              </text>
              <text x={30} y={86} fill="rgba(255,255,255,0.8)" fontFamily={FONT} fontSize={18}>
                8 tampons = une boisson offerte
              </text>
            </svg>
          </div>
        </Obj>
        {/* 3 — tampons, titulaire, QR */}
        <Obj x={cx} y={cy} z={layerZ(3, T.stamps)}>
          <div style={{ ...plate, overflow: "visible", opacity: layerOpacity(T.stamps), color: C.paper }}>
            <div style={{ position: "absolute", left: pad, top: pad + 186 * k, display: "flex", gap: (580 * k - 52 * k * 8) / 7 }}>
              {Array.from({ length: 8 }).map((_, i) => (
                <Ring key={i} size={52 * k} variant={i < 6 ? "stamp" : "empty"} color={C.paper} />
              ))}
            </div>
            <div style={{ position: "absolute", left: pad, right: pad, bottom: pad, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
              <div>
                <div style={{ fontSize: 15 * k, fontWeight: 700, letterSpacing: "0.12em", opacity: 0.8 }}>MEMBRE</div>
                <div style={{ fontSize: 28 * k, fontWeight: 700 }}>Camille — Démo</div>
              </div>
              <div style={{ padding: 6 * k, background: "#fff", borderRadius: 8 * k }}>
                <Qr id="demoCard" size={64 * k} />
              </div>
            </div>
            <div style={{ position: "absolute", right: pad, top: pad, textAlign: "right" }}>
              <div style={{ fontSize: 15 * k, fontWeight: 700, letterSpacing: "0.12em", opacity: 0.8 }}>TAMPONS</div>
              <div style={{ fontSize: 30 * k, fontWeight: 700 }}>6/8</div>
            </div>
          </div>
        </Obj>
        {/* 4 — logo du commerce */}
        <Obj x={cx} y={cy} z={layerZ(4, T.logo)}>
          <div style={{ ...plate, overflow: "visible", opacity: layerOpacity(T.logo) }}>
            <div style={{ position: "absolute", left: pad, top: pad, display: "flex", alignItems: "center", gap: 16 * k }}>
              <div
                style={{
                  width: 56 * k,
                  height: 56 * k,
                  borderRadius: "50%",
                  background: C.paper,
                  color: frame > T.color + 10 ? color : C.ink,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                  fontSize: 22 * k,
                  scale: String(stampScale(frame, T.logo + 12)),
                  boxShadow: `0 0 0 ${3 * k}px rgba(255,255,255,0.25), 0 0 30px rgba(199,185,232,0.6)`,
                }}
              >
                MC
              </div>
              <div style={{ fontWeight: 700, fontSize: 30 * k, letterSpacing: "-0.02em", color: frame > T.color + 10 ? C.paper : C.ink }}>Maison Centrale</div>
            </div>
          </div>
        </Obj>

        {label("Logo", 4, T.logo, 90)}
        {label("Couleur", 1, T.color, cw - 110)}
        {label("Bannière", 2, T.banner, cw / 2)}
      </Space>

      <Hud cam={cam} amount={0.6}>
        <div style={{ position: "absolute", left: pick(140, 90), top: pick(330, 190) }}>
          <Headline
            size={96}
            lines={[
              { text: "Votre logo.", at: T.logo - 4 },
              { text: "Vos couleurs.", at: T.color },
              { text: "Votre fidélité.", at: T.banner, color: C.lavender },
            ]}
          />
        </div>
      </Hud>
      <Note tone="night" at={40} text="Illustration — rendu variable selon le Wallet" style={{ left: pick(140, 90), bottom: pick(60, 90) }} />

      <Sfx name="whoosh" at={T.logo - 6} volume={0.4} />
      <Sfx name="stamp" at={T.logo + 12} volume={0.8} />
      <Sfx name="whoosh" at={T.color - 6} volume={0.4} />
      <Sfx name="click" at={T.plum} volume={0.45} />
      <Sfx name="click" at={T.coral} volume={0.45} />
      <Sfx name="click" at={T.back} volume={0.45} />
      <Sfx name="swipe" at={T.banner} volume={0.45} />
      <Sfx name="pop" at={T.stamps + 6} volume={0.5} />
      <Sfx name="stamp" at={T.collapse + 24} volume={0.7} />
    </AbsoluteFill>
  );
};
