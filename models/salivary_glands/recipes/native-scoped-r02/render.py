import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);D=Path(a.build);O=Path(a.out)
expected={'context.glb': '1764c63011e698b9047d1abe79c647b8b609b7d8f9b18b740b17cdc65db930f8', 'glands-ducts.glb': 'a53134ec91195f5c42b8be4cde3536343e62857a7ecf5ab5d11bf3eba6ead515'}
for n,h in expected.items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h,'Model hash mismatch'
assert not O.exists(),'Output must be new';O.mkdir(parents=True);rows=[]
for phase in ['glands-ducts','context']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);G=D/f'{phase}.glb';bpy.ops.import_scene.gltf(filepath=str(G));pts=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);t=(lo+hi)*.5;s=max(hi-lo);sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=False;sc.render.resolution_x=1100;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX'
 for d,p in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
  bpy.ops.object.light_add(type='AREA',location=t+Vector(d)*s*4);o=bpy.context.object;o.data.energy=p*(s*4)**2;o.data.shape='DISK';o.data.size=s*2;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=s*1.15;sc.camera=cam
 for name,d in ([('front-source',(0,-1,0)),('oblique',(1,-1,.5))] if phase=='glands-ducts' else [('side-source',(1,0,0)),('inferior-source',(0,0,-1)),('superior-source',(0,0,1)),('oblique',(1,-1,.5))]):
  cam.location=t+Vector(d).normalized()*s*4;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();fn=f'{phase}-{name}.png';sc.render.filepath=str(O/fn);bpy.ops.render.render(write_still=True);rows.append({'file':fn,'glb_sha256':hashlib.sha256(G.read_bytes()).hexdigest(),'camera':list(cam.location),'target':list(t),'ortho_scale':cam.data.ortho_scale,'scope':'Native source-direction camera names; no validated clinical axis or registration'})
(O/'bindings.json').write_text(json.dumps(rows,indent=2))
