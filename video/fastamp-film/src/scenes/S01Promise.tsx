import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Headline, Sub } from "../components/Headline";
import { LOGO_RINGS_LANDED, Logo3D, accentOffset } from "../components/Logo3D";
import { Sfx } from "../components/Sfx";
import { Obj, RingLight, Space, Void, camAt } from "../components/Space";
import { WalletCard } from "../components/WalletCard";
import { float, prog } from "../components/anim";
import { useLayout } from "../components/layout";
import { C } from "../theme";

const AT = 6;
const LANDED = LOGO_RINGS_LANDED(AT); // 82
const DIVE = 118;
const DEEP = -1800; // profondeur du second décor

// 01 — La promesse. Les anneaux du logo arrivent de la profondeur et se posent,
// la caméra plonge dans l'anneau lavande et découvre la carte qui flotte au-dessus du sol.
export const S01Promise: React.FC = () => {
  const frame = useCurrentFrame();
  const { pick } = useLayout();
  const logoW = pick(980, 900);
  const acc = accentOffset(logoW);
  const cam = camAt(frame, [
    { f: 0, x: 120, y: -40, z: -700, ry: -22, rx: 6 },
    { f: LANDED + 4, x: 0, y: 0, z: 0, ry: 0, rx: 0, ease: [0.25, 0.1, 0.25, 1] },
    { f: DIVE, x: 0, y: 0, z: 40 },
    { f: DIVE + 26, x: acc.x * 0.6, y: acc.y * 0.6, z: -DEEP - 260, ry: 0, rx: 0, ease: [0.7, 0, 0.3, 1] },
    { f: 300, x: pick(20, 0), y: 0, z: -DEEP - 40, ry: pick(-3, 0), rx: -1.5, ease: [0.2, 0.6, 0.3, 1] },
  ]);
  const focus = interpolate(frame, [DIVE, DIVE + 26], [0, DEEP], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const logoOpacity = 1 - prog(frame, DIVE + 6, 10);
  const f = float(frame, 30);
  const cardIn = prog(frame, DIVE + 18, 30);
  return (
    <AbsoluteFill>
      <Void glowX={pick(62, 50)} glowY={pick(38, 62)} glow={0.7 + 0.3 * prog(frame, DIVE, 30)} />
      <Space cam={cam} focus={focus} floor={pick(330, 620)} dof={0.01}>
        {logoOpacity > 0 ? <Logo3D cx={0} cy={0} cz={0} width={logoW} at={AT} opacity={logoOpacity} /> : null}

        {/* Second décor : la lumière, la carte, la promesse */}
        <Obj x={pick(820, 320)} y={pick(-460, -700)} z={DEEP - 900} sharp>
          <RingLight size={pick(320, 300)} intensity={prog(frame, DIVE + 4, 30)} />
        </Obj>
        <Obj
          x={pick(420, 0)}
          y={pick(60, 360) + f.y + (1 - cardIn) * 260}
          z={DEEP + 40}
          ry={pick(-14, -8) + f.ry}
          rx={6 + f.rx}
        >
          <div style={{ opacity: cardIn }}>
            <WalletCard width={pick(660, 760)} filled={6} />
          </div>
        </Obj>
        <Obj x={pick(-420, 0)} y={pick(-40, -430)} z={DEEP + 120} ry={pick(8, 0)}>
          <div style={{ width: pick(860, 900) }}>
            <Headline
              size={pick(98, 96)}
              lines={[
                { text: "Une carte dans", at: DIVE + 22 },
                { text: "leur téléphone.", at: DIVE + 28 },
                { text: "Une raison", at: DIVE + 64, color: C.lavender },
                { text: "de revenir.", at: DIVE + 70, color: C.lavender },
              ]}
            />
            <Sub
              at={DIVE + 108}
              size={pick(38, 40)}
              text="Fastamp, la fidélité pensée pour les commerces indépendants."
              style={{ marginTop: 36, maxWidth: pick(700, 860), color: "rgba(250,249,252,0.86)" }}
            />
          </div>
        </Obj>
      </Space>

      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Sfx key={i} name="stamp" at={AT + i * 6 + 34} volume={0.5 + i * 0.06} />
      ))}
      <Sfx name="pop" at={LANDED} volume={0.9} />
      <Sfx name="whoosh" at={0} volume={0.35} />
      <Sfx name="whoosh" at={DIVE - 2} volume={0.8} />
      <Sfx name="swipe" at={DIVE + 18} volume={0.5} />
    </AbsoluteFill>
  );
};
