"""Illustrative surface treatment of the exact retained s0189 thyroid export.

Blender 4.3.2 Laplacian Smooth; no raw-label reconstruction or sample normalization.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

SOURCE = 'models/thyroid_ct_s0189/exports/source-candidate-02/thyroid_ct_s0189_source_frame.glb'
SOURCE_SHA = '4add07e2efed2d67efb1d4ba225a109fe448043c79182e3d2e1a96e671534883'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def topo(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    remaining = set(bm.verts)
    counts = []
    while remaining:
        stack = [remaining.pop()]
        count = 0
        while stack:
            v = stack.pop()
            count += 1
            for edge in v.link_edges:
                other = edge.other_vert(v)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
        counts.append(count)
    data = {'vertices': len(bm.verts), 'faces': len(bm.faces),
            'components': sorted(counts, reverse=True),
            'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
            'zero_area_faces': sum(f.calc_area() < 1e-10 for f in bm.faces),
            'signed_volume_mm3': bm.calc_volume(signed=True)}
    bm.free()
    return data


def bounds(vertices):
    return [[min(v[i] for v in vertices), max(v[i] for v in vertices)] for i in range(3)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--strength', type=float, default=.35)
    parser.add_argument('--iterations', type=int, default=8)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if args.out.exists():
        raise FileExistsError('Use a new output directory')
    source = args.root / SOURCE
    if source.stat().st_size != 151580 or sha(source) != SOURCE_SHA:
        raise ValueError('Wrong source identity')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if len(objects) != 1:
        raise ValueError('Expected one retained thyroid mesh')
    ob = objects[0]
    world = ob.matrix_world.copy()
    original = [world @ v.co for v in ob.data.vertices]
    center = sum(original, Vector()) / len(original)
    for v, p in zip(ob.data.vertices, original):
        v.co = (p - center) * 1000
    ob.matrix_world.identity()
    ob.data.update()
    before = topo(ob.data)
    group = ob.vertex_groups.new(name='negative-Y ridge-facing emphasis; reduced central bridge')
    weights = []
    for v, p in zip(ob.data.vertices, original):
        # The sampled negative-Y surface carries the target ridges. This is a
        # source-coordinate selection, not a claim of independently verified axes.
        t = min(1, max(0, (-v.normal.y + .35) / .55))
        t = t * t * (3 - 2 * t)
        front = .20 + .80 * t
        lateral = min(1, max(0, (abs(p.x) * 1000 - 5) / 8))
        lateral = lateral * lateral * (3 - 2 * lateral)
        weight = front * (.35 + .65 * lateral)
        weights.append(weight)
        group.add([v.index], weight, 'REPLACE')
    bpy.context.view_layer.objects.active = ob
    modifier = ob.modifiers.new('Established Laplacian Smooth surface treatment', 'LAPLACIANSMOOTH')
    modifier.iterations = args.iterations
    modifier.lambda_factor = args.strength
    modifier.lambda_border = 0
    modifier.use_volume_preserve = True
    modifier.use_normalized = True
    modifier.vertex_group = group.name
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    after = topo(ob.data)
    if before['vertices'] != after['vertices'] or before['faces'] != after['faces']:
        raise ValueError('Unexpected topology change')
    if after['nonmanifold_edges'] or after['zero_area_faces'] or after['signed_volume_mm3'] <= 0:
        raise ValueError('Invalid smoothed exterior')
    positions = [v.co / 1000 + center for v in ob.data.vertices]
    distances = [(p-q).length * 1000 for p, q in zip(original, positions)]
    for v, p in zip(ob.data.vertices, positions):
        v.co = p
    ob.name = 's0189 thyroid — illustrative ridge reduction'
    ob['source_sha256'] = SOURCE_SHA
    ob['derivative'] = 'Blender Laplacian Smooth on the sampled negative-Y ridge-facing surface, with reduced opposite-face/central-bridge influence; illustrative exterior, not improved segmentation'
    ob['clinical_scope'] = 'Retained public clinical-source sample; not healthy/normative anatomy. No new anatomical structures.'
    ob['units_limit'] = 'Source-frame metres inferred from the retained 1.5mm label convention; original header unit flag unspecified.'
    ob['runtime'] = 'unverified'
    args.out.mkdir(parents=True)
    output = args.out / 'thyroid-illustrative-exterior.glb'
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(output), export_format='GLB', use_selection=True,
                              export_extras=True, export_yup=True, export_animations=False)
    record = {'source': {'file': SOURCE, 'sha256': SOURCE_SHA, 'bytes': 151580},
              'artifact': {'file': output.name, 'sha256': sha(output), 'bytes': output.stat().st_size},
              'blender': bpy.app.version_string,
              'modifier': {'type': 'LAPLACIANSMOOTH', 'strength': args.strength,
                           'iterations': args.iterations, 'volume_preserve': True, 'normalized': True,
                           'selection': 'Negative-Y ridge-facing emphasis with reduced opposite-face and central-bridge influence; source-coordinate editorial selection, not tissue segmentation or anatomical orientation proof.'},
              'before': before, 'after': after,
              'displacement_mm': {'max': max(distances), 'rms': math.sqrt(sum(x*x for x in distances)/len(distances)),
                                  'p95': sorted(distances)[int(.95 * (len(distances)-1))],
                                  'central_abs_x_lt5_max': max(d for d,p in zip(distances,original) if abs(p.x)<.005)},
              'relative_volume_change': after['signed_volume_mm3']/before['signed_volume_mm3']-1,
              'source_bounds_m': bounds(original), 'candidate_bounds_m': bounds(positions),
              'frame': 'Native source frame retained; temporary local-mm operation reversed before export.',
              'limits': ['Smoothing parameters are presentation choices at 1.5mm source-label scale; no measured anatomical tolerance.',
                         'Exact same-sample trachea context is external, so no new tracheal distance/collision validation.',
                         'No new internal anatomy, clinical or browser/runtime approval.']}
    (args.out/'build-record.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
