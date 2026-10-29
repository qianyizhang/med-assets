"""Check hydrated package/source/pixel identities; no geometry or runtime claim."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'assemblies/hypothalamus-pituitary/teaching-stalk-r01'
REVIEW = ROOT / 'reviews/hypothalamus_pituitary/2026-10-29-teaching-stalk-r01'
EXPECTED = '31ddd537a8aa3ac7dcd75a9a9789132fb10bcfeccb4149e14443d845fd7fb373'


def verify(path, size, sha):
    raw = path.read_bytes()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError(f'Identity mismatch or unresolved LFS pointer: {path.relative_to(ROOT)}')


def main():
    build = json.loads((REVIEW / 'build-record.json').read_text())
    artifact = build['artifact']
    if artifact != {'file': 'hypothalamus-pituitary-teaching.glb', 'bytes': 130668, 'sha256': EXPECTED}:
        raise ValueError('Unexpected reviewed candidate identity')
    verify(PACKAGE / artifact['file'], artifact['bytes'], EXPECTED)
    for source in build['sources'].values():
        verify(ROOT / source['file'], source['bytes'], source['sha256'])
    bindings = json.loads((REVIEW / 'renders/raster-bindings.json').read_text())
    expected_names = {f'{version}-{view}.png' for version in ('original', 'updated')
                      for view in ('whole', 'junction', 'junction-side')}
    if len(bindings) != 6 or {b['file'] for b in bindings} != expected_names:
        raise ValueError('Incomplete matched evidence')
    source_shas = {s['sha256'] for s in build['sources'].values()}
    for binding in bindings:
        verify(REVIEW / 'renders' / binding['file'], binding['bytes'], binding['sha256'])
        expected = {EXPECTED} if binding['file'].startswith('updated-') else source_shas
        if {a['sha256'] for a in binding['artifacts']} != expected:
            raise ValueError('Image bound to unexpected model')
    export = json.loads((REVIEW / 'export-check.json').read_text())
    if export['artifact_sha256'] != EXPECTED or any(export[k] for k in
            ('edge_incidence_not_two', 'zero_area_faces', 'nonadjacent_self_contacts')):
        raise ValueError('Export receipt is not passing for this candidate')
    print('PASS: exact candidate, two retained inputs and six bound PNGs; export receipt matches. No runtime claim.')


if __name__ == '__main__':
    main()
