import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(a.baseline);O=Path(a.out)
assert hashlib.sha256(S.read_bytes()).hexdigest()=='865717807c724b375f25fdc745e231525730ed80a374042a1e4f89cf32b8b4b6'
assert not O.exists(),'Output must be new';O.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(S));objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@v.co for o in objs for v in o.data.vertices];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);t=(lo+hi)*.5;size=max(hi-lo);sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.render.resolution_x=1100;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.world.color=(.10,.10,.10);sc.view_settings.view_transform='AgX'
for d,p in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
 bpy.ops.object.light_add(type='AREA',location=t+Vector(d)*size*4);o=bpy.context.object;o.data.energy=p*(size*4)**2;o.data.shape='DISK';o.data.size=size*2;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=size*1.12;cam.location=t+Vector((0,-size*4,0));cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(O/'whole.png');bpy.ops.render.render(write_still=True)
(O/'bindings.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'bounds':[list(lo),list(hi)],'camera':list(cam.location),'target':list(t),'ortho_scale':cam.data.ortho_scale,'scope':'Native authored baseline coordinate view; different model/frame than source candidate; not registered comparison'},indent=2))
