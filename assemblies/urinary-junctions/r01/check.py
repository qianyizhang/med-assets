"""Check both gross routes on world-space triangles from the clean GLB."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

parser = argparse.ArgumentParser()
parser.add_argument("--glb", required=True, type=Path)
parser.add_argument("--junctions", required=True, type=Path)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
surfaces = {}
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
        surfaces[obj.name] = BVHTree.FromPolygons(
            vertices, [list(p.vertices) for p in obj.data.polygons]
        )
joins = json.loads(args.junctions.read_text())
expected = {"bladder-outlet", "outlet-join"} | {
    f"{side}-{join}"
    for side in ("left", "right")
    for join in ("renal", "vesical", "upper-course", "lower-course")
}
if set(joins) != expected:
    raise ValueError("Incomplete set of junctions")
distances = {}
for key, (anchor, *parts) in joins.items():
    errors = [surfaces[name].find_nearest(Vector(anchor))[3] for name in parts]
    if len(parts) != 2 or max(errors) > 0.00005:
        raise ValueError(f"{key} does not meet both surfaces: {errors}")
    distances[key] = max(errors)
print(
    json.dumps(
        dict(
            sha256=hashlib.sha256(args.glb.read_bytes()).hexdigest(),
            meshes=len(surfaces),
            maxDistanceMetres=distances,
        )
    )
)
