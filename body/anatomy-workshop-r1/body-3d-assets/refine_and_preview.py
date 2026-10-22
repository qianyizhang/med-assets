import bpy,bmesh,math,json,os,ast,random
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;D=R.parent/'body-3d-delivery';s=bpy.context.scene;ctrl=bpy.data.objects['WORKSHOP CONTROL · material and cutaway'];manifest=json.load(open(D/'manifest.json'));specs={a['id']:a for a in manifest['assets']};om=json.load(open(R/'object_map.json'));objects={id:[bpy.data.objects[n] for n in names] for id,names in om.items()};collections={id:objects[id][0].users_collection[0] for id in objects};sources={o['source_file'][:-5]:o for o in bpy.data.objects if 'source_file' in o};mats={id:bpy.data.materials[id+' tissue / clinical / transparent'] for id in objects if id!='heart_detailed'}
root=ast.parse(open(R/'build_collection.py').read());nodes=[n for n in root.body if isinstance(n,(ast.FunctionDef,ast.Import,ast.ImportFrom)) or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['colors','clinical'] for t in n.targets)];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(R/'build_collection.py'),'exec'))
for ma in bpy.data.materials:
 if not ma.use_nodes:continue
 for n in ma.node_tree.nodes:
  if n.type=='BSDF_PRINCIPLED':
   n.inputs['Subsurface Scale'].default_value=.002;n.inputs['Specular IOR Level'].default_value=.26;n.inputs['Coat Weight'].default_value=.12
  if n.type=='TEX_NOISE' and n.inputs['Scale'].default_value>30:
   n.inputs['Scale'].default_value=26 if 'pancreas' in ma.name else 110 if 'lung' in ma.name else 75
  if n.type=='BUMP':n.inputs['Distance'].default_value=.00032 if 'pancreas' in ma.name else .00016
for o in bpy.data.objects:
 if o.type=='LIGHT':o.data.energy*=.35
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.014,.021,.030,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.3
# Mild volume-preserving appearance refinement and explicit outward normals.
for id,ob in sources.items():
 bpy.context.view_layer.objects.active=ob;mod=ob.modifiers.new('Surface cleanup · 3 smoothing passes','SMOOTH');mod.factor=.45;mod.iterations=3;bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.to_mesh(ob.data);bm.free()
 ob['modifications']='Weld within 0.001 mm; remove tiny/duplicate faces; fill boundary loops; outward normals; one subdivision and 3 mild smoothing passes; UV unwrap. Display derivative, not recovered anatomy.'
# Tracheal C-shaped cartilage rings: absent posterior quarter, only upper tracheal shaft.
ob=sources['trachea'];vs=[v.co for v in ob.data.vertices]
for j,z in enumerate([.116+i*.0044 for i in range(14)]):
 band=[v for v in vs if abs(v.z-z)<.0026]
 if len(band)<4:continue
 xmin,xmax=min(v.x for v in band),max(v.x for v in band);ymin,ymax=min(v.y for v in band),max(v.y for v in band);cx=(xmin+xmax)*.5;cy=(ymin+ymax)*.5;rx=(xmax-xmin)*.51;ry=(ymax-ymin)*.51
 if rx>.014:continue
 pts=[(cx+rx*math.cos(a),cy+ry*math.sin(a),z) for a in [math.radians(135+k*270/36) for k in range(37)]]
 tube('Tracheal C cartilage '+str(j+1),pts,.00065,'trachea','tracheal_cartilage_'+str(j+1),bpy.data.materials['Pale fibrous tissue'],'surface')
# Pancreatic duct follows principal-axis centroid bins of source surface; illustration only.
import numpy as np
ob=sources['pancreas'];v=np.array([list(v.co) for v in ob.data.vertices]);c=v.mean(0);_,_,vh=np.linalg.svd(v-c,full_matrices=False);axis=vh[0];proj=(v-c)@axis;pts=[]
for t in np.linspace(np.quantile(proj,.08),np.quantile(proj,.92),12):
 q=v[abs(proj-t)<.007]
 if len(q):pts.append(Vector(q.mean(0)))
if len(pts)>4:tube('Pancreatic duct · illustrative internal route',pts,.0012,'pancreas','pancreatic_duct',bpy.data.materials['Renal collecting system'],'detail')
# Internal duct available via transparency / detail reveal, not a claimed segmented lumen.
specs['pancreas']['detailSupport']=True
# Ensure new detail meshes have UVs and snapshot map.
for id,obs in objects.items():
 for ob in obs:
  if ob.type!='MESH' or ob.data.uv_layers:continue
  ob.hide_viewport=False;ob.hide_set(False);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT');ob.data.uv_layers.active.name='Teaching UV'
for id in ['kidney_left','kidney_right','stomach','gallbladder']:
 specs[id]['notes'].append('Source-derived exterior plus explicitly authored internal teaching layers. Inner wall thickness and kidney cortex/pyramids/calyces/pelvis or gastric rugae are not source segmentations.')
specs['trachea']['organIds']=['lungs','trachea'];specs['bladder']['organIds']=['bladder','kidneys','ureters']
json.dump(manifest,open(D/'manifest.json','w'),ensure_ascii=False,indent=2);json.dump({id:[o.name for o in obs] for id,obs in objects.items()},open(R/'object_map.json','w'),indent=2)
ctrl['cutaway']=0;ctrl['material_mode']=0;bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop.blend'),compress=True)
def render(id,name,cut,mat,sz=1000):
 for key,col in collections.items():col.hide_render=(key!=id)
 ctrl['cutaway']=cut;ctrl['material_mode']=mat;bpy.context.view_layer.update();ob=objects[id][0];lo,hi,c,dim=bounds(ob)
 if id=='brain':c=Vector((0,0,.405));dim=Vector((.14,.18,.15))
 cam=bpy.data.objects['CAM · organ closeup'];cam.location=c+Vector((.05,-.5,.035));aim(cam,c);cam.data.ortho_scale=max(dim.x,dim.z)*1.55;s.camera=cam;s.render.resolution_x=s.render.resolution_y=sz;s.cycles.samples=48;s.render.filepath=str(D/'renders'/name);bpy.ops.render.render(write_still=True)
render('kidney_left','02_kidney_cutaway_preview.png',1,1)
render('stomach','03_stomach_cutaway_preview.png',1,0)
render('brain','04_brain_preview.png',0,0)
for id,col in collections.items():col.hide_render=(id=='heart_detailed')
ctrl['cutaway']=0;ctrl['material_mode']=0;s.camera=bpy.data.objects['CAM · complete assembly'];s.render.resolution_x=1200;s.render.resolution_y=1600;s.cycles.samples=48;s.render.filepath=str(D/'renders/01_assembly_preview.png');bpy.ops.render.render(write_still=True)
print('REFINEMENT PREVIEWS COMPLETE',flush=True)
