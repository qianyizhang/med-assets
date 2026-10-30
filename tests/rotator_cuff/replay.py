"""Blender 4.3.2: hash-gated native subset, clean reimport and matched renders.

blender -b --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python tests/rotator_cuff/replay.py -- --source Startup.blend --out NEW_DIR
Use --no-render for a geometry-only replay. No upstream code is executed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector, kdtree
from bpy_extras.object_utils import world_to_camera_view

SOURCE_SHA = '9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
SOURCE_COMMIT = 'c08bde5325e35a46404d86a6bd458c484297cc2d'
NAMES = ['Humerus.r', 'Scapula.r', 'Supraspinatus muscle.r',
         'Infraspinatus muscle.r', 'Teres minor muscle.r', 'Subscapularis muscle.r']
COLORS = [(.70, .67, .57), (.70, .67, .57), (.72, .40, .12),
          (.53, .11, .085), (.32, .13, .39), (.09, .38, .36)]
VIEWS = {
    'posterior': ([-.135, .035, 1.355], [0, 1, .12], .27),
    'anterior': ([-.135, .035, 1.355], [0, -1, .1], .27),
    'lateral': ([-.145, .035, 1.355], [-1, .35, .15], .27),
    'overview': ([-.15, .035, 1.23], [0, 1, .08], .55),
}
# Visible surface picks, not anatomical attachments. Ray hits are mandatory.
PICKS = {
    'posterior': [('1', NAMES[2], [350, 345]), ('2', NAMES[3], [360, 500]),
                  ('3', NAMES[4], [578, 476]), ('S', NAMES[1], [350, 375])],
    'anterior': [('4', NAMES[5], [560, 520])],
    'overview': [('S', NAMES[1], [366, 371]), ('H', NAMES[0], [544, 535])],
}
TOLERANCE = 5e-7  # Native units; float32 export/import accounting, not accuracy.


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def surface(obj):
    obj.data.calc_loop_triangles()
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    triangles = [tuple(t.vertices) for t in obj.data.loop_triangles]
    raw = b''.join(struct.pack('<fff', *v.co) for v in obj.data.vertices)
    raw += b''.join(struct.pack('<III', *t) for t in triangles)
    return points, triangles, hashlib.sha256(raw).hexdigest()


def capture(objects, out):
    out.mkdir()
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.cycles.use_denoising = False
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.world = bpy.data.worlds.new('World')
    scene.world.color = (.12, .12, .12)
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    views = []
    for name, (target, direction, scale) in VIEWS.items():
        target = Vector(target)
        camera.location = target + Vector(direction).normalized() * 1.5
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = scale
        for obj in list(bpy.data.objects):
            if obj.type == 'LIGHT':
                bpy.data.objects.remove(obj, do_unlink=True)
        rotation = camera.rotation_euler.to_quaternion()
        for ix, (offset, power, size) in enumerate([
                ((-.5, .6, .8), 70, .65), ((.6, .2, .4), 35, .6),
                ((0, .2, -.5), 45, .5)]):
            light = bpy.data.objects.new('Area'+str(ix), bpy.data.lights.new('Area'+str(ix), 'AREA'))
            bpy.context.collection.objects.link(light)
            light.location = target + rotation @ Vector(offset)
            light.rotation_euler = (target-light.location).to_track_quat('-Z', 'Y').to_euler()
            light.data.energy, light.data.size, light.data.shape = power, size, 'DISK'
        bpy.context.view_layer.update()
        anchors = []
        for key, expected, pixel in PICKS.get(name, []):
            ray = rotation @ Vector((0, 0, -1))
            origin = camera.location + rotation @ Vector(((pixel[0]/900-.5)*scale,
                                                          (.5-pixel[1]/900)*scale, 0))
            hit, point, normal, face, obj, matrix = scene.ray_cast(
                bpy.context.evaluated_depsgraph_get(), origin, ray)
            require(hit and obj.name == expected, f'{name}/{key}: pick hit {obj.name if obj else None}, expected {expected}')
            q = world_to_camera_view(scene, camera, point)
            anchors.append({'id': key, 'object': expected, 'face': face,
                            'world': list(point), 'pixel': [900*q.x, 900*(1-q.y)]})
        scene.render.filepath = str(out / (name+'.png'))
        bpy.ops.render.render(write_still=True)
        views.append({'file': name+'.png', 'sha256': sha(out/(name+'.png')),
                      'anchors': anchors})
    return views


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    require(not bpy.context.preferences.filepaths.use_scripts_auto_execute,
            'Run with --disable-autoexec')
    require(sha(args.source) == SOURCE_SHA, 'Source SHA-256 mismatch')
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(args.source, link=False) as (src, dst):
        require(all(n in src.objects for n in NAMES), 'Missing named surface')
        dst.objects = list(NAMES)
    originals = list(dst.objects)
    for obj in originals:
        bpy.context.collection.objects.link(obj)
        obj.hide_set(False)
        obj.hide_viewport = obj.hide_render = False
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    objects, source_surfaces, rows = {}, {}, []
    for obj, color in zip(originals, COLORS):
        name = obj.name
        require(obj.type == 'MESH' and len(obj.modifiers) == 0, 'Unexpected source surface evaluation')
        require(not obj.constraints and not obj.animation_data, 'Unexpected source animation or constraint')
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(graph), depsgraph=graph)
        copied = bpy.data.objects.new(name+' selected', mesh)
        copied.matrix_world = obj.matrix_world.copy()
        copied['source_object'] = name
        copied['source_sha256'] = SOURCE_SHA
        bpy.context.collection.objects.link(copied)
        material = bpy.data.materials.new(name+' illustrative')
        material.diffuse_color = (*color, 1)
        material.use_nodes = True
        bsdf = material.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Roughness'].default_value = .8
        mesh.materials.clear()
        mesh.materials.append(material)
        points, triangles, digest = surface(copied)
        source_surfaces[name] = (points, triangles)
        edge_uses = Counter(tuple(sorted((f[i], f[(i+1) % 3])))
                            for f in triangles for i in range(3))
        rows.append({'name': name, 'parent': obj.parent.name if obj.parent else None,
                     'vertices': len(points), 'triangles': len(triangles),
                     'localSurfaceSha256': digest, 'nativeMatrix': [list(r) for r in obj.matrix_world],
                     'illustrativeLinearRGB': list(color),
                     'boundaryEdges': sum(n == 1 for n in edge_uses.values()),
                     'nonmanifoldEdges': sum(n > 2 for n in edge_uses.values())})
        objects[name] = copied
    for obj in originals:
        bpy.data.objects.remove(obj, do_unlink=True)
    for name, obj in objects.items():
        obj.name = name
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene['source'] = 'Z-Anatomy / BodyParts3D'
    scene['license'] = 'CC BY-SA 4.0; retain historical BodyParts3D CC BY-SA 2.1 Japan credit'
    scene['scope'] = 'Right cuff muscle surface localization; no attachments, tendon continuity, action or clinical validation'
    bpy.ops.export_scene.gltf(filepath=str(out/'right-rotator-cuff.glb'), export_format='GLB',
                              export_animations=False, export_extras=True, export_cameras=False,
                              export_lights=False)
    inventory = {'sourceCommit': SOURCE_COMMIT, 'sourceSha256': SOURCE_SHA,
                 'sourceArchive': {'url': 'https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/'+SOURCE_COMMIT+'/Z-Anatomy.zip',
                                   'sha256': 'e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736',
                                   'bytes': 86734957, 'member': 'Z-Anatomy/Startup.blend', 'memberBytes': 306838281},
                 'license': {'name': 'CC BY-SA 4.0',
                             'file': 'sources/datasets/z-anatomy/ulnar-elbow/License.txt',
                             'sha256': '196b66b56551a862e59872f7cdb70e6d9a6ad84e9105962fca8ec28c14e97520'},
                 'artifact': {'file': 'right-rotator-cuff.glb', 'sha256': sha(out/'right-rotator-cuff.glb'),
                              'bytes': (out/'right-rotator-cuff.glb').stat().st_size},
                 'objects': rows, 'sourceAxes': 'Native Blender Z-up; glTF maps (x,y,z) to (x,z,-y)',
                 'geometryChanges': 'None; detach selection with effective native matrices; illustrative materials only'}
    write_json(out/'inventory.json', inventory)
    source_views = capture(objects, out/'source') if not args.no_render else []
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(out/'right-rotator-cuff.glb'))
    objects = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
    require(set(objects) == set(NAMES), 'Reimport object set mismatch')
    checks = []
    for name, obj in objects.items():
        expected, faces = source_surfaces[name]
        actual, imported_faces, _ = surface(obj)
        tree = kdtree.KDTree(len(expected))
        for index, point in enumerate(expected):
            tree.insert(point, index)
        tree.balance()
        canonical = [tree.find(p)[1] for p in expected]
        matches = [tree.find(p) for p in actual]
        error = max(m[2] for m in matches)
        require(error <= TOLERANCE, 'Native coordinate mismatch: '+name)
        source_topology = Counter(tuple(sorted(canonical[i] for i in f)) for f in faces)
        export_topology = Counter(tuple(sorted(matches[i][1] for i in f)) for f in imported_faces)
        require(source_topology == export_topology, 'Triangle multiset mismatch: '+name)
        checks.append({'name': name, 'importedVertices': len(actual), 'triangles': len(imported_faces),
                       'maxWorldError': error, 'triangleMultisetMatches': True})
    export_views = capture(objects, out/'export') if not args.no_render else []
    write_json(out/'checks.json', {'artifactSha256': inventory['artifact']['sha256'],
               'toleranceNativeUnits': TOLERANCE, 'scope': 'Exhaustive surface coordinates and triangle multiplicity; no watertightness or anatomy certification',
               'objects': checks, 'sourceViews': source_views, 'exportViews': export_views})
    print('PASS: native source and clean export surface checks; '+inventory['artifact']['sha256'])


if __name__ == '__main__':
    main()
