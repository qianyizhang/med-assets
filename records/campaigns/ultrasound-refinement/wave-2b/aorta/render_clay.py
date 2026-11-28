"""Render matched exteriors on the Wave 1B neutral clay rig."""

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
    parser.add_argument("replay", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--brief", type=Path, default=HERE / "frozen.json")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    reference, replay, baseline, output = args.reference, args.replay, args.baseline, args.output
    frozen = json.loads(args.brief.read_text())
    affine = np.array(frozen["source"]["rasMmFromVoxel"])
    spec = importlib.util.spec_from_file_location(
        "clay_rig", HERE.parent.parent / "wave-1b/render_clay.py"
    )
    rig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rig)
    output.mkdir(parents=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = (400, 530)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Neutral backdrop")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.045, 0.045, 0.045, 1)
    background.inputs["Strength"].default_value = 0.5
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = -0.8

    clay = bpy.data.materials.new("Matte clay")
    clay.use_nodes = True
    shader = clay.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.47, 0.47, 0.47, 1)
    shader.inputs["Roughness"].default_value = 0.58

    camera = bpy.data.objects.new("Orthographic camera", bpy.data.cameras.new("Orthographic"))
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    lights = [
        rig.area("Key", (0, 0, 0.35), 20, 0.16, (0, 0, 0)),
        rig.area("Fill", (0, 0, 0.35), 7, 0.24, (0, 0, 0)),
        rig.area("Rim", (0, 0, 0.35), 12, 0.13, (0, 0, 0)),
    ]

    def render(name, geometries, center, direction, target, scale):
        forward = Vector(direction).normalized()
        side = forward.cross(Vector((0, 0, 1))).normalized()
        camera.location = Vector(target) + 0.6 * forward
        camera.data.ortho_scale = scale
        rig.aim(camera, target)
        for light, (depth, lateral, height) in zip(
            lights, ((0.24, -0.17, 0.2), (0.20, 0.20, -0.12), (-0.17, 0.08, 0.25)), strict=True
        ):
            light.location = (
                Vector(target) + depth * forward + lateral * side + height * Vector((0, 0, 1))
            )
            rig.aim(light, target)
        for label, (vertices, faces) in geometries.items():
            points = (vertices - center) / 1000
            a, b, c = points[faces].transpose(1, 0, 2)
            if np.einsum("ij,ij->", a, np.cross(b, c)) < 0:
                faces = faces[:, ::-1]
            data = bpy.data.meshes.new(label)
            data.from_pydata(points, [], faces)
            data.materials.append(clay)
            data.polygons.foreach_set("use_smooth", [True] * len(data.polygons))
            obj = bpy.data.objects.new(label, data)
            bpy.context.collection.objects.link(obj)
            scene.render.filepath = str((output / f"{name}-{label}.png").resolve())
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.meshes.remove(data)

    for name, config in frozen["exports"].items():
        with np.load(reference / f"{name}-reference.npz", allow_pickle=False) as raw:
            vertices, faces = raw["vertices"], raw["faces"]
        center = (vertices.max(0) + vertices.min(0)) / 2
        basename = name
        if frozen["source"].get("label", "").startswith("common_carotid_artery_"):
            basename = "carotid" if name.endswith("-full") else "neck"
        geometries = {
            "raw": (vertices, faces),
            "r01": rig.packed_ras(replay / f"{basename}.mesh", affine, None),
        }
        if "prior" in config:
            pin = config["prior"]["stage"]
            geometries["previous"] = rig.packed_ras(
                baseline / "stage" / pin["path"],
                affine,
                pin | {"triangles": config["prior"]["triangles"]},
            )
        scale = float(np.ptp(vertices[:, 2]) / 1000 * 1.15)
        render(f"{name}-anterior", geometries, center, (0.4, 1, 0.19), (0, 0, 0), scale)
        if name == "aorta":
            target_z = (float(affine[2, 3] + 332 * affine[2, 2]) - center[2]) / 1000
            render(f"{name}-detail", geometries, center, (-0.9, -0.65, 0.15), (0, 0, target_z), 0.1)
        elif frozen["source"]["case"] == "s1233":
            target_z = (float(affine[2, 3] + 178 * affine[2, 2]) - center[2]) / 1000
            render(
                f"{name}-detail", geometries, center, (-0.9, -0.75, 0.21), (0, 0, target_z), 0.09
            )
        elif frozen["source"].get("label") == "trachea" and name == "trachea":
            target = tuple((np.array([7.0, 118.0, 185.0]) - center) / 1000)
            render(f"{name}-detail", geometries, center, (-0.9, -0.75, 0.21), target, 0.065)
        else:
            render(f"{name}-detail", geometries, center, (-0.9, -0.75, 0.21), (0, 0, 0), 0.034)


if __name__ == "__main__":
    main()
