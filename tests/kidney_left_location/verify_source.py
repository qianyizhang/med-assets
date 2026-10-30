"""Read-only source/crop proof. Requires Pillow; no render or asset mutation."""
import hashlib
import json
from pathlib import Path
import re
import struct

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[2]
DISPLAY = ROOT / 'reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/display'
EXPECTED = {
    'models/kidney_left/exports/hra-female-v1.3-r02/kidney_left.glb': '8e55b5ae48821f067f41bd23ffdd668f68c7ff705cf49e9a40287042fee469fc',
    'reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/display/contact.webp': '2a194bee7c66deab78bb74a090ee4f6bc44b6bcb59f9c57164100ffed506690d',
    'reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/display/medulla_and_tip_surfaces_front.webp': 'b140b1200fe8947b2185da28e7dc39d27cc991facbb88d18bcb0e3bd81ef010c',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def foreground(image):
    """Source-specific pixel mask for silhouette bounds, not anatomy segmentation."""
    return [(x, y) for y in range(image.height) for x in range(image.width)
            if (lambda c: c[0] - c[1] > 12 and c[0] > 65)(image.getpixel((x, y)))]


def outline(image):
    pixels = foreground(image)
    ymin, ymax = min(y for x, y in pixels), max(y for x, y in pixels)
    rows = list(range(ymin, ymax + 1, 4))
    if rows[-1] != ymax:
        rows.append(ymax)
    left, right = [], []
    for y in rows:
        xs = [x for x, yy in pixels if yy == y]
        left.append((min(xs), y))
        right.append((max(xs), y))
    return 'M' + ' L'.join(f'{x},{y}' for x, y in left + right[::-1]) + ' Z'


def verify():
    for path, digest in EXPECTED.items():
        require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, 'Source mismatch: ' + path)
    record = json.loads((DISPLAY.parent / 'record.json').read_text())
    require(record['artifact']['sha256'] == next(iter(EXPECTED.values())), 'Artifact binding')
    require(record['evidence'][0]['originalPngSha256'] == '8479f68fd98b473ab73e55080b6aca8aba64f54391b9a8923ed5e2601ec564c3', 'Historical PNG binding')
    recipe = (ROOT / 'tests/kidney_pair/recipes/render_exact.py').read_text()
    # Pin the recipe whose whole-model frame and loop order were inspected.
    require(hashlib.sha256(recipe.encode()).hexdigest() ==
            'ad77856fbe21d366dbab314fd4b390e2ef0996539425d4049c029fd556f1055a',
            'Camera recipe changed')
    contact = Image.open(DISPLAY / 'contact.webp').convert('RGB')
    require(contact.size == (1260, 1436), 'Contact dimensions')
    raw = (ROOT / next(iter(EXPECTED))).read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    gltf, binary = json.loads(raw[20:20 + size]), raw[28 + size:]
    points = []
    for node in gltf['nodes']:
        require(not any(k in node for k in ['translation', 'rotation', 'scale', 'matrix']), 'Unexpected source transform')
        if 'mesh' not in node:
            continue
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            accessor = gltf['accessors'][primitive['attributes']['POSITION']]
            buffer = gltf['bufferViews'][accessor['bufferView']]
            require(accessor['componentType'] == 5126 and accessor['type'] == 'VEC3', 'Position type')
            offset = buffer.get('byteOffset', 0) + accessor.get('byteOffset', 0)
            coords = [struct.unpack_from('<3f', binary, offset + i * buffer.get('byteStride', 12))
                      for i in range(accessor['count'])]
            points.extend((node['extras']['layer_key'], p) for p in coords)
    lo = [min(p[i] for k, p in points) for i in range(3)]
    hi = [max(p[i] for k, p in points) for i in range(3)]
    center = [(a + b) / 2 for a, b in zip(lo, hi)]
    span = max(b - a for a, b in zip(lo, hi))
    scale = span * 1.18
    deltas = []
    for mode, y in [('exterior', 112), ('internal', 1016)]:
        selected = [p for k, p in points if mode == 'exterior' or k in ['renal_pyramids', 'papilla_labeled_tip_surfaces']]
        for col, axis in enumerate(['front', 'back', 'medial']):
            # glTF (x,y,z) -> Blender (x,-z,y); the recorded review axes only.
            uv = [(210 + (p[0] - center[0] if axis == 'front' else center[0] - p[0] if axis == 'back'
                          else p[2] - center[2]) * 420 / scale,
                   210 - (p[1] - center[1]) * 420 / scale) for p in selected]
            projected = [min(u for u, v in uv), min(v for u, v in uv), max(u for u, v in uv), max(v for u, v in uv)]
            pixels = foreground(contact.crop((col * 420, y, (col + 1) * 420, y + 420)))
            observed = [min(x for x, y in pixels), min(y for x, y in pixels), max(x for x, y in pixels) + 1, max(y for x, y in pixels) + 1]
            delta = max(abs(a - b) for a, b in zip(observed, projected))
            require(delta <= 2, f'{mode}/{axis}: crop/frame mismatch {delta}')
            deltas.append(round(delta, 6))
    single = Image.open(DISPLAY / 'medulla_and_tip_surfaces_front.webp').convert('RGB')
    require(single.size == (900, 900), 'Standalone render dimensions')
    small = single.resize((420, 420), Image.Resampling.BICUBIC)
    crop = contact.crop((0, 1016, 420, 1436))
    error = sum(ImageStat.Stat(ImageChops.difference(small, crop)).mean) / 3
    require(error < 1, f'Lossy internal comparison changed: {error}')
    source_js = (ROOT / 'studies/kidney_left_location/source.js').read_text()
    saved = json.loads(re.search(r'export const outlinePath = (.*);', source_js)[1])
    require(saved == outline(contact.crop((0, 112, 420, 532))), 'Outline detached from exterior pixels')
    require(EXPECTED['reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/display/contact.webp'] in source_js, 'UI hash pin')
    print(json.dumps({'status': 'passed', 'sourceHashes': 3, 'projectedTileBoundsMaxErrorPx': max(deltas),
                      'standaloneVsContactMeanAbsRGB': error, 'editorialOutlinePoints': saved.count('L') + 1,
                      'compositionRecipe': 'Not retained; tile layout corroborated by source projections and standalone pixels. No full composition replay claimed.'}, indent=2))


if __name__ == '__main__':
    verify()
