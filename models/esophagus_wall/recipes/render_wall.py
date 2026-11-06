import bpy,pathlib,hashlib,json,bmesh
from mathutils import Vector
import argparse,sys
parser=argparse.ArgumentParser(description='Render exact GLB into a NEW output directory only.')
parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
D=pathlib.Path(a.output).resolve();D.mkdir(parents=True,exist_ok=False);P=pathlib.Path(a.input).resolve()
params=json.loads(P.with_name('parameters.json').read_text());L=params['length_m'];R=params['adventitia_outer_radius_m'];(D/'parameters.json').write_text(json.dumps(params,indent=2))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(P));obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(obs)==5
records=[]
for o in obs:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8);bm.normal_update();records.append({'node':o.name,'finite':all(__import__('math').isfinite(x) for v in bm.verts for x in v.co),'boundary_edges_welded':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges_welded':sum(not e.is_manifold for e in bm.edges),'positive_volume':bm.calc_volume(signed=True)>0,'zero_area_faces':sum(f.calc_area()<=1e-16 for f in bm.faces)});bm.free()
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=96;sc.cycles.use_denoising=False;sc.cycles.seed=17;sc.render.resolution_x=1000;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.world.color=(.12,.12,.12);sc.view_settings.view_transform='AgX';sc.render.image_settings.file_format='PNG';target=Vector((0,0,L/2));f=.2*max(L/.045,R/.0118)
for delta,power in [((-.6,-.7,.8),20),((.5,-.3,.1),9),((0,.5,.5),14)]:
 bpy.ops.object.light_add(type='AREA',location=target+Vector(delta)*f);l=bpy.context.object;l.data.energy=power*f*f;l.data.shape='DISK';l.data.size=.4*f;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam;cams=[]
for name,d,scale in [('oblique',(.85,-1.7,1.1),.067),('longitudinal',(0,-1,.10),.060),('cross-section',(0,0,1),.033)]:
 cam.location=target+Vector(d).normalized()*.3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale*(R/.0118 if name=='cross-section' else max(L/.045,R/.0118));sc.render.filepath=str(D/(name+'.png'));bpy.ops.render.render(write_still=True);cams.append({'name':name,'position':list(cam.location),'target':list(target),'ortho_scale':cam.data.ortho_scale})
(D/'reimport-receipt.json').write_text(json.dumps({'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'clean_scene_reimport':True,'objects':records,'cameras':cams,'render':'Blender 4.3.2 Cycles CPU, 96 samples, no denoising, 1000x1100','scope':'Finite/volume and 1e-8 m tolerance-weld edge diagnostics plus rendered layer readability only. Not exact-index manifold proof, tissue anatomy validation or browser runtime.'},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(D/'reimport-review.blend'),compress=True)
