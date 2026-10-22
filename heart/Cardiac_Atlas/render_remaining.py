import os
import bpy,os
R=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene;c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse'];s.cycles.use_denoising=False;s.cycles.transparent_max_bounces=24
for ma in bpy.data.materials:
 if not ma.use_nodes:continue
 for no in ma.node_tree.nodes:
  if no.name.startswith('TRANSPARENT •'):
   no.inputs['Transmission Weight'].default_value=0.;no.inputs['Alpha'].default_value=1.;no.inputs['Roughness'].default_value=.3
  if no.type=='MIX_SHADER' and no.location.y==-250:no.inputs[0].default_value=.88

def render(name,mode,cut,camera,hide=(),frame=1,sz=1400,samples=96):
 c['material_set']=mode;c['cutaway']=cut;s.camera=bpy.data.objects[camera];s.frame_set(frame)
 for col in bpy.data.collections:
  if col.name[:2] in ('04','05','06'):col.hide_render=col.name[:2] in hide
 s.cycles.samples=samples;s.render.resolution_x=s.render.resolution_y=sz;s.render.filepath=R+'/renders/'+name+'.png';bpy.ops.render.render(write_still=True)
render('04_transparent',2,0,'CAM 01 • anterior hero',sz=1300,samples=96)
render('05_posterior_vessels',1,0,'CAM 03 • posterior vessels')
render('06_valve_apparatus',1,1,'CAM 04 • valve apparatus',('04','05','06'),frame=1)
render('07_systolic_section',1,1,'CAM 02 • anterior teaching section',('04','05','06'),frame=10)
