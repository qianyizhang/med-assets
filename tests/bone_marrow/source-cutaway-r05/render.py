import bpy,json,sys,argparse,hashlib
from pathlib import Path
from mathutils import Vector
ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--out',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);B=Path(a.baseline);C=Path(a.candidate);O=Path(a.out)
for f,h in [(B,'c277ea5b96dfa8437e6ab80e3f5d69d87b95b3a5e0412ec521b3192377d95597'),(C,'7b21b74fb3712b2816801337bd4d0732ef8bb035a999ad36558b8235609cfe02')]:
 if hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError('Input hash mismatch')
if O.exists():raise ValueError('Output must be new')
O.mkdir(parents=True);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(C));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.render.resolution_x=1000;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.world.color=(.10,.10,.10);sc.view_settings.view_transform='AgX';t=Vector((.091,-.078,.761));s=.18;f=s/.15
for di,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
 bpy.ops.object.light_add(type='AREA',location=t+Vector(di)*f);o=bpy.context.object;o.data.energy=power*f*f;o.data.shape='DISK';o.data.size=.4*f;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam
rows=[]
for name,d in [('front',(0,-1,0)),('oblique',(.7,-1,.15)),('reverse',(-.6,1,.1)),('close',(0,-1,.1))]:
 tt=Vector((.091,-.078,.783)) if name=='close' else t;cam.data.ortho_scale=.13 if name=='close' else s;cam.location=tt+Vector(d).normalized();cam.rotation_euler=(tt-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{name}.png');bpy.ops.render.render(write_still=True);rows.append({'file':f'{name}.png','sha256':hashlib.sha256((O/f'{name}.png').read_bytes()).hexdigest(),'input_sha256':hashlib.sha256(C.read_bytes()).hexdigest(),'camera':list(cam.location),'target':list(tt),'ortho_scale':cam.data.ortho_scale})

(O/'bindings.json').write_text(json.dumps(rows,indent=2))
