"""Reproduce the excluded left submandibular source centerline crossing."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils.bvhtree import BVHTree
from mathutils.geometry import interpolate_bezier

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
from z_anatomy import verified_member_hash


def crossing(source):
    source_hash = verified_member_hash(source)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    names = ("Submandibular duct.l", "Mylohyoid muscle.l")
    with bpy.data.libraries.load(str(source), link=False) as (available, selected):
        if not all(name in available.objects for name in names):
            raise ValueError("Missing source object for the negative control")
        selected.objects = list(names)
    duct, muscle = selected.objects
    for obj in selected.objects:
        bpy.context.collection.objects.link(obj)
        obj.hide_set(False)
        obj.hide_viewport = False
    bpy.context.view_layer.update()
    vertices = [muscle.matrix_world @ vertex.co for vertex in muscle.data.vertices]
    surface = BVHTree.FromPolygons(vertices, [list(face.vertices) for face in muscle.data.polygons])
    hits = []
    for spline in duct.data.splines:
        controls = list(spline.bezier_points)
        for start, end in zip(controls, controls[1:]):
            points = interpolate_bezier(start.co, start.handle_right, end.handle_left, end.co, 31)
            world = [duct.matrix_world @ point for point in points]
            for a, b in zip(world, world[1:]):
                step = b - a
                if step.length < 1e-8:
                    continue
                hit = surface.ray_cast(a, step.normalized(), step.length)[0]
                if hit is not None:
                    hits.append(list(hit))
    if not hits:
        raise ValueError("Expected left submandibular source crossing was not detected")
    return {"source_sha256": source_hash, "source_objects": names, "sampled_intersections": hits}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    report = crossing(args.source)
    with args.out.open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
