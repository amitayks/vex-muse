"""check.py VIDEO [REF] — per-frame: is the tesseract drawn, does it move, how close to the reference render."""
import sys, cv2, numpy as np
vid = sys.argv[1]; ref = sys.argv[2] if len(sys.argv) > 2 else None
def frames(p):
    c = cv2.VideoCapture(p)
    while True:
        ok, f = c.read()
        if not ok: return
        yield cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
A = list(frames(vid)); R = list(frames(ref)) if ref else None
ink = np.array([(g[:870, 300:1350] < 90).sum() for g in A])            # dark pixels in the tesseract zone
mot = np.array([0] + [np.abs(A[i] - A[i - 1]).mean() for i in range(1, len(A))])
empty = [i for i in range(len(A)) if ink[i] < 500 and i > 3]
print(f"frames {len(A)} | frames with no drawing (after build-in): {len(empty)}" + (f" first at {empty[0]/30:.2f}s" if empty else ""))
print(f"frames identical to previous: {int((mot[1:] < 0.05).sum())} | mean motion {mot.mean():.3f}")
if R:
    n = min(len(A), len(R)); d = np.array([np.abs(A[i] - R[i]).mean() for i in range(n)])
    strong = np.array([(np.abs(A[i] - R[i]) > 60).mean() * 100 for i in range(n)])
    print(f"vs reference: mean abs diff {d.mean():.2f}/255 (max {d.max():.2f} at {d.argmax()/30:.2f}s); strongly different pixels {strong.mean():.2f}% (max {strong.max():.2f}%)")
