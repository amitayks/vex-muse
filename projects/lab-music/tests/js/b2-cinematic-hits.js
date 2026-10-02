// b2-cinematic-hits.js — 90 BPM (bar = 2.667 s): impacts EXACTLY at 8.0, 16.0, 24.0 s (bars 3, 6, 9); D minor; ring-out to 30 s.
var meta = { bpm: 90 };
async function score(ctx, T) {
  const H = [8, 16, 24], r = T.rand(9), sr = ctx.sampleRate;
  const master = ctx.createDynamicsCompressor(); master.threshold.value = -10; master.ratio.value = 3; master.connect(ctx.destination);
  const ir = ctx.createBuffer(2, sr * 3.5, sr); for (let c = 0; c < 2; c++) { const d = ir.getChannelData(c); for (let i = 0; i < d.length; i++) d[i] = (r() * 2 - 1) * Math.pow(1 - i / d.length, 3); }
  const verb = ctx.createConvolver(); verb.buffer = ir; const wet = ctx.createGain(); wet.gain.value = 0.35; verb.connect(wet).connect(master);
  const bus = ctx.createGain(); bus.connect(master); bus.connect(verb);
  const nb = (() => { const b = ctx.createBuffer(1, sr * 4, sr), d = b.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = r() * 2 - 1; return b; })();
  const hz = n => 440 * Math.pow(2, (n - 69) / 12);
  const impact = (t, big) => {
    const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.setValueAtTime(big ? 90 : 75, t); o.frequency.exponentialRampToValueAtTime(28, t + 1.4);
    g.gain.setValueAtTime(1.0, t); g.gain.exponentialRampToValueAtTime(0.001, t + (big ? 4 : 2.5)); o.connect(g).connect(bus); o.start(t); o.stop(t + 4.2);
    const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), n = ctx.createGain(); s.buffer = nb; f.type = 'lowpass'; f.frequency.setValueAtTime(6000, t); f.frequency.exponentialRampToValueAtTime(200, t + 1.2);
    n.gain.setValueAtTime(0.9, t); n.gain.exponentialRampToValueAtTime(0.001, t + 1.5); s.connect(f).connect(n).connect(bus); s.start(t); s.stop(t + 1.6);
    if (big) { const c = ctx.createBufferSource(), hp = ctx.createBiquadFilter(), cg = ctx.createGain(); c.buffer = nb; hp.type = 'highpass'; hp.frequency.value = 5000; cg.gain.setValueAtTime(0.35, t); cg.gain.exponentialRampToValueAtTime(0.001, t + 3); c.connect(hp).connect(cg).connect(bus); c.start(t, 1); c.stop(t + 3.1); }
  };
  const taiko = (t, a) => { const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.setValueAtTime(110, t); o.frequency.exponentialRampToValueAtTime(55, t + 0.25); g.gain.setValueAtTime(a, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.5); o.connect(g).connect(bus); o.start(t); o.stop(t + 0.55); };
  const pad = (notes, t0, t1, g0, g1, cut0, cut1, type = 'sawtooth') => { for (const n of notes) for (const dt of [-8, 8]) {
    const o = ctx.createOscillator(), f = ctx.createBiquadFilter(), g = ctx.createGain(); o.type = type; o.frequency.value = hz(n); o.detune.value = dt;
    f.type = 'lowpass'; f.frequency.setValueAtTime(cut0, t0); f.frequency.exponentialRampToValueAtTime(cut1, t1);
    g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(g0, t0 + 0.8); g.gain.exponentialRampToValueAtTime(g1, t1 - 0.02); g.gain.linearRampToValueAtTime(0.0001, t1);
    o.connect(f).connect(g).connect(bus); o.start(t0); o.stop(t1); } };
  // 0-8: ticking 8ths + low D drone
  for (let t = 0; t < 8 - 0.01; t += T.beat / 2) { const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain(); s.buffer = nb; f.type = 'bandpass'; f.frequency.value = 4200; f.Q.value = 12; g.gain.setValueAtTime(0.25, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.03); s.connect(f).connect(g).connect(bus); s.start(t, r()); s.stop(t + 0.04); }
  pad([38, 45], 0, 8, 0.05, 0.08, 300, 700);
  // 8-16: rising strings + brass swell + noise riser into 16
  pad([50, 53, 57], 8, 16, 0.02, 0.07, 600, 5000); pad([38, 45, 50], 8, 16, 0.03, 0.09, 200, 1800, 'square');
  { const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain(); s.buffer = nb; f.type = 'bandpass'; f.Q.value = 3; f.frequency.setValueAtTime(400, 12); f.frequency.exponentialRampToValueAtTime(9000, 16); g.gain.setValueAtTime(0.0001, 12); g.gain.exponentialRampToValueAtTime(0.4, 15.98); g.gain.setValueAtTime(0, 16); s.connect(f).connect(g).connect(bus); s.start(12); s.stop(16); }
  // 16-24: driving taiko 8ths with accents, 16th string ostinato, brass stab each bar
  for (let t = 16; t < 24 - 0.01; t += T.beat / 2) { const k = Math.round((t - 16) / (T.beat / 2)); taiko(t, k % 4 === 0 ? 0.8 : 0.35); }
  const ost = [62, 65, 69, 74]; for (let t = 16, k = 0; t < 24 - 0.01; t += T.beat / 4, k++) { const o = ctx.createOscillator(), f = ctx.createBiquadFilter(), g = ctx.createGain(); o.type = 'sawtooth'; o.frequency.value = hz(ost[k % 4]); f.type = 'lowpass'; f.frequency.value = 3000; g.gain.setValueAtTime(0.06, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.12); o.connect(f).connect(g).connect(bus); o.start(t); o.stop(t + 0.14); }
  for (let t = 16; t < 24 - 0.01; t += T.bar) pad([50, 57, 62], t, t + 0.9, 0.08, 0.03, 2500, 900, 'square');
  pad([38, 50], 16, 24, 0.06, 0.08, 500, 1500);
  for (const t of H) impact(t, t !== 8);
}
