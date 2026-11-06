"""Blender 4.3.2 CPU renders and clean-import checks of the actual GLB variants."""
import argparse
import array
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline', type=Path, required=True)
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--revision', choices=('v1', 'v2'), required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--candidate-only', action='store_true')
parser.add_argument('--audit-only', action='store_true', help='Reimport/material audit without rerendering')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
raw = args.baseline.read_bytes()
expected, record = build.build(raw, args.revision)
build.require(args.candidate.read_bytes() == expected, 'Candidate differs from deterministic build')
doc, _ = build.unpack(raw)
groups = build.membership(doc)
node_group = {name: g['number'] for g in groups for name in g['nodes']}
args.output.mkdir(parents=True, exist_ok=False)


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    start = time.perf_counter()
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
    return objects, time.perf_counter() - start


def signature(obj):
    mesh = obj.data
    digest = hashlib.sha256()
    for collection, prop, count, kind in (
            (mesh.vertices, 'co', 3, 'f'), (mesh.loops, 'vertex_index', 1, 'i'),
            (mesh.polygons, 'loop_total', 1, 'i'), (mesh.corner_normals, 'vector', 3, 'f')):
        values = array.array(kind, [0]) * (len(collection) * count)
        collection.foreach_get(prop, values)
        digest.update(values.tobytes())
    return {'geometryNormalsSha256': digest.hexdigest(), 'vertices': len(mesh.vertices),
            'polygons': len(mesh.polygons), 'worldMatrix': [list(row) for row in obj.matrix_world]}


def material_signature(material):
    def value(socket):
        v = getattr(socket, 'default_value', None)
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return list(v)
    return {
        'nodes': {n.name: {'type': n.type, 'inputs': [(s.identifier, value(s)) for s in n.inputs],
                           'layerName': getattr(n, 'layer_name', None),
                           'operation': getattr(n, 'operation', None),
                           'blendType': getattr(n, 'blend_type', None)}
                  for n in material.node_tree.nodes},
        'links': sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier)
                        for l in material.node_tree.links),
    }


def anchors(scene, camera):
    """Choose deep visible lobe points, then verify the exact image-pixel ray hit."""
    deps = bpy.context.evaluated_depsgraph_get()
    direction = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    size, scale = 64, camera.data.ortho_scale
    mask, names = {}, {}
    def ray(x, y):
        point = Vector(((x / 800 - .5) * scale, (.5 - y / 800) * scale, 0))
        hit = scene.ray_cast(deps, camera.matrix_world @ point, direction)
        return hit[4].name if hit[0] else None
    for y in range(size):
        for x in range(size):
            name = ray((x + .5) * 800 / size, (y + .5) * 800 / size)
            group = node_group.get(name)
            if group:
                mask[x, y] = group
                names[x, y] = name
    result = []
    for group in groups:
        cells = {p for p, g in mask.items() if g == group['number']}
        if len(cells) < 6:
            continue
        deepest = cells
        while True:
            eroded = {p for p in deepest if all((p[0]+dx, p[1]+dy) in deepest
                       for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)))}
            if not eroded:
                break
            deepest = eroded
        cx = sum(p[0] for p in cells) / len(cells)
        cy = sum(p[1] for p in cells) / len(cells)
        p = min(deepest, key=lambda p: ((p[0]-cx)**2 + (p[1]-cy)**2, p))
        pixel = [int((v + .5)*800/size) for v in p]
        name = ray(pixel[0]+.5, pixel[1]+.5)
        build.require(node_group.get(name) == group['number'], 'Anchor hit wrong group')
        result.append({'number': group['number'], 'label': group['label'], 'pixel': pixel,
                       'hitNode': name, 'gridVisibleCells': len(cells)})
    return result


baseline_objects, seconds = load(args.baseline)
signatures = {n: signature(o) for n, o in baseline_objects.items()}
source_materials = {m.name: material_signature(m) for o in baseline_objects.values() for m in o.data.materials}
center = Vector((-.0049615577, .0801189318, .4785911739))
views = [('context', center, Vector((0, -1, 0)), .296339),
         ('reverse', center, Vector((0, 1, 0)), .296339),
         ('right-detail', Vector((-.068, .074, .458)), Vector((-.7, -1, .15)), .155)]
