// example-riser.js — a 2-bar riser into a downbeat hit, the kind of sting that sits under a chorus entrance.
var meta = { bpm: 128 };
async function score(ctx, T) {
  const out = ctx.createDynamicsCompressor(); out.connect(ctx.destination);
  // noise riser: filtered white noise, cutoff sweeps up over 2 bars
  const len = T.at(2), nb = ctx.createBuffer(1, Math.ceil(len * ctx.sampleRate), ctx.sampleRate), d = nb.getChannelData(0), r = T.rand(7);
  for (let i = 0; i < d.length; i++) d[i] = r() * 2 - 1;
  const n = ctx.createBufferSource(); n.buffer = nb;
  const f = ctx.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = 4;
  f.frequency.setValueAtTime(300, 0); f.frequency.exponentialRampToValueAtTime(9000, len);
  const g = ctx.createGain(); g.gain.setValueAtTime(0.0001, 0); g.gain.exponentialRampToValueAtTime(0.6, len * 0.98); g.gain.setValueAtTime(0, len);
  n.connect(f).connect(g).connect(out); n.start(0);
  // snare roll accelerating on 16ths in the second bar
  for (let k = 0; k < 16; k++) {
    const t = T.at(1) + k * T.beat / 4, s = ctx.createOscillator(), sg = ctx.createGain();
    s.type = 'triangle'; s.frequency.value = 190; sg.gain.setValueAtTime(0.15 + k * 0.02, t); sg.gain.exponentialRampToValueAtTime(0.001, t + 0.08);
    s.connect(sg).connect(out); s.start(t); s.stop(t + 0.1);
  }
  // downbeat impact: sub drop + click
  const t0 = T.at(2), sub = ctx.createOscillator(), sg = ctx.createGain();
  sub.frequency.setValueAtTime(110, t0); sub.frequency.exponentialRampToValueAtTime(38, t0 + 0.6);
  sg.gain.setValueAtTime(0.9, t0); sg.gain.exponentialRampToValueAtTime(0.001, t0 + 1.2);
  sub.connect(sg).connect(out); sub.start(t0); sub.stop(t0 + 1.3);
}
