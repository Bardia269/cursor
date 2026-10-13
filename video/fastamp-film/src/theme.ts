import { staticFile } from "remotion";

// Palette extraite de la DA Fastamp (13/10/2026).
export const C = {
  night: "#120927",
  deep: "#230A5C",
  transit: "#1B0C3E",
  lavender: "#C7B9E8",
  paper: "#FAF9FC",
  ink: "#18171A",
  graphite: "#1B1C1F",
  // Couleurs de carte du commerce fictif (pas des couleurs de marque).
  cardBlue: "#5688D8",
  cardPlum: "#9A6BB9",
  cardCoral: "#D77862",
};

export const HERO_GRADIENT = `linear-gradient(105deg, ${C.night} 0%, ${C.transit} 55%, ${C.deep} 100%)`;

// Helvetica Neue / Helvetica / Arial dans la DA : Liberation Sans est la
// métrique Arial embarquée pour un rendu identique sur toutes les machines.
export const FONT = "FastampSans, 'Helvetica Neue', Helvetica, Arial, sans-serif";

const fontFaces = `
@font-face { font-family: FastampSans; font-weight: 400; src: url(${staticFile("fonts/LiberationSans-Regular.ttf")}) format("truetype"); }
@font-face { font-family: FastampSans; font-weight: 700; src: url(${staticFile("fonts/LiberationSans-Bold.ttf")}) format("truetype"); }
`;

if (typeof document !== "undefined" && !document.getElementById("fastamp-fonts")) {
  const style = document.createElement("style");
  style.id = "fastamp-fonts";
  style.textContent = fontFaces;
  document.head.appendChild(style);
}

export const EASE_OUT = [0.16, 1, 0.3, 1] as const;
export const EASE_IN_OUT = [0.65, 0, 0.35, 1] as const;

export const FPS = 30;
export const TRANSITION = 24;
