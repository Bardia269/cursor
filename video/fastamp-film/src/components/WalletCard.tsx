import React from "react";
import { useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { Ring } from "./Ring";
import { Qr } from "./ui";
import { stampOpacity, stampScale } from "./anim";

export type CardLayers = { logo: number; color: number; banner: number; stamps: number };

type Props = {
  width: number;
  color?: string;
  filled?: number;
  total?: number;
  /** frame à laquelle le tampon `filled` (index filled-1) est apposé ; avant, il est vide. */
  stampAt?: number;
  layers?: CardLayers;
  holder?: string;
  showQr?: boolean;
  style?: React.CSSProperties;
};

const ALL: CardLayers = { logo: 1, color: 1, banner: 1, stamps: 1 };

// Carte Wallet illustrative (commerce fictif « Maison Centrale ») :
// coins nettement arrondis, ombre douce, profondeur limitée.
export const WalletCard: React.FC<Props> = ({
  width,
  color = C.cardBlue,
  filled = 6,
  total = 8,
  stampAt,
  layers = ALL,
  holder = "Camille — Démo",
  showQr = true,
  style,
}) => {
  const frame = useCurrentFrame();
  const k = width / 640;
  const h = 404 * k;
  const pad = 30 * k;
  const stampSize = 52 * k;
  const shown = stampAt !== undefined && frame < stampAt ? filled - 1 : filled;
  return (
    <div
      style={{
        width,
        height: h,
        borderRadius: 30 * k,
        position: "relative",
        overflow: "hidden",
        background: "#ECE9F3",
        boxShadow: `0 ${30 * k}px ${60 * k}px rgba(10,4,30,0.35), 0 ${6 * k}px ${14 * k}px rgba(10,4,30,0.18)`,
        fontFamily: FONT,
        color: C.paper,
        ...style,
      }}
    >
      {/* Couche couleur, révélée depuis le logo du commerce */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(140deg, ${color} 0%, ${color} 55%, color-mix(in srgb, ${color} 78%, #000) 100%)`,
          clipPath: `circle(${layers.color * 130}% at ${pad + 28 * k}px ${pad + 28 * k}px)`,
        }}
      />
      {/* En-tête : logo + nom */}
      <div
        style={{
          position: "absolute",
          left: pad,
          top: pad,
          right: pad,
          display: "flex",
          alignItems: "center",
          gap: 16 * k,
          height: 56 * k,
        }}
      >
        <div
          style={{
            width: 56 * k,
            height: 56 * k,
            borderRadius: "50%",
            background: C.paper,
            color: layers.color > 0.5 ? color : C.ink,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
            fontSize: 22 * k,
            letterSpacing: "-0.04em",
            scale: String(layers.logo),
            opacity: layers.logo,
            boxShadow: `0 0 0 ${3 * k}px rgba(255,255,255,0.25)`,
          }}
        >
          MC
        </div>
        <div
          style={{
            fontWeight: 700,
            fontSize: 30 * k,
            letterSpacing: "-0.02em",
            color: layers.color > 0.4 ? C.paper : C.ink,
            opacity: 0.4 + 0.6 * layers.logo,
          }}
        >
          Maison Centrale
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ textAlign: "right", opacity: layers.stamps }}>
          <div style={{ fontSize: 15 * k, fontWeight: 700, letterSpacing: "0.12em", opacity: 0.8 }}>TAMPONS</div>
          <div style={{ fontSize: 30 * k, fontWeight: 700 }}>
            {shown}/{total}
          </div>
        </div>
      </div>
      {/* Bannière */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: pad + 72 * k,
          height: 96 * k,
          overflow: "hidden",
          clipPath: `inset(0 ${(1 - layers.banner) * 100}% 0 0)`,
        }}
      >
        <svg width="100%" height="100%" viewBox="0 0 640 96" preserveAspectRatio="none">
          <rect width={640} height={96} fill="rgba(0,0,0,0.16)" />
          <circle cx={470} cy={96} r={80} fill="rgba(255,255,255,0.14)" />
          <circle cx={560} cy={30} r={44} fill="rgba(255,255,255,0.12)" />
          <rect x={0} y={60} width={640} height={2} fill="rgba(255,255,255,0.22)" />
          <text x={30} y={46} fill="rgba(255,255,255,0.92)" fontFamily={FONT} fontWeight={700} fontSize={26}>
            Café · Pâtisserie
          </text>
          <text x={30} y={86} fill="rgba(255,255,255,0.75)" fontFamily={FONT} fontSize={18}>
            8 tampons = une boisson offerte
          </text>
        </svg>
      </div>
      {/* Tampons */}
      <div
        style={{
          position: "absolute",
          left: pad,
          top: pad + 186 * k,
          display: "flex",
          gap: (580 * k - pad * 0 - stampSize * total) / (total - 1) - 0.01,
          width: 580 * k,
          opacity: layers.stamps,
        }}
      >
        {Array.from({ length: total }).map((_, i) => {
          const isNew = stampAt !== undefined && i === filled - 1;
          const on = i < shown || isNew;
          if (isNew) {
            return (
              <div key={i} style={{ position: "relative", width: stampSize, height: stampSize }}>
                <Ring size={stampSize} variant="empty" color={C.paper} style={{ position: "absolute", opacity: frame < (stampAt ?? 0) ? 1 : 0 }} />
                <Ring
                  size={stampSize}
                  variant="stamp"
                  color={C.paper}
                  style={{
                    position: "absolute",
                    scale: String(stampScale(frame, stampAt ?? 0)),
                    opacity: stampOpacity(frame, stampAt ?? 0),
                  }}
                />
              </div>
            );
          }
          return <Ring key={i} size={stampSize} variant={on ? "stamp" : "empty"} color={C.paper} />;
        })}
      </div>
      {/* Titulaire + QR de la carte */}
      <div
        style={{
          position: "absolute",
          left: pad,
          right: pad,
          bottom: pad,
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          opacity: layers.stamps,
        }}
      >
        <div>
          <div style={{ fontSize: 15 * k, fontWeight: 700, letterSpacing: "0.12em", opacity: 0.8 }}>MEMBRE</div>
          <div style={{ fontSize: 28 * k, fontWeight: 700 }}>{holder}</div>
        </div>
        {showQr ? (
          <div style={{ padding: 6 * k, background: "#fff", borderRadius: 8 * k }}>
            <Qr id="demoCard" size={64 * k} />
          </div>
        ) : null}
      </div>
    </div>
  );
};
