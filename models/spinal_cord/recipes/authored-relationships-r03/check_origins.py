import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--out',required=True);ap.add_argument('--controls',required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(args.candidate);O=Path(args.out);assert hashlib.sha256(S.read_bytes()).hexdigest()=='5d9f0f88ff8498f611aea583e080558691d592a3ce50c89ecb847cf18b4d1471';assert not O.exists(),'Output exists';C=Path(args.controls);assert hashlib.sha256(C.read_bytes()).hexdigest()=='d0335cbb771847b9d1e6b17a9ee2e33ab7ec2c226a0471e3fe6d5d69543fefc3';bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(S),merge_vertices=False)
cord=next(o for o in bpy.context.scene.objects if o.name.startswith('Authored cord'));v=[cord.matrix_world@x.co for x in cord.data.vertices];f=[list(p.vertices) for p in cord.data.polygons];tree=BVHTree.FromPolygons(v,f,all_triangles=True,epsilon=0)
def inside(p,d):
 d=Vector(d).normalized();p=Vector(p);n=0
 for _ in range(50):
  q,no,ix,dist=tree.ray_cast(p,d,2)
  if q is None:return n%2==1,n
  n+=1;p=q+d*1e-7
 raise RuntimeError('too many intersections')
rows=[]
for r in json.load(open(C))['descending_root_controls']:
 p=Vector(r['control_points'][0]);name=f"Representative descending {r['role']} root {r['illustrative_lane']} side{r['side']}";o=bpy.data.objects[name];vv=[o.matrix_world@x.co for x in o.data.vertices];dist=min((x-p).length for x in vv);results=[inside(p,d) for d in [(1,.223,.317),(-.31,1,.123),(.17,.32,1)]];rows.append({'name':name,'nominal_start_m':list(p),'nearest_actual_export_vertex_mm':dist*1000,'inside_cord_three_ray_agreement':all(x[0] for x in results),'ray_crossings':[x[1] for x in results]})
r={'sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'rows':rows,'scope':'Recorded authored start points checked against fresh exactGLB cord geometry with3non-axis ray parities; actual root surface vertex within radius independently checked. Finite precision, not full intersectionproof.'};O.write_text(json.dumps(r,indent=2));print('allinside',all(x['inside_cord_three_ray_agreement'] for x in rows),'distmax',max(x['nearest_actual_export_vertex_mm'] for x in rows))
