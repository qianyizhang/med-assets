import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(a.source);O=Path(a.out)
assert hashlib.sha256(S.read_bytes()).hexdigest()=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd','Source hash mismatch'
assert not O.exists(),'Output must be new';O.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
names=['Submandibular duct.l','Mylohyoid muscle.l']
with bpy.data.libraries.load(str(S),link=False) as(a,b):b.objects=list(names)
for o in b.objects:bpy.context.collection.objects.link(o);o.hide_set(False);o.hide_viewport=False
bpy.context.view_layer.update();m=bpy.data.objects[names[1]];v=[m.matrix_world@v.co for v in m.data.vertices];tree=BVHTree.FromPolygons(v,[list(p.vertices) for p in m.data.polygons]);d=bpy.data.objects[names[0]];rows=[]
for sp in d.data.splines:
 for p in sp.bezier_points:
  w=d.matrix_world@p.co;hit=tree.ray_cast(Vector((w.x,w.y,2)),Vector((0,0,-1)),3)[0];rows.append({'duct_point':list(w),'mylohyoid_top_z':None if hit is None else hit.z,'duct_above_top':None if hit is None else w.z-hit.z})
(O/'duct-floor-check.json').write_text(json.dumps(rows,indent=2));print(rows)

from mathutils.geometry import interpolate_bezier
samples=[]
for sp in d.data.splines:
 for a,b in zip(sp.bezier_points,sp.bezier_points[1:]):
  samples += [d.matrix_world@v for v in interpolate_bezier(a.co,a.handle_right,b.handle_left,b.co,31)]
hits=[]
for a,b in zip(samples,samples[1:]):
 delta=b-a
 if delta.length<1e-8:continue
 h=tree.ray_cast(a,delta.normalized(),delta.length)[0]
 if h is not None:hits.append(list(h))
(O/'duct-floor-intersections.json').write_text(json.dumps({'sampled_centerline_surface_intersections':hits},indent=2))
