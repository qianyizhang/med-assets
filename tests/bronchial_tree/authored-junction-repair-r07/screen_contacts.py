import bpy,pathlib,json,itertools,argparse,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D=pathlib.Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);P=pathlib.Path(args.input);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(P));obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];trees={};triangles={}
for o in obs:
 o.data.calc_loop_triangles();vs=[o.matrix_world@v.co for v in o.data.vertices];fs=[list(t.vertices) for t in o.data.loop_triangles];trees[o.name]=BVHTree.FromPolygons(vs,fs,all_triangles=True);triangles[o.name]=[[vs[i] for i in f] for f in fs]
starts={'lung_upper_lobe_right':Vector((-.028,.009,.060)),'lung_middle_lobe_right':Vector((-.042,.008,.033)),'lung_lower_lobe_right':Vector((-.042,.008,.033)),'lung_upper_lobe_left':Vector((.042,.008,.068)),'lung_lower_lobe_left':Vector((.042,.008,.068))}
def group(n):return next((x for x in starts if n.startswith(x)),None)
rows=[]
for a,b in itertools.combinations(obs,2):
 hits=trees[a.name].overlap(trees[b.name])
 if not hits:continue
 ga,gb=group(a.name),group(b.name);pts=[sum(triangles[a.name][i]+triangles[b.name][j],Vector())/6 for i,j in hits];same=ga is not None and ga==gb;centers=[]
 if ga:centers.append(starts[ga])
 if gb:centers.append(starts[gb])
 if ga is None and gb is None:centers.append(Vector((0,.007,.080)))
 maxdistance=max(min((p-c).length for c in centers) for p in pts) if centers else None
 rows.append({'a':a.name,'b':b.name,'bvh_triangle_overlap_pairs':len(hits),'same_lobar_recipe_group':same,'max_overlap_centroid_distance_to_declared_attachment_m':maxdistance,'outside_12mm_attachment_region':not same and maxdistance>.012,'caveat':'BVH overlap candidates, conservative screening not proof of actual vascular/airway graph connection'})
pathlib.Path(args.output).write_text(json.dumps({'baseline':'2d2d4e269995f11179cfa423a302f144d9d163883ccde0995a2987e83dd2e898','attachment_reference':'Original build_collection.py lines126–136 at canonical0b4e3dbb; authored recipe only, not clinical anatomy','pairs':rows},indent=2));print(json.dumps([r for r in rows if r['outside_12mm_attachment_region']],indent=2));print('pairs',len(rows))
