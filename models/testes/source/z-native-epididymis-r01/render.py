"""Clean import of the exact GLB. Fixed native cameras shared across revisions."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--views", nargs="+", default=["whole", "posterior-close", "side-close"])
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if args.out.exists():
        raise FileExistsError("Output must be a new directory")
    args.out.mkdir(parents=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(args.artifact))
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.world.color = (.12, .12, .12)
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    target = Vector((0, -.02, .80))
    for direction, power in [((-.6, .7, .8), 14), ((.5, -.3, .1), 7), ((0, -.5, .5), 10)]:
        bpy.ops.object.light_add(type="AREA", location=target + Vector(direction) * .8)
        light = bpy.context.object
        light.data.energy = power * .8 ** 2
        light.data.shape = "DISK"
        light.data.size = .4
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.lens = 50
    camera.data.clip_start = .001
    scene.camera = camera
    views = {
        "whole": ((0, -.015, .805), (.3, 1, .2), .215),
        "posterior-close": ((-.0206, -.052, .744), (-.35, 1, .22), .055),
        "side-close": ((-.0206, -.052, .744), (-1, 0, .08), .055),
        "anterior-close": ((-.0206, -.052, .744), (0, -1, .1), .055),
    }
    rows = []
    for name in args.views:
        aim, direction, scale = views[name]
        camera.location = Vector(aim) + Vector(direction).normalized() * .8
        camera.rotation_euler = (Vector(aim) - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = scale
        scene.render.filepath = str(args.out / (name + ".png"))
        bpy.ops.render.render(write_still=True)
        output = Path(scene.render.filepath)
        rows.append({"file": output.name, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                     "target": aim, "camera": list(camera.location), "scale": scale})
    (args.out / "render.json").write_text(json.dumps({
        "artifact_sha256": hashlib.sha256(args.artifact.read_bytes()).hexdigest(),
        "blender": bpy.app.version_string, "engine": "Cycles CPU", "samples": 24,
        "view_transform": "AgX", "views": rows,
        "scope": "Clean GLB import; fixed source-coordinate views, not validated anatomical/physical scale"}, indent=2) + "\n")


if __name__ == "__main__":
    main()
