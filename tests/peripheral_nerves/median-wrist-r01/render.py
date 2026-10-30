"""Clean exact-GLB captures with fixed cameras and source-object-bound locators."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if a.out.exists():raise FileExistsError('New render directory required')
if hashlib.sha256(a.glb.read_bytes()).hexdigest()!=a.sha256:raise ValueError('Wrong GLB')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.glb))
objects={o.get('source_object'):o for o in bpy.context.scene.objects if o.type=='MESH'}
assert len(objects)==33
definitions=[('trunk','Median nerve.r',(-.255,-.026,.877)),
             ('common','Common palmar digital branches of median nerve.r',(-.280,-.040,.808)),
             ('proper','Proper palmar digital branches of median nerve.r',(-.298,-.062,.750)),
             ('scaphoid','Scaphoid bone.r',(-.2756951153278351,-.0252621341496706,.8556894063949585))]
anchors=[]
for key,name,point in definitions:
 o=objects[name];q=Vector(point)
 idx=min(range(len(o.data.vertices)),key=lambda i:(o.matrix_world@o.data.vertices[i].co-q).length)
 anchors.append({'key':key,'sourceObject':name,'vertex':idx,'world':list(o.matrix_world@o.data.vertices[idx].co)})
for key,name,fn in [('proximal','Median nerve.r',max),('distal','Proper palmar digital branches of median nerve.r',min)]:
 o=objects[name];idx=fn(range(len(o.data.vertices)),key=lambda i:(o.matrix_world@o.data.vertices[i].co).z)
 anchors.append({'key':key,'sourceObject':name,'vertex':idx,'world':list(o.matrix_world@o.data.vertices[idx].co)})
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=128;sc.cycles.use_denoising=False
sc.render.threads_mode='FIXED';sc.render.threads=4
sc.render.resolution_x=sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.world=bpy.data.worlds.new('Matched wrist world');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.65,1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=.5
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=0;sc.view_settings.gamma=1
t=Vector((-.26,-.03,.85));lights=[]
for d,e in [((-.5,-.7,.6),70),((.5,-.4,.3),40),((0,.6,.5),45)]:
 bpy.ops.object.light_add(type='AREA',location=t+Vector(d));o=bpy.context.object;o.data.energy=e;o.data.size=.5;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
 lights.append({'location':list(o.location),'energy':e,'size':.5,'rotation':list(o.rotation_euler)})
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam
a.out.mkdir(parents=True);views=[]
for label,target,direction,scale in [('whole-source',(-.23,-.025,1.10),(0,-1,0),.86),('hand-palmar',(-.275,-.045,.80),(0,-1,0),.245),('wrist-oblique',(-.265,-.025,.855),(-.55,-1,.35),.14)]:
 t=Vector(target);cam.location=t+Vector(direction).normalized()*1.5;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 bpy.context.view_layer.update();sc.render.filepath=str(a.out/(label+'.png'));bpy.ops.render.render(write_still=True)
 projected=[]
 for anchor in anchors:
  q=world_to_camera_view(sc,cam,Vector(anchor['world']))
  projected.append({**anchor,'pixel':[q.x*900,(1-q.y)*900],'depth':q.z})
 views.append({'file':label+'.png','sha256':hashlib.sha256((a.out/(label+'.png')).read_bytes()).hexdigest(),'camera':list(cam.location),'target':list(t),'orthoScale':scale,'anchors':projected})
(a.out/'bindings.json').write_text(json.dumps({'artifactSha256':a.sha256,'views':views,'lights':lights,'render':{'engine':'Blender 4.3.2 Cycles CPU','samples':128,'denoising':False,'resolution':[900,900],'viewTransform':'AgX','exposure':0,'gamma':1},'scope':'All selected GLB objects retained and visible; camera crops only. Native source-axis directions. No soft-tissue, tunnel, physical-scale or clinical claim.'},indent=2)+'\n')
