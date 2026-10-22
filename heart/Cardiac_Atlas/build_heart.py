import bpy, math, json, os, sys, random
from mathutils import Vector
ROOT=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,ROOT)
from heart_geometry import CHAMBERS,point,crescent_section,SEPTUM,inside
random.seed(14)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)
scene=bpy.context.scene
scene.name='CARDIAC ATLAS • Animated anatomy'
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=.025
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=32
scene.cycles.use_denoising=False
scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.fps=30
scene.frame_start=1;scene.frame_end=120
scene.world.color=(.035,.035,.035)
scene.view_settings.view_transform='AgX'
scene.render.film_transparent=False

COL={}
for n in ['00 CONTROLS','01 CHAMBER WALLS','02 ENDOCARDIUM','03 VALVES AND CHORDAE','04 GREAT VESSELS','05 CORONARY CIRCULATION','06 MEMBRANES AND FAT','07 SEPTA','08 BLOOD POOLS • export only','09 LABELS','10 STUDIO']:
 c=bpy.data.collections.new(n);scene.collection.children.link(c);COL[n[:2]]=c

def relocate(obj,col):
 for c in list(obj.users_collection):c.objects.unlink(obj)
 COL[col].objects.link(obj)

def driver(prop,idx=None,expr='v',control_prop='ventricular_systole'):
 fc=prop.driver_add('default_value') if idx is None else prop.driver_add('default_value',idx)
 dr=fc.driver;dr.type='SCRIPTED';dr.expression=expr
 v=dr.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+control_prop+'"]'
 return fc

ctrl=bpy.data.objects.new('HEART CONTROL • material + cutaway + pulse',None);COL['00'].objects.link(ctrl)
ctrl.empty_display_type='CIRCLE';ctrl.empty_display_size=2.6
for key,val,lo,hi,desc in [('material_set',0,0,2,'0 tissue / 1 clinical categories / 2 transparent'),('cutaway',0,0,1,'0 complete anatomy / 1 anterior teaching cutaway'),('ventricular_systole',0.,0.,1.,'Driven by illustrative 75 BPM timeline'),('atrial_systole',0.,0.,1.,'Precedes ventricular contraction'),('AV_open',1.,0.,1.,'Mitral and tricuspid opening'),('semilunar_open',0.,0.,1.,'Aortic and pulmonary opening'),('show_pericardium',0,0,1,'Pericardial envelope visibility')]:
 ctrl[key]=val;ctrl.id_properties_ui(key).update(min=lo,max=hi,description=desc)

# One 0.8-second cycle: atrial systole, isovolumetric contraction, ejection,
# isovolumetric relaxation, passive filling. Boundaries are illustrative.
tracks={
 'atrial_systole':[(1,0),(3,1),(5,0),(25,0)],
 'ventricular_systole':[(1,0),(4,0),(6,.25),(10,1),(12,1),(15,.12),(18,0),(25,0)],
 'AV_open':[(1,1),(4,1),(5,0),(13,0),(14,1),(25,1)],
 'semilunar_open':[(1,0),(5,0),(6,1),(11,1),(12,0),(25,0)]}
for key,keys in tracks.items():
 for fr,value in keys:ctrl[key]=float(value);ctrl.keyframe_insert(data_path='["'+key+'"]',frame=fr)
for fc in ctrl.animation_data.action.fcurves:
 fc.modifiers.new('CYCLES')
 for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type='AUTO_CLAMPED';kp.handle_right_type='AUTO_CLAMPED'
scene.frame_set(1)

MAT={}
def mat(name,clinical,tissue=None,rough=.34,transparent=True,subsurface=.055):
 m=bpy.data.materials.new(name);m.use_nodes=True
 m.diffuse_color=(*clinical,1)
 nodes=m.node_tree.nodes;nodes.clear();links=m.node_tree.links
 out=nodes.new('ShaderNodeOutputMaterial');out.location=(800,80)
 tissue=tissue or clinical
 t=nodes.new('ShaderNodeBsdfPrincipled');t.name='TISSUE • procedural microstructure';t.location=(80,300)
 t.inputs['Base Color'].default_value=(*tissue,1);t.inputs['Roughness'].default_value=rough
 t.inputs['Subsurface Weight'].default_value=subsurface
 t.inputs['Subsurface Radius'].default_value=(1.,.28,.14)
 t.inputs['Coat Weight'].default_value=.15;t.inputs['Coat Roughness'].default_value=.23
 tex=nodes.new('ShaderNodeTexNoise');tex.location=(-680,200);tex.inputs['Scale'].default_value=11.;tex.inputs['Detail'].default_value=4.1;tex.inputs['Roughness'].default_value=.75
 coord=nodes.new('ShaderNodeTexCoord');coord.location=(-900,100);links.new(coord.outputs['Generated'],tex.inputs['Vector'])
 ramp=nodes.new('ShaderNodeValToRGB');ramp.location=(-450,380)
 ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(*[v*.40 for v in tissue],1)
 ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(*[min(v*1.45+.025,1) for v in tissue],1)
 links.new(tex.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],t.inputs['Base Color'])
 bumptex=nodes.new('ShaderNodeTexNoise');bumptex.location=(-660,-80);bumptex.inputs['Scale'].default_value=150.;bumptex.inputs['Detail'].default_value=3
 links.new(coord.outputs['Generated'],bumptex.inputs['Vector'])
 bump=nodes.new('ShaderNodeBump');bump.location=(-170,80);bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.006
 links.new(bumptex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],t.inputs['Normal'])
 c=nodes.new('ShaderNodeBsdfPrincipled');c.name='CLINICAL • teaching color';c.location=(80,-30)
 c.inputs['Base Color'].default_value=(*clinical,1);c.inputs['Roughness'].default_value=.3;c.inputs['Coat Weight'].default_value=.18
 mix=nodes.new('ShaderNodeMixShader');mix.location=(420,240);driver(mix.inputs[0],expr='1 if v == 1 else 0',control_prop='material_set')
 links.new(t.outputs[0],mix.inputs[1]);links.new(c.outputs[0],mix.inputs[2])
 if transparent:
  g=nodes.new('ShaderNodeBsdfPrincipled');g.name='TRANSPARENT • X-ray teaching shell';g.location=(80,-330)
  g.inputs['Base Color'].default_value=(*[.45+.45*v for v in clinical],1);g.inputs['Transmission Weight'].default_value=0.;g.inputs['IOR'].default_value=1.10;g.inputs['Roughness'].default_value=.16;g.inputs['Alpha'].default_value=1.
  tr=nodes.new('ShaderNodeBsdfTransparent');tr.location=(100,-600)
  glassmix=nodes.new('ShaderNodeMixShader');glassmix.inputs[0].default_value=.88;glassmix.location=(420,-250);links.new(g.outputs[0],glassmix.inputs[1]);links.new(tr.outputs[0],glassmix.inputs[2])
  mix2=nodes.new('ShaderNodeMixShader');mix2.location=(610,100);driver(mix2.inputs[0],expr='1 if v == 2 else 0',control_prop='material_set')
  links.new(mix.outputs[0],mix2.inputs[1]);links.new(glassmix.outputs[0],mix2.inputs[2]);links.new(mix2.outputs[0],out.inputs[0])
 else:links.new(mix.outputs[0],out.inputs[0])
 MAT[name]=m;return m

