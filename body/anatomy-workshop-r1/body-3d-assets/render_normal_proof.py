import bpy,json,math
from pathlib import Path
from mathutils import Vector
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parent;D=R.parent/'body-3d-delivery';path=D/'textures/pancreas_Normal_OpenGL_1K.png';arr=np.array(Image.open(path));best=None
for y in range(0,961,16):
 for x in range(0,961,16):
  a=arr[y:y+64,x:x+64];good=((a[:,:,3]>250)&(a[:,:,2]>245)).mean()
  if good>.995:
   sd=float(a[:,:,:2].std((0,1)).sum())
   if best is None or sd>best[0]:best=(sd,x,y)
if best is None:best=(0,256,256)
_,x,y=best
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=128;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=False;s.cycles.seed=17;s.render.resolution_x=s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[1].default_value=.05
me=bpy.data.meshes.new('Actual baked normal patch');me.from_pydata([(-.05,0,-.05),(.05,0,-.05),(.05,0,.05),(-.05,0,.05)],[],[(0,1,2,3)]);me.update();ob=bpy.data.objects.new('Actual baked normal patch',me);s.collection.objects.link(ob);uv=me.uv_layers.new();coords=[(x/1024,1-(y+64)/1024),((x+64)/1024,1-(y+64)/1024),((x+64)/1024,1-y/1024),(x/1024,1-y/1024)]
for l,co in zip(uv.data,coords):l.uv=co
ma=bpy.data.materials.new('Same grey material; normal strength 0 versus 1');ma.use_nodes=True;ob.data.materials.append(ma);nt=ma.node_tree;p=nt.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.26,.26,.26,1);p.inputs['Roughness'].default_value=.32;im=bpy.data.images.load(str(path));im.colorspace_settings.name='Non-Color';tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tx.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],p.inputs['Normal'])
bpy.ops.object.camera_add(location=(0,-.3,0));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.112;s.camera=cam
bpy.ops.object.light_add(type='AREA',location=(-.14,-.045,.08));li=bpy.context.object;li.data.energy=1.7;li.data.size=.08;li.rotation_euler=(-li.location).to_track_quat('-Z','Y').to_euler()
for strength in [0,1]:nm.inputs['Strength'].default_value=strength;s.render.filepath=str(D/'renders'/f'normal_patch_{strength}.png');bpy.ops.render.render(write_still=True)
a=np.array(Image.open(D/'renders/normal_patch_0.png')).astype(float);b=np.array(Image.open(D/'renders/normal_patch_1.png')).astype(float);q={'asset':'pancreas','source_texture':path.name,'crop_xy_size':[x,y,64],'normal_strengths':[0,1],'same_light_camera_material_seed':True,'mean_absolute_render_pixel_difference':float(abs(a-b).mean()),'max_render_pixel_difference':float(abs(a-b).max()),'interpretation':'Subtle artistic surface relief; not measured tissue microanatomy or displacement.'};json.dump(q,open(D/'docs/NORMAL_ON_OFF_QA.json','w'),indent=2);print('NORMAL PROOF COMPLETE',q)
