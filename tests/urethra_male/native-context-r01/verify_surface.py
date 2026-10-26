import bpy,json,collections,argparse,sys,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);opts=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);P=opts.work;O=opts.out;assert hashlib.sha256((P/'r01/context.glb').read_bytes()).hexdigest()=='d2d88c936287f4ea5978aba1f17e86975c587a102e498595dd7a58aa07c269e7';O.mkdir(parents=True,exist_ok=False)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(P/'r01/context.glb'))
objs={o.get('source_object',o.name):o for o in bpy.context.scene.objects if o.type=='MESH'}
print(list(objs))
u=objs['Urethra'];v=[u.matrix_world@x.co for x in u.data.vertices];faces=[list(p.vertices) for p in u.data.polygons];lut={};vv=[];mapping=[]
for x in v:
 key=tuple(x)
 if key not in lut:lut[key]=len(vv);vv.append(x)
 mapping.append(lut[key])
faces=[[mapping[i] for i in f] for f in faces];v=vv
edges=collections.Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in faces for i in range(len(f)))
bound=[e for e,n in edges.items() if n==1];adj=collections.defaultdict(set)
for a,b in bound:adj[a].add(b);adj[b].add(a)
comps=[];left=set(adj)
while left:
 stack=[left.pop()];cc=[]
 while stack:
  a=stack.pop();cc.append(a)
  for b in adj[a]:
   if b in left:left.remove(b);stack.append(b)
 comps.append({'vertices':len(cc),'center':[sum(v[j][i] for j in cc)/len(cc) for i in range(3)],'degree2':all(len(adj[j])==2 for j in cc)})
(O/'topology.json').write_text(json.dumps({'vertices':len(v),'faces':len(faces),'boundary_edges':len(bound),'edge_incidence_gt2':sum(n>2 for n in edges.values()),'boundary_components':comps,'scope':'Open modeled curve surface; no separate wall thickness, lumen, patency or clinical outlet validation'},indent=2))
