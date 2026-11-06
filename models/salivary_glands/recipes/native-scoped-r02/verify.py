import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils.kdtree import KDTree
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--build',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(a.source);D=Path(a.build);O=Path(a.out);R=json.loads((D/'source-members.json').read_text());names=[r['name'] for r in R['members']]
assert hashlib.sha256(S.read_bytes()).hexdigest()=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd','Source hash mismatch'
assert hashlib.sha256((D/'context.glb').read_bytes()).hexdigest()=='1764c63011e698b9047d1abe79c647b8b609b7d8f9b18b740b17cdc65db930f8','Candidate hash mismatch'
assert len(names)==15 and 'Submandibular duct.l' not in names and 'Submandibular duct.r' not in names,'Excluded source component present'
assert not O.exists(),'Output must be new';O.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(S),link=False) as (a,b):b.objects=list(names)
for o in b.objects:bpy.context.collection.objects.link(o);o.hide_set(False);o.hide_viewport=False;o.hide_render=False
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get(); expected={}; out={'source_hash_match':hashlib.sha256(S.read_bytes()).hexdigest()==R['source_sha256'],'members':[]}
for o in b.objects:
 e=o.evaluated_get(dep);me=e.to_mesh();pts=[o.matrix_world@v.co for v in me.vertices];expected[o.name]=pts
 row=next(x for x in R['members'] if x['name']==o.name)
 out['members'].append({'name':o.name,'matrix_max_error':max(abs(o.matrix_world[i][j]-row['matrix_world'][i][j]) for i in range(4) for j in range(4)), 'bbox_native':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]})
 e.to_mesh_clear()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
G=D/'context.glb';bpy.ops.import_scene.gltf(filepath=str(G));out['export_hash_match']=hashlib.sha256(G.read_bytes()).hexdigest()==R['exports']['context.glb']
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 n=o.get('source_object');pts=expected[n];kd=KDTree(len(pts))
 for i,p in enumerate(pts):kd.insert(p,i)
 kd.balance();row=next(x for x in out['members'] if x['name']==n);row['import_vertex_to_source_max_distance']=max(kd.find(o.matrix_world@v.co)[2] for v in o.data.vertices)
assert out['source_hash_match'] and out['export_hash_match']
assert all(r['matrix_max_error']==0 and r.get('import_vertex_to_source_max_distance',float('inf'))<2e-7 for r in out['members']),'Source-preservation tolerance failed'
out['scope']='Native effective transforms and sampled nearest-source vertex preservation, not exhaustive topology/anatomy proof'
(O/'geometry-check.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
