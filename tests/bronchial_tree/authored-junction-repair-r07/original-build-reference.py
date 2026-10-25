import bpy,bmesh,math,json,os,sys,random
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;D=R.parent/'body-3d-delivery';SRC=R.parent/'body-3d-source/tb3/presentation/task-explorer/anatomy'
random.seed(219)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for ma in list(bpy.data.materials):bpy.data.materials.remove(ma)
s=bpy.context.scene;s.name='ANATOMY WORKSHOP · reusable teaching assets';s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.resolution_x=1600;s.render.resolution_y=1600;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=30;s.view_settings.view_transform='AgX';s.world.color=(.035,.035,.035)
ctrl=bpy.data.objects.new('WORKSHOP CONTROL · material and cutaway',None);s.collection.objects.link(ctrl);ctrl['material_mode']=0;ctrl['cutaway']=0
ctrl.id_properties_ui('material_mode').update(min=0,max=2,description='0 tissue-style; 1 categorical teaching colors; 2 transparent shells')
ctrl.id_properties_ui('cutaway').update(min=0,max=1,description='Show supported schematic internal teaching sections')
collections={};objects={};stats=[]
manifest=json.load(open(D/'manifest.json'));specs={a['id']:a for a in manifest['assets']}
colors={'liver':(.31,.072,.045),'kidney_left':(.40,.105,.065),'kidney_right':(.40,.105,.065),'spleen':(.24,.065,.10),'pancreas':(.65,.40,.22),'stomach':(.58,.27,.21),'gallbladder':(.28,.32,.10),'heart':(.39,.095,.085),'lung_left':(.58,.29,.32),'lung_right':(.58,.29,.32),'aorta':(.62,.26,.22),'trachea':(.62,.55,.40),'pulmonary_vein':(.32,.14,.23),'vertebrae_L3':(.76,.68,.46),'bronchial_tree':(.70,.56,.33),'bladder':(.64,.36,.26),'brain':(.62,.43,.34),'heart_detailed':(.38,.10,.07)}
clinical={'liver':(.66,.29,.09),'kidney_left':(.75,.19,.25),'kidney_right':(.80,.30,.25),'spleen':(.40,.22,.64),'pancreas':(.92,.66,.16),'stomach':(.86,.44,.33),'gallbladder':(.37,.68,.17),'heart':(.76,.12,.17),'lung_left':(.35,.64,.82),'lung_right':(.38,.72,.77),'aorta':(.87,.08,.09),'trachea':(.75,.80,.62),'pulmonary_vein':(.77,.18,.25),'vertebrae_L3':(.85,.82,.67),'bronchial_tree':(.93,.73,.28),'bladder':(.94,.68,.24),'brain':(.72,.48,.69),'heart_detailed':(.76,.12,.17)}
def coll(id):
 if id not in collections:
  co=bpy.data.collections.new(id+' · '+specs[id]['name']['en']);s.collection.children.link(co);collections[id]=co;objects[id]=[]
 return collections[id]
def driver(socket,expr):
 d=socket.driver_add('default_value').driver;d.expression=expr;v=d.variables.new();v.name='m';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["material_mode"]'
