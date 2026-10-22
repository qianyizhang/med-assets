exec(open(__file__.replace('finalize_geometry.py','refine_and_preview.py')).read().split('for ma in bpy.data.materials:')[0])
sources={o['source_file'][:-5]:o for o in bpy.data.objects if 'source_file' in o and o.get('view_role')=='surface'}
# Apply refinement to original exteriors rather than their copied section metadata.
for id,ob in sources.items():
 bpy.context.view_layer.objects.active=ob;mod=ob.modifiers.new('Display surface cleanup','SMOOTH');mod.factor=.35;mod.iterations=3;bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.to_mesh(ob.data);bm.free()
# Rebuild stomach section through anterior quartile so the complete curved body remains intelligible.
for ob in list(objects['stomach']):
 if ob.get('view_role')!='surface':objects['stomach'].remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
ob=sources['stomach'];lo,hi,c,dim=bounds(ob);cp=duplicate(ob,'Stomach | anterior teaching section','stomach','stomach_cutaway',ma=mats['stomach']);inside=bpy.data.objects.new('temp inner',ob.data.copy());s.collection.objects.link(inside)
for v in inside.data.vertices:v.co=c+(v.co-c)*.90
applybool(cp,inside);bpy.data.objects.remove(inside,do_unlink=True)
ys=sorted(v.co.y for v in ob.data.vertices);plane=ys[int(len(ys)*.24)]
bpy.ops.mesh.primitive_cube_add(size=1,location=(c.x,plane-.5,c.z));cu=bpy.context.object;applybool(cp,cu);bpy.data.objects.remove(cu,do_unlink=True);cp['cut_plane_blender_y_m']=plane
bvh=BVHTree.FromPolygons([v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons]);mat=bpy.data.materials['Gastric mucosa and rugae']
for j in range(13):
 pts=[];z=c.z+dim.z*(-.39+j*.065)
 for k in range(34):
  x=c.x+dim.x*(-.44+k*.027);zz=z+.001*math.sin(k*.8+j);hit,n,face,d=bvh.ray_cast(Vector((x,1,zz)),Vector((0,-1,0)),2)
  if hit is not None and hit.y>plane+.003:pts.append(hit-n*.0035)
 if len(pts)>4:tube('Gastric ruga '+str(j+1),pts,.00095,'stomach','gastric_ruga_'+str(j+1),mat)
# Shrink the renal pelvis slightly to reveal calyceal joining points.
for id in ['kidney_left','kidney_right']:
 for ob in objects[id]:
  if ob.get('anatomy_id')==id+'_pelvis':
   for v in ob.data.vertices:v.co.x*=.60;v.co.y*=.70;v.co.z*=.72
  if '_pyramid_' in ob.get('anatomy_id',''):
   # Slightly narrower bases leave clear cortical columns between representative pyramids.
   for v in ob.data.vertices:v.co.y*=.8
# Remove tiny isolated pancreatic surface components (keep substantive shape; report counts).
ob=sources['pancreas'];bm=bmesh.new();bm.from_mesh(ob.data);unseen=set(bm.verts);components=[]
while unseen:
 todo=[unseen.pop()];found=[]
 while todo:
  v=todo.pop();found.append(v)
  for e in v.link_edges:
   w=e.other_vert(v)
   if w in unseen:unseen.remove(w);todo.append(w)
 components.append(found)
large=max(map(len,components));small=[v for comp in components if len(comp)<large*.01 for v in comp]
if small:bmesh.ops.delete(bm,geom=small,context='VERTS')
bm.to_mesh(ob.data);bm.free();ob['removed_tiny_component_vertices']=len(small)
# Collection geometry and materials are final before baking.
for id,obs in objects.items():
 for ob in obs:
  if ob.type=='MESH' and len(ob.data.materials):
   ma=ob.data.materials[0]
   if 'clinical_color' in ma:ob['clinical_color']=ma['clinical_color']
json.dump({id:[o.name for o in obs] for id,obs in objects.items()},open(R/'object_map.json','w'),indent=2)
ctrl['cutaway']=0;ctrl['material_mode']=0
for id,col in collections.items():col.hide_render=(id=='heart_detailed');col.hide_viewport=(id=='heart_detailed')
s.camera=bpy.data.objects['CAM · complete assembly'];bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop.blend'),compress=True)
print('GEOMETRY FINALIZED',flush=True)
