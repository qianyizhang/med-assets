"""Audit two source selections, clean-import the full atlas, and render task matches."""

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ATLAS = ROOT / "heart/Cardiac_Atlas_Animated"
sys.path.insert(0, str(ATLAS / "recipes/shared-source-r01"))
from build import AORTA, CLIP, FULL, LV, MOTION, SOURCE, STATIC, build, decode, identity

STATIC_CONTROL = ROOT / "heart/Cardiac_Atlas/exports/teaching-economy-r01/Cardiac_Atlas_Clinical_Full_ED.glb"
STATIC_NATIVE = ROOT / "heart/Cardiac_Atlas/Cardiac_Atlas.blend"
STATIC_ORIGINAL = STATIC_CONTROL.parents[1] / "Cardiac_Atlas_Clinical_Full_ED.glb"
MOTION_CONTROL = ATLAS / "exports/wall-motion-r01/ventricular-wall-motion.glb"
FULL_CONTROL = ATLAS / "Heart_Clinical_Animated.glb"
CONTROL_HASHES = {
    STATIC_CONTROL: "342e445b8d460458d322a7e5db875d462867b1e7f99043c711bce73c34c9a813",
    STATIC_ORIGINAL: "32802a9a36963c2f8935f632f28ba3602d1ce004919e5e203ff87bbdcb52fa2f",
    MOTION_CONTROL: "a57fc0eec4cb8d26dfc50ff0db9360fea346a12096236b64f9d4492695c72905",
    FULL_CONTROL: "6912d439271c3525230a90fe403d586000e6a66ab37f82bf0419604181e52263",
}
VASCULAR = (AORTA, "Pulmonary trunk", "Left pulmonary artery", "Right pulmonary artery")
MOTION_NODES = (AORTA, LV)
FULL_TARGETS = (*VASCULAR, LV, "LA | complete wall", "Mitral valve | leaflet 1", "Aortic valve | leaflet 1")
TOLERANCE_MM = 0.002
EDIT_MM = 1.0


def vector_diff(left, right):
    return max((a - b).length for a, b in zip(left, right, strict=True)) * 1000


def symmetric_vertex_distance(left, right):
    """Compare clean-imported vertex clouds independent of UV splitting and vertex order."""
    def directed(points, target):
        tree = KDTree(len(target))
        for index, position in enumerate(target):
            tree.insert(position, index)
        tree.balance()
        return max(tree.find(position)[2] for position in points)

    return max(directed(left, right), directed(right, left)) * 1000


def native_records(path):
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=True)
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    records = {}
    for name in (*VASCULAR, LV, "LV | anterior section"):
        obj = scene.objects[name]
        mesh = obj.data
        points = [tuple(vertex.co) for vertex in mesh.vertices]
        keys = [(key.name, tuple(tuple(vertex.co) for vertex in key.data))
                for key in mesh.shape_keys.key_blocks] if mesh.shape_keys else []
        fingerprint_data = (points, keys, [tuple(row) for row in obj.matrix_world],
                            [tuple(poly.vertices) for poly in mesh.polygons],
                            [poly.material_index for poly in mesh.polygons])
        records[name] = {
            "vertices": len(points),
            "polygons": len(mesh.polygons),
            "sha256": hashlib.sha256(json.dumps(fingerprint_data).encode()).hexdigest(),
        }
    return records


