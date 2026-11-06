"""V6 bounded surface revision. Requires the exact baseline GLB and geometrically identical generated baseline master.
No whole-mesh remesh. Reprojects upper-crown z only; all lower vertices are unchanged.
"""
import bpy,bmesh,math,json,hashlib,sys,time
import numpy as np
from pathlib import Path
from mathutils import Vector
START=time.perf_counter();BASE=Path(__file__).parent
OUT=BASE/(sys.argv[sys.argv.index('--')+1])
if OUT.exists():raise RuntimeError('Preserve attempts: choose a new folder')
SOURCE=BASE/'baseline/FDI36-authored-master.blend'
SOURCE_GLB=BASE/'baseline/FDI36-authored.glb'
assert hashlib.sha256(SOURCE_GLB.read_bytes()).hexdigest()=='54b29904746bf0a53a96143326e09cef84995d2e40a29cd1da634b43908fe38c'
OUT.mkdir();bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
root=scene.objects['FDI36_Authored_Educational'];controls=bpy.data.collections['AUTHORING_INPUTS_hidden'];ob=scene.objects['FDI36_Exterior_AUTHORED']
EXPECTED_BASELINE = '54b29904746bf0a53a96143326e09cef84995d2e40a29cd1da634b43908fe38c'
def verify_source_scene(export_path):
 # Bind loaded scene transforms, materials, normals and semantic nodes as well as geometry.
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);root.select_set(True)
 for item in scene.objects:
  if item.type=='EMPTY' and item.parent==root:item.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(export_path),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
 actual=hashlib.sha256(Path(export_path).read_bytes()).hexdigest()
 assert actual==EXPECTED_BASELINE,('Loaded source scene differs from canonical baseline',actual)
 return actual
verify_source_scene(OUT/'verified-source.glb')
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
 values=[depth*math.exp(-(min(segdist(x,y,a,b) for a,b in zip(line,line[1:]))/w)**2) for line,w,depth in G]
 peak=max(values);tau=.018
 return max(0,peak+tau*math.log(sum(math.exp((v-peak)/tau) for v in values)/len(values)))
def v5_height(x,y):
 r=min(.999999,polar_radius(x,y))
 return EQ+math.sqrt(1-r*r)*(raw_height(x,y)-EQ)-groove(x,y)*max(0,1-r**8)

# V6 local feature regions. These are authored teaching-shape controls, not measurements.
RIDGES=[('MB_triangular_ridge',(-2.65,-2.30),(-.95,-.62),.30,.42),('DB_triangular_ridge',(.95,-2.38),(.32,-.62),.25,.40),('ML_triangular_ridge',(-2.55,2.48),(-.95,.62),.34,.43),('DL_triangular_ridge',(1.40,2.34),(.62,.55),.29,.41),('Mesial_marginal_ridge',(-4.02,-1.2),(-3.98,1.5),.22,.35),('Distal_marginal_ridge',(3.82,-.10),(3.57,1.36),.17,.33)]
FOSSAE=[]  # Existing TPS basins are bounded by added positive ridges; no second depression field.
def feature_height(x,y):
 z=0
 for name,a,b,amp,width in RIDGES:
  dx=b[0]-a[0];dy=b[1]-a[1];t=((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)
  if 0<t<1:
   d=abs((x-a[0])*dy-(y-a[1])*dx)/math.hypot(dx,dy)
   z+=amp*math.sin(math.pi*t)**2*math.exp(-(d/width)**2)
 for name,pts,depth in FOSSAE:
  (ax,ay),(bx,by),(cx,cy)=pts;den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
  a=((by-cy)*(x-cx)+(cx-bx)*(y-cy))/den;b=((cy-ay)*(x-cx)+(ax-cx)*(y-cy))/den;c=1-a-b
  if min(a,b,c)>0:z-=depth*(27*a*b*c)**2
 return z
def height(x,y):return v5_height(x,y)+feature_height(x,y)

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
source_check=check(ob)
assert source_check['decoded_triangles_sha256']=='7bb59a58776c4dcfc6e4d7de2792576c62a4322c5b9f7deef0dfda5abfb078e5'
# Keep root/lower-crown mesh, topology, XY, materials and frame unchanged.
original=[tuple(v.co) for v in ob.data.vertices]
changed=0;delta=[]
for v in ob.data.vertices:
 x,y,z=[q*1000 for q in v.co]
 if z<=3.5:continue
 w=smoothstep(min(1,(z-3.5)/1.0))
 target=height(x,y-.65)
 shift=(target-z)*w
 v.co.z+=shift/1000;delta.append(shift);changed+=1
ob.data.update()
assert all(tuple(v.co)==p for v,p in zip(ob.data.vertices,original) if p[2]<=.0035)
assert all(v.co.x==p[0] and v.co.y==p[1] for v,p in zip(ob.data.vertices,original))
# Preserve original source inputs in the master and add a distinct v6 crown control copy.
orig_input=next(o for o in controls.objects if o.name.startswith('Crown'))
cp=orig_input.copy();cp.data=orig_input.data.copy();cp.name='V6_Crown_Analytic_Control';controls.objects.link(cp);cp.hide_render=True;cp.hide_set(True)
for v in cp.data.vertices:
 x,y,z=[q*1000 for q in v.co]
 if z>EQ+1e-4:v.co.z=height(x,y-.65)/1000
cp.data.update()
anchors={}
for o in scene.objects:
 if o.type=='EMPTY' and o!=root:
  p=list(o.location)
  if o.name.startswith('Cusp_') or 'fossa' in o.name or 'ridge' in o.name:
   p[2]=height(p[0]*1000,p[1]*1000-.65)/1000;o.location=p
  anchors[o.name]=[q*1000 for q in o.location]
root['revision']='V6: analytic upper-crown reprojection after V5 union; local ridge and triangular fossa fields.'
params=json.loads((BASE/'baseline/authored-parameters.json').read_text())
params.update({'v6_ridge_controls_mm':RIDGES,'v6_triangular_fossae_mm':FOSSAE,'fossa_rule':'Existing TPS basins; no added negative fossa fields. Positive ridges define their surroundings.','groove_rule':'log-mean-exp smooth maximum, tau 0.018 mm, bounded at/below original maximum depth','source_master_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'projection_band_mm':[3.5,4.5],'projection_method':'Only z coordinate above 3.5 mm changes. Smoothstep blend reaches analytic surface above 4.5 mm.','changed_vertices':changed,'z_change_range_mm':[min(delta),max(delta)],'unchanged_lower_vertices':sum(p[2]<=.0035 for p in original),'all_xy_coordinates_unchanged':True})
(OUT/'authored-parameters.json').write_text(json.dumps(params,indent=2)+'\n')
# Technical topology gate before and after clean export.

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
