"""Capture the exact exported GLB and bind visible teaching landmarks."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

VIEWS = [('whole-posterior', (-.06, .04, .72), (0, 1, .1), .67),
         ('hip-posterior', (-.06, .045, .90), (0, 1, 0), .27),
         ('hip-oblique', (-.07, .045, .90), (-.9, 1, .25), .29)]
DEFINITIONS = [('nerve', 'Sciatic nerve.r', (-.060, .064, .845)),
               ('ischial', 'Hip bone.r', (-.055, .060, .815)),
               ('trochanter', 'Femur.r', (-.130, .040, .856))]
p = argparse.ArgumentParser()
p.add_argument('--glb', type=Path, required=True)
p.add_argument('--sha256', required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
if a.out.exists():
    raise FileExistsError('New render directory required')
if hashlib.sha256(a.glb.read_bytes()).hexdigest() != a.sha256:
    raise ValueError('Wrong GLB')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.glb))
objects = {o.get('source_object'): o for o in bpy.context.scene.objects if o.type == 'MESH'}
assert set(objects) == {'Sciatic nerve.r', 'Hip bone.r', 'Sacrum', 'Femur.r'}
trees = {}
for name, obj in objects.items():
    obj.data.calc_loop_triangles()
    trees[name] = BVHTree.FromPolygons([obj.matrix_world @ v.co for v in obj.data.vertices],
                                     [tuple(t.vertices) for t in obj.data.loop_triangles], all_triangles=True)

def first_hit(point, direction):
    toward = Vector(direction).normalized()
    hits = []
    for name, tree in trees.items():
        hit, normal, index, distance = tree.ray_cast(point + toward * 2, -toward, 3)
        if hit is not None:
            hits.append((distance, name, (hit - point).length))
    return min(hits) if hits else None

anchors, checks = {}, []
for key, name, guide in DEFINITIONS:
    obj = objects[name]
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    candidates = sorted(range(len(points)), key=lambda i: (points[i] - Vector(guide)).length)
    selected = None
    for index in candidates:
        if (points[index] - Vector(guide)).length > .025:
            break
        hits = [first_hit(points[index], view[2]) for view in VIEWS[1:]]
        if all(h is not None and h[1] == name and h[2] < 1e-5 for h in hits):
            selected = index
            break
    if selected is None:
        raise ValueError('No visible vertex in intended landmark region: ' + key)
    anchors[key] = {'sourceObject': name, 'vertex': selected, 'world': list(points[selected])}
    for view, hit in zip(VIEWS[1:], hits):
        checks.append({'view': view[0], 'anchor': key, 'firstVisibleSourceObject': hit[1],
                       'pointDifference': hit[2], 'passed': True})
obj = objects['Sciatic nerve.r']
for key, fn in [('proximal', max), ('distal', min)]:
    index = fn(range(len(obj.data.vertices)), key=lambda i: (obj.matrix_world @ obj.data.vertices[i].co).z)
    anchors[key] = {'sourceObject': 'Sciatic nerve.r', 'vertex': index,
                    'world': list(obj.matrix_world @ obj.data.vertices[index].co)}

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.cycles.use_denoising = False
scene.cycles.seed = 0
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds.new('Hip study world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.65, .65, .65, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
target = Vector((-.06, .045, .90))
lights = []
for offset, energy in [((-.5, .7, .6), 70), ((.5, .4, .3), 40), ((0, -.6, .5), 45)]:
    bpy.ops.object.light_add(type='AREA', location=target + Vector(offset))
    light = bpy.context.object
    light.data.energy, light.data.size = energy, .5
    light.rotation_euler = (target - light.location).to_track_quat('-Z', 'Y').to_euler()
    lights.append({'location': list(light.location), 'rotation': list(light.rotation_euler),
                   'energy': energy, 'size': .5})
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.type = 'ORTHO'
scene.camera = camera
a.out.mkdir(parents=True)
views = []
for label, target, direction, scale in VIEWS:
    target = Vector(target)
    camera.location = target + Vector(direction).normalized() * 1.5
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = scale
    bpy.context.view_layer.update()
    path = a.out / (label + '.png')
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    pixels = {}
    for key, anchor in anchors.items():
        q = world_to_camera_view(scene, camera, Vector(anchor['world']))
        pixels[key] = [q.x * 900, (1 - q.y) * 900]
    views.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'camera': list(camera.location), 'rotation': list(camera.rotation_euler),
                  'target': list(target), 'scale': scale, 'anchorPixels': pixels})
receipt = {'artifactSha256': a.sha256, 'anchors': anchors, 'visibleLabelChecks': checks,
           'views': views, 'lights': lights,
           'render': {'engine': 'Blender 4.3.2 Cycles CPU', 'samples': 64, 'denoising': False,
                      'resolution': [900, 900], 'viewTransform': 'AgX', 'exposure': 0, 'gamma': 1},
           'scope': 'All four selected surfaces visible; camera crops only. Exact vertex and first-visible '
                    'surface checks support labels, not anatomical or clinical validation.'}
(a.out / 'bindings.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('CAPTURE COMPLETE', json.dumps({'views': len(views), 'visibleLabelChecks': len(checks)}))
