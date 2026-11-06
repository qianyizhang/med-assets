"""Original educational FDI36 external mesh. All coordinates here are authored mm.
No patient/scan input or traced images. Run: blender -b -t 8 --python build.py -- v1
"""
import bpy,bmesh,math,json,hashlib,sys,time
import numpy as np
from pathlib import Path
from mathutils import Vector
START=time.perf_counter()
OUT=Path(__file__).parent/(sys.argv[sys.argv.index('--')+1])
if OUT.exists():raise RuntimeError('Preserve attempts: choose a fresh output folder')
OUT.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
root=bpy.data.objects.new('FDI36_Authored_Educational',None);scene.collection.objects.link(root)
root['scope']='Original educational exterior. Not scanned, patient-specific, clinically validated, or a preparation guide.'
root['axes']='Blender metres: +X distal, +Y lingual, +Z occlusal. CEJ nominal z=0. GLB standard Y-up conversion.'
controls=bpy.data.collections.new('AUTHORING_INPUTS_hidden');scene.collection.children.link(controls)
# V5 replaces the joined height-field/wall crown with a tangent-continuous cap.
# Heights below are original authoring targets, not measured anatomical values.
C=[('MB',-2.65,-2.30,2.13,1.82,1.78),('DB',.95,-2.38,1.86,1.68,1.48),('D',3.60,-.90,1.36,1.48,1.10),('ML',-2.55,2.48,1.78,1.64,2.12),('DL',1.40,2.34,1.67,1.59,1.86)]
G=[([(-3.55,.05),(-2.0,-.02),(-.45,-.30),(1.12,-.12),(2.85,.38)],.22,.10),([(-.45,-.30),(-.70,-1.60),(-.62,-4.35)],.21,.085),([(1.12,-.12),(2.20,-1.55),(3.00,-3.55)],.20,.075),([(-.45,-.30),(-.35,1.45),(-.18,4.25)],.21,.085)]
def segdist(x,y,a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)));return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
def smoothstep(u):return u*u*(3-2*u)
def outline(t):
 c,s=math.cos(t),math.sin(t);n=2.45
 x=5.5*math.copysign(abs(c)**(2/n),c)*(1-.075*max(s,0))
 y=4.8*math.copysign(abs(s)**(2/n),s)*(1-.14*max(c,0))
 lobe=sum(.028*math.exp(-(math.atan2(math.sin(t-math.atan2(cy,cx)),math.cos(t-math.atan2(cy,cx)))/.36)**2) for _,cx,cy,*_ in C)
 return x*(1+lobe),y*(1+lobe)
# Invert the monotonic authored outline to obtain each control's normalized radius.
def polar_radius(x,y):
 lo,hi=0,math.pi/2
 ax,ay=abs(x),abs(y)
 for _ in range(45):
  a=(lo+hi)/2;t=a if x>=0 and y>=0 else math.pi-a if x<0<=y else math.pi+a if x<0 and y<0 else 2*math.pi-a
  xx,yy=outline(t)
  if abs(yy)/max(abs(xx),1e-12) < ay/max(ax,1e-12):lo=a
  else:hi=a
 a=(lo+hi)/2;t=a if x>=0 and y>=0 else math.pi-a if x<0<=y else math.pi+a if x<0 and y<0 else 2*math.pi-a
 xx,yy=outline(t)
 return math.hypot(x,y)/math.hypot(xx,yy)
# Cusp tips, sloping triangular ridges, bounded broad fossae, marginal ridges.
H=[(-2.65,-2.30,7.08),(.95,-2.38,6.76),(3.60,-.90,6.22),(-2.55,2.48,7.62),(1.40,2.34,7.30),
   (-1.85,-1.45,6.58),(-1.10,-.78,5.95),(.55,-1.45,6.27),(.28,-.68,5.80),
   (-1.82,1.62,6.80),(-1.05,.80,6.00),(1.08,1.48,6.55),(.65,.67,5.84),
   (2.90,-.57,5.93),(2.25,-.23,5.57),
   (-.35,-.20,5.33),(-2.96,.10,5.48),(2.95,.35,5.29),
   (-4.12,.10,6.12),(-4.00,-1.10,6.17),(-3.98,1.30,6.35),
   (3.94,.38,5.79),(3.72,1.25,5.99),
   (-1.65,-3.60,6.04),(.00,-3.70,5.93),(2.20,-3.20,5.71),
   (-1.50,3.72,6.55),(.40,3.65,6.39),
   (-.55,-3.60,5.51),(-.20,3.62,5.82)]