def open_glb(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
    scene = bpy.context.scene
    objects = {obj.name: obj for obj in scene.objects if obj.type == "MESH"}
    for obj in objects.values():
        for slot in obj.material_slots:
            shader = slot.material.node_tree.nodes.get("Principled BSDF")
            slot.material.diffuse_color = shader.inputs["Base Color"].default_value
    return scene, objects


def coords(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]


def pose(scene, objects, names, seconds=0.0):
    sample = seconds * scene.render.fps / scene.render.fps_base
    frame = int(sample)
    scene.frame_set(frame, subframe=sample - frame)
    bpy.context.view_layer.update()
    return {name: coords(objects[name]) for name in names}


def cloud_errors(reference, candidate):
    return {name: symmetric_vertex_distance(reference[name], candidate[name]) for name in reference}


def ensure(error, threshold=TOLERANCE_MM):
    if max(error.values()) > threshold:
        raise ValueError(f"Expected world-space differences under {threshold} mm, got {error}")


def scalar(document, binary, index):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    if accessor["type"] != "SCALAR" or accessor["componentType"] != 5126:
        raise ValueError("Expected float scalar animation data")
    return np.frombuffer(binary, dtype="<f4", count=accessor["count"],
                         offset=view.get("byteOffset", 0) + accessor.get("byteOffset", 0))


def inventory(path):
    raw = path.read_bytes()
    if path in CONTROL_HASHES and hashlib.sha256(raw).hexdigest() != CONTROL_HASHES[path]:
        raise ValueError(f"Wrong comparison control {path}")
    document, binary = decode(raw)
    nodes = {node["name"] for node in document["nodes"] if "mesh" in node}
    result = {
        **identity(path),
        "triangles": sum(document["accessors"][p["indices"]]["count"] // 3
                         for mesh in document["meshes"] for p in mesh["primitives"]),
        "meshes": len(nodes),
        "primitives": sum(len(mesh["primitives"]) for mesh in document["meshes"]),
    }
    if any("uri" in binding for kind in ("buffers", "images") for binding in document.get(kind, [])):
        raise ValueError(f"Unexpected external resource in {path.name}")
    if document.get("animations"):
        (animation,) = document["animations"]
        if animation["name"] != CLIP:
            raise ValueError("Wrong cardiac clip identity")
        channels = {}
        for channel in animation["channels"]:
            target = channel["target"]
            sampler = animation["samplers"][channel["sampler"]]
            times, values = [scalar(document, binary, sampler[key]) for key in ("input", "output")]
            rows = values.reshape(len(times), -1)
            if (target["path"] != "weights" or sampler["interpolation"] != "LINEAR"
                    or not np.allclose(times, np.arange(25) / 30, rtol=0, atol=5e-8)
                    or not np.array_equal(rows[0], rows[-1])):
                raise ValueError(f"Unclosed or wrongly spaced cardiac channel in {path.name}")
            channels[document["nodes"][target["node"]]["name"]] = (times, rows)
        result["clipSeconds"] = 0.8
        result["clipChannels"] = len(channels)
        return result, nodes, channels
    return result, nodes, {}


def compare_channels(previous, current):
    if previous.keys() != current.keys():
        raise ValueError("The animated node inventories differ")
    if any(not np.array_equal(previous[name][0], current[name][0]) for name in previous):
        raise ValueError("The authored motion sample times changed")
    maximum = max(float(np.max(np.abs(previous[name][1] - current[name][1]))) for name in previous)
    if maximum > 1e-6:
        raise ValueError(f"Authored morph values changed by {maximum}")
    return maximum


def atlas_registration(full_path, static_path, motion_path):
    # Compare source neighborhoods at end diastole and independently imported motion,
    # including anterior/posterior vessels, a wall and both valve classes.
    scene, objects = open_glb(FULL_CONTROL)
    full_before_nodes = set(objects)
    originals = [pose(scene, objects, FULL_TARGETS, f / 30) for f in range(25)]
    scene, objects = open_glb(full_path)
    if set(objects) != full_before_nodes:
        raise ValueError("Complete imported selection changed")
    full_poses = [pose(scene, objects, FULL_TARGETS, f / 30) for f in range(25)]
    exact = {name: 0.0 for name in FULL_TARGETS}
    for before, after in zip(originals, full_poses, strict=True):
        for name, value in cloud_errors(before, after).items():
            exact[name] = max(exact[name], value)
    ensure(exact)
    movement = {name: max(vector_diff(full_poses[0][name], phase[name]) for phase in full_poses)
                for name in FULL_TARGETS}
    moved = set(FULL_TARGETS) - set(VASCULAR)
    if min(movement[name] for name in moved) < 0.1 or max(movement[name] for name in VASCULAR) > 1e-6:
        raise ValueError(f"Unexpected wall/valve motion or vessel drift: {movement}")
    scene, objects = open_glb(static_path)
    static_ed = pose(scene, objects, (*VASCULAR, LV))
    scene, objects = open_glb(motion_path)
    motion_ed = pose(scene, objects, MOTION_NODES)
    common = {"staticVersusFull": cloud_errors(static_ed, full_poses[0]),
              "motionVersusStatic": cloud_errors(motion_ed, static_ed)}
    for errors in common.values():
        ensure(errors)
    return {"fullVersusOriginalMm": exact, "fullMaxMovementMm": movement, "sharedEdPositionErrorMm": common}


def edit_replay(output, static_path, motion_path):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=True)
    for vertex in bpy.data.objects[AORTA].data.vertices:
        vertex.co.x += EDIT_MM / 25
    changed = output / "disposable-aorta-edit.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(changed))
    edited_folder = output / "edited"
    edited_folder.mkdir()
    build(changed, edited_folder, False)
    results = {}
    for original in (static_path, motion_path):
        scene, base = open_glb(original)
        names = sorted(base)
        phase = pose(scene, base, names, 0.4)
        scene, changed_parts = open_glb(edited_folder / original.name)
        if set(changed_parts) != set(names):
            raise ValueError("Disposable edit altered the teaching selection")
        edited = pose(scene, changed_parts, names, 0.4)
        aorta = phase.pop(AORTA)
        offset = Vector((EDIT_MM / 1000, 0.0, 0.0))
        predicted = [point + offset for point in aorta]
        shifted = symmetric_vertex_distance(predicted, edited[AORTA])
        unchanged = cloud_errors(phase, edited)
        ensure({"aortaEditResidual": shifted, **unchanged})
        results[original.name] = {
            "axis": "Blender +X, patient left", "sourceTranslationMm": EDIT_MM,
            "expectedAortaWorldPositionResidualMm": shifted,
            "unchangedMeshes": len(unchanged), "maxUnchangedMeshWorldPositionErrorMm": max(unchanged.values()),
            "editedBytes": identity(edited_folder / original.name),
        }
    return results


