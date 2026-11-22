"""Render paired whole-model checks of the TAQ-005 exact exports."""

import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path.cwd()
INPUT = Path(sys.argv[sys.argv.index("--") + 1])
OUTPUT = Path(sys.argv[sys.argv.index("--") + 2])

# Most native GLBs are upright on Blender Z. Posterior is essential for
# adrenals, pulmonary vein, and parathyroid rather than an anterior default.
POSTERIOR = {"09", "18", "19", "22"}
NEUTRAL = (0.51, 0.43, 0.38)
SIZE = 640


def identity(path):
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def open_model(row):
    path = ROOT / row["path"]
    if identity(path) != {key: row[key] for key in ("sha256", "bytes")}:
        raise ValueError(f"Wrong bytes for {path}")
    if path.suffix == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        meshes = [o for o in bpy.context.view_layer.objects if o.type == "MESH" and o.visible_get()]
        for obj in scene.objects:
            obj.hide_render = obj not in meshes
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
        scene = bpy.context.scene
        meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    if not meshes:
        raise ValueError(f"No meshes in {path}")
    return scene, meshes


def configure(scene):
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = scene.render.resolution_y = SIZE
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.studiolight_rotate_z = 0.0
    shading.show_cavity = False
    shading.show_shadows = False
    shading.show_specular_highlight = True
    shading.background_type = "WORLD"
    scene.world = bpy.data.worlds.new("Review backdrop")
    scene.world.color = (0.035, .035, .035)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    camera = bpy.data.objects.new("TAQ review camera", bpy.data.cameras.new("TAQ review camera"))
    scene.collection.objects.link(camera)
    camera.data.type = "ORTHO"
    scene.camera = camera
    return camera


def frame_camera(camera, framed, direction):
    points = [obj.matrix_world @ Vector(point) for obj in framed for point in obj.bound_box]
    rotation = Vector(direction).to_track_quat("Z", "Y")
    projected = [rotation.inverted() @ point for point in points]
    lower = Vector([min(point[i] for point in projected) for i in range(3)])
    upper = Vector([max(point[i] for point in projected) for i in range(3)])
    span = max(upper - lower)
    camera.location = rotation @ ((lower + upper) / 2 + Vector((0, 0, 3 * span)))
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = rotation
    camera.data.clip_start = max(.00001, span * .0001)
    camera.data.clip_end = span * 12
    camera.data.ortho_scale = max((upper - lower)[:2]) * 1.13


def shot(scene, camera, meshes, direction, path, palette, visible=None, fixed=False):
    if not fixed:
        framed = visible if path.name == "01-heart-lung.png" else meshes
        frame_camera(camera, framed, direction)
    shown = meshes if visible is None else visible
    for obj in meshes:
        obj.hide_render = obj not in shown
    shading = scene.display.shading
    shading.color_type = "MATERIAL" if palette else "SINGLE"
    shading.single_color = NEUTRAL
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {
        "file": path.name,
        **identity(path),
        "direction": direction,
        "camera": list(camera.location),
        "orthoScale": camera.data.ortho_scale,
        "palette": palette,
        "visible": sorted(obj.name for obj in shown),
    }


def set_motion_sample(scene, row, index):
    if row["id"] != "06":
        return
    scene.frame_set(1 if index == 0 else 11)
    for obj in scene.objects:
        if obj.type == "MESH":
            obj.data.update()


def capture(row):
    scene, meshes = open_model(row)
    camera = configure(scene)
    stats = []
    for obj in meshes:
        obj.data.calc_loop_triangles()
        stats.append({
            "name": obj.name,
            "triangles": len(obj.data.loop_triangles),
            "materials": len(obj.material_slots),
        })
        for material in obj.data.materials:
            if material and material.node_tree:
                shader = next((node for node in material.node_tree.nodes
                               if node.type == "BSDF_PRINCIPLED"), None)
                if shader and not shader.inputs["Base Color"].is_linked:
                    material.diffuse_color = shader.inputs["Base Color"].default_value
    side = 1 if row["id"] in POSTERIOR else -1
    main = (.23, side, .12)
    reverse = (-.59, -side, .33)
    number = row["id"]
    set_motion_sample(scene, row, 0)
    views = [shot(scene, camera, meshes, main, OUTPUT / f"{number}-main.png", True)]
    motion = None
    if number == "06":
        set_motion_sample(scene, row, 1)
        motion = shot(scene, camera, meshes, main, OUTPUT / "06-frame11.png", True, fixed=True)
        set_motion_sample(scene, row, 0)
    views.append(shot(scene, camera, meshes, reverse, OUTPUT / f"{number}-reverse.png", False))
    if motion:
        views.append(motion)
    if row["id"] in {"12", "17"}:
        source = [obj for obj in meshes if obj.name.endswith("| source surface")]
        if len(source) != 1:
            raise ValueError(f"Expected one source surface in {row['path']}")
        section = [obj for obj in meshes if obj not in source]
        groups = (("all", meshes), ("source", source), ("section", section))
        for name, visible in groups:
            views.append(shot(scene, camera, meshes, main, OUTPUT / f"{row['id']}-{name}.png", False, visible))
    if row["id"] == "01":
        visible = [obj for obj in meshes if obj.name == "Heart | source surface" or "Lung " in obj.name]
        views.append(shot(scene, camera, meshes, main, OUTPUT / "01-heart-lung.png", False, visible))
    return {**row, "views": views, "objects": stats, "blendFrame": scene.frame_current}


def main():
    OUTPUT.mkdir(exist_ok=False, parents=True)
    report = {"blender": bpy.app.version_string, "build": bpy.app.build_hash.decode(), "rows": []}
    for entry in json.loads(INPUT.read_text())["rows"]:
        row = {key: entry[key] for key in ("id", "family", "path", "sha256", "bytes")}
        report["rows"].append(capture(row))
        (OUTPUT / "render.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
