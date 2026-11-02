import bpy,json,hashlib,struct,sys,time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parent; SRC=R/'source/Network_Systems_Draft.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC))
selected=[o for o in bpy.data.objects if ('lymphatic' in o.name or o.name.startswith('Thoracic duct'))]
skin=next(o for o in bpy.data.objects if o.name=='Continuous translucent whole-body envelope')
def sig(obs):
 return {o.name:{'world_vertices':sorted(set(tuple(round(float(x),6) for x in (o.matrix_world@v.co)) for v in o.data.vertices)),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in obs}
route=next(o for o in selected if o.name.startswith('Thoracic duct')); vs=[route.matrix_world@v.co for v in route.data.vertices]; endpoints={'upper':sum(vs[-8:],Vector())/8,'lower':sum(vs[:8],Vector())/8};
original=sig(selected); body=skin.copy();body.data=skin.data.copy();bpy.context.scene.collection.objects.link(body)
# Isolate the four original pads, preserving coordinates and material.
for o in list(bpy.data.objects):
 if o not in selected and o!=body:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in selected:o.select_set(True)
bpy.context.view_layer.objects.active=selected[0]
bpy.ops.export_scene.gltf(filepath=str(R/'selected-source-routes.glb'),use_selection=True,export_format='GLB',export_extras=True)
for o in selected:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(R/'selected-source-routes.glb'))
selected=[o for o in bpy.data.objects if ('lymphatic' in o.name or o.name.startswith('Thoracic duct'))]
actual=sig(selected); assert original==actual,(original.keys(),actual.keys())
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.seed=152;scene.cycles.use_denoising=False
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
scene.world.color=(.45,.45,.45);scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
for pos,power,size in [((-.6,-1,1),80,1),((.7,-.2,.3),50,1)]:
 d=bpy.data.lights.new('Softbox','AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new('Softbox',d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,-.2))-o.location).to_track_quat('-Z','Y').to_euler()
mat=bpy.data.materials.new('Locator grey');mat.diffuse_color=(.25,.28,.3,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.25,.28,.3,1);bs.inputs['Roughness'].default_value=.8;body.data.materials.clear();body.data.materials.append(mat)
d=bpy.data.cameras.new('Matched orthographic');cam=bpy.data.objects.new('Matched orthographic',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO'
receipt={'source_blend_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'selected_names':list(original),'geometry_preserved_rounded_m':1e-6,'source_signature':original,'views':{},'scope':'Original collecting scaffold preserved. Source-named thoracic duct is schematic; source caps are not verified junctions or lumen. Other tissues omitted. Body outline is editorial only.'}
for view,pos,target,scale,res in [('overview',(0,-4,-.35),(0,0,-.35),1.8,(720,900)),('detail',(.12,-2,.25),(.02,.025,.02),.52,(720,700))]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=scale;scene.render.resolution_x,scene.render.resolution_y=res
 bpy.context.view_layer.update()
 coords={k:list(world_to_camera_view(scene,cam,p)) for k,p in endpoints.items()}
 receipt['views'][view]={'camera':pos,'target':target,'ortho_scale':scale,'pixels':res,'anchors':coords,'matching':'Same reimported route geometry and camera. Original shows all routes; Updated composites a separately rendered selected route over dimmed grayscale scaffold, with editorial body outline and endpoint labels.'}
 body.hide_render=True
 for o in selected:o.hide_render=False
 scene.render.filepath=str(R/f'{view}-pads.png');bpy.ops.render.render(write_still=True)
 for o in selected:o.hide_render=not o.name.startswith('Thoracic duct')
 scene.render.filepath=str(R/f'{view}-route.png');bpy.ops.render.render(write_still=True)
 body.hide_render=False
 for o in selected:o.hide_render=True
 scene.render.filepath=str(R/f'{view}-body.png');bpy.ops.render.render(write_still=True)
(R/'build-receipt.json').write_text(json.dumps(receipt,indent=2))
print('BUILD_OK',R)
