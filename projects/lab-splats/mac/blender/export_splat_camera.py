"""export_splat_camera.py - Blender 5.2 -> Muse splat renderer camera bridge.

Writes the active scene camera's animation as the "frames" camera of a modal_splat.py shot:
  {"type":"frames", "fps":30.0, "c2w":[[16 floats], ...], "fov":[vfov deg, ...], "focus":[m, ...], ...}
c2w is camera-to-world, OpenCV convention (x right, y down, z forward), row-major 4x4, expressed in the
world frame of the PLY: the LOCAL frame of the splat object (`--splat <object>`), so the splat can sit in
Blender rotated / moved / uniformly scaled (e.g. turned Z-up) and the export still lands in PLY coordinates.
With no splat object the Blender world frame is used (the PLY must then sit at identity).

  c2w_ply = normalize_scale( splat.matrix_world^-1 @ camera.matrix_world ) @ diag(1, -1, -1, 1)

fov is the vertical field of view of the render (from Blender's own projection matrix, so sensor fit,
sensor size, lens / FOV units and the render aspect are all honoured). Lens shift, non-square pixels and
orthographic cameras are not representable in modal_splat.py and are refused (shift) or warned.

Run it three ways:
  1. CLI   : blender -b scene.blend --python export_splat_camera.py -- --out cam.json [--splat garden] [--camera Camera]
                                                                      [--start 1 --end 90 --step 1] [--shot shot_template.json]
  2. Editor: open in the Text Editor and Run Script (writes //splat_camera.json next to the .blend)
  3. Menu  : run once, then File > Export > Muse splat camera (.json)
With --shot, the template shot JSON is copied and its "camera" replaced, giving a ready render job.
"""
import json, math, os, sys

import bpy
from mathutils import Matrix

FLIP = Matrix(((1, 0, 0, 0), (0, -1, 0, 0), (0, 0, -1, 0), (0, 0, 0, 1)))  # Blender/OpenGL cam -> OpenCV cam


def find_splat(scene, name):
    if name:
        ob = bpy.data.objects.get(name)
        if ob is None:
            raise ValueError(f"splat object '{name}' not found")
        return ob
    for ob in scene.objects:  # tag convention: custom property muse_splat = 1 marks the PLY frame
        if ob.get("muse_splat"):
            return ob
    return None


def vertical_fov(scene, cam_ob, depsgraph):
    r = scene.render
    W = r.resolution_x * r.resolution_percentage / 100.0
    H = r.resolution_y * r.resolution_percentage / 100.0
    P = cam_ob.calc_matrix_camera(depsgraph, x=int(round(W)), y=int(round(H)), scale_x=r.pixel_aspect_x, scale_y=r.pixel_aspect_y)
    return math.degrees(2.0 * math.atan(1.0 / P[1][1])), P, (int(round(W)), int(round(H)))


def focus_distance(cam_ob, world_mat):
    dof = cam_ob.data.dof
    if not dof.use_dof:
        return None
    if dof.focus_object is not None:
        p = dof.focus_object.matrix_world.translation
        c = world_mat.translation
        fwd = -(world_mat.to_3x3().normalized().col[2])  # Blender camera looks down its local -Z
        return max((p - c).dot(fwd), 1e-4)
    return dof.focus_distance


