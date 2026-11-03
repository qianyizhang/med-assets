#!/usr/bin/env python3
"""Replay pinned editorial placement. Python 3.11+, stdlib only; never fit anatomy."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

PRESETS = Path(__file__).with_name('editorial-alignment-20261103.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def proper_similarity(matrix):
    """Require finite row-major affine matrix with proper rotation + uniform scale."""
    if (len(matrix) != 4 or any(len(row) != 4 for row in matrix)
            or any(not math.isfinite(x) for row in matrix for x in row)
            or matrix[3] != [0, 0, 0, 1]):
        raise ValueError('Expected a finite 4x4 affine matrix')
    cols = [tuple(matrix[i][j] for i in range(3)) for j in range(3)]
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    scale2 = dot(cols[0], cols[0])
    a, b, c = cols
    determinant = (a[0] * (b[1] * c[2] - b[2] * c[1])
                   - b[0] * (a[1] * c[2] - a[2] * c[1])
                   + c[0] * (a[1] * b[2] - a[2] * b[1]))
    if (scale2 <= 0 or determinant <= 0
            or any(not math.isclose(dot(col, col), scale2, rel_tol=1e-10)
                   for col in cols)
            or any(abs(dot(cols[i], cols[j])) > scale2 * 1e-10
                   for i in range(3) for j in range(i))):
        raise ValueError('Reflection, shear or nonuniform scale is not allowed')


def align_bytes(data, preset):
    """Add one scene root; retain every original node and all non-JSON chunks."""
    if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
        raise ValueError('Input is an LFS pointer; obtain the authorized GLB payload')
    if sha(data) != preset['input_sha256']:
        raise ValueError('Input SHA-256 mismatch; do not reuse this fit on new geometry')
    if len(data) < 20 or struct.unpack_from('<III', data) != (0x46546C67, 2, len(data)):
        raise ValueError('Invalid GLB 2.0 header')
    length, kind = struct.unpack_from('<II', data, 12)
    if kind != 0x4E4F534A or length % 4 or 20 + length > len(data):
        raise ValueError('Invalid GLB JSON chunk')
    doc = json.loads(data[20:20 + length])
    tail = data[20 + length:]
    offset = 0
    while offset < len(tail):
        if len(tail) - offset < 8:
            raise ValueError('Truncated GLB chunk')
        count = struct.unpack_from('<I', tail, offset)[0]
        offset += 8 + count
        if count % 4 or offset > len(tail):
            raise ValueError('Invalid GLB chunk length')
    matrix = preset['matrix_row_major']
    proper_similarity(matrix)
    scene = doc['scenes'][doc.get('scene', 0)]
    root = len(doc['nodes'])
    doc['nodes'].append({
        'name': preset['root_name'],
        'matrix': [matrix[i][j] for j in range(4) for i in range(4)],
        'children': scene['nodes'],
        'extras': {
            'role': 'Editorial cross-source placement only; not anatomical registration',
            'original_sha256': sha(data),
        },
    })
    scene['nodes'] = [root]
    encoded = json.dumps(doc, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    result = (struct.pack('<III', 0x46546C67, 2, 20 + len(encoded) + len(tail))
              + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded + tail)
    if sha(result) != preset['output_sha256']:
        raise ValueError('Output differs from the pinned reviewed placement')
    return result


def main():
    presets = json.loads(PRESETS.read_text())['presets']
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('preset', choices=presets)
    parser.add_argument('input', type=Path, help='Exact original GLB; no network fetch')
    parser.add_argument('output', type=Path, help='New aligned GLB; must not exist')
    args = parser.parse_args()
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('Output already exists; originals and earlier exports are protected')
        result = align_bytes(args.input.read_bytes(), presets[args.preset])
        with args.output.open('xb') as out:
            out.write(result)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Alignment not written: {error}\n')
    print(f'{sha(result)}  {args.output}')


if __name__ == '__main__':
    main()
