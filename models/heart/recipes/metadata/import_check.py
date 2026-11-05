"""Native Blender import/state comparison, without rendering or saving a scene."""
from array import array
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import SOURCE, TARGET, decode, require


def plain(value):
    if hasattr(value, 'to_dict'):
        return {key: plain(item) for key, item in value.to_dict().items()}
    if hasattr(value, 'to_list'):
        return value.to_list()
    return value


def digest(values):
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def imported(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    require(bpy.ops.import_scene.gltf(filepath=str(path)) == {'FINISHED'}, 'GLB import failed')
    document, _ = decode(path.read_bytes())
    expected = document['scenes'][0]['extras']
    actual = {key: plain(value) for key, value in bpy.context.scene.items()}
    require(actual == expected, 'Importer scene metadata differs')
    objects = sorted(bpy.context.scene.objects, key=lambda obj: obj.name)
    require(len(objects) == 1 and objects[0].type == 'MESH', 'Unexpected imported objects')
    obj = objects[0]
    require({key: plain(value) for key, value in obj.items()} == document['nodes'][0]['extras'],
            'Importer node provenance differs')
    mesh = obj.data
    coordinates = array('f', [0]) * (len(mesh.vertices)*3)
    mesh.vertices.foreach_get('co', coordinates)
    mesh.calc_loop_triangles()
    indices = array('i', [0]) * (len(mesh.loop_triangles)*3)
    mesh.loop_triangles.foreach_get('vertices', indices)
    actions = []
    for action in bpy.data.actions:
        curves = [(curve.data_path, curve.array_index,
                   [(list(key.co), key.interpolation) for key in curve.keyframe_points])
                  for curve in action.fcurves]
        actions.append({'name': action.name, 'curves': curves})
    require(len(actions) == 1 and len(actions[0]['curves']) == 3
            and all(path == 'location' and len(keys) == 81 for path, _, keys in actions[0]['curves']),
            'Expected imported translation curves')
    matrices = []
    for index in range(81):
        frame = index*1.5  # 0..4 seconds at 30 fps; no physiological phase assignment.
        bpy.context.scene.frame_set(math.floor(frame), subframe=frame % 1)
        matrices.append([value for row in obj.matrix_world for value in row])
    require(matrices[0] != matrices[32], 'Imported animation did not move the surface')
    return {
        'meshVertices': len(mesh.vertices), 'triangles': len(mesh.loop_triangles),
        'positionSha256': hashlib.sha256(coordinates.tobytes()).hexdigest(),
        'triangleIndexSha256': hashlib.sha256(indices.tobytes()).hexdigest(),
        'nodeExtras': document['nodes'][0]['extras'],
        'materials': sorted(material.name for material in bpy.data.materials),
        'embeddedImages': sorted((image.name, list(image.size)) for image in bpy.data.images),
        'actionsSha256': digest(actions), 'sampleMatricesSha256': digest(matrices),
    }


if __name__ == '__main__':
    baseline, corrected = imported(SOURCE), imported(TARGET)
    require(baseline == corrected, 'Native imported data/state changed')
    report = {
        'blender': bpy.app.version_string, 'sourceAndTargetImportPassed': True,
        'sceneExtrasMatchEachGLB': True, 'nodeProvenanceUnchanged': True,
        'meshVertices': corrected['meshVertices'], 'triangles': corrected['triangles'],
        'positionSha256': corrected['positionSha256'],
        'triangleIndexSha256': corrected['triangleIndexSha256'],
        'animationCurvesSha256': corrected['actionsSha256'],
        'worldMatricesAt81TimesSha256': corrected['sampleMatricesSha256'],
        'materialsAndImageInventoryUnchanged': True,
        'scope': 'Native import and sampled state only; no render, browser, physiology or clinical approval',
    }
    print('HEART_IMPORT_RESULT '+json.dumps(report, sort_keys=True))
