"""Render endocrine atlas and s1233 groups from their separate clean imports."""

import argparse
import json
from pathlib import Path
import sys

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from render_teaching import configure_scene, render_pair, sha256
from teaching_scene import bounds

ORIGINAL = HERE.parent / "r01" / "endocrine-locator.glb"
POSTERIOR = (0, 1, 0)


def load(path, expected):
    if sha256(path) != expected:
        raise ValueError(f"Restore the pinned endocrine model before rendering: {path.name}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
    scene = bpy.context.scene
    configure_scene(scene)
    return scene, [o for o in scene.objects if o.type == "MESH"]


def render_view(scene, meshes, output, view, source, digest):
    record = render_pair(scene, meshes, view, output)
    record["glb"] = {"file": source.name, "sha256": digest}
    return record


def render(models, output):
    geometry_path = models / "geometry.json"
    artifacts = json.loads(geometry_path.read_text())["artifacts"]
    original_pin = artifacts["atlas-neck-posterior"]["source"]["sha256"]
    scene, meshes = load(ORIGINAL, original_pin)
    neck_bounds = [list(vec) for vec in bounds([o for o in meshes if o.name.startswith("Neck -")])]
    base_neck = {"front": POSTERIOR, "cameraBounds": neck_bounds}
    output.mkdir(parents=True, exist_ok=False)
    views = [
        render_view(scene, meshes, output, {"id": "neck-original", "include": ["Neck - *"], **base_neck},
                    ORIGINAL, original_pin),
        render_view(scene, meshes, output,
                    {"id": "abdomen-atlas", "include": ["Adrenal*", "Pancreas*"], "front": POSTERIOR},
                    ORIGINAL, original_pin),
    ]
    for name, view_id, options in (
        ("atlas-neck-posterior", "neck-updated", base_neck),
        ("s1233-thyroid", "thyroid-s1233", {}),
        ("s1233-adrenals", "abdomen-s1233", {"front": POSTERIOR}),
    ):
        spec = artifacts[name]["glb"]
        path = models / spec["file"]
        scene, meshes = load(path, spec["sha256"])
        views.append(render_view(scene, meshes, output, {"id": view_id, **options}, path, spec["sha256"]))
    source, candidate = views[0], views[2]
    if (
        source["orthographicScale"] != candidate["orthographicScale"]
        or [image["camera"] for image in source["images"]] != [image["camera"] for image in candidate["images"]]
    ):
        raise ValueError("The atlas neck comparison used different cameras")
    (output / "renders.json").write_text(json.dumps({
        "blender": bpy.app.version_string,
        "geometrySha256": sha256(geometry_path),
        "materials": "Authored matte context and gland roles",
        "frames": {
            "neck-original": "r01 atlas locator",
            "neck-updated": "r01 atlas locator, same camera and lighting",
            "abdomen-atlas": "r01 locator, illustrative mixed atlas placement",
            "thyroid-s1233": "s1233 scan frame, independent of the atlas neck",
            "abdomen-s1233": "s1233 scan frame, independent of the atlas abdomen",
        },
        "views": views,
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    render(args.models, args.output)
