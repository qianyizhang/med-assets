"""Read-only review of the exact original HRA GLB; no export/repair/recolor.
Blender --background --factory-startup --disable-autoexec --python THIS.py
"""
import bpy, pathlib, json, hashlib, math, shutil, struct, collections
from mathutils import Vector
import argparse, sys
parser=argparse.ArgumentParser()
parser.add_argument('--model', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--checks-only', action='store_true')
options=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
E=pathlib.Path(options.model).resolve(); R=pathlib.Path(options.output).resolve()
if R.exists(): raise RuntimeError('Use a new output directory; never overwrite retained evidence')
R.mkdir(parents=True); (R/'screenshots').mkdir()
assert hashlib.sha256(E.read_bytes()).hexdigest()=='7b047002cbb1dc06f37baa441783390d76cdb444b6144d6caa623923707953fd'
sha=hashlib.sha256(E.read_bytes()).hexdigest()
blob=E.read_bytes(); n,kind=struct.unpack_from('<II',blob,12); doc=json.loads(blob[20:20+n]); assert kind==0x4e4f534a
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(E))
obs=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name)
labels={
 'Yao_afferent_lymphatic_vessel':('1','Afferent lymphatic vessel'),
 'Yao_capsule_of_lymph_node':('2','Capsule of lymph node'),
 'Yao_follicles':('3','Lymph node follicles'),
 'Yao_efferent_lymph_node':('4','Efferent lymphatic vessel'),
 'Yao_medulla_of_lymph_node':('5','Medulla of lymph node'),
 'Yao_paracortex':('6','Paracortex / T-cell domain'),
 'Yao_blood_vasculature':('7','Source vascular network (label conflict)')}
assert set(labels)=={o.name for o in obs}
rows=[]
for o in obs:
 vs=[o.matrix_world@v.co for v in o.data.vertices];o.data.calc_loop_triangles()
 edges=collections.Counter();unique={};remap=[]
 for v in o.data.vertices:
  key=tuple(v.co);unique.setdefault(key,len(unique));remap.append(unique[key])
 parent=list(range(len(unique)))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for p in o.data.polygons:
  ids=[remap[i] for i in p.vertices]
  for i,a in enumerate(ids):
   b=ids[(i+1)%len(ids)];edges[tuple(sorted((a,b)))]+=1
   aa,bb=find(a),find(b)
   if aa!=bb:parent[bb]=aa
 areas=[(vs[t.vertices[1]]-vs[t.vertices[0]]).cross(vs[t.vertices[2]]-vs[t.vertices[0]]).length/2 for t in o.data.loop_triangles]
 raw=next(n for n in doc['nodes'] if n.get('name')==o.name)
 rows.append({'source_node':o.name,'key':labels[o.name][0],'display_label':labels[o.name][1],
 'provider_extras':raw.get('extras',{}),'vertices':len(vs),'triangles':len(areas),
 'all_positions_finite':all(math.isfinite(a) for v in vs for a in v),
 'all_vertex_normals_finite':all(math.isfinite(a) for v in o.data.vertices for a in v.normal),
 'zero_area_triangles':sum(a==0 for a in areas),'triangles_below_1e-20_m2':sum(a<1e-20 for a in areas),
 'exact_tuple_boundary_edges':sum(v==1 for v in edges.values()),
 'exact_tuple_non_two_incident_edges':sum(v!=2 for v in edges.values()),
 'exact_tuple_connected_components':len({find(i) for i in range(len(unique))}),
 'bounds_blender_import_m':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],
 'materials':[m.name for m in o.data.materials]})
