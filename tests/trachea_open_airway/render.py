"""Matched exact-GLB reimport renders for the r06 authored teaching derivative."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--current-only',action='store_true');p.add_argument('--views',default='whole,bifurcation,proximal,branch-outlet');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(exist_ok=False,parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False
s.render.resolution_x=900;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.world.color=(.12,.12,.12);s.view_settings.view_transform='AgX'
target=Vector((-.003,.012,.125));f=.135/.15
for d,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
 bpy.ops.object.light_add(type='AREA',location=target+Vector(d)*f);o=bpy.context.object;o.data.energy=power*f*f;o.data.shape='DISK';o.data.size=.4*f;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';s.camera=camera
record=json.loads((a.candidate_dir/'build-record.json').read_text());centers=next(x for x in record['variants'] if x['variant']=='open')['opening_centers'];outlet=max(centers,key=lambda v:v[0])
views=[('whole',(-.003,.012,.125),(.3,-1,.3),.145),('bifurcation',(-.003,.025,.088),(.12,-1,.45),.079),('proximal',(0,-.003,.172),(.4,-.5,1),.045),('branch-outlet',outlet,(1,-.18,.18),.035)]
rows=[]
phases=[('baseline',a.baseline),('open',a.candidate_dir/'trachea-open.glb'),('cutaway',a.candidate_dir/'trachea-cutaway.glb')]
for phase,path in phases:
 if a.current_only and phase=='baseline':continue
 for ob in list(s.objects):
  if ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(path),merge_vertices=True)
 if phase=='baseline':
  for ob in s.objects:
   if ob.type!='MESH':continue
   m=bpy.data.materials.new('Matched external tissue');m.use_nodes=True
   bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*((.73,.66,.51) if ob.name.startswith('Authored') else (.55,.43,.30)),1);bs.inputs['Roughness'].default_value=.8
   ob.data.materials.clear();ob.data.materials.append(m)
 for name,t,d,scale in views:
  if name not in a.views.split(','):continue
  if phase=='cutaway' and name in ('proximal','branch-outlet'):continue
  target=Vector(t);camera.location=target+Vector(d).normalized()*.6;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
  output=a.out/f'{phase}-{name}.png';s.render.filepath=str(output);bpy.ops.render.render(write_still=True)
  rows.append({'file':output.name,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'artifact_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera':list(camera.location),'target':t,'orthoscale':scale,'pixels':[900,1000],'samples':32,'material_note':'Matched external/band colors. Newly authored inner shell and editorial rims have distinct illustrative colors, not tissue segmentation.'})
  (a.out/'render-bindings.json').write_text(json.dumps(rows,indent=2)+'\n')
