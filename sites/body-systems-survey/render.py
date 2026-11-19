"""Render paired orthographic screenshots of local GLBs in Blender."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SIZE = (600, 460)
PALETTE = {
    "bone": (0.72, 0.61, 0.44),
    "skin": (0.66, 0.41, 0.28),
    "muscle": (0.54, 0.20, 0.16),
    "organ": (0.55, 0.23, 0.18),
    "nerve": (0.72, 0.47, 0.16),
    "air": (0.19, 0.46, 0.48),
    "lung": (0.43, 0.61, 0.58),
    "artery": (0.52, 0.21, 0.13),
    "vein": (0.22, 0.36, 0.53),
    "gland": (0.65, 0.42, 0.21),
    "lymph": (0.30, 0.49, 0.30),
    "context": (0.42, 0.48, 0.51),
    "duct": (0.69, 0.51, 0.23),
}


def matte(slot, role):
    shade = PALETTE[role]
    opacity = 1.0
    base = slot.name.casefold() if slot else ""
    if base.startswith("illustrative_context_"):
        feature = base.removeprefix("illustrative_context_")
        if feature in {"bone", "rectum", "bladder"}:
            shade = PALETTE["context"]
            opacity = 0.23 if feature == "bone" else 0.38
        elif feature == "focus":
            shade = PALETTE["duct"]
    elif role == "muscle" and any(term in base for term in (
        "calcaneus", "tibia", "fibula", "talus", "humerus", "scapula",
    )):
        shade = PALETTE["bone"]
    elif base.startswith("urethra teaching"):
        shade = PALETTE["duct"]
    elif any(term in base for term in ("spongiosum", "cavernosum", "glans penis")):
        opacity = 0.52
    elif any(term in base for term in ("cartilage", "tendon", "meniscus", "fascia", "ivory", "nerve")):
        shade = PALETTE["bone"]
    elif any(term in base for term in ("artery", "arterial", "aortic")):
        shade = PALETTE["artery"]
    elif any(term in base for term in ("vein", "venous")):
        shade = PALETTE["vein"]
    elif any(term in base for term in ("duct", "ureter", "urethra", "wall_lumen")):
        shade = PALETTE["duct"]
    elif any(term in base for term in ("context", "reference", "guide")):
        shade = PALETTE["context"]
    mat_name = f"Survey {shade}, {opacity}"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(mat_name)
        mat.diffuse_color = (*shade, 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = (*shade, 1)
        shader.inputs["Roughness"].default_value = 0.74
        shader.inputs["Alpha"].default_value = opacity
    return mat


def object_role(obj, default):
    name = obj.name.casefold()
    families = {
        "duct": ("ureter to bladder", "urethral outlet"),
        "air": ("tracheal axis", "lobar bronchus", "bronchial branch"),
    }
    return next((role for role, words in families.items()
                 if any(word in name for word in words)), default)


def setup(engine):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = engine
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 3
    scene.render.resolution_x, scene.render.resolution_y = SIZE
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.world = bpy.data.worlds.new("Survey world")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.60, 0.64, 0.70, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.32
    if engine == "BLENDER_WORKBENCH":
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "MATERIAL"
        scene.display.shading.show_shadows = False
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "BOTH"
    else:
        scene.cycles.device = "CPU"
        scene.cycles.samples = 12
        scene.cycles.use_denoising = True
        scene.view_settings.view_transform = "AgX"
    return scene


def position_light(scene, center, extent, label, offset, energy, size):
    data = bpy.data.lights.new(label, "AREA")
    data.energy = energy * extent ** 2
    data.shape = "DISK"
    data.size = size * extent
    obj = bpy.data.objects.new(label, data)
    scene.collection.objects.link(obj)
    obj.location = center + Vector(offset) * extent
    obj.rotation_euler = (center - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(job, engine, output):
    scene = setup(engine)
    if engine == "CYCLES" and job["id"] in {"pelvis-f", "urethra-m", "penis"}:
        scene.cycles.samples = 48
    inputs = []
    objects = []
    for source in job["inputs"]:
        path = REPO / source["path"]
        with path.open("rb") as model:
            if model.read(4) != b"glTF":
                raise ValueError(f"Missing hydrated GLB bytes: {path}")
            model.seek(0)
            digest = hashlib.file_digest(model, "sha256").hexdigest()
        if digest != source["sha256"]:
            raise ValueError(f"Pinned GLB bytes differ: {path}")
        existing = set(scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(path))
        imported = [obj for obj in scene.objects if obj not in existing and obj.type == "MESH"]
        if not imported:
            raise ValueError(f"No imported meshes: {path}")
        for obj in imported:
            if source["surfaceOnly"] and obj.get("view_role") != "surface":
                obj.hide_render = True
                continue
            for index, mat in enumerate(obj.data.materials):
                obj.data.materials[index] = matte(mat, object_role(obj, source["role"]))
            if not obj.data.materials:
                obj.data.materials.append(matte(None, object_role(obj, source["role"])))
        objects.extend(obj for obj in imported if not obj.hide_render)
        inputs.append({**source, "meshes": len(imported)})
    scene.frame_set(1)
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    lo = Vector([min(point[i] for point in points) for i in range(3)])
    hi = Vector([max(point[i] for point in points) for i in range(3)])
    center = (lo + hi) / 2
    extent = max(hi - lo)
    if extent <= 0:
        raise ValueError(f"Degenerate scene: {job['id']}")
    if engine == "CYCLES":
        position_light(scene, center, extent, "Key", (-2, -3, 4), 540, 3)
        position_light(scene, center, extent, "Fill", (3, -2, 1), 240, 4)
        position_light(scene, center, extent, "Rim", (1, 3, 3), 350, 3)
    cam_data = bpy.data.cameras.new("Orthographic")
    cam = bpy.data.objects.new("Orthographic", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.type = "ORTHO"
    cam_data.clip_start = extent * 0.01
    cam_data.clip_end = extent * 24
    front = Vector(job.get("front", (0, -1, 0)))
    right = Vector((-front.y, front.x, 0))
    directions = [("iso", right + front + Vector((0, 0, 1))), ("ortho", front)]
    poses = []
    for label, direction in directions:
        rotation = (-direction).to_track_quat("-Z", "Y")
        inverse = rotation.inverted()
        projection = [inverse @ (point - center) for point in points]
        min_x, max_x = min(p.x for p in projection), max(p.x for p in projection)
        min_y, max_y = min(p.y for p in projection), max(p.y for p in projection)
        midpoint = rotation @ Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, 0))
        span = max(max_x - min_x, (max_y - min_y) * SIZE[0] / SIZE[1])
        poses.append((label, direction.normalized(), rotation, midpoint, span))
    cam_data.ortho_scale = max(pose[-1] for pose in poses) * 1.12
    for label, direction, rotation, midpoint, _ in poses:
        cam.location = center + direction * extent * 5 + midpoint
        cam.rotation_euler = rotation.to_euler()
        scene.render.filepath = str(output / f"{job['id']}-{label}.png")
        bpy.ops.render.render(write_still=True)
    return {
        "id": job["id"],
        "inputs": inputs,
        "nativeBounds": [list(lo), list(hi)],
        "orthographicScale": cam_data.ortho_scale,
        "straightViewDirection": list(front),
        "blender": bpy.app.version_string,
        "engine": engine,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="CYCLES")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--only")
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    jobs = json.loads((HERE / "jobs.json").read_text())
    selected = jobs[options.index::options.stride]
    if options.only:
        ids = set(options.only.split(","))
        selected = [job for job in jobs if job["id"] in ids]
        if len(selected) != len(ids):
            raise ValueError(f"Unknown job: {options.only}")
    options.output.mkdir(parents=True)
    for job in selected:
        receipt = render(job, options.engine, options.output.resolve())
        (options.output / f"{job['id']}.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
