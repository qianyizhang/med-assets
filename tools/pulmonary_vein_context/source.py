"""Exact retained pulmonary-vein and same-case context inputs; no downloads."""
import hashlib
import json
import math
from pathlib import Path
import struct

GLB_PATH = 'models/pulmonary_vein/exports/metadata-cleanup-r01/pulmonary_vein.glb'
GLB_SHA = '9e0454c0a920bcd9292d1aced370ff781b97aa8fb87b0439eb1f0ac21517a593'
GLB_BYTES = 1718704
SOURCE_DIR = 'body/anatomy-workshop-r1/body-3d-source/tb3/presentation/task-explorer/anatomy'
SOURCE_SHA = '1968b148d325c9b169c521bda23cad7d357b1c2e00580f0db3bfcaeaf974b038'
MANIFEST_SHA = '31d9696f77ded3e075d7c921fadcdc2258eeab6212f4720c5ee67a27d28fafec'
MASK_SHA = '08bf9cc04f61e27090d70487ecf84128e543080b5fc15d883a05468795a44eeb'
SOURCE_REVISION = '75ec4e6530abe4d434b07958e90bdc9dec062bef'
CONTEXT = {
    'heart': '545f45eb67d47965c6e86aa6bd9442069e603a600adaf278db2b90c11cc5f61d',
    'lung_upper_lobe_left': 'ec02009248f99a7bfcdb91bf856eb05ae526643018e2d1e05d3fc5383039a0fe',
    'lung_lower_lobe_left': 'b22148bc98b0524a76a3d60bccdd9702dd94dc0223fb5276ba15d47ae6c8f6ad',
    'lung_upper_lobe_right': 'e3ca11acda193927cc1ec9e9fe096aa724811aa05f2f775aaf18ff26aee0ab29',
    'lung_middle_lobe_right': 'c5f89cefa2c5894108b84bf933afbd419399f89a7ca786bfb6495e2dba01b819',
    'lung_lower_lobe_right': '1d23017adc49bf2bd610f3b675be99732f968382db921ccf6adb2fdcffe129bb',
}
CAMERAS = {
    'overview': {'position': [0., .55, .065], 'scale': .36},
    'detail': {'position': [.034754461608827114, .55, .05972786992788315], 'scale': .13},
}
RESOLUTION = [900, 700]
POSTERIOR_BASIS = [[-1., 0., 0.], [0., 0., 1.], [0., 1., 0.]]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ras_to_blender(point):
    r, a, s = point
    return (-r / 1000., -(a - 155.) / 1000., (s - 430.) / 1000.)


def gltf_to_blender(point):
    x, y, z = point
    return (x, -z, y)


def project(point, camera):
    # Posterior camera: screen right is patient right (native Blender -X).
    x, _, z = point
    cx, _, cz = camera['position']
    pixels_per_metre = RESOLUTION[0] / camera['scale']
    return [RESOLUTION[0] / 2 - (x - cx) * pixels_per_metre,
            RESOLUTION[1] / 2 - (z - cz) * pixels_per_metre]


def geometry_sha(vertices, faces):
    b = b''.join(struct.pack('<fff', *v) for v in vertices)
    b += b''.join(struct.pack('<III', *f) for f in faces)
    return sha(b)


def bounds(vertices):
    return [[min(v[i] for v in vertices) for i in range(3)],
            [max(v[i] for v in vertices) for i in range(3)]]


