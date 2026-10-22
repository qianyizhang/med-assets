import os
import bpy,json,os,re
R=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene;c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse'];s.frame_set(1)
# Only standard PBR colors travel in generic exports; native shader networks remain in .blend.
materials={}
for ob in bpy.data.objects:
 if ob.type!='MESH':continue
 for slot in ob.material_slots:
  old=slot.material
  if old is None:continue
  if old.name not in materials:
   m=bpy.data.materials.new('GLTF '+old.name);m.use_nodes=True;m.diffuse_color=old.diffuse_color
   p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=old.diffuse_color;p.inputs['Roughness'].default_value=.38
   materials[old.name]=m
  slot.link='OBJECT';slot.material=materials[old.name]
# Driver-hidden structures are explicitly controlled by export selection below.
for ob in bpy.data.objects:
 for prop in ('hide_render','hide_viewport'):
  try:ob.driver_remove(prop)
  except:pass
 ob.hide_viewport=False;ob.hide_set(False)
for col in bpy.data.collections:col.hide_viewport=False
for cut,name in [(False,'Cardiac_Atlas_Clinical_Full_ED.glb'),(True,'Cardiac_Atlas_Clinical_Cutaway_ED.glb')]:
 bpy.ops.object.select_all(action='DESELECT')
 for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  cols={co.name[:2] for co in ob.users_collection}
  include=bool(cols&{'01','02','03','04','05','06'})
  if '01' in cols:
   if 'complete wall' in ob.name:include=not cut
   elif 'anterior section' in ob.name:include=cut
   elif 'appendage' in ob.name:include=not cut
  if 'pericardium' in ob.name.lower():include=False
  if cut and cols&{'05','06'}:include=False
  if include:ob.select_set(True)
 bpy.ops.export_scene.gltf(filepath=R+'/exports/'+name,export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_morph=False,export_apply=True,export_yup=True,export_extras=True)
print('GLB exports complete; glTF XYZ = (Blender X, Blender Z, -Blender Y), BU retained by exporter unless scene-unit metadata applies; inspect bounds manifest.')