for n,c in CHAMBERS.items():
 mat(n+' • epicardium',c['color'],(.31,.045,.035) if n in ('LV','LA') else (.29,.055,.045),.29)
 mat(n+' • myocardium',tuple(min(1,v*1.3+.03) for v in c['color']),(.39,.075,.065),.4)
 mat(n+' • endocardium',tuple(min(1,v*.5+.4) for v in c['color']),(.52,.25,.18),.30)
mat('Valve • fibrous ivory',(.93,.80,.47),(.72,.58,.40),.4,False,.025)
mat('Chordae • collagen',(.90,.88,.69),(.82,.72,.56),.33,False,.02)
mat('Septa • muscular amber',(.79,.37,.08),(.36,.06,.045),.38)
mat('Aorta • systemic arterial',(.78,.065,.07),(.48,.15,.13),.32)
mat('Pulmonary artery • low oxygen',(.10,.33,.77),(.44,.21,.20),.33)
mat('Vena cava • low oxygen',(.12,.40,.81),(.30,.19,.24),.35)
mat('Pulmonary veins • oxygenated',(.89,.18,.19),(.39,.18,.18),.34)
mat('Coronary arteries',(.93,.21,.075),(.55,.16,.09),.29,False)
mat('Coronary veins',(.08,.34,.66),(.22,.13,.22),.29,False)
mat('Epicardial fat',(.86,.71,.38),(.63,.47,.19),.46,False,.07)
mat('Pericardium • serous sac',(.35,.85,.82),(.57,.58,.49),.25)
mat('Bloodpool • export only',(.5,.02,.03),(.5,.02,.03),.3,False)
mat('Annular connective tissue',(.66,.76,.75),(.52,.43,.30),.45,False)

all_anatomy=[]; exports=[]
def mesh_obj(name,verts,faces,col,materials,indices=None,anat_id=None,label=None):
 me=bpy.data.meshes.new(name+' mesh');me.from_pydata(verts,[],faces);me.update()
 ob=bpy.data.objects.new(name,me);COL[col].objects.link(ob)
 for m in materials:me.materials.append(MAT[m])
 for p in me.polygons:p.use_smooth=True
 if indices:
  for p,i in zip(me.polygons,indices):p.material_index=i
 uv=me.uv_layers.new(name='Anatomical UV')
 for p in me.polygons:
  for li in p.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co
   uv.data[li].uv=((math.atan2(co.y,co.x)/(2*math.pi))%1,(co.z+2.5)/6.5)
 if anat_id:ob['anatomy_id']=anat_id
 if label is not None:ob['segmentation_label']=label
 ob['units']='1 Blender unit = 25 mm';all_anatomy.append(ob)
 return ob

def surf(params,N=96,M=60):
 verts=[point(params,0,0)]
 for j in range(1,M):
  t=(1-math.cos(math.pi*j/M))/2
  verts += [point(params,t,2*math.pi*i/N) for i in range(N)]
 top=len(verts);verts.append(point(params,1,0));faces=[]
 for i in range(N):faces.append((0,1+(i+1)%N,1+i))
 for j in range(M-2):
  a=1+j*N;b=a+N
  for i in range(N):faces.append((a+i,a+(i+1)%N,b+(i+1)%N,b+i))
 a=1+(M-2)*N
 for i in range(N):faces.append((a+i,a+(i+1)%N,top))
 return verts,faces

# Full shells are closed surfaces with oppositely-oriented inner surfaces. They are
# genuine wall volumes, not transparent solids pretending to have cavities.
full_walls={};pools={};cutwalls={};panels={}
for n,c in CHAMBERS.items():
 vo,fo=surf(c['outer']);vi,fi=surf(c['inner'])
 vv=vo+vi;ff=fo+[tuple(len(vo)+i for i in reversed(f)) for f in fi]
 wall=mesh_obj(n+' | complete wall',vv,ff,'01',[n+' • epicardium',n+' • endocardium'],[0]*len(fo)+[1]*len(fi),'wall_'+n,c['label_wall'])
 full_walls[n]=wall;exports.append(wall)
 pool=mesh_obj(n+' | closed blood pool',vi,fi,'08',['Bloodpool • export only'],anat_id='bloodpool_'+n,label=c['label_pool'])
 pool.hide_render=True;pool.hide_set(True);pools[n]=pool;exports.append(pool)
 # Split by a sagittally oblique anterior section: robust boolean creates genuine exposed wall thickness.
 cut=wall.copy();cut.data=wall.data.copy();COL['01'].objects.link(cut);cut.name=n+' | anterior section';all_anatomy.append(cut)
 cut.data.materials.append(MAT[n+' • myocardium'])
 # Keep posterior shell. Plane y=-0.15 for ventricles and y=.05 for atria.
 # Blender exact boolean with a generously sized cube removes foreground.
 plane_y=(.05 if n=='RV' else -.10) if n in ('LV','RV') else .12
 bpy.ops.mesh.primitive_cube_add(size=2,location=(0,plane_y-5,0));cutter=bpy.context.object;cutter.name='temporary section cutter';cutter.scale=(5,5,6)
 cutter.data.materials.append(MAT[n+' • myocardium'])
 bpy.context.view_layer.objects.active=cut
 mod=cut.modifiers.new('Closed teaching section','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.data.objects.remove(cutter,do_unlink=True)
 # Color cut faces by near constant Y normal; retain smooth original curved wall.
 for p in cut.data.polygons:
  if abs(p.normal.y)>.999:p.material_index=2;p.use_smooth=False
 cut['anatomy_id']='cutaway_'+n;cut['presentation_only']=True;cutwalls[n]=cut
 for ob,expr in [(wall,'v > 0.5'),(cut,'v < 0.5')]:
  for prop in ('hide_render','hide_viewport'):
   fc=ob.driver_add(prop);dr=fc.driver;dr.expression=expr;v=dr.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["cutaway"]'

# Carve intersecting blood pools from neighboring muscular volumes. Label priority
# in the analytic segmentation is identical: no myocardium may invade a pool.
for nn,other in [('LV','RV'),('RV','LV')]:
 for ob in (full_walls[nn],cutwalls[nn]):
  bpy.context.view_layer.objects.active=ob
  bo=ob.modifiers.new('Respect neighboring blood pool','BOOLEAN');bo.operation='DIFFERENCE';bo.object=pools[other];bo.solver='EXACT'
  bpy.ops.object.modifier_apply(modifier=bo.name)
  import bmesh
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=list(bm.faces))
  seen=set();discard=[]
  for face in bm.faces:
   if face in seen:continue
   stack=[face];seen.add(face);part=[]
   while stack:
    f=stack.pop();part.append(f)
    for e in f.edges:
     if len(e.link_faces)==2:
      for nf in e.link_faces:
       if nf not in seen:seen.add(nf);stack.append(nf)
   if len(part)<=2:discard.extend(part)
  if discard:bmesh.ops.delete(bm,geom=discard,context='FACES')
  bm.to_mesh(ob.data);bm.free();ob.data.update()

