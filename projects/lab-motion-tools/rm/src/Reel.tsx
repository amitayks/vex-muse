import React from "react";
import { AbsoluteFill, Audio, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing, delayRender, continueRender } from "remotion";
import { evolvePath } from "@remotion/paths";
import { useAudioData, visualizeAudio } from "@remotion/media-utils";
import { interpolate as flubber } from "flubber";

export const reelSchema = null;
const INK = "#111013", CREAM = "#EEE8E0", BLUE = "#3140E8", SUN = "#F2C841";

const SHAPES = {
  circle: "M200,20 C299.4,20 380,100.6 380,200 C380,299.4 299.4,380 200,380 C100.6,380 20,299.4 20,200 C20,100.6 100.6,20 200,20 Z",
  square: "M90,40 H310 C337.6,40 360,62.4 360,90 V310 C360,337.6 337.6,360 310,360 H90 C62.4,360 40,337.6 40,310 V90 C40,62.4 62.4,40 90,40 Z",
  tri: "M200,34 L366,318 C375,335 364,352 344,352 H56 C36,352 25,335 34,318 Z",
};
const spark = (() => { let d = ""; const n = 11; for (let i = 0; i < n; i++) { const a = -Math.PI / 2 + i * 2 * Math.PI / n, a2 = a + Math.PI / n, R = 195 - (i % 3) * 16, r = 62;
  const p = (ang: number, rad: number) => `${(200 + rad * Math.cos(ang)).toFixed(1)},${(200 + rad * Math.sin(ang)).toFixed(1)}`;
  d += (i ? "L" : "M") + p(a - 0.09, R) + " L" + p(a + 0.09, R) + " L" + p(a2, r) + " "; } return d + "Z"; })();
const seq = [SHAPES.circle, SHAPES.square, SHAPES.tri, spark];
const cols = ["#EA4032", BLUE, SUN, "#EA4032"];
const morphs = seq.slice(0, -1).map((s, i) => flubber(s, seq[i + 1], { maxSegmentLength: 4 }));

export const Reel: React.FC<{ bpm: number; words: string[]; accent: string }> = ({ bpm, words, accent }) => {
  const frame = useCurrentFrame(); const { fps } = useVideoConfig();
  const B = 60 / bpm, t = frame / fps, beat = t / B;           // time in beats: the only clock the design reads
  const audio = useAudioData(staticFile("beat128.wav"));

  // ---- bar 1: morph chain, one identity per beat (flubber) ----
  const k = Math.min(2, Math.floor(beat)), local = beat - Math.floor(beat);
  const mp = interpolate(local, [0.62, 0.95], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.83, 0, 0.17, 1) });
  const d = beat >= 3 ? spark : morphs[k](mp);
  const fill = beat >= 3 ? cols[3] : mp < 0.5 ? cols[k] : cols[k + 1];
  const rot = interpolate(beat, [0, 4], [0, 300], { easing: Easing.bezier(0.65, 0, 0.35, 1) });
  const pop = spring({ frame, fps, config: { damping: 11, mass: 0.6 } });
  // outline draws itself around the shape (evolvePath = stroke-dasharray math)
  const draw = evolvePath(interpolate(beat, [0.2, 1.2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), SHAPES.circle);

  // ---- bar 2: kinetic words on beats, sizes pulse with the kick (audio-reactive) ----
  const bar2 = beat >= 4;
  const amp = audio ? visualizeAudio({ fps, frame, audioData: audio, numberOfSamples: 16 })[0] : 0;
  const wi = Math.min(words.length - 1, Math.floor(beat - 4));
  const wLocal = beat - 4 - wi;
  const wIn = spring({ frame: Math.round((wLocal) * B * fps), fps, config: { damping: 14, stiffness: 220 } });

  return (
    <AbsoluteFill style={{ background: bar2 ? accent : INK }}>
      <Audio src={staticFile("beat128.wav")} />
      {!bar2 && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <svg viewBox="-100 -100 600 600" width={760} height={760} style={{ transform: `rotate(${rot}deg) scale(${pop})` }}>
            <path d={SHAPES.circle} fill="none" stroke={CREAM} strokeWidth={3} strokeDasharray={draw.strokeDasharray} strokeDashoffset={draw.strokeDashoffset} opacity={beat < 1.3 ? 0.8 : 0} />
            <path d={d} fill={fill} />
          </svg>
          <div style={{ position: "absolute", right: 120, top: 120, fontFamily: "MuseMono", fontSize: 22, letterSpacing: "0.14em", color: CREAM }}>
            FLUBBER · {["CIRCLE", "SQUARE", "TRIANGLE", "SPARK"][Math.min(3, Math.round(beat))]}
          </div>
        </AbsoluteFill>
      )}
      {bar2 && (
        <AbsoluteFill style={{ alignItems: "flex-start", justifyContent: "center", paddingLeft: 170 }}>
          <div style={{ fontFamily: wi === 2 || wi === 3 ? "MuseSerif" : "MuseDisplay", fontStyle: wi === 2 || wi === 3 ? "italic" : "normal",
            fontSize: (wi === 4 ? 230 : 300) * (1 + amp * 0.12), color: wi === 2 || wi === 3 ? CREAM : INK, lineHeight: 1,
            transform: `translateY(${(1 - wIn) * 120}px)`, opacity: Math.min(1, wIn * 1.4) }}>{words[wi]}</div>
          <div style={{ position: "absolute", left: 170, bottom: 120, display: "flex", gap: 10 }}>
            {words.map((_, i) => <div key={i} style={{ width: 60, height: 8, background: i <= wi ? INK : "rgba(17,16,19,.25)" }} />)}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
