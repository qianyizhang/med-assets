import bpy,json,pathlib,hashlib
from mathutils import Vector
import argparse,sys
parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=pathlib.Path);parser.add_argument('--output',required=True,type=pathlib.Path);parser.add_argument('--skip-renders',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
D=args.output.resolve();D.mkdir(parents=True,exist_ok=True);S=args.source.resolve()
EXPECTED_SOURCE_SHA256='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
assert hashlib.sha256(S.read_bytes()).hexdigest()==EXPECTED_SOURCE_SHA256,'Source SHA256 mismatch; do not substitute a different atlas'

names=['Calcaneal tendon.r','Soleus muscle.r','Medial head of gastrocnemius.r','Lateral head of gastrocnemius.r','Calcaneus.r','Tibia.r','Fibula.r','Talus.r']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(S),link=False) as (a,b):
 missing=[x for x in names if x not in a.objects];b.objects=[x for x in names if x in a.objects]
for o in b.objects:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();records=[];obs=[]
for o in b.objects:
 e=o.evaluated_get(dg);m=e.to_mesh();v=[tuple(e.matrix_world@p.co) for p in m.vertices];m.calc_loop_triangles();f=[tuple(p.vertices) for p in m.loop_triangles];e.to_mesh_clear();mesh=bpy.data.meshes.new(o.name+' diagnostic');mesh.from_pydata(v,[],f);mesh.update();n=bpy.data.objects.new(o.name+' diagnostic',mesh);bpy.context.scene.collection.objects.link(n);obs.append(n);n['source_object_name']=o.name;n['source_frame']='Z-Anatomy native evaluated world';n['study_scope']='right Achilles contextual study; no validated attachment';n['role']='tendon' if 'tendon' in o.name else 'muscle' if 'muscle' in o.name or 'gastrocnemius' in o.name else 'bone'
 col=(.85,.65,.2) if 'tendon' in o.name else (.5,.14,.12) if 'muscle' in o.name or 'gastrocnemius' in o.name else (.55,.59,.62)
 ma=bpy.data.materials.new(o.name);ma.diffuse_color=(*col,1);n.data.materials.append(ma)
 for p in n.data.polygons:p.use_smooth=True
 records.append(dict(name=o.name,vertices=len(v),faces=len(f),bounds=[[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]],zero_area=sum(p.area==0 for p in mesh.polygons)))
for o in b.objects:bpy.data.objects.remove(o,do_unlink=True)
json.dump(dict(source=str(S),source_sha256=hashlib.sha256(S.read_bytes()).hexdigest(),missing=missing,records=records,scope='Source-named right calf-tendon-calcaneus spatial diagnostic only. No attachment validation, geometry edits or canonical export.'),open(D/'source-check.json','w'),indent=2)

# Export exact selected, unmodified evaluated source; render only reimported GLB.
for o in bpy.context.scene.objects:o.select_set(False)
for o in obs:o.select_set(True)
bpy.context.view_layer.objects.active=obs[0]
g=D/'achilles-right-context-proposal.glb'
bpy.ops.export_scene.gltf(filepath=str(g),export_format='GLB',use_selection=True,export_extras=True)
for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(g));obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
checks=[]
for o in obs:
 vs=[o.matrix_world@v.co for v in o.data.vertices];rec=next(r for r in records if r['name']==o['source_object_name']);bounds=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
 checks.append(dict(name=o['source_object_name'],source_vertices=rec['vertices'],export_vertices=len(vs),bounds_max_abs_delta=max(abs(bounds[j][i]-rec['bounds'][j][i]) for j in range(2) for i in range(3)),triangles=len(o.data.polygons)))
json.dump(dict(glb_sha256=hashlib.sha256(g.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(S.read_bytes()).hexdigest(),source_named_meshes=len(records),reimport_named_meshes=len(obs),checks=checks),open(D/'exact-export-check.json','w'),indent=2)
if args.skip_renders:sys.exit(0)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.resolution_x=900;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.world.color=(.09,.09,.09)
vs=[o.matrix_world@v.co for o in obs for v in o.data.vertices];target=Vector([(min(v[i] for v in vs)+max(v[i] for v in vs))/2 for i in range(3)])
for pos,pow in [((1,-2,3),300),((-2,1,2),400)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=pow;o.data.size=2;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();c=bpy.context.object;s.camera=c;c.data.type='ORTHO';c.data.ortho_scale=.58
neutral=bpy.data.materials.new('Uniform neutral gray diagnostic');neutral.diffuse_color=(.45,.45,.45,1)
views=[]
for name,delta,gray,close in [('export-posterior',(0,3,0),False,False),('export-lateral',(-3,0,0),False,False),('neutral-oblique',(-2,2,.25),True,False),('heel-close-lateral',(-3,0,0),False,True),('heel-close-posterior',(0,3,0),False,True),('heel-close-neutral-oblique',(-2,2,.25),True,True)]:
 for o in obs:
  if 'original_material' not in o:o['original_material']=o.data.materials[0].name
  o.data.materials[0]=neutral if gray else bpy.data.materials[o['original_material']]
 t=Vector((-.08,.066,.068)) if close else target;c.data.ortho_scale=.14 if close else .58
 c.location=t+Vector(delta);c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(D/(name+'.png'));bpy.ops.render.render(write_still=True)
 views.append(dict(file=name+'.png',target=list(t),camera=list(c.location),orthographic_scale=c.data.ortho_scale,uniform_gray=gray,hidden=[],geometry_changes=[],glb_sha256=hashlib.sha256(g.read_bytes()).hexdigest()))
json.dump(views,open(D/'export-render-binding.json','w'),indent=2)
