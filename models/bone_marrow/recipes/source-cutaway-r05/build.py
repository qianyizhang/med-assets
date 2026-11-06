import bpy,bmesh,numpy as np,math,json,random,sys,argparse,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);S=Path(args.source);O=Path(args.out)
if hashlib.sha256(S.read_bytes()).hexdigest()!='d224985628cc62d0c9c4284019b73505c9ebf14d78d30a040d74a7b33c68620e':raise ValueError('Pinned source hash mismatch')
if O.exists():raise ValueError('Output must be new')
O.mkdir(parents=True);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(S),merge_vertices=True);src=next(o for o in bpy.context.scene.objects if o.name=='FJ3259 left femur')
for other in list(bpy.context.scene.objects):
 if other!=src:bpy.data.objects.remove(other,do_unlink=True)
bpy.context.view_layer.objects.active=src;src.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);src.data.update()
# Weld only bit-identical positions before offsetting; no surface displacement.
bm=bmesh.new();bm.from_mesh(src.data);seen={};tm={}
for v in bm.verts:
 key=tuple(v.co)
 if key in seen:tm[v]=seen[key]
 else:seen[key]=v
bmesh.ops.weld_verts(bm,targetmap=tm);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(src.data);bm.free();src.data.update();raw=src.copy();raw.data=src.data.copy();bpy.context.collection.objects.link(raw);raw.hide_render=True;raw.hide_viewport=True
V=np.array([v.co[:] for v in src.data.vertices]);F=[p.vertices[:] for p in src.data.polygons];tree=BVHTree.FromPolygons(V.tolist(),F,all_triangles=True)
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.74;return m
bone=mat('Cortical / trabecular bone - teaching color',(.63,.56,.43));red=mat('Red marrow - illustrative exposed backing',(.35,.055,.065));yellow=mat('Yellow marrow - illustrative',(.62,.38,.065))
def clip(o,cuty=-.080,cutz=.690,fill=False):
 bm=bmesh.new();bm.from_mesh(o.data)
 for co,no in [((0,cuty,0),(0,1,0)),((0,0,cutz),(0,0,1))]:
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=co,plane_no=no,clear_inner=True,clear_outer=False)
 if fill:bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free();o.data.update()
src.name='Source exterior with authored cortical shell - cut after offset';src.data.materials.clear();src.data.materials.append(bone)
# Local authored inner-offset correction; source exterior remains fixed.
vg=src.vertex_groups.new(name='Bounded illustrative inset near concave source feature');center=Vector((.12258849,-.05768254,.80282640));weights=[]
for v in src.data.vertices:
 d=(v.co-center).length
 if d<=.0035:w=.15
 elif d>=.007:w=1.
 else:w=.15+.85*(.5-.5*math.cos(math.pi*(d-.0035)/.0035))
 vg.add([v.index],w,'REPLACE');weights.append(w)
mod=src.modifiers.new('Illustrative inward shell before cut','SOLIDIFY');mod.thickness=.002;mod.offset=-1;mod.vertex_group=vg.name;mod.thickness_vertex_group=0;mod.use_even_offset=True;mod.thickness_clamp=.5;mod.use_thickness_angle_clamp=True;bpy.ops.object.modifier_apply(modifier=mod.name)
for loc,scale in [((.1,-.58,.5),(1,.5,1)),((.1,0,-.31),(1,1,1))]:
 bpy.ops.mesh.primitive_cube_add(size=2,location=loc);cut=bpy.context.object;cut.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.context.view_layer.objects.active=src;mod=src.modifiers.new('Declared planar teaching cut','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
for p in src.data.polygons:p.use_smooth=True
# Inner display volumes: source envelope offset, then exposed cutback. Not segmentation.
def inner(name,material,zlo,zhi,cuty):
 o=raw.copy();o.data=raw.data.copy();bpy.context.collection.objects.link(o);o.hide_render=False;o.hide_viewport=False;o.name=name
 for v in o.data.vertices:v.co-=v.normal*.003
 clip(o,cuty,zlo,True)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=(0,0,zhi),plane_no=(0,0,-1),clear_inner=True);bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free();o.data.materials.clear();o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
mar=inner('Illustrative marrow - partially removed, color transition not physiological boundary',red,.693,.84,-.074)
bm=bmesh.new();bm.from_mesh(mar.data)
for zz in np.arange(.728,.763,.004):bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=(0,0,float(zz)),plane_no=(0,0,1))
bm.to_mesh(mar.data);bm.free();attr=mar.data.color_attributes.new(name='Illustrative marrow color',type='FLOAT_COLOR',domain='CORNER')
for p in mar.data.polygons:
 for li in p.loop_indices:
  zz=mar.data.vertices[mar.data.loops[li].vertex_index].co.z;tt=max(0,min(1,(zz-.73)/.025));tt=tt*tt*(3-2*tt);attr.data[li].color=tuple((1-tt)*a+tt*b for a,b in zip((.62,.38,.065,1),(.35,.055,.065,1)))
mm=mat('Marrow color is illustrative, not age-specific distribution',(.4,.2,.1));n=mm.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name=attr.name;mm.node_tree.links.new(n.outputs['Color'],mm.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);mar.data.materials.clear();mar.data.materials.append(mm)
# Connected sample lattice, only inside source envelope and away from shell.
rng=random.Random(261026);nodes=[]
def inside(p):
 hit,n,idx,d=tree.find_nearest(p)
 if hit is None or d<.0027:return False
 return (Vector(p)-hit).dot(n)<0