# A thin-plate interpolant controls actual cap heights; edge continuation is smooth.
# The cosine latitude factor guarantees a vertical tangent at the maximal contour.
EQ=2.35
points=np.array([[x,y] for x,y,z in H],float)
vals=np.array([EQ+(z-EQ)/math.sqrt(max(.04,1-polar_radius(x,y)**2)) for x,y,z in H])
def kernel(d2):return .5*d2*np.log(np.maximum(d2,1e-16))
d2=np.sum((points[:,None,:]-points[None,:,:])**2,axis=2);K=kernel(d2);K+=np.eye(len(H))*.045
P=np.column_stack((np.ones(len(H)),points));A=np.block([[K,P],[P.T,np.zeros((3,3))]])
coef=np.linalg.solve(A,np.concatenate((vals,np.zeros(3))))
def raw_height(x,y):
 d2=np.sum((points-np.array([x,y]))**2,axis=1)
 return float(np.dot(coef[:-3],kernel(d2))+coef[-3]+coef[-2]*x+coef[-1]*y)
def groove(x,y):
 # Maximum instead of sum avoids a punched crater where grooves meet.
 return max(depth*math.exp(-(min(segdist(x,y,a,b) for a,b in zip(line,line[1:]))/w)**2) for line,w,depth in G)
def height(x,y):
 r=min(.999999,polar_radius(x,y))
 return EQ+math.sqrt(1-r*r)*(raw_height(x,y)-EQ)-groove(x,y)*max(0,1-r**8)
def make(name,vs,fs):
 me=bpy.data.meshes.new(name);me.from_pydata([[v/1000 for v in p] for p in vs],[],fs);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob);return ob
N=384;R=128
vs=[(0,.65,height(0,0))];fs=[]
for j in range(1,R+1):
 phi=j/R*math.pi/2;r=math.sin(phi);c=math.cos(phi)
 for k in range(N):
  x,y=outline(k*2*math.pi/N);x*=r;y*=r
  z=EQ+c*(raw_height(x,y)-EQ)-groove(x,y)*max(0,1-r**8)
  vs.append((x,y+.65,z))
for k in range(N):fs.append((0,1+k,1+(k+1)%N))
for j in range(R-1):
 a=1+j*N;b=a+N
 for k in range(N):fs.append((a+k,b+k,b+(k+1)%N,a+(k+1)%N))
last=1+(R-1)*N
# Same vertical tangent as cap at u=0, then a smoothly constricting cervical wall.
for j in range(1,65):
 u=j/64;a=len(vs);e=smoothstep(u)
 for k in range(N):
  t=k*2*math.pi/N;x,y=outline(t)
  bottom=-2.05-.85*(abs(x)/5.5)**1.3
  z=EQ*(1-u)+bottom*u
  f=1-.26*e+.025*math.sin(math.pi*u)**2*max(0,-math.sin(t))
  tilt=.65*(1-e)
  vs.append((x*f,y*f+tilt,z))
 for k in range(N):fs.append((last+k,a+k,a+(k+1)%N,last+(k+1)%N))
 last=a
center=len(vs);vs.append((0,0,-1.85))
for k in range(N):fs.append((center,last+(k+1)%N,last+k))
parts=[make('Crown_and_root_trunk_AUTHORED',vs,fs)]

def root_mesh(name,stations):
 verts=[];faces=[];n=96
 # Smooth Catmull-Rom station sampling, authored dimensions including asymmetrical fluting.
 for j in range(97):
  u=j/96*(len(stations)-1);i=min(len(stations)-2,int(u));t=u-i
  ps=[stations[max(0,i-1)],stations[i],stations[i+1],stations[min(len(stations)-1,i+2)]]
  q=[.5*(2*ps[1][c]+(-ps[0][c]+ps[2][c])*t+(2*ps[0][c]-5*ps[1][c]+4*ps[2][c]-ps[3][c])*t*t+(-ps[0][c]+3*ps[1][c]-3*ps[2][c]+ps[3][c])*t*t*t) for c in range(5)]
  x,y,z,rx,ry=q
  for k in range(n):
   a=k*2*math.pi/n;flute=1-.13*(abs(math.cos(a))**8)*math.sin(math.pi*j/96)
   verts.append((x+max(.04,rx)*math.cos(a)*flute,y+max(.04,ry)*math.sin(a),z))
 for j in range(96):
  for k in range(n):faces.append((j*n+k,(j+1)*n+k,(j+1)*n+(k+1)%n,j*n+(k+1)%n))
 faces.append(tuple(reversed(range(n))));faces.append(tuple(range(96*n,97*n)))
 return make(name,verts,faces)
