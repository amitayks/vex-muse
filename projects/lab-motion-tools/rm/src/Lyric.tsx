import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";
// Transparent kinetic-lyric layer. Words + onsets come from song.json (props), never retyped.
type W = { w: string; t0: number; t1: number };
const INK = "#111013", CREAM = "#EEE8E0", RED = "#EA4032";
export const Lyric: React.FC<{ words: W[]; slam: string; slamAt: number }> = ({ words, slam, slamAt }) => {
  const f = useCurrentFrame(), { fps } = useVideoConfig(), t = f / fps;
  // phrases: a new phrase clears the last one (a lyric block never outgrows its zone)
  const phraseStart = words.findIndex(w => /^'cause$/i.test(w.w));
  const inPhrase2 = phraseStart > 0 && t >= words[phraseStart].t0 - 1 / fps;
  const shown = words.filter((w, i) => t >= w.t0 - 1 / fps && (inPhrase2 ? i >= phraseStart : i < (phraseStart > 0 ? phraseStart : 1e9)));
  const slamIn = spring({ frame: f - Math.round(slamAt * fps), fps, config: { damping: 9, stiffness: 260, mass: 0.7 } });
  const preSlam = t < slamAt;
  return (
    <AbsoluteFill>
      {preSlam && (
        <div style={{ position: "absolute", left: 120, top: 190, width: 1000, display: "flex", flexWrap: "wrap", gap: "0 34px", alignItems: "baseline" }}>
          {shown.map((w, i) => {
            const s = spring({ frame: f - Math.round((w.t0 - 1 / fps) * fps), fps, config: { damping: 13, stiffness: 320, mass: 0.6 } });
            const serif = /^(my|the|'cause)$/i.test(w.w);
            const hero = /p\(doom\)/i.test(w.w);
            return (
              <span key={i} style={{ display: "inline-block", overflow: "hidden", paddingBottom: 14 }}>
                <span style={{ display: "inline-block", transform: `translateY(${(1 - s) * 105}%) rotate(${(1 - s) * (hero ? -8 : 0)}deg)`,
                  fontFamily: serif ? "MuseSerif" : "MuseDisplay", fontStyle: serif ? "italic" : "normal",
                  fontSize: hero ? 190 : serif ? 150 : 128, lineHeight: 1, color: hero ? RED : CREAM,
                  textShadow: "0 6px 0 rgba(17,16,19,.55)", letterSpacing: serif ? 0 : "-0.01em" }}>{serif ? w.w.toLowerCase() : w.w.toUpperCase()}</span>
              </span>
            );
          })}
        </div>
      )}
      {!preSlam && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ fontFamily: "MuseDisplay", fontSize: 470, color: CREAM, lineHeight: 1, transform: `scale(${interpolate(slamIn, [0, 1], [1.9, 1])})`,
            opacity: Math.min(1, slamIn * 3), textShadow: `0 14px 0 ${INK}`, letterSpacing: "-0.02em",
            filter: `blur(${interpolate(slamIn, [0, 0.6], [14, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.quad) })}px)` }}>{slam}</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
