import bpy,bmesh,sys,argparse,pathlib,json,hashlib,math,heapq
from mathutils import Vector
import numpy as np
P=pathlib.Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--input',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);O=pathlib.Path(a.out);

S=pathlib.Path(a.input);assert hashlib.sha256(S.read_bytes()).hexdigest()=='8820a14b820239c0ea53a3597ad7731b7c66eb41f05b197fde2e90ee08fb47e4','Source hash mismatch'
O.mkdir(exist_ok=False)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(S),merge_vertices=True);o=next(x for x in bpy.context.scene.objects if x.type=='MESH');bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);me=o.data
base=np.array([v.co[:] for v in me.vertices],dtype=np.float64);edges=np.array([e.vertices[:] for e in me.edges]);adj=[[] for _ in base]
for i,j in edges:adj[i].append(j);adj[j].append(i)
target=np.array([0,.007,.080]);seed=int(np.argmin(np.linalg.norm(base-target,axis=1)));dist=np.full(len(base),np.inf);dist[seed]=0;todo=[(0,seed)]
while todo:
 d,i=heapq.heappop(todo)
 if d!=dist[i] or d>.014:continue
 for j in adj[i]:
  v=d+np.linalg.norm(base[i]-base[j])
  if v<dist[j] and v<.014:dist[j]=v;heapq.heappush(todo,(v,j))
rad=np.linalg.norm(base-target,axis=1);weight=np.where((rad<.010)&(dist<.014),.5*(1+np.cos(np.pi*np.minimum(rad,.010)/.010)),0);ids=np.flatnonzero(weight>0);coords=base.copy()
for it in range(65):
 for factor in (.45,):
  delta=np.array([coords[adj[i]].mean(axis=0)-coords[i] for i in ids]);coords[ids]+=delta*weight[ids,None]*factor
  move=coords[ids]-base[ids];length=np.linalg.norm(move,axis=1);coords[ids]=base[ids]+move*np.minimum(1,.0005/np.maximum(length,1e-30))[:,None]
oldnorm=np.zeros_like(base)
for lp in me.loops:oldnorm[lp.vertex_index]+=np.array(me.corner_normals[lp.index].vector)
oldnorm/=np.maximum(np.linalg.norm(oldnorm,axis=1)[:,None],1e-30)
for v,c in zip(me.vertices,coords):v.co=c
me.update();bm=bmesh.new();bm.from_mesh(me);bm.normal_update();r={'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'euler':len(bm.verts)-len(bm.edges)+len(bm.faces),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-18 for f in bm.faces),'selected_vertices':len(ids),'max_displacement_m':float(np.linalg.norm(coords-base,axis=1).max()),'outside_support_exact':bool(np.array_equal(coords[weight==0],base[weight==0])),'method':'65 positive Laplacian .45 local iterations; cosine spatial taper10mm + geodesic14mm eligibility; pervertex0.5mm displacement bound; unchanged topology, no union or routes added','seed_source_coordinate':base[seed].tolist(),'scope':'Authored surface refinement, not anatomy validation'};bm.free()
# Preserve imported normals outside region; local geometry normal blend only.
normal=[]
for i,v in enumerate(me.vertices):
 auto=np.array(v.normal);w=min(1,weight[i]*3);n=auto*w+oldnorm[i]*(1-w);normal.append(tuple(n/max(np.linalg.norm(n),1e-30)))
me.normals_split_custom_set_from_vertices(normal)
for k in list(bpy.context.scene.keys()):del bpy.context.scene[k]
o['scope']='Authored schematic; local junction fairing only, no anatomical or lumen validation.'
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.export_scene.gltf(filepath=str(O/'candidate.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False)
r['export_sha256']=hashlib.sha256((O/'candidate.glb').read_bytes()).hexdigest();(O/'geometry-qa.json').write_text(json.dumps(r,indent=2));np.savez_compressed(O/'vertex-invariants.npz',baseline=base,candidate=coords,weights=weight)
