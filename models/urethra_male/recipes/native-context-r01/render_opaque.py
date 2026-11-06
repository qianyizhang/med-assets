import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);opts=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);P=opts.work;O=P/'r01/renders';O.mkdir(exist_ok=False);rows=[]
assert hashlib.sha256((P/'r01/context.glb').read_bytes()).hexdigest()=='d2d88c936287f4ea5978aba1f17e86975c587a102e498595dd7a58aa07c269e7'
for phase in ['urethra','context']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);G=P/'r01'/f'{phase}.glb';bpy.ops.import_scene.gltf(filepath=str(G));pts=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);t=(lo+hi)*.5;s=max(hi-lo);sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=False;sc.render.resolution_x=1100;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX'
 for d,p in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
  bpy.ops.object.light_add(type='AREA',location=t+Vector(d)*s*4);o=bpy.context.object;o.data.energy=p*(s*4)**2;o.data.shape='DISK';o.data.size=s*2;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=s*1.15;sc.camera=cam
 for name,d in [('side-source',(1,0,0)),('oblique',(1,-1,.4))]:
  cam.location=t+Vector(d).normalized()*s*4;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();fn=f'{phase}-{name}.png';sc.render.filepath=str(O/fn);bpy.ops.render.render(write_still=True);rows.append({'file':fn,'glb_sha256':hashlib.sha256(G.read_bytes()).hexdigest(),'camera':list(cam.location),'target':list(t),'ortho_scale':cam.data.ortho_scale,'scope':'Native source-direction camera names; no validated clinical axis or registration'})
(O/'bindings.json').write_text(json.dumps(rows,indent=2))
