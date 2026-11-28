"""Render the staged IVC locator, raw half-label and clean packed candidate in neutral clay."""

import argparse
import json
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "report", "previous", "candidate", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    tools = runpy.run_path(str(HERE.parents[1] / "wave-2a/spleen/render_clay.py"))
    aim, area, packed = (tools[name] for name in ("aim", "area", "packed_ras"))
    data = json.loads(args.report.read_text())
    with np.load(args.reference, allow_pickle=False) as reference:
        xyz, faces, affine = (reference[key] for key in ("vertices", "faces", "affine"))
    baseline = packed(args.previous, affine, data["frozen"]["previousSweep"])
    candidate = packed(args.candidate, affine, data["exports"]["abdominal"]["export"])
    center = (xyz.min(0) + xyz.max(0)) / 2

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 20
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 340, 650
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Neutral backdrop")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.045, 0.045, 0.045, 1)
    background.inputs["Strength"].default_value = 0.48
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = -1.1

    clay = bpy.data.materials.new("Matte clay")
    clay.use_nodes = True
    shader = clay.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.43, 0.43, 0.43, 1)
    shader.inputs["Roughness"].default_value = 0.51
    objects = []
    for name, (vertices, indices) in zip(
        ("Previous delivery", "CT half-label", "Refined r01"),
        (baseline, (xyz, faces), candidate),
        strict=True,
    ):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata((vertices - center) * 0.001, [], indices)
        mesh.materials.append(clay)
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.hide_render = True
        objects.append(obj)

    camera = bpy.data.objects.new("Matched camera", bpy.data.cameras.new("Orthographic"))
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    lights = [
        area("Softbox", (0, 0, 0.25), 9, 0.14, (0, 0, 0)),
        area("Fill", (0, 0, 0.25), 2, 0.20, (0, 0, 0)),
        area("Rim", (0, 0, 0.25), 5, 0.14, (0, 0, 0)),
    ]
    views = [
        ("anterior", (0.32, 0.94, 0.10), (0, 0, 0), 0.224),
        ("reverse", (-0.83, -0.54, 0.04), (0, 0, 0), 0.224),
        ("shoulder", (0.86, 0.49, 0.16), (0.019, -0.003, 0.047), 0.076),
    ]
    args.output.mkdir(parents=True, exist_ok=False)
    for view, direction, center_view, scale in views:
        target, forward = Vector(center_view), Vector(direction).normalized()
        up = Vector((0, 0, 1))
        side = forward.cross(up).normalized()
        camera.location = target + 0.4 * forward
        camera.data.ortho_scale = scale
        aim(camera, target)
        for light, (depth, lateral, height) in zip(
            lights,
            ((0.13, -0.13, 0.13), (0.11, 0.14, 0.02), (-0.12, 0.04, 0.16)),
            strict=True,
        ):
            light.location = target + depth * forward + lateral * side + height * up
            aim(light, target)
        for index, obj in enumerate(objects):
            obj.hide_render = False
            scene.render.filepath = str((args.output / f"{view}-{index}.png").resolve())
            bpy.ops.render.render(write_still=True)
            obj.hide_render = True


if __name__ == "__main__":
    main()
