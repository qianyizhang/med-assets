import bpy,pathlib,json,hashlib,sys,argparse
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--source',required=True);ap.add_argument('--output',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);C=pathlib.Path(a.candidate);O=pathlib.Path(a.output);S=pathlib.Path(a.source);assert hashlib.sha256(S.read_bytes()).hexdigest()=='3408ca8e8f394dd268b1dbeafdc59fdc8cc104c0976628e455dbc070ae0a7993';assert hashlib.sha256(C.read_bytes()).hexdigest()=='8820a14b820239c0ea53a3597ad7731b7c66eb41f05b197fde2e90ee08fb47e4';O.mkdir(exist_ok=False)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.resolution_x=1000;sc.render.resolution_y=850;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX'
old=json.load(open(P/'baseline-cameras.json'));target=Vector(old['cameras'][0]['target']);span=old['cameras'][0]['ortho_scale']/1.12;f=span/.15
for di,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
 bpy.ops.object.light_add(type='AREA',location=target+Vector(di)*f);l=bpy.context.object;l.data.energy=power*f*f;l.data.shape='DISK';l.data.size=.4*f;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam;rows=[]
for phase,file in [('before',S),('after',C)]:
 for o in list(sc.objects):
  if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(file),merge_vertices=True)
 mat=bpy.data.materials.new('Matched diagnostic');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.44,.39,.34,1);bs.inputs['Roughness'].default_value=.8
 for o in sc.objects:
  if o.type=='MESH':o.data.materials.clear();o.data.materials.append(mat)
 for name,di in [('whole',(.8,-1,.3)),('close',(0,-1,.1)),('rotated-close',(.6,-1,-.4)),('opposite-close',(0,1,.1))]:
  t=Vector((.042,.008,.068)) if 'close' in name else target;cam.data.ortho_scale=.045 if 'close' in name else span*1.12;cam.location=t+Vector(di).normalized()*span*4;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{phase}-{name}.png');bpy.ops.render.render(write_still=True);rows.append({'file':f'{phase}-{name}.png','glb_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'position':list(cam.location),'target':list(t),'quaternion':list(cam.rotation_euler.to_quaternion()),'ortho_scale':cam.data.ortho_scale})
(O/'bindings.json').write_text(json.dumps(rows,indent=2))
