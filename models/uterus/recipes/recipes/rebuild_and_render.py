import bpy,pathlib,json,hashlib,shutil,math
from mathutils import Vector
D=pathlib.Path(__file__).resolve().parents[1];S=D/'source/hra'
SETS={'uterus_hra':['VH_F_Uterus.glb']}
for organ,files in SETS.items():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);M=D/'models'/organ;E=M/'exports/source-candidate-02';E.mkdir(parents=True,exist_ok=True);R=D/'reviews'/organ/'source-candidate-02';P=R/'screenshots';P.mkdir(parents=True,exist_ok=True);(M/'source').mkdir(exist_ok=True)
 for f in files:bpy.ops.import_scene.gltf(filepath=str(S/f));shutil.copy(S/f,M/'source'/f)
 src={o.name:[[min((o.matrix_world@v.co)[i] for v in o.data.vertices) for i in range(3)],[max((o.matrix_world@v.co)[i] for v in o.data.vertices) for i in range(3)]] for o in bpy.context.scene.objects if o.type=='MESH'}
 
 for ob in list(bpy.context.scene.objects):
  if ob.type=='MESH' and any(t in ob.name for t in ['anterior_wall_of_uterus','posterior_wall_of_uterus']):bpy.data.objects.remove(ob,do_unlink=True)
 glb=E/(organ+'_native_frame.glb')
 if False:shutil.copy(S/files[0],glb)
 else:
  bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',export_extras=True)
 # Reimport exact delivered bytes, preserving all original materials and transforms.
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(glb));obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
 for o in obs:
  coords=[o.matrix_world@v.co for v in o.data.vertices];bb=[[min(v[i] for v in coords) for i in range(3)],[max(v[i] for v in coords) for i in range(3)]];err=max(abs(a-b) for row,ref in zip(bb,src[o.name]) for a,b in zip(row,ref));checks.append({'name':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'source_bounds_max_error_m':err,'all_finite':all(math.isfinite(x) for v in coords for x in v),'original_materials_retained':[m.name for m in o.data.materials]})
 sha=hashlib.sha256(glb.read_bytes()).hexdigest();(R/'exact-export-tests.json').write_text(json.dumps({'sha256':sha,'source_files':[{'file':f,'sha256':hashlib.sha256((S/f).read_bytes()).hexdigest()} for f in files],'expected_source_subset_present':len(src)-2==len(checks),'excluded_original_nodes':['VH_F_anterior_wall_of_uterus','VH_F_posterior_wall_of_uterus'],'checks':checks,'geometry_change':'Only excluded2nested wall solids overlapping exterior region surfaces; retained vertex positions/materials unchanged, no cavity created','frame':'HRA native GLB metres; x left y superior z anterior (named breast identity test), no BP3D registration','visual':'unreviewed','runtime':'untested'},indent=2))
 (M/'candidate-manifest.json').write_text(json.dumps({'schemaVersion':1,'id':organ+'_r01','logicalReplacementFor':{'uterus_hra':'draft_uterus','prostate_hra':'draft_prostate','breasts_hra':'draft_breasts'}[organ],'file':str(glb.relative_to(D)),'sha256':sha,'license':'CC-BY-4.0','status':'unreviewed','sourceFrame':'HRA native reference organ frame','isolatedViewerOnly':True,'defaultWholeBodyReplacement':False},indent=2))
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.world.color=(.1,.1,.1);coords=[o.matrix_world@v.co for o in obs for v in o.data.vertices];lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)]);target=(lo+hi)/2;span=max(hi-lo)*1.3
 for loc,power,size in [((-1,-2,2),180,2),((1,-1,1),100,2),((0,2,2),150,2)]:
  bpy.ops.object.light_add(type='AREA',location=target+Vector(loc));l=bpy.context.object;l.data.energy=power;l.data.size=size;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=span;scene.camera=cam
 views=[('front',(0,-2,0)),('back',(0,2,0)),('left',(2,0,0)),('oblique',(1,-2,.4)),('superior',(0,0,2))]
 for name,delta in views:
  cam.location=target+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(P/(name+'.png'));bpy.ops.render.render(write_still=True)
 for name,delta in [('inferior',(0,0,-2)),('posterior-oblique',(1,2,-.3))]:
  cam.location=target+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(P/(name+'.png'));bpy.ops.render.render(write_still=True)
 (R/'layer-visibility.json').write_text(json.dumps({'display_selection':'Outer named region surfaces; redundant anterior/posterior wall solids omitted','excluded_source_nodes':['VH_F_anterior_wall_of_uterus','VH_F_posterior_wall_of_uterus'],'not_a_cutaway':'No cavity claimed; omitted overlapping nested solids only'},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(E/(organ+'_review_scene.blend')));print('READY',organ,sha,flush=True)
