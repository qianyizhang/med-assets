"""Compare repository animation with retained canonical samples, not canonical bytes."""
import argparse
import bisect
import hashlib
import json
import struct
from pathlib import Path

from verify_pair import read

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb'
SOURCE_SHA = '6912d439271c3525230a90fe403d586000e6a66ab37f82bf0419604181e52263'
CANONICAL_SHA = '17b26d1459c0fbbbc71d051452c4074d1237683ffe02c1a8021d7ac83583857a'
FIXTURE = 'reviews/runtime/2026-10-23-software-ci-heart-lymph/source-expected-morph-fixture.json'


def compare(source_repo):
    source = source_repo / SOURCE
    doc, payload, digest = read(source)
    assert digest == SOURCE_SHA and source.stat().st_size == 8180224
    fixture_raw = (ROOT / FIXTURE).read_bytes()
    fixture = json.loads(fixture_raw)
    assert fixture['asset']['sha256'] == CANONICAL_SHA
    assert fixture['asset']['bytes'] == 8180452
    contract = json.loads((ROOT / 'ci/glb-runtime-fixture.json').read_text())['heart']
    assert fixture['tracks'] == contract['tracks']
    assert len(doc['animations']) == 1
    animation = doc['animations'][0]
    assert animation['name'] == fixture['animationName']
    assert len(animation['channels']) == len(fixture['tracks']) == 228
    assert len(doc['meshes']) == contract['meshes'] == 247
    assert sum(len(m['primitives']) for m in doc['meshes']) == contract['renderMeshes'] == 251

    def scalar(index):
        accessor = doc['accessors'][index]
        view = doc['bufferViews'][accessor['bufferView']]
        assert accessor['componentType'] == 5126 and accessor['type'] == 'SCALAR'
        assert 'sparse' not in accessor and 'byteStride' not in view
        offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        return struct.unpack_from('<' + 'f' * accessor['count'], payload, offset)

    by_node = {c['target']['node']: c for c in animation['channels']}
    assert set(by_node) == {t['node'] for t in fixture['tracks']}
    errors = []
    for track in fixture['tracks']:
        node = doc['nodes'][track['node']]
        assert node['name'] == track['name']
        assert len(doc['meshes'][node['mesh']]['primitives']) == track['renderPrimitives']
        channel = by_node[track['node']]
        assert channel['target']['path'] == 'weights'
        sampler = animation['samplers'][channel['sampler']]
        assert sampler.get('interpolation', 'LINEAR') == 'LINEAR'
        times, values = scalar(sampler['input']), scalar(sampler['output'])
        assert len(times) == len(values) == 25
        assert times[-1] == fixture['duration']
        for t, expected in zip(fixture['times'], track['values'], strict=True):
            i = max(0, min(len(times) - 2, bisect.bisect_right(times, t) - 1))
            fraction = max(0., min(1., (t - times[i]) / (times[i + 1] - times[i])))
            actual = values[i] + fraction * (values[i + 1] - values[i])
            errors.append(abs(actual - expected))
    assert len(errors) == 912 and max(errors) < 1e-12
    return {
        'result': 'passed-recorded-sample-compatibility-only',
        'source': {'file': SOURCE, 'sha256': digest, 'bytes': source.stat().st_size},
        'canonical': {**fixture['asset'], 'trackedRepositoryPath': None,
                      'sitePath': 'body/3d/assets/motion/heart_animated_clinical.glb',
                      'exactBytesTested': False},
        'fixture': {'file': FIXTURE, 'sha256': hashlib.sha256(fixture_raw).hexdigest()},
        'matchingTrackNamesAndNodeIndices': 228,
        'matchingMeshes': 247, 'matchingRenderPrimitives': 251,
        'comparedTimesSeconds': fixture['times'], 'comparedScalarValues': len(errors),
        'maximumAbsoluteError': max(errors),
        'sourceNodeCount': len(doc['nodes']), 'recordedCanonicalNodeCount': contract['nodes'],
        'scope': 'Names, indices, primitive counts and four recorded morph samples agree. '
                 'This does not prove canonical geometry, fitting transforms, all samples, '
                 'byte identity, clean reimport or replacement applicability. '
                 'assets/heart.glb in the CI fixture is a transient download destination.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Refusing existing receipt')
    result = compare(args.source_repo)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
