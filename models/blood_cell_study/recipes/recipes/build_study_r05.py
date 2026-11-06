"""AUTHORED blood-cell teaching study. No scanned/measured/patient geometry.
All geometry and palette here are independently authored; see provenance.json.
"""
import bpy,bmesh,math,json,pathlib,hashlib,random
from mathutils import Vector,Matrix
D=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
def material(name,color,rough=.6):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=0;m.diffuse_color=(*color,1);return m
rbc_mat=material('AUTHORED crimson | not measured natural color',(.47,.032,.055),.5)
cyto_mat=material('AUTHORED pale cytoplasm | opaque outer boundary',(.50,.47,.50),.6)
cut_mat=material('AUTHORED cut face | pedagogical section',(.32,.23,.33),.7)
nuc_mat=material('AUTHORED nucleus violet | illustrative color',(.075,.025,.12),.58)
gran_mat=material('AUTHORED selected cytoplasm granules | not measured count',(.34,.16,.40),.7)
plt_mat=material('AUTHORED platelet ochre | illustrative color',(.64,.36,.085),.7)
objects=[]
def meta(o,role,label):
 o['authorship']='independently authored educational schematic; not microscopy or patient data';o['structure']=label;o['view_role']=role;o['scale']='illustrative relative dimensions; not measured micrometres';objects.append(o);return o
def meshobj(name,vs,fs,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 return o
def rbc(name,loc,rot):
 M=128;N=48;vs=[(0,0,.15)];fs=[]
 # Full meridional path: upper center -> outer rim -> lower center.
 for k in range(1,2*N):
  a=math.pi*k/(2*N);r=math.sin(a);z=math.cos(a)*(.15+.62*r*r-.28*r**4)
  for j in range(M):
   t=2*math.pi*j/M;vs.append((r*math.cos(t),r*math.sin(t),z))
 bot=len(vs);vs.append((0,0,-.15))
 for j in range(M):fs.append((0,1+j,1+(j+1)%M))
 for k in range(2*N-2):
  a=1+k*M;b=a+M
  for j in range(M): q=(j+1)%M;fs.append((a+j,b+j,b+q,a+q))
 a=1+(2*N-2)*M
 for j in range(M):fs.append((a+j,bot,a+(j+1)%M))
 o=meshobj(name,vs,fs,rbc_mat);o.location=loc;o.rotation_euler=rot
 return meta(o,'closed erythrocyte exterior','biconcave erythrocyte; no nucleus; no perforation')
def ellipsoid(name,loc,scale,mat,segments=64,rings=32):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def tube(name,coords,radius,mat):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=radius;c.bevel_resolution=5;c.use_fill_caps=True
 s=c.splines.new('BEZIER');s.bezier_points.add(len(coords)-1)
 for p,co in zip(s.bezier_points,coords):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(mat);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');return bpy.context.object
# Study layout is separate display specimens, not a blood smear or population field.
r1=rbc('RBC_A_closed_biconcave',(-3.75,0,.9),(math.radians(67),math.radians(-12),math.radians(8)))
r2=rbc('RBC_B_closed_biconcave_profile',(-3.75,.05,-1.45),(math.radians(20),math.radians(8),math.radians(-15)))
# All nuclear components authored around a shared neutrophil local origin.
parts=[]
for i,(loc,scale,angle) in enumerate([((-.49,-.04,.28),(.31,.29,.53),.28),((.46,-.02,.30),(.30,.27,.49),-.22),((.02,-.06,-.55),(.50,.28,.27),.13)]):
 o=ellipsoid('nuclear lobe '+str(i),loc,scale,nuc_mat)
 # Smooth low-order bean-like bending, not random surface noise or measured nuclear morphology.
 for v in o.data.vertices:
  if i==0:v.co.x+=.11*(v.co.z/.53)**2
  elif i==1:v.co.x-=.10*(v.co.z/.49)**2
  else:v.co.z+=.09*(v.co.x/.50)**2
 o.rotation_euler[1]=angle;parts.append(o)

parts.append(tube('nuclear neck 01',[(-.35,-.03,.53),(-.05,-.03,.66),(.30,-.03,.52)],.105,nuc_mat))
parts.append(tube('nuclear neck 12',[(.52,-.04,.08),(.42,-.06,-.20),(.24,-.06,-.44)],.105,nuc_mat))
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();nucleus=bpy.context.object;nucleus.name='NEUTROPHIL_INTACT_one_connected_segmented_nucleus';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
rem=nucleus.modifiers.new('authored union voxel remesh','REMESH');rem.mode='VOXEL';rem.voxel_size=.024;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
sm=nucleus.modifiers.new('limited authored surface fairing','SMOOTH');sm.factor=.45;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
meta(nucleus,'internal nucleus hidden by intact cell exterior','one connected three-lobed illustrative neutrophil nucleus')
# A cytoplasm sphere minus nucleus provides disjoint tissue volumes, no arbitrary external beads.
cyto=ellipsoid('NEUTROPHIL_INTACT_cytoplasm_and_closed_outer_boundary',(0,0,0),(1.45,1.45,1.45),cyto_mat,96,64)
bpy.context.view_layer.objects.active=cyto
bo=cyto.modifiers.new('exclude exact authored nucleus volume','BOOLEAN');bo.operation='DIFFERENCE';bo.solver='EXACT';bo.object=nucleus;bpy.ops.object.modifier_apply(modifier=bo.name)
meta(cyto,'closed neutrophil exterior','cytoplasm encloses same connected nucleus as cutaway')
# Derivative cutaway: duplicate same cytoplasm/nucleus; remove the front half of cytoplasm only.
shift=Vector((3.65,0,0))
cut=cyto.copy();cut.data=cyto.data.copy();bpy.context.collection.objects.link(cut);cut.name='NEUTROPHIL_CUTAWAY_front_half_cytoplasm_removed';cut.data.materials.append(cut_mat)
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,-2,0));cutter=bpy.context.object;cutter.name='temporary front-half cutter';cutter.scale=(3,2.02,3);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
cutter.data.materials.append(cyto_mat);cutter.data.materials.append(cut_mat)
for p in cutter.data.polygons:p.material_index=1
bpy.context.view_layer.objects.active=cut;bo=cut.modifiers.new('AUTHORED cutaway y less than 0.02 removed','BOOLEAN');bo.operation='DIFFERENCE';bo.solver='EXACT';bo.object=cutter;bpy.ops.object.modifier_apply(modifier=bo.name);bpy.data.objects.remove(cutter,do_unlink=True)
# Flat cut plane must not receive smooth normals across its exposed section.
for p in cut.data.polygons:
 if all(abs(cut.data.vertices[i].co.y-.02)<1e-5 for i in p.vertices):p.use_smooth=False;p.material_index=1
