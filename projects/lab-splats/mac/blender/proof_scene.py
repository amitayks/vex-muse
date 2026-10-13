"""proof_scene.py - prove the Blender -> splat camera convention (Blender 5.2, background).

blender -b --factory-startup --python proof_scene.py -- --ply X.ply --cams cameras.json --out DIR
        [--frame 30] [--proxy-max 1500000] [--vol-rel runs/.../x.ply] [--kiri] [--no-render]

1. Loads the 3DGS PLY as a light point-cloud proxy (numpy reader, SH DC colour, opacity filter),
   object "splat_world" (custom prop muse_splat=1). The object is moved, turned Z-up and scaled x2,
   so the PLY frame is NOT the Blender world frame - the export must undo that.
   With --kiri the PLY is ALSO imported through KIRI 3DGS Render (real splats, EEVEE) under the same transform.
2. Animates a 60-frame camera move (dolly, pan, lens 30 -> 42 mm) from training camera 0.
3. Exports the move with export_splat_camera.py -> camera_frames.json and shot_blender.json.
4. Renders --frame with EEVEE -> blender_fNNN.png.
5. Projects 500 PLY points with Blender's own world_to_camera_view and with the exported c2w + vertical fov
   (the pinhole modal_splat.py uses) and reports the max pixel disagreement -> proof.json.
"""
import json, math, os, random, sys

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export_splat_camera as esc  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
import argparse  # noqa: E402
ap = argparse.ArgumentParser()
ap.add_argument("--ply", required=True); ap.add_argument("--cams", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--frame", type=int, default=30); ap.add_argument("--proxy-max", type=int, default=1_500_000)
ap.add_argument("--vol-rel", default=None); ap.add_argument("--kiri", action="store_true"); ap.add_argument("--no-render", action="store_true")
ap.add_argument("--res", default="1280x720")
A = ap.parse_args(argv)
os.makedirs(A.out, exist_ok=True)
W, H = (int(v) for v in A.res.split("x"))
C0 = 0.28209479177387814


def read_ply(path):
    with open(path, "rb") as f:
        hdr = b""
        while not hdr.endswith(b"end_header\n"):
            hdr += f.readline()
        lines = hdr.decode().splitlines()
        n = next(int(l.split()[2]) for l in lines if l.startswith("element vertex"))
        props = [l.split() for l in lines if l.startswith("property")]
        tmap = {"float": "<f4", "double": "<f8", "uchar": "u1", "int": "<i4", "uint": "<u4", "short": "<i2", "ushort": "<u2"}
        dt = np.dtype([(p[2], tmap[p[1]]) for p in props])
        return np.frombuffer(f.read(n * dt.itemsize), dtype=dt, count=n)


def srgb_to_lin(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = W, H, 100
scene.render.fps, scene.render.fps_base = 30, 1.0
scene.frame_start, scene.frame_end = 1, 60
scene.view_settings.view_transform = "Standard"
scene.render.film_transparent = False
world = bpy.data.worlds.new("black"); world.color = (0, 0, 0); scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg: bg.inputs[0].default_value = (0, 0, 0, 1)
try:
    scene.eevee.taa_render_samples = 16
except AttributeError:
    pass

cams = json.load(open(A.cams))
up = Vector(cams.get("auto_up") or [0, 0, 1]).normalized()
center = Vector(cams["points_median"])

# splat frame: PLY -> Blender world.  turn auto_up onto +Z, centre the scene, scale x2.
R = up.rotation_difference(Vector((0, 0, 1))).to_matrix().to_4x4()
S = Matrix.Scale(2.0, 4)
T = Matrix.Translation(Vector((0.5, -1.0, 0.25)))
splat_mat = T @ S @ R @ Matrix.Translation(-center)

# ---------------------------------------------------------------- proxy from the PLY
v = read_ply(A.ply)
xyz = np.stack([v["x"], v["y"], v["z"]], 1).astype(np.float32)
rgb = np.clip(0.5 + C0 * np.stack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]], 1), 0, 1)
alpha = 1 / (1 + np.exp(-v["opacity"].astype(np.float32)))
rad = np.exp(np.stack([v["scale_0"], v["scale_1"], v["scale_2"]], 1).astype(np.float32)).max(1)
keep = alpha > 0.35
idx = np.nonzero(keep)[0]
rng = np.random.default_rng(0)
if len(idx) > A.proxy_max:
    idx = np.sort(rng.choice(idx, A.proxy_max, replace=False))
