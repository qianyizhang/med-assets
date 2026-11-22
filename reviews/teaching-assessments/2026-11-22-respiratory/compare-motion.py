import bpy
import json
import runpy
import sys
from pathlib import Path
from mathutils import Vector
root=Path.cwd()
out=Path(sys.argv[sys.argv.index('--') + 1]).resolve()
out.mkdir(parents=True, exist_ok=False)
owner='reviews/teaching-assessments/2026-11-21-form-followup/render.py'
base=runpy.run_path(owner)
assembly=root/'body/breathing/Breathing_Assembly.blend'
expected = 'fc68b49ca75d02d50330e9d5b5d5182843e6d0e7ca4d43d665cbde48ac23b841'
if base['identity'](assembly)['sha256'] != expected:
    raise ValueError('The exact reviewed Breathing assembly is required')
bpy.ops.wm.open_mainfile(filepath=str(assembly),load_ui=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('Diagnostic world')
scene.world.color=(.1,.1,.1)
scene.view_settings.view_transform='AgX'
camera_data=bpy.data.cameras.new('Comparison camera')
camera_data.type='ORTHO'
camera=bpy.data.objects.new('Comparison camera',camera_data)
scene.collection.objects.link(camera)
scene.camera=camera
camera.data.clip_start=.001
for o in list(scene.objects):
    if o.type=='LIGHT':
        o.hide_render=True
targets=[o for o in scene.objects if o.type=='MESH' and (o.name.startswith('Lung ') or o.name in ('Authored schematic diaphragm','Liver | source surface'))]
rows=[]
for frame in (1,49):
    scene.frame_set(frame)
    for name, target, scale in [('whole',Vector((0,0,.005)),.46),('detail',Vector((0,0,-.06)),.32)]:
        for variant,direction in [('anterior',(0,-1,.04)),('side',(1,-.22,.03))]:
            rows+=base['capture'](scene,None,out,f'motion-{frame}-{name}',targets,target,scale,[(variant,direction,('palette',))])
(out/'motion-compare.json').write_text(json.dumps({'asset':base['identity'](assembly),'targetSelection':'five lung lobes, diaphragm, liver; all other meshes hidden for both views','views':rows},indent=2))
