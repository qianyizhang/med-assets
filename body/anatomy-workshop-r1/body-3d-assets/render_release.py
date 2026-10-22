import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;D=R.parent/'body-3d-delivery';s=bpy.context.scene;c=bpy.data.objects['WORKSHOP CONTROL · material and cutaway'];om=json.load(open(R/'object_map.json'));cols={id:bpy.data.objects[names[0]].users_collection[0] for id,names in om.items()};s.cycles.use_denoising=False;s.cycles.samples=128

for col in cols.values():col.hide_viewport=False

def aim(ob,p):ob.rotation_euler=(Vector(p)-ob.location).to_track_quat('-Z','Y').to_euler()
def view(ids,name,center,scale,mode=0,cut=0,offset=(.02,-.7,.02),res=1200,samples=128):
 for id,col in cols.items():col.hide_render=id not in ids
 c['material_mode']=mode;c['cutaway']=cut;bpy.context.view_layer.update();cam=bpy.data.objects['CAM · organ closeup'];cam.location=Vector(center)+Vector(offset);aim(cam,center);cam.data.ortho_scale=scale;s.camera=cam;s.render.resolution_x=s.render.resolution_y=res;s.cycles.samples=samples;s.render.filepath=str(D/'renders'/name);bpy.ops.render.render(write_still=True)
view(['kidney_left','kidney_right','bladder'],'09_urinary_system.png',(0,-.005,-.205),.32,1,1,res=1400)
view(['brain'],'10_brain_schematic.png',(0,0,.405),.195,0,0,res=1200)
view(['brain'],'11_brain_section_schematic.png',(0,0,.405),.195,1,1,offset=(.6,-.12,.04),res=1200)
# Lung surfaces transparent, authored lobar tree and tracheal rings opaque for clarity.
changed=[]
for ma in bpy.data.materials:
 if ma.name.startswith('bronchial_tree tissue') or ma.name.startswith('trachea tissue'):
  out=next(n for n in ma.node_tree.nodes if n.type=='OUTPUT_MATERIAL');n=out.inputs[0].links[0].from_node
  try:n.inputs[0].driver_remove('default_value')
  except:pass
  n.inputs[0].default_value=0;changed.append(n)
view(['lung_left','lung_right','bronchial_tree'],'12_lobar_airway_hierarchy.png',(0,.005,.065),.31,2,0,res=1400)
# All-organ source assembly with the independent heart optional and not overlaid.
for id,col in cols.items():col.hide_render=(id in ['heart_detailed','bronchial_tree'])
c['material_mode']=0;c['cutaway']=0;s.camera=bpy.data.objects['CAM · complete assembly'];s.render.resolution_x=1200;s.render.resolution_y=1600;s.cycles.samples=128;s.render.filepath=str(D/'renders/13_final_assembly.png');bpy.ops.render.render(write_still=True)
# Neutral clay matched comparison: original raw surface versus revised display geometry.
for id,col in cols.items():col.hide_render=(id!='liver')
ob=next(bpy.data.objects[n] for n in om['liver'] if bpy.data.objects[n].get('view_role')=='surface');vs=[v.co for v in ob.data.vertices];center=Vector([sum(v[i] for v in vs)/len(vs) for i in range(3)]);cam=bpy.data.objects['CAM · organ closeup'];cam.location=center+Vector((.05,-.6,.04));aim(cam,center);cam.data.ortho_scale=.245;s.camera=cam;s.render.resolution_x=s.render.resolution_y=1200
ma=bpy.data.materials.new('Neutral clay evidence');ma.use_nodes=True;p=ma.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.28,.31,.33,1);p.inputs['Roughness'].default_value=.65;ob.data.materials.clear();ob.data.materials.append(ma);s.render.filepath=str(D/'renders/15_refined_clay.png');bpy.ops.render.render(write_still=True)
source=json.load(open(R.parent/'body-3d-source/tb3/presentation/task-explorer/anatomy/liver.json'));me=bpy.data.meshes.new('Immutable raw comparison');me.from_pydata([(-v[0]/1000,-(v[1]-155)/1000,(v[2]-430)/1000) for v in source['vertices']],[],source['faces']);raw=bpy.data.objects.new('Raw source comparison only',me);s.collection.objects.link(raw);me.materials.append(ma)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
for po in me.polygons:po.use_smooth=True
ob.hide_render=True;s.render.filepath=str(D/'renders/14_original_clay.png');bpy.ops.render.render(write_still=True)
print('RELEASE RENDERS COMPLETE',flush=True)
