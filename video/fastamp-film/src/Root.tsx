import React from "react";
import { Composition, Folder } from "remotion";
import { FILM_DURATION, Film, SCENES } from "./Film";
import { FPS } from "./theme";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Fastamp-16x9" component={Film} durationInFrames={FILM_DURATION} fps={FPS} width={1920} height={1080} />
      <Composition id="Fastamp-9x16" component={Film} durationInFrames={FILM_DURATION} fps={FPS} width={1080} height={1920} />
      <Folder name="Scenes-16x9">
        {SCENES.map((s) => (
          <Composition key={s.id} id={s.id} component={s.component} durationInFrames={s.duration} fps={FPS} width={1920} height={1080} />
        ))}
      </Folder>
      <Folder name="Scenes-9x16">
        {SCENES.map((s) => (
          <Composition key={s.id} id={`${s.id}-V`} component={s.component} durationInFrames={s.duration} fps={FPS} width={1080} height={1920} />
        ))}
      </Folder>
    </>
  );
};
