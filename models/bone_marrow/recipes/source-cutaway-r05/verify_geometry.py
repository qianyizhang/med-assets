"""Blender verifier; run blender -b --python-exit-code 1 --python verify_geometry.py -- --candidate FILE --source FILE --out NEWDIR. Finite precision teaching-asset QA, not clinical validation."""
import bpy, numpy as np, json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
ap.add_argument('--candidate-sha256',default='7b21b74fb3712b2816801337bd4d0732ef8bb035a999ad36558b8235609cfe02');ap.add_argument('--source-sha256',default='d224985628cc62d0c9c4284019b73505c9ebf14d78d30a040d74a7b33c68620e');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
S=Path(a.candidate);R=Path(a.source);O=Path(a.out)
for f,h in [(S,a.candidate_sha256),(R,a.source_sha256)]:
 if hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError('Input SHA256 mismatch: '+f.name)
if O.exists():raise FileExistsError('Refusing existing output directory')
O.mkdir(parents=True,exist_ok=False)
def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
clear();bpy.ops.import_scene.gltf(filepath=str(R),merge_vertices=False)
src=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name=='FJ3259 left femur')
v=np.array([tuple(src.matrix_world@q.co) for q in src.data.vertices]);sv,inv=np.unique(v,axis=0,return_inverse=True);sf=inv[np.array([p.vertices[:] for p in src.data.polygons])];tree=BVHTree.FromPolygons(sv.tolist(),sf.tolist(),all_triangles=True)
clear();bpy.ops.import_scene.gltf(filepath=str(S),merge_vertices=False)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def hit(A,B):
 ea=[sub(A[(i+1)%3],A[i]) for i in range(3)];eb=[sub(B[(i+1)%3],B[i]) for i in range(3)];na=cross(ea[0],ea[1]);nb=cross(eb[0],eb[1]);axes=[na,nb]+[cross(a,b) for a in ea for b in eb]+[cross(na,e) for e in ea]+[cross(nb,e) for e in eb]
 for ax in axes:
  length=dot(ax,ax)**.5
  if length<1e-25:continue
  aa=[dot(p,ax)/length for p in A];bb=[dot(p,ax)/length for p in B]
  if max(aa)<min(bb)-1e-10 or max(bb)<min(aa)-1e-10:return False
 return True

dirs=[Vector(d).normalized() for d in [(1,.223,.317),(-.31,1,.123),(.17,.32,1)]]
def parity(p,d):
 origin=Vector(p);count=0
 for _ in range(100):
  loc,n,i,dist=tree.ray_cast(origin,d)
  if loc is None:return count%2
  count+=1;origin=loc+d*1e-7
 raise RuntimeError('Ray exceeded100crossings')
rows=[];passed=True
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 v=np.array([tuple(o.matrix_world@q.co) for q in o.data.vertices]);v,inv=np.unique(v,axis=0,return_inverse=True);f=inv[np.array([p.vertices[:] for p in o.data.polygons])]
 es=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);e,n=np.unique(es,axis=0,return_counts=True);parent=np.arange(len(v))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for aa,bb in e:
  aa=find(aa);bb=find(bb)
  if aa!=bb:parent[bb]=aa
 comps=len(set(find(i) for i in range(len(v))));area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)
 outside=[]
 for i,p in enumerate(v):
  h,normal,ix,d=tree.find_nearest(Vector(p))
  if d>1e-6 and (Vector(p)-h).dot(normal)>1e-6 and sum(parity(p,dr) for dr in dirs)<2:outside.append((i,float(d)))
 row={'name':o.name,'vertices':len(v),'triangles':len(f),'components':comps,'boundary_edges':int((n==1).sum()),'edge_incidence_not2':int((n!=2).sum()),'zero_area':int((area==0).sum()),'outside_source_vertices_over_1um':len(outside),'max_outside_m':max([d for _,d in outside],default=0)}
 if 'cortical shell' in o.name:
  t=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True);contacts=[];candidates=0
  for i,j in t.overlap(t):
   if i>=j or set(f[i])&set(f[j]):continue
   candidates+=1
   if hit(v[f[i]],v[f[j]]):contacts.append([int(i),int(j)])
  row.update({'nonadjacent_bvh_candidates':candidates,'nonadjacent_triangle_contacts':len(contacts),'contact_pairs':contacts})
  passed=passed and not contacts
 passed=passed and comps==1 and row['edge_incidence_not2']==0 and row['zero_area']==0 and not outside;rows.append(row)
report={'candidate_sha256':a.candidate_sha256,'source_sha256':a.source_sha256,'scoped_geometry_pass':bool(passed),'meshes':rows,'limits':['Exact-coordinate weld for checks only; no candidate mutation.','Vertex-containment screening, not every triangle-interior proof.','Shell nonadjacent BVH/SAT excludes shared-vertex pairs; finite precision.','No exhaustive network self-intersection proof.','Intentional network/backing contact is not segmented tissue, attachment count or mechanical validation.','No clinical anatomy or runtime approval.']}
(O/'geometry.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if not passed:raise RuntimeError('Scoped geometry checks failed; see geometry.json')
