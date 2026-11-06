import bpy,bmesh,pathlib,json,hashlib,math,argparse,sys
from mathutils import Vector,Quaternion,kdtree
from mathutils.bvhtree import BVHTree
D=pathlib.Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--skip-renders',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);W=pathlib.Path(args.work);O=W/'result';O.mkdir(parents=True,exist_ok=True);P=W/'recipe-trim-input/recipe_trimmed_routes.glb';bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(P));obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];vs=[];fs=[];norms=[];localtrees={};localtris={};contactpoints=[]
mat=bpy.data.materials.new('Neutral schematic diagnostic');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.44,.39,.34,1);bs.inputs['Roughness'].default_value=.8
for o in obs:
 o.data.materials.clear();o.data.materials.append(mat);o.data.calc_loop_triangles();v=[o.matrix_world@x.co for x in o.data.vertices];f=[list(t.vertices) for t in o.data.loop_triangles];localtrees[o.name]=BVHTree.FromPolygons(v,f,all_triangles=True);localtris[o.name]=[[v[i] for i in t] for t in f];off=len(vs);vs.extend(v);fs.extend([[i+off for i in t] for t in f]);corner=[Vector((0,0,0)) for x in o.data.vertices]
 for loop in o.data.loops:corner[loop.vertex_index]+=o.data.corner_normals[loop.index].vector
 norms.extend([(o.matrix_world.to_3x3()@n).normalized() for n in corner])
for row in json.load(open(W/'trim-contact-audit.json'))['pairs']:
 a,b=row['a'],row['b']
 if row['outside_12mm_attachment_region']:raise ValueError('Unexpected cross-group contact; union not allowed')
 for i,j in localtrees[a].overlap(localtrees[b]):contactpoints.append(sum(localtris[a][i]+localtris[b][j],Vector())/6)
pts={tuple(round(x/.0005)*.0005 for x in p) for p in contactpoints};kd=kdtree.KDTree(len(pts))
for i,p in enumerate(pts):kd.insert(Vector(p),i)
kd.balance();tree=BVHTree.FromPolygons(vs,fs,all_triangles=True);me=bpy.data.meshes.new('Existing authored surfaces combined');me.from_pydata(vs,[],fs);me.update();candidate=bpy.data.objects.new('Authored bronchial junction-consolidation experiment',me);bpy.context.scene.collection.objects.link(candidate);me.materials.append(mat);bpy.context.view_layer.objects.active=candidate;m=candidate.modifiers.new('Uniform union support','REMESH');m.mode='VOXEL';m.voxel_size=.0003;m.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=m.name);bm=bmesh.new();bm.from_mesh(candidate.data);sel=[v for v in bm.verts if kd.find(v.co)[2]<.005];weights={v:(1 if kd.find(v.co)[2]<.001 else .5*(1+math.cos(math.pi*(kd.find(v.co)[2]-.001)/.004))) for v in sel}
for _ in range(24):
 prev={v:v.co.copy() for v in sel};bmesh.ops.smooth_vert(bm,verts=sel,factor=.3,use_axis_x=True,use_axis_y=True,use_axis_z=True)
 for v in sel:
  v.co=prev[v]+(v.co-prev[v])*weights[v];hit,n,i,d=tree.find_nearest(v.co)
  if d>.0005:v.co=hit+(v.co-hit).normalized()*.0005
remaining=set(bm.verts);components=[]
while remaining:
 todo=[remaining.pop()];cnt=0
 while todo:
  v=todo.pop();cnt+=1
  for e in v.link_edges:
   n=e.other_vert(v)
   if n in remaining:remaining.remove(n);todo.append(n)
 components.append(cnt)
chi=len(bm.verts)-len(bm.edges)+len(bm.faces);r={'input_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'baseline_sha256':'2d2d4e269995f11179cfa423a302f144d9d163883ccde0995a2987e83dd2e898','method':'Combine 8 unchanged and 15 original-recipe distal segments after redundant stem removal;0.3mm voxel union; cosine-tapered fairing only within5mm of screened original contact regions, max0.5mm outputvertex-to-originalsurface constraint. No new routes or coordinateframe mixing.','contact_clusters':len(pts),'contact_gate':'All cross-group overlap candidates within declared12mm attachment regions; originalrecipe supports contacts, not anatomy','vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'euler_characteristic':chi,'components_vertices':components,'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area':sum(f.calc_area()==0 for f in bm.faces),'topology_gate':len(components)==1 and chi==2 and all(e.is_manifold for e in bm.edges),'max_outputvertex_to_originalsurface_distance_m':max(tree.find_nearest(v.co)[3] for v in bm.verts),'distance_scope':'Nearest triangle in 23 trimmed-input surfaces; unidirectional vertex sample, not fullHausdorff proof'};bm.to_mesh(candidate.data);bm.free()
candidate.data.update()
for p in candidate.data.polygons:p.use_smooth=True
newnormals=[]
for v in candidate.data.vertices:
 w=min(1,max(0,(kd.find(v.co)[2]-.005)/.003));auto=v.normal.copy()
 if w==0:newnormals.append(tuple(auto));continue
 hit,n,idx,d=tree.find_nearest(v.co);ia,ib,ic=fs[idx];a,b,c=vs[ia],vs[ib],vs[ic];ab=b-a;ac=c-a;ap=hit-a;d00=ab.dot(ab);d01=ab.dot(ac);d11=ac.dot(ac);d20=ap.dot(ab);d21=ap.dot(ac);den=d00*d11-d01*d01
 if abs(den)<1e-20:interp=n
 else:
  v0=(d11*d20-d01*d21)/den;w0=(d00*d21-d01*d20)/den;interp=(norms[ia]*(1-v0-w0)+norms[ib]*v0+norms[ic]*w0).normalized()
 newnormals.append(tuple((auto*(1-w)+interp*w).normalized()))
