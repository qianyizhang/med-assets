"""Apply only the camera-inertia fix to exact canonical or lifecycle-v2 source."""
from pathlib import Path
import argparse
import hashlib
import json

SOURCE_HASHES = {
    '9214093398033ab75beeec8c273d1f85a28408ee6096f3fe0bb91723ecc6f80b': 'canonical-v40',
    'd11cffd8a69ee32cc70ccd6712064b5e5f4c8c0f9f710614453007c640461b1e': 'lifecycle-v2',
}
MODULE = 'camera-reset.mjs'
LIFECYCLE_SHA = '2e2b67adb61140feefa64ffae50207258aa507bb555ebe8549c6b7b0989e8969'


def patched(raw):
    if hashlib.sha256(raw).hexdigest() not in SOURCE_HASHES:
        raise ValueError('candidate.js does not match an accepted exact source')
    text = raw.decode()
    for old, new in (
        ('camera.zoom=1;camera.position.fromArray(v.position_three);',
         'clearPendingOrbit(controls);camera.zoom=1;camera.position.fromArray(v.position_three);'),
        ('const d=Math.max(size.x,size.y,size.z,.001)*2;',
         'clearPendingOrbit(controls);const d=Math.max(size.x,size.y,size.z,.001)*2;'),
    ):
        if text.count(old) != 1:
            raise ValueError('Expected unique camera integration anchor: ' + old)
        text = text.replace(old, new, 1)
    return ("import {clearPendingOrbit} from './camera-reset.mjs';\n" + text).encode()


def apply(directory):
    target = Path(directory)
    source = target / 'candidate.js'
    raw = source.read_bytes()
    result = patched(raw)
    if SOURCE_HASHES[hashlib.sha256(raw).hexdigest()] == 'lifecycle-v2':
        dependency = target / 'viewer-lifecycle.mjs'
        if not dependency.is_file() or hashlib.sha256(dependency.read_bytes()).hexdigest() != LIFECYCLE_SHA:
            raise ValueError('Exact lifecycle-v2 module required for composed source')
    module = target / MODULE
    if module.exists():
        raise ValueError('Camera reset module already exists; use a fresh source copy')
    payload = (Path(__file__).parent / MODULE).read_bytes()
    module.write_bytes(payload)
    source.write_bytes(result)
    return {name: hashlib.sha256((target / name).read_bytes()).hexdigest()
            for name in ('candidate.js', MODULE)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review_dir', type=Path)
    print(json.dumps(apply(parser.parse_args().review_dir), indent=2))
