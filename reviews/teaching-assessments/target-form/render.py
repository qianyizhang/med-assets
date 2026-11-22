"""Clean-import matched views for the authored bronchial and HRA ovary trials."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VIEWS = HERE.parent / "2026-11-22-body-cardiovascular-digestive-endocrine" / "render.py"
OVARY = ROOT / "reviews/ovaries/2026-11-21-form-assessment-r01/views.json"
AIRWAY = HERE.parent / "refinement-form/trial-render.json"


def import_meshes(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()), merge_vertices=False)
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    meshes = {obj.name: obj for obj in scene.objects if obj.type == "MESH"}
    return scene, meshes


def packed(meshes):
    result = {}
    for name, obj in sorted(meshes.items()):
        mesh = obj.data
        mesh.calc_loop_triangles()
        positions = np.empty(len(mesh.vertices) * 3, np.float32)
        faces = np.empty(len(mesh.loop_triangles) * 3, np.int32)
        mesh.vertices.foreach_get("co", positions)
        mesh.loop_triangles.foreach_get("vertices", faces)
        result[name] = (positions.reshape(-1, 3), faces.reshape(-1, 3), obj.matrix_world.copy())
    return result


def overlaps(points, faces, changed):
    tree = BVHTree.FromPolygons(points.tolist(), faces.tolist(), all_triangles=True, epsilon=0)
    query = BVHTree.FromPolygons(points.tolist(), faces[changed].tolist(), all_triangles=True, epsilon=0)
    pairs = set()
    for a, b in query.overlap(tree):
        a = changed[a]
        if not np.isin(faces[a], faces[b]).any():
            pairs.add(tuple(sorted((int(a), b))))
    return pairs


def capture_airway(row, path, label, output):
    tools = runpy.run_path(str(VIEWS))
    scene, meshes = import_meshes(path)
    camera = tools["configure"](scene)
    scene.render.resolution_y = 544
    camera.data.clip_start = .001
    camera.data.clip_end = 5
    recorded = []
    for old in row:
        view = old["file"].replace("bronchial_tree-original-", "").removesuffix(".png")
        camera.location = old["camera"]
        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = Quaternion(old["rotation"])
        camera.data.ortho_scale = old["orthoScale"]
        frame = tools["shot"](scene, camera, list(meshes.values()), [0, 0, 0],
                              output / f"bronchial-{label}-{view}.png", False, fixed=True)
        recorded.append({key: value for key, value in frame.items() if key != "direction"}
                        | {"rotation": old["rotation"], "view": view})
    return packed(meshes), recorded


def mark_ovary_materials(scene, position, scale):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.cycles.seed = 17
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("Neutral world")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (.10, .10, .10, 1)
    background.inputs["Strength"].default_value = .65
    lights = []
    for name, offset, power, width in (
            ("Broad key", (-.62, -.70, .80), .70, .48),
            ("Fill", (.54, -.42, .12), .23, .50),
            ("Rim", (0, .53, .50), .31, .38)):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = power * (scale / .15) ** 2
        data.shape = "DISK"
        data.size = scale * width
        lamp = bpy.data.objects.new(name, data)
        scene.collection.objects.link(lamp)
        lamp.location = position + Vector(offset) * scale
        lamp.rotation_euler = (position - lamp.location).to_track_quat("-Z", "Y").to_euler()
        lights.append(lamp)
    return lights


def capture_ovary(rows, path, label, output):
    tools = runpy.run_path(str(VIEWS))
    scene, meshes = import_meshes(path)
    camera = bpy.data.objects.new("Matched evidence camera", bpy.data.cameras.new("Evidence"))
    camera.data.type = "ORTHO"
    camera.data.clip_start = .001
    camera.data.clip_end = 3
    scene.collection.objects.link(camera)
    scene.camera = camera
    recorded = []
    for row in rows:
        visible = set(row["visibleNodes"])
        if not visible.issubset(meshes):
            raise ValueError("A protected ovary or tubal node is missing")
        for name, obj in meshes.items():
            obj.hide_render = name not in visible
        direction = row["angle"]
        side = row["file"].split("-")[1]
        camera.location = row["cameraM"]
        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = Quaternion(row["cameraQuaternion"])
        camera.data.ortho_scale = scale = row["orthoScaleM"]
        lights = mark_ovary_materials(scene, Vector(row["targetM"]), scale)
        view = f"{side}-{direction}"
        path = output / f"ovary-{label}-{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        recorded.append({**row, **tools["identity"](path), "file": path.name, "view": view,
                         "material": "glTF material"})
        if direction == "alternate":
            for material in bpy.data.materials:
                shader = next((node for node in material.node_tree.nodes
                               if node.type == "BSDF_PRINCIPLED"), None) if material.node_tree else None
                if shader:
                    shader["priorBaseColor"] = list(shader.inputs["Base Color"].default_value)
                    shader.inputs["Base Color"].default_value = (.44, .39, .34, 1)
            neutral = output / f"ovary-{label}-{view}-neutral.png"
            scene.render.filepath = str(neutral)
            bpy.ops.render.render(write_still=True)
            recorded.append({**row, **tools["identity"](neutral), "file": neutral.name, "view": f"{view}-neutral",
                             "material": "neutral base color, respective GLB roughness"})
            for material in bpy.data.materials:
                if material.node_tree:
                    for shader in material.node_tree.nodes:
                        if "priorBaseColor" in shader:
                            shader.inputs["Base Color"].default_value = shader["priorBaseColor"]
                            del shader["priorBaseColor"]
        for lamp in lights:
            bpy.data.objects.remove(lamp, do_unlink=True)
    return packed(meshes), recorded


def compare(kind, base, edited, check_contacts):
    if base.keys() != edited.keys():
        raise ValueError("Clean import changed selectable part names")
    stats = {}
    for name, (a, faces, frame) in base.items():
        b, candidate_faces, candidate_frame = edited[name]
        if frame != candidate_frame or not np.array_equal(faces, candidate_faces):
            raise ValueError("Changed frame or triangle indices on reimport")
        moved = np.linalg.norm(b.astype(float) - a.astype(float), axis=1)
        if kind == "ovary" and np.any(moved):
            raise ValueError("Ovary material trial changed clean-import geometry")
        stats[name] = {"vertices": len(a), "triangles": len(faces),
                       "movedVertices": int(np.count_nonzero(moved)), "maxMovementMm": float(moved.max() * 1000)}
        if kind == "bronchial" and check_contacts:
            changed = np.flatnonzero((moved[faces] != 0).any(axis=1))
            before = overlaps(a, faces, changed)
            after = overlaps(b, faces, changed)
            stats[name]["nonadjacentContacts"] = {
                "before": len(before), "after": len(after), "new": len(after - before),
            }
            if after - before:
                raise ValueError(f"New nonadjacent triangle contacts in fairing support: {len(after - before)}")
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unused")
    parser.add_argument("output", type=Path)
    parser.add_argument("--bronchial", type=Path)
    parser.add_argument("--ovary", type=Path)
    parser.add_argument("--check-contacts", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if not (args.bronchial or args.ovary):
        parser.error("Select at least one trial")
    args.output.mkdir(parents=True, exist_ok=False)
    record = {"blender": bpy.app.version_string, "build": bpy.app.build_hash.decode(), "assets": {}}
    if args.bronchial:
        accepted = json.loads(AIRWAY.read_text())["assets"]["bronchial_tree"]["original"]
        control = ROOT / "models/bronchial_tree/exports/distal-sampling-r14/bronchial_distal_sampling.glb"
        before, original = capture_airway(accepted["views"], control, "original", args.output)
        after, updated = capture_airway(accepted["views"], args.bronchial, "updated", args.output)
        record["assets"]["bronchial"] = {"original": original, "updated": updated,
                                        "cleanImport": compare("bronchial", before, after, args.check_contacts)}
    if args.ovary:
        rows = [view for plate in json.loads(OVARY.read_text())["plates"]
                for view in plate["framesLeftToRight"]
                if (view["angle"], view["material"]) in (("native", "palette"), ("alternate", "neutral"))]
        control = ROOT / "models/ovaries/exports/hra-ovary-tubal-r01/ovary-tubal-context.glb"
        before, original = capture_ovary(rows, control, "original", args.output)
        after, updated = capture_ovary(rows, args.ovary, "updated", args.output)
        record["assets"]["ovary"] = {"original": original, "updated": updated,
                                    "cleanImport": compare("ovary", before, after, False)}
    identify = runpy.run_path(str(VIEWS))["identity"]
    for kind, path in (("bronchial", args.bronchial), ("ovary", args.ovary)):
        if path:
            record["assets"][kind]["candidate"] = identify(path)
    (args.output / "render.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
