"""Project the verified Wave 1B evidence into the offline Gallery build."""
import hashlib
import json

from med_assets.artifacts import verify_bytes
from med_assets.ultrasound_review import validate_reviews

REVIEW = 'experiments/ultrasound-sweep/development/asset-reviews/kidney-wave-1b'
OWNER = 'models/kidney_right_s1233/asset.record.json'


def prepare_ultrasound_progress(repo, destination):
    package = validate_reviews(repo / REVIEW / 'reviews.json')
    review, = package['records']
    record = json.loads((repo / OWNER).read_text())
    revision, = record['revisions']
    export, = revision['exports']
    ref = f"{record['assetId']}@{revision['revisionId']}:{export['id']}"
    raw = (repo / REVIEW / 'measurements.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != package['measurementsSha256']:
        raise ValueError('Ultrasound progress measurements differ from the review pin')
    measurements = json.loads(raw)
    expected = {key: export[key] for key in ('bytes', 'sha256', 'triangles')}
    if review['revision'] != ref or review['meshSha256'] != export['sha256'] or measurements['export'] != expected:
        raise ValueError('Ultrasound progress evidence differs from the exact AssetKit revision')

    destination.mkdir(parents=True, exist_ok=True)
    payload = verify_bytes((repo / export['path']).read_bytes(), export)
    (destination / 'kidney-right.mesh').write_bytes(payload)
    for name in ('matched-surfaces.webp', 'protected-planes.webp', 'live-frame-12.webp'):
        # validate_reviews has checked that each recorded witness resolves inside the package.
        witness = (repo / REVIEW / name).read_bytes()
        if hashlib.sha256(witness).hexdigest() != package['evidenceSha256'][name]:
            raise ValueError(f'Ultrasound progress witness differs from the review pin: {name}')
        (destination / name).write_bytes(witness)

    data = dict(ref=ref, export=expected, previous=measurements['previousSweep'],
                savedChordMm=measurements['savedChord']['millimetres'],
                proposedScores=review['proposedScores'], observations=review['scoreEvidence'],
                source=record['sources'][0])
    (destination / 'record.json').write_text(json.dumps(data, ensure_ascii=False) + '\n')
