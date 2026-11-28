"""Compile package-owned ultrasound progress cards for the offline Gallery."""
import json
import re
from hashlib import sha256
from pathlib import Path

from assetkit.delivery import DeliveryGraph
from assetkit.registry import AssetRegistry, RecordExportRef
from med_assets.artifacts import repo_file, unique_keys, verify_bytes
from med_assets.ultrasound_review import AXES, MAX_AXIS_SCORE, review_images, validate_reviews

REVIEW_ROOT = 'experiments/ultrasound-sweep/development/asset-reviews'
AUDIT = 'records/campaigns/ultrasound-refinement/wave-0/audit-summary.json'


def read_json(path):
    return json.loads(path.read_bytes(), object_pairs_hook=unique_keys)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def prepare_card(repo, manifest_path, card, ref, registry, delivery, destination):
    folder = manifest_path.parent
    package = validate_reviews(repo_file(folder, 'reviews.json'))
    ref_key = f'{ref.asset}@{ref.revision}:{ref.export}'
    selector = card['review']
    matches = [record for record in package['records']
               if record.get('revision') == ref_key
               and all(record.get(key) == selector[key] for key in ('case', 'chapter', 'part'))]
    if len(matches) != 1:
        raise ValueError(f'{manifest_path}: expected one exact workbench review for {ref_key}')
    review = matches[0]
    _, _, export = registry.require_record_export(ref)
    expected = dict(bytes=export.bytes, sha256=export.sha256, triangles=export.triangles)
    raw = repo_file(folder, 'measurements.json').read_bytes()
    if sha256(raw).hexdigest() != package['measurementsSha256']:
        raise ValueError(f'{manifest_path}: measurements differ from the review pin')
    measurements = json.loads(raw, object_pairs_hook=unique_keys)
    if export.format != 'mesh' or review['meshSha256'] != export.sha256 or measurements['export'] != expected:
        raise ValueError(f'{manifest_path}: evidence differs from the exact AssetKit revision')

    adopted = card['adopted']
    if type(adopted) is not bool:
        raise ValueError(f'{manifest_path}: adopted must be a boolean')
    if adopted:
        consumer = delivery.get(f"ultrasound:case:{review['case']}:{review['chapter']}")
        if consumer is None or not any(
            (pin.asset_id, pin.revision_id, pin.export_id, pin.sha256)
            == (ref.asset, ref.revision, ref.export, export.sha256)
            for pin in consumer.runtime_pins
        ):
            raise ValueError(f'{manifest_path}: adopted mesh lacks an exact chapter pin')

    destination.mkdir()
    claim = expected | {'path': export.path}
    mesh = Path(export.path).name
    payload = verify_bytes(repo_file(repo, export.path).read_bytes(), claim)
    (destination / mesh).write_bytes(payload)
    witnesses = {Path(name).name for name in review_images(review)}
    figures = card['figures']
    if not figures:
        raise ValueError(f'{manifest_path}: expected a lead comparison figure')
    for figure in figures:
        name = figure['file']
        if name not in witnesses or Path(name).suffix != '.webp':
            raise ValueError(f'{manifest_path}: figure is outside the selected review: {name}')
        witness = repo_file(folder, name).read_bytes()
        if sha256(witness).hexdigest() != package['evidenceSha256'][name]:
            raise ValueError(f'{manifest_path}: witness differs from the review pin: {name}')
        (destination / name).write_bytes(witness)

    owner = read_json(repo_file(repo, ref.record))
    source, = (row for row in owner['sources'] if row['sourceId'] == card['sourceId'])
    scores = review['scores']
    data = dict(ref=ref_key, mesh=mesh, export=expected, previous=measurements['previousSweep'],
                scores=scores, disposition=review['disposition'], scope=review['note'],
                observations=review['scoreEvidence'], sourceUrl=source['url'], adopted=adopted,
                qualified=all(scores.get(axis) == MAX_AXIS_SCORE for axis in AXES))
    for field in ('cardTitle', 'subtitle', 'revisionTitle', 'revisionLinkLabel',
                  'coordinateFrame', 'sourceLabel', 'detailsLabel', 'figures'):
        data[field] = card[field]
    if 'savedChordContext' in card:
        data['savedChord'] = measurements['savedChord'] | {'context': card['savedChordContext']}
    write_json(destination / 'record.json', data)
    return data


def prepare_ultrasound_progress(repo, destination):
    manifests = []
    slugs = set()
    for path in sorted((repo / REVIEW_ROOT).glob('*/gallery-card.json')):
        path = repo_file(repo, path.relative_to(repo).as_posix())
        card = read_json(path)
        slug = card['slug']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or slug in slugs:
            raise ValueError(f'{path}: invalid or duplicate Ultrasound Development slug: {slug}')
        slugs.add(slug)
        manifests.append((path, card, RecordExportRef.model_validate(card['exportRef'])))

    registry = AssetRegistry.load(repo, include_legacy_adapters=False)
    delivery = DeliveryGraph.load(repo, include_legacy_adapters=False, registry=registry)
    native_exports = {(asset.id, rev.id, exp.id): exp.sha256
                      for asset, rev, exp in registry.iter_exports()}
    governed = {consumer.id for consumer in delivery.consumers if consumer.kind == 'ultrasound-case'
                for pin in consumer.runtime_pins
                if (digest := native_exports.get((pin.asset_id, pin.revision_id, pin.export_id)))
                and pin.sha256 in (None, digest)}
    population = read_json(repo_file(repo, AUDIT))['summary']['population']

    destination.mkdir(parents=True, exist_ok=True)
    adopted = qualified = triangles_saved = bytes_saved = 0
    counted = set()
    cards = []
    for path, manifest, ref in manifests:
        slug = manifest['slug']
        card = prepare_card(repo, path, manifest, ref, registry, delivery, destination / slug)
        cards.append(slug)
        adopted += card['adopted']
        qualified += card['qualified']
        previous, current = card['previous'], card['export']
        replacement = (previous['sha256'], current['sha256'])
        if card['adopted'] and replacement not in counted:
            counted.add(replacement)
            triangles_saved += previous['triangles'] - current['triangles']
            bytes_saved += previous['bytes'] - current['bytes']
    write_json(destination / 'index.json', dict(cards=sorted(cards), campaign=dict(
        chapters=population['chapters'], governedChapters=len(governed),
        reviewed=len(cards), adopted=adopted, qualified=qualified,
        trianglesSaved=triangles_saved, bytesSaved=bytes_saved)))
