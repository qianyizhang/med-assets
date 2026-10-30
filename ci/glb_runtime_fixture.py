"""Assemble the runtime contract from its retained, hash-pinned morph evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(root=ROOT):
    fixture = json.loads((root / 'ci/glb-runtime-fixture.json').read_text())
    heart = fixture['heart']
    if 'tracks' in heart:
        raise ValueError('Keep morph tracks only in the retained source')
    source = heart['tracksSource']
    path = (root / source['file']).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Morph expectations must be inside the repository')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != source['sha256']:
        raise ValueError('Morph expectation SHA-256 mismatch')
    expected = json.loads(raw)
    resource = next(item for item in fixture['resources'] if item.get('id') == 'heart')
    for key in ('sha256', 'bytes'):
        if expected['asset'][key] != resource[key]:
            raise ValueError('Morph expectations belong to a different heart asset')
    for key in ('animationName', 'duration', 'times'):
        if expected[key] != heart[key]:
            raise ValueError('Morph animation contract mismatch: ' + key)
    tracks = expected['tracks']
    if len(tracks) != heart['channels'] or sum(t['renderPrimitives'] for t in tracks) != heart['morphRenderMeshes']:
        raise ValueError('Morph channel/primitive count mismatch')
    # Keep the served JSON shape and field order, including all sampled values.
    fixture['heart'] = {('tracks' if key == 'tracksSource' else key):
                        (tracks if key == 'tracksSource' else value)
                        for key, value in heart.items()}
    return fixture
