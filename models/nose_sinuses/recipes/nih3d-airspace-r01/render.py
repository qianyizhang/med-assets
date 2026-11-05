import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(a.baseline);C=Path(a.candidate);O=Path(a.out)
for f,h in [(S,'5f7be3713d4c45f137d972615d3b475f0c7c7256db157971458f104ed923a947'),(C,'3d8c4d56e09d72ae369c697d2bb9435cc3792f9dbe225e7d456ff58174a577be')]:
 if hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError('Hash mismatch')
if O.exists():raise ValueError('Output must be new')
O.mkdir(parents=True);rows=[]
for phase,F in [('baseline',S),('candidate',C)]:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(F));vs=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices];lo=Vector([min(v[i] for v in vs) for i in range(3)]);hi=Vector([max(v[i] for v in vs) for i in range(3)]);t=(lo+hi)/2;s=max(hi-lo);f=s/.15
 m=bpy.data.materials.new('Neutral diagnostic');m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(.42,.38,.33,1);b.inputs['Roughness'].default_value=.8
 for o in bpy.context.scene.objects:
  if o.type=='MESH':o.data.materials.clear();o.data.materials.append(m)
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=False;sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX'
 for di,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
  bpy.ops.object.light_add(type='AREA',location=t+Vector(di)*f);q=bpy.context.object;q.data.energy=power*f*f;q.data.shape='DISK';q.data.size=.4*f;q.rotation_euler=(t-q.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=s*1.18;cam.data.clip_end=s*100;sc.camera=cam
 views=[('oblique',(.7,-1,.3))] if phase=='baseline' else [('minusY',(0,-1,0)),('plusY',(0,1,0)),('plusX',(1,0,0)),('oblique',(.7,-1,.3))]
 for name,d in views:
  cam.location=t+Vector(d).normalized()*s*3;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();fn=f'{phase}-{name}.png';sc.render.filepath=str(O/fn);bpy.ops.render.render(write_still=True);rows.append({'file':fn,'input_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'camera':list(cam.location),'target':list(t),'ortho_scale':cam.data.ortho_scale,'scope':'source-coordinate view; independent display fit; no anatomical axis or physical scale claim','png_sha256':hashlib.sha256((O/fn).read_bytes()).hexdigest()})
(O/'bindings.json').write_text(json.dumps(rows,indent=2))
