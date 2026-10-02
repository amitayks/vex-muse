# Motion brief — the taste, written down

The one-line showreel prompt worked because the model supplied taste. For work that must be good every
time, I write the taste as constraints. Fill every field; a blank field is a decision not yet made.

```
PIECE        <title> · <duration s> · <W×H> · <fps> · platform <X / IG / YT>
FEELING      one sentence the viewer leaves with
AUDIENCE     who, and what they decode in <1 s (tools, memes, UI, brands)
GRID         <BPM> BPM · <bars> bars · downbeat 0 = <song s>; every time is (bar*4+beat)*60/BPM
MOTIF        <object from THIS song's world> — opens doing <meaning> · carries transitions by <its own device> ·
             ends as <its payoff>
PALETTE      ink #… · accent #… · field2 #… · field3 #… · paper #…   (flat fields, hard switches)
TYPE         faces chosen for this song's voice (roles: statement / human / label) — sizes per mode
TEXTURE      grain σ≈1–2/255 on flats · bloom on light-on-dark type · DOF only on 3D
CHROME       frame furniture only if the concept needs it (none is a valid answer)
CHAPTERS     bar a–b  <craft>  field <colour>  event: <what changes first→last frame>  verb: <SLAMS / MORPHS…>
             …one idea per chapter; each different, all under one palette/type/motif
RHYTHM       derived from the song's energy curve (accelerando → hard stop is one option, not the rule)
TRANSITIONS  motif-driven (iris / zoom-match / collapse) or hard cut on a downbeat; 1–2 shader moments max;
             never crossfade by default
TEXT         every line: mode (hero / integrated / subtitle / none), zone, words from song.json
END CARD     wordmark + motif lands on the downbeat · subtitle types on · holds ≥ 1.5 s
MUST NOT     website-hero layouts, one layout repeated, fixed-clock slides, generic slogans, gradients
             for their own sake, glossy blobs without an event, crossfade soup, text over busy plates
CHECKS       cuts on beats ≥60% · holds 20–40% · every text readable at 360 px · motif at open+close ·
             no invisible text · lint 0 errors
```

ORIGINALITY  fingerprint traits used (max 1, with the song's reason) · 'could this look belong to another song?' → no

The lab reel in `assets/reel-template/` is a study replica of the Sep 2026 trend: its code is reusable,
its look is the fingerprint — never ship it as a style.
