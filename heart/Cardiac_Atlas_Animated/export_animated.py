import bpy, os, json, math
from mathutils import Vector
R=os.path.dirname(os.path.abspath(__file__))
s=bpy.context.scene;c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse']
s.frame_start=1;s.frame_end=25;s.render.fps=30
# Preserve editable original driver rig and packed maps in a portable native copy.
s['animation_delivery']='Portable cardiac-cycle morph clips accompany this editable original. One cycle frames 1–25 at 30fps; 0.8 seconds, illustrative 75 BPM. Not biomechanical/CFD simulation.'
t=bpy.data.texts.new('EXPORT ANIMATED GLB • reproducible recipe');t.write(open(__file__).read())
s.frame_set(1);c['cutaway']=0;c['material_set']=0
bpy.ops.wm.save_as_mainfile(filepath=R+'/Cardiac_Atlas_Animated_Source.blend')
meshes=[o for o in bpy.data.objects if o.type=='MESH' and {co.name[:2] for co in o.users_collection}&{'01','02','03','04','05','06'} and 'pericardium' not in o.name.lower()]
# Sample the authored continuous control rig before removing any drivers.
samples={}
for f in range(1,26):
 s.frame_set(f);bpy.context.view_layer.update()
 for o in meshes:
  if o.data.shape_keys:samples.setdefault(o.name,[]).append([float(k.value) for k in o.data.shape_keys.key_blocks][1:])
json.dump(samples,open(R+'/authored_morph_samples.json','w'),indent=2)
for o in meshes:
 keys=o.data.shape_keys
 if keys:
  keys.animation_data_clear()
  # Apply topology-preserving leaflet modifiers independently to every shape.
  if len(o.modifiers):
   key_names=[k.name for k in keys.key_blocks]
   positions=[];newmesh=None
   for j in range(len(keys.key_blocks)):
    for k in keys.key_blocks[1:]:k.value=0
    if j:keys.key_blocks[j].value=1
    bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
    positions.append([v.co.copy() for v in me.vertices])
    if j==0:newmesh=me
    else:bpy.data.meshes.remove(me)
   o.modifiers.clear();o.data=newmesh
   for name,coords in zip(key_names,positions):
    k=o.shape_key_add(name=name)
    assert len(k.data)==len(coords)
    for v,co in zip(k.data,coords):v.co=co
   keys=o.data.shape_keys
  for j,k in enumerate(keys.key_blocks[1:]):
   for f,values in enumerate(samples[o.name],1):k.value=values[j];k.keyframe_insert('value',frame=f,group='Cardiac cycle')
  if keys.animation_data and keys.animation_data.action:
   keys.animation_data.action.name='Cardiac cycle • 75 BPM | '+o.name
   for fc in keys.animation_data.action.fcurves:
    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 for prop in ('hide_render','hide_viewport'):
  try:o.driver_remove(prop)
  except:pass
 o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
for col in bpy.data.collections:col.hide_viewport=False
# Portable clinical materials; original procedural materials stay in native source.
clinical={}
for o in meshes:
 for slot in o.material_slots:
  old=slot.material
  if not old:continue
  if old.name not in clinical:
   m=bpy.data.materials.new('Clinical | '+old.name);m.use_nodes=True;m.diffuse_color=old.diffuse_color
   p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=old.diffuse_color;p.inputs['Roughness'].default_value=.38
   clinical[old.name]=m
  slot.link='OBJECT';slot.material=clinical[old.name]
s.frame_set(1)
for cut,name in [(False,'Heart_Clinical_Animated.glb'),(True,'Heart_Cutaway_Animated.glb'),(False,'Heart_Tissue_Animated.glb')]:
 bpy.ops.object.select_all(action='DESELECT')
 for o in meshes:
  cols={co.name[:2] for co in o.users_collection};include=True
  if '01' in cols:
   if 'complete wall' in o.name:include=not cut
   elif 'anterior section' in o.name:include=cut
   elif 'appendage' in o.name:include=not cut
  if cut and cols&{'05','06'}:include=False
  if include:o.select_set(True)
  if name=='Heart_Tissue_Animated.glb' and 'complete wall' in o.name:
   for slot in o.material_slots:slot.material=bpy.data.materials['BAKED TISSUE • shared 2K PBR atlas']
 bpy.ops.export_scene.gltf(filepath=R+'/'+name,export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='SCENE',export_anim_scene_split_object=False,export_nla_strips_merged_animation_name='CardiacCycle_75BPM',export_frame_range=True,export_force_sampling=True,export_skins=False,export_morph=True,export_morph_normal=True,export_apply=False,export_yup=True,export_extras=True,export_anim_slide_to_zero=True)
 print('EXPORTED',name,flush=True)
print('DONE',flush=True)