# Pulse as editable shape keys with regional contraction, longitudinal shortening,
# wall thickening visual effect and mild torsion (not a biomechanical simulation).
def pulse(ob,group='V',strength=1.):
 if ob.type!='MESH' or len(ob.data.vertices)==0:return
 ob.shape_key_add(name='Basis');key=ob.shape_key_add(name='Systole • regional shortening')
 for v,k in zip(ob.data.vertices,key.data):
  p=v.co.copy();z=p.z
  if group=='V':
   w=max(0,min(1,(1.25-z)/3.55));theta=.075*w*strength
   cx=.43;cy=.06
   x,y=p.x-cx,p.y-cy
   radial=1-.115*strength
   k.co.x=cx+radial*(x*math.cos(theta)-y*math.sin(theta));k.co.y=cy+radial*(x*math.sin(theta)+y*math.cos(theta));k.co.z=1.0+(z-1.0)*(1-.055*strength)
  elif group=='A':
   center=Vector((-.95,0,1.4)) if ob.get('anatomy_id','').endswith('RA') or ob.name.startswith('RA') else Vector((.5,.6,1.4))
   k.co=center+(p-center)*(1-.075*strength)
  else:k.co=p
 fc=key.driver_add('value');dr=fc.driver;dr.expression='v';v=dr.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+('atrial_systole' if group=='A' else 'ventricular_systole')+'"]'

for n in CHAMBERS:
 for ob in (full_walls[n],cutwalls[n],pools[n]):pulse(ob,'A' if n in ('LA','RA') else 'V')

# Tube mesh: hollow thick-walled open-ended vessels with closed wall annuli.
# Parallel-transport frames reduce artificial twisting along vessels.
def sample_path(points,steps=8):
 ps=[Vector(p[:3]) for p in points];rs=[p[3] for p in points];out=[]
 for i in range(len(ps)-1):
  p0=ps[max(0,i-1)];p1=ps[i];p2=ps[i+1];p3=ps[min(len(ps)-1,i+2)]
  for j in range(steps):
   t=j/steps;t2=t*t;t3=t2*t
   p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3)
   out.append((p,rs[i]*(1-t)+rs[i+1]*t))
 out.append((ps[-1],rs[-1]));return out

vessel_schema=[]
def tube(name,points,material,col='04',sides=32,steps=7,wall=.075,closed_solid=False,anat_id=None,label=None,animate=False):
 path=sample_path(points,steps);verts=[];frames=[]
 prev=Vector((1,0,0))
 for i,(p,r) in enumerate(path):
  tang=(path[min(i+1,len(path)-1)][0]-path[max(0,i-1)][0]).normalized()
  normal=(prev-tang*prev.dot(tang)).normalized()
  if normal.length<.1:normal=tang.cross(Vector((0,1,0))).normalized()
  bitang=tang.cross(normal).normalized();frames.append((normal,bitang));prev=normal
  for s in range(sides):
   a=2*math.pi*s/sides;verts.append(tuple(p+r*(normal*math.cos(a)+bitang*math.sin(a))))
 faces=[];indices=[];nr=len(path)
 for j in range(nr-1):
  for s in range(sides):faces.append((j*sides+s,j*sides+(s+1)%sides,(j+1)*sides+(s+1)%sides,(j+1)*sides+s));indices.append(0)
 if closed_solid:
  verts.append(tuple(path[0][0]));bot=len(verts)-1;verts.append(tuple(path[-1][0]));top=len(verts)-1
  for s in range(sides):faces.append((bot,(s+1)%sides,s));indices.append(0);faces.append((top,(nr-1)*sides+s,(nr-1)*sides+(s+1)%sides));indices.append(0)
 else:
  offset=len(verts)
  for (p,r),(normal,bitang) in zip(path,frames):
   ir=max(r-wall,r*.68)
   for s in range(sides):
    a=2*math.pi*s/sides;verts.append(tuple(p+ir*(normal*math.cos(a)+bitang*math.sin(a))))
  for j in range(nr-1):
   for s in range(sides):faces.append((offset+j*sides+s,offset+(j+1)*sides+s,offset+(j+1)*sides+(s+1)%sides,offset+j*sides+(s+1)%sides));indices.append(0)
  for j in (0,nr-1):
   for s in range(sides):
    q=(j*sides+s,j*sides+(s+1)%sides,offset+j*sides+(s+1)%sides,offset+j*sides+s)
    faces.append(tuple(reversed(q)) if j==nr-1 else q);indices.append(0)
 ob=mesh_obj(name,verts,faces,col,[material],anat_id=anat_id)
 if animate:pulse(ob,'V',.65)
 if label:
  # Closed lumen is an export-only mesh with the identical transported centerline.
  ip=[(float(p.x),float(p.y),float(p.z),float(max(r-wall,r*.68))) for p,r in path]
  vessel_schema.append({'anatomy_id':anat_id,'name':name,'label':label,'sampled_centerline_BU':ip})
 return ob

