"""Deterministic static glTF container and independent decoded source checks."""
import hashlib
import json
import struct

PALETTE = {'globe': [.64, .66, .67, 1], 'muscle': [.32, .35, .37, 1],
           'nerve': [.60, .61, .57, 1], 'trochlea': [.22, .24, .25, 1]}
ROLES = tuple(PALETTE)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def vector_basis(value, inverse=False):
    x, y, z = map(float, value)
    return [x, -z, y] if inverse else [x, z, -y]


def matrix_basis(matrix, inverse=False):
    permutation = (0, 2, 1, 3)
    sign = (1, 1, -1, 1)
    result = [[0.0]*4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            if inverse:
                result[permutation[i]][permutation[j]] = sign[i]*sign[j]*matrix[i][j]
            else:
                result[i][j] = sign[i]*sign[j]*matrix[permutation[i]][permutation[j]]
    return result


def flatten(matrix):
    return [matrix[row][column] for column in range(4) for row in range(4)]


def unflatten(values):
    require(len(values) == 16, 'Invalid matrix length')
    return [[values[column*4+row] for column in range(4)] for row in range(4)]


def corners_sha(positions, normals, indices):
    data = bytearray()
    for index in indices:
        data.extend(struct.pack('<ffffff', *positions[index], *normals[index]))
    return sha(data)


def role_for(name):
    if name.startswith(('Sclera.', 'Cornea.')):
        return 'globe'
    if name.startswith('Optic nerve (II).'):
        return 'nerve'
    if name.startswith('Trochlea of superior oblique muscle.'):
        return 'trochlea'
    require('muscle.' in name, 'Unsupported source name: '+name)
    return 'muscle'


def encode(document, payload):
    text = json.dumps(document, separators=(',', ':'), ensure_ascii=False).encode()
    text += b' '*((-len(text)) % 4)
    payload += b'\0'*((-len(payload)) % 4)
    return (struct.pack('<III', 0x46546c67, 2, 28+len(text)+len(payload)) +
            struct.pack('<II', len(text), 0x4e4f534a) + text +
            struct.pack('<II', len(payload), 0x004e4942) + payload)


def decode(data):
    require(data[:4] == b'glTF' and len(data) >= 28, 'Expected hydrated GLB')
    _, version, total = struct.unpack_from('<III', data)
    require(version == 2 and total == len(data), 'Invalid GLB header')
    length, kind = struct.unpack_from('<II', data, 12)
    require(kind == 0x4e4f534a, 'Missing JSON chunk')
    document = json.loads(data[20:20+length])
    cursor = 20+length
    length, kind = struct.unpack_from('<II', data, cursor)
    require(kind == 0x004e4942 and cursor+8+length == len(data), 'Unexpected GLB chunks')
    return document, data[cursor+8:]


def make(objects, source):
    document = {'asset': {'version': '2.0', 'generator': 'med-assets source-native eye exterior r01',
                          'copyright': 'Z-Anatomy / BodyParts3D; CC BY-SA 4.0; see retained attribution'},
                'scene': 0, 'scenes': [], 'nodes': [], 'meshes': [], 'materials': [],
                'accessors': [], 'bufferViews': [], 'buffers': [],
                'extras': {'source': source, 'scope': 'Static source-labelled exterior courses; no attachment, action, pathway or anterior-layer claim.'}}
    payload = bytearray()
    for role in ROLES:
        document['materials'].append({'name': 'Editorial neutral '+role, 'doubleSided': True,
            'pbrMetallicRoughness': {'baseColorFactor': PALETTE[role], 'metallicFactor': 0, 'roughnessFactor': .62}})

    def accessor(values, kind, component, bounds=False):
        payload.extend(b'\0'*((-len(payload)) % 4))
        offset = len(payload)
        width = 3 if kind == 'VEC3' else 1
        fmt = {5126: 'f', 5123: 'H', 5125: 'I'}[component]
        for value in values:
            payload.extend(struct.pack('<'+fmt*width, *(value if width == 3 else [value])))
        document['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(payload)-offset})
        item = {'bufferView': len(document['bufferViews'])-1, 'componentType': component, 'count': len(values), 'type': kind}
        if bounds:
            item['min'] = [min(p[a] for p in values) for a in range(3)]
            item['max'] = [max(p[a] for p in values) for a in range(3)]
        document['accessors'].append(item)
        return len(document['accessors'])-1

    for obj in objects:
        positions = [vector_basis(p) for p in obj['positions']]
        normals = [vector_basis(n) for n in obj['normals']]
        primitive = {'attributes': {'POSITION': accessor(positions, 'VEC3', 5126, True),
                                     'NORMAL': accessor(normals, 'VEC3', 5126)},
                     'indices': accessor(obj['indices'], 'SCALAR', 5123 if len(positions) <= 65535 else 5125),
                     'material': ROLES.index(role_for(obj['name'])), 'mode': 4}
        document['meshes'].append({'name': obj['name'], 'primitives': [primitive]})
        document['nodes'].append({'name': obj['name'], 'mesh': len(document['meshes'])-1,
                                  'matrix': flatten(matrix_basis(obj['matrixNative'])),
                                  'extras': {'sourceName': obj['name'], 'sourceType': obj['sourceType'],
                                             'sourceParent': obj['sourceParent'], 'sourceSide': obj['name'][-1]}})
    for side in ('r', 'l'):
        document['scenes'].append({'name': 'Source '+side.upper()+' exterior courses',
            'nodes': [i for i, obj in enumerate(objects) if obj['name'].endswith('.'+side)],
            'extras': {'visibility': 'Editorial unilateral scene; all opposite-side source objects remain in the other scene.',
                       'orientation': 'Side labels follow source names; no independent patient-orientation certification.',
                       'opticSegment': 'Retained source segment only; no pathway continuity claim.'}})
    payload.extend(b'\0'*((-len(payload)) % 4))
    document['buffers'] = [{'byteLength': len(payload)}]
    return encode(document, bytes(payload))


def read_accessor(document, payload, index):
    item = document['accessors'][index]
    require(set(item) <= {'bufferView', 'componentType', 'count', 'type', 'min', 'max'}, 'Unexpected accessor encoding')
    view = document['bufferViews'][item['bufferView']]
    require(view['buffer'] == 0 and 'byteStride' not in view, 'Unexpected buffer view')
    width = {'VEC3': 3, 'SCALAR': 1}[item['type']]
    fmt = {5126: 'f', 5123: 'H', 5125: 'I'}[item['componentType']]
    stride = struct.calcsize('<'+fmt*width)
    require(view['byteLength'] == item['count']*stride, 'Accessor byte extent differs')
    values = [struct.unpack_from('<'+fmt*width, payload, view['byteOffset']+i*stride) for i in range(item['count'])]
    return [list(v) if width == 3 else v[0] for v in values]


def verify(data, bindings):
    document, payload = decode(data)
    require(len(document['nodes']) == len(document['meshes']) == len(bindings), 'Source object inventory differs')
    require(len(document['buffers']) == 1 and document['buffers'][0] == {'byteLength': len(payload)}, 'Buffer extent differs')
    require(not any(k in document for k in ('animations', 'skins', 'textures', 'images')), 'Unexpected rig/texture/animation')
    require(document['scene'] == 0 and len(document['scenes']) == 2, 'Source-side scene contract differs')
    for scene, side in zip(document['scenes'], ('r', 'l')):
        require(scene['nodes'] == [i for i, b in enumerate(bindings) if b['name'].endswith('.'+side)], 'Source-side partition differs')
    expected_materials = [{'name': 'Editorial neutral '+role, 'doubleSided': True,
        'pbrMetallicRoughness': {'baseColorFactor': PALETTE[role], 'metallicFactor': 0, 'roughnessFactor': .62}} for role in ROLES]
    require(document['materials'] == expected_materials, 'Editorial material semantics differ')
    rows = []
    for i, binding in enumerate(bindings):
        node = document['nodes'][i];mesh = document['meshes'][i]
        require(node['name'] == mesh['name'] == binding['name'] and node['mesh'] == i, 'Source name mapping differs')
        require(set(node) == {'name', 'mesh', 'matrix', 'extras'}, 'Unexpected node transform/hierarchy')
        require(matrix_basis(unflatten(node['matrix']), inverse=True) == binding['matrixNative'], 'Native matrix differs')
        require(node['extras'] == {'sourceName': binding['name'], 'sourceType': binding['sourceType'],
                                   'sourceParent': binding['sourceParent'], 'sourceSide': binding['name'][-1]}, 'Source provenance differs')
        require(len(mesh['primitives']) == 1, 'Unexpected primitive count')
        primitive = mesh['primitives'][0]
        require(primitive['mode'] == 4 and primitive['material'] == ROLES.index(role_for(binding['name'])), 'Display role differs')
        positions = [vector_basis(v, inverse=True) for v in read_accessor(document, payload, primitive['attributes']['POSITION'])]
        normals = [vector_basis(v, inverse=True) for v in read_accessor(document, payload, primitive['attributes']['NORMAL'])]
        indices = read_accessor(document, payload, primitive['indices'])
        require(len(indices) == binding['triangles']*3, 'Triangle count differs')
        require(corners_sha(positions, normals, indices) == binding['nativeTriangleCornersSha256'], 'Native triangle positions/normals differ')
        rows.append({'name': binding['name'], 'nativeMatrixExact': True, 'nativeTriangleCornersExact': True})
    return {'objects': len(rows), 'sourceSideScenes': 2, 'defaultSourceSide': 'r', 'rows': rows}
