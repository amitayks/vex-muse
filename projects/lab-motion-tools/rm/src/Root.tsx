import React from "react";
import { Composition } from "remotion";
import { Reel, reelSchema } from "./Reel";
import { Lyric } from "./Lyric";
import "./fonts";
// 128 BPM, 2 bars = 3.75 s. Everything downstream is written in beats.
export const Root: React.FC = () => (
  <>
  <Composition id="Reel" component={Reel} durationInFrames={Math.round(3.75 * 30) + 12} fps={30} width={1920} height={1080}
    defaultProps={{ bpm: 128, words: ["EVERY", "BEAT", "IS", "A", "DECISION."], accent: "#EA4032" }} />
  <Composition id="Lyric" component={Lyric} durationInFrames={120} fps={30} width={1920} height={1080}
    defaultProps={{ words: [], slam: "FOOM", slamAt: 3.08 }} />
  </>
);
export { reelSchema };