def material(name,color,cat,rough=.38,detail=False,texture=True):
 ma=bpy.data.materials.new(name);ma.diffuse_color=(*color,1);ma.use_nodes=True;n=ma.node_tree.nodes;n.clear();l=ma.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');out.location=(700,100)
 p=n.new('ShaderNodeBsdfPrincipled');p.name='TISSUE';p.location=(100,260);p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Coat Weight'].default_value=.22;p.inputs['Subsurface Weight'].default_value=.06
 if texture:
  tx=n.new('ShaderNodeTexNoise');tx.inputs['Scale'].default_value=8;tx.inputs['Detail'].default_value=4;tx.location=(-700,400)
  ramp=n.new('ShaderNodeValToRGB');ramp.location=(-450,450);ramp.color_ramp.elements[0].position=.17;ramp.color_ramp.elements[0].color=(*(c*.67 for c in color),1);ramp.color_ramp.elements[1].position=.83;ramp.color_ramp.elements[1].color=(*(min(1,c*1.25+.025) for c in color),1);l.new(tx.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
  micro=n.new('ShaderNodeTexNoise');micro.location=(-700,100);micro.inputs['Scale'].default_value=120 if 'lung' in name else 70;micro.inputs['Detail'].default_value=3
  bump=n.new('ShaderNodeBump');bump.location=(-130,100);bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.0003 if 'lung' in name else .00018;l.new(micro.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 c=n.new('ShaderNodeBsdfPrincipled');c.name='CLINICAL';c.location=(100,-20);c.inputs['Base Color'].default_value=(*cat,1);c.inputs['Roughness'].default_value=.43
 tr=n.new('ShaderNodeBsdfTransparent');tr.location=(100,-280);tr.inputs[0].default_value=(.9,.96,1,1)
 trans=n.new('ShaderNodeMixShader');trans.location=(330,-120);trans.inputs[0].default_value=.80 if not detail else .05;l.new(c.outputs[0],trans.inputs[1]);l.new(tr.outputs[0],trans.inputs[2])
 mix=n.new('ShaderNodeMixShader');mix.location=(350,200);driver(mix.inputs[0],'1 if m>0.5 else 0');l.new(p.outputs[0],mix.inputs[1]);l.new(c.outputs[0],mix.inputs[2])
 end=n.new('ShaderNodeMixShader');end.location=(550,100);driver(end.inputs[0],'1 if m>1.5 else 0');l.new(mix.outputs[0],end.inputs[1]);l.new(trans.outputs[0],end.inputs[2]);l.new(end.outputs[0],out.inputs[0]);ma['clinical_color']=list(cat);return ma
mats={id:material(id+' tissue / clinical / transparent',colors[id],clinical[id]) for id in colors}
medulla=material('Renal medullary pyramids',(.49,.18,.15),(.88,.42,.27),detail=True)
cortex=material('Renal cortex',(.54,.23,.16),(.85,.28,.28),detail=True)
collecting=material('Renal collecting system',(.79,.62,.40),(.99,.84,.32),detail=True)
fibrous=material('Pale fibrous tissue',(.72,.59,.43),(.93,.89,.68),detail=True)
rugae_mat=material('Gastric mucosa and rugae',(.61,.27,.24),(.91,.53,.39),detail=True)
white=material('White matter section',(.78,.70,.51),(.95,.88,.61),detail=True)
vent=material('Ventricular teaching cavity',(.14,.27,.40),(.19,.57,.79),detail=True)
def register(ob,id,aid,role='surface',deriv=None,ma=None):
 for co in list(ob.users_collection):co.objects.unlink(ob)
 coll(id).objects.link(ob);objects[id].append(ob);ob['organ_id']=id;ob['anatomy_id']=aid;ob['view_role']=role;ob['derivation']=deriv or ('source-derived' if specs[id]['sourceKind']=='segmented' else 'schematic');ob['clinical_color']=list(clinical[id]);ob['educational_only']=True
 if ma:ob.data.materials.clear();ob.data.materials.append(ma)
 if ob.type=='MESH':
  for p in ob.data.polygons:p.use_smooth=True
 if (role=='surface' and specs[id]['cutawaySupport']) or role in ['cutaway','detail']:
  for prop in ['hide_render','hide_viewport']:
   d=ob.driver_add(prop).driver;d.expression='c > .5' if role=='surface' else 'c < .5';v=d.variables.new();v.name='c';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["cutaway"]'
 return ob
def mesh(name,vs,fs,id,aid,role='surface',deriv=None,ma=None):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);s.collection.objects.link(ob);return register(ob,id,aid,role,deriv,ma)
def repair(ob):
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0000003)
 seen=set();dups=[]
 for f in bm.faces:
  k=frozenset(v for v in f.verts)
  if k in seen or f.calc_area()<1e-12:dups.append(f)
  else:seen.add(k)
 if dups:bmesh.ops.delete(bm,geom=dups,context='FACES')
 boundary=[e for e in bm.edges if e.is_boundary]
 if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
 return sum(1 for e in ob.data.edges) # topology audited later
sources={}
for fn in sorted(SRC.glob('*.json')):
 id=fn.stem
 if id in ['manifest','prostate']:continue
 data=json.load(open(fn));group='lung_left' if id.endswith('_left') and id.startswith('lung') else 'lung_right' if id.endswith('_right') and id.startswith('lung') else id
 vs=[(-p[0]/1000,-(p[1]-155)/1000,(p[2]-430)/1000) for p in data['vertices']]
 ob=mesh(id.replace('_',' ').title()+' | source surface',vs,data['faces'],group,id+'_surface',ma=mats[group]);repair(ob);sources[id]=ob
 # Display smoothing: one subdivision; retained originals remain untouched on disk.
 bpy.context.view_layer.objects.active=ob;ob.select_set(True);mod=ob.modifiers.new('Display subdivision · not recovered anatomy','SUBSURF');mod.levels=1;mod.render_levels=1;bpy.ops.object.modifier_apply(modifier=mod.name);ob.select_set(False)
 ob['source_case']='s1233';ob['source_revision']='75ec4e6530abe4d434b07958e90bdc9dec062bef';ob['source_file']=fn.name