V=[
 ('Aorta | root, ascending, arch and descending',[(.34,.17,.64,.30),(.26,.20,1.35,.31),(.19,.31,2.19,.32),(.43,.44,2.86,.31),(.95,.67,3.02,.29),(1.34,.91,2.58,.27),(1.38,1.03,1.60,.25),(1.39,1.08,.30,.23)],'Aorta • systemic arterial','aorta',11),
 ('Brachiocephalic trunk',[ (.29,.33,2.63,.16),(.02,.38,3.08,.15),(-.20,.34,3.48,.135)],'Aorta • systemic arterial','brachiocephalic_trunk',11),
 ('Right common carotid',[(-.17,.34,3.41,.085),(-.16,.34,3.80,.075)],'Aorta • systemic arterial','right_common_carotid',11),
 ('Right subclavian',[(-.17,.34,3.41,.09),(-.65,.39,3.55,.07)],'Aorta • systemic arterial','right_subclavian',11),
 ('Left common carotid',[(.66,.55,2.99,.115),(.67,.57,3.40,.095),(.70,.58,3.78,.085)],'Aorta • systemic arterial','left_common_carotid',11),
 ('Left subclavian',[(1.02,.75,2.87,.125),(1.28,.84,3.27,.105),(1.65,.88,3.48,.085)],'Aorta • systemic arterial','left_subclavian',11),
 ('Pulmonary trunk',[(-.55,-.35,.52,.30),(-.40,-.44,1.14,.33),(-.18,-.37,1.78,.34),(.02,-.16,2.20,.32)],'Pulmonary artery • low oxygen','pulmonary_trunk',12),
 ('Left pulmonary artery',[(.02,-.16,2.20,.25),(.58,.01,2.24,.23),(1.05,.21,2.25,.21),(1.65,.35,2.20,.19)],'Pulmonary artery • low oxygen','left_pulmonary_artery',12),
 ('Right pulmonary artery',[(.02,.05,2.18,.25),(-.54,.54,2.17,.22),(-1.14,.65,2.13,.20),(-1.75,.63,2.13,.18)],'Pulmonary artery • low oxygen','right_pulmonary_artery',12),
 ('Superior vena cava',[(-1.02,.22,1.56,.26),(-1.13,.35,2.24,.27),(-1.12,.38,2.92,.25)],'Vena cava • low oxygen','superior_vena_cava',13),
 ('Inferior vena cava',[(-1.09,.32,1.00,.28),(-1.22,.49,.42,.27),(-1.23,.54,-.14,.24)],'Vena cava • low oxygen','inferior_vena_cava',13),
 ('Right superior pulmonary vein',[(.18,.98,1.68,.16),(-.45,1.10,1.80,.16),(-1.37,1.19,1.80,.15)],'Pulmonary veins • oxygenated','right_superior_pulmonary_vein',14),
 ('Right inferior pulmonary vein',[(.14,.94,1.16,.17),(-.48,1.10,1.13,.17),(-1.37,1.22,1.05,.15)],'Pulmonary veins • oxygenated','right_inferior_pulmonary_vein',14),
 ('Left superior pulmonary vein',[(.93,.93,1.72,.17),(1.42,1.06,1.80,.17),(1.91,1.10,1.86,.15)],'Pulmonary veins • oxygenated','left_superior_pulmonary_vein',14),
 ('Left inferior pulmonary vein',[(1.01,.94,1.15,.17),(1.48,1.07,1.13,.16),(1.95,1.13,1.10,.15)],'Pulmonary veins • oxygenated','left_inferior_pulmonary_vein',14),
]
for name,ps,ma,aid,label in V:tube(name,ps,ma,anat_id=aid,label=label)
with open(os.path.join(ROOT,'vessel_geometry.json'),'w') as f:json.dump(vessel_schema,f,indent=2)

# Ellipsoid helper produces actual transformed mesh vertices (simplifies exports and deformation).
def ellipsoid(name,center,scale,material,col='03',aid=None,segments=40,rings=24):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=center)
 ob=bpy.context.object;ob.name=name;ob.scale=scale
 bpy.ops.object.transform_apply(location=True,rotation=False,scale=True);relocate(ob,col)
 ob.data.materials.append(MAT[material]);all_anatomy.append(ob)
 for p in ob.data.polygons:p.use_smooth=True
 if aid:ob['anatomy_id']=aid
 return ob

# Interventricular septal muscle: narrow curved slab, covered by endocardium.
# The IV septum is an actual sector of LV muscular wall, never an object
# cutting through the LV blood pool. It follows the curved LV/RV interface.
def septum_mesh():
 N=48;M=44;verts=[];faces=[]
 for layer in ('outer','inner'):
  par=CHAMBERS['LV'][layer]
  for j in range(M+1):
   z=SEPTUM['z0']+(SEPTUM['z1']-SEPTUM['z0'])*j/M;t=(z-par[0])/(par[1]-par[0])
   for i in range(N+1):verts.append(point(par,t,SEPTUM['theta0']+(SEPTUM['theta1']-SEPTUM['theta0'])*i/N))
 offset=(M+1)*(N+1)
 for layer in (0,1):
  for j in range(M):
   for i in range(N):
    a=layer*offset+j*(N+1)+i;q=(a,a+1,a+N+2,a+N+1)
    faces.append(tuple(reversed(q)) if layer else q)
 for j in range(M):
  a=j*(N+1);b=(j+1)*(N+1);faces.append((a,b,b+offset,a+offset))
  a=j*(N+1)+N;b=(j+1)*(N+1)+N;faces.append((a,a+offset,b+offset,b))
 for i in range(N):
  a=i;b=i+1;faces.append((a,a+offset,b+offset,b))
  a=M*(N+1)+i;b=a+1;faces.append((a,b,b+offset,a+offset))
 return verts,faces
