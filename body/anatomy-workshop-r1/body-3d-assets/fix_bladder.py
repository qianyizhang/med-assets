exec(open(__file__.replace('fix_bladder.py','refine_and_preview.py')).read().split('for ma in bpy.data.materials:')[0])
sources={o['source_file'][:-5]:o for o in bpy.data.objects if 'source_file' in o and o.get('view_role')=='surface'}
for o in list(objects['bladder']):
 if o.get('anatomy_id')!='bladder_surface':objects['bladder'].remove(o);bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update();ob=objects['bladder'][0];cp,plane,c,dim=section_shell(ob,'bladder',shrink=.90);cp['derivation']='Fully authored schematic bladder wall and section';cp['cutaway_note']='Schematic bladder wall and trigone; not derived from a segmented bladder'
for p in cp.data.polygons:p.use_smooth=abs(p.normal.y)<.97
bpy.context.view_layer.objects.active=cp;mod=cp.modifiers.new('Rounded section rim','BEVEL');mod.width=.0006;mod.segments=3;mod.limit_method='ANGLE';mod.angle_limit=.55;bpy.ops.object.modifier_apply(modifier=mod.name)
collect=bpy.data.materials['Renal collecting system'];tri=[(c.x-.012,plane+.003,c.z-.006),(c.x+.012,plane+.003,c.z-.006),(c.x,plane+.003,c.z-.027)]
mesh('Bladder trigone · schematic',tri,[(0,1,2)],'bladder','bladder_trigone','detail','schematic',bpy.data.materials['Gastric mucosa and rugae'])
for id in ['kidney_left','kidney_right']:
 _,_,kc,kd=bounds(sources[id]);side=1 if id.endswith('left') else -1;start=kc+Vector((-side*kd.x*.27,0,-.004));end=Vector((side*.012,plane+.008,c.z-.006));tube(id+' ureter to bladder',[start,start+Vector((-side*.010,0,-.055)),Vector((side*.026,.005,-.210)),end],.0022,'bladder',id+'_ureter',collect,'surface',radii=[1,.85,.75,.7])
tube('Single urethral outlet · schematic',[c+Vector((0,0,-.034)),c+Vector((0,.003,-.055))],.003,'bladder','urethral_outlet',bpy.data.materials['Pale fibrous tissue'],'surface')
for o in objects['bladder']:
 if len(o.data.materials) and 'clinical_color' in o.data.materials[0]:o['clinical_color']=o.data.materials[0]['clinical_color']
json.dump({id:[o.name for o in obs] for id,obs in objects.items()},open(R/'object_map.json','w'),indent=2)
# Rebuild every bake once with a sole UV layer; remove superseded image/material payload.
for ma in list(bpy.data.materials):
 if 'baked portable PBR' in ma.name:bpy.data.materials.remove(ma,do_unlink=True)
for im in list(bpy.data.images):
 if ' 1K' in im.name:bpy.data.images.remove(im,do_unlink=True)
ctrl['cutaway']=0;ctrl['material_mode']=0;bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop.blend'),compress=True)
print('BLADDER POSITION FIX',list(c),flush=True)
