"""Exhaustive source/reimport surface and effective-transform preservation check."""
import argparse, collections, hashlib, importlib.util, json, sys
from pathlib import Path
import bpy
from mathutils.kdtree import KDTree

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('median_build',HERE/'build.py')
recipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipe)
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--glb',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if a.out.exists():raise FileExistsError('Receipt must be new')
assert hashlib.sha256(a.source.read_bytes()).hexdigest()==recipe.SOURCE_SHA
assert hashlib.sha256(a.glb.read_bytes()).hexdigest()==a.sha256
def snapshot(o,dg):
 e=o.evaluated_get(dg);m=bpy.data.meshes.new_from_object(e,depsgraph=dg);m.calc_loop_triangles()
 result=([e.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],e.matrix_world.copy())
 bpy.data.meshes.remove(m);return result
def tree(points):
 k=KDTree(len(points))
 for i,v in enumerate(points):k.insert(v,i)
 k.balance();return k
bpy.ops.wm.open_mainfile(filepath=str(a.source),load_ui=False,use_scripts=False)
dg=bpy.context.evaluated_depsgraph_get();native={n:snapshot(bpy.data.objects[n],dg) for n in recipe.NAMES}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(a.glb))
objects={o.get('source_object'):o for o in bpy.context.scene.objects if o.type=='MESH'}
assert set(objects)==set(recipe.NAMES)
dg=bpy.context.evaluated_depsgraph_get();rows=[];tolerance=1e-6
for name in recipe.NAMES:
 sp,st,sm=native[name];ep,et,em=snapshot(objects[name],dg)
 sk,ek=tree(sp),tree(ep);nearest=[sk.find(v) for v in ep]
 worst=max([r[2] for r in nearest]+[ek.find(v)[2] for v in sp])
 assert worst<tolerance,(name,'vertex displacement',worst)
 # Weld exact coincident source positions solely for triangle identity comparison.
 canonical={}
 for i,v in enumerate(sp):canonical.setdefault(tuple(v),i)
 source_ids=[canonical[tuple(v)] for v in sp]
 export_ids=[source_ids[r[1]] for r in nearest]
 src=collections.Counter(tuple(sorted(source_ids[i] for i in t)) for t in st)
 dst=collections.Counter(tuple(sorted(export_ids[i] for i in t)) for t in et)
 assert src==dst,(name,'source surface triangle mismatch')
 matrix_error=max(abs(sm[i][j]-em[i][j]) for i in range(4) for j in range(4))
 assert matrix_error<tolerance,(name,'effective matrix mismatch',matrix_error)
 rows.append({'sourceObject':name,'sourceVertices':len(sp),'exportVertices':len(ep),'triangles':len(st),'maxBidirectionalVertexDifference':worst,'maxMatrixDifference':matrix_error,'surfaceTrianglesMatch':True})
receipt={'sourceSha256':recipe.SOURCE_SHA,'artifactSha256':a.sha256,'result':'passed','objects':rows,
         'tolerance':tolerance,'scope':'All 33 evaluated surface vertex clouds checked bidirectionally; all source triangles compared after exact-coordinate source seam welding; effective world matrices checked. Float32 numerical tolerance, not anatomical accuracy or physical-scale validation.',
         'limitations':'Does not validate nerve continuity, nerve/flexor relationships, clinical anatomy, browser runtime or absence of every self-intersection.'}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'result':'passed','objects':len(rows),'triangles':sum(x['triangles'] for x in rows),'maxVertexDifference':max(x['maxBidirectionalVertexDifference'] for x in rows)},indent=2))
