"""Replay the retained breathing scene and verify its evaluated world geometry."""

import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets.blender_scene import evaluated_positions
from med_assets.glb_selection import identity


def make_breathing(source, output, selection):
    bpy.ops.wm.open_mainfile(filepath=str(source.resolve()), load_ui=False)
    scene = bpy.context.scene
    names = selection["retainedTriangles"]
    objects = {obj.name: obj for obj in scene.objects if obj.type == "MESH"}
    if not names.keys() <= objects.keys():
        raise ValueError("Expected all five lobes, diaphragm and liver in the source")
    keep = set()
    for name in names:
        obj = objects[name]
        while obj:
            keep.add(obj)
            obj = obj.parent
    for obj in list(scene.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.orphans_purge(do_recursive=True)
    scene.frame_set(selection["openingFrame"])
    scene["teaching_selection"] = "Five lung lobes, authored diaphragm and liver. Gross phase comparison."
    scene["control_sha256"] = selection["source"]["sha256"]
    bpy.ops.wm.save_as_mainfile(filepath=str(output.resolve()), compress=True, relative_remap=True)


def open_samples(path, selection, *, exact_inventory):
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()), load_ui=False)
    scene = bpy.context.scene
    start, end = selection["frames"]
    if (scene.frame_start, scene.frame_end) != (start, end):
        raise ValueError(f"Timeline changed in {path}")
    meshes = {obj.name: obj for obj in scene.objects if obj.type == "MESH"}
    expected = selection["retainedTriangles"]
    if exact_inventory and meshes.keys() != expected.keys():
        raise ValueError(f"Wrong retained mesh inventory in {path}")
    for name, count in expected.items():
        mesh = meshes[name].data
        mesh.calc_loop_triangles()
        if len(mesh.loop_triangles) != count:
            raise ValueError(f"Unexpected retained triangle count for {name} in {path}")
    fps = scene.render.fps / scene.render.fps_base
    dependencies = {Path(bpy.path.abspath(path)).resolve() for path in bpy.utils.blend_paths() if path}

    def samples():
        for frame in range(start, end + 1):
            scene.frame_set(frame)
            yield {name: np.asarray(evaluated_positions(meshes[name])) for name in expected}

    return fps, dependencies, samples()


def verify_motion(sources, selection):
    control, reviewed, rebuilt = sources
    fps, control_paths, source_frames = open_samples(control, selection, exact_inventory=False)
    before = list(source_frames)
    errors = {}
    for path in (reviewed, rebuilt):
        replay_fps, dependencies, frames = open_samples(path, selection, exact_inventory=True)
        if replay_fps != fps or not dependencies <= control_paths:
            raise ValueError(f"Sample rate or resolved file dependencies changed in {path}")
        drift = 0.
        for source, replay in zip(before, frames, strict=True):
            for name, source_vertices in source.items():
                target_vertices = replay[name]
                if source_vertices.shape != target_vertices.shape:
                    raise ValueError(f"Retained vertex count changed for {name}")
                drift = max(drift, float(np.linalg.norm(source_vertices - target_vertices, axis=1).max()) * 1000)
        if drift > selection["maximumWorldErrorMm"]:
            raise ValueError(f"Retained world-space geometry shifted by {drift:g} mm in {path}")
        errors[path.name if path == reviewed else "rebuild"] = drift
    return {"evaluatedFrames": len(before), "verifiedMeshes": len(selection["retainedTriangles"]),
            "fps": fps, "maxWorldErrorMm": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Fresh scratch output directory")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if bpy.app.build_hash.decode() != "fab76e95306d":
        parser.error("Use Blender 5.2.3 LTS Release Candidate fab76e95306d")
    selection = json.loads((HERE / "selection.json").read_text())
    source, reviewed = [ROOT / selection[key]["path"] for key in ("source", "reference")]
    for path, key in ((source, "source"), (reviewed, "reference")):
        if identity(path.read_bytes()) != {field: selection[key][field] for field in ("bytes", "sha256")}:
            raise ValueError(f"Wrong or unhydrated scene: {path}")
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output / reviewed.name
    make_breathing(source, output, selection)
    receipt = verify_motion((source, reviewed, output), selection)
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