xyz_k, rgb_k, rad_k = xyz[idx], rgb[idx], np.clip(rad[idx] * 1.2, 0.002, 0.08)
me = bpy.data.meshes.new("splat_proxy")
me.vertices.add(len(xyz_k)); me.vertices.foreach_set("co", xyz_k.ravel())
col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
col.data.foreach_set("color", np.concatenate([srgb_to_lin(rgb_k), np.ones((len(rgb_k), 1))], 1).astype(np.float32).ravel())
ra = me.attributes.new("prad", "FLOAT", "POINT"); ra.data.foreach_set("value", rad_k.astype(np.float32))
me.update()
ob = bpy.data.objects.new("splat_world", me)
scene.collection.objects.link(ob)
ob.matrix_world = splat_mat
ob["muse_splat"] = 1
ob["ply"] = A.ply

# geometry nodes: mesh -> points with per-point radius
ng = bpy.data.node_groups.new("splat_points", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput")
m2p = ng.nodes.new("GeometryNodeMeshToPoints")
rad_in = ng.nodes.new("GeometryNodeInputNamedAttribute"); rad_in.data_type = "FLOAT"; rad_in.inputs["Name"].default_value = "prad"
setm = ng.nodes.new("GeometryNodeSetMaterial")
ng.links.new(gi.outputs[0], m2p.inputs["Mesh"]); ng.links.new(rad_in.outputs["Attribute"], m2p.inputs["Radius"])
ng.links.new(m2p.outputs["Points"], setm.inputs["Geometry"]); ng.links.new(setm.outputs["Geometry"], go.inputs[0])
mat = bpy.data.materials.new("splat_emit"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "Col"
em = nt.nodes.new("ShaderNodeEmission"); outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(at.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs["Emission"], outn.inputs["Surface"])
setm.inputs["Material"].default_value = mat
mod = ob.modifiers.new("points", "NODES"); mod.node_group = ng

kiri_info = None
if A.kiri:
    try:
        import addon_utils
        addon_utils.enable("bl_ext.user_default.dgs_render_by_kiri_engine", default_set=True)
        before = set(bpy.data.objects)
        bpy.ops.sna.dgs_render_import_ply_e0a3a(filepath=A.ply)
        new = [o for o in bpy.data.objects if o not in before]
        k = [o for o in new if o.type == "MESH"][0]
        k.matrix_world = splat_mat
        ob.hide_render = True; ob.hide_viewport = True
        kiri_info = {"object": k.name, "splats": len(k.data.vertices), "modifiers": [m.name for m in k.modifiers]}
    except Exception as e:  # keep the proxy if KIRI fails headless
        kiri_info = {"error": repr(e)}

# ---------------------------------------------------------------- camera move from training camera 0
c0 = cams["cams"][0]
c2w0 = Matrix(c0["c2w"])                          # OpenCV, PLY frame
cam_bl0 = splat_mat @ c2w0 @ esc.FLIP              # Blender camera in world (may hold the x2 scale)
loc0, rot0, _ = cam_bl0.decompose()
cd = bpy.data.cameras.new("cam"); cd.sensor_fit = "AUTO"; cd.sensor_width = 36.0
cam = bpy.data.objects.new("cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.rotation_mode = "QUATERNION"
fwd = rot0 @ Vector((0, 0, -1)); right = rot0 @ Vector((1, 0, 0))
keys = [(1, 0.0, 0.0, 0.0, 30.0), (30, 1.4, 0.35, 8.0, 36.0), (60, 2.6, 0.9, 16.0, 42.0)]  # frame, dolly, truck, yaw deg, lens
for fr, dolly, truck, yaw, lens in keys:
    cam.location = loc0 + fwd * dolly + right * truck
    q = rot0.copy(); q.rotate(Matrix.Rotation(math.radians(-yaw), 4, Vector((0, 0, 1))).to_quaternion())
    roll = Matrix.Rotation(math.radians(yaw * 0.25), 4, "Z").to_quaternion()
    cam.rotation_quaternion = q @ roll
    cd.lens = lens
    cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_quaternion", frame=fr)
    cd.keyframe_insert("lens", frame=fr)

# ---------------------------------------------------------------- export (the bridge under test)
cam_json = os.path.join(A.out, "camera_frames.json")
res = esc.export(scene, splat="splat_world", out=cam_json)
tmpl = {"width": W, "height": H, "fps": 30, "bg": [0, 0, 0], "lens": {"samples": 1, "shutter": 0.0, "aperture": 0.0},
        "layers": [{"ply": A.vol_rel or A.ply, "xform": None, "effects": []}]}
json.dump(tmpl, open(os.path.join(A.out, "_tmpl.json"), "w"))
esc.export(scene, splat="splat_world", out=os.path.join(A.out, "shot_blender.json"), shot_template=os.path.join(A.out, "_tmpl.json"))
os.remove(os.path.join(A.out, "_tmpl.json"))

# ---------------------------------------------------------------- projection proof at --frame
scene.frame_set(A.frame)
i = A.frame - scene.frame_start
C = np.array(res["c2w"][i]).reshape(4, 4); fov = res["fov"][i]
fy = (H / 2) / math.tan(math.radians(fov) / 2)
w2c = np.linalg.inv(C)
sel = rng.choice(len(xyz_k), 4000, replace=False)
errs, used = [], 0
for j in sel:
    p = xyz_k[j].astype(np.float64)
    q = w2c @ np.array([*p, 1.0])
    if q[2] <= 0.05:
        continue
    u, vv = fy * q[0] / q[2] + W / 2, fy * q[1] / q[2] + H / 2
    if not (0 <= u < W and 0 <= vv < H):
        continue
    b = world_to_camera_view(scene, cam, splat_mat @ Vector(p))
    ub, vb = b.x * W, (1 - b.y) * H
    errs.append(math.hypot(u - ub, vv - vb)); used += 1
    if used >= 500:
        break
proof = {"frame": A.frame, "index_in_json": i, "t_sec": i / res["fps"], "c2w": res["c2w"][i], "fov_deg": fov,
         "points_compared": used, "max_px_err": max(errs), "mean_px_err": sum(errs) / len(errs),
         "lens_mm_at_frame": cd.lens, "proxy_points": int(len(xyz_k)), "splat_matrix_world": [list(r) for r in splat_mat],
         "kiri": kiri_info, "blender": bpy.app.version_string}

def kiri_to_camera(k_name):
    """Headless stand-in for KIRI's 'Align Active To View': write the scene camera's view and projection
    matrices into the KIRI_3DGS_Render_GN sockets (same socket order as align_active_to_view.py)."""
    k = bpy.data.objects[k_name]; gn = k.modifiers.get("KIRI_3DGS_Render_GN")
    dg = bpy.context.evaluated_depsgraph_get()
    view = cam.matrix_world.inverted()
    proj = cam.calc_matrix_camera(dg, x=W, y=H)
    s = 2
    for M in (view, proj):
        for col in range(4):
            for row in range(4):
                gn[f"Socket_{s}"] = M[row][col]; s += 1
    gn["Socket_34"], gn["Socket_35"] = W, H
    gn["Socket_50"] = 0      # update mode: 0 = Enable Camera Updates (1 = disabled, 2 = point cloud)
    gn["Socket_54"] = True   # Use Active Camera
    k.update_tag(refresh={"OBJECT"})


if kiri_info and "object" in kiri_info:
    kiri_to_camera(kiri_info["object"])

if not A.no_render:
    import time
    scene.render.filepath = os.path.join(A.out, f"blender_f{A.frame:03d}.png")
    t0 = time.time(); bpy.ops.render.render(write_still=True); proof["render_s"] = round(time.time() - t0, 2)
    proof["render_png"] = scene.render.filepath
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, "proof_scene.blend"))
json.dump(proof, open(os.path.join(A.out, "proof.json"), "w"), indent=1)
print("PROOF", json.dumps({k: proof[k] for k in ("frame", "fov_deg", "points_compared", "max_px_err", "mean_px_err", "kiri")}))
