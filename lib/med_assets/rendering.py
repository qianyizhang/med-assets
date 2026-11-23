"""Blender lighting, camera framing and matched view rendering."""

from fnmatch import fnmatchcase
import hashlib
import math

import bpy
from mathutils import Vector


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def area_light(scene, center, extent, name, offset, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy * extent**2
    data.shape = "DISK"
    data.size = size * extent
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = center + Vector(offset) * extent
    obj.rotation_euler = (center - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def render_pair(scene, meshes, view, output):
    include = view.get("include", ["*"])
    selected = set()
    for pattern in include:
        matches = {obj for obj in meshes if fnmatchcase(obj.name, pattern)}
        if not matches:
            raise ValueError(f"No imported mesh matches {pattern!r} for {view['id']}")
        selected.update(matches)
    if not selected:
        raise ValueError("Empty view")
    for obj in meshes:
        obj.hide_render = obj not in selected
    scene.frame_set(view.get("frame", 1))
    deps = bpy.context.evaluated_depsgraph_get()
    points = []
    for obj in selected:
        evaluated = obj.evaluated_get(deps)
        points.extend(evaluated.matrix_world @ Vector(p) for p in evaluated.bound_box)
    bounds = [
        [min(p[i] for p in points) for i in range(3)],
        [max(p[i] for p in points) for i in range(3)],
    ]
    if "cameraBounds" in view:
        lo, hi = map(Vector, view["cameraBounds"])
        points = [
            Vector((x, y, z))
            for x in (lo.x, hi.x)
            for y in (lo.y, hi.y)
            for z in (lo.z, hi.z)
        ]
    else:
        lo, hi = map(Vector, bounds)
    extent = max(hi - lo)
    center = (hi + lo) / 2
    front = Vector(view.get("front", (0, -1, 0))).normalized()
    right = Vector((-front.y, front.x, 0)).normalized()
    if extent <= 0 or not right.length or not math.isfinite(extent):
        raise ValueError(f"Degenerate view {view['id']}")
    directions = [
        ("iso", (front + right + Vector((0, 0, 1))).normalized()),
        ("ortho", front),
    ]
    camera = scene.camera
    camera.data.clip_start = extent * 0.001
    camera.data.clip_end = extent * 24
    poses = []
    sizes = []
    for label, direction in directions:
        rot = (-direction).to_track_quat("-Z", "Y")
        projected = [rot.inverted() @ (p - center) for p in points]
        xs = [p.x for p in projected]
        ys = [p.y for p in projected]
        midpoint = rot @ Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, 0))
        poses.append((label, direction, rot, midpoint))
        sizes.append(
            max(
                max(xs) - min(xs),
                (max(ys) - min(ys))
                * scene.render.resolution_x
                / scene.render.resolution_y,
            )
        )
    camera.data.ortho_scale = max(sizes) * 1.09
    lights = [
        area_light(scene, center, extent, name, offset, energy, size)
        for name, offset, energy, size in [
            ("Key", (-2, -3, 4), 540, 3),
            ("Fill", (3, -2, 1), 240, 4),
            ("Rim", (1, 3, 3), 350, 3),
        ]
    ]
    images = []
    for label, direction, rot, midpoint in poses:
        camera.location = center + direction * extent * 5 + midpoint
        camera.rotation_euler = rot.to_euler()
        path = output / f"{view['id']}-{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        images.append(
            dict(
                file=path.name,
                sha256=sha256(path),
                direction=list(direction),
                camera=list(camera.location),
            )
        )
    for lamp in lights:
        bpy.data.lights.remove(lamp.data, do_unlink=True)
    return dict(
        id=view["id"],
        frame=scene.frame_current,
        visible=sorted(ob.name for ob in selected),
        bounds=bounds,
        orthographicScale=camera.data.ortho_scale,
        images=images,
    )


def configure_scene(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x, scene.render.resolution_y = 800, 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.world = bpy.data.worlds.new("Survey world")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.60, 0.64, 0.70, 1)
    bg.inputs[1].default_value = 0.32
    scene.view_settings.view_transform = "AgX"
    camera = bpy.data.cameras.new("Evidence projection")
    camera.type = "ORTHO"
    scene.camera = bpy.data.objects.new("Evidence camera", camera)
    scene.collection.objects.link(scene.camera)