parts.append(root_mesh('Mesial_root_AUTHORED',[(-2.20,0,-1.6,2.02,3.18),(-2.65,.05,-4.0,1.65,2.90),(-3.15,.12,-7.2,1.30,2.40),(-3.05,.30,-10.8,.90,1.60),(-2.35,.50,-13.80,.15,.24)]))
parts.append(root_mesh('Distal_root_AUTHORED',[(2.15,0,-1.6,1.92,2.85),(2.60,.12,-4.0,1.60,2.45),(3.45,.25,-7.2,1.20,1.65),(4.20,.40,-10.2,.76,.95),(4.55,.55,-12.9,.16,.20)]))
# Preserve the independent editable inputs, then make one connected exterior.
for ob in parts:
 cp=ob.copy();cp.data=ob.data.copy();controls.objects.link(cp);cp.hide_render=True;cp.hide_set(True)
bpy.ops.object.select_all(action='DESELECT')
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='FDI36_Exterior_AUTHORED'
# Remesh in millimetres to avoid Blender voxel-size lower clamping at metre scale.
for v in ob.data.vertices:v.co*=1000
rem=ob.modifiers.new('Union_0.06mm','REMESH');rem.mode='VOXEL';rem.voxel_size=.06;rem.use_smooth_shade=True;actual_voxel_mm=rem.voxel_size;bpy.ops.object.modifier_apply(modifier=rem.name)
for v in ob.data.vertices:v.co/=1000
smooth=ob.modifiers.new('Subtle_surface_blend','SMOOTH');smooth.factor=.32;smooth.iterations=22;bpy.ops.object.modifier_apply(modifier=smooth.name)
vg=ob.vertex_groups.new(name='Root_transition_blend')
for v in ob.data.vertices:
 weight=max(0,min(1,(.001-v.co.z)/.002))
 if weight>0:vg.add([v.index],weight,'REPLACE')
smooth=ob.modifiers.new('Root_transition_blend','SMOOTH');smooth.vertex_group=vg.name;smooth.factor=.5;smooth.iterations=70;bpy.ops.object.modifier_apply(modifier=smooth.name)
ob.parent=root
for p in ob.data.polygons:p.use_smooth=True

