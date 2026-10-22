import os
import bpy,os,json,math
R=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene;c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse'];s.cycles.use_denoising=False
# Final anatomical controls and useful timeline landmarks.
for fr,name in [(1,'Atrial systole / ED'),(4,'AV valves close'),(6,'Ventricular ejection'),(12,'Semilunar valves close'),(14,'Diastolic filling')]:
 m=s.timeline_markers.new(name,frame=fr)
s.cycles.samples=96;s.render.resolution_x=s.render.resolution_y=1600
s['material_set_names']='0: procedural tissue-style; 1: clinical circulation colors; 2: transparent educational shell'
s['animation_model']='Illustrative regional shape-key shortening + torsion; valve timing; no biomechanical or flow simulation'
s['pericardial_layers']='Endocardium/myocardium/epicardium represented by material-bearing wall surfaces; parietal serous pericardium separate simplified envelope. Epicardium is visceral serous layer. Fibrous sac thickness/reflections simplified.'
# Persist the original-source generation recipe updated after visual QA.
for fn in ('build_heart.py','heart_geometry.py'):
 tx=bpy.data.texts.get(fn)
 if tx:tx.clear();tx.write(open(R+'/'+fn).read())
# A cleaner registered teaching preset is stored as camera rather than displacing geometry.
cam=bpy.data.objects['CAM 02 • anterior teaching section'];cam.data.ortho_scale=6.8
# Fix redundant hidden septal display copy; exported full septum remains available independently.
for ob in bpy.data.objects:
 if ob.name=='Interventricular septum | teaching section':
  for prop in ('hide_render','hide_viewport'):
   try:ob.driver_remove(prop)
   except:pass
  ob.hide_render=True;ob.hide_viewport=True
# Add clinical septal material to actual cut wall faces to avoid coincident shell artifacts.
ob=bpy.data.objects['LV | anterior section'];ob.data.materials.append(bpy.data.materials['Septa • muscular amber']);idx=len(ob.data.materials)-1
for p in ob.data.polygons:
 co=p.center
 if co.x<.34 and co.z<.7 and co.z>-1.7 and co.y>-.12:p.material_index=idx
# Default starting view is tissue exterior.
c['material_set']=0;c['cutaway']=0;c['show_pericardium']=0;s.frame_set(1);s.camera=bpy.data.objects['CAM 01 • anterior hero']
bpy.ops.wm.save_as_mainfile(filepath=R+'/Cardiac_Atlas.blend')
# Final high-quality still set.
def render(name,mode,cut,camera,hide=(),frame=1,sz=1500,samples=128):
 c['material_set']=mode;c['cutaway']=cut;s.camera=bpy.data.objects[camera];s.frame_set(frame)
 for col in bpy.data.collections:
  if col.name[:2] in ('04','05','06'):col.hide_render=col.name[:2] in hide
 # Suppress appendages when anterior wall is removed; they otherwise hover in the window.
 for ob in bpy.data.objects:
  if 'auricular appendage' in ob.name:ob.hide_render=bool(cut)
 s.cycles.samples=samples;s.render.resolution_x=s.render.resolution_y=sz;s.render.filepath=R+'/renders/'+name+'.png';bpy.ops.render.render(write_still=True)
render('01_tissue_hero',0,0,'CAM 01 • anterior hero')
render('02_clinical_cutaway',1,1,'CAM 02 • anterior teaching section',('04','05','06'))
render('03_clinical_full',1,0,'CAM 01 • anterior hero')
render('04_transparent',2,0,'CAM 01 • anterior hero',samples=192)
render('05_posterior_vessels',1,0,'CAM 03 • posterior vessels')
render('06_valve_apparatus',1,1,'CAM 04 • valve apparatus',('04','05','06'),frame=1,sz=1500)
# Image of systolic leaflet closure provides a visual comparison with diastole.
render('07_systolic_section',1,1,'CAM 02 • anterior teaching section',('04','05','06'),frame=10)
