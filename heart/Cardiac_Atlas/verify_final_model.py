import bpy,json,os
R=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene;c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse']
q={'blender_version':bpy.app.version_string,'units_mm_per_BU':s.unit_settings.scale_length*1000,'fps':s.render.fps,'mesh_count':sum(o.type=='MESH' for o in bpy.data.objects),'shape_key_objects':sum(o.type=='MESH' and o.data.shape_keys is not None for o in bpy.data.objects),'control_types':{k:type(c[k]).__name__ for k in ['atrial_systole','ventricular_systole','AV_open','semilunar_open']},'wall_uv_layers':{n:[u.name for u in bpy.data.objects[n].data.uv_layers] for n in ['LV | complete wall','RV | complete wall','LA | complete wall','RA | complete wall']},'image_textures':[{'name':im.name,'packed':bool(im.packed_file),'size':list(im.size)} for im in bpy.data.images if 'atlas' in im.name.lower()]}
assert all(v=='float' for v in q['control_types'].values())
assert all('Baked tissue atlas' in v for v in q['wall_uv_layers'].values())
assert all(im['packed'] for im in q['image_textures'])
s.frame_set(7);q['frame7_ventricular_systole']=float(c['ventricular_systole']);assert 0<q['frame7_ventricular_systole']<1
s.frame_set(1);q['reference_frame']=1
for fn in ['build_heart.py','heart_geometry.py','fix_continuous_controls.py','bake_tissue_atlas.py','post_bake_finalize.py','finalize_and_render.py','render_animation.py','export_details.py','export_meshes.py']:
 tx=bpy.data.texts.get(fn) or bpy.data.texts.new(fn);tx.clear();tx.write(open(R+'/'+fn).read())
json.dump(q,open(R+'/exports/final_native_QA.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=R+'/Cardiac_Atlas.blend')
print('FINAL MODEL QA PASSED',q)
