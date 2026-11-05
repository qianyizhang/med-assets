import bpy,csv,pathlib,json,hashlib
from mathutils import Vector
import argparse,sys
ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,required=True,help='Canonical BP3D obj root containing hash/file paths from dependency map');ap.add_argument('--dependency-map',type=pathlib.Path,required=True);ap.add_argument('--output-root',type=pathlib.Path,required=True);ap.add_argument('--verify-exports',type=pathlib.Path);ap.add_argument('--skip-renders',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
C=args.source_root.resolve();O=args.output_root.resolve();O.mkdir(parents=True,exist_ok=True);D=O/'evidence';D.mkdir(exist_ok=True);(O/'exports').mkdir(exist_ok=True)
deps=json.loads(args.dependency_map.read_text());selected={r['id']:r for r in deps['components']};parts={k:r['concept'] for k,r in selected.items()};records=[];objects={}

bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*c,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.7;return m
bone=mat('context bone — diagnostic color',(.56,.48,.34));cart=mat('source cartilage/disc — diagnostic teal',(.08,.52,.52))
for fid,identity in parts.items():
 p=C/selected[fid]['canonical_obj_relative_path'];raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();cp=p;assert h==selected[fid]['sha256'] and len(raw)==selected[fid]['bytes']
 v=[];f=[]
 for l in raw.decode().splitlines():
  if l.startswith('v '):v.append(tuple(float(x)*.001 for x in l.split()[1:4]))
  elif l.startswith('f '):f.append(tuple(int(x.split('/')[0])-1 for x in l.split()[1:]))
 me=bpy.data.meshes.new(fid);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(fid+' '+identity[1],me);bpy.context.collection.objects.link(o);o.data.materials.append(cart if ('cartilage' in identity[1] or 'disk' in identity[1]) else bone)
 for face in me.polygons:face.use_smooth=True
 objects[fid]=o;records.append({'id':fid,'concept':identity,'path':str(cp),'sha256':h,'vertices':len(v),'faces':len(f),'bounds_m':[[min(x[i] for x in v) for i in range(3)],[max(x[i] for x in v) for i in range(3)]]})
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100;s.world=bpy.data.worlds.new('world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.07,.09,.12,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam
lights=[]
for _ in range(3):bpy.ops.object.light_add(type='AREA');lights.append(bpy.context.object)
renders=[]
def render(name,ids,view):
 for fid,o in objects.items():o.hide_render=fid not in ids
 verts=[v.co for fid in ids for v in objects[fid].data.vertices];lo=Vector([min(v[i] for v in verts) for i in range(3)]);hi=Vector([max(v[i] for v in verts) for i in range(3)]);c=(lo+hi)/2;span=max(hi-lo);cam.location=c+Vector(view).normalized()*span*3;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=span*1.2
 for l,pos,power in zip(lights,[(-1,-2,2),(2,-1,.5),(.4,2,1)],[160,100,180]):l.location=c+Vector(pos)*span;l.rotation_euler=(c-l.location).to_track_quat('-Z','Y').to_euler();l.data.energy=power*span*span;l.data.size=span*1.5
 p=D/(name+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);renders.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'visibleIds':ids,'camera':list(cam.location),'orthoScale':cam.data.ortho_scale})
costal=[k for k,v in parts.items() if 'costal cartilage' in v[1] or ' rib' in v[1] or v[1]=='sternum'];lumbar=[k for k,v in parts.items() if 'lumbar' in v[1]]

from collections import Counter
from mathutils.kdtree import KDTree
reports=[]
studies={'second-costal': ['FJ3335','FJ3242','FJ3229','FJ3336','FJ3158','FJ3160','FJ3153','FJ3178','FJ3290'], 'L3-L4-disc':['FJ3162','FJ3165','FJ3215']}
for study,ids in studies.items():
 bpy.ops.object.select_all(action='DESELECT')
 for fid in ids:
  o=objects[fid];o.hide_render=False;o.select_set(True);o['source_file_id']=fid;o['source_concept_id']=parts[fid][0];o['structure_label']=parts[fid][1];o['teaching_study']=study;o['source_geometry']='unchanged BP3D 4.0; mm to m uniformly';o['role']='selected tissue' if ('cartilage' in parts[fid][1] or 'disk' in parts[fid][1]) else 'anatomical context'
 p=(args.verify_exports.resolve() if args.verify_exports else O/'exports')/(study+'.glb')
 if not args.verify_exports:bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_extras=True)
 originals=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p));new=[o for o in bpy.data.objects if o not in originals and o.type=='MESH'];bpy.context.view_layer.update();checks=[]
 for o in new:
  fid=o['source_file_id'];src=objects[fid];kd=KDTree(len(src.data.vertices))
  for i,v in enumerate(src.data.vertices):kd.insert(src.matrix_world@v.co,i)
  kd.balance();mapping={};dist=[]
  for i,v in enumerate(o.data.vertices):_,j,d=kd.find(o.matrix_world@v.co);mapping[i]=j;dist.append(d)
  src.data.calc_loop_triangles();o.data.calc_loop_triangles();vertex_key=lambda i:tuple(src.matrix_world@src.data.vertices[i].co);expected=Counter(tuple(sorted(vertex_key(i) for i in t.vertices)) for t in src.data.loop_triangles);actual=Counter(tuple(sorted(vertex_key(mapping[i]) for i in t.vertices)) for t in o.data.loop_triangles)
  check={'id':fid,'max_roundtrip_vertex_error_m':max(dist),'same_triangle_vertex_mapping':actual==expected,'triangles':len(o.data.loop_triangles),'source_sha256':next(r['sha256'] for r in records if r['id']==fid)};print('ROUNDTRIP',check,flush=True);assert max(dist)<1e-7 and actual==expected;checks.append(check)
  # Render imported export, not source scene. Source objects stay hidden.
  objects[fid]=o
 for old in originals:
  if old.type=='MESH':old.hide_render=True
 for n,v in [('front',(0,-1,0)),('side',(1,0,0)),('neutral-oblique',(1,-2,.5))]:
  if not args.skip_renders:render(study+'-'+n,ids,v)
 for o in new:bpy.data.objects.remove(o,do_unlink=True)
 objects={o.name.split(' ')[0]:o for o in originals if o.type=='MESH'}
 reports.append({'study':study,'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'selected_ids':ids,'checks':checks,'noAnimationClaim':True})
(O/'exact-export-tests.json').write_text(json.dumps({'studies':reports,'renderBindings':renders,'sourceRecords':records,'noCanonicalEdits':True,'noNewAcceptedModelCount':True},indent=2))