def bounds(ob):
 vs=[ob.matrix_world@v.co for v in ob.data.vertices];lo=Vector([min(v[i] for v in vs) for i in range(3)]);hi=Vector([max(v[i] for v in vs) for i in range(3)]);return lo,hi,(lo+hi)*.5,hi-lo

def tube(name,pts,radius,id,aid,ma,role='detail',radii=None):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=radius;cu.bevel_resolution=3;cu.resolution_u=16;cu.use_fill_caps=True
 sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for i,(p,co) in enumerate(zip(sp.bezier_points,pts)):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO';p.radius=radii[i] if radii else 1
 ob=bpy.data.objects.new(name,cu);s.collection.objects.link(ob);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH');ob=bpy.context.object;return register(ob,id,aid,role,'schematic',ma)
def ellipsoid(name,center,radii,id,aid,ma,role='detail'):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,location=center);ob=bpy.context.object;ob.name=name;ob.scale=radii;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return register(ob,id,aid,role,'schematic',ma)
def cone_between(name,base,tip,radius,id,aid,ma):
 a,b=Vector(base),Vector(tip);v=b-a;bpy.ops.mesh.primitive_cone_add(vertices=40,radius1=radius,radius2=radius*.12,depth=v.length,location=(a+b)*.5);ob=bpy.context.object;ob.name=name;ob.rotation_euler=v.to_track_quat('Z','Y').to_euler();bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);bev=ob.modifiers.new('Soft papillary form','BEVEL');bev.width=.001;bev.segments=3;bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=bev.name);return register(ob,id,aid,'detail','schematic',ma)
def duplicate(ob,name,id,aid,role='cutaway',ma=None):
 cp=ob.copy();cp.data=ob.data.copy();cp.animation_data_clear();cp.name=name;s.collection.objects.link(cp);return register(cp,id,aid,role,'source-derived exterior; schematic wall/section',ma)