json.dump({'source_glb_sha256':sha,'export_glb_sha256':sha,'source_and_export_byte_identical':True,
 'expected_meshes':7,'actual_meshes':len(obs),'exact_named_object_match':True,
 'geometry_materials_transforms_extras':'Original artifact bytes unchanged; Blender review import only',
 'status':'TECHNICAL_INGEST_OK_WITH_SOURCE_TOPOLOGY_AND_LABEL_WARNINGS',
 'topology_method':'Per-object explicit exact float-tuple equality remap for counts only. No mutation, no BMesh merge. Connected components use remapped vertex adjacency.',
 'not_tested':['self intersections','anatomical correctness','histology validity','flow continuity','patient normative size','browser runtime','assembly registration'],
 'objects':rows},open(R/'exact-export-tests.json','w'),indent=2)
json.dump({'sha256':sha,'labels':rows,'provider_label_conflict':{'node':'Yao_blood_vasculature','extras_label':'Lymph vasculature','ontology':'UBERON:0004536','policy':'Do not silently identify this as either blood or lymph network. Retain source fields and show unresolved warning.'}},open(R/'layer-key.json','w'),indent=2)
if options.checks_only: print('EXACT_SOURCE_CHECKS_COMPLETE'); sys.exit(0)
v=[o.matrix_world@x.co for o in obs for x in o.data.vertices]
ct=Vector([(min(x[i] for x in v)+max(x[i] for x in v))/2 for i in range(3)])
span=max(max(x[i] for x in v)-min(x[i] for x in v) for i in range(3))*1.18
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=False
s.render.resolution_x=1100;s.render.resolution_y=900;s.render.resolution_percentage=100
s.world.color=(.045,.045,.045)
for delta,power in [((-1,-2,2),130),((1,-1,-1),90),((0,2,1),110)]:
 bpy.ops.object.light_add(type='AREA',location=ct+Vector(delta));l=bpy.context.object;l.data.energy=power;l.data.size=2;l.rotation_euler=(ct-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam;cam.data.ortho_scale=span
screens=[]
def render(name,direction,hidden=()):
 for o in obs:o.hide_render=o.name in hidden
 cam.location=ct+Vector(direction);cam.rotation_euler=(ct-cam.location).to_track_quat('-Z','Y').to_euler()
 p=R/'screenshots'/(name+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 screens.append({'file':'screenshots/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'camera_direction_blender':direction,'hidden_source_nodes':list(hidden),'visible_source_nodes':[o.name for o in obs if not o.hide_render]})
cap='Yao_capsule_of_lymph_node';med='Yao_medulla_of_lymph_node';vascular='Yao_blood_vasculature'
render('whole-oblique',(1,-2,.5))
render('capsule-hidden-oblique',(1,-2,.5),[cap])
render('capsule-hidden-lower',(1,-2,-1.6),[cap])
render('capsule-medulla-hidden',(1,-2,.5),[cap,med])
render('follicles-paracortex-context',(1,-2,.5),[cap,med,vascular])
for o in obs:
 render('layer-'+labels[o.name][0],(1,-2,.5),[x.name for x in obs if x!=o])
for o in obs:o.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(R/'exact-source-review-scene.blend'))
json.dump({'exact_glb_sha256':sha,'geometry_materials_transforms':'Unchanged. Only camera/lights and explicitly recorded layer visibility differ between screenshots. All isolated layers retain original relative coordinates and common camera scale; no exploded transform.','frame':'HRA original GLB frame; Blender glTF import coordinate conversion only. Camera directions are not anatomical claims. Separate from Z/BP3D.','camera_recipe':{'target_center_blender_import_m':list(ct),'orthographic_scale_m':span,'position_rule':'center + camera_direction_blender (recorded per view)','rotation_rule':'(center-camera.location).to_track_quat(-Z,Y).to_euler()','resolution':[1100,900],'engine':'Cycles','samples':48,'denoising':False,'lights':[{'type':'AREA','offset_from_center':v,'energy':e,'size':2} for v,e in [([-1,-2,2],130),([1,-1,-1],90),([0,2,1],110)]],'world_color':[.045,.045,.045],'blender_version':bpy.app.version_string,'material_edits':'none'},'screenshots':screens},open(R/'render-evidence.json','w'),indent=2)
print('REVIEW_COMPLETE',sha)