cut.location+=shift;meta(cut,'explicit cutaway; front half cytoplasm removed','same authored cell, cutaway at y=0.02, nucleus kept intact')
nc=nucleus.copy();nc.data=nucleus.data.copy();bpy.context.collection.objects.link(nc);nc.name='NEUTROPHIL_CUTAWAY_same_connected_nucleus';nc.location+=shift;meta(nc,'internal nucleus exposed only by cutaway','duplicate of intact nucleus; same mesh coordinates')
# Sparse, stylized granules embedded just behind cut plane. They are selected representatives, not granule number/density.
rng=random.Random(20261023);granules=[]
for i in range(34):
 for tries in range(200):
  x=rng.uniform(-1.25,1.25);z=rng.uniform(-1.25,1.25);y=rng.uniform(.025,.065)
  if x*x+z*z<1.28**2 and all(((x-a)/.50)**2+((z-b)/.50)**2>1 for a,b in [(-.49,.31),(.46,.30),(.02,-.55)]) and not (-.35<x<.35 and .35<z<.78):break
 else: continue
 size=rng.uniform(.026,.043);g=ellipsoid('NEUTROPHIL_INTACT_selected_granule_%02d'%i,(x,y,z),(size,size,size),gran_mat,16,8);meta(g,'internal illustrative granule','selected schematic granule; count/size arbitrary')
 gc=g.copy();gc.data=g.data.copy();bpy.context.collection.objects.link(gc);gc.location+=shift;gc.name='NEUTROPHIL_CUTAWAY_selected_granule_%02d'%i;meta(gc,'internal illustrative granule exposed by cutaway','same selected schematic granule; count/size arbitrary')
for i,(loc,rot) in enumerate([((-.85,0,-2.30),(.5,.2,.2)),((.20,.1,-2.40),(1.0,.25,-.4)),((1.15,0,-2.20),(.3,-.1,.2))]):
 o=ellipsoid('PLATELET_%02d_closed_disc'%i,loc,(.34,.34,.105),plt_mat,48,24);o.rotation_euler=rot;meta(o,'closed platelet exterior','small oblate illustrative platelet; no nucleus, no activation claim')
