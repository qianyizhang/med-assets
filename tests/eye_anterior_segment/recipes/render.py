import bpy,pathlib,json,hashlib,sys
from mathutils import Vector
D=pathlib.Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:];mode=args[0];p=D/'models'/(mode+'.glb');out=D/'reviews'/mode;out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(p));obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];by={o.name:o for o in obs};scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.world.color=(.11,.11,.11);scene.view_settings.view_transform='AgX'
pts=[o.matrix_world@v.co for o in obs for v in o.data.vertices];lo=Vector([min(v[i] for v in pts)for i in range(3)]);hi=Vector([max(v[i] for v in pts)for i in range(3)]);target=(lo+hi)/2;extent=max(hi-lo)
for delta,power in [((-2,-3,3),420),((3,-1,1),180),((0,3,2),280)]:
 bpy.ops.object.light_add(type='AREA',location=target+Vector(delta));l=bpy.context.object;l.data.energy=power;l.data.size=2;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=extent*1.25;scene.camera=cam;rows=[]
views=[('anterior',(0,-2,0),[]),('posterior',(0,2,0),[]),('oblique-posterior',(1,2,.6),[]),('side',(2,0,0),[]),('lens-zonules-processes',(0,2,.3),['VH_M_cornea_R','VH_M_iris_R','VH_M_ciliary_body_R','VH_M_ciliary_muscle_R']),('cornea-iris-lens',(2,-1,.4),['VH_M_ciliary_body_R','VH_M_ciliary_muscle_R','VH_M_ciliary_processes_R','VH_M_suspensory_ligament_of_lens_R'])]
if mode=='source-subset':views=views[:4]
for name,delta,hidden in views:
 for o in obs:o.hide_render=o.name in hidden
 cam.location=target+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);rows.append({'view':name,'cameraLocation':list(cam.location),'target':list(target),'orthoScaleM':cam.data.ortho_scale,'visibleNodes':[o.name for o in obs if not o.hide_render],'hiddenNodes':hidden,'file':name+'.png','sha256':hashlib.sha256((out/(name+'.png')).read_bytes()).hexdigest()})
(out/'render-manifest.json').write_text(json.dumps({'exportSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'renderer':'Blender '+bpy.app.version_string+' Cycles CPU 48 samples no denoising AgX','sourceImportedInEmptyScene':True,'geometryAtNativeHraCoordinates':True,'views':rows},indent=2))
