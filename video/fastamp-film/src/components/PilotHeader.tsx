import React from "react";
import { C } from "../theme";
import { PremiumBadge } from "./ui";

/** En-tête d'un écran manager : onglet Pilotage › module, badge Premium. */
export const PilotHeader: React.FC<{ module: string; k: number; dark?: boolean; badgeAt: number }> = ({ module, k, dark, badgeAt }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      paddingBottom: 18 * k,
      marginBottom: 22 * k,
      borderBottom: `1.5px solid ${dark ? "rgba(199,185,232,0.2)" : "rgba(35,10,92,0.12)"}`,
    }}
  >
    <div style={{ fontSize: 24 * k, fontWeight: 700, color: dark ? "rgba(250,249,252,0.6)" : "rgba(24,23,26,0.5)" }}>
      Compte manager · Pilotage ›{" "}
      <span style={{ color: dark ? C.paper : C.ink }}>{module}</span>
    </div>
    <PremiumBadge size={20 * k} at={badgeAt} />
  </div>
);