if args.audit_only:
    views = []
variants = [(args.revision, args.candidate)]
if not args.candidate_only:
    variants.insert(0, ('baseline', args.baseline))
rows, imports = [], []
for variant, path in variants:
    objects, seconds = load(path)
    build.require(set(objects) == set(signatures), 'Changed imported mesh inventory')
    build.require({n: signature(o) for n, o in objects.items()} == signatures,
                  'Clean reimport changed geometry/normals/transforms')
    material_doc = doc if variant == 'baseline' else build.unpack(expected)[0]
    for node in material_doc['nodes']:
        if 'mesh' not in node:
            continue
        imported = objects[node['name']].data.materials
        primitives = material_doc['meshes'][node['mesh']]['primitives']
        wanted = [material_doc['materials'][p['material']] for p in primitives]
        build.require(len(imported) == len(wanted), 'Imported material count changed')
        for material, wanted_material in zip(imported, wanted):
            build.require(material.name == wanted_material['name'], 'Imported material name mismatch')
            if material.name in source_materials:
                build.require(material_signature(material) == source_materials[material.name],
                              'Retained source material graph changed')
                continue
            bsdf = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            pbr = wanted_material['pbrMetallicRoughness']
            build.require(not bsdf.inputs['Base Color'].is_linked and not bsdf.inputs['Roughness'].is_linked,
                          'Unexpected linked lobe teaching material')
            build.require(all(abs(a-b) < 1e-6 for a, b in zip(
                bsdf.inputs['Base Color'].default_value, pbr['baseColorFactor'])),
                f'Imported color mismatch: {material.name}: {list(bsdf.inputs["Base Color"].default_value)} vs {pbr["baseColorFactor"]}')
            build.require(abs(bsdf.inputs['Roughness'].default_value-pbr['roughnessFactor']) < 1e-6,
                          'Imported roughness mismatch')
    imports.append({'variant': variant, 'seconds': seconds, 'meshCount': len(objects),
                    'geometryNormalsTransformsExact': True, 'importedMaterialValuesMatch': True,
                    'materials': {n: [m.name for m in o.data.materials] for n, o in objects.items()}})
    scene = bpy.context.scene
    scene.world = bpy.data.worlds.new('ReviewWorld')
    scene.world.color = (.11, .11, .11)
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples = 'CPU', 24
    scene.cycles.use_denoising, scene.cycles.seed = False, 0
    scene.render.resolution_x = scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
    for delta, power in [((-2, -3, 3), 420), ((3, -1, 1), 180), ((0, 3, 2), 280)]:
        bpy.ops.object.light_add(type='AREA', location=center + Vector(delta))
        light = bpy.context.object
        light.data.energy, light.data.size = power, 2
        light.rotation_euler = (center-light.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    scene.camera = camera
    for name, target, direction, scale in views:
        camera.location = target + direction
        camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = scale
        scene.render.filepath = str(args.output / f'{variant}-{name}.png')
        start = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        image = Path(scene.render.filepath)
        rows.append({'variant': variant, 'view': name, 'file': image.name,
                     'sha256': build.sha(image.read_bytes()), 'bytes': image.stat().st_size,
                     'seconds': time.perf_counter()-start, 'cameraLocation': list(camera.location),
                     'target': list(target), 'orthoScaleM': camera.data.ortho_scale,
                     'visibleNodes': sorted(objects), 'anchors': anchors(scene, camera)})
receipt = {'build': record, 'renderer': bpy.app.version_string, 'engine': 'Cycles CPU',
           'samples': 24, 'seed': 0, 'resolution': [800, 800], 'denoising': False,
           'viewTransform': 'AgX', 'look': 'AgX - Medium High Contrast', 'exposure': 0, 'gamma': 1,
           'baselineSignatures': signatures, 'sourceMaterialGraphs': source_materials,
           'imports': imports, 'views': rows,
           'scope': 'Native GLB import and offline render only; no browser or clinical approval.'}
(args.output / 'render.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(f'PASS clean reimports/material checks; {len(rows)} rendered views')
