"""Check the actual GLB mesh surfaces at the documented junction coordinates."""

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
parser.add_argument("--placement", required=True, type=Path)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
meshes = {}
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
        meshes[obj.name] = BVHTree.FromPolygons(
            coords, [list(p.vertices) for p in obj.data.polygons]
        )
placement = json.loads(args.placement.read_text())
errors = []
for coord, parts in placement["junctions"]:
    for name in parts:
        distance = meshes[name].find_nearest(Vector(coord))[3]
        if distance > 0.00005:
            raise ValueError(f"{name} misses {coord} by {distance} m")
        errors.append(distance)
# The lower cap and trunk enter the cisterna through its two ends.
for coord in [(0.004, 0.038, -0.206), (0, 0.04, -0.20)]:
    direction = Vector((0.37, -0.72, 0.61)).normalized()
    _, normal, face, _ = meshes["Cisterna chyli - schematic"].ray_cast(
        Vector(coord), direction
    )
    if face is None or normal.dot(direction) <= 0:
        raise ValueError("Trunk or duct endpoint lies outside the imported cisterna")
for region in ["Spleen locator", "Thymus locator"]:
    if not any(k.startswith(region) for k in meshes):
        raise ValueError("Absent " + region)
print(
    json.dumps(
        dict(
            sha256=hashlib.sha256(args.glb.read_bytes()).hexdigest(),
            meshes=len(meshes),
            surfaceTests=len(errors),
            maxDistanceMetres=max(errors),
        )
    )
)
