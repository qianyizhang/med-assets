"""Issue 102 extension contract; no downloader, browser launcher or security overrides."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = json.loads((HERE / 'fixture.json').read_text())
FRAME_IDS = [f'esophagus-{variant}-{state}' for variant in ('baseline', 'candidate')
             for state in ('oblique', 'transverse', *[f'layer-{i}' for i in range(1, 6)])]
FRAME_IDS += ['esophagus-candidate-gray-en', 'esophagus-candidate-gray-zh',
              'esophagus-candidate-hidden', 'esophagus-candidate-restored']


def require(test, message):
    if not test:
        raise ValueError(message)


def exact(path, spec):
    require(path.is_file() and path.stat().st_size == spec['bytes'], 'Exact GLB size required')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == spec['sha256'], 'Exact GLB SHA-256 required')
    return raw


def chunks(raw):
    require(len(raw) >= 20 and struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'GLB header')
    result = []
    offset = 12
    while offset < len(raw):
        require(offset + 8 <= len(raw), 'Truncated chunk')
        size, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        require(size % 4 == 0 and offset + size <= len(raw), 'Chunk bound')
        result.append((kind, raw[offset:offset + size]))
        offset += size
    require(len(result) == 2 and [c[0] for c in result] == [0x4e4f534a, 0x004e4942], 'Embedded JSON/BIN only')
    return result


def verify_pair(baseline, candidate):
    a, b = [chunks(exact(path, FIXTURE[key])) for path, key in
            ((baseline, 'baseline'), (candidate, 'candidate'))]
    docs = [json.loads(x[0][1]) for x in (a, b)]
    require(a[1:] == b[1:] and hashlib.sha256(a[1][1]).hexdigest() == FIXTURE['binarySHA256'], 'Geometry bytes changed')
    restored = copy.deepcopy(docs[1])
    for i in range(5):
        restored['materials'][i]['pbrMetallicRoughness']['baseColorFactor'] = docs[0]['materials'][i]['pbrMetallicRoughness']['baseColorFactor']
    require(restored == docs[0], 'Change outside five colors')
    for variant, doc in zip(('baseline', 'candidate'), docs):
        require(len(doc['nodes']) == len(doc['meshes']) == len(doc['materials']) == 5, 'Five compartments required')
        require(not doc.get('animations') and not doc.get('images') and not doc.get('extensionsRequired'), 'Unexpected asset feature')
        require(len(doc['buffers']) == 1 and not doc['buffers'][0].get('uri'), 'Embedded buffer only')
        triangles = 0
        for layer in FIXTURE['layers']:
            i = layer['node']; node = doc['nodes'][i]; mesh = doc['meshes'][i]; mat = doc['materials'][i]
            require(node['mesh'] == i and node['name'] == mesh['name'] == mat['name'] == layer['name'], 'Layer/name/material mapping')
            require(node['extras']['layer_order_inside_out'] == layer['number'], 'Inside-out numbering')
            require(len(mesh['primitives']) == 1, 'One primitive per compartment')
            primitive = mesh['primitives'][0]
            require(primitive['material'] == i and primitive.get('mode', 4) == 4, 'Primitive material/triangles')
            triangles += doc['accessors'][primitive['indices']]['count'] // 3
            require(mat['pbrMetallicRoughness']['baseColorFactor'] == layer[variant + 'RGBA'], 'Exported RGBA')
        require(triangles == 7700, 'Triangle count')
    return {'baseline': FIXTURE['baseline']['sha256'], 'candidate': FIXTURE['candidate']['sha256'],
            'meshes': 5, 'triangles': 7700, 'onlyFiveColorsChanged': True, 'runtimeVerified': False}


def prepare(source, output):
    """Use a caller-supplied exact local baseline; output must be new. Never fetch/publish."""
    source, output = Path(source).resolve(), Path(output).resolve()
    exact(source, FIXTURE['baseline'])
    require(not output.exists(), 'Refusing existing output')
    subprocess.run([sys.executable, str(ROOT / 'tests/esophagus_wall/palette_trial.py'),
                    '--input', str(source), '--params', str(ROOT / 'tests/esophagus_wall/parameters.json'),
                    '--output', str(output)], check=True, timeout=30, stdout=subprocess.DEVNULL)
    baseline = output / 'baseline/esophagus-wall-cutaway-r01.glb'
    candidate = output / 'candidate/esophagus-wall-palette-r01.glb'
    return verify_pair(baseline, candidate)


def validate_frame(row, raw, previous):
    """Check extension-specific evidence before the shared XWD/display match gate.

    raw is decoded real RGBA readPixels, bottom-up. previous contains only this
    module's accepted raw frames, in order. This does not replace display capture.
    """
    require(len(previous) < len(FRAME_IDS) and row['id'] == FRAME_IDS[len(previous)], 'Frame sequence')
    name = row['id']; variant = 'baseline' if '-baseline-' in name else 'candidate'
    require(row['asset'] == FIXTURE[variant]['id'] and row['assetSHA256'] == FIXTURE[variant]['sha256'], 'Asset identity')
    require(row['width'] == row['height'] == 512 and len(raw) == 512 * 512 * 4, 'Framebuffer bounds')
    require(row['glError'] == 0 and row['contextLost'] is False, 'GL error/context loss')
    require(hashlib.sha256(raw).hexdigest() == row['pixelSHA256'], 'Readback hash')
    require(all(a == 255 for a in raw[3::4]), 'Opaque framebuffer required')
    isolated = int(name[-1]) if '-layer-' in name else None
    expected = [dict(node=i, name=l['name'], visible=(i + 1 == isolated if isolated else not (name.endswith('-hidden') and i == 4)))
                for i, l in enumerate(FIXTURE['layers'])]
    require(row['visibleNodes'] == expected, 'Exact layer visibility')
    gray = '-gray-' in name
    require(row['rendererInfo']['calls'] > 0 and row['rendererInfo']['triangles'] ==
            (2 if gray else 1540 if isolated else 6160 if name.endswith('-hidden') else 7700), 'Rendered triangle count')
    require(row['materials'] == [dict(number=l['number'], name=l['name'], rgba=l[variant + 'RGBA'],
                                    metalness=0, roughness=0.7200000286102295, doubleSided=True)
                                 for l in FIXTURE['layers']], 'Loaded exported material evidence')
    language = 'zh' if name.endswith('-gray-zh') else 'en'
    require(row['legend']['language'] == language, 'Legend language')
    require(row['legend']['labels'] == [f"{l['number']}  {l[language]}" for l in FIXTURE['layers']], 'Bilingual number mapping')
    require(row['legend']['notice'] == FIXTURE['notices'][language] and row['legend']['context'] == FIXTURE['context'][language], 'Candidate/context notice')
    require(row['legend']['attribution'] == FIXTURE['attribution'], 'Source attribution')
    rect = row['legend']['rect']
    require(0 <= rect['x'] and 0 <= rect['y'] and 300 <= rect['width'] <= 600 and 100 <= rect['height'] <= 650
            and rect['x'] + rect['width'] <= 1280 and rect['y'] + rect['height'] <= 1024, 'Legend outside captured display')
    compare = None
    if variant == 'candidate' and (name.endswith('-oblique') or name.endswith('-transverse') or isolated):
        compare = name.replace('-candidate-', '-baseline-')
    elif name.endswith('-hidden') or name.endswith('-restored'):
        compare = 'esophagus-candidate-transverse'
    changed = None
    if compare:
        source = previous[compare]
        changed = sum(max(abs(raw[i+k] - source[i+k]) for k in range(3)) > 2 for i in range(0, len(raw), 4))
        require(changed == 0 if name.endswith('-restored') else changed >= 64, 'Real framebuffer change/restore check')
    if gray:
        source = previous['esophagus-candidate-transverse']
        require(row['graySourceSHA256'] == hashlib.sha256(source).hexdigest(), 'Grayscale source frame')
        anchors = row['anchors']
        require(len(anchors) == 5, 'Five numbered anchors required')
        excluded = set()
        for i, anchor in enumerate(anchors):
            require(anchor['number'] == i+1 and anchor['hitNode'] == i and anchor['point'] == FIXTURE['layers'][i]['anchor'], 'Raycast anchor-to-layer mapping')
            x, y = anchor['pixel']
            require(isinstance(x, int) and isinstance(y, int) and 32 <= x < 480 and 32 <= y < 480, 'Anchor bounds')
            point = FIXTURE['layers'][i]['anchor']
            require([x, y] == [int((point[0]/.0165+1)*256+.5), int((1+point[2]/.0165)*256+.5)], 'Anchor projection')
            patch = [raw[(yy*512+xx)*4] for yy in range(511-y-10, 511-y+11) for xx in range(x-10, x+11)]
            require(sum(v < 32 for v in patch) >= 20 and sum(v > 220 for v in patch) >= 10, 'Missing visible numbered badge')
            # Fixed 25x25 badges only: no caller-specified pixel masks.
            excluded.update((yy*512+xx) for yy in range(511-y-12, 511-y+13) for xx in range(x-12, x+13))
        for p in range(512*512):
            if p in excluded:
                continue
            j = p*4; lum = int(.2126*source[j] + .7152*source[j+1] + .0722*source[j+2] + .5)
            require(max(abs(raw[j+k] - lum) for k in range(3)) <= 2, 'Grayscale must derive from rendered pixels')
        # A badge must actually change pixels; text/number legibility remains visual review.
        require(sum(any(abs(raw[p*4+k] - raw[p*4]) > 2 for k in (1, 2)) for p in excluded) == 0, 'Grayscale badges must be neutral')
    return {'frame': name, 'independentChangedPixels': changed,
            'displayMatchRequired': True, 'legendActualPixelReviewRequired': True,
            'anatomicalApproval': False, 'clinicalApproval': False}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.input, args.output), indent=2))


def capture_snapshot(row, work, previous, shared):
    """Same display/readback gate as reviewed harness, with extension semantics.

    Called only AFTER the shared global FRAME_IDS sequence check. No browser,
    HTTP, source-host, POST-size, profile or sandbox policy belongs to this module.
    """
    import base64
    import time
    raw = base64.b64decode(row.pop('rgbaBase64'), validate=True)
    own_previous = {k: v for k, v in previous.items() if k.startswith('esophagus-')}
    evidence = validate_frame(row, raw, own_previous)
    corner = raw[:4]
    presence = sum(any(abs(raw[i+k] - corner[k]) > 2 for k in range(3)) for i in range(0, len(raw), 4))
    require(presence > 500, 'Independent readback has no meaningful asset pixels')
    encoded = row.pop('canvasPNG')
    require(encoded.startswith('data:image/png;base64,'), 'Canvas PNG encoding')
    image = base64.b64decode(encoded.split(',', 1)[1], validate=True)
    require(image[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', image[16:24]) == (512, 512), 'Canvas PNG dimensions')
    name = row['id']; (shared.OUT / (name + '.canvas.png')).write_bytes(image)
    time.sleep(.25)
    xwd = (work / 'framebuffer/Xvfb_screen0').read_bytes()
    w, h, rgb = shared.decode_xwd(xwd)
    display = shared.png(w, h, rgb)
    (shared.OUT / (name + '.display.png')).write_bytes(display)
    rect = row['displayRect']; x, y = rect['x'], rect['y']
    require(rect['width'] == rect['height'] == 512 and isinstance(x, int) and isinstance(y, int)
            and 0 <= x <= w-512 and 0 <= y <= h-512, 'Canvas outside display')
    legend_rect = row['legend']['rect']
    require(legend_rect['x'] + legend_rect['width'] <= w and legend_rect['y'] + legend_rect['height'] <= h, 'Legend outside actual display')
    crop = b''.join(rgb[((y+dy)*w+x)*3:((y+dy)*w+x+512)*3] for dy in range(512))
    matched = 0; maximum = 0
    for dy in range(512):
        for dx in range(512):
            a = ((511-dy)*512+dx)*4; b = (dy*512+dx)*3
            delta = max(abs(raw[a+k]-crop[b+k]) for k in range(3))
            maximum = max(maximum, delta); matched += delta <= 3
    fraction = matched/(512*512)
    (shared.OUT / (name + '.display-crop.png')).write_bytes(shared.png(512,512,crop))
    receipt = {'id':name, 'displayMatch':fraction >= .98, 'displayMatchingFraction':fraction,
               'maxDisplayChannelDifference':maximum, 'displaySHA256':hashlib.sha256(display).hexdigest(),
               'xwdSHA256':hashlib.sha256(xwd).hexdigest(), 'independentNonBackgroundPixels':presence, **evidence}
    shared.dump(name + '.json', {**row, 'capture':receipt})
    require(fraction >= .98, 'Display screenshot does not match actual GL readback')
    previous[name] = raw
    return receipt
