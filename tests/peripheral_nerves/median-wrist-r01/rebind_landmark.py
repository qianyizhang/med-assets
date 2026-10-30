"""Correct the occluded scaphoid leader while reusing unchanged render bytes."""
import argparse,copy,hashlib,json,shutil,sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--captures',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if a.out.exists():raise FileExistsError('New binding/capture directory required')
assert hashlib.sha256(a.glb.read_bytes()).hexdigest()=='6094265d2263f3b501f4e487ff7f859b83205bde99bca9312d48c26f29680c50'
path=a.captures/'bindings.json';assert hashlib.sha256(path.read_bytes()).hexdigest()=='e39564585b530e682dd6e36e4236479930452befa1b8620bc6c06027420ce26f'
b=json.loads(path.read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(a.glb))
o=next(o for o in bpy.context.scene.objects if o.get('source_object')=='Scaphoid bone.r')
point=o.matrix_world@o.data.vertices[47].co
assert (point-Vector((-.2756951153278351,-.0252621341496706,.8556894063949585))).length<1e-7
sc=bpy.context.scene;sc.render.resolution_x=sc.render.resolution_y=900;sc.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam
a.out.mkdir(parents=True)
for v in b['views']:
 source=a.captures/v['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==v['sha256']
 shutil.copyfile(source,a.out/v['file'])
 cam.location=Vector(v['camera']);t=Vector(v['target']);cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=v['orthoScale'];bpy.context.view_layer.update()
 q=world_to_camera_view(sc,cam,point)
 anchor=next(x for x in v['anchors'] if x['key']=='scaphoid')
 anchor.update({'vertex':47,'world':list(point),'pixel':[q.x*900,(1-q.y)*900],'depth':q.z})
b['annotationRevision']='V2: scaphoid vertex 47 is visible in both labelled views. Prior anchor was hidden by trapezium; no anatomy/camera/raw-pixel change.'
b['captureReuse']={'from':'v1/renders','bindingsSha256':'e39564585b530e682dd6e36e4236479930452befa1b8620bc6c06027420ce26f','rawImageBytesUnchanged':True}
(a.out/'bindings.json').write_text(json.dumps(b,indent=2)+'\n')
