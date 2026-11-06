import bpy,bmesh,json,hashlib,re,itertools,argparse,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--out',required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(args.candidate);O=Path(args.out);assert hashlib.sha256(S.read_bytes()).hexdigest()=='5d9f0f88ff8498f611aea583e080558691d592a3ce50c89ecb847cf18b4d1471';assert not O.exists(),'Output exists';bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(S),merge_vertices=False);rows=[];meshes={}
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 verts=[];keys={};ids=[]
 for v in o.data.vertices:
  p=tuple(o.matrix_world@v.co)
  if p not in keys:keys[p]=len(verts);verts.append(p)
  ids.append(keys[p])
 faces=[[ids[i] for i in p.vertices] for p in o.data.polygons];m=bpy.data.meshes.new('check');m.from_pydata(verts,[],faces);m.update();bm=bmesh.new();bm.from_mesh(m);bmesh.ops.triangulate(bm,faces=bm.faces);bm.verts.ensure_lookup_table();bm.verts.index_update();fs=[[v.index for v in f.verts] for f in bm.faces];edge_bad=sum(len(e.link_faces)!=2 for e in bm.edges);comps=0;seen=set()
 for v in bm.verts:
  if v.index in seen:continue
  comps+=1;todo=[v];seen.add(v.index)
  while todo:
   vv=todo.pop()
   for e in vv.link_edges:
    w=e.other_vert(vv)
    if w.index not in seen:seen.add(w.index);todo.append(w)
 rows.append({'name':o.name,'raw_vertices':len(o.data.vertices),'exact_weld_vertices':len(verts),'triangles':len(fs),'euler':len(bm.verts)-len(bm.edges)+len(bm.faces),'components':comps,'edge_incidence_not2':edge_bad,'zeroarea':sum(f.calc_area()<1e-18 for f in bm.faces),'signed_volume_m3':bm.calc_volume(signed=True)});bm.free();meshes[o.name]={'verts':[Vector(v) for v in verts],'faces':fs,'tree':BVHTree.FromPolygons(verts,fs,all_triangles=True,epsilon=0)}
# BVH broadphase then separating-axis test, double math via Python float, tolerance explicit.
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
roots=[n for n in meshes if n.startswith('Representative') or n.startswith('Filum')];pairs=[]
def group(n):
 if n.startswith('Filum'):return ('filum',)
 if ' upper ' in n:return ('upper',*re.search(r'upper (\d+) side(-?\d+)',n).groups())
 return ('descending',*re.search(r'(?:root|nerve) (\d+) side(-?\d+)',n).groups())
for a,b in itertools.combinations(roots,2):
 if group(a)==group(b):continue
 A=meshes[a];B=meshes[b];cand=A['tree'].overlap(B['tree']);actual=[]
 for i,j in cand:
  if hit([A['verts'][v] for v in A['faces'][i]],[B['verts'][v] for v in B['faces'][j]]):actual.append([i,j])
 pairs.append({'a':a,'b':b,'bvh_candidates':len(cand),'sat_contacts':len(actual),'first_contacts':actual[:4]})
cord=next(v for n,v in meshes.items() if n.startswith('Authored cord'))
attachments=[]
for n in meshes:
 if ' root ' in n:
  cand=cord['tree'].overlap(meshes[n]['tree']);count=sum(hit([cord['verts'][v] for v in cord['faces'][i]],[meshes[n]['verts'][v] for v in meshes[n]['faces'][j]]) for i,j in cand);attachments.append({'name':n,'cord_surface_contacts':count})
r={'sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'mesh_topology':rows,'all_nonadjacent_nerve_filum_pairs':len(pairs),'pair_screen':pairs,'cord_attachments':attachments,'scope':'Fresh GLB import; exact-coordinate weld, triangulation for checks only. BVH broadphase then triangle SAT with1e-10m gap tolerance. This is finite-precision screening, not exact-arithmetic proof or anatomical validation. Samelevel dorsal/ventral/mixed-nerve group convergence excluded only; all unrelated upper/descending nerve groups and filum included.'};O.write_text(json.dumps(r,indent=2));print('meshes',len(rows),'badedges',sum(x['edge_incidence_not2'] for x in rows),'badcontacts',sum(x['sat_contacts'] for x in pairs),'missingattachments',sum(x['cord_surface_contacts']==0 for x in attachments))
