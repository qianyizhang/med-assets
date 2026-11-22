"""Compare the static r01 GLBs by resolving every rendered primitive."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct
import subprocess

from build import read_glb, sha
from repack_static import MIN_SAVINGS, read_baseline

TABLES = ('meshes', 'materials', 'accessors', 'bufferViews')
FORMATS = {(5123, 'SCALAR'): 'H', (5126, 'VEC2'): '2f', (5126, 'VEC3'): '3f'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Scene:
    def __init__(self, data):
        self.doc, self.binary = read_glb(data)
        self.used = defaultdict(set)
        self.decoded = {}
        self.triangles = 0
        self.primitives = 0

    def entry(self, table, index):
        require(type(index) is int and 0 <= index < len(self.doc[table]), f'Invalid {table} index')
        self.used[table].add(index)
        return self.doc[table][index]

    def accessor(self, index):
        row = self.entry('accessors', index)
        view = self.entry('bufferViews', row['bufferView'])
        if index not in self.decoded:
            # The pinned baseline uses one tightly packed, dense view per
            # accessor. Decode that layout only, rejecting changed encodings.
            fmt = struct.Struct('<' + FORMATS[row['componentType'], row['type']])
            start, size = view['byteOffset'], view['byteLength']
            require(not ({'sparse', 'byteOffset'} & row.keys()) and
                    'byteStride' not in view and view['buffer'] == 0 and
                    0 <= start <= len(self.binary) - size and start % 4 == 0 and
                    size > 0 and size == fmt.size * row['count'], 'Unexpected accessor encoding')
            payload = self.binary[start:start + size]
            self.decoded[index] = (
                without(row, 'bufferView'), without(view, 'byteOffset'),
                tuple(fmt.iter_unpack(payload)), payload,
            )
        return self.decoded[index]

    def mesh(self, index):
        mesh = self.entry('meshes', index)
        resolved = []
        for primitive in mesh['primitives']:
            self.primitives += 1
            self.triangles += self.doc['accessors'][primitive['indices']]['count'] // 3
            resolved.append({
                **primitive,
                'indices': self.accessor(primitive['indices']),
                'attributes': {name: self.accessor(i) for name, i in primitive['attributes'].items()},
                'material': self.entry('materials', primitive['material']),
            })
        return {**mesh, 'primitives': resolved}

    def counts(self):
        return {
            'table_entries': {table: len(self.doc[table]) for table in TABLES},
            'referenced_entries': {table: len(self.used[table]) for table in TABLES},
            'primitives': self.primitives,
            'triangles': self.triangles,
            'decoded_accessor_elements': sum(len(row[2]) for row in self.decoded.values()),
            'bin_bytes': len(self.binary),
        }


def without(record, *keys):
    return {key: value for key, value in record.items() if key not in keys}


def verify(baseline, candidate):
    original, updated = Scene(baseline), Scene(candidate)
    require(without(original.doc, 'nodes', 'buffers', *TABLES) ==
            without(updated.doc, 'nodes', 'buffers', *TABLES), 'Scene hierarchy or metadata changed')
    before, after = original.doc['nodes'], updated.doc['nodes']
    names = [node['name'] for node in before]
    require(len(set(names)) == len(before) == len(after) == 124, 'Expected 124 distinct objects')
    roots = updated.doc['scenes'][updated.doc['scene']]['nodes']
    require(sorted(roots) == list(range(124)), 'Expected all 124 objects at the scene root')
    for old, new in zip(before, after):
        require(without(old, 'mesh') == without(new, 'mesh'), f"Node changed: {old['name']}")
        require(original.mesh(old['mesh']) == updated.mesh(new['mesh']),
                f"Decoded primitive, mesh or material changed: {old['name']}")
    old_counts, new_counts = original.counts(), updated.counts()
    require(old_counts['referenced_entries'] == new_counts['referenced_entries'] ==
            new_counts['table_entries'], 'Missing or unreachable table entries')
    # Every packed byte belongs to a retained view or is zero alignment padding.
    end = 0
    for view in updated.doc['bufferViews']:
        start = (end + 3) & ~3
        require(view['byteOffset'] == start and not any(updated.binary[end:start]),
                'Unexpected BIN gap, padding or overlapping view')
        end = start + view['byteLength']
    padded = (end + 3) & ~3
    require(updated.doc['buffers'] == [{'byteLength': padded}] and
            len(updated.binary) == padded and not any(updated.binary[end:]), 'Unexpected BIN tail')
    savings = len(baseline) - len(candidate)
    require(savings >= MIN_SAVINGS, 'Candidate misses the export-byte savings target')
    return {
        'baseline': {'sha256': sha(baseline), 'bytes': len(baseline), **old_counts},
        'candidate': {'sha256': sha(candidate), 'bytes': len(candidate), **new_counts},
        'saved_bytes': savings,
        'exact_decoded_primitives_materials_nodes_and_scenes': True,
        'object_names': names,
    }


def pixels(path):
    return subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(path), '-frames:v', '1',
         '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
        check=True, stdout=subprocess.PIPE,
    ).stdout


def verify_renders(root, result):
    original, updated = root / 'Original', root / 'Updated'
    old_binding = (original / 'bindings.json').read_bytes()
    new_binding = (updated / 'bindings.json').read_bytes()
    before, after = json.loads(old_binding), json.loads(new_binding)
    require(before['sha256'] == result['baseline']['sha256'] and
            after['sha256'] == result['candidate']['sha256'] and
            after['matchedBindingSha256'] == sha(old_binding), 'Render bindings mismatch')
    settings = ('rendererRecipeSha256', 'frame', 'fps', 'bounds', 'lights', 'samples', 'hiddenCutawayMeshes')
    require(all(before[key] == after[key] for key in settings) and
            before['visibleMeshes'] == after['visibleMeshes'] == 124, 'Render settings mismatch')
    views = ('whole-front', 'seam-neutral')
    require(tuple(view['view'] for view in before['views']) ==
            tuple(view['view'] for view in after['views']) == views, 'Missing or unexpected render views')
    comparisons = []
    for old, new in zip(before['views'], after['views']):
        require(without(old, 'sha256') == without(new, 'sha256'), 'View framing mismatch')
        original_png, updated_png = original / old['file'], updated / new['file']
        for path, binding in ((original_png, old), (updated_png, new)):
            data = path.read_bytes()
            require(sha(data) == binding['sha256'], 'PNG hash mismatch')
            require(data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR' and
                    struct.unpack_from('>II', data, 16) == (960, 960), 'Expected a 960×960 PNG')
        a, b = pixels(original_png), pixels(updated_png)
        require(len(a) == len(b) == 960 * 960 * 4 and a == b, f"Pixel mismatch: {old['view']}")
        comparisons.append({
            'view': old['view'], 'size': [960, 960], 'differing_pixels': 0,
            'rgba8_sha256': sha(a), 'original_png_sha256': old['sha256'],
            'updated_png_sha256': new['sha256'],
        })
    return {'original_binding_sha256': sha(old_binding), 'updated_binding_sha256': sha(new_binding),
            'views': comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--renders', type=Path, help='Also compare Original and Updated renders using FFmpeg')
    args = parser.parse_args()
    try:
        result = verify(read_baseline(args.source), args.candidate.read_bytes())
        if args.renders:
            result['pixels'] = verify_renders(args.renders, result)
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Verification failed: {error}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
