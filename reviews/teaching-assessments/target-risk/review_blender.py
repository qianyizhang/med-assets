"""Verify exact retained exports, build protected mesh trials, and capture matched task views."""

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.glb import decode

CONTROL = {
    "breath": ("body/breathing/Breathing_Assembly.blend", "fc68b49ca75d02d50330e9d5b5d5182843e6d0e7ca4d43d665cbde48ac23b841"),
    "heart": ("heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb", "6912d439271c3525230a90fe403d586000e6a66ab37f82bf0419604181e52263"),
    "bladder": ("models/bladder/exports/hra-female-context-r03/bladder_hra_female_context_r03.glb", "91f04d1c831a61944da116184f389461517587c90c91fd94e199fba1619aa6b9"),
    "parathyroid": ("models/parathyroids/exports/z-localization-r01/parathyroids_native.glb", "b6fbbabfa7efd12b8c377f5bc56193bd81776daab999a8c1ac8286f693b85b45"),
    "lymph": ("models/lymph_node/exports/hra-tissue-layers-r01/lymph-node-tissue-layers.glb", "bf4ffa85c96459f2666949196915244697f3f5e33ebf485482c8223ba1fcb23e"),
    "stomach": ("models/stomach/exports/metadata-cleanup-r01/stomach.glb", "ad0876f37f92945171750d31d9c53165535a697e60a3d2ac8a3f3f78667fdec6"),
    "gallbladder": ("models/gallbladder/exports/metadata-cleanup-r01/gallbladder.glb", "faa06e38130b3f63cc0094914eeb9adfb874ba2a2dc78da49e1c255c1f740227"),
}
CANDIDATE = {
    "heart": "heart/Cardiac_Atlas_Animated/exports/wall-motion-r01/ventricular-wall-motion.glb",
    "bladder": "models/bladder/exports/pelvic-base-r01/bladder-pelvic-base.glb",
    "parathyroid": "models/parathyroids/exports/z-localization-r01/parathyroids_thyroid_context.glb",
}
NEUTRAL = (.58, .58, .57, 1)
TARGET = (.86, .57, .30, 1)
DOME = "Authored schematic diaphragm"
LIVER = "Liver | source surface"
LV = "LV | complete wall"
AORTA = "Aorta | root, ascending, arch and descending"


def identity(path):
    return {"path": path.as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}


def receipt(folder, record):
    (folder / "receipt.json").write_text(json.dumps(record, indent=2) + "\n")


def check_source(family):
    path, digest = CONTROL[family]
    asset = identity(Path(path))
    if asset["sha256"] != digest:
        raise ValueError(f"Wrong source for {family}")
    return asset


def poses(scene, meshes, names, frames, positions):
    samples = {}
    for frame in frames:
        scene.frame_set(frame)
        samples[frame] = {name: positions(meshes[name]) for name in names}
    return samples


def exact_poses(control, candidate):
    errors = {}
    for frame, previous in control.items():
        errors[frame] = {name: max((a - b).length for a, b in zip(vertices, candidate[frame][name], strict=True)) * 1000
                         for name, vertices in previous.items()}
    if any(distance > .0001 for frame in errors.values() for distance in frame.values()):
        raise ValueError("Retained world-space geometry shifted more than 0.0001 mm")
    return errors


def mesh_inventory(meshes):
    sizes = {}
    for name, mesh in meshes.items():
        mesh.data.calc_loop_triangles()
        sizes[name] = len(mesh.data.loop_triangles)
    return sizes


