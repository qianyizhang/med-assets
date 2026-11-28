"""Render the schematic, frozen CT surface and freshly decoded r01 export."""

import json
import struct
import sys
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


def main():
    reference, mesh, output = map(Path, sys.argv[sys.argv.index("--") + 1 :])
    frozen = json.loads(
        (Path(__file__).resolve().parent.parent / "wave-1/reference.json").read_text()
    )
    with np.load(reference, allow_pickle=False) as data:
        raw, faces = data["vertices"], data["faces"]
    packed = mesh.read_bytes()
    n, triangles = struct.unpack_from("<2I", packed)
    vox = np.frombuffer(packed, "<f4", n * 3, 8).reshape(-1, 3)
    refined_faces = np.frombuffer(packed, "<u4", triangles * 3, 8 + 12 * n).reshape(-1, 3)
    affine = np.asarray(frozen["source"]["rasMmFromVoxel"])
    refined = np.einsum("vi,ji->vj", vox, affine[:3, :3]) + affine[:3, 3]
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

    clay = bpy.data.materials.new("Matte clay")
    clay.use_nodes = True
    shader = clay.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.52, 0.52, 0.52, 1)
    shader.inputs["Roughness"].default_value = 0.51
    shader.inputs["Specular IOR Level"].default_value = 0.31
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32)
    schematic = bpy.context.object
    schematic.scale = (0.024, 0.021, 0.0535)
    objects = [schematic]
    for name, vertices, indices in (
        ("CT mask", raw, faces),
        ("Refined r01", refined, refined_faces),
    ):
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
        area("Fill", (0, 0, 0.25), 3, 0.18, (0, 0, 0)),
        area("Edge", (0, 0, 0.25), 5, 0.12, (0, 0, 0)),
    ]
    output.mkdir(parents=True, exist_ok=True)
    for name, direction, target, scale in (
        ("overview", (0.1, -1, 0.14), (0, 0, 0), 0.165),
        ("reverse", (-1, 0.75, 0.25), (0, 0, 0.004), 0.152),
    ):
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