def applybool(ob,cutter,operation='DIFFERENCE'):
 bpy.context.view_layer.objects.active=ob;mod=ob.modifiers.new('Authored educational section','BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name)
def section_shell(ob,id,thickness=.003,shrink=.84,ma=None):
 lo,hi,c,dim=bounds(ob);cp=duplicate(ob,id+' | anterior teaching section',id,id+'_cutaway',ma=ma or mats[id]);inside=bpy.data.objects.new('temp inner',ob.data.copy());s.collection.objects.link(inside)
 for v in inside.data.vertices:v.co=c+(v.co-c)*shrink
 applybool(cp,inside);bpy.data.objects.remove(inside,do_unlink=True)
 # Remove anterior half, anterior is negative Blender Y.
 plane=c.y-dim.y*.04;bpy.ops.mesh.primitive_cube_add(size=1,location=(c.x,plane-.5,c.z));cut=bpy.context.object;cut.scale=(1,1,1);applybool(cp,cut);bpy.data.objects.remove(cut,do_unlink=True)
 cp['cut_plane_blender_y_m']=plane;cp['cutaway_note']='Schematic wall thickness and frontal teaching section, not scan segmentation of wall layers';return cp,plane,c,dim
# Kidney sections and radial collecting-system teaching structures.
for id in ['kidney_left','kidney_right']:
 ob=sources[id];cp,plane,c,dim=section_shell(ob,id,shrink=.79,ma=cortex);side=1 if id.endswith('left') else -1
 pelvis=Vector((c.x-side*dim.x*.19,plane+.002,c.z-.002));ellipsoid(id+' renal pelvis',pelvis,(.008,.005,.014),id,id+'_pelvis',collecting)
 for j in range(7):
  ang=math.radians(-75+j*25);base=Vector((c.x+side*dim.x*.30*math.cos(ang),plane+.006,c.z+dim.z*.37*math.sin(ang)))
  tip=pelvis+Vector((side*.005,0,(j-3)*.003));cone_between(id+' medullary pyramid '+str(j+1),base,tip,min(dim.x*.12,.009),id,id+'_pyramid_'+str(j+1),medulla)
  end=tip+Vector((-side*.001,-.001,0));tube(id+' calyx '+str(j+1),[end,(end+pelvis)*.5+Vector((0,-.002,0)),pelvis],.0017,id,id+'_calyx_'+str(j+1),collecting)
 tube(id+' hilar ureter origin',[pelvis,pelvis+Vector((-side*.008,0,-.012)),pelvis+Vector((-side*.010,.002,-.027))],.0024,id,id+'_ureter_origin',collecting)
# Stomach cutaway with raycast-adherent inner rugae.
ob=sources['stomach'];cp,plane,c,dim=section_shell(ob,'stomach',shrink=.88,ma=mats['stomach']);bvh=BVHTree.FromPolygons([v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons])
for j in range(9):
 pts=[];z=c.z+dim.z*(-.34+j*.085)
 for k in range(25):
  x=c.x+dim.x*(-.36+k*.03);zz=z+.0018*math.sin(k*.65+j)
  hit,normal,face,distance=bvh.ray_cast(Vector((x,1,zz)),Vector((0,-1,0)),2)
  if hit is not None and hit.y>plane+.005:pts.append(hit-normal*.0035)
 if len(pts)>3:tube('Gastric ruga '+str(j+1),pts,.0013,'stomach','gastric_ruga_'+str(j+1),rugae_mat)
# Gallbladder lumen and a representative cystic duct continuation.
ob=sources['gallbladder'];cp,plane,c,dim=section_shell(ob,'gallbladder',shrink=.86)
tube('Cystic duct · schematic',[c+Vector((-.012,0,.007)),c+Vector((-.024,.003,.014)),c+Vector((-.028,.009,.025))],.0018,'gallbladder','cystic_duct',collecting)
# Lobar bronchial hierarchy: branches terminate inside representative lobes, not segmental anatomy.
air=mats['bronchial_tree'];carina=Vector((0,.007,.080));mainR=Vector((-.028,.009,.060));interR=Vector((-.042,.008,.033));mainL=Vector((.042,.008,.068))
tube('Distal tracheal teaching axis',[Vector((.003,.006,.140)),Vector((.001,.007,.111)),carina],.007,'bronchial_tree','distal_trachea',air,'surface',radii=[1,1,.9])
paths=[('right_main',[carina,mainR,interR],.006),('left_main',[carina,Vector((.021,.009,.070)),mainL],.0055)]
for aid,pts,rad in paths:tube(aid.replace('_',' ').title(),pts,rad,'bronchial_tree',aid,air,'surface',radii=[1,.9,.8])
for lobe,start in [('lung_upper_lobe_right',mainR),('lung_middle_lobe_right',interR),('lung_lower_lobe_right',interR),('lung_upper_lobe_left',mainL),('lung_lower_lobe_left',mainL)]:
 lo,hi,cc,dm=bounds(sources[lobe]);end=cc+Vector((0,dm.y*.05,dm.z*.05));mid=start.lerp(end,.55);tube(lobe+' lobar bronchus',[start,mid,end],.0036,'bronchial_tree',lobe+'_lobar_bronchus',air,'surface',radii=[1,.8,.52])
 # Three distal illustrative offshoots per lobe, not named segmental mapping.
 for j in range(3):
  dest=cc+Vector(((j-1)*dm.x*.18,dm.y*(.10 if j%2 else -.12),dm.z*(.22 if j==1 else -.20)))
  tube(lobe+' distal illustration '+str(j+1),[mid,end,dest],.0017,'bronchial_tree',lobe+'_distal_'+str(j+1),air,'surface',radii=[1,.8,.32])
# Bladder with open frontal wall, trigone and bilateral ureters placed pedagogically.
bl=ellipsoid('Urinary bladder | authored surface',Vector((0,-.027,-.285)),(.039,.031,.040),'bladder','bladder_surface',mats['bladder'],'surface')
# Flatten superior dome mildly and taper neck.
for v in bl.data.vertices:
 f=(v.co.z/.04+1)*.5;v.co.x*=.74+.26*f;v.co.y*=.85+.15*f
# section_shell expects world-space geometry, bake location into vertex coordinates.
for v in bl.data.vertices:v.co+=bl.location
bl.location=(0,0,0)
cp,plane,c,dim=section_shell(bl,'bladder',shrink=.88)
trig=[(c.x-.012,plane+.006,c.z-.006),(c.x+.012,plane+.006,c.z-.006),(c.x,plane+.006,c.z-.027)]
mesh('Bladder trigone · schematic',trig,[(0,1,2)],'bladder','bladder_trigone','detail','schematic',rugae_mat)
for id in ['kidney_left','kidney_right']:
 _,_,kc,kd=bounds(sources[id]);side=1 if 'left' in id else -1;start=kc+Vector((-side*kd.x*.27,0,-.004));end=Vector((side*.012,plane+.009,c.z-.006))
 tube(id+' ureter to bladder',[start,start+Vector((-side*.010,0,-.055)),Vector((side*.026,.005,-.210)),end],.0022,'bladder',id+'_ureter',collecting,'surface',radii=[1,.85,.75,.7])
tube('Urethral outlet · schematic',[c+Vector((0,0,-.034)),c+Vector((0,.003,-.055))],.003,'bladder','urethral_outlet',fibrous,'surface')
# Authored brain hemispheres with folds, cerebellum, stem; positions schematic.
def parametric(name,func,nu,nv,id,aid,ma,role='surface'):
 vs=[];fs=[]
 for j in range(nv+1):
  for i in range(nu):vs.append(func(i/nu,j/nv))
 for j in range(nv):
  for i in range(nu):a=j*nu+i;b=j*nu+(i+1)%nu;fs.append((a,b,b+nu,a+nu))
 ob=mesh(name,vs,fs,id,aid,role,'schematic',ma);repair(ob);return ob
bc=Vector((0,0,.405))
brains=[]
for side in [-1,1]:
 def f(u,v,side=side):
  a=u*math.tau;b=v*math.pi;fold=math.sin(7*a+1.4*math.sin(3*b))*math.sin(9*b+.8*math.cos(3*a));rel=1+.055*fold*math.sin(b)**2
  return bc+Vector((side*(.003+.065*(.5+.5*math.cos(a))*math.sin(b)*rel),-.080*math.sin(a)*math.sin(b)*rel,.055*math.cos(b)*rel+.014))
 ob=parametric(('Right' if side<0 else 'Left')+' cerebral hemisphere | schematic folds',f,112,72,'brain','hemisphere_'+('right' if side<0 else 'left'),mats['brain']);brains.append(ob)
 # Sagittal teaching section is a distinct smooth white-matter core, not a labeled gyral atlas.
 cp=duplicate(ob,ob.name+' | cutaway','brain',ob['anatomy_id']+'_cutaway',ma=mats['brain'])
 if side==1:
  bpy.ops.mesh.primitive_cube_add(size=1,location=(.506,0,.405));cu=bpy.context.object;applybool(cp,cu);bpy.data.objects.remove(cu,do_unlink=True)
  ellipsoid('White matter teaching core',bc+Vector((.004,0,.012)),(.005,.059,.038),'brain','white_matter_core',white)
  tube('Lateral ventricle · schematic C',[bc+Vector((.010,-.036,.007)),bc+Vector((.010,-.018,.028)),bc+Vector((.010,.016,.028)),bc+Vector((.010,.032,.003)),bc+Vector((.010,.018,-.004))],.004,'brain','lateral_ventricle',vent)
  tube('Corpus callosum · schematic arch',[bc+Vector((.013,-.037,.017)),bc+Vector((.013,-.012,.038)),bc+Vector((.013,.018,.036)),bc+Vector((.013,.037,.016))],.004,'brain','corpus_callosum',fibrous)
cb=ellipsoid('Cerebellum | schematic folia',bc+Vector((0,.041,-.036)),(.050,.039,.026),'brain','cerebellum',mats['brain'],'surface')
for v in cb.data.vertices:v.co*=1+.018*math.cos(v.co.z/.026*24)
# Cerebellum/stem should remain visible in either view; duplicate roles for clear toggle.
cp=duplicate(cb,'Cerebellum | section context','brain','cerebellum_cutaway')
st=ellipsoid('Brainstem | schematic',bc+Vector((0,.016,-.054)),(.012,.014,.033),'brain','brainstem',fibrous,'surface');duplicate(st,'Brainstem | section context','brain','brainstem_cutaway')
# Keep detailed pre-existing authored heart as optional fitted replacement, with explicit provenance.
for kind,fn in [('surface','Cardiac_Atlas_Clinical_Full_ED.glb'),('cutaway','Cardiac_Atlas_Clinical_Cutaway_ED.glb')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/'sources'/fn));new=[o for o in bpy.data.objects if o not in before];meshes=[o for o in new if o.type=='MESH'];walls=[o for o in meshes if 'complete wall' in o.name] or meshes
 coords=[o.matrix_world@v.co for o in walls for v in o.data.vertices];lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)]);center=(lo+hi)*.5
 _,_,target,dim=bounds(sources['heart']);scale=min(dim[i]/max(hi[i]-lo[i],.0001) for i in range(3))
 for ob in meshes:
  mat=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=Matrix.Identity(4)
  for v in ob.data.vertices:v.co=(mat@v.co-center)*scale+target
  register(ob,'heart_detailed','authored_'+kind+'_'+ob.name,kind,'independently authored; uniform pedagogical fit, not source registered')
  ob['clinical_color']=list(ob.data.materials[0].diffuse_color[:3]) if len(ob.data.materials) else list(clinical['heart'])
 for ob in new:
  if ob.type!='MESH':bpy.data.objects.remove(ob,do_unlink=True)
