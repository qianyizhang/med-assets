#!/usr/bin/env python3
"""Local render E2E: exact input, native pixels, matched views and teaching omission.

This verifies the review deliverable, not whether its anatomy is correct.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = '457b08b1edab5fc39db3b49e09635091721847e06262b7cb937fd006223c6750'
OMITTED = {'VH_M_ciliary_body_R', 'VH_M_ciliary_muscle_R', 'VH_M_ciliary_processes_R',
           'VH_M_suspensory_ligament_of_lens_R'}
TEACHING = {'VH_M_cornea_R', 'VH_M_iris_R', 'VH_M_lens_R'}
PAIRS = [('posterior-detail-full', 'posterior-detail-isolated'),
         ('oblique-detail-full', 'oblique-detail-isolated'),
         ('anterior-order-full', 'anterior-order-three-structures'),
         ('corneal-profile-full', 'corneal-profile-three-structures')]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check(output):
    receipt = json.loads((output / 'render-manifest.json').read_text())
    require(receipt['artifact']['sha256'] == EXPECTED, 'wrong reviewed artifact')
    require(receipt['artifact']['file'] == 'models/eye_anterior_segment/exports/hra-v1.3-r01/anterior_segment.glb',
            'wrong artifact path')
    require(hashlib.sha256((ROOT / receipt['artifact']['file']).read_bytes()).hexdigest() == EXPECTED,
            'local artifact missing or changed')
    require(receipt['geometryAndMaterialsEdited'] is False, 'unexpected authoring changes')
    require(receipt['renderer'] == '4.3.2' and receipt['resolution'] == [1000, 1000],
            'renderer or resolution mismatch')
    rows = receipt['views']
    by_name = {r['view']: r for r in rows}
    require(len(rows) == len(by_name) == 9, 'missing or duplicate views')
    for row in rows:
        require(row['file'] == row['view'] + '.png' and '/' not in row['file'], 'unexpected output filename')
        path = output / row['file']
        require(path.stat().st_size == row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'],
                'pixel-file hash or size mismatch: ' + row['view'])
        with Image.open(path) as image:
            require(image.size == (1000, 1000), 'not native 1000px output')
            require(max(ImageStat.Stat(image.convert('RGB')).stddev) > 8, 'blank/near-blank render')
        visible, hidden = set(row['visibleNodes']), set(row['hiddenNodes'])
        require(visible.isdisjoint(hidden) and visible | hidden == OMITTED | TEACHING, 'visibility partition mismatch')
    for full, hidden in PAIRS:
        a, b = by_name[full], by_name[hidden]
        require(all(a[key] == b[key] for key in ['cameraLocation', 'target', 'orthoScaleM']),
                'unmatched camera: ' + full)
        require(a['sha256'] != b['sha256'], 'visibility change did not change pixels')
    for name in ['anterior-order-three-structures', 'corneal-profile-three-structures']:
        row = by_name[name]
        require(set(row['hiddenNodes']) == OMITTED and set(row['visibleNodes']) == TEACHING,
                'unsupported ciliary/zonular geometry not omitted from teaching view')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    check(parser.parse_args().output)
    print('PASS local render E2E: nine nonblank native PNGs, exact hashes, four matched pairs, '
          'unsupported geometry omitted from both teaching views. No anatomy/runtime certification.')