def export(scene=None, camera=None, splat=None, start=None, end=None, step=1, out=None, shot_template=None):
    scene = scene or bpy.context.scene
    cam_ob = bpy.data.objects[camera] if camera else scene.camera
    if cam_ob is None or cam_ob.type != "CAMERA":
        raise ValueError("no camera: set the scene camera or pass --camera")
    if cam_ob.data.type != "PERSP":
        raise ValueError(f"camera type {cam_ob.data.type} is not supported (perspective only)")
    if abs(cam_ob.data.shift_x) > 1e-6 or abs(cam_ob.data.shift_y) > 1e-6:
        raise ValueError("lens shift is not supported by modal_splat.py (principal point is the centre); set shift to 0")
    sp = find_splat(scene, splat)
    r = scene.render
    warn = []
    if abs(r.pixel_aspect_x - r.pixel_aspect_y) > 1e-6:
        warn.append("non-square pixels: fov is exported for the vertical axis only")
    start = scene.frame_start if start is None else start
    end = scene.frame_end if end is None else end
    fps = r.fps / r.fps_base
    keep = scene.frame_current
    c2ws, fovs, focus, scales = [], [], [], []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for f in range(start, end + 1, step):
        scene.frame_set(f)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        cam_eval = cam_ob.evaluated_get(depsgraph)
        Mc = cam_eval.matrix_world.copy()
        M = Mc
        if sp is not None:
            M = sp.evaluated_get(depsgraph).matrix_world.inverted() @ Mc
        R = M.to_3x3()
        s = sum(R.col[i].length for i in range(3)) / 3.0  # remove (uniform) scale: camera scale or splat scale
        scales.append(s)
        Rn = R.normalized()
        A = Rn.to_4x4(); A.translation = M.translation
        C = A @ FLIP
        c2ws.append([C[i][j] for i in range(4) for j in range(4)])
        vf, P, (W, H) = vertical_fov(scene, cam_eval, depsgraph)
        fovs.append(vf)
        fd = focus_distance(cam_eval, Mc)
        if fd is not None:
            focus.append(fd / (sp.matrix_world.to_3x3().col[0].length if sp is not None else 1.0))
    scene.frame_set(keep)
    out_cam = {"type": "frames", "fps": fps, "c2w": c2ws, "fov": fovs}
    if focus:
        out_cam["focus"] = focus
    meta = {
        "convention": "OpenCV c2w (x right, y down, z forward), row-major 4x4, PLY frame; fov = vertical deg",
        "blender": bpy.app.version_string, "blend": bpy.data.filepath, "camera": cam_ob.name,
        "splat_object": sp.name if sp else None, "frames": [start, end, step], "render_size": [W, H],
        "lens_mm": cam_ob.data.lens, "sensor_fit": cam_ob.data.sensor_fit, "warnings": warn,
    }
    if sp is not None and max(scales) - min(scales) > 1e-5:
        meta["warnings"].append("splat or camera scale changes over the move")
    out_cam["_meta"] = meta
    result = out_cam
    if shot_template:
        shot = json.load(open(shot_template))
        shot["camera"] = out_cam
        shot["fps"] = fps
        shot["duration"] = len(c2ws) / fps
        shot.setdefault("width", W); shot.setdefault("height", H)
        result = shot
    if out:
        out = bpy.path.abspath(out)
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        with open(out, "w") as fh:
            json.dump(result, fh)
        print(f"[splat-camera] wrote {out}: {len(c2ws)} frames @ {fps:g} fps, splat frame = {sp.name if sp else 'world'}")
    return result


class MUSE_OT_export_splat_camera(bpy.types.Operator):
    bl_idname = "muse.export_splat_camera"
    bl_label = "Muse splat camera (.json)"
    bl_options = {"REGISTER"}
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="//splat_camera.json")
    splat: bpy.props.StringProperty(name="Splat object", default="")

    def invoke(self, context, event):
        sp = find_splat(context.scene, None)
        if sp:
            self.splat = sp.name
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            res = export(context.scene, splat=self.splat or None, out=self.filepath)
        except ValueError as e:
            self.report({"ERROR"}, str(e)); return {"CANCELLED"}
        self.report({"INFO"}, f"exported {len(res['c2w'])} frames")
        return {"FINISHED"}


def _menu(self, context):
    self.layout.operator(MUSE_OT_export_splat_camera.bl_idname, text="Muse splat camera (.json)")


def register():
    bpy.utils.register_class(MUSE_OT_export_splat_camera)
    bpy.types.TOPBAR_MT_file_export.append(_menu)


def _cli():
    import argparse
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="//splat_camera.json")
    ap.add_argument("--splat"); ap.add_argument("--camera")
    ap.add_argument("--start", type=int); ap.add_argument("--end", type=int); ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--shot", help="template shot JSON; output becomes a full shot")
    a = ap.parse_args(argv)
    export(splat=a.splat, camera=a.camera, start=a.start, end=a.end, step=a.step, out=a.out, shot_template=a.shot)


if __name__ == "__main__":
    if bpy.app.background:
        _cli()
    else:
        try:
            register()
        except ValueError:
            pass  # already registered
        export(out="//splat_camera.json")