collections['heart_detailed'].hide_render=True;collections['heart_detailed'].hide_viewport=True
# UVs on all actual mesh objects. Each source outer mesh has a real non-overlapping atlas.
for id,obs in objects.items():
 for ob in obs:
  if ob.type!='MESH':continue
  for prop in ['hide_viewport']:
   try:ob.driver_remove(prop)
   except:pass
  ob.hide_viewport=False;ob.hide_set(False);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  if id!='heart_detailed':
   bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
  if ob.data.uv_layers:ob.data.uv_layers.active.name='Teaching UV'
  ob.select_set(False)
  if (ob['view_role']=='surface' and specs[id]['cutawaySupport']) or ob['view_role'] in ['cutaway','detail']:
   d=ob.driver_add('hide_viewport').driver;d.expression='c > .5' if ob['view_role']=='surface' else 'c < .5';v=d.variables.new();v.name='c';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["cutaway"]'
# Studio
studio=bpy.data.collections.new('STUDIO · not anatomy');s.collection.children.link(studio)
def move_studio(ob):
 for co in list(ob.users_collection):co.objects.unlink(ob)
 studio.objects.link(ob)
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def camera(name,loc,target,scale):
 bpy.ops.object.camera_add(location=loc);ob=bpy.context.object;ob.name=name;ob.data.type='ORTHO';ob.data.ortho_scale=scale;aim(ob,target);move_studio(ob);return ob