sv,sf=septum_mesh();sept=mesh_obj('Interventricular septum | curved muscular partition',sv,sf,'07',['Septa • muscular amber'],anat_id='interventricular_septum',label=9)
exports.append(sept);pulse(sept)
# Its complete geometry is retained for export; anterior section follows the LV cut.
sept.hide_render=True;sept.hide_set(True)
sc=sept.copy();sc.data=sept.data.copy();COL['07'].objects.link(sc);sc.name='Interventricular septum | teaching section';sc.hide_render=False;sc.hide_set(False);sc.shape_key_clear()
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,-5.10,0));cu=bpy.context.object;cu.scale=(5,5,6)
bpy.context.view_layer.objects.active=sc;bo=sc.modifiers.new('Anterior septal cut','BOOLEAN');bo.operation='DIFFERENCE';bo.object=cu;bo.solver='EXACT';bpy.ops.object.modifier_apply(modifier=bo.name);bpy.data.objects.remove(cu,do_unlink=True);pulse(sc)
for prop in ('hide_render','hide_viewport'):
 fc=sc.driver_add(prop);d=fc.driver;d.expression='True';v=d.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["cutaway"]'
septA=ellipsoid('Interatrial septum',(-.22,.40,1.35),(.10,.48,.57),'Septa • muscular amber','07','interatrial_septum');pulse(septA,'A');septA['segmentation_label']=10;exports.append(septA)
ellipsoid('Fossa ovalis | right atrial septal depression',(-.33,-.004,1.38),(.045,.017,.17),'Annular connective tissue','07','fossa_ovalis')

# Atrial appendages, lobulated but not exaggerated independent heart lobes.
for n,points in [('RA',[(-1.20,-.35,1.73,.26),(-.96,-.54,1.81,.23),(-.69,-.53,1.73,.14),(-.48,-.47,1.61,.035)]),('LA',[(.91,.14,1.64,.20),(1.22,-.10,1.57,.19),(1.23,-.29,1.35,.14),(1.07,-.37,1.20,.035)])]:
 ob=tube(n+' auricular appendage',points,n+' • epicardium','01',wall=.05,closed_solid=True,anat_id=n+'_appendage');pulse(ob,'A')

# Valve annuli and leaflets. AV leaflets sweep inferiorly when open, meet centrally
# when closed; semilunar cusps have pocket-like geometry and no chordae.
valves={}
def ring(name,center,rx,ry,material,axis=(0,0,1),thick=.035):
 # default ring lies transverse with a gentle anatomical tilt added to Z.
 pts=[]
 for i in range(65):
  a=2*math.pi*i/64;pts.append((center[0]+rx*math.cos(a),center[1]+ry*math.sin(a),center[2]+.08*math.cos(a),thick))
 return tube(name,pts,material,'03',sides=12,steps=1,closed_solid=True,anat_id=name.lower().replace(' ','_'))

def leaflet_valve(name,center,rx,ry,count,semilunar=False):
 ring(name+' | annulus',center,rx,ry,'Annular connective tissue',thick=.043 if not semilunar else .035)
 oblist=[];free_edges=[]
 for l in range(count):
  nseg=24;nv=8;verts=[];opened=[]
  # leaflet sectors overlap minutely at commissures to show coaptation.
  start=2*math.pi*l/count;end=2*math.pi*(l+1)/count
  for j in range(nv+1):
   u=j/nv
   for i in range(nseg+1):
    a=start+(end-start)*i/nseg
    # At closed position leaflet spans from annulus to a small central coaptation.
    radial=1-u*.96
    z=center[2]-.10*u+.06*math.sin(math.pi*u)*math.sin(math.pi*i/nseg)
    if semilunar:z=center[2]-.16*math.sin(math.pi*u)+.045*u
    verts.append((center[0]+rx*radial*math.cos(a),center[1]+ry*radial*math.sin(a),z+.08*math.cos(a)*(1-u)))
    arc=max(0,math.sin(math.pi*i/nseg))
    ro=(1-.13*u*arc) if semilunar else (1-u*(.20+.20*arc))
    zo=center[2]-(.20 if semilunar else .43)*u*(arc**.6)-.035*math.sin(math.pi*u)
    opened.append((center[0]+rx*ro*math.cos(a),center[1]+ry*ro*math.sin(a),zo+.08*math.cos(a)))
  faces=[]
  for j in range(nv):
   for i in range(nseg):
    a=j*(nseg+1)+i;faces.append((a,a+1,a+nseg+2,a+nseg+1))
  ob=mesh_obj(name+' | leaflet '+str(l+1),verts,faces,'03',['Valve • fibrous ivory'],anat_id=name.lower().replace(' ','_')+'_leaflet_'+str(l+1))
  ob.shape_key_add(name='Basis • closed');key=ob.shape_key_add(name='Opening')
  for v,p in zip(key.data,opened):v.co=p
  fc=key.driver_add('value');d=fc.driver;d.expression='v';v=d.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+('semilunar_open' if semilunar else 'AV_open')+'"]'
  sol=ob.modifiers.new('Fibrous leaflet thickness','SOLIDIFY');sol.thickness=.012
  sub=ob.modifiers.new('Smooth leaflet curvature','SUBSURF');sub.levels=1;sub.render_levels=1
  oblist.append(ob)
  free_edges.append([opened[nv*(nseg+1)+i] for i in [3,7,12,17,21]])
 valves[name]=oblist
 return free_edges

mitral_center=(.55,.13,.67);tri_center=(-.65,.05,.79)
mit_edges=leaflet_valve('Mitral valve',mitral_center,.48,.38,2)
tri_edges=leaflet_valve('Tricuspid valve',tri_center,.47,.40,3)
leaflet_valve('Aortic valve',(.32,.17,1.02),.245,.245,3,True)
leaflet_valve('Pulmonary valve',(-.37,-.43,1.17),.268,.268,3,True)

