import bpy,pathlib,json,collections,hashlib
import argparse,sys
parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=pathlib.Path);parser.add_argument('--output',required=True,type=pathlib.Path);parser.add_argument('--skip-renders',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
D=args.output.resolve();D.mkdir(parents=True,exist_ok=True);S=args.source.resolve()
EXPECTED_SOURCE_SHA256='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
assert hashlib.sha256(S.read_bytes()).hexdigest()==EXPECTED_SOURCE_SHA256,'Source SHA256 mismatch; do not substitute a different atlas'

names=[r['name'] for r in json.load(open(D/'source-check.json'))['records']]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(S),link=False) as (a,b):b.objects=names
for o in b.objects:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();orig={}
def signature(m,matrix):
 m.calc_loop_triangles();v=[matrix@p.co for p in m.vertices];tris=collections.Counter();zero=0
 for t in m.loop_triangles:
  a,b,c=[v[i] for i in t.vertices]
  if (b-a).cross(c-a).length==0:zero+=1;continue
  tris[tuple(sorted(tuple(round(x,7) for x in v[i]) for i in t.vertices))]+=1
 return dict(vertices=len(v),triangles=len(m.loop_triangles),zero_triangles=zero,coords=set(tuple(round(x,7) for x in p) for p in v),nonzero=tris)
for o in b.objects:
 e=o.evaluated_get(dg);m=e.to_mesh();orig[o.name]=signature(m,e.matrix_world);e.to_mesh_clear()
for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(D/'achilles-right-context-proposal.glb'));out=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 a=orig[o['source_object_name']];b=signature(o.data,o.matrix_world)
 out.append(dict(name=o['source_object_name'],source_duplicate_triangles=sum(v-1 for v in a['nonzero'].values() if v>1),source_vertices=a['vertices'],export_vertices=b['vertices'],source_triangles=a['triangles'],export_triangles=b['triangles'],source_zero_triangles=a['zero_triangles'],export_zero_triangles=b['zero_triangles'],source_unique_positions=len(a['coords']),export_unique_positions=len(b['coords']),missing_positions=len(a['coords']-b['coords']),extra_positions=len(b['coords']-a['coords']),missing_nonzero_triangles=sum((a['nonzero']-b['nonzero']).values()),extra_nonzero_triangles=sum((b['nonzero']-a['nonzero']).values()),missing_triangle_coords=list((a['nonzero']-b['nonzero']).elements()),extra_triangle_coords=list((b['nonzero']-a['nonzero']).elements())))
json.dump(dict(comparison='World coordinates rounded to 1e-7 native source units; nonzero triangles compared as unordered coordinate triplet multisets',records=out),open(D/'source-vs-export-geometry.json','w'),indent=2)
