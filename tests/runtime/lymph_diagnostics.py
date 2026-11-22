"""Independent receipt gates and a compact, hash-bound diagnostic contact sheet."""
import base64
import hashlib
import html
import math

SAMPLES = [('front', [1, .5, 2]), ('right', [2, .5, -1]),
           ('reverse', [-1, -.5, -2]), ('left', [-2, .5, 1])]
ATTRIBUTION = ('Kristen Browne; Heidi Schlehlein (2022), 3D Reference Organ for Lymph Node, Male v1.2. '
               'https://doi.org/10.48539/HBM299.VVXH.634; CC BY 4.0 '
               'https://creativecommons.org/licenses/by/4.0/. Editorial cutaway and diagnostic rendering are modifications; no endorsement.')
CONTROLS = ('negated-normals', 'reversed-winding')
ORBIT_IDS = [f'lymph-{asset}-orbit-{sample}-{side}'
             for sample, _ in SAMPLES[1:] for asset in ('source', 'candidate')
             for side in ('front', 'back')]
CONTROL_IDS = [f'lymph-control-{kind}{suffix}' for kind in CONTROLS
               for suffix in ('', '-restored')]
NORMAL_IDS = [f'lymph-{asset}-normal-{side}' for asset in ('source', 'candidate')
              for side in ('front', 'back')] + ORBIT_IDS


def require(test, message):
    if not test:
        raise ValueError(message)


def validate_normals(value, fixture):
    require(value['normalPolicy'] == {'zeroEpsilon': 1e-6, 'unitTolerance': 1e-3},
            'Unexpected normal validity policy')
    require(value['orbitSamples'] == [{'id': key, 'direction': direction} for key, direction in SAMPLES],
            'Unexpected fixed camera samples')
    rows = value['normalDiagnostics']
    require(len(rows) == 14, 'Missing loaded normal diagnostics')
    for asset in ('lymph', 'lymphCandidate'):
        selected = [row for row in rows if row['asset'] == asset]
        require(len(selected) == 7 and len({row['mesh'] for row in selected}) == 7,
                'Missing/duplicate mesh diagnostics')
        resource = fixture['lymphCandidate'] if asset == 'lymphCandidate' else next(
            x for x in fixture['resources'] if x.get('id') == asset)
        for row in selected:
            require(row['assetSHA256'] == resource['sha256'], 'Normal report identity mismatch')
            for key in ('referencedVertices', 'triangles', 'nonfinite', 'zero', 'nonunit',
                        'degenerateTriangles', 'opposedNormalCorners'):
                require(type(row[key]) is int and row[key] >= 0, 'Invalid normal diagnostic count')
            require(row['referencedVertices'] > 0 and row['triangles'] > 0, 'Empty normal audit')
            require(row['nonfinite'] == 0 and row['frontSide'] is True, 'Finite/front-side gate failed')
            require(row['zero'] + row['nonunit'] <= row['referencedVertices'], 'Invalid normal totals')
            require(row['degenerateTriangles'] <= row['triangles'] and
                    row['opposedNormalCorners'] <= 3 * row['triangles'], 'Invalid facing totals')
            lo, hi = row['minLength'], row['maxLength']
            require(all(type(x) in (int, float) and math.isfinite(x) for x in (lo, hi))
                    and 0 <= lo <= hi, 'Invalid normal length bounds')
            if asset == 'lymphCandidate':
                require(row['zero'] == row['nonunit'] == 0 and lo > 1e-6 and
                        lo >= 1 - 1e-3 and hi <= 1 + 1e-3, 'Candidate has invalid normals')
    return rows


