import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--out',required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);S0=Path(args.source);C=Path(args.candidate);O=Path(args.out)
assert hashlib.sha256(S0.read_bytes()).hexdigest()=='d42747691a71eea955ca70371a404eecee082b63d1dd2f1787c09e903e2d90d2'
assert hashlib.sha256(C.read_bytes()).hexdigest()=='5d9f0f88ff8498f611aea583e080558691d592a3ce50c89ecb847cf18b4d1471'
O.mkdir(exist_ok=False)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.render.resolution_x=950;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX';target=Vector((0,.06,.04));span=.6;f=span/.15
for di,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
 bpy.ops.object.light_add(type='AREA',location=target+Vector(di)*f);o=bpy.context.object;o.data.energy=power*f*f;o.data.shape='DISK';o.data.size=.4*f;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam;rows=[]
for phase,S in [('before',S0),('after',C)]:
 for o in list(sc.objects):
  if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(S),merge_vertices=True);mat=bpy.data.materials.new('Matched neutral');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.44,.39,.34,1);bs.inputs['Roughness'].default_value=.8
 for o in sc.objects:
  if o.type=='MESH':o.data.materials.clear();o.data.materials.append(mat)
 for name,di in [('whole',(0,-1,0)),('side',(1,0,0)),('lower',(0,-1,.05)),('lower-oblique',(.65,-1,.1))]:
  t=Vector((0,.054,-.14)) if 'lower' in name else target;cam.data.ortho_scale=.225 if 'lower' in name else .62;cam.location=t+Vector(di).normalized()*2;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{phase}-{name}.png');bpy.ops.render.render(write_still=True);rows.append({'file':f'{phase}-{name}.png','glb_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'camera':list(cam.location),'target':list(t),'orthoscale':cam.data.ortho_scale})
(O/'bindings.json').write_text(json.dumps(rows,indent=2))
