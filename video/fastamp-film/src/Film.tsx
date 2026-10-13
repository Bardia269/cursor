import React from "react";
import { Audio } from "@remotion/media";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { Easing, interpolate, staticFile, useVideoConfig } from "remotion";
import { S01Promise } from "./scenes/S01Promise";
import { S02Join } from "./scenes/S02Join";
import { S03Identity } from "./scenes/S03Identity";
import { S04Visit } from "./scenes/S04Visit";
import { S05Notify } from "./scenes/S05Notify";
import { S06Signals } from "./scenes/S06Signals";
import { S07Autopilot } from "./scenes/S07Autopilot";
import { S08Impact } from "./scenes/S08Impact";
import { S09Plans } from "./scenes/S09Plans";
import { S10Invite } from "./scenes/S10Invite";
import { stampIris } from "./transitions/stampIris";
import { C, TRANSITION } from "./theme";

export const SCENES = [
  { id: "S01-Promesse", component: S01Promise, duration: 300 },
  { id: "S02-Rejoindre", component: S02Join, duration: 240 },
  { id: "S03-Identite", component: S03Identity, duration: 240 },
  { id: "S04-Passage", component: S04Visit, duration: 270 },
  { id: "S05-Lien", component: S05Notify, duration: 255 },
  { id: "S06-Signals", component: S06Signals, duration: 255 },
  { id: "S07-Autopilot", component: S07Autopilot, duration: 255 },
  { id: "S08-Impact", component: S08Impact, duration: 255 },
  { id: "S09-Niveaux", component: S09Plans, duration: 210 },
  { id: "S10-Invitation", component: S10Invite, duration: 300 },
] as const;

export const FILM_DURATION = SCENES.reduce((a, s) => a + s.duration, 0) - TRANSITION * (SCENES.length - 1);

/** Origine de chaque iris (fraction de l'image) : l'anneau s'ouvre là où l'œil est déjà. */
const IRIS: [number, number, string][] = [
  [0.72, 0.56, C.lavender], // carte → comptoir
  [0.8, 0.52, C.deep], // téléphone → carte géante
  [0.68, 0.52, C.lavender], // carte → passage
  [0.53, 0.46, C.deep], // tampon → notifications
  [0.78, 0.4, C.lavender], // alerte → Signals
  [0.8, 0.62, C.deep], // validation → Autopilot
  [0.62, 0.55, C.lavender], // relance → Impact
  [0.5, 0.6, C.deep], // Impact → niveaux
  [0.5, 0.5, C.lavender], // niveaux → invitation
];

export const Film: React.FC = () => {
  const { fps, width, height, durationInFrames } = useVideoConfig();
  return (
    <>
      <TransitionSeries name="Film Fastamp">
        {SCENES.map((s, i) => {
          const Scene = s.component;
          const iris = IRIS[i];
          return (
            <React.Fragment key={s.id}>
              <TransitionSeries.Sequence name={s.id} durationInFrames={s.duration} premountFor={fps}>
                <Scene />
              </TransitionSeries.Sequence>
              {iris ? (
                <TransitionSeries.Transition
                  presentation={stampIris({ x: iris[0], y: iris[1], width, height, ringColor: iris[2] })}
                  timing={linearTiming({ durationInFrames: TRANSITION, easing: Easing.bezier(0.7, 0, 0.25, 1) })}
                />
              ) : null}
            </React.Fragment>
          );
        })}
      </TransitionSeries>
      <Audio
        src={staticFile("audio/music.wav")}
        volume={(f) =>
          0.5 * interpolate(f, [0, 20, durationInFrames - 75, durationInFrames - 1], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
        }
      />
    </>
  );
};
