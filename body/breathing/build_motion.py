"""Replay the illustrative respiratory GLBs from the exact Workshop meshes."""

import argparse
import hashlib
import json
import math
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np

PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE.parents[1] / 'tools'))
from glb import decode

CLIP = 'Illustrative breathing · 4 seconds'
AMPLITUDES = {
    'liver': .008, 'stomach': .006, 'spleen': .006, 'kidney_left': .004,
    'kidney_right': .004, 'pancreas': .003, 'gallbladder': .008, 'heart': .002,
}


def manifest_assets():
    return json.loads((PACKAGE / 'animation-manifest.json').read_text())['assets']


def write_glb(path, document, binary):
    # Preserve the imported generator's ASCII JSON encoding and key order.
    binary += b'\0' * (-len(binary) % 4)
    document['buffers'] = [{'byteLength': len(binary)}]
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    path.write_bytes(
        struct.pack('<III', 0x46546C67, 2, 28 + len(encoded) + len(binary))
        + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
        + struct.pack('<II', len(binary), 0x004E4942) + binary
    )


def buffer_view(document, binary, array):
    binary += b'\0' * (-len(binary) % 4)
    views = document.setdefault('bufferViews', [])
    views.append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': array.nbytes})
    binary += array.tobytes()
    return len(views) - 1


def add_accessor(document, binary, values, kind):
    array = np.asarray(values, dtype='<f4').reshape(-1, {'SCALAR': 1, 'VEC3': 3}[kind])
    view = buffer_view(document, binary, array)
    accessors = document.setdefault('accessors', [])
    accessors.append({
        'bufferView': view, 'componentType': 5126, 'count': len(array), 'type': kind,
        'min': array.min(axis=0).tolist(), 'max': array.max(axis=0).tolist(),
    })
    return len(accessors) - 1


