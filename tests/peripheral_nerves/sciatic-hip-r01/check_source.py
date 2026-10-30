"""Check stored GLB surfaces separately from Blender's known import omissions."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils.kdtree import KDTree

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sciatic_build', HERE / 'build.py')
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)
EXPECTED_IMPORT_DROP = {'Sacrum': Counter({(2712, 2713, 2771): 1})}

def snapshot(obj, graph):
    evaluated = obj.evaluated_get(graph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=graph)
    mesh.calc_loop_triangles()
    result = ([evaluated.matrix_world @ v.co for v in mesh.vertices],
              [tuple(t.vertices) for t in mesh.loop_triangles], evaluated.matrix_world.copy())
    bpy.data.meshes.remove(mesh)
    return result

def tree(points):
    result = KDTree(len(points))
    for i, point in enumerate(points):
        result.insert(point, i)
    result.balance()
    return result

def decode_glb(path):
    data = path.read_bytes()
    assert struct.unpack_from('<4sII', data) == (b'glTF', 2, len(data))
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4e4f534a
    doc = json.loads(data[20:20+size])
    binary_size, binary_kind = struct.unpack_from('<II', data, 20+size)
    assert binary_kind == 0x004e4942
    binary = data[28+size:28+size+binary_size]
    def accessor(index):
        item = doc['accessors'][index]
        view = doc['bufferViews'][item['bufferView']]
        assert 'sparse' not in item and view.get('buffer', 0) == 0
        count = {'SCALAR': 1, 'VEC3': 3}[item['type']]
        fmt = '<' + {5123: 'H', 5125: 'I', 5126: 'f'}[item['componentType']] * count
        offset = view.get('byteOffset', 0) + item.get('byteOffset', 0)
        stride = view.get('byteStride', struct.calcsize(fmt))
        return [struct.unpack_from(fmt, binary, offset+i*stride) for i in range(item['count'])]
    conversion = Matrix(((1,0,0,0), (0,0,-1,0), (0,1,0,0), (0,0,0,1)))
    result = {}
    assert len(doc['nodes']) == 4
    for node in doc['nodes']:
        assert not node.get('children')
        name = node['extras']['source_object']
        if 'matrix' in node:
            transform = Matrix([node['matrix'][i::4] for i in range(4)])
        else:
            rotation = node.get('rotation', [0,0,0,1])
            transform = Matrix.LocRotScale(Vector(node.get('translation', [0,0,0])),
                Quaternion((rotation[3], *rotation[:3])), Vector(node.get('scale', [1,1,1])))
        points, triangles = [], []
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            assert primitive.get('mode', 4) == 4
            offset = len(points)
            points.extend(conversion @ transform @ Vector(p) for p in accessor(primitive['attributes']['POSITION']))
            indices = [row[0] + offset for row in accessor(primitive['indices'])]
            assert len(indices) % 3 == 0
            triangles.extend(tuple(indices[i:i+3]) for i in range(0, len(indices), 3))
        result[name] = (points, triangles, conversion @ transform @ conversion.inverted())
    return result

def compare(source, candidate):
    source_points, source_triangles, source_matrix = source
    points, triangles, matrix = candidate
    used = {i for triangle in source_triangles for i in triangle}
    source_tree, candidate_tree = tree(source_points), tree(points)
    nearest = [source_tree.find(v) for v in points]
    worst = max([v[2] for v in nearest] +
                [candidate_tree.find(source_points[i])[2] for i in used])
    canonical = {}
    for i, value in enumerate(source_points):
        canonical.setdefault(tuple(value), i)
    source_ids = [canonical[tuple(v)] for v in source_points]
    candidate_ids = [source_ids[v[1]] for v in nearest]
    expected = Counter(tuple(sorted(source_ids[i] for i in t)) for t in source_triangles)
    actual = Counter(tuple(sorted(candidate_ids[i] for i in t)) for t in triangles)
    matrix_error = max(abs(source_matrix[i][j]-matrix[i][j]) for i in range(4) for j in range(4))
    assert worst < 1e-6 and matrix_error < 1e-6, (worst, matrix_error)
    return worst, matrix_error, expected-actual, actual-expected, len(source_points)-len(used)

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--glb', type=Path, required=True)
parser.add_argument('--sha256', required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
if args.out.exists():
    raise FileExistsError('Receipt must be new')
assert hashlib.sha256(args.source.read_bytes()).hexdigest() == recipe.SOURCE_SHA
assert hashlib.sha256(args.glb.read_bytes()).hexdigest() == args.sha256
stored = decode_glb(args.glb)
assert set(stored) == set(recipe.NAMES)
bpy.ops.wm.open_mainfile(filepath=str(args.source), load_ui=False, use_scripts=False)
graph = bpy.context.evaluated_depsgraph_get()
native = {name: snapshot(bpy.data.objects[name], graph) for name in recipe.NAMES}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(args.glb))
objects = {o.get('source_object'): o for o in bpy.context.scene.objects if o.type == 'MESH'}
assert set(objects) == set(recipe.NAMES)
graph = bpy.context.evaluated_depsgraph_get()
rows = []
for name in recipe.NAMES:
    raw = compare(native[name], stored[name])
    assert not raw[2] and not raw[3], (name, 'stored GLB surface mismatch')
    reimport = snapshot(objects[name], graph)
    imported = compare(native[name], reimport)
    assert imported[2] == EXPECTED_IMPORT_DROP.get(name, Counter()) and not imported[3], (name, 'unexpected import difference')
    assert raw[4] == (21 if name == 'Sacrum' else 0), (name, 'unexpected unused source vertices')
    rows.append({'sourceObject': name, 'sourceVertices': len(native[name][0]),
                 'unusedSourceVerticesOmitted': raw[4], 'storedGLBVertices': len(stored[name][0]),
                 'storedGLBTriangles': len(stored[name][1]), 'reimportTriangles': len(reimport[1]),
                 'storedSurfaceTrianglesMatch': True, 'maxStoredVertexDifference': raw[0],
                 'maxReimportVertexDifference': imported[0], 'maxEffectiveMatrixDifference': max(raw[1], imported[1]),
                 'knownImporterOmission': [list(t) for t in imported[2]]})
receipt = {'sourceSha256': recipe.SOURCE_SHA, 'artifactSha256': args.sha256,
           'result': 'passed-with-explicit-import-limits', 'objects': rows,
           'numericalTolerance': 1e-6,
           'scope': 'All four stored GLB surface vertex clouds/triangles and effective matrices checked. '
                    'Exact source-coincident seam vertices mapped for triangle comparison. Float32 tolerance only.',
           'importBoundary': 'GLB omits 21 unused Sacrum vertices. Raw GLB retains all 24154 source surface triangles. '
                             'Blender 4.3.2 reimport omits only source Sacrum triangle (2712,2713,2771), '
                             'a narrow face with native double-area 1.942817136463481e-8. No artifact repair or route change.',
           'limitations': 'No anatomical, piriformis-clearance, clinical, physical-scale or browser-runtime validation.'}
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({'result': receipt['result'], 'objects': len(rows),
                  'storedTriangles': sum(r['storedGLBTriangles'] for r in rows),
                  'reimportTriangles': sum(r['reimportTriangles'] for r in rows)}, indent=2))
