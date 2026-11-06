"""Reimport exact export; use recorded source-native cameras and extracted lighting.
New renders may differ across Blender/platform versions; no anatomy/runtime certification.
"""
import argparse,hashlib,json,pathlib,sys
import bpy
from mathutils import Matrix,Vector
parser=argparse.ArgumentParser();parser.add_argument('--model',required=True);parser.add_argument('--review',required=True);parser.add_argument('--output',required=True)
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);p=pathlib.Path(a.model);r=pathlib.Path(a.review);out=pathlib.Path(a.output)
if out.exists():raise RuntimeError('Use a new output directory')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='7f9f215f810003fddc76ede225f051dc7014c67216e804403a4632d628ad82aa'
manifest=json.loads((r/'historical-render-manifest.json').read_text());lights=json.loads((r/'lighting-recipe.json').read_text());out.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(p.resolve()));objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==8
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=manifest['samples'];scene.cycles.use_denoising=False;scene.render.resolution_x,scene.render.resolution_y=manifest['resolution'];scene.render.resolution_percentage=100;scene.frame_set(manifest['frame']);scene.render.film_transparent=lights['filmTransparent']
scene.world.color=lights['worldColor'];scene.world.use_nodes=lights['worldNodes']
if lights['worldNodes']:
 b=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');v=lights['worldBackgrounds'][0];b.inputs['Color'].default_value=v['color'];b.inputs['Strength'].default_value=v['strength']
scene.view_settings.view_transform=lights['viewTransform'];scene.view_settings.look=lights['look'];scene.view_settings.exposure=lights['exposure'];scene.view_settings.gamma=lights['gamma']
for l in lights['lights']:
 data=bpy.data.lights.new(l['name'],l['type']);data.energy=l['energy'];data.color=l['color']
 if l['size'] is not None:data.size=l['size']
 obj=bpy.data.objects.new(l['name'],data);scene.collection.objects.link(obj);obj.matrix_world=Matrix(l['matrixWorld'])
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';scene.camera=cam;rows=[]
for v in manifest['views']:
 c=v['camera'];cam.location=c['position'];cam.rotation_euler=(Vector(c['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=c['orthographic_scale'];hidden=v.get('actual_hidden_source_meshes',[])
 assert set(hidden)<={o.name for o in objects}
 for o in objects:o.hide_render=o.name in hidden
 file=out/v['image'];scene.render.filepath=str(file.resolve());bpy.ops.render.render(write_still=True);rows.append({'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'hiddenForInspectionOnly':hidden})
(out/'replay.json').write_text(json.dumps({'artifactSha256':manifest['glb_sha256'],'blender':bpy.app.version_string,'views':rows,'scope':'Exact source camera/visibility recipe execution; not original image byte-equivalence or clinical/runtime approval'},indent=2)+'\n')
print('PLACENTA_REPLAY_COMPLETE',len(rows))
