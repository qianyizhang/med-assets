"""Clean-reimport source/candidate proof with exact recorded comparison cameras."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser()
p.add_argument('--source',required=True)
p.add_argument('--out',required=True)
p.add_argument('--frame',type=int,default=0)
p.add_argument('--kind',choices=['static','animated'],required=True)
p.add_argument('--views',default='whole-front,seam-front,seam-oblique,seam-neutral,seam-rv-chordae-identity')
p.add_argument('--identity-prefix',default='RV chordae')
p.add_argument('--identity-view',default='seam-rv-chordae-identity')
p.add_argument('--match',type=Path)
p.add_argument('--label',choices=['Original','Updated','Diagnostic'],default='Diagnostic')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
src=Path(a.source); out=Path(a.out)
if out.exists(): raise RuntimeError('Refusing existing diagnostic output')
out.mkdir(parents=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(src))
scene.frame_set(a.frame)
objects=[o for o in scene.objects if o.type=='MESH']
for o in objects:
    if a.kind=='static' and o.get('view_role')=='cutaway': o.hide_render=True
visible=[o for o in objects if not o.hide_render]
coords=[o.matrix_world@v.co for o in visible for v in o.data.vertices]
lo=Vector([min(v[i] for v in coords) for i in range(3)])
hi=Vector([max(v[i] for v in coords) for i in range(3)])
center=(lo+hi)/2; extent=max(hi-lo)
match=json.loads(a.match.read_text()) if a.match else None
if match:
    reference_lo,reference_hi=map(Vector,match['bounds'])
    center=(reference_lo+reference_hi)/2;extent=max(reference_hi-reference_lo)
wall=bpy.data.objects.get('RV | complete wall')
ra=bpy.data.objects.get('RA | complete wall')
def bounds(o):
    pts=[o.matrix_world@v.co for v in o.data.vertices]
    return [Vector([f(v[i] for v in pts) for i in range(3)]) for f in [min,max]]
wl,wh=bounds(wall);rl,rh=bounds(ra)
# Locate the named chamber seam; source-based target, not a fabricated surface.
target=Vector(((rl.x+rh.x+wl.x+wh.x)/4,(rl.y+rh.y+wl.y+wh.y)/4,(wh.z+rl.z)/2))
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48
scene.cycles.use_denoising=False
scene.render.resolution_x=960;scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('Diagnostic world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.075,.09,.11,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
lights=[]
for direction,power in [((-.6,-.7,.8),14),((.5,-.3,.1),7),((0,.5,.5),10)]:
    bpy.ops.object.light_add(type='AREA',location=center+Vector(direction)*extent*4)
    o=bpy.context.object;o.data.energy=power*(extent*4)**2;o.data.shape='DISK';o.data.size=extent*2
    o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    lights.append({'location':list(o.location),'energy':o.data.energy,'size':o.data.size})
if match:
    for o,values in zip([o for o in scene.objects if o.type=='LIGHT'],match['lights']):
        o.location=values['location'];o.data.energy=values['energy'];o.data.size=values['size']
        o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    lights=match['lights']
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';scene.camera=cam
cam.data.clip_start=extent*.001;cam.data.clip_end=extent*100
views=[]
def render(name,t,scale,direction=(0,-1,0)):
    if name not in a.views.split(','): return
    cam.location=t+Vector(direction).normalized()*extent*4
    cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=scale;scene.render.filepath=str(out/(name+'.png'))
    if match:
        reference=next(v for v in match['views'] if v.get('view',Path(v['file']).stem)==name)
        cam.location=reference['camera'];cam.rotation_euler=reference['rotation'];cam.data.ortho_scale=reference['orthoScale']
        t=Vector(reference['target']);scale=reference['orthoScale']
    bpy.ops.render.render(write_still=True)
    views.append({'view':name,'file':name+'.png','sha256':hashlib.sha256((out/(name+'.png')).read_bytes()).hexdigest(),'camera':list(cam.location),'rotation':list(cam.rotation_euler),'target':list(t),'orthoScale':scale})
render('whole-front',center,extent*1.12)
render('seam-front',target,extent*.40)
render('seam-oblique',target,extent*.40,(.45,-1,.08))
neutral=bpy.data.materials.new('Diagnostic neutral override');neutral.use_nodes=True
bs=neutral.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.6,.6,.6,1);bs.inputs['Roughness'].default_value=.6
scene.view_layers[0].material_override=neutral
render('seam-neutral',target,extent*.40)
scene.view_layers[0].material_override=None
saved={o.name:list(o.data.materials) for o in visible}
for o in visible:
    o.data.materials.clear();o.data.materials.append(neutral)
highlight=bpy.data.materials.new('Diagnostic named-object identity only');highlight.use_nodes=True
bs=highlight.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(1,.05,.02,1);bs.inputs['Roughness'].default_value=.5
highlighted=[]
for o in visible:
    if o.name.startswith(a.identity_prefix):
        o.data.materials.clear();o.data.materials.append(highlight);highlighted.append(o.name)
render(a.identity_view,target,extent*.40)
report={'kind':'exact-export-clean-reimport-proof','label':a.label,'source':src.name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'rendererRecipeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'matchedBindingSha256':hashlib.sha256(a.match.read_bytes()).hexdigest() if a.match else None,'frame':a.frame,'fps':scene.render.fps,'visibleMeshes':len(visible),'hiddenCutawayMeshes':[o.name for o in objects if o.hide_render],'highlightedIdentityOnly':highlighted,'bounds':[list(lo),list(hi)],'lights':lights,'samples':scene.cycles.samples,'views':views,'limitations':['diagnostic override is not material or anatomy improvement','source visibility restoration is not an RV inlet geometry repair','no clinical or runtime approval']}
(out/'bindings.json').write_text(json.dumps(report,indent=2)+'\n')