def validate_frame(row, baseline):
    """Camera and actual final-draw GL culling state, independent of RGB tests."""
    name = row['id']
    if name not in NORMAL_IDS + CONTROL_IDS:
        return
    require(row['asset'] == ('lymph' if name.startswith('lymph-source-') else 'lymphCandidate'),
            'Diagnostic asset mismatch')
    sample = next((key for key, _ in SAMPLES if f'-orbit-{key}-' in name), 'front')
    if name in ORBIT_IDS:
        require(row.get('orbitSample') == sample, 'Wrong orbit label')
    spec, reference = row['camera'], baseline['camera']
    require(all(spec[key] == reference[key] for key in ('min', 'max', 'target', 'orthographicSpan')),
            'Diagnostic bounds/scale differ from source')
    direction = dict(SAMPLES)[sample]
    length = math.sqrt(sum(x*x for x in direction))
    radius = reference['orthographicSpan'] / 2.4
    expected = [t + d / length * radius * 4 for t, d in zip(reference['target'], direction)]
    actual = spec['cameraPosition']
    require(len(actual) == 3 and all(math.isfinite(a) and abs(a-b) <= 1e-9
                                   for a, b in zip(actual, expected)), 'Unexpected orbit camera')
    state = row['culling']
    require(state['enabled'] is True and state['mode'] == 1029, 'Back-face culling not active')
    clockwise, counterclockwise = 2304, 2305
    front = baseline['culling']['frontFace']
    require(front in (clockwise, counterclockwise), 'Unknown GL winding')
    back = name in NORMAL_IDS and name.endswith('-back')
    require(state['frontFace'] == ((clockwise if front == counterclockwise else counterclockwise) if back else front), 'Unexpected GL facing state')
    require(row['diagnostic'] == ('normal-back' if back else 'normal-front'), 'Wrong diagnostic pass')
    if name in CONTROL_IDS:
        kind = next(kind for kind in CONTROLS if name.startswith('lymph-control-' + kind))
        if name.endswith('-restored'):
            require(row.get('restoredAfter') == kind and not row.get('mutatedInMemory'), 'Invalid restoration receipt')
        else:
            require(row.get('negativeControl') == kind and row.get('mutatedInMemory') is True,
                    'Missing renderer mutation receipt')


def control_difference(name, raw, previous, changed):
    if name not in CONTROL_IDS:
        return None
    difference = changed(raw, previous['lymph-candidate-normal-front'])
    require(difference == 0 if name.endswith('-restored') else difference >= 100,
            'Renderer negative control/restoration failed')
    return difference


def contact_sheet(previous, png):
    """20 labelled 256px tiles from independently checked GL readback, no new render."""
    ids = NORMAL_IDS + CONTROL_IDS
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1510" viewBox="0 0 1024 1510">',
             '<rect width="1024" height="1510" fill="white"/>']
    cells = []
    for i, name in enumerate(ids):
        raw = previous[name]
        # OpenGL origin is bottom left. Sample pixel centers at 2:1 reduction.
        rgb = b''.join(raw[((511-y)*512+x)*4:((511-y)*512+x)*4+3]
                       for y in range(1, 512, 2) for x in range(1, 512, 2))
        thumb = png(256, 256, rgb)
        x, y = (i % 4) * 256, (i // 4) * 284
        label = name.removeprefix('lymph-').replace('orbit-', '')
        parts.append(f'<text x="{x+4}" y="{y+16}" font-family="sans-serif" font-size="12">{html.escape(label)}</text>')
        parts.append(f'<image x="{x}" y="{y+24}" width="256" height="256" href="data:image/png;base64,{base64.b64encode(thumb).decode()}"/>')
        cells.append({'frame': name, 'readPixelsSHA256': hashlib.sha256(raw).hexdigest(),
                      'thumbnailSHA256': hashlib.sha256(thumb).hexdigest()})
    for y, text in [(1440, 'Sampled diagnostic evidence only. Source/candidate normal passes; last row deliberately wrong normals/winding and restorations.'),
                    (1460, 'Kristen Browne; Heidi Schlehlein (2022). Lymph Node, Male v1.2. doi.org/10.48539/HBM299.VVXH.634. CC BY 4.0.'),
                    (1480, 'Editorial cutaway and diagnostic render modifications; no endorsement. Vessel identity unresolved. No clinical/anatomical approval.')]:
        parts.append(f'<text x="8" y="{y}" font-family="sans-serif" font-size="12">{html.escape(text)}</text>')
    parts.append('</svg>')
    return '\n'.join(parts).encode(), cells
