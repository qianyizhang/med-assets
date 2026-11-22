"""Inspect evaluated motion surfaces and the exact editable assembly cost."""
from collections import Counter
import json
from pathlib import Path
import runpy
import sys
import bpy
from mathutils import Vector

owner = Path('reviews/teaching-assessments/2026-11-22-respiratory')
output = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
output.mkdir(parents=True, exist_ok=False)
helper = runpy.run_path('reviews/teaching-assessments/2026-11-21-form-followup/render.py')
binding = json.loads((owner / 'motion-compare.json').read_text())
model = Path('body/breathing/Breathing_Assembly.blend')
assert helper['identity'](model) == binding['asset']
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()), load_ui=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('Diagnostic world')
scene.world.color = (.1, .1, .1)
scene.view_settings.view_transform = 'AgX'
camera_data = bpy.data.cameras.new('Comparison camera')
camera_data.type = 'ORTHO'
camera_data.clip_start = .001
camera = bpy.data.objects.new('Comparison camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
neutral = bpy.data.materials.new('Neutral diagnostic')
neutral.use_nodes = True
shader = neutral.node_tree.nodes['Principled BSDF']
shader.inputs['Base Color'].default_value = (.44,.39,.34,1)
shader.inputs['Roughness'].default_value = .8
for obj in list(scene.objects):
    if obj.type == 'LIGHT':
        obj.hide_render = True

def components(mesh):
    ids = {}
    vertices = [ids.setdefault(tuple(v.co),len(ids)) for v in mesh.vertices]
    parent = list(range(len(ids)))
    def find(index):
        while index != parent[index]:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index
    for edge in mesh.edges:
        a,b = (vertices[i] for i in edge.vertices)
        parent[find(b)] = find(a)
    return len({find(i) for i in range(len(parent))})

def animation_channels(datablock):
    animation = datablock.animation_data
    if animation is None or animation.action is None or animation.action_slot is None:
        return []
    return [
        dict(path=curve.data_path,index=curve.array_index)
        for layer in animation.action.layers
        for strip in layer.strips
        for bag in strip.channelbags
        if bag.slot_handle == animation.action_slot.handle
        for curve in bag.fcurves
    ]

parts = []
for obj in scene.objects:
    if obj.type != 'MESH':
        continue
    mesh = obj.data
    mesh.calc_loop_triangles()
    parts.append(dict(name=obj.name, connectedComponents=components(mesh),
                      triangles=len(mesh.loop_triangles),
                      trianglesByMaterial=dict(Counter(t.material_index for t in mesh.loop_triangles)),
                      objectChannels=animation_channels(obj),
                      morphChannels=animation_channels(mesh.shape_keys) if mesh.shape_keys else []))

rows = []
for frame in (1,49):
    source = next(v for v in binding['views'] if v['file']==f'motion-{frame}-detail-side-palette.png')
    scene.frame_set(frame)
    target = Vector(source['targetM'])
    direction = Vector(source['cameraM']) - target
    visible = [scene.objects[name] for name in source['visibleNodes']]
    rows.extend(helper['capture'](scene,neutral,output,f'motion-{frame}-detail',visible,target,
                                  source['orthoScaleM'],[('side',direction,('neutral',))]))
(output / 'neutral-motion.json').write_text(json.dumps(dict(asset=binding['asset'],parts=parts,views=rows),indent=2)+'\n')