# AV support apparatus: two conventional LV papillary groups; three RV groups.
for n,centers,edges in [('LV',[(.30,-.03,-1.02),(.91,.22,-.89)],mit_edges),('RV',[(-.65,.12,-.65),(-.30,.18,-1.10),(-.80,.20,-.15)],tri_edges)]:
 for k,p in enumerate(centers):
  head=(p[0],p[1],p[2]+.28)
  ob=ellipsoid(n+' papillary muscle '+str(k+1),p,(.115,.095,.36),n+' • endocardium',aid=n+'_papillary_'+str(k+1));pulse(ob)
  for l,edge in enumerate(edges):
   for j,e in enumerate(edge):
    # Each group supports adjacent leaflet edges: small branching collagen cords.
    if n=='RV' and l not in (k,(k+1)%3):continue
    bend=((head[0]+e[0])*.5,(head[1]+e[1])*.5+.015, (head[2]+e[2])*.5)
    ob=tube(n+' chordae | papillary '+str(k+1)+' leaflet '+str(l+1)+' cord '+str(j+1),[(*head,.009),(*bend,.007),(*e,.0045)],'Chordae • collagen','03',sides=6,steps=3,closed_solid=True,anat_id=n+'_chord_'+str(k)+'_'+str(l)+'_'+str(j))
    # Chordae endpoints follow the valve opening through an explicit shape key.
    ob.shape_key_add(name='Basis • AV open');key=ob.shape_key_add(name='AV closure tracking')
    for v,kv in zip(ob.data.vertices,key.data):
     w=max(0,min(1,(v.co.z-head[2])/(e[2]-head[2]+1e-5)))
     cc=mitral_center if n=='LV' else tri_center
     kv.co.x=v.co.x+(cc[0]-e[0])*.95*w;kv.co.y=v.co.y+(cc[1]-e[1])*.95*w;kv.co.z=v.co.z+.33*w
    fc=key.driver_add('value');d=fc.driver;d.expression='1-v';v=d.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["AV_open"]'

# Fine trabeculae carneae on the visible posterior endocardial surface.
for n in ('LV','RV'):
 params=CHAMBERS[n]['inner']
 for i in range(14):
  theta=(2.18+.90*(i+.3)/14) if n=='RV' else (.10+math.pi*(i+.3)/14)
  t0=.12+.27*random.random();t1=min(.76,t0+.23+.17*random.random());pts=[]
  for j in range(9):
   t=t0+(t1-t0)*j/8;ang=theta+.08*math.sin(j*.9+i)
   p=Vector(point(params,t,ang));cx,cy=(crescent_section(params,t)[:2] if isinstance(params,dict) else (params[2]+(params[3]-params[2])*t,params[4]+(params[5]-params[4])*t))
   p.x=cx+(p.x-cx)*.996;p.y=cy+(p.y-cy)*.996
   pts.append((*p,.023+.012*math.sin(math.pi*j/8)))
  ob=tube(n+' trabecula '+str(i+1),pts,n+' • myocardium','02',sides=7,steps=2,closed_solid=True,anat_id=n+'_trabecula_'+str(i+1));pulse(ob)
 # Cross-link ridges in irregular orientation rather than striped cylinders.
 for i in range(6):
  t=.24+i*.065;pts=[];aa=.3+random.random()*1.1
  for j in range(7):
   a=(2.35+.50*j/6) if n=='RV' else (aa+.9*j/6);p=Vector(point(params,t+.035*math.sin(j+i),a));p.y-=.002
   pts.append((*p,.021))
  ob=tube(n+' transverse trabecula '+str(i+1),pts,n+' • myocardium','02',sides=6,steps=2,closed_solid=True);pulse(ob)
# Right ventricular moderator band, a representative normal variant.
ob=tube('RV moderator band',[(-.13,.10,-.63,.035),(-.39,.12,-.78,.043),(-.65,.12,-.67,.035)],'RV • endocardium','02',sides=12,steps=7,closed_solid=True,anat_id='moderator_band');pulse(ob)
# Pectinate ridges in the right atrium (posterior-right wall represented).
for i in range(12):
 pts=[]
 for j in range(8):
  t=.25+.5*j/7;p=point(CHAMBERS['RA']['inner'],t,.15+math.pi*i/13);pts.append((p[0],p[1]-.012,p[2],.013))
 ob=tube('RA pectinate ridge '+str(i+1),pts,'RA • endocardium','02',sides=6,steps=2,closed_solid=True);pulse(ob,'A')

# Keep coronary vessels and fat attached to the actual outer myocardial surface.
from mathutils.kdtree import KDTree
surf_positions=[]
for nn in ('LV','RV'):
 vv,ff=surf(CHAMBERS[nn]['outer'],N=160,M=100)
 surf_positions.extend(Vector(v) for v in vv)
kdt=KDTree(len(surf_positions))
for i,p in enumerate(surf_positions):kdt.insert(p,i)
kdt.balance()
def epicardial_project(points):
 import numpy as np
 out=[]
 for x,y,z,r in points:
  t=max(0,min(1,(z+2.30)/3.38));cx=.86-.43*t;cy=-.18+.38*t
  direction=Vector((x-cx,y-cy,0));direction.normalize()
  radii=np.linspace(0,3.5,500);xx=cx+radii*direction.x;yy=cy+radii*direction.y
  mask=inside(xx,yy,z,CHAMBERS['LV']['outer'])|inside(xx,yy,z,CHAMBERS['RV']['outer'])
  if mask.any():
   rr=float(radii[np.where(mask)[0][-1]])+r*.7;p=Vector((cx+direction.x*rr,cy+direction.y*rr,z))
  else:p=Vector((x,y,z))
  out.append((*p,r))
 return out

