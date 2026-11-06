"""Blender: neutral, unreviewed display previews of exact existing GLB inputs."""
import bpy, json, hashlib, math, os
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[1]
ROOT=Path(os.environ.get("MED_ASSETS_REPO", OUT.parents[1])).expanduser().resolve()
DEST=OUT/'.local/preview-renders';DEST.mkdir(parents=True,exist_ok=True)
d=json.loads((OUT/'app/src/data.json').read_text())
rows=d['queries']['model_survey']['rows']+d['queries']['products']['rows']
jobs=[]
for id in ['lung_left','lung_right','vertebrae_L3','body-atlas','trachea','spinal_cord']:
 r=next(r for r in rows if r['id']==id)
 ms=r['media']
 if id=='body-atlas':ms=[m for m in ms if not m['path'].endswith(('heart_detailed.glb','bronchial_tree.glb'))]
 elif id=='trachea':ms=[m for m in ms if m['path'].endswith('trachea-cutaway.glb')]
 elif id=='spinal_cord':ms=[m for m in ms if '/authored-roots-r04/' in m['path']]
 jobs.append((id,ms))
old_receipt=json.loads((DEST/'render-bindings.json').read_text()) if (DEST/'render-bindings.json').exists() else []
receipt=[]
for id,ms in jobs:
 if all((DEST/f'{id}-{j}.png').exists() for j in range(2)):
  previous=[x for x in old_receipt if x['id']==id]
  expected=[{k:m[k] for k in ['path','sha256']} for m in ms]
  if len(previous)!=2 or any(x['inputs']!=expected or hashlib.sha256((DEST/x['image']).read_bytes()).hexdigest()!=x.get('imageSha256') for x in previous):
   raise RuntimeError('Existing preview bindings differ; preserve the old bundle and render into a fresh output directory')
  receipt.extend(previous)
  continue
 bpy.ops.wm.read_factory_settings(use_empty=True)
 for m in ms:
  data=(ROOT/m['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==m['sha256']
  bpy.ops.import_scene.gltf(filepath=str(ROOT/m['path']))
 scene=bpy.context.scene
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=False
 scene.render.resolution_x=1100;scene.render.resolution_y=900;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('Preview world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.06,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
 mat=bpy.data.materials.new('Neutral preview material');mat.diffuse_color=(.49,.57,.64,1);mat.use_nodes=True
 bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.49,.57,.64,1);bs.inputs['Roughness'].default_value=.65
 scene.view_layers[0].material_override=mat
 meshes=[o for o in scene.objects if o.type=='MESH'];assert meshes
 pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
 lo=Vector([min(p[k] for p in pts) for k in range(3)]);hi=Vector([max(p[k] for p in pts) for k in range(3)]);center=(lo+hi)/2;extent=max(hi-lo)
 def light(name,v,power,size):
  ld=bpy.data.lights.new(name,'AREA');ld.energy=power*extent*extent;ld.shape='DISK';ld.size=size*extent
  ob=bpy.data.objects.new(name,ld);scene.collection.objects.link(ob);ob.location=center+Vector(v)*extent;ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
 light('Soft key',(2,-3,4),450,3);light('Fill',(-3,-1,1),200,4);light('Rim',(1,3,3),300,3)
 camd=bpy.data.cameras.new('Preview camera');cam=bpy.data.objects.new('Preview camera',camd);scene.collection.objects.link(cam);scene.camera=cam;camd.type='ORTHO';camd.clip_start=max(extent*.0001,1e-5);camd.clip_end=extent*30
 for j,direction in enumerate([(1.5,-4,1.2),(-2,3,1)]):
  cam.location=center+Vector(direction).normalized()*extent*5;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  inv=cam.matrix_world.inverted();bpy.context.view_layer.update();inv=cam.matrix_world.inverted();pro=[inv@p for p in pts]
  spanx=max(p.x for p in pro)-min(p.x for p in pro);spany=max(p.y for p in pro)-min(p.y for p in pro)
  mid=Vector(((max(p.x for p in pro)+min(p.x for p in pro))/2,(max(p.y for p in pro)+min(p.y for p in pro))/2,0))
  cam.location+=cam.rotation_euler.to_matrix()@mid
  camd.ortho_scale=max(spanx,spany*(1100/900))*1.18
  scene.render.filepath=str(DEST/f'{id}-{j}.png');bpy.ops.render.render(write_still=True)
  receipt.append({'id':id,'image':f'{id}-{j}.png','imageSha256':hashlib.sha256((DEST/f'{id}-{j}.png').read_bytes()).hexdigest(),'inputs':[{k:m[k] for k in ['path','sha256']} for m in ms],'engine':'Cycles CPU, 64 samples, neutral material override','blender':bpy.app.version_string,'scope':'Fresh illustrative inventory preview, not replay of prior review pixels or new visual/anatomy/runtime approval'})
(DEST/'render-bindings.json').write_text(json.dumps(receipt,indent=2))
