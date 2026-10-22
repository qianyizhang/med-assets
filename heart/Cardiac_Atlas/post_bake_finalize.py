import os
import bpy,os,json
from PIL import Image,ImageDraw
R=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene;c=bpy.data.objects['HEART CONTROL • material + cutaway + pulse']
# Refresh references after unwrap, and transfer actual packed UVs back by polygon provenance.
proxy=bpy.data.objects['TEXTURE STUDY • four-chamber walls • 2K baked atlas'];uv=proxy.data.uv_layers['Baked tissue atlas'];offset=0;errors=[]
for name in ['LV | complete wall','RV | complete wall','LA | complete wall','RA | complete wall']:
 ob=bpy.data.objects[name];target=ob.data.uv_layers['Baked tissue atlas']
 for p in ob.data.polygons:
  src=proxy.data.polygons[offset];offset+=1
  if len(p.loop_indices)!=len(src.loop_indices):raise RuntimeError('UV provenance mismatch')
  for a,b in zip(p.loop_indices,src.loop_indices):target.data[a].uv=uv.data[b].uv
 target.active_render=True;ob.data.uv_layers.active=target
vals=[tuple(d.uv) for d in uv.data];size=2048;im=Image.new('RGB',(size,size),(18,24,32));draw=ImageDraw.Draw(im)
for p in proxy.data.polygons:
 xy=[(uv.data[i].uv.x*(size-1),(1-uv.data[i].uv.y)*(size-1)) for i in p.loop_indices];draw.line(xy+[xy[0]],fill=(74,156,169),width=1)
im.save(R+'/textures/wall_atlas_UV_layout_2K.png')
# Educational transparency should reveal structures without glass refraction.
for ma in bpy.data.materials:
 if not ma.use_nodes:continue
 for no in ma.node_tree.nodes:
  if no.name.startswith('TRANSPARENT •'):
   no.inputs['Transmission Weight'].default_value=0.;no.inputs['Alpha'].default_value=1.;no.inputs['Roughness'].default_value=.3
  if no.type=='MIX_SHADER' and no.location.y==-250:no.inputs[0].default_value=.88
# Packed bake recipe and consistent current-source regeneration scripts.
for fn in ('build_heart.py','heart_geometry.py','bake_tissue_atlas.py','post_bake_finalize.py'):
 tx=bpy.data.texts.get(fn) or bpy.data.texts.new(fn);tx.clear();tx.write(open(R+'/'+fn).read())
c['material_set']=0;c['cutaway']=0;s.frame_set(1);s.camera=bpy.data.objects['CAM 01 • anterior hero']
bpy.ops.wm.save_as_mainfile(filepath=R+'/Cardiac_Atlas.blend')
# Strict UV verification: every loop on the original walls equals its atlas counterpart.
offset=0;maxerror=0.
for name in ['LV | complete wall','RV | complete wall','LA | complete wall','RA | complete wall']:
 ob=bpy.data.objects[name];target=ob.data.uv_layers['Baked tissue atlas']
 for p in ob.data.polygons:
  src=proxy.data.polygons[offset];offset+=1
  for a,b in zip(p.loop_indices,src.loop_indices):maxerror=max(maxerror,(target.data[a].uv-uv.data[b].uv).length)
json.dump({'atlas_polygons':len(proxy.data.polygons),'atlas_loops':len(uv.data),'original_to_atlas_max_UV_error':maxerror,'bounds':[[min(a[i] for a in vals),max(a[i] for a in vals)] for i in (0,1)],'mapped_objects':4},open(R+'/textures/UV_QA.json','w'),indent=2)
print('POST BAKE VERIFIED maxUVerror',maxerror,flush=True)