def make_breathing(source, output):
    bpy.ops.wm.open_mainfile(filepath=str(Path(source["path"]).resolve()), load_ui=False)
    scene = bpy.context.scene
    selected = {o for o in scene.objects if o.type == "MESH" and
                (o.name.startswith("Lung ") or o.name in (DOME, LIVER))}
    if len(selected) != 7:
        raise ValueError("Expected exact five lobes, diaphragm and liver")
    keep = set(selected)
    for obj in selected:
        parent = obj.parent
        while parent:
            keep.add(parent)
            parent = parent.parent
    for obj in list(scene.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.orphans_purge(do_recursive=True)
    scene.frame_set(1)
    scene["teaching_selection"] = "Five lung lobes, authored diaphragm and liver. Gross phase comparison."
    scene["control_sha256"] = source["sha256"]
    bpy.ops.wm.save_as_mainfile(filepath=str(output.resolve()), compress=True)
    return identity(output)


def capture(helper, scene, camera, meshes, frame, label, shown, binding):
    scene.frame_set(frame)
    for name, mesh in meshes.items():
        if name not in shown:
            continue
        if name == LV or name == DOME:
            mesh.color = TARGET
        elif name == AORTA or name == LIVER:
            mesh.color = (.49, .37, .31, 1)
        elif name.startswith("Lung "):
            mesh.color = (.64, .67, .69, 1)
    target, direction, scale = binding
    return helper["take"](scene, camera, meshes, label, shown, target, direction, scale)


def motion(helper, folder, family):
    control = check_source(family)
    candidate = make_breathing(control, folder / "breathing-dome.blend") if family == "breath" else identity(Path(CANDIDATE[family]))
    scene, camera, meshes = helper["opening"](control)
    previous_sizes = mesh_inventory(meshes)
    scene_range = scene.frame_start, scene.frame_end
    fps = scene.render.fps / scene.render.fps_base
    if family == "breath":
        names = sorted(n for n in meshes if n.startswith("Lung ") or n in (DOME, LIVER))
        anchors = (1, 49, 121)
        pinned = json.loads((HERE.parent / "2026-11-22-respiratory/motion-compare.json").read_text())
        view = next(v for v in pinned["views"] if v["file"] == "motion-1-detail-side-palette.png")
        target = Vector(view["targetM"])
        binding = (target, Vector(view["cameraM"]) - target, view["orthoScaleM"])
        visibility = {"phase": names, "isolated": [DOME]}
    else:
        names = [LV, AORTA]
        frames = range(round(.8 * fps) + 1)
        reference = poses(scene, meshes, names, frames, helper["evaluated_positions"])
        displacement = {f: {name: max((a - b).length for a, b in zip(reference[0][name], values, strict=True)) * 1000
                            for name, values in vectors.items()} for f, vectors in reference.items()}
        peak = max(displacement, key=lambda f: displacement[f][LV])
        anchors = (0, peak, frames[-1])
        direction = (.72, .67, .15)
        target, scale = helper["frame_points"]([v for points in reference[0].values() for v in points], direction)
        binding = (target, direction, scale)
        visibility = {"phase": names}
    frames = range(1, 122) if family == "breath" else frames
    control_poses = poses(scene, meshes, names, frames, helper["evaluated_positions"])
    views = []
    for frame in anchors[:2]:
        for label, shown in visibility.items():
            views.append(capture(helper, scene, camera, meshes, frame, f"control-{frame}-{label}", shown, binding))
    scene, camera, meshes = helper["opening"](candidate)
    if set(meshes) != set(names):
        raise ValueError("Wrong retained motion inventory")
    if (scene.frame_start, scene.frame_end) != scene_range and family == "breath":
        raise ValueError("Respiratory timeline changed")
    if scene.render.fps / scene.render.fps_base != fps:
        raise ValueError("Sample rate changed")
    after_sizes = mesh_inventory(meshes)
    if any(previous_sizes[n] != after_sizes[n] for n in meshes):
        raise ValueError("Retained triangle count drift")
    candidate_poses = poses(scene, meshes, names, frames, helper["evaluated_positions"])
    errors = exact_poses(control_poses, candidate_poses)
    for frame in anchors[:2]:
        for label, shown in visibility.items():
            views.append(capture(helper, scene, camera, meshes, frame, f"candidate-{frame}-{label}", shown, binding))
    report = {"control": control, "candidate": candidate, "controlTriangles": sum(previous_sizes.values()),
              "candidateTriangles": sum(after_sizes.values()), "retainedTriangles": after_sizes,
              "fps": fps, "samples": len(frames), "comparedFrames": anchors,
              "maxCandidateVsControlMm": max(d for frame in errors.values() for d in frame.values()),
              "views": views}
    if family == "heart":
        report["peakDisplacementMm"] = displacement[peak]
    else:
        def frame_height(frame, name, bound):
            return bound(p.z for p in control_poses[frame][name]) * 1000
        report["superiorDomeDescentMm"] = frame_height(1, DOME, max) - frame_height(49, DOME, max)
        report["inferiorLeftLowerLobeDescentMm"] = (frame_height(1, "Lung Lower Lobe Left | source surface", min)
                                                   - frame_height(49, "Lung Lower Lobe Left | source surface", min))
        report["inferiorLiverDescentMm"] = frame_height(1, LIVER, min) - frame_height(49, LIVER, min)
    receipt(folder, report)


def parathyroid(helper, folder):
    control = check_source("parathyroid")
    candidate = identity(Path(CANDIDATE["parathyroid"]))
    record = json.loads((ROOT / "reviews/parathyroids/2026-10-25-localization-r01/record.json").read_text())
    if candidate["sha256"] != record["context_glb_sha256"]:
        raise ValueError("Companion differs from the exact source selection")
    views, positions, bindings, centroids = [], {}, {}, {}
    for side, asset in (("candidate", candidate), ("control", control)):
        scene, camera, meshes = helper["opening"](asset)
        points = {n: helper["evaluated_positions"](o) for n, o in meshes.items()}
        for name, mesh in meshes.items():
            mesh.color = TARGET if "parathyroid" in name.lower() else NEUTRAL
        if side == "candidate":
            positions = {n: cloud for n, cloud in points.items() if "parathyroid" in n.lower()}
            for label, direction in (("posterior", (0, 1, 0)), ("patient-right", (-.98, .21, .08)),
                                     ("patient-left", (.98, .21, .08))):
                target, scale = helper["frame_points"]([p for part in points.values() for p in part], direction)
                bindings[label] = (target, direction, scale)
            for n, part in points.items():
                center = sum(part, Vector()) / len(part)
                centroids[n] = [round(v * 1000, 5) for v in center]
        else:
            errors = exact_poses({0: positions}, {0: points})
        for label, binding in bindings.items():
            views.append(capture(helper, scene, camera, meshes, 1, f"{side}-{label}", set(meshes), binding))
            bpy.context.view_layer.update()
            views[-1]["targetProjection"] = {
                n: list(world_to_camera_view(scene, camera, sum(cloud, Vector()) / len(cloud)))[:2]
                for n, cloud in points.items() if "parathyroid" in n.lower()
            }
    receipt(folder, {"control": control, "candidate": candidate, "centroidsMmBlender": centroids,
                     "maxGlandVertexDriftMm": max(errors[0].values()), "views": views})


def bladder(helper, folder):
    control = check_source("bladder")
    candidate = identity(Path(CANDIDATE["bladder"]))
    retained = json.loads((HERE / "selections.json").read_text())["bladder"]["retain"]
    focus = {n for n in retained if any(word in n for word in ("_base", "_neck", "trigone", "orifice"))}
    context = set(retained)
    no_dome = {n for n in retained if "_dome" not in n}
    views, reference, bindings = [], {}, {}
    for side, asset in (("control", control), ("candidate", candidate)):
        scene, camera, meshes = helper["opening"](asset)
        points = {n: helper["evaluated_positions"](meshes[n]) for n in retained}
        if side == "control":
            reference = points
            for label, direction in (("rear", (0, 1, .85)), ("reverse", (.4, -1, .85))):
                target, scale = helper["frame_points"]([p for n in focus for p in points[n]], direction)
                bindings[label] = (target, direction, scale * 1.18)
        else:
            errors = exact_poses({0: reference}, {0: points})
            if set(meshes) != context:
                raise ValueError("Unexpected selectable objects in bladder edition")
        for n, item in meshes.items():
            item.color = TARGET if "orifice" in n else (.78, .56, .55, 1) if n in focus else NEUTRAL
        for label, binding in bindings.items():
            for mode, names in (("context", set(meshes)), ("base", focus), ("ureters", no_dome)):
                views.append(capture(helper, scene, camera, meshes, 1, f"{side}-{label}-{mode}", names, binding))
    receipt(folder, {"control": control, "candidate": candidate,
                     "maxVertexDriftMm": max(errors[0].values()), "views": views})


def digestive(helper, folder, family, candidate=None):
    control = check_source(family)
    scene, _, meshes = helper["opening"](control)
    source_name = next(n for n in meshes if n.endswith("| source surface"))
    section = set(meshes) - {source_name}
    modes = {"all": set(meshes), "exterior": {source_name}, "section": section}
    bindings = {}
    for label, direction in (("front", (.23, -1, .12)), ("oblique", (-.65, -1, .36))):
        target, scale = helper["frame_points"](
            [p for item in meshes.values() for p in helper["evaluated_positions"](item)], direction)
        bindings[label] = (target, direction, scale)
    views = []
    for side, asset in (("control", control), *([("candidate", candidate)] if candidate else [])):
        scene, camera, meshes = helper["opening"](asset)
        for n, mesh in meshes.items():
            mesh.color = NEUTRAL if n == source_name or "section" in n else TARGET
        for label, binding in bindings.items():
            for mode, names in modes.items():
                if mode == "all" and (label != "front" or side != "control"):
                    continue
                views.append(capture(helper, scene, camera, meshes, 1, f"{side}-{label}-{mode}", names, binding))
    receipt(folder, {"control": control, "candidate": candidate, "views": views})


def lock_duplicate_faces(simplify, oriented):
    def contract(positions, triangles, locked, max_edge, ratio):
        # The source has 37 double-sided face pairs. BMesh cannot represent
        # coincident faces with the same indices. Preserve those stars and restore
        # the removed copies before checking the complete attributed stream.
        _, first, inverse, counts = np.unique(
            np.sort(triangles, axis=1), axis=0, return_index=True, return_inverse=True, return_counts=True)
        duplicates = counts[inverse] > 1
        is_first = np.zeros(len(triangles), dtype=bool)
        is_first[first] = True
        locked = locked.copy()
        duplicate_vertices = np.unique(triangles[duplicates])
        touching = np.isin(triangles, duplicate_vertices).any(axis=1)
        locked[triangles[touching].ravel()] = True
        edited = simplify(positions, triangles[is_first], locked, max_edge, ratio)
        return oriented(np.concatenate((edited, triangles[~is_first])))
    return contract


def simplify(family, folder, fine=False):
    trial = runpy.run_path(str(HERE.parent / "refinement-economy/trial.py"))
    control = check_source(family)
    raw = Path(control["path"]).read_bytes()
    doc, binary = decode(raw)
    if family == "stomach":
        # The source exterior, section backing, and smallest two folds are kept as anchors.
        rules = [{"match": r"Gastric mucosal fold (?:[3-9]|1[01])\.001 #",
                  "ratio": .48, "edgePx": 25, "minTriangles": 3000, "featureZoom": 2, "maxPx": .8}]
        span = .128
    else:
        rules = [{"match": "medulla", "ratio": .74 if fine else .46, "edgePx": 4 if fine else 22,
                  "minTriangles": 10000, "featureZoom": 2, "maxPx": .8}]
        span = .021
    row = {"rules": rules}
    if family == "lymph":
        operations = trial["geometry_replacements"].__globals__
        operations["simplify"] = lock_duplicate_faces(operations["simplify"], trial["SKIN"]["oriented"])
    replacements, rebindings, sparse, parts, before, after = trial["geometry_replacements"](row, doc, binary, span)
    candidate = None
    if replacements:
        data = trial["replace_accessors"](doc, binary, replacements, rebindings, sparse)
        trial["verify_streams"](raw, data, replacements, rebindings)
        output = folder / "candidate.glb"
        output.write_bytes(data)
        candidate = identity(output)
        _, _, before_scene = trial["scene_import"](Path(control["path"]))
        _, _, after_scene = trial["scene_import"](output)
        if before_scene.keys() != after_scene.keys() or any(
                {k: v for k, v in props.items() if k != "triangles"} !=
                {k: v for k, v in after_scene[n].items() if k != "triangles"} for n, props in before_scene.items()):
            raise ValueError("Selectability, frame, material or shape key changed")
    (folder / "mesh-trial.json").write_text(json.dumps(
        {"control": control, "candidate": candidate, "parts": parts,
         "controlTriangles": before, "candidateTriangles": after, "rules": rules}, indent=2) + "\n")
    return candidate


def lymph(helper, folder, candidate):
    control = check_source("lymph")
    scene, camera, meshes = helper["opening"](control)
    capsule = next(n for n in meshes if "capsule" in n)
    medulla = next(n for n in meshes if "medulla" in n)
    directions = {"front": (.25, -.9, .2), "oblique": (-.62, -.55, -.41)}
    bindings = {}
    for label, direction in directions.items():
        target, scale = helper["frame_points"](helper["evaluated_positions"](meshes[capsule]), direction)
        bindings[label] = (target, direction, scale)
    views = []
    for side, asset in (("control", control), *([("candidate", candidate)] if candidate else [])):
        scene, camera, meshes = helper["opening"](asset)
        for label, binding in bindings.items():
            for mode, visible in (("interior", set(meshes) - {capsule}), ("medulla", {medulla}), ("capsule", {capsule})):
                for name, mesh in meshes.items():
                    mesh.color = NEUTRAL if mode != "interior" else helper["COLORS"].get(name, NEUTRAL)
                views.append(capture(helper, scene, camera, meshes, 1, f"{side}-{label}-{mode}", visible, binding))
    receipt(folder, {"control": control, "candidate": candidate, "views": views})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", choices=CONTROL)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fine", action="store_true", help="Try shorter medulla edge contractions")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    folder = args.output
    folder.mkdir()
    helper = runpy.run_path(str(HERE.parent / "refinement-risk/render.py"))
    helper["take"].__globals__["OUTPUT"] = folder
    helper["opening"].__globals__["SIZE"] = 640
    family = args.family
    if family in ("heart", "breath"):
        motion(helper, folder, family)
    elif family == "parathyroid":
        parathyroid(helper, folder)
    elif family == "bladder":
        bladder(helper, folder)
    elif family in ("lymph", "stomach"):
        candidate = simplify(family, folder, args.fine)
        (lymph if family == "lymph" else digestive)(helper, folder, *(
            [candidate] if family == "lymph" else [family, candidate]))
    else:
        digestive(helper, folder, family)


if __name__ == "__main__":
    main()