def decode_glb(raw):
    require(len(raw) == GLB_BYTES and sha(raw) == GLB_SHA, 'Retained GLB identity mismatch')
    magic, version, length = struct.unpack_from('<4sII', raw)
    require(magic == b'glTF' and version == 2 and length == len(raw), 'Invalid GLB header')
    n, kind = struct.unpack_from('<I4s', raw, 12)
    require(kind == b'JSON', 'Missing GLB JSON chunk')
    doc = json.loads(raw[20:20+n])
    bin_size, kind = struct.unpack_from('<I4s', raw, 20+n)
    binary = raw[28+n:]
    require(kind == b'BIN\0' and bin_size == len(binary), 'Invalid GLB binary chunk')
    require(len(doc['nodes']) == len(doc['meshes']) == 1, 'Unexpected retained components')
    node = doc['nodes'][0]
    require(node['name'] == 'Pulmonary Vein | source surface', 'Wrong retained source node')
    require(not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale')),
            'Unexpected retained node transform')
    extra = node['extras']
    require(extra['source_case'] == 's1233' and extra['source_revision'] == SOURCE_REVISION,
            'Wrong retained source case/revision')
    primitive = doc['meshes'][0]['primitives'][0]
    require(len(doc['meshes'][0]['primitives']) == 1 and primitive.get('mode', 4) == 4,
            'Unexpected retained primitive')

    def accessor(index):
        a = doc['accessors'][index]
        require('sparse' not in a, 'Sparse accessor unsupported')
        v = doc['bufferViews'][a['bufferView']]
        count = {'VEC3': 3, 'SCALAR': 1}[a['type']]
        fmt = '<' + {5126: 'f', 5125: 'I', 5123: 'H'}[a['componentType']] * count
        size = struct.calcsize(fmt)
        start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        return [struct.unpack_from(fmt, binary, start + i * v.get('byteStride', size))
                for i in range(a['count'])]

    positions = [gltf_to_blender(p) for p in accessor(primitive['attributes']['POSITION'])]
    indices = [p[0] for p in accessor(primitive['indices'])]
    require(len(indices) % 3 == 0 and max(indices) < len(positions), 'Invalid retained triangles')
    faces = [indices[i:i+3] for i in range(0, len(indices), 3)]
    require(all(math.isfinite(x) for p in positions for x in p), 'Nonfinite source coordinate')
    return doc, positions, faces, sha(binary)


def load_inputs(root):
    root = Path(root)
    raw = (root / GLB_PATH).read_bytes()
    doc, positions, faces, binary_sha = decode_glb(raw)
    source_dir = root / SOURCE_DIR
    source_raw = (source_dir / 'pulmonary_vein.json').read_bytes()
    require(sha(source_raw) == SOURCE_SHA, 'Retained source JSON identity mismatch')
    source = json.loads(source_raw)
    require(source['source_case'] == 's1233' and source['coordinates'] == 'RAS millimetres',
            'Wrong source frame')
    manifest_raw = (source_dir / 'manifest.json').read_bytes()
    require(sha(manifest_raw) == MANIFEST_SHA, 'Source manifest identity mismatch')
    mask = json.loads(manifest_raw)['assets']['pulmonary_vein']
    require(mask['source_sha256'] == MASK_SHA and mask['source_components'] == 4
            and mask['retained_component_voxels'] == 3953 and mask['asset_sha256'] == SOURCE_SHA,
            'Source component receipt differs')
    contexts, context_rows = {}, []
    for name, expected in CONTEXT.items():
        path = source_dir / (name + '.json')
        data = path.read_bytes()
        require(sha(data) == expected, 'Context identity mismatch: ' + name)
        row = json.loads(data)
        require(row['source_case'] == 's1233' and row['coordinates'] == 'RAS millimetres'
                and row['id'] == name, 'Context case/frame mismatch: ' + name)
        vs = [ras_to_blender(p) for p in row['vertices']]
        fs = row['faces']
        contexts[name] = (vs, fs)
        context_rows.append({'name': name, 'path': SOURCE_DIR + '/' + name + '.json',
                             'sha256': expected, 'case': row['source_case'], 'coordinates': row['coordinates'],
                             'vertices': len(vs), 'triangles': len(fs), 'blenderBoundsM': bounds(vs),
                             'geometrySha256': geometry_sha(vs, fs)})
    record = {'path': GLB_PATH, 'sha256': GLB_SHA, 'bytes': len(raw), 'binaryChunkSha256': binary_sha,
              'node': doc['nodes'][0]['name'], 'vertices': len(positions), 'triangles': len(faces),
              'geometrySha256': geometry_sha(positions, faces), 'blenderBoundsM': bounds(positions),
              'sourceJsonSha256': SOURCE_SHA, 'sourceManifestSha256': sha(manifest_raw),
              'sourceMaskSha256': MASK_SHA, 'sourceCase': 's1233', 'sourceRevision': SOURCE_REVISION,
              'sourceComponentReceipt': {'originalComponents': 4, 'retainedLargestComponentVoxels': 3953,
                                         'rawMaskRecomputed': False},
              'contexts': context_rows,
              'coordinateMapping': {'rasMmToBlenderM': '(-R/1000, -(A-155)/1000, (S-430)/1000)',
                                    'gltfToBlender': '(x, -z, y)', 'independentFitting': False},
              'laterality': {'source': 'RAS +X is patient right; retained RAS X is negative',
                             'posteriorScreenLeft': 'patient left', 'posteriorScreenRight': 'patient right'}}
    return record, positions, faces, contexts
