import os
import bpy,json,os
from mathutils import Vector
R=os.path.dirname(os.path.abspath(__file__));qa=json.load(open(R+'/textures/Normal_QA.json'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.resolution_x=s.render.resolution_y=640;s.world.color=(.015,.015,.015)
bpy.ops.mesh.primitive_plane_add(size=2);p=bpy.context.object;p.name='Normal-map diagnostic patch'
x,y=qa['diagnostic_crop_center_pixel'];r=qa['diagnostic_crop_halfwidth'];uv=p.data.uv_layers.active
for loop in uv.data:
 u,v=loop.uv;loop.uv=((x-r+2*r*u)/2048,1-(y+r-2*r*v)/2048)
m=bpy.data.materials.new('Same material; normal strength only changes');m.use_nodes=True;p.data.materials.append(m);nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.28,.32,.36,1);bs.inputs['Roughness'].default_value=.28
im=bpy.data.images.load(R+'/textures/wall_atlas_Normal_OpenGL_2K.png');im.colorspace_settings.name='Non-Color';tx=nodes.new('ShaderNodeTexImage');tx.image=im;nm=nodes.new('ShaderNodeNormalMap');links.new(tx.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
def light(pos,energy,size):
 d=bpy.data.lights.new('Grazing strip','AREA');o=bpy.data.objects.new('Grazing strip',d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();d.energy=energy;d.shape='RECTANGLE';d.size=size;d.size_y=.18
light((-2,-.1,.8),220,1.8);light((2,1,2),20,2)
d=bpy.data.cameras.new('Diagnostic camera');cam=bpy.data.objects.new('Diagnostic camera',d);s.collection.objects.link(cam);cam.location=(0,-2.2,3.4);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=2.6;s.camera=cam
for strength,name in [(0,'normal_off'),(1,'normal_on')]:
 nm.inputs['Strength'].default_value=strength;s.render.filepath=R+'/textures/'+name+'.png';bpy.ops.render.render(write_still=True)
