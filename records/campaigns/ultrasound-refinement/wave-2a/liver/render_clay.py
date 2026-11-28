"""Render the CT half-label and both liver exports with a fixed orthographic rig."""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("previous", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    frozen = json.loads((HERE / "frozen.json").read_text())
    spec = importlib.util.spec_from_file_location(
        "clay_rig", HERE.parents[1] / "wave-1b/render_clay.py"
    )
    if not spec or not spec.loader:
        raise ImportError("The Wave 1B clay renderer is unavailable")
    rig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rig)
    affine = np.asarray(frozen["source"]["rasMmFromVoxel"])
    with np.load(args.reference, allow_pickle=False) as raw:
        raw_v, raw_f = raw["vertices"], raw["faces"]
    baseline = frozen["baseline"]["sweeps/liver/scenes/liver.mesh"] | {"triangles": 123204}
    meshes = [
        ("half-label", raw_v, raw_f),
        ("r01", *rig.packed_ras(args.previous, affine, baseline)),
        ("r02", *rig.packed_ras(args.candidate, affine, None)),
    ]
    center = (raw_v.min(axis=0) + raw_v.max(axis=0)) / 2
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 570, 370
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Neutral backdrop")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.045, 0.045, 0.045, 1)
    background.inputs["Strength"].default_value = 0.5
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = -1.1

    clay = bpy.data.materials.new("Matte clay")
    clay.use_nodes = True
    shader = clay.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.52, 0.52, 0.52, 1)
    shader.inputs["Roughness"].default_value = 0.58
    shader.inputs["Specular IOR Level"].default_value = 0.31
    objects = []
    for name, vertices, faces in meshes:
        points = (vertices - center) / 1000
        a, b, c = points[faces].transpose(1, 0, 2)
        if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
            faces = faces[:, ::-1]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(points, [], faces)
        mesh.materials.append(clay)
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.hide_render = True
        objects.append(obj)

    camera = bpy.data.objects.new("Orthographic camera", bpy.data.cameras.new("Orthographic"))
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    lights = [
        rig.area("Key", (0, 0, 0.35), 22, 0.16, (0, 0, 0)),
        rig.area("Fill", (0, 0, 0.35), 6, 0.24, (0, 0, 0)),
        rig.area("Rim", (0, 0, 0.35), 12, 0.13, (0, 0, 0)),
    ]
    args.output.mkdir(parents=True)
    views = [
        ("anterior", (0.18, 1, 0.16), (0, 0, 0), 0.240),
        ("inferior", (0.18, 0.72, -0.77), (0, 0.01, -0.035), 0.205),
        ("dome", (-0.82, 0.72, 0.48), (-0.061, 0.026, 0.046), 0.121),
    ]
    for label, direction, target, scale in views:
        forward = Vector(direction).normalized()
        side = forward.cross(Vector((0, 0, 1))).normalized()
        camera.location = Vector(target) + 0.5 * forward
        camera.data.ortho_scale = scale
        rig.aim(camera, target)
        offsets = ((0.24, -0.18, 0.18), (0.15, 0.22, 0.04), (-0.16, 0.08, 0.19))
        for light, (depth, lateral, height) in zip(lights, offsets, strict=True):
            light.location = (
                Vector(target) + depth * forward + lateral * side + height * Vector((0, 0, 1))
            )
            rig.aim(light, target)
        for obj in objects:
            obj.hide_render = False
            scene.render.filepath = str((args.output / f"{label}-{obj.name}.png").resolve())
            bpy.ops.render.render(write_still=True)
            obj.hide_render = True


if __name__ == "__main__":
    main()
