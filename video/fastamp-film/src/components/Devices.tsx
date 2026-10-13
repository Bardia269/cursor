import React from "react";
import { Img, staticFile } from "remotion";
import { C, FONT } from "../theme";

type PhoneProps = { width: number; children?: React.ReactNode; screen?: string; style?: React.CSSProperties };

export const Phone: React.FC<PhoneProps> = ({ width, children, screen = C.paper, style }) => {
  const h = width * 2.05;
  const bezel = width * 0.035;
  return (
    <div
      style={{
        width,
        height: h,
        borderRadius: width * 0.16,
        background: "#0E0D11",
        padding: bezel,
        boxShadow: `0 ${width * 0.08}px ${width * 0.2}px rgba(10,4,30,0.35), inset 0 0 0 2px #2A2930`,
        position: "relative",
        ...style,
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: width * 0.13,
          background: screen,
          overflow: "hidden",
          position: "relative",
          fontFamily: FONT,
        }}
      >
        {children}
        <div
          style={{
            position: "absolute",
            top: width * 0.035,
            left: "50%",
            translate: "-50% 0",
            width: width * 0.3,
            height: width * 0.085,
            borderRadius: width,
            background: "#0E0D11",
          }}
        />
      </div>
    </div>
  );
};

type TabletProps = { width: number; children?: React.ReactNode; style?: React.CSSProperties; title?: string };

/** Tablette de l'équipe : l'appareil Fastamp, clairement distinct du téléphone client. */
export const Tablet: React.FC<TabletProps> = ({ width, children, style, title = "Fastamp · Scanner" }) => {
  const h = width * 0.74;
  const bezel = width * 0.03;
  return (
    <div
      style={{
        width,
        height: h,
        borderRadius: width * 0.06,
        background: "#0E0D11",
        padding: bezel,
        boxShadow: `0 ${width * 0.05}px ${width * 0.12}px rgba(10,4,30,0.3), inset 0 0 0 2px #2A2930`,
        position: "relative",
        ...style,
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: width * 0.035,
          background: C.paper,
          overflow: "hidden",
          position: "relative",
          fontFamily: FONT,
          color: C.ink,
        }}
      >
        <div
          style={{
            height: width * 0.085,
            background: C.night,
            color: C.paper,
            display: "flex",
            alignItems: "center",
            padding: `0 ${width * 0.04}px`,
            gap: width * 0.02,
            fontWeight: 700,
            fontSize: width * 0.034,
          }}
        >
          <Img src={staticFile("brand/icon.svg")} style={{ width: width * 0.05, height: width * 0.05, borderRadius: width * 0.01 }} />
          {title}
        </div>
        {children}
      </div>
    </div>
  );
};