def mat(name,c,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;return m
ob.data.materials.append(mat('Crown_ivory_ILLUSTRATIVE',(.84,.80,.68),.32));ob.data.materials.append(mat('Root_warm_ILLUSTRATIVE',(.77,.66,.49),.48))
for p in ob.data.polygons:p.material_index=1 if p.center.z < (.00015+.08*p.center.y+.00025*math.cos(2*math.atan2(p.center.y,p.center.x))) else 0
anchors={}
for name,x,y,*_ in C:anchors['Cusp_'+name]=(x,y+.65,height(x,y))
anchors.update({'Mesial_marginal_ridge':(-4.12,.75,height(-4.12,.10)),'Distal_marginal_ridge':(3.94,1.03,height(3.94,.38)),'Mesial_triangular_fossa':(-2.96,.75,height(-2.96,.10)),'Distal_triangular_fossa':(2.95,1.0,height(2.95,.35)),'MB_triangular_ridge':(-1.85,-.80,height(-1.85,-1.45)),'ML_triangular_ridge':(-1.82,2.27,height(-1.82,1.62)),'CEJ_origin':(0,0,0),'Central_fossa':(-.05,.45,height(-.05,-.2)),'Mesial_apex':(-2.35,.5,-13.8),'Distal_apex':(4.55,.55,-12.9)})
for name,point in anchors.items():
 a=bpy.data.objects.new(name,None);scene.collection.objects.link(a);a.parent=root;a.location=Vector(point)/1000;a.empty_display_size=.00035;a['note']='Authored landmark locator, not clinical measurement.'
params={'cusps':C,'height_control_points_mm':H,'crown_method':'thin-plate height controls on tangent-continuous cosine cap and smoothstep cervical wall','groove_centerlines':G,'nominal_outline_mm':[11,9.6],'nominal_root_lengths_mm':[13.8,12.9],'crown_tilt_offset_mm':.65,'voxel_mm':actual_voxel_mm,'units':'metres in mesh; mm in recipe','axes':root['axes']}
(OUT/'authored-parameters.json').write_text(json.dumps(params,indent=2))
# Technical topology gate before and after clean export.
def check(obj):
 mesh=obj.data;mesh.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(mesh)
 edges={};vol=bm.calc_volume(signed=True);bad=sum(not e.is_manifold for e in bm.edges);bm.free()
 assert all(math.isfinite(q) for v in mesh.vertices for q in v.co)
 assert all(math.isfinite(q) for v in mesh.vertices for q in v.normal)
 assert all(abs(v.normal.length-1)<.0002 for v in mesh.vertices)
 assert all(t.area>1e-16 for t in mesh.loop_triangles)
 assert not bad and vol>0,(bad,vol)
 # Connectivity over actual vertex edges.
 adj=[[] for _ in mesh.vertices]
 for e in mesh.edges:a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 seen=set();components=0
 for i in range(len(adj)):
  if i in seen:continue
  components+=1;stack=[i];seen.add(i)
  while stack:
   for k in adj[stack.pop()]:
    if k not in seen:seen.add(k);stack.append(k)
 assert components==1,components
 coords=[tuple(round(float(q),8) for q in v.co) for v in mesh.vertices]
 tris=sorted(tuple(sorted(coords[i] for i in t.vertices)) for t in mesh.loop_triangles)
 return {'vertices':len(mesh.vertices),'triangles':len(tris),'nonmanifold_edges':bad,'components':components,'volume_mm3':vol*1e9,'bounds_mm':[[min(p[k] for p in coords)*1000,max(p[k] for p in coords)*1000] for k in range(3)],'decoded_triangles_sha256':hashlib.sha256(repr(tris).encode()).hexdigest()}
before=check(ob)
# Master is editable, with hidden retained authoring inputs, semantic anchors and final exterior.
controls.hide_viewport=True;controls.hide_render=True
bpy.context.view_layer.objects.active=ob;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FDI36-authored-master.blend'))
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);root.select_set(True)
for name in anchors:scene.objects[name].select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FDI36-authored.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
# Clean reimport into a new scene, weld normal/material splits for topology checks only.
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;bpy.ops.import_scene.gltf(filepath=str(OUT/'FDI36-authored.glb'));ob=next(o for o in scene.objects if o.type=='MESH')
me=ob.data.copy();check_ob=bpy.data.objects.new('Disposable_topology_check',me);bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-9);bm.to_mesh(me);bm.free();me.update();after=check(check_ob);bpy.data.objects.remove(check_ob);bpy.data.meshes.remove(me)
assert before['triangles']==after['triangles']
assert before['decoded_triangles_sha256']==after['decoded_triangles_sha256'],(before,after)
# Reimported actual artifact, no authoring geometry or image-generation reference.
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.studiolight_rotate_z=.3;scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.curvature_ridge_factor=1.2;scene.display.shading.curvature_valley_factor=1.1;scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('World');scene.world.color=(.055,.065,.08)
scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cam=bpy.data.objects.new('EvidenceCamera',bpy.data.cameras.new('EvidenceCamera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.lens=50;cam.data.clip_start=.001;cam.data.clip_end=10
views={};
from bpy_extras.object_utils import world_to_camera_view
for name,direction,target,scale in [('occlusal',(0,0,1),(0,.3,3),15),('buccal',(0,-1,0),(0,0,-3),27),('lingual',(0,1,0),(0,0,-3),27),('mesial',(-1,0,0),(0,0,-3),27),('distal',(1,0,0),(0,0,-3),27),('three-quarter',(-.8,-1,.85),(0,0,-2.0),27),('occlusal-detail',(0,0,1),(0,.3,5),13)]:
 target=Vector(target)/1000;cam.location=target+Vector(direction).normalized()*.10;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale/1000;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 loc={}
 for n in anchors:
  q=world_to_camera_view(scene,cam,scene.objects[n].matrix_world.translation);loc[n]=[round(q.x*1000),round((1-q.y)*1100)]
 views[name]={'direction':direction,'target_m':list(target),'ortho_scale_mm':scale,'anchor_pixels':loc,'sha256':hashlib.sha256((OUT/(name+'.png')).read_bytes()).hexdigest()}
receipt={'scope':'Original educational exterior, not clinical or scanned.','before':before,'after_clean_reimport':after,'glb':{'bytes':(OUT/'FDI36-authored.glb').stat().st_size,'sha256':hashlib.sha256((OUT/'FDI36-authored.glb').read_bytes()).hexdigest()},'master_sha256':hashlib.sha256((OUT/'FDI36-authored-master.blend').read_bytes()).hexdigest(),'views':views,'duration_s':time.perf_counter()-START,'gates':{'technical':'passed-scoped','visual':'pending','anatomical_plausibility':'pending independent reference-screened review','clinical':'not validated','runtime':'not tested'}}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({'output':str(OUT),'triangles':before['triangles'],'bytes':receipt['glb']['bytes'],'seconds':receipt['duration_s']}))
