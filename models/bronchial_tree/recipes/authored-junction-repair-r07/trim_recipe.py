import bpy,bmesh,pathlib,json,hashlib,argparse,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D=pathlib.Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--output',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);O=pathlib.Path(a.output);O.mkdir(parents=True,exist_ok=True);P=pathlib.Path(a.baseline);assert hashlib.sha256(P.read_bytes()).hexdigest()=='2d2d4e269995f11179cfa423a302f144d9d163883ccde0995a2987e83dd2e898';bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(P));originals=[o for o in bpy.context.scene.objects if o.type=='MESH'];new=[];records=[]
starts={'lung_upper_lobe_right':Vector((-.028,.009,.060)),'lung_middle_lobe_right':Vector((-.042,.008,.033)),'lung_lower_lobe_right':Vector((-.042,.008,.033)),'lung_upper_lobe_left':Vector((.042,.008,.068)),'lung_lower_lobe_left':Vector((.042,.008,.068))}
for lobe,start in starts.items():
 j=json.load(open(D/'recipe-source'/(lobe+'.json')));v=[Vector((-p[0]/1000,-(p[1]-155)/1000,(p[2]-430)/1000)) for p in j['vertices']];me=bpy.data.meshes.new('recipe source bounds');me.from_pydata(v,[],j['faces']);me.update();src=bpy.data.objects.new('recipe source bounds',me);bpy.context.scene.collection.objects.link(src);bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0000003);seen=set();dups=[]
 for f in bm.faces:
  key=frozenset(f.verts)
  if key in seen or f.calc_area()<1e-12:dups.append(f)
  else:seen.add(key)
 if dups:bmesh.ops.delete(bm,geom=dups,context='FACES')
 boundary=[e for e in bm.edges if e.is_boundary]
 if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();bpy.context.view_layer.objects.active=src;mod=src.modifiers.new('Original display subdivision','SUBSURF');mod.levels=1;bpy.ops.object.modifier_apply(modifier=mod.name);v=[x.co.copy() for x in src.data.vertices];bpy.data.objects.remove(src,do_unlink=True);lo=Vector([min(p[k] for p in v) for k in range(3)]);hi=Vector([max(p[k] for p in v) for k in range(3)]);cc=(lo+hi)/2;dm=hi-lo;end=cc+Vector((0,dm.y*.05,dm.z*.05));mid=start.lerp(end,.55)
 for k in range(3):
  name=lobe+' distal illustration '+str(k+1);old=bpy.data.objects[name];dest=cc+Vector(((k-1)*dm.x*.18,dm.y*(.10 if k%2 else -.12),dm.z*(.22 if k==1 else -.20)));cu=bpy.data.curves.new('Exact original recipe centerline','CURVE');cu.dimensions='3D';cu.resolution_u=16;cu.bevel_depth=.0017;cu.bevel_resolution=3;cu.use_fill_caps=True;sp=cu.splines.new('BEZIER');sp.bezier_points.add(2)
  for p,co,rad in zip(sp.bezier_points,[mid,end,dest],[1,.8,.32]):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO';p.radius=rad
  tmp=bpy.data.objects.new('Temporary original recipe reconstruction',cu);bpy.context.scene.collection.objects.link(tmp);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();e=tmp.evaluated_get(dg);em=e.to_mesh();oldtree=BVHTree.FromPolygons([old.matrix_world@x.co for x in old.data.vertices],[list(p.vertices) for p in old.data.polygons]);drift=max(oldtree.find_nearest(x.co)[3] for x in em.vertices);e.to_mesh_clear()
  points=[sp.bezier_points[i] for i in [1,2]];control=[points[0].co.copy(),points[0].handle_right.copy(),points[1].handle_left.copy(),points[1].co.copy()];out=bpy.data.curves.new('Trimmed original distal segment','CURVE');out.dimensions='3D';out.resolution_u=16;out.bevel_depth=.0017;out.bevel_resolution=3;out.use_fill_caps=True;s=out.splines.new('BEZIER');s.bezier_points.add(1)
  for p,src in zip(s.bezier_points,points):
   p.co=src.co;p.handle_left_type='FREE';p.handle_right_type='FREE';p.handle_left=src.handle_left;p.handle_right=src.handle_right;p.radius=src.radius;p.tilt=src.tilt
  copied=[s.bezier_points[0].co.copy(),s.bezier_points[0].handle_right.copy(),s.bezier_points[1].handle_left.copy(),s.bezier_points[1].co.copy()];assert control==copied
  ob=bpy.data.objects.new(name+' trimmed',out);bpy.context.scene.collection.objects.link(ob);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH');ob=bpy.context.object;old.name=name+' historical';ob.name=name
  for p in ob.data.polygons:p.use_smooth=True
  ob['derivation']='Authored schematic; exact original end-to-dest Bezier segment retained; redundant mid-to-end segment omitted';ob['clinical_status']='No clinical route validation';new.append(ob);records.append({'name':name,'removed_redundant_start':list(mid),'retained_bezier_control_points':[list(p) for p in control],'copied_controls_exact':control==copied,'retained_radii':[.8,.32],'bevel_depth':.0017,'original_recipe_reconstruction_max_vertex_to_baseline_surface_m':drift});bpy.data.objects.remove(tmp,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in originals:
 if 'distal illustration' not in o.name:o.select_set(True)
for o in new:o.select_set(True)
bpy.context.view_layer.objects.active=new[0];p=O/'recipe_trimmed_routes.glb';bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_extras=True,export_animations=False);(O/'proof.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'export_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'generator_source':'Canonical build_collection.py lines126–136; authored graphic recipe, not clinical anatomy','retained_node_count':23,'retained_distal_terminal_count':15,'records':records,'scope':'No terminal repositioning or new anatomical routes; removes redundant duplicate-stem implementation, not a patient airway repair'},indent=2));print('max recipe discrepancy',max(r['original_recipe_reconstruction_max_vertex_to_baseline_surface_m'] for r in records))
