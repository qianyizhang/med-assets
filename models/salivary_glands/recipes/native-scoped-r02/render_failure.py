import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--diagnostic-context',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);G=Path(a.diagnostic_context);O=Path(a.out)
assert hashlib.sha256(G.read_bytes()).hexdigest()=='8026bc00d8e19ac1b15d0c24375111f058a9bb182fc172fa1d30b1f6cb9e265c','Rejected-source diagnostic hash mismatch'
assert not O.exists(),'Output must be new';O.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(G))
keep=['Submandibular duct.l','Mylohyoid muscle.l']
for o in list(bpy.context.scene.objects):
 if o.type!='MESH' or o.get('source_object') not in keep:bpy.data.objects.remove(o,do_unlink=True)
assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==2
muscle=next(o for o in bpy.context.scene.objects if o.get('source_object')=='Mylohyoid muscle.l');duct=next(o for o in bpy.context.scene.objects if o.get('source_object')=='Submandibular duct.l');duct.data.materials[0].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.62,.32,.05,1)
t=Vector((.0227275,-.039177,1.519201));s=.027;sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX'
for d,p in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
 bpy.ops.object.light_add(type='AREA',location=t+Vector(d)*s*6);o=bpy.context.object;o.data.energy=p*(s*6)**2;o.data.shape='DISK';o.data.size=s*3;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=s;sc.camera=cam;rows=[]
for name,d in [('opaque-oblique',(1,1,1)),('opaque-reverse',(-1,-1,1)),('translucent-oblique',(1,1,1))]:
 if name.startswith('translucent'):muscle.data.materials[0].node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.23
 cam.location=t+Vector(d).normalized()*.3;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);rows.append({'file':name+'.png','camera':list(cam.location),'target':list(t),'ortho_scale':s,'translucent_display':name.startswith('translucent')})
(O/'bindings.json').write_text(json.dumps({'original_context_sha256':hashlib.sha256(G.read_bytes()).hexdigest(),'source_objects':keep,'geometry_changes':'None; otherobjects hidden for diagnostic; duct highlight and muscle transparency explicitly non-tissue appearance','scope':'Confirmed source defect: centerline passes through modeled mylohyoid; no proposed anatomy repair','views':rows},indent=2))
