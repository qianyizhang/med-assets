import os
import bpy,json
R=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene;c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse']
tracks={
 'atrial_systole':[(1,0.),(3,1.),(5,0.),(25,0.)],
 'ventricular_systole':[(1,0.),(4,0.),(6,.25),(10,1.),(12,1.),(15,.12),(18,0.),(25,0.)],
 'AV_open':[(1,1.),(4,1.),(5,0.),(13,0.),(14,1.),(25,1.)],
 'semilunar_open':[(1,0.),(5,0.),(6,1.),(11,1.),(12,0.),(25,0.)]}
c.animation_data_clear()
for key,keys in tracks.items():
 del c[key];c[key]=float(keys[0][1]);c.id_properties_ui(key).update(min=0.,max=1.,description='Continuous floating-point animated control')
 for fr,value in keys:c[key]=float(value);c.keyframe_insert(data_path='["'+key+'"]',frame=fr)
for fc in c.animation_data.action.fcurves:
 fc.update_autoflags(c);fc.modifiers.new('CYCLES')
 for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type='AUTO_CLAMPED';kp.handle_right_type='AUTO_CLAMPED'
q=[]
for fr in range(1,26):
 s.frame_set(fr);bpy.context.view_layer.update();q.append({'frame':fr,**{k:float(c[k]) for k in ['atrial_systole','ventricular_systole','AV_open','semilunar_open']}})
json.dump(q,open(R+'/exports/continuous_control_QA.json','w'),indent=2)
assert 0<q[6]['ventricular_systole']<1,'Contraction must interpolate continuously'
for fn in ['build_heart.py','fix_continuous_controls.py']:
 tx=bpy.data.texts.get(fn) or bpy.data.texts.new(fn);tx.clear();tx.write(open(R+'/'+fn).read())
s.frame_set(1);c['material_set']=0;c['cutaway']=0;bpy.ops.wm.save_as_mainfile(filepath=R+'/Cardiac_Atlas.blend')
print('FLOAT CONTROL QA',q[6],flush=True)
