"""Matched, clean GLB reimport views. PNGs remain local; no upload side effects."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--baseline', type=Path, required=True)
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--phase', choices=('both','before','current'), default='both')
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
a.out.mkdir(exist_ok=False, parents=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s = bpy.context.scene
s.render.engine = 'CYCLES'; s.cycles.samples = 24; s.cycles.use_denoising = False
s.render.resolution_x = 900; s.render.resolution_y = 1000; s.render.resolution_percentage = 100
s.world.color = (.13,.13,.13); s.view_settings.view_transform = 'AgX'
target = Vector((0,.06,.04)); f = .6/.15
for direction, power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
    bpy.ops.object.light_add(type='AREA',location=target+Vector(direction)*f)
    light = bpy.context.object; light.data.energy = power*f*f
    light.data.shape='DISK'; light.data.size = .4*f
    light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(); camera=bpy.context.object; camera.data.type='ORTHO'; s.camera=camera
views = [
    ('whole', (0,.06,.04), (.45,-1,.12), .62),
    ('pair', (.017,.066,.195), (.15,-1,.65), .056),
    ('lower', (0,.054,-.14), (.65,-1,.1), .225),
]
rows=[]
for phase, path in [('before',a.baseline),('current',a.candidate)]:
    if a.phase != 'both' and phase != a.phase: continue
    for ob in list(s.objects):
        if ob.type=='MESH': bpy.data.objects.remove(ob,do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=str(path),merge_vertices=True)
    mat=bpy.data.materials.new('Matched neutral'); mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(.44,.39,.34,1)
    bs.inputs['Roughness'].default_value=.8
    for ob in s.objects:
        if ob.type=='MESH': ob.data.materials.clear(); ob.data.materials.append(mat)
    for name, t, direction, scale in views:
        target=Vector(t); camera.data.ortho_scale=scale
        camera.location=target+Vector(direction).normalized()*2
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        path_out=a.out/f'{phase}-{name}.png'; s.render.filepath=str(path_out)
        bpy.ops.render.render(write_still=True)
        rows.append({'file':path_out.name,'sha256':hashlib.sha256(path_out.read_bytes()).hexdigest(),
                     'artifact_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'camera':list(camera.location),'target':t,'orthoscale':scale,
                     'material':'matched neutral','samples':24,'pixels':[900,1000]})
        (a.out/'render-bindings.json').write_text(json.dumps(rows,indent=2)+'\n')
