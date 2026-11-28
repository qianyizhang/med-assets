"""Render matched previous, half-label and refined clay plates."""

import argparse
import json
import struct
import sys
from hashlib import sha256
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


def aim(obj, at):
    obj.rotation_euler = (Vector(at) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area(name, position, energy, size, target):
    light = bpy.data.lights.new(name, "AREA")
    light.energy = energy
    light.shape = "DISK"
    light.size = size
    obj = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    aim(obj, target)
    return obj


def packed_ras(path, affine, expected):
    data = path.read_bytes()
    if expected and (
        sha256(data).hexdigest() != expected["sha256"] or len(data) != expected["bytes"]
    ):
        raise ValueError(f"Packed mesh identity mismatch: {path}")
    vertices, triangles = struct.unpack_from("<2I", data)
    if (expected and triangles != expected["triangles"]) or len(data) != 8 + 12 * (
        vertices + triangles
    ):
        raise ValueError(f"Unexpected mesh counts: {path}")
    xyz = np.frombuffer(data, "<f4", vertices * 3, 8).reshape(-1, 3)
    faces = np.frombuffer(data, "<u4", triangles * 3, 8 + 12 * vertices).reshape(-1, 3)
    return np.einsum("vi,ji->vj", xyz, affine[:3, :3]) + affine[:3, 3], faces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("measurements", type=Path)
    parser.add_argument("previous", type=Path)
    parser.add_argument("mesh", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    receipt = json.loads(args.measurements.read_text())
    organ = receipt["frozen"]["organ"]
    with np.load(args.reference, allow_pickle=False) as data:
        raw, faces = data["vertices"], data["faces"]
    affine = np.asarray(receipt["frozen"]["source"]["rasMmFromVoxel"])
    refined, refined_faces = packed_ras(args.mesh, affine, receipt["export"])
    previous, previous_faces = packed_ras(args.previous, affine, receipt["previousSweep"])
    output = args.output
    center = (raw.min(0) + raw.max(0)) / 2

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 20
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 518, 370
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Neutral backdrop")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.045, 0.045, 0.045, 1)
    background.inputs["Strength"].default_value = 0.48
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = -1.7

    clay = bpy.data.materials.new("Matte clay")
    clay.use_nodes = True
    shader = clay.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.43, 0.43, 0.43, 1)
    shader.inputs["Roughness"].default_value = 0.51
    shader.inputs["Specular IOR Level"].default_value = 0.31
    objects = []
    sources = [
        ("Previous delivery", previous, previous_faces),
        ("CT half-label", raw, faces),
        ("Refined r01", refined, refined_faces),
    ]
    for name, vertices, indices in sources:
        geometry = bpy.data.meshes.new(name)
        points = (vertices - center) * 0.001
        a, b, c = points[indices].transpose(1, 0, 2)
        if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
            indices = indices[:, ::-1]
        geometry.from_pydata(points, [], indices)
        obj = bpy.data.objects.new(name, geometry)
        bpy.context.collection.objects.link(obj)
        objects.append(obj)
    for obj in objects:
        obj.data.materials.append(clay)
        obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
        obj.hide_render = True

    camera = bpy.data.objects.new(
        "Matched orthographic camera", bpy.data.cameras.new("Orthographic")
    )
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    lights = [
        area("Softbox", (0, 0, 0.25), 9, 0.11, (0, 0, 0)),
        area("Fill", (0, 0, 0.25), 2, 0.18, (0, 0, 0)),
        area("Edge", (0, 0, 0.25), 5, 0.12, (0, 0, 0)),
    ]
    output.mkdir(parents=True, exist_ok=True)
    if organ == "spleen":
        views = [
            ("overview", (-0.38, -0.92, 0.22), (0, 0, 0), 0.155),
            ("reverse", (1, 0.35, 0.12), (0, 0, 0), 0.155),
            ("detail", (1, 0.35, 0.12), (0, 0.001, 0.004), 0.10),
        ]
    else:
        views = [
            ("overview", (0.35, 0.75, 0.55), (0, 0, 0), 0.18),
            ("reverse", (-0.28, -0.65, 0.72), (0, 0, 0), 0.18),
            ("detail", (-0.28, -0.65, 0.72), (-0.035, 0, 0.008), 0.095),
        ]
    for name, direction, target, scale in views:
        forward = Vector(direction).normalized()
        up = Vector((0, 0, 1))
        side = forward.cross(up).normalized()
        camera.location = Vector(target) + 0.4 * forward
        camera.data.ortho_scale = scale
        aim(camera, target)
        for light, (depth, lateral, height) in zip(
            lights, ((0.13, -0.13, 0.17), (0.11, 0.14, 0.045), (-0.12, 0.04, 0.15)), strict=True
        ):
            light.location = Vector(target) + depth * forward + lateral * side + height * up
            aim(light, target)
        for i, obj in enumerate(objects):
            obj.hide_render = False
            scene.render.filepath = str((output / f"{name}-{i}.png").resolve())
            bpy.ops.render.render(write_still=True)
            obj.hide_render = True


if __name__ == "__main__":
    main()
