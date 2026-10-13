import React from "react";
import { C } from "../theme";

type Props = {
  size: number;
  color?: string;
  /** stamp = double contour du logo ; accent = anneau lavande épais ; empty = emplacement libre */
  variant?: "stamp" | "accent" | "empty";
  style?: React.CSSProperties;
};

// Proportions reprises du symbole officiel (r 23 / 13.5, traits 7 / 3, accent r 20 trait 11).
export const Ring: React.FC<Props> = ({ size, color = C.paper, variant = "stamp", style }) => {
  return (
    <svg width={size} height={size} viewBox="-30 -30 60 60" style={{ overflow: "visible", ...style }}>
      {variant === "stamp" ? (
        <>
          <circle r={23} fill="none" stroke={color} strokeWidth={7} />
          <circle r={13.5} fill="none" stroke={color} strokeWidth={3} />
        </>
      ) : null}
      {variant === "accent" ? <circle r={20} fill="none" stroke={color} strokeWidth={11} /> : null}
      {variant === "empty" ? (
        <circle r={23} fill="none" stroke={color} strokeWidth={2.5} strokeDasharray="5 6" opacity={0.7} />
      ) : null}
    </svg>
  );
};
