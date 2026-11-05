"""Reversible editorial FDI31 layer reveal; source mesh coordinates untouched.
Run: blender -b -t 4 -P render_source.py -- --source FDI31-balanced.glb --out renders
"""
import bpy, math, pathlib, argparse, sys, json, hashlib
from mathutils import Vector, Matrix
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser(); p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--test',action='store_true'); a=p.parse_args(args)
out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(pathlib.Path(a.source).resolve()))
objs={o.name.split('/')[-1]:o for o in bpy.context.scene.objects if o.type=='MESH'}
root=bpy.data.objects.new('EDITORIAL_PRESENTATION_ROOT',None);bpy.context.collection.objects.link(root)
# Global display rotation only; no anatomical front/back correspondence asserted.
center=Vector((0.0077,-0.015,0.008))
for name,o in objs.items():
 o.parent=root; o.location=-center
 o.color={'enamel':(0.86,.91,.90,1),'dentin':(.84,.57,.23,1),'pulp':(.84,.19,.37,1),'bone':(.39,.53,.65,1)}[name]
root.scale=(100,100,100);root.rotation_euler=(math.pi/2,0,0)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=640;sc.render.resolution_y=480;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True
sh=sc.display.shading;sh.light='STUDIO';sh.studiolight_rotate_z=.4;sh.color_type='OBJECT';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.2;sh.curvature_valley_factor=.7
sh.show_specular_highlight=True;sh.background_type='WORLD';sc.world.color=(.04,.05,.07);sc.display.render_aa='16'
bpy.ops.object.camera_add(location=(3,-7,2.2));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.05;sc.camera=cam
sc.view_settings.view_transform='Standard';sc.render.fps=8;sc.frame_start=1;sc.frame_end=72
# Fixed camera and source-relative whole-group rotation. Animation offsets reset exactly.
N=1 if a.test else 72
for i in range(N):
 sc.frame_set(i+1)
 t=i/71 if not a.test else .44
 # gentle separation with matched fixed camera; no slicing or implicit tissue removal
 if t<.17: ex=0
 elif t<.4: u=(t-.17)/.23; ex=u*u*(3-2*u)
 elif t<.72: ex=1
 elif t<.92: u=(t-.72)/.2;ex=1-u*u*(3-2*u)
 else: ex=0
 for name,o in objs.items():
  o.location=-center+Vector({'bone':(-.010,0,0),'enamel':(.010,0,0),'dentin':(0,0,0),'pulp':(.0045,0,.005)}[name])*ex
  o.keyframe_insert(data_path="location",frame=i+1)
 root.rotation_euler[2]=.12*math.sin(2*math.pi*t)
 root.keyframe_insert(data_path="rotation_euler",frame=i+1)
 sc.render.filepath=str(out/f'{i:04d}.png');bpy.ops.render.render(write_still=True)
if not a.test:
 sc.frame_set(1)
 for o in objs.values():o.location=-center
 root.rotation_euler[2]=0
 bpy.ops.wm.save_as_mainfile(filepath=str(out.parent/'fdi31-reveal.blend'))
 manifest={'source_sha256':hashlib.sha256(pathlib.Path(a.source).read_bytes()).hexdigest(),'render_engine':'Blender Workbench 4.3','frames':72,'fps':8,'source_meshes':list(objs),'geometry_changes':'none; object transforms for editorial exploded view only','anatomy_status':'not validated; prepared T2 specimen; source labels only','motion_status':'editorial layer displacement, not tissue motion','reset_exact':all((o.location+center).length<1e-10 for o in objs.values())}
 (out.parent/'render-manifest.json').write_text(json.dumps(manifest,indent=2))
