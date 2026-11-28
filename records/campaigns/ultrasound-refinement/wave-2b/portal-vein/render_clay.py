"""Render the three reimported surfaces in matched orthographic clay views."""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

SHARED = Path(__file__).resolve().parents[2] / "wave-2a/spleen/render_clay.py"
SPEC = importlib.util.spec_from_file_location("clay", SHARED)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load {SHARED}")
clay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(clay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "measurements", "previous", "mesh", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--preset", choices=("portal-vein", "thyroid"), default="portal-vein")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    receipt = json.loads(args.measurements.read_text())
    affine = np.asarray(receipt["frozen"]["source"]["rasMmFromVoxel"])
    with np.load(args.reference, allow_pickle=False) as arrays:
        raw, faces = arrays["vertices"], arrays["faces"]
    surfaces = [
        clay.packed_ras(args.previous, affine, receipt["previousSweep"]),
        (raw, faces),
        clay.packed_ras(args.mesh, affine, receipt["export"]),
    ]
    center = (raw.min(0) + raw.max(0)) / 2

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 540, 370
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Neutral gray")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.045, 0.045, 0.045, 1)
    background.inputs["Strength"].default_value = 0.55
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = -1.4

    material = bpy.data.materials.new("Matte clay")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.43, 0.43, 0.43, 1)
    shader.inputs["Roughness"].default_value = 0.53
    objects = []
    for i, (vertices, indices) in enumerate(surfaces):
        geometry = bpy.data.meshes.new(f"Source {i}")
        points = (vertices - center) / 1000
        a, b, c = points[indices].transpose(1, 0, 2)
        if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
            indices = indices[:, ::-1]
        geometry.from_pydata(points, [], indices)
        obj = bpy.data.objects.new(geometry.name, geometry)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(material)
        obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
        obj.hide_render = True
        objects.append(obj)

    camera = bpy.data.objects.new("Matched camera", bpy.data.cameras.new("Orthographic"))
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    lights = [
        clay.area(name, (0, 0, 0.25), power, size, (0, 0, 0))
        for name, power, size in (("Key", 7, 0.13), ("Fill", 2, 0.16), ("Rim", 4, 0.10))
    ]
    junction = (np.array([24, 199, 351]) - center) / 1000
    views = (
        ("overview", (0.08, -0.75, 0.66), (0, 0, 0), 0.214),
        ("reverse", (-0.18, 0.68, 0.73), (0, 0, 0), 0.224),
        ("detail", (0.08, -0.75, 0.66), junction, 0.103),
    )
    if args.preset == "thyroid":
        views = (
            ("overview", (0.08, 0.95, 0.35), (0, 0, 0), 0.087),
            ("reverse", (-0.10, -0.92, 0.28), (0, 0, 0), 0.087),
            ("detail", (0.04, 0.85, 0.52), (0, 0.01, -0.003), 0.053),
        )
    args.output.mkdir(parents=True)
    for name, direction, origin, scale in views:
        target = Vector(origin)
        forward = Vector(direction).normalized()
        up = Vector((0, 0, 1))
        side = forward.cross(up).normalized()
        camera.location = target + 0.4 * forward
        camera.data.ortho_scale = scale
        clay.aim(camera, target)
        for light, (depth, lateral, height) in zip(
            lights, ((0.13, -0.13, 0.17), (0.11, 0.14, 0.045), (-0.12, 0.04, 0.15)), strict=True
        ):
            light.location = target + depth * forward + lateral * side + height * up
            clay.aim(light, target)
        for i, obj in enumerate(objects):
            obj.hide_render = False
            scene.render.filepath = str((args.output / f"{name}-{i}.png").resolve())
            bpy.ops.render.render(write_still=True)
            obj.hide_render = True


if __name__ == "__main__":
    main()
