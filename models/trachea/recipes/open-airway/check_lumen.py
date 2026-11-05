"""Sample air-space connectivity inside the cast envelope on the exported shell.

This is a 1.2 mm grid/path screen with triangle-tested steps, not fluid simulation
or clinical lumen calibration. The fixed baseline confines the sampled region.
"""
import argparse,collections,hashlib,json,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if a.out.exists():raise FileExistsError(a.out)
record=json.loads(a.record.read_text());variant=next(v for v in record['variants'] if v['variant']=='open')
assert hashlib.sha256(a.candidate.read_bytes()).hexdigest()==variant['sha256']
assert hashlib.sha256(a.baseline.read_bytes()).hexdigest()==record['baseline_sha256']
def tree(path):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(path),merge_vertices=False)
 ob=next(o for o in bpy.context.scene.objects if o.name.startswith('Trachea |'))
 bm=bmesh.new();bm.from_mesh(ob.data)
 for v in bm.verts:v.co=ob.matrix_world@v.co
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table();bm.verts.index_update()
 vs=[v.co.copy() for v in bm.verts];fs=[tuple(v.index for v in f.verts) for f in bm.faces]
 result=BVHTree.FromPolygons(vs,fs,all_triangles=True,epsilon=0);bm.free();return result,vs
base,verts=tree(a.baseline);wall,_=tree(a.candidate)
direction=Vector((1,.371,.193)).normalized()
def inside(t,p):
 start=p.copy();count=0
 for _ in range(40):
  hit,_,_,_=t.ray_cast(start,direction,1)
  if hit is None:return count%2==1
  count+=1;start=hit+direction*1e-7
 raise ValueError('Unexpected ray complexity')
planes=[(Vector(p),Vector(n).normalized()) for _,p,n in variant['section_planes']]
low=Vector([min(v[k] for v in verts) for k in range(3)]);high=Vector([max(v[k] for v in verts) for k in range(3)])
step=.0012;counts=[int((high[k]-low[k])/step)+1 for k in range(3)];air={}
for ix in range(counts[0]):
 for iy in range(counts[1]):
  for iz in range(counts[2]):
   v=low+Vector((ix*step,iy*step,iz*step))
   if any((v-point).dot(normal)>-1e-6 for point,normal in planes):continue
   if not inside(base,v):continue
   nearest=wall.find_nearest(v)
   if nearest is None or nearest[3]<.00015 or inside(wall,v):continue
   air[ix,iy,iz]=v
centers=[Vector(v) for v in variant['opening_centers']]
seeds=[min(air,key=lambda k:(air[k]-c).length_squared) for c in centers]
assert all((air[k]-c).length<.003 for k,c in zip(seeds,centers)),'No air seed at opening'
start=seeds[0];seen={start};parents={};todo=collections.deque([start]);blocked=0
while todo:
 key=todo.popleft()
 for axis in range(3):
  for sign in (-1,1):
   neighbor=list(key);neighbor[axis]+=sign;neighbor=tuple(neighbor)
   if neighbor in seen or neighbor not in air:continue
   delta=air[neighbor]-air[key];hit,_,_,_=wall.ray_cast(air[key],delta.normalized(),delta.length)
   if hit is not None:blocked+=1;continue
   seen.add(neighbor);parents[neighbor]=key;todo.append(neighbor)
paths=[]
for seed in seeds:
 assert seed in seen,'Opening not connected to common air space'
 chain=[seed]
 while chain[-1]!=start:chain.append(parents[chain[-1]])
 paths.append([list(air[k]) for k in reversed(chain)])
a.out.write_text(json.dumps({'artifact_sha256':variant['sha256'],'grid_step_m':step,'sample_clearance_m':.00015,'air_samples':len(air),'connected_air_samples':len(seen),'opening_seeds':[list(air[k]) for k in seeds],'all_three_openings_connected':True,'triangle_blocked_neighbor_steps':blocked,'paths':paths,'scope':__doc__.strip()},indent=2)+'\n')
print('PASS sampled air continuity:',len(seen),'connected samples; all three openings; triangle-tested path steps')
