import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);G=Path(a.candidate);O=Path(a.out)
assert hashlib.sha256(G.read_bytes()).hexdigest()=='c44d35e13be11d2fb35141747d819d4609a45ca0a5527c89e1015618d17cab70','Candidate hash mismatch'
assert not O.exists(),'Output must be new';O.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(G));pts=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);t=(lo+hi)*.5;s=max(hi-lo);sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX'
for d,p in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
 bpy.ops.object.light_add(type='AREA',location=t+Vector(d)*s*4);o=bpy.context.object;o.data.energy=p*(s*4)**2;o.data.shape='DISK';o.data.size=s*2;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=s*1.25;sc.camera=cam;rows=[]
for name,d in [('minus-y',(0,-1,0)),('plus-y',(0,1,0)),('side',(1,0,0)),('oblique',(1,-1,.4)),('inferior-source',(0,0,-1))]:
 cam.location=t+Vector(d).normalized()*s*4;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);rows.append({'file':name+'.png','camera':list(cam.location),'target':list(t),'ortho_scale':cam.data.ortho_scale})
(O/'bindings.json').write_text(json.dumps({'sha256':hashlib.sha256(G.read_bytes()).hexdigest(),'bounds':[list(lo),list(hi)],'views':rows,'scope':'Exact export fresh import; native coordinate directions not anatomically validated axes; source geometry unchanged, materials/visibility changed'},indent=2))