# Coronary arteries and veins, representative right-dominant pattern.
C=[
 ('Left main coronary',[(.30,-.04,1.13,.065),(.18,-.24,.95,.060),(.06,-.48,.76,.054)],'Coronary arteries'),
 ('LAD | anterior interventricular artery',[(.06,-.48,.76,.052),(.02,-.66,.21,.046),(.22,-.72,-.39,.038),(.50,-.71,-1.01,.028),(.73,-.53,-1.70,.016),(.85,-.25,-2.17,.008)],'Coronary arteries'),
 ('Circumflex coronary',[(.06,-.48,.76,.047),(.60,-.52,.79,.045),(1.13,-.28,.73,.038),(1.35,.24,.72,.032),(1.13,.79,.70,.021)],'Coronary arteries'),
 ('Right coronary artery',[(.13,-.03,1.14,.058),(-.29,-.45,.85,.052),(-.97,-.71,.73,.047),(-1.55,-.34,.56,.038),(-1.52,.25,.35,.031),(-.91,.69,.17,.025)],'Coronary arteries'),
 ('Right marginal artery',[(-1.44,-.43,.56,.031),(-1.26,-.66,.02,.027),(-.84,-.70,-.57,.021),(-.33,-.57,-1.17,.011)],'Coronary arteries'),
 ('Posterior descending artery',[(-.91,.69,.17,.029),(-.24,.71,-.28,.025),(.18,.62,-.94,.017),(.63,.34,-1.71,.009)],'Coronary arteries'),
 ('Great cardiac vein',[(.91,-.30,-2.01,.014),(.66,-.58,-1.49,.023),(.43,-.76,-.75,.033),(.15,-.76,.03,.043),(.18,-.59,.69,.049),(.80,-.46,.78,.052),(1.33,.19,.71,.058),(1.03,.87,.65,.062)],'Coronary veins'),
 ('Coronary sinus',[(1.04,.87,.65,.10),(.43,1.02,.62,.105),(-.25,.98,.66,.10),(-.89,.57,.80,.085)],'Coronary veins'),
 ('Middle cardiac vein',[(.67,.43,-1.72,.018),(.20,.71,-.93,.025),(-.13,.80,-.30,.032),(-.34,.95,.60,.046)],'Coronary veins'),
 ('Small cardiac vein',[(-.59,-.59,-.84,.015),(-1.12,-.64,-.14,.025),(-1.54,-.25,.53,.033),(-1.48,.34,.61,.038),(-.88,.64,.71,.042)],'Coronary veins'),
]
groove=[]
for ii in range(10):
 z=.74-2.90*ii/9;tt=max(.001,min(.999,(z+1.96)/3.15));cx,cy,_,mid,width,span=crescent_section(CHAMBERS['RV']['outer'],tt)
 angle=math.radians(225)+span
 if z<-1.85:angle=math.radians(300)
 groove.append((cx+math.cos(angle),cy+.88*math.sin(angle),z,.052*(1-ii/11)))
for ii,(name,ps,ma) in enumerate(C):
 if name.startswith('LAD |'):C[ii]=(name,groove,ma)
 if name=='Left main coronary':C[ii]=(name,[(.30,-.04,1.13,.065),(.68,-.22,.95,.060),(*groove[0][:3],.054)],ma)
 if name=='Circumflex coronary':C[ii]=(name,[(*groove[0][:3],.047),(1.13,-.28,.73,.038),(1.35,.24,.72,.032),(1.13,.79,.70,.021)],ma)
 if name=='Great cardiac vein':C[ii]=(name,[(x+.055,y-.045,z,r*.85) for x,y,z,r in groove[::-1]]+[(1.3,.2,.72,.055),(1.03,.87,.65,.062)],ma)
for name,ps,ma in C:tube(name,ps if name in ('Left main coronary','Coronary sinus') else epicardial_project(ps),ma,'05',sides=12,steps=8,closed_solid=True,anat_id=name.split(' |')[0].lower().replace(' ','_'),animate=True)
# Diagonal and marginal branches hugging the ventricular surface.
for i in range(5):
 x,y,z,rr=groove[i+1]
 t=max(0,min(1,(z+2.30)/3.38));cx=.86-.43*t;cy=-.18+.38*t
 angle=math.atan2((y-cy)/.88,x-cx)
 pts=[(x,y,z,.025-i*.002),(cx+math.cos(angle+.28),cy+.88*math.sin(angle+.28),z-.13,.016-i*.0015),(cx+math.cos(angle+.57),cy+.88*math.sin(angle+.57),z-.30,.006)]
 tube('LAD diagonal branch '+str(i+1),epicardial_project(pts),'Coronary arteries','05',sides=9,steps=6,closed_solid=True,animate=True)
for i in range(4):
 pts=[(-.28-i*.29,-.67,.73-i*.035,.020),(-.48-i*.28,-.73,.35-i*.06,.013),(-.58-i*.24,-.63,-.05-i*.08,.006)]
 tube('RCA ventricular branch '+str(i+1),epicardial_project(pts),'Coronary arteries','05',sides=8,steps=6,closed_solid=True,animate=True)
# Cream epicardial fat concentrated in AV and interventricular grooves, not uniform coat.
for i in range(60):
 a=2*math.pi*i/60;x=-.05+1.27*math.cos(a);y=.10+.65*math.sin(a);z=.72+.08*math.cos(a)
 # Skip crowded valve outflow region in the anterior center.
 if -.45<x<.5 and y<0:continue
 ob=ellipsoid('Epicardial fat | AV groove '+str(i),(x,y,z),(random.uniform(.045,.09),random.uniform(.035,.075),random.uniform(.025,.055)),'Epicardial fat','06',segments=12,rings=8);pulse(ob,'V',.5)
for i in range(32):
 t=i/31;x=.08+.77*t;y=-.68+.40*t*t;z=.62-2.65*t
 ob=ellipsoid('Epicardial fat | LAD groove '+str(i),(x+.075,y+.015,z),(.03+.02*random.random(),.025,.045),'Epicardial fat','06',segments=10,rings=6);pulse(ob)

# Separate parietal pericardium sac, thin serous envelope with a display switch.
ps=(-2.50,2.40,.64,-.05,-.10,.25,1.80,1.18,.53,1.)
pv,pf=surf(ps,N=96,M=60)
peri=mesh_obj('Parietal pericardium | removable envelope',pv,pf,'06',['Pericardium • serous sac'],anat_id='parietal_pericardium')
sol=peri.modifiers.new('Thin parietal serous membrane','SOLIDIFY');sol.thickness=.018
for prop in ('hide_render','hide_viewport'):
 fc=peri.driver_add(prop);d=fc.driver;d.expression='v < .5';v=d.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["show_pericardium"]'
peri['note']='Simplified parietal envelope; epicardial chamber outer surfaces represent visceral serous pericardium. Pericardial recesses and detailed reflections omitted.'

for colkey in ('02','03'):
 for ob in COL[colkey].objects:
  for prop in ('hide_render','hide_viewport'):
   fc=ob.driver_add(prop);d=fc.driver;d.expression='cut < .5 and mode < 1.5'
   for varname,propname in [('cut','cutaway'),('mode','material_set')]:
    v=d.variables.new();v.name=varname;v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+propname+'"]'

for ob in bpy.data.objects:
 if 'auricular appendage' in ob.name:
  for prop in ('hide_render','hide_viewport'):
   fc=ob.driver_add(prop);d=fc.driver;d.expression='v > .5';v=d.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["cutaway"]'