candidate.data.normals_split_custom_set_from_vertices(newnormals);candidate.data.calc_loop_triangles();outtree=BVHTree.FromPolygons([v.co for v in candidate.data.vertices],[list(t.vertices) for t in candidate.data.loop_triangles],all_triangles=True)
ends=[('distal tracheal teaching-axis top',Vector((.003,.006,.140)))];starts={'lung_upper_lobe_right':Vector((-.028,.009,.060)),'lung_middle_lobe_right':Vector((-.042,.008,.033)),'lung_lower_lobe_right':Vector((-.042,.008,.033)),'lung_upper_lobe_left':Vector((.042,.008,.068)),'lung_lower_lobe_left':Vector((.042,.008,.068))}
for row in json.load(open(W/'recipe-trim-input/proof.json'))['records']:ends.append((row['name'],Vector(row['retained_bezier_control_points'][-1])))
r['terminal_witnesses']=[{'name':n,'authored_recipe_position':list(p),'original_surface_distance_m':tree.find_nearest(p)[3],'candidate_surface_distance_m':outtree.find_nearest(p)[3]} for n,p in ends];r['terminal_count_scope']='16declared terminal witnesses from originalrecipe, not skeleton-extracted or clinical terminalcount';r['terminal_witness_gate']=all(x['candidate_surface_distance_m']<=x['original_surface_distance_m']+.0005 for x in r['terminal_witnesses']);r['status']='experiment pending pixel/exact-export checks; wholeanatomy not approved'
for k in list(bpy.context.scene.keys()):del bpy.context.scene[k]
candidate['derivation']='Authored schematic, not segmented anatomy';candidate['scope']='Consolidated intended junctions only; source routegraph unvalidated. Closed illustrative surface, no lumen/motion.';candidate['original_authored_node_names']=[o.name for o in obs]
bpy.ops.object.select_all(action='DESELECT');candidate.select_set(True);bpy.context.view_layer.objects.active=candidate;p=O/'bronchial_whole_junction_experiment.glb';bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_extras=True,export_animations=False);r['export_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.resolution_x=1000;sc.render.resolution_y=850;sc.render.resolution_percentage=100;sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX';oldqa=json.load(open(D/'baseline-cameras.json'));target=Vector(oldqa['cameras'][0]['target']);span=oldqa['cameras'][0]['ortho_scale']/1.12;f=span/.15
for di,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
 bpy.ops.object.light_add(type='AREA',location=target+Vector(di)*f);l=bpy.context.object;l.data.energy=power*f*f;l.data.shape='DISK';l.data.size=.4*f;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam;cams=[]
(O/'qa.json').write_text(json.dumps(r,indent=2))
if args.skip_renders:sys.exit(0)
for phase in ['candidate']:
 candidate.hide_render=phase=='baseline'
 for o in obs:o.hide_render=phase!='baseline'
 for name,di in [('front',(0,-1,0)),('oblique',(.8,-1,.3)),('main_close',(0,-1,.1)),('left_lobar_close',(0,-1,.1))]:
  t=Vector((0,.0075,.082)) if name=='main_close' else Vector((.042,.008,.068)) if name=='left_lobar_close' else target;cam.data.ortho_scale=.045 if 'close' in name else span*1.12;cam.location=t+Vector(di).normalized()*span*4;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/(phase+'-'+name+'.png'));bpy.ops.render.render(write_still=True);cams.append({'phase':phase,'file':phase+'-'+name+'.png','position':list(cam.location),'target':list(t),'quaternion_wxyz':list(cam.rotation_euler.to_quaternion()),'ortho_scale':cam.data.ortho_scale})
r['cameras']=cams;(O/'qa.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(O/'review.blend'),compress=True)
