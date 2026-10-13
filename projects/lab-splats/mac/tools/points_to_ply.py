#!/usr/bin/env python3
"""points_to_ply.py - COLMAP points3D.bin -> minimal 3DGS PLY (isotropic splats, SH degree 0). Test asset only."""
import math, struct, sys
src, dst = sys.argv[1], sys.argv[2]; size = float(sys.argv[3]) if len(sys.argv) > 3 else 0.03
C0 = 0.28209479177387814; pts = []
with open(src, "rb") as f:
    n, = struct.unpack("<Q", f.read(8))
    for _ in range(n):
        _id, x, y, z, r, g, b, _e = struct.unpack("<QdddBBBd", f.read(43)); tl, = struct.unpack("<Q", f.read(8)); f.seek(8 * tl, 1)
        pts.append((x, y, z, (r / 255 - 0.5) / C0, (g / 255 - 0.5) / C0, (b / 255 - 0.5) / C0))
props = ["x", "y", "z", "f_dc_0", "f_dc_1", "f_dc_2", "opacity", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]
hdr = "ply\nformat binary_little_endian 1.0\nelement vertex %d\n" % len(pts) + "".join(f"property float {p}\n" for p in props) + "end_header\n"
ls = math.log(size); op = 3.0
with open(dst, "wb") as o:
    o.write(hdr.encode())
    for p in pts: o.write(struct.pack("<14f", *p, op, ls, ls, ls, 1, 0, 0, 0))
print(dst, len(pts))
