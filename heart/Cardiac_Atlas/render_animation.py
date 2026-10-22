import os
import bpy,os,json,math
R=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene;c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse'];s.cycles.use_denoising=False;s.cycles.samples=20;s.cycles.transparent_max_bounces=24
s.render.resolution_x=s.render.resolution_y=640;s.render.image_settings.file_format='PNG'
for ma in bpy.data.materials:
 if not ma.use_nodes:continue
 for no in ma.node_tree.nodes:
  if no.name.startswith('TRANSPARENT •'):
   no.inputs['Transmission Weight'].default_value=0.;no.inputs['Alpha'].default_value=1.;no.inputs['Roughness'].default_value=.3
  if no.type=='MIX_SHADER' and no.location.y==-250:no.inputs[0].default_value=.88
for mode,name in [(0,'tissue'),(1,'clinical'),(2,'transparent')]:
 os.makedirs(R+'/animation/'+name,exist_ok=True)
 c['material_set']=mode;c['cutaway']=1 if mode==1 else 0;c['show_pericardium']=0
 s.camera=bpy.data.objects['CAM 02 • anterior teaching section' if mode==1 else 'CAM 01 • anterior hero']
 for col in bpy.data.collections:
  if col.name[:2] in ('04','05','06'):col.hide_render=(mode==1)
 for fr in range(1,25):
  s.frame_set(fr);s.render.filepath=R+'/animation/'+name+'/'+str(fr).zfill(3)+'.png'
  if not os.path.exists(s.render.filepath):bpy.ops.render.render(write_still=True)
# Numeric proof of deformations and cycle timing.
qa=[]
for fr in (1,3,5,8,10,12,14,20,24,25):
 s.frame_set(fr);bpy.context.view_layer.update();ob=bpy.data.objects['LV | complete wall'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=[v.co.z for v in me.vertices];x=[v.co.x for v in me.vertices]
 qa.append({'frame':fr,'time_seconds':(fr-1)/30,'atrial_contraction':float(c['atrial_systole']),'ventricular_contraction':float(c['ventricular_systole']),'AV_open':float(c['AV_open']),'semilunar_open':float(c['semilunar_open']),'LV_bounds_x_BU':[min(x),max(x)],'LV_bounds_z_BU':[min(z),max(z)]});ev.to_mesh_clear()
json.dump(qa,open(R+'/exports/animation_QA.json','w'),indent=2)
print('ANIMATION FRAMES COMPLETE')
