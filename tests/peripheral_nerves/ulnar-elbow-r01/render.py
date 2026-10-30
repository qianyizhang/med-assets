"""Matched exact-GLB reimports, recorded cameras and source-vertex locators."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

p=argparse.ArgumentParser();p.add_argument('--glb',required=True);p.add_argument('--sha256',required=True);p.add_argument('--out',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);G=Path(a.glb);O=Path(a.out)
assert hashlib.sha256(G.read_bytes()).hexdigest()==a.sha256, 'Wrong GLB'
O.mkdir(parents=True,exist_ok=False)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(G))
objects={o.get('source_object'):o for o in bpy.context.scene.objects if o.type=='MESH'}
assert set(objects)=={'Ulnar nerve.r','Humerus.r','Ulna.r','Radius.r'}
# Source .j graphical landmark endpoints identify regions; nearest retained mesh
# vertices bind editorial locators. These are not newly reconstructed landmarks.
definitions=[
 ('nerve','Ulnar nerve.r',(-.196,.043,1.12),'Named source nerve; elbow-region point'),
 ('medial_epicondyle','Humerus.r',(-.184041053,.036097266,1.108540416),'Medial epicondyle of humerus.j source graphical endpoint'),
 ('olecranon','Ulna.r',(-.214689255,.055331923,1.105144143),'Olecranon.j source graphical endpoint')]
anchors=[]
for key,name,ref,semantic in definitions:
    o=objects[name];ref=Vector(ref)
    idx=min(range(len(o.data.vertices)),key=lambda i:(o.matrix_world@o.data.vertices[i].co-ref).length)
    point=o.matrix_world@o.data.vertices[idx].co
    anchors.append({'key':key,'source_object':name,'vertex':idx,'world':list(point),'source_reference':list(ref),'reference_distance':(point-ref).length,'semantic_source':semantic})
nerve=objects['Ulnar nerve.r']
for key,fn in [('proximal_extent',max),('distal_extent',min)]:
    idx=fn(range(len(nerve.data.vertices)),key=lambda i:(nerve.matrix_world@nerve.data.vertices[i].co).z)
    anchors.append({'key':key,'source_object':'Ulnar nerve.r','vertex':idx,'world':list(nerve.matrix_world@nerve.data.vertices[idx].co),'semantic_source':'Source curve visible extent; not anatomical origin or terminal branch'})
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=128;sc.cycles.use_denoising=False
sc.render.threads_mode='FIXED';sc.render.threads=4
sc.render.resolution_x=sc.render.resolution_y=800;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.world=bpy.data.worlds.new('Matched world');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.7,.7,1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=.5
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=0;sc.view_settings.gamma=1
target=Vector((-.20,.025,1.12));lights=[]
for delta,energy in [((.5,.7,.6),80),((-.5,.3,.3),45),((0,-.6,.6),55)]:
    bpy.ops.object.light_add(type='AREA',location=target+Vector(delta));l=bpy.context.object
    l.data.energy=energy;l.data.size=.5;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
    lights.append({'location':list(l.location),'energy':energy,'size':.5,'rotation_euler':list(l.rotation_euler)})
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam
views=[]
for label,t,d,scale in [
 ('whole-posterior',(-.195,.02,1.13),(0,1,0),.66),
 ('elbow-posterior',(-.217,.035,1.105),(0,1,0),.16),
 ('elbow-posteromedial',(-.217,.035,1.105),(1,1,0),.16),
 ('elbow-medial',(-.217,.035,1.105),(1,0,0),.16)]:
    t=Vector(t);cam.location=t+Vector(d).normalized()*1.5
    cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    bpy.context.view_layer.update();sc.render.filepath=str(O/(label+'.png'));bpy.ops.render.render(write_still=True)
    projected=[]
    for anchor in anchors:
        q=world_to_camera_view(sc,cam,Vector(anchor['world']))
        projected.append({**anchor,'pixel':[q.x*800,(1-q.y)*800],'depth':q.z})
    views.append({'file':label+'.png','sha256':hashlib.sha256((O/(label+'.png')).read_bytes()).hexdigest(),
                  'artifactSha256':a.sha256,'camera':list(cam.location),'target':list(t),'ortho_scale':scale,'anchors':projected})
(O/'bindings.json').write_text(json.dumps({'artifactSha256':a.sha256,'views':views,'lights':lights,
 'render':{'engine':'Blender 4.3.2 Cycles CPU','samples':128,'denoising':False,'resolution':[800,800],'projection':'orthographic','view_transform':'AgX','exposure':0,'gamma':1,'frame':1},
 'scope':'Exact GLB reimport. Same cameras/lights/scale/sampling for v1 and v2; intentional material and metadata changes only. Source-axis labels; no patient or physical-scale validation.'},indent=2)+'\n')