# Poisson-like random samples: irregular connected scaffold, no periodic lattice.
for attempt in range(80000):
 p=Vector((rng.uniform(.035,.153),rng.uniform(-.079,-.048),rng.uniform(.741,.833)))
 if not inside(p):continue
 if any((p-q).length<.0032 for q in nodes):continue
 nodes.append(p)
 if len(nodes)>=1100:break
A=np.array(nodes);edges=set()
for i,p in enumerate(nodes):
 ds=np.linalg.norm(A-np.array(p),axis=1)
 for j in np.argsort(ds)[1:6]:
  if ds[j]>.008:continue
  if all(inside(p.lerp(nodes[j],t)) for t in [.25,.5,.75]):edges.add(tuple(sorted((i,int(j)))))
adj={i:set() for i in range(len(nodes))}
for a,b in edges:adj[a].add(b);adj[b].add(a)
seen=set();comps=[]
for i in adj:
 if i in seen:continue
 stack=[i];c=set()
 while stack:
  q=stack.pop()
  if q in c:continue
  c.add(q);stack.extend(adj[q]-c)
 seen|=c;comps.append(c)
keep=max(comps,key=len);edges=[e for e in edges if e[0] in keep and e[1] in keep]
# Explicit source-envelope attachments: illustrative struts extend into inner cortical boundary.
attachments=[]
for i in sorted(keep):
 p=nodes[i];hit,n,idx,d=tree.find_nearest(p)
 if d<.0055 and i%3==0:
  endpoint=hit-n*.0017
  if endpoint.y>=-.080 and endpoint.z>.741:
   nodes.append(endpoint);attachments.append((i,len(nodes)-1))
edges.extend(attachments)
cu=bpy.data.curves.new('Connected illustrative trabecular graph','CURVE');cu.dimensions='3D';cu.bevel_depth=.00043;cu.bevel_resolution=2;cu.resolution_u=1;cu.use_fill_caps=True
for a,b in edges:
 sp=cu.splines.new('POLY');sp.points.add(1);sp.points[0].co=(*nodes[a],1);sp.points[1].co=(*nodes[b],1);rr=rng.uniform(.7,1.45);sp.points[0].radius=rr;sp.points[1].radius=rr
o=bpy.data.objects.new('Connected illustrative trabecular network - not patient microarchitecture',cu);bpy.context.collection.objects.link(o);o.data.materials.append(bone);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');m=o.modifiers.new('Join network intersections','REMESH');m.mode='VOXEL';m.voxel_size=.00028;m.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=m.name);m=o.modifiers.new('Bounded network surface smoothing','SMOOTH');m.factor=.6;m.iterations=3;bpy.ops.object.modifier_apply(modifier=m.name)
# Inspect generated voxel islands; remove only tiny8-vertex artifacts, never source anatomy.
bm=bmesh.new();bm.from_mesh(o.data);seen=set();components=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];part=set()
 while stack:
  q=stack.pop()
  if q in part:continue
  part.add(q);stack.extend(e.other_vert(q) for e in q.link_edges if e.other_vert(q) not in part)
 seen|=part;components.append(part)
components.sort(key=len,reverse=True);islands=[]
for part in components[1:]:
 coords=np.array([v.co[:] for v in part]);span=coords.max(0)-coords.min(0);islands.append({'vertices':len(part),'bounds':[coords.min(0).tolist(),coords.max(0).tolist()],'span':span.tolist()})
 if len(part)>8 or max(span)>.00056:raise ValueError('Unexpected generated disconnected component; do not silently remove')
 bmesh.ops.delete(bm,geom=list(part),context='VERTS')
bm.to_mesh(o.data);bm.free()
# Network-only display simplification; all source/cortex/marrow meshes untouched.
pre=len(o.data.polygons);m=o.modifiers.new('Network display tessellation reduction','DECIMATE');m.ratio=.35;bpy.ops.object.modifier_apply(modifier=m.name);post=len(o.data.polygons)
for p in o.data.polygons:p.use_smooth=True
bpy.data.objects.remove(raw,do_unlink=True)
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':
  for key in list(ob.keys()):del ob[key]
  ob['representation']='BP3D femur exterior with authored cortical offset, marrow and trabecular network';ob['limits']='Not CT microarchitecture, measured cortex, age-specific distribution or clinical model';ob['cutaway']='Proximal fragment and anterior display window; front marrow partly removed'
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(O/'marrow_cutaway.glb'),export_format='GLB',export_extras=True);(O/'record.json').write_text(json.dumps({'source_object':'FJ3259 left femur','source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((O/'marrow_cutaway.glb').read_bytes()).hexdigest(),'local_inset_support':{'center':list(center),'inner_radius_m':.0035,'outer_radius_m':.007,'min_weight':.15,'modified_vertex_weights':sum(w<1 for w in weights)},'whole_original_status':'Needs revision','count_delta':0,'scope':'Authored interior cutaway on source-derived exterior, not patient cortex or trabecular segmentation','nodes_in_largest_graph':len(keep),'edges':len(edges),'discarded_sample_nodes':len(nodes)-len(keep)-len(attachments),'cortical_attachment_struts':len(attachments),'illustrative_cortical_offset_m':.002,'source_exact_coordinate_weld':True,'generated_islands_removed':islands,'network_faces_before_decimation':pre,'network_faces_after_decimation':post,'marrow_cutback':'front marrow partly removed to expose network; empty display space is not anatomical air'},indent=2))
