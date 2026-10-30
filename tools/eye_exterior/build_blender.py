"""Evaluate only the pinned native eye surfaces; do not run source scripts."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb

PIN = '9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
SIZE = 306838281
STEMS = ('Cornea', 'Sclera', 'Inferior oblique muscle', 'Inferior rectus muscle',
         'Lateral rectus muscle', 'Medial rectus muscle', 'Superior oblique muscle',
         'Superior rectus muscle', 'Trochlea of superior oblique muscle', 'Optic nerve (II)')
NAMES = sorted(stem+'.'+side for stem in STEMS for side in ('l', 'r'))


def source_hash(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def collect(source, reference):
    if source.stat().st_size != SIZE or source_hash(source) != PIN:
        raise ValueError('Wrong pinned source member')
    if bpy.app.version_string != '4.3.2':
        raise ValueError('Replay requires Blender 4.3.2')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    with bpy.data.libraries.load(str(source), link=False) as (available, chosen):
        assert set(NAMES) <= set(available.objects)
        chosen.objects = NAMES
    for obj in chosen.objects:
        bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    objects = []; bindings = []; metadata = []
    for src in chosen.objects:
        expected = next(r for r in reference['objects'] if r['name'] == src.name)
        mesh = bpy.data.meshes.new_from_object(src.evaluated_get(deps), preserve_all_data_layers=True, depsgraph=deps)
        mesh.calc_loop_triangles()
        matrix = [list(row) for row in src.matrix_world]
        world = [src.matrix_world @ v.co for v in mesh.vertices]
        packed = b''.join(struct.pack('<fff', *p) for p in world)
        packed += b''.join(struct.pack('<III', *t.vertices) for t in mesh.loop_triangles)
        world_hash = glb.sha(packed)
        assert world_hash == expected['worldGeometrySha256'], src.name
        assert matrix == expected['matrixWorld']
        assert len(mesh.vertices) == expected['evaluatedVertices']
        assert len(mesh.loop_triangles) == expected['evaluatedTriangles']
        positions = []; normals = []; indices = []; split = {}
        for triangle in mesh.loop_triangles:
            for loop in triangle.loops:
                vertex = mesh.loops[loop].vertex_index
                normal = tuple(mesh.corner_normals[loop].vector)
                key = (vertex, normal)
                if key not in split:
                    split[key] = len(positions)
                    positions.append(list(mesh.vertices[vertex].co)); normals.append(list(normal))
                indices.append(split[key])
        item = {'name': src.name, 'sourceType': src.type, 'sourceParent': expected['parent'],
                'matrixNative': matrix, 'positions': positions, 'normals': normals, 'indices': indices}
        objects.append(item)
        bindings.append({key: item[key] for key in ('name', 'sourceType', 'sourceParent', 'matrixNative')} | {
            'sourceEvaluatedVertices': len(mesh.vertices), 'exportVertices': len(positions),
            'triangles': len(indices)//3, 'nativeTriangleCornersSha256': glb.corners_sha(positions, normals, indices),
            'sourceEvaluatedWorldGeometrySha256': world_hash,
            'nativeBounds': [[min(p[a] for p in world) for a in range(3)], [max(p[a] for p in world) for a in range(3)]],
            'displayRole': glb.role_for(src.name)})
        metadata.append({k: expected[k] for k in ('name', 'type', 'parent', 'matrixWorld', 'dataName',
                         'modifiers', 'materials', 'rawVertices', 'sourceCurve') if k in expected})
    assert len(objects) == 20 and sum(b['triangles'] for b in bindings) == 35884
    assert source_hash(source) == PIN
    return objects, bindings, metadata


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--reference', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise ValueError('Output directory must be new')
    reference = json.loads(args.reference.read_text())
    objects, bindings, metadata = collect(args.source, reference)
    source = {'member': 'Z-Anatomy/Startup.blend', 'bytes': SIZE, 'sha256': PIN,
              'archiveCommit': 'bb293be456f6d2245191f37752d14ec76894740d'}
    data = glb.make(objects, source)
    checks = glb.verify(data, bindings)
    assert glb.make(objects, source) == data
    args.output.mkdir(parents=True)
    (args.output/'eye-exterior-courses.glb').write_bytes(data)
    records = {'bindings.json': {'source': source, 'objects': bindings},
               'source-materials.json': {'source': source, 'objects': metadata,
                   'use': 'Raw source material metadata retained for provenance only. Action-labelled shaders are not exported or interpreted as muscle function.'},
               'build-receipt.json': {'source': source, 'artifact': {'file': 'eye-exterior-courses.glb', 'bytes': len(data), 'sha256': glb.sha(data)},
                   'blender': bpy.app.version_string, 'sourceBytesUnchanged': True, 'autoExec': False,
                   'triangles': sum(b['triangles'] for b in bindings), 'decodedVerification': checks,
                   'deterministicSecondEncoding': True,
                   'geometry': 'Exact source-evaluated local triangle corners and normals. Native world matrices recovered exactly from the common glTF basis conversion. Existing source modifier/curve evaluation retained.',
                   'hierarchy': '20 static root nodes retain source world matrices and source-parent names. Annotation/font parents are not exported; no rig or animation is transferred.',
                   'scenes': 'Source R is default; Source L is a separate selectable scene. All 20 source surfaces remain in the GLB. No bilateral pathway claim.',
                   'units': 'Native source coordinate units; no independently calibrated physical-size claim.'}}
    for name, record in records.items():
        (args.output/name).write_text(json.dumps(record, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(records['build-receipt.json']['artifact']))


if __name__ == '__main__':
    main()
