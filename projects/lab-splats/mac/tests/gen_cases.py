import ast, json, math, random, sys
src = open(sys.argv[1]).read(); tree = ast.parse(src)
keep = {"_norm", "look_c2w", "_catmull", "_ease", "camera_at"}
mod = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in keep], type_ignores=[])
ns = {"math": math}; exec(compile(mod, "modal_splat_fns", "exec"), ns)
random.seed(3); cases = []
for k in range(40):
    n = random.randint(1, 6); T = sorted(random.uniform(0, 10) for _ in range(n)); T[0] = 0.0
    keys = [{"t": T[i], "pos": [random.uniform(-5, 5) for _ in range(3)], "look": [random.uniform(-5, 5) for _ in range(3)],
             "fov": random.uniform(20, 90), "roll": random.uniform(-30, 30)} for i in range(n)]
    cam = {"type": "keys", "keys": keys}
    if k % 3 == 0: cam["ease"] = random.choice(["linear", "in", "out", "smooth", "inout"])
    up = [random.uniform(-1, 1) for _ in range(3)]
    ts = [random.uniform(-1, 11) for _ in range(7)] + [T[-1], 0.0]
    cases.append({"cam": cam, "up": up, "ts": ts, "py": [[ns["camera_at"](cam, t, up)[0].tolist(), float(ns["camera_at"](cam, t, up)[1])] for t in ts]})
# frames camera incl. python round-half-even
fr = {"type": "frames", "fps": 24, "c2w": [[float(i)] * 16 for i in range(10)], "fov": [30 + i for i in range(10)]}
ts = [i / 48 for i in range(30)]
cases.append({"cam": fr, "up": [0, 0, 1], "ts": ts, "py": [[ns["camera_at"](fr, t, [0, 0, 1])[0].tolist(), float(ns["camera_at"](fr, t, [0, 0, 1])[1])] for t in ts]})
json.dump(cases, open(sys.argv[2], "w"))
print("cases", len(cases))
