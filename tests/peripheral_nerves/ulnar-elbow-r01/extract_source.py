"""Read-only source screen: no canonical changes or anatomical route repair."""
import bpy, hashlib, json
from pathlib import Path
from mathutils import Vector

import argparse, sys
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
SOURCE = Path(a.source)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == '9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
OUT = Path(a.out)
OUT.mkdir(exist_ok=False)
names = ['Ulnar nerve.r', 'Humerus.r', 'Ulna.r', 'Radius.r']
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(SOURCE), link=False) as (a, b):
    assert all(n in a.objects for n in names)
    b.objects = names
originals = list(b.objects)
for old in originals:
    bpy.context.collection.objects.link(old)
    old.hide_set(False)
    old.hide_viewport = old.hide_render = False
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
rows = []
for old in originals:
    evaluated = old.evaluated_get(dg)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=dg)
    copy = bpy.data.objects.new(old.name + ' diagnostic', mesh)
    copy.matrix_world = old.matrix_world.copy()
    bpy.context.collection.objects.link(copy)
    copy['source_object'] = old.name
    copy['scope'] = 'Unmodified evaluated source geometry, native frame; source-only diagnostic'
    color = (.66, .36, .035) if old.type == 'CURVE' else (.40, .45, .49)
    m = bpy.data.materials.new(old.name + ' illustrative diagnostic material')
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = .8
    mesh.materials.clear()
    mesh.materials.append(m)
    row = {'name':old.name, 'type':old.type, 'vertices':len(mesh.vertices), 'faces':len(mesh.polygons), 'matrix_world':[list(v) for v in old.matrix_world]}
    if old.type == 'CURVE':
        row['curve'] = {'bevel_depth':old.data.bevel_depth, 'bevel_resolution':old.data.bevel_resolution, 'resolution_u':old.data.resolution_u, 'splines':[{'type':s.type, 'points':len(s.bezier_points), 'cyclic':s.use_cyclic_u} for s in old.data.splines]}
    rows.append(row)
for old in originals:
    bpy.data.objects.remove(old, do_unlink=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'native-elbow.glb'), export_format='GLB', export_animations=False, export_extras=True)
