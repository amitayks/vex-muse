// b1-beat128.js — 16 bars at 128 BPM = exactly 30.000 s; A minor; hard stop on the last sample.
var meta = { bpm: 128 };
async function score(ctx, T) {
  const END = T.at(16), master = ctx.createDynamicsCompressor(); master.threshold.value = -14; master.ratio.value = 4; master.connect(ctx.destination);
  const duck = ctx.createGain(); duck.connect(master);                      // sidechain bus for pads/bass
  const r = T.rand(3), noise = (len) => { const b = ctx.createBuffer(1, Math.ceil(len * ctx.sampleRate), ctx.sampleRate), d = b.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = r() * 2 - 1; return b; };
  const nb = noise(1);
  const hz = n => 440 * Math.pow(2, (n - 69) / 12);
  const env = (g, t, a, peak, dec) => { g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + a + dec); };
  const kick = t => { const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.setValueAtTime(150, t); o.frequency.exponentialRampToValueAtTime(45, t + 0.12); env(g, t, 0.002, 1.0, 0.32); o.connect(g).connect(master); o.start(t); o.stop(Math.min(END, t + 0.4));
    duck.gain.setValueAtTime(0.35, t); duck.gain.linearRampToValueAtTime(1, Math.min(END, t + T.beat * 0.8)); };
  const clap = t => { const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain(); s.buffer = nb; f.type = 'bandpass'; f.frequency.value = 1500; f.Q.value = 0.8; env(g, t, 0.001, 0.55, 0.16); s.connect(f).connect(g).connect(master); s.start(t, r() * 0.5); s.stop(Math.min(END, t + 0.2)); };
  const hat = (t, open) => { const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain(); s.buffer = nb; f.type = 'highpass'; f.frequency.value = 8000; env(g, t, 0.001, open ? 0.18 : 0.12, open ? 0.18 : 0.04); s.connect(f).connect(g).connect(master); s.start(t, r() * 0.5); s.stop(Math.min(END, t + 0.25)); };
  const prog = [57, 53, 48, 55];                                              // Am F C G roots (2 bars each)
  const pluckF = ctx.createBiquadFilter(); pluckF.type = 'lowpass'; pluckF.Q.value = 6; pluckF.frequency.setValueAtTime(900, 0); pluckF.frequency.setValueAtTime(900, T.at(4) - 0.01); pluckF.frequency.linearRampToValueAtTime(5200, T.at(4)); pluckF.connect(master);
  const hook = [69, 72, 76, 72, 74, 72, 69, 67];                              // A C E C D C A G, 8ths
  for (let bar = 0; bar < 16; bar++) {
    const root = prog[Math.floor(bar / 2) % 4];
    for (let b = 0; b < 4; b++) {
      const t = T.at(bar, b); kick(t); hat(t + T.beat / 2, bar >= 4 && b % 2 === 1);
      if (bar >= 4 && (b === 1 || b === 3)) clap(t);
      // sub bass: offbeat 8ths on the root
      const o = ctx.createOscillator(), g = ctx.createGain(); o.type = 'sine'; o.frequency.value = hz(root - 24); env(g, t + T.beat / 2, 0.005, 0.5, T.beat * 0.45); o.connect(g).connect(duck); o.start(t + T.beat / 2); o.stop(Math.min(END, t + T.beat));
    }
    for (let k = 0; k < 8; k++) {                                             // pluck hook
      const t = T.at(bar, k / 2), o = ctx.createOscillator(), g = ctx.createGain(); o.type = 'sawtooth'; o.frequency.value = hz(hook[(k + bar) % 8] + (bar % 4 === 3 && k > 5 ? 2 : 0));
      env(g, t, 0.003, 0.16, 0.22); o.connect(g).connect(pluckF); o.start(t); o.stop(Math.min(END, t + 0.3));
    }
    if (bar >= 4) for (const iv of [0, 3, 7, 12]) {                          // pads from bar 5, minor-ish stacks
      const t = T.at(bar), o = ctx.createOscillator(), g = ctx.createGain(), f = ctx.createBiquadFilter(); o.type = 'sawtooth'; o.detune.value = (iv % 2 ? 7 : -7); o.frequency.value = hz(root - 12 + iv - (iv === 3 && [53, 48].includes(root) ? -1 : 0));
      f.type = 'lowpass'; f.frequency.value = 2200; g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.035, t + 0.3); g.gain.setValueAtTime(0.035, t + T.bar - 0.05); g.gain.linearRampToValueAtTime(0.0001, t + T.bar);
      o.connect(f).connect(g).connect(duck); o.start(t); o.stop(Math.min(END, t + T.bar));
    }
  }
}
