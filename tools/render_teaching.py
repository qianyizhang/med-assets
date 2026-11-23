"""Render matched orthographic evidence from a portable GLB, in Blender."""

import argparse
import json
from pathlib import Path
import re
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from med_assets.rendering import area_light, configure_scene, render_pair, sha256

__all__ = ["area_light", "configure_scene", "render_pair", "sha256"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("glb", "views", "output"):
        parser.add_argument("--" + arg, type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    views = json.loads(args.views.read_text())
    ids = [view["id"] for view in views]
    if (
        not ids
        or len(set(ids)) != len(ids)
        or any(not re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids)
    ):
        raise ValueError("View IDs must be unique filename-safe slugs")
    args.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Bone display helpers are Blender UI geometry and would enlarge the camera fit.
    bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()), disable_bone_shape=True)
    scene = bpy.context.scene
    meshes = [o for o in scene.objects if o.type == "MESH"]
    for obj in list(scene.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    configure_scene(scene)
    results = [render_pair(scene, meshes, view, args.output) for view in views]
    record = dict(
        glb=args.glb.name,
        sha256=sha256(args.glb),
        blender=bpy.app.version_string,
        viewsSha256=sha256(args.views),
        views=results,
    )
    (args.output / "renders.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
