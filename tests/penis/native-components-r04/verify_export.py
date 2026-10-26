import bpy,numpy as np,json,hashlib,argparse,sys
from pathlib import Path
from mathutils.kdtree import KDTree
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(a.source);G=Path(a.candidate);O=Path(a.out)
assert hashlib.sha256(S.read_bytes()).hexdigest()=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd','Source hash mismatch'
assert hashlib.sha256(G.read_bytes()).hexdigest()=='c44d35e13be11d2fb35141747d819d4609a45ca0a5527c89e1015618d17cab70','Candidate hash mismatch'
assert not O.exists(),'Output must be new';O.mkdir(parents=True)
names=['Glans penis','Corpus spongiosum of penis','Corpus cavernosum of penis']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(S),link=False) as (a,b):b.objects=list(names)
for o in b.objects:bpy.context.collection.objects.link(o)
bpy.context.view_layer.update()
def mesh(o):
 v=np.array([tuple(o.matrix_world@p.co) for p in o.data.vertices]);v,inv=np.unique(v,axis=0,return_inverse=True);o.data.calc_loop_triangles();f=inv[np.array([t.vertices[:] for t in o.data.loop_triangles])];return v,f
src={o.name:mesh(o) for o in b.objects}
def canonical(f):
 f=np.array([np.roll(t,-np.argmin(t)) for t in f]);return f[np.lexsort(f.T[::-1])]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(G),merge_vertices=False);bpy.context.view_layer.update();rows=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 name=o.name.removesuffix(' source display');assert name in src;v,f=src[name];w,g=mesh(o);kd=KDTree(len(v))
 for i,p in enumerate(v):kd.insert(p,i)
 kd.balance();mapping=[];d=[]
 for p in w:
  _,i,dd=kd.find(p);mapping.append(i);d.append(dd)
 gm=np.array(mapping)[g];rows.append({'name':name,'source_vertices':len(v),'export_vertices':len(w),'max_world_coordinate_error_m':max(d),'unique_bijective_mapping':len(set(mapping))==len(v)==len(w),'oriented_triangles_equal_after_mapping':np.array_equal(canonical(f),canonical(gm))})
assert sorted(r['name'] for r in rows)==sorted(names)
r={'source_blend_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(G.read_bytes()).hexdigest(),'exact_object_membership':True,'meshes':rows,'scope':'Selective source load, view-layer update before world transforms, export fresh import. Float32 coordinate tolerance2e-7m, no bit-exact claim. Source topology defects retained; no anatomy or lumen validation.'};r['scoped_source_preservation_pass']=all(x['unique_bijective_mapping'] and x['oriented_triangles_equal_after_mapping'] and x['max_world_coordinate_error_m']<2e-7 for x in rows);(O/'source-export.json').write_text(json.dumps(r,indent=2));print(r)