# Presentation stage.
def plainmat(name,color,metal=0,rough=.4):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
stage=plainmat('Studio charcoal',(.016,.024,.034),0,.6)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-2.65));floor=bpy.context.object;floor.name='Studio floor';floor.data.materials.append(stage);relocate(floor,'10')

def camera(name,pos,target,lens=58,ortho=None):
 data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);COL['10'].objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.lens=lens
 if ortho:data.type='ORTHO';data.ortho_scale=ortho
 return ob
cameras={
 'hero':camera('CAM 01 • anterior hero',(6.7,-13.3,5.0),(0,0,.62),60,7.8),
 'cutaway':camera('CAM 02 • anterior teaching section',(1.0,-14.5,3.4),(.0,.05,.56),60,7.4),
 'posterior':camera('CAM 03 • posterior vessels',(-5.4,12.0,4.3),(.05,.25,.65),60,7.6),
 'valves':camera('CAM 04 • valve apparatus',(2.4,-8.0,3.2),(-.10,.0,.35),65,4.6),
}
scene.camera=cameras['hero']

def area(name,pos,energy,color,size,target=(0,0,.4)):
 da=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,da);COL['10'].objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();da.energy=energy;da.color=color;da.shape='DISK';da.size=size
area('Key • warm softbox',(-4,-6,7),700,(1,.85,.73),5)
area('Fill • cool softbox',(5,-3,3),500,(.66,.81,1),4)
area('Rim • upper rear',(1,4,6),900,(.72,.91,1),3)
area('Low fill',(-3,-2,-.4),220,(.76,.85,1),3)
world=bpy.data.worlds.new('Deep blue studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.075,.105,1);world.node_tree.nodes['Background'].inputs[1].default_value=.38;scene.world=world

# Render presets, anatomical structure manifest, and closed reference meshes.
scene['README']='See embedded README and exported docs. 0/1/2 material_set changes tissue/clinical/transparent. cutaway toggles full/sectioned walls. Spacebar plays 75 BPM illustrative cycle. All structures named, editable; no external assets.'
scene['coordinates']='BU: X patient-left, Y posterior, Z superior. RAS millimeters=(-25X,-25Y,+25Z).'
scene['clinical_status']='Procedural educational model, not patient-derived or clinically validated.'
scene['reference_phase']='Frame 1 end-diastole, beginning of atrial systole. 30fps,24 frames/cycle,75bpm.'
text=bpy.data.texts.new('README • START HERE')
text.write('''CARDIAC ATLAS / EDUCATIONAL PROCEDURAL HEART\n\nSelect HEART CONTROL in 00 CONTROLS. Custom properties:\nmaterial_set: 0 procedural tissue, 1 teaching color-coded, 2 transparent.\ncutaway: 0 full exterior, 1 anterior teaching section.\nshow_pericardium: 0 hide, 1 show simplified parietal sac.\n\nSpacebar plays 75 BPM illustrative heartbeat. Regional shape-key contraction and timed valve opening are editable. There is no armature because tissue deformation is represented by shape keys, which are more suitable for this procedural presentation. Ventricular shortening and subtle torsion are schematic, not physical simulation.\n\nCoordinate convention: Blender X patient left, Y posterior, Z superior. 1 BU = 25 mm; scale_length=0.025. RAS mm = (-25X,-25Y,+25Z). Frame 1 is reference end-diastole / atrial systole begins.\n\nThree presentation materials are procedural, self-contained node networks. The tissue look is illustrative wet tissue, NOT a photogrammetric or photographic texture. Clinical red/blue indicate circulation categories; actual venous blood is not blue. Transparent mode is an educational shell view.\n\n4 chambers; 4 valves (2/3/3/3 leaflets); papillary muscles, chordae, trabeculae; interatrial/interventricular septa; endocardium/myocardium/epicardium; simplified parietal pericardium; systemic/pulmonary vessels; representative right-dominant coronaries. Anatomical variability, microstructure, conduction system, pericardial reflections, physiology, and exact lumen continuity are simplified.\n\nSee docs for complete limitations, sources and imaging coordinate manifest.\n''')
# Save source script inside the blend for reproducibility.
for fn in ('build_heart.py','heart_geometry.py'):
 tx=bpy.data.texts.new(fn);tx.write(open(os.path.join(ROOT,fn)).read())

scene.frame_set(1);ctrl['material_set']=0;ctrl['cutaway']=0
# Store object census without export-only pools in render count.
manifest=[]
for ob in all_anatomy:
 if ob.type=='MESH':manifest.append({'object':ob.name,'anatomy_id':ob.get('anatomy_id',''),'vertices':len(ob.data.vertices),'faces':len(ob.data.polygons),'shape_keys':[k.name for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [],'segmentation_label':ob.get('segmentation_label',None)})
with open(os.path.join(ROOT,'anatomy_manifest.json'),'w') as f:json.dump(manifest,f,indent=2)
# Mesh export excludes modifiers/shape deformation and records exact end-diastole basis.
meshdata=[]
for ob in exports:
 mesh=ob.data;mesh.calc_loop_triangles()
 meshdata.append({'object':ob.name,'anatomy_id':ob.get('anatomy_id',''),'label':ob.get('segmentation_label'),'vertices_BU':[list(v.co) for v in mesh.vertices],'triangles':[list(t.vertices) for t in mesh.loop_triangles]})
with open(os.path.join(ROOT,'exports','anatomy_meshes.json'),'w') as f:json.dump({'coordinate_spec':'../geometry_spec.json','phase':1,'meshes':meshdata},f,separators=(',',':'))
# Convenient viewport defaults.
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':
   a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT');ctrl.select_set(True);bpy.context.view_layer.objects.active=ctrl
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Cardiac_Atlas.blend'))
print('BUILD COMPLETE',len(all_anatomy),'anatomy objects')
# Initial diagnostic hero and section render at restrained preview resolution.
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.cycles.samples=24
scene.render.filepath=os.path.join(ROOT,'renders','01_tissue_hero.png');bpy.ops.render.render(write_still=True)
ctrl['material_set']=1;ctrl['cutaway']=1;scene.camera=cameras['cutaway'];scene.frame_set(1)
scene.render.filepath=os.path.join(ROOT,'renders','02_clinical_cutaway.png');bpy.ops.render.render(write_still=True)
