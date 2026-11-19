"""Package the checked representative right root and ramus for standalone reuse."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from render_teaching import configure_scene, render_pair, sha256
from teaching_scene import bounds, colorize, export, load_meshes, material

SOURCE = HERE.parent / "nervous-senses.glb"
SOURCE_SHA = "9566e891615c5c428523f86c691f4e08efe170f02524fff853f5dae125267bdf"
MODEL = "right-root-ramus"
PARTS = {
    "Central | Representative dorsal root descending 2 side-1": (
        "Dorsal root and included ganglion", "right-dorsal-root", (0.10, 0.39, 0.34),
    ),
    "Central | Representative ventral root descending 2 side-1": (
        "Ventral root", "right-ventral-root", (0.56, 0.49, 0.39),
    ),
    "Central | Representative mixed nerve descending 2 side-1": (
        "Mixed spinal nerve", "right-mixed-spinal-nerve", (0.20, 0.15, 0.39),
    ),
    "Central | Ventral ramus and plexus bridge": (
        "Authored ventral ramus and plexus bridge", "right-ramus-plexus", (0.61, 0.33, 0.08),
    ),
}


def triangle_positions(obj):
    """Compare oriented triangle corners on a one-micrometre coordinate grid."""
    obj.data.calc_loop_triangles()
    corners = [tuple(round(value * 1e6) for value in obj.matrix_world @ v.co)
               for v in obj.data.vertices]
    triangles = Counter()
    for tri in obj.data.loop_triangles:
        a, b, c = (corners[i] for i in tri.vertices)
        triangles[min((a, b, c), (b, c, a), (c, a, b))] += 1
    return triangles


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    renders = output / "renders"
    renders.mkdir()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    originals = load_meshes(SOURCE, SOURCE_SHA, lambda name: name in PARTS)
    if {obj.name for obj in originals} != set(PARTS):
        raise ValueError("The exact four source root and ramus meshes are required")
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    lo, hi = bounds(originals)
    fixed_camera = {"front": (-0.26, 1, 0.28), "cameraBounds": [list(lo), list(hi)]}
    configure_scene(scene)
    before = render_pair(scene, originals, {**fixed_camera, "id": "original"}, renders)
    before["glb"] = {"file": SOURCE.name, "sha256": SOURCE_SHA}

    expected = {}
    for obj in originals:
        source_name = obj.name
        title, anatomy_id, rgb = PARTS[source_name]
        expected[title] = triangle_positions(obj)
        obj.name = title
        obj["anatomy_id"] = anatomy_id
        obj["source_node"] = source_name
        obj["source_sha256"] = SOURCE_SHA
        colorize(obj, material(title, rgb))
    bpy.data.objects.remove(scene.camera, do_unlink=True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                region = area.spaces.active.region_3d
                region.view_location = (lo + hi) / 2
                region.view_distance = max(hi - lo) * 2
                region.view_rotation = Vector(fixed_camera["front"]).to_track_quat("Z", "Y")
                region.view_perspective = "ORTHO"
                area.spaces.active.shading.color_type = "MATERIAL"
    export(output, MODEL)

    model = output / f"{MODEL}.glb"
    identity = sha256(model)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    updated = load_meshes(model, identity)
    if {obj.name: triangle_positions(obj) for obj in updated} != expected:
        raise ValueError("Clean import changed the named meshes or oriented triangle corners")
    for obj in updated:
        title, anatomy_id, _ = PARTS[obj["source_node"]]
        if (obj.name, obj["anatomy_id"], obj["source_sha256"]) != (title, anatomy_id, SOURCE_SHA):
            raise ValueError(f"Clean import changed part provenance for {obj.name}")
        if [mat.name for mat in obj.data.materials] != [title]:
            raise ValueError(f"Clean import lost the named material for {obj.name}")

    scene = bpy.context.scene
    configure_scene(scene)
    after = render_pair(scene, updated, {**fixed_camera, "id": "updated"}, renders)
    after["glb"] = {"file": model.name, "sha256": identity}
    if before["orthographicScale"] != after["orthographicScale"] or [
        image["camera"] for image in before["images"]
    ] != [image["camera"] for image in after["images"]]:
        raise ValueError("Root study camera changed")

    close_hi = hi.copy()
    close_hi.z = lo.z + (hi.z - lo.z) * 0.38
    junction = render_pair(scene, updated, {
        "id": "junction", "front": fixed_camera["front"],
        "cameraBounds": [list(lo), list(close_hi)],
    }, renders)
    junction["glb"] = after["glb"]
    (renders / "renders.json").write_text(json.dumps({
        "blender": bpy.app.version_string,
        "views": [before, after, junction],
        "modelBytes": model.stat().st_size,
        "triangleCounts": {title: triangles.total() for title, triangles in expected.items()},
        "geometryCheck": "Equal oriented world-space triangle corners on a one-micrometre grid",
        "frame": "Original illustrative nervous-senses assembly, Blender metres",
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    build(parser.parse_args(sys.argv[sys.argv.index("--") + 1:]).output)
