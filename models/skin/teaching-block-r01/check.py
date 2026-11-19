"""Measure selected joins in an independent Blender import, in millimetres."""
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def main():
    glb = Path(sys.argv[sys.argv.index('--') + 1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb.resolve()))
    points, trees = {}, {}
    triangles = 0
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        mesh.calc_loop_triangles()
        triangles += len(mesh.loop_triangles)
        vertices = [1000 * (obj.matrix_world @ v.co) for v in mesh.vertices]
        points[obj.name] = vertices
        trees[obj.name] = BVHTree.FromPolygons(vertices, [tri.vertices for tri in mesh.loop_triangles], all_triangles=True)
    expected = {
        'Skin | ' + name for name in ['Dermis', 'Epidermis', 'Subcutaneous tissue', 'Hair root and shaft',
                                     'Follicle (cut sheath)', 'Eccrine secretory coil', 'Sweat duct and open pore']
    } | {'Skin | Fat lobule %02d' % i for i in range(1, 16)} | {
        'Nail | ' + name for name in ['Distal digit tissue', 'Germinal matrix', 'Nail bed',
                                      'Nail plate with free edge', 'Proximal nail fold']
    }
    require(set(points) == expected, 'Unexpected or missing nodes in clean import')
    dermis = trees['Skin | Dermis']
    def cast(tree, origin, direction, distance=10):
        return tree.ray_cast(Vector(origin), Vector(direction), distance)[0]

    base = min(v.z for v in points['Skin | Follicle (cut sheath)'])
    bottom = cast(dermis, (-1.13, .4, -1), (0, 0, 1))
    roof = cast(dermis, (-1.13, .4, 9), (0, 0, -1))
    require(bottom.z < base < roof.z, 'Follicle bulb falls outside the dermal depth')
    under = trees['Skin | Subcutaneous tissue']
    epi = trees['Skin | Epidermis']
    for x in (-2.8, -.4, 1.9, 2.85):
        for lower, upper in ((under, dermis), (dermis, epi)):
            lower_high = cast(lower, (x, .5, 9), (0, 0, -1))
            upper_low = cast(upper, (x, .5, -1), (0, 0, 1))
            require(abs(lower_high.z - upper_low.z) < .001, 'Adjacent tissues separated at sample')
    duct = trees['Skin | Sweat duct and open pore']
    top = max(v.z for v in points['Skin | Sweat duct and open pore'])
    require(abs(top - 4.1) < .001, 'Duct rim and skin surface separated')
    for tree in (duct, epi):
        require(cast(tree, (1.49, .025, 4.3), (0, 0, -1), .25) is None, 'Pore lumen is occluded')
    rim = cast(duct, (1.49 + .115, .008, 4.3), (0, 0, -1))
    require(rim and abs(rim.z - top) < .001, 'Missing solid rim beside pore lumen')
    cyclic = {tuple(round(k, 4) for k in v) for v in points['Skin | Eccrine secretory coil']}
    channel = {tuple(round(k, 4) for k in v) for v in points['Skin | Sweat duct and open pore']}
    require(len(cyclic & channel) == 40, 'Coil to duct join lacks matching inner/outer rings')
    contact = {}
    for tissue, x in [('Germinal matrix', 4.78), ('Nail bed', 6.05)]:
        low = cast(trees['Nail | Nail plate with free edge'], (x, .4, -1), (0, 0, 1))
        high = cast(trees['Nail | ' + tissue], (x, .4, 9), (0, 0, -1))
        require(abs(high.z - low.z) < .001, 'Gap under plate over ' + tissue)
        contact[tissue] = round(abs(high.z-low.z), 6)
    print(json.dumps(dict(glbSha256=hashlib.sha256(glb.read_bytes()).hexdigest(), meshes=len(points),
                          triangles=triangles, bulbBaseMm=base, localDermalIntervalMm=[bottom.z, roof.z],
                          ductRimMm=top, commonDuctCoilCoordinates=len(cyclic & channel),
                          nailContactGapsMm=contact), indent=2))


if __name__ == '__main__':
    main()
