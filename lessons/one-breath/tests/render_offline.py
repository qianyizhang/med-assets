"""Render the exact shared Three scene snapshots in Blender; not browser/WebGL evidence."""
import argparse,json,sys,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
def conv(x):return (x[0],-x[2],x[1])
for source in sorted(a.input.glob('*.json')):
 if source.name=='states.json':continue
 doc=json.loads(source.read_text())
 if 'meshes' not in doc:continue
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for item in doc['meshes']:
  vertices=[conv(item['vertices'][i:i+3]) for i in range(0,len(item['vertices']),3)];faces=[item['indices'][i:i+3] for i in range(0,len(item['indices']),3)]
  mesh=bpy.data.meshes.new(item['name']);mesh.from_pydata(vertices,[],faces);mesh.update();ob=bpy.data.objects.new(item['name'],mesh);bpy.context.collection.objects.link(ob)
  for color in item['materials']:
   m=bpy.data.materials.new(item['name']);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color['color'],1);bs.inputs['Roughness'].default_value=.85;bs.inputs['Alpha'].default_value=color['opacity'];mesh.materials.append(m)
  for face in mesh.polygons:face.use_smooth=True
  for group in item.get('groups',[]):
   for face in mesh.polygons[group['start']//3:(group['start']+group['count'])//3]:face.material_index=group['materialIndex']
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.resolution_x=1100;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.film_transparent=True;s.world.color=(.23,.28,.29);s.view_settings.view_transform='AgX'
 target=Vector(conv(doc['camera']['target']))
 for pos,energy,size in [((.4,.7,.8),45,.5),((-.4,.2,.5),22,.5),((0,.25,-.5),22,.4)]:
  bpy.ops.object.light_add(type='AREA',location=conv(pos));lamp=bpy.context.object;lamp.data.energy=energy;lamp.data.size=size;lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add(location=conv(doc['camera']['position']));cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=doc['camera']['height']*1100/720;s.camera=cam
 output=source.with_suffix('.png');s.render.filepath=str(output);bpy.ops.render.render(write_still=True)
 record={'image':output.name,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'snapshot':source.name,'snapshot_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'assets':doc['assetIdentities'],'state':doc['state'],'camera':doc['camera'],'scope':'Actual offline Blender render of shared Three.js snapshot geometry/morph state. Not browser screenshot or WebGL acceptance.'}
 output.with_suffix('.binding.json').write_text(json.dumps(record,indent=2)+'\n')
