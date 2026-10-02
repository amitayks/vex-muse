// b2-hits-only.js — 90 BPM (bar = 2.667 s): impacts EXACTLY at 8.0, 16.0, 24.0 s (bars 3, 6, 9); D minor; ring-out to 30 s.
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
  { const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain(); s.buffer = nb; f.type = 'bandpass'; f.Q.value = 3; f.frequency.setValueAtTime(400, 12); f.frequency.exponentialRampToValueAtTime(9000, 16); g.gain.setValueAtTime(0.0001, 12); g.gain.exponentialRampToValueAtTime(0.4, 15.98); g.gain.setValueAtTime(0, 16); s.connect(f).connect(g).connect(bus); s.start(12); s.stop(16); }
  for (const t of H) impact(t, t !== 8);
}
