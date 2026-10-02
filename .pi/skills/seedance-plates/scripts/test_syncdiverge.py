#!/usr/bin/env python3
"""Validate syncdiverge on real plates with known answers, $0.

  $PY test_syncdiverge.py <project_dir> <clean_plate.mp4> <clean_slice.wav> <other_plate.mp4> <other_slice.wav>

Builds synthetic plate soundtracks from a clean plate and checks the detector finds what
was done to them:
  clean          -> in_sync
  wrong slice    -> no_copy
  replace @2.0 s -> diverges, t_div ~ 2.0   (the model re-sang / hallucinated from there)
  slip 100 ms    -> diverges (slip), t_div ~ 2.0, local lag ~ +100
  slip 250 ms    -> diverges, t_div ~ 2.0
  silence @2.0 s -> diverges, t_div ~ 2.0   (soundtrack dropped out)
Exit code 1 if any case fails.
"""
import sys, os, json, tempfile, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from syncdiverge import analyse, pcm


def wav(path, y, sr):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", path],
                   input=y.astype(np.float32).tobytes(), check=True)


def main():
    _, proj, cp, cs, op, osl = sys.argv
    a, sr = pcm(cp); o, _ = pcm(op)  # the other plate's soundtrack = plausible wrong content
    T = int(2.0 * sr); d = tempfile.mkdtemp()
    cases = {
        "clean": (cp, cs, lambda r: r["verdict"] == "in_sync"),
        "wrong_slice": (cp, osl, lambda r: r["verdict"] == "no_copy"),
    }
    synth = {
        "replace@2.0": np.concatenate([a[:T], o[T:len(a)]]),
        "slip100@2.0": np.concatenate([a[:T], np.zeros(int(0.10 * sr), np.float32), a[T:]])[:len(a)],
        "slip250@2.0": np.concatenate([a[:T], np.zeros(int(0.25 * sr), np.float32), a[T:]])[:len(a)],
        "silence@2.0": np.concatenate([a[:T], 1e-4 * np.random.default_rng(0).standard_normal(len(a) - T).astype(np.float32)]),
    }
    for k, y in synth.items():
        p = os.path.join(d, k + ".wav"); wav(p, y, sr)
        cases[k] = (p, cs, lambda r: r["verdict"] == "diverges" and abs(r["t_div"] - 2.0) <= 0.3)
    ok_all = True
    for k, (p, s, ok) in cases.items():
        r, _ = analyse(p, s); good = ok(r); ok_all &= good
        print(f"{'PASS' if good else 'FAIL'} {k:12s} verdict={r['verdict']:9s} lag={r['lag_ms']:+d} match={r['match']:.2f} "
              f"copy={r['copy_margin']:.2f} thr={r['threshold']:.2f} t_div={r.get('t_div')} events={[(e['kind'], e['t0'], e['median_local_lag_ms']) for e in r['events']]}")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