# Exported text annotations make cutaway status visible even in a generic viewer.
labelmat=material('AUTHORED annotation gray; not anatomy',(.48,.48,.48),.8)
for name,body,pos,size in [('RBC','ERYTHROCYTES',(-3.75,-.15,-2.60),.19),('INTACT','INTACT',(0,-.15,-1.78),.19),('CUTAWAY','CUTAWAY',(3.65,-.15,-1.78),.19),('PLATELET','PLATELETS',(.15,-.15,-2.85),.18)]:
 c=bpy.data.curves.new('label '+name,'FONT');c.body=body;c.align_x='CENTER';c.size=size;c.extrude=.002;c.bevel_depth=0;c.resolution_u=4
 o=bpy.data.objects.new('ANNOTATION_'+name,c);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(math.pi/2,0,0);c.materials.append(labelmat)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7);bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7);bm.to_mesh(o.data);bm.free();meta(o,'annotation not anatomy','text display annotation: '+body)
# Repair Bfont collinear cap triangulation without changing glyph silhouette.
# A zero-area triangle A-B-C has B on edge A-C; split its neighbour along A-C at B.
label_repairs=[]
for o in objects:
 if not o.name.startswith('ANNOTATION_'):continue
 o.data.calc_loop_triangles();vs=[v.co.copy() for v in o.data.vertices];fs=[tuple(t.vertices) for t in o.data.loop_triangles];count=0
 while True:
  bad=next((i for i,f in enumerate(fs) if len(f)==3 and (vs[f[1]]-vs[f[0]]).cross(vs[f[2]]-vs[f[0]]).length/2<1e-12),None)
  if bad is None:break
  f=fs[bad];aa,bb=max([(f[0],f[1]),(f[1],f[2]),(f[2],f[0])],key=lambda e:(vs[e[0]]-vs[e[1]]).length);mid=next(v for v in f if v not in (aa,bb))
  found=False
  for k,g in enumerate(fs):
   if k==bad or aa not in g or bb not in g:continue
   for ii in range(3):
    a,b=g[ii],g[(ii+1)%3];other=g[(ii+2)%3]
    if {a,b}=={aa,bb}:
     fs[k]=(a,mid,other);fs.append((mid,b,other));fs.pop(bad);count+=1;found=True;break
   if found:break
  if not found:raise RuntimeError('No neighbour for collinear annotation cap')
 me=bpy.data.meshes.new(o.data.name+' cleaned');me.from_pydata(vs,[],fs);me.materials.append(labelmat);me.update();o.data=me;label_repairs.append({'node':o.name,'collinearCapsRetriangulated':count})
# Parent properties survive glTF extras. No body registration or patient axes are implied.
for o in objects:o['arrangement']='separate display specimens; not counts, concentrations, proportions or in-vivo arrangement'
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
out=D/'models/blood-cell-authored-study-r05.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=str(D/'models/blood-cell-authored-study-r05.blend'))
# Quantitative design diagnostics (not measured biological data).
co=[v.co for v in nucleus.data.vertices];maxrad=max(v.length for v in co)
bm=bmesh.new();bm.from_mesh(nucleus.data);components=0;seen=set()
for v in bm.verts:
 if v.index in seen:continue
 components+=1;stack=[v];seen.add(v.index)
 while stack:
  x=stack.pop()
  for e in x.link_edges:
   y=e.other_vert(x)
   if y.index not in seen:seen.add(y.index);stack.append(y)
bm.free()
j={'export':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'blender':bpy.app.version_string,'nucleusMaxRadius':maxrad,'intactCellOuterRadius':1.45,'nucleusMinimumOuterBoundaryClearance':1.45-maxrad,'nucleusGraphConnectedComponents':components,'cutawayNucleusSameLocalGeometry':True,'RBCFormula':'r=sin(a), z=cos(a)*(0.15+0.62*r^2-0.28*r^4), a in [0,pi]; x=r cos(theta), y=r sin(theta); unique closed poles','RBCAuthoredDiameter':2.0,'RBCAuthoredCenterThickness':.30,'neutrophilAuthoredDiameter':2.90,'plateletAuthoredDiameter':.68,'unitMeaning':'arbitrary display units, not measured micrometres','allGeometryAuthored':True,'annotationTriangulationRepairs':label_repairs,'runtime':'unverified'}
(D/'reviews/build-r05.json').write_text(json.dumps(j,indent=2));print(json.dumps(j,indent=2))