def render_binding(camera, target):
    return {
        "position": list(camera.location),
        "target": list(target),
        "rotation": list(camera.rotation_quaternion),
        "near": camera.data.clip_start,
        "far": camera.data.clip_end,
        "height": camera.data.ortho_scale,
    }


def apply_binding(camera, binding):
    camera.location = binding["position"]
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = binding["rotation"]
    camera.data.clip_start = binding["near"]
    camera.data.clip_end = binding["far"]
    camera.data.ortho_scale = binding["height"]


def render(helper, output, task, before, after):
    records = {}
    bindings = {}
    motion = task == "motion"
    for revision, path in (("original", before), ("updated", after)):
        scene, objects = open_glb(path)
        camera = helper["configure"](scene)
        if motion:
            views = (
                ("rest", (.216, .201, .045), 0.0, tuple(objects), tuple(objects), True),
                ("peak", (.216, .201, .045), 1 / 3, tuple(objects), tuple(objects), True),
                ("reverse", (-.48, -.80, .21), 1 / 3, tuple(objects), tuple(objects), False),
            )
        else:
            views = (
                ("overview", (.42, -1, .1), 0.0, tuple(objects), tuple(objects), True),
                ("detail", (.2, -1, .24), 0.0, VASCULAR, VASCULAR, True),
                ("reverse", (-.59, .7, .33), 0.0, VASCULAR, VASCULAR, False),
            )
        records[revision] = []
        for label, direction, seconds, shown, framed, palette in views:
            pose(scene, objects, (), seconds)
            if label not in bindings:
                # Frame the matched motion views at the same reference phase.
                if motion and label in ("rest", "peak"):
                    target = Vector((.0222792, .00593888, .0131365))
                    camera.location = target + Vector(direction)
                    camera.rotation_mode = "QUATERNION"
                    camera.rotation_quaternion = Vector(direction).to_track_quat("Z", "Y")
                    camera.data.ortho_scale = .1580501
                    camera.data.clip_start, camera.data.clip_end = .00001, 8
                else:
                    helper["frame_camera"](camera, [objects[name] for name in framed], direction)
                    target = camera.location - Vector(direction).normalized() * (camera.data.clip_end / 4)
                bindings[label] = render_binding(camera, target)
            apply_binding(camera, bindings[label])
            receipt = helper["shot"](
                scene, camera, list(objects.values()), direction, output / f"{task}-{revision}-{label}.png",
                palette, [objects[name] for name in shown], fixed=True,
            )
            receipt["timeSeconds"] = seconds
            receipt["targetM"] = bindings[label]["target"]
            records[revision].append(receipt)
    return {"cameraBindingBlender": bindings, "views": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_folder", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    output = args.output.resolve()
    output.mkdir(parents=True)
    static_path = args.build_folder / STATIC
    motion_path = args.build_folder / MOTION
    full_path = args.build_folder / FULL
    inputs = {name: inventory(path) for name, path in {
        "staticControl": STATIC_CONTROL, "staticOriginal": STATIC_ORIGINAL, "staticCandidate": static_path,
        "motionControl": MOTION_CONTROL, "motionCandidate": motion_path,
        "fullControl": FULL_CONTROL, "fullCandidate": full_path,
    }.items()}
    if inputs["staticControl"][1] != inputs["staticCandidate"][1] or set(MOTION_NODES) != inputs["motionCandidate"][1]:
        raise ValueError("Task selection inventory changed")
    if inputs["staticCandidate"][2] or inputs["motionCandidate"][2].keys() != {LV}:
        raise ValueError("Wrong task animation inventory")
    native = native_records(SOURCE)
    if native != native_records(STATIC_NATIVE):
        raise ValueError("Native cardiac sources disagree on protected registration")
    report = {
        "blender": bpy.app.version_string, "build": bpy.app.build_hash.decode(),
        "nativeImports": {"historical": identity(STATIC_NATIVE), "shared": identity(SOURCE), "identicalTargets": native},
        "exports": {name: data[0] for name, data in inputs.items()},
        "toleranceMm": TOLERANCE_MM,
        "animationMaxWeightDifference": {
            "focused": compare_channels(inputs["motionControl"][2], inputs["motionCandidate"][2]),
            "full": compare_channels(inputs["fullControl"][2], inputs["fullCandidate"][2]),
        },
    }

    scene, objects = open_glb(STATIC_CONTROL)
    great_vessels_before = pose(scene, objects, VASCULAR)
    scene, objects = open_glb(static_path)
    report["staticProtectedVertexErrorMm"] = cloud_errors(great_vessels_before, pose(scene, objects, VASCULAR))
    ensure(report["staticProtectedVertexErrorMm"])
    scene, objects = open_glb(STATIC_ORIGINAL)
    static_context_names = sorted(objects)
    original_context = pose(scene, objects, static_context_names)
    scene, objects = open_glb(static_path)
    report["staticOriginalAllMeshMaxVertexErrorMm"] = max(
        cloud_errors(original_context, pose(scene, objects, static_context_names)).values())
    ensure({"unreducedStaticContext": report["staticOriginalAllMeshMaxVertexErrorMm"]})
    report["fullModelCleanReimport"] = atlas_registration(full_path, static_path, motion_path)

    scene, objects = open_glb(MOTION_CONTROL)
    prior_poses = [pose(scene, objects, MOTION_NODES, frame / 30) for frame in range(25)]
    scene, objects = open_glb(motion_path)
    updated_poses = [pose(scene, objects, MOTION_NODES, frame / 30) for frame in range(25)]
    motion_errors = [cloud_errors(a, b) for a, b in zip(prior_poses, updated_poses, strict=True)]
    report["focusedMotionMaxWorldVertexErrorMm"] = {name: max(row[name] for row in motion_errors) for name in MOTION_NODES}
    ensure(report["focusedMotionMaxWorldVertexErrorMm"])
    motion_peak = {name: max(vector_diff(updated_poses[0][name], p[name]) for p in updated_poses)
                   for name in MOTION_NODES}
    if motion_peak[AORTA] != 0 or motion_peak[LV] < 0.1:
        raise ValueError(f"Unexpected focused range of motion: {motion_peak}")
    report["focusedMaxWorldMotionMm"] = motion_peak
    report["disposableSourceEdit"] = edit_replay(output, static_path, motion_path)
    (output / "checks.json").write_text(json.dumps(report, indent=2) + "\n")

    renderer = runpy.run_path(str(HERE.parent / "2026-11-22-body-cardiovascular-digestive-endocrine/render.py"))
    report["render"] = {
        "static": render(renderer, output, "static", STATIC_CONTROL, static_path),
        "motion": render(renderer, output, "motion", MOTION_CONTROL, motion_path),
    }
    (output / "checks.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