s.camera=camera('CAM · complete assembly',(0,-1.5,.09),(0,0,.07),.91)
camera('CAM · organ closeup',(.16,-.6,.15),(0,0,0),.2)
for name,loc,power,size,col in [('KEY',(-.5,-.7,.8),90,.7,(1,.84,.72)),('FILL',(.6,-.4,.3),55,.65,(.65,.82,1)),('RIM',(.1,.4,.6),100,.6,(.75,.88,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.name=name;ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size;ob.data.color=col;aim(ob,(0,0,.1));move_studio(ob)
# Native documentation embedded.
tx=bpy.data.texts.new('START HERE · anatomy provenance and controls');tx.write('ANATOMY WORKSHOP\nEducational reusable meshes. Not clinically validated.\nSelect WORKSHOP CONTROL for material_mode 0 tissue/1 categorical/2 transparency; cutaway 0 full/1 supported authored sections.\n17 s1233 source surfaces retain relative positions after one shared translation. Optional detailed heart, brain, bladder, ureters and airway internals are authored teaching geometry, not registered scans.\nOne Blender unit = one metre. Blender X patient left, Y posterior, Z superior. Export glTF X patient left,Y superior,Z anterior.\nSource-derived low-poly surfaces were repaired and subdivided once for display; originals remain unchanged in source archive.\nKidney, stomach and gallbladder inner walls are schematic derivatives; no clinical wall thickness, collecting-system segmentation or airway segmental atlas is claimed.\n')
ctrl['material_mode']=0;ctrl['cutaway']=0
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop.blend'),compress=True)
# Persistent helper map used by export/bake phase.
json.dump({id:[o.name for o in obs] for id,obs in objects.items()},open(R/'object_map.json','w'),indent=2)
s.render.resolution_x=1200;s.render.resolution_y=1600;s.cycles.samples=32;s.render.filepath=str(D/'renders/01_assembly_preview.png');bpy.ops.render.render(write_still=True)
print('COLLECTION BUILD COMPLETE',flush=True)
