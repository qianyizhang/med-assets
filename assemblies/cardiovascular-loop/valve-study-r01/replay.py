"""Save the editable study and render clean imports for the valve comparison."""
import argparse
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import STUDY, digest
from render_teaching import configure_scene, render_pair


def import_scene(asset):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(asset.resolve()), disable_bone_shape=True)
    return bpy.context.scene


def render(asset, views, manifest, output, editable=None):
    output.mkdir(parents=True, exist_ok=False)
    scene = import_scene(asset)
    scene.unit_settings.system = "METRIC"
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    if editable:
        bpy.ops.wm.save_as_mainfile(filepath=str(editable.resolve()))
    configure_scene(scene)
    result = {
        "glb": asset.name, "sha256": digest(asset), "blender": bpy.app.version_string,
        "viewsSha256": digest(manifest),
        "views": [render_pair(scene, meshes, view, output) for view in views],
    }
    (output / "renders.json").write_text(json.dumps(result, indent=2) + "\n")


def replay(work):
    manifest = Path(__file__).with_name("views.json")
    views = json.loads(manifest.read_text())
    build = work / "build"
    render(build / f"{STUDY}.glb", views, manifest, work / "renders", build / f"{STUDY}.blend")
    render(build / "matched-source.glb", views, manifest, work / "matched-source")
    seated, = (view for view in views if view["id"] == "mitral-seated")
    displaced = {**seated, "id": "mitral-displaced"}
    render(build / "mitral-lift-evidence.glb", [displaced], manifest, work / "displaced")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    replay(args.work)