def positions(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return np.ndarray(
        (accessor['count'], 3), '<f4', buffer=binary, offset=offset,
        strides=(view.get('byteStride', 12), 4),
    ).copy()


def inspiration_delta(xyz, is_lung):
    delta = np.zeros_like(xyz)
    if is_lung:
        # Common field across lobes in glTF metres, with +Y superior.
        weight = np.clip((.19 - xyz[:, 1]) / .27, 0, 1)
        weight = weight * weight * (3 - 2 * weight)
        delta[:, 1] = -.018 * weight
        delta[:, 0] = xyz[:, 0] * .075 * weight
        delta[:, 2] = (xyz[:, 2] + .025) * .09 * weight
    else:
        radius = np.clip((xyz[:, 0] / .155)**2 + ((xyz[:, 2] + .012) / .087)**2, 0, 1)
        delta[:, 1] = -.018 * (1 - radius)**.55 - .003
    return delta


def add_motion(document, binary, organ):
    times = np.linspace(0, 4, 81)
    phase = times / 4
    # Smooth endpoints and a 40% inspiration, 60% expiration cycle.
    weight = np.where(
        phase <= .4,
        (1 - np.cos(np.pi * phase / .4)) / 2,
        (1 + np.cos(np.pi * (phase - .4) / .6)) / 2,
    )
    time_index = add_accessor(document, binary, times, 'SCALAR')
    animation = {'name': CLIP, 'samplers': [], 'channels': []}
    for node_index, node in enumerate(document['nodes']):
        if 'mesh' not in node:
            continue
        if organ.startswith('lung') or organ == 'diaphragm':
            mesh = document['meshes'][node['mesh']]
            for primitive in mesh['primitives']:
                xyz = positions(document, binary, primitive['attributes']['POSITION'])
                delta = inspiration_delta(xyz, organ.startswith('lung'))
                primitive['targets'] = [{'POSITION': add_accessor(document, binary, delta, 'VEC3')}]
            mesh['weights'] = [0]
            mesh.setdefault('extras', {})['targetNames'] = ['Inspiration']
            path = 'weights'
            output = add_accessor(document, binary, weight, 'SCALAR')
        else:
            base = np.array(node.get('translation', [0, 0, 0]))
            motion = base + np.column_stack([weight * 0, -AMPLITUDES[organ] * weight, weight * 0])
            path = 'translation'
            output = add_accessor(document, binary, motion, 'VEC3')
        animation['channels'].append({
            'sampler': len(animation['samplers']), 'target': {'node': node_index, 'path': path},
        })
        animation['samplers'].append({'input': time_index, 'output': output, 'interpolation': 'LINEAR'})
    document['animations'] = [animation]
    document.setdefault('extras', {})['motion_note'] = (
        'Authored educational respiratory deformation; not measured motion, CFD, or validated physiology.'
    )
    return len(animation['channels'])


def diaphragm():
    """Build the authored, open schematic surface in the Workshop frame."""
    vertices, faces = [], []
    sides, rings = 64, 18
    for ring in range(rings + 1):
        radius = ring / rings
        for step in range(sides):
            angle = 2 * math.pi * step / sides
            x = .155 * radius * math.cos(angle)
            z = -.012 + .087 * radius * math.sin(angle)
            y = -.075 + .043 * (1 - radius * radius) + .006 * max(0, -x / .155) * (1 - radius * radius)
            vertices.append([x, y, z])
    for ring in range(rings):
        for step in range(sides):
            a = ring * sides + step
            c = ring * sides + (step + 1) % sides
            b = (ring + 1) * sides + step
            d = (ring + 1) * sides + (step + 1) % sides
            faces.extend([a, b, c, c, b, d])
    document = {
        'asset': {'version': '2.0', 'generator': 'Educational breathing authoring script'},
        'scene': 0,
        'scenes': [{'nodes': [0]}],
        'nodes': [{
            'name': 'Authored schematic diaphragm', 'mesh': 0,
            'extras': {'view_role': 'surface', 'educational_only': True},
        }],
        'meshes': [{'primitives': []}],
        'materials': [{
            'name': 'Schematic diaphragm',
            'pbrMetallicRoughness': {'baseColorFactor': [.63, .38, .28, .65], 'roughnessFactor': .7},
            'alphaMode': 'BLEND', 'doubleSided': True,
        }],
    }
    binary = bytearray()
    position = add_accessor(document, binary, vertices, 'VEC3')
    view = buffer_view(document, binary, np.array(faces, dtype='<u4'))
    indices = len(document['accessors'])
    document['accessors'].append({'bufferView': view, 'componentType': 5125, 'count': len(faces), 'type': 'SCALAR'})
    normals = np.zeros((len(vertices), 3), dtype=np.float32)
    xyz = np.asarray(vertices)
    for a, b, c in np.array(faces).reshape(-1, 3):
        normal = np.cross(xyz[b] - xyz[a], xyz[c] - xyz[a])
        normals[a] += normal
        normals[b] += normal
        normals[c] += normal
    lengths = np.linalg.norm(normals, axis=1)
    normals[lengths > 0] /= lengths[lengths > 0, None]
    normals[lengths == 0] = [0, 1, 0]
    normal = add_accessor(document, binary, normals, 'VEC3')
    document['meshes'][0]['primitives'] = [{
        'attributes': {'POSITION': position, 'NORMAL': normal}, 'indices': indices, 'material': 0,
    }]
    return document, binary


def replay(source, output):
    if output.exists() or output.is_symlink():
        raise FileExistsError(f'Choose a fresh output directory: {output}')
    report = {}
    # Keep incomplete builds in an owned scratch directory until all inputs pass.
    with tempfile.TemporaryDirectory(prefix='.breathing-', dir=output.parent) as temporary:
        staged = Path(temporary) / 'clips'
        staged.mkdir()
        for asset in manifest_assets():
            organ = asset['id']
            if organ == 'diaphragm':
                document, binary = diaphragm()
            else:
                exact = asset['staticExport']
                path = source / Path(exact['file']).name
                raw = path.read_bytes()
                if len(raw) != exact['bytes'] or hashlib.sha256(raw).hexdigest() != exact['sha256']:
                    raise ValueError(f'Workshop mesh differs from the manifest or is an LFS pointer: {path}')
                document, source_binary = decode(raw)
                binary = bytearray(source_binary)
            report[organ] = add_motion(document, binary, organ)
            write_glb(staged / Path(asset['file']).name, document, binary)
        (staged / 'validation.json').write_text(json.dumps(report, indent=2))
        # Reserve the destination exclusively, including against an empty directory.
        output.mkdir()
        try:
            staged.replace(output)
        except OSError:
            output.rmdir()
            raise
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=PACKAGE.parent / 'anatomy-workshop-r1' / 'meshes')
    parser.add_argument('--output', type=Path, required=True, help='Fresh directory under an existing parent')
    args = parser.parse_args()
    try:
        report = replay(args.source, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
