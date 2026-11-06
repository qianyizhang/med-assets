"""Exact-export topology and finite-precision shell self-contact screen."""
import argparse,hashlib,itertools,json,sys
from pathlib import Path
import bpy,bmesh
from mathutils.bvhtree import BVHTree
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if a.out.exists():raise FileExistsError(a.out)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(a.candidate),merge_vertices=False)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def hit(A,B):
 ea=[sub(A[(i+1)%3],A[i]) for i in range(3)];eb=[sub(B[(i+1)%3],B[i]) for i in range(3)];na=cross(ea[0],ea[1]);nb=cross(eb[0],eb[1]);axes=[na,nb]+[cross(x,y) for x in ea for y in eb]+[cross(na,e) for e in ea]+[cross(nb,e) for e in eb]
 for ax in axes:
  length=dot(ax,ax)**.5
  if length<1e-25:continue
  aa=[dot(p,ax)/length for p in A];bb=[dot(p,ax)/length for p in B]
  if max(aa)<min(bb)-1e-10 or max(bb)<min(aa)-1e-10:return False
 return True
rows=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(ob.data)
 for v in bm.verts:v.co=ob.matrix_world@v.co
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table();bm.verts.index_update()
 verts=[tuple(v.co) for v in bm.verts];faces=[tuple(v.index for v in f.verts) for f in bm.faces]
 comps=0;seen=set()
 for v in bm.verts:
  if v.index in seen:continue
  comps+=1;todo=[v];seen.add(v.index)
  while todo:
   vv=todo.pop()
   for e in vv.link_edges:
    w=e.other_vert(vv)
    if w.index not in seen:seen.add(w.index);todo.append(w)
 row={'name':ob.name,'vertices':len(verts),'triangles':len(faces),'components':comps,'euler':len(bm.verts)-len(bm.edges)+len(bm.faces),'bad_edge_incidence':sum(len(e.link_faces)!=2 for e in bm.edges),'zero_area':sum(f.calc_area()<1e-18 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True)}
 if ob.name.startswith('Trachea |'):
  tree=BVHTree.FromPolygons(verts,faces,all_triangles=True,epsilon=0);cand=[];actual=[]
  for i,j in tree.overlap(tree):
   if i>=j or set(faces[i])&set(faces[j]):continue
   cand.append((i,j))
   if hit([verts[k] for k in faces[i]],[verts[k] for k in faces[j]]):actual.append((i,j))
  row['nonadjacent_self_candidates']=len(cand);row['nonadjacent_self_contacts']=len(actual);row['first_self_contacts']=actual[:20]
 rows.append(row);bm.free()
r={'artifact_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),'meshes':rows,'scope':'Export reimport; 1e-8 m seam weld, manifold/volume and shell triangle SAT with 1e-10 m gap tolerance. Finite precision, not anatomical or exhaustive geometric proof.'}
a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows[0] if rows[0]['name'].startswith('Trachea |') else next(x for x in rows if x['name'].startswith('Trachea |'))))
assert all(x['bad_edge_incidence']==0 and x['zero_area']==0 and x['signed_volume']>0 for x in rows),'Topology failure'
assert all(x.get('nonadjacent_self_contacts',0)==0 for x in rows),'Shell self-contact failure'
