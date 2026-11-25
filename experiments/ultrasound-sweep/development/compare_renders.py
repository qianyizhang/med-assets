"""Capture and compare named B-mode frames from assembled study builds."""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory

from PIL import Image

FIELD_KEYS = ('voxelMm', 'probeType', 'fieldShape', 'fieldWidthMm', 'sectorDepthMm')


def read_catalogue(path: Path, variable: str):
    prefix = f'const {variable} = '
    source = path.read_text(encoding='utf-8').strip()
    if not source.startswith(prefix) or not source.endswith(';'):
        raise ValueError(f'Invalid study data in {path}')
    return json.loads(source[len(prefix):-1])


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def read_webp(path: Path) -> tuple[bytes, list[int]]:
    data = path.read_bytes()
    with Image.open(BytesIO(data)) as image:
        if image.format != 'WEBP':
            raise ValueError(f'Expected a WebP image at {path}')
        size = list(image.size)
        image.load()
    return data, size


def frame_rows(study: Path, *, region: str | None = None, sweeps: list[str] | None = None):
    tours = read_catalogue(study / 'abdomen-tours.js', 'abdomenTours')
    refs = read_catalogue(study / 'references.js', 'abdomenReferences')
    for tour in tours:
        slug = tour['id']
        if region and tour.get('bodyRegion', 'Abdomen') != region:
            continue
        if sweeps and slug not in sweeps:
            continue
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug):
            raise ValueError(f'Invalid sweep ID: {slug}')
        asset_root = study / tour['assetRoot']
        poses = read_catalogue(asset_root / 'sweep.js', 'sweep')
        for key in tour['keyframes']:
            frame = key['frame']
            if not isinstance(frame, int) or not 0 <= frame < len(poses):
                raise ValueError(f'Invalid keyframe {slug}/{frame}')
            scan, size = read_webp(asset_root / 'media' / f'scan-{frame:02}.webp')
            section, section_size = read_webp(asset_root / 'media' / f'section-{frame:02}.webp')
            ref = refs[key['referenceId']]
            acquired, reference_size = read_webp(study / ref['path'])
            yield f'{slug}/{frame}', {
                'case': tour.get('case', 's1233'),
                'field': {name: tour.get(name) for name in FIELD_KEYS},
                'pose': poses[frame],
                'crop': 'full uncompressed frame',
                'displaySize': size,
                'sectionSize': section_size,
                'sectionSha256': digest(section),
                'referenceId': key['referenceId'],
                'referenceBinding': ref,
                'referenceSize': reference_size,
                'referenceSha256': digest(acquired),
            }, scan, acquired


def frame_path(key: str) -> str:
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*/[0-9]+', key):
        raise ValueError(f'Invalid comparison key: {key}')
    return key.replace('/', '-') + '.webp'


def dump_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n'


def snapshot(study: Path, destination: Path, region: str | None, sweeps: list[str]) -> int:
    if destination.exists():
        raise ValueError(f'Baseline destination already exists: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temporary:
        stage = Path(temporary) / 'baseline'
        stage.mkdir()
        records = {}
        for key, fixed, scan, _ in frame_rows(study, region=region, sweeps=sweeps):
            (stage / frame_path(key)).write_bytes(scan)
            records[key] = {'fixed': fixed, 'scanSha256': digest(scan)}
        if not records:
            raise ValueError('The selected baseline has no named keyframes.')
        if unknown := set(sweeps) - {key.split('/')[0] for key in records}:
            raise ValueError('Selected sweeps unavailable: ' + ', '.join(sorted(unknown)))
        (stage / 'baseline.json').write_text(dump_json({'version': 1, 'rows': records}), encoding='utf-8')
        stage.rename(destination)
    return len(records)


def compare(baseline: Path, study: Path, before_label: str, after_label: str) -> tuple[int, int]:
    previous = json.loads((baseline / 'baseline.json').read_text(encoding='utf-8'))
    if previous['version'] != 1 or not previous['rows']:
        raise ValueError('Baseline schema or contents are incompatible.')
    labels = [label.strip() for label in (before_label, after_label)]
    if not all(labels) or labels[0] == labels[1]:
        raise ValueError('Supply distinct nonempty labels for the two render runs.')
    before = previous['rows']
    sweeps = sorted({key.split('/')[0] for key in before})
    bundle = study / 'development'
    if not (bundle / 'index.html').is_file():
        raise ValueError(f'Assemble the candidate Development view first: {bundle}')
    marker = bundle / 'comparison.js'
    records = {}
    changed = 0
    with TemporaryDirectory(dir=bundle) as temporary:
        stage = Path(temporary) / 'evidence'
        for group in ('before', 'after', 'reference'):
            (stage / group).mkdir(parents=True)
        for key, fixed, scan, acquired in frame_rows(study, sweeps=sweeps):
            if key not in before:
                continue
            previous_row = before[key]
            if discrepancies := [name for name, value in fixed.items() if value != previous_row['fixed'].get(name)]:
                raise ValueError(f'{key} changed {", ".join(discrepancies)}. Appearance comparison requires fixed inputs.')
            file = frame_path(key)
            baseline_scan, baseline_size = read_webp(baseline / file)
            before_hash = digest(baseline_scan)
            if before_hash != previous_row['scanSha256'] or baseline_size != fixed['displaySize']:
                raise ValueError(f'Baseline render bytes or dimensions changed for {key}.')
            after_hash = digest(scan)
            changed += before_hash != after_hash
            for group, data in [('before', baseline_scan), ('after', scan), ('reference', acquired)]:
                (stage / group / file).write_bytes(data)
            records[key] = {
                'referenceId': fixed['referenceId'],
                'beforeSha256': before_hash,
                'afterSha256': after_hash,
                'changed': before_hash != after_hash,
                'fixed': fixed,
            }
        if missing := before.keys() - records.keys():
            raise ValueError('Candidate keyframes unavailable: ' + ', '.join(sorted(missing)))
        manifest = {'version': 1, 'beforeLabel': labels[0], 'afterLabel': labels[1], 'rows': records}
        # Use an immutable media directory so the browser serves one run even during a rebuild.
        batch_id = digest(dump_json(manifest).encode('utf-8'))[:20]
        batch_dir = bundle / 'comparison' / batch_id
        for key, record in records.items():
            for group in ('before', 'after', 'reference'):
                record[group] = f'comparison/{batch_id}/{group}/{frame_path(key)}'
        (stage / 'manifest.json').write_text(dump_json(manifest), encoding='utf-8')
        batch_dir.parent.mkdir(exist_ok=True)
        if batch_dir.exists():
            for source in stage.rglob('*'):
                if source.is_file() and (batch_dir / source.relative_to(stage)).read_bytes() != source.read_bytes():
                    raise ValueError(f'Existing evidence bytes differ in {batch_dir}.')
        else:
            stage.rename(batch_dir)
        # Publish the manifest only after all evidence files have been verified or installed.
        interface = Path(temporary) / 'comparison.js'
        interface_data = {
            **manifest,
            'rows': {key: {field: row[field] for field in ('referenceId', 'before', 'after', 'reference', 'changed')}
                     for key, row in records.items()},
        }
        interface.write_text('const ultrasoundRenderComparison = ' + dump_json(interface_data).rstrip() + ';\n',
                             encoding='utf-8')
        shutil.move(interface, marker)
    return len(records), changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    capture = commands.add_parser('snapshot', help='Freeze actual scan bytes and comparison identities.')
    capture.add_argument('study', type=Path)
    capture.add_argument('baseline', type=Path)
    capture.add_argument('--region', help='Capture only the named body region, e.g. Abdomen.')
    capture.add_argument('--sweep', action='append', default=[], help='Capture only this sweep ID; repeat for more.')
    pair = commands.add_parser('compare', help='Compare a saved baseline with an assembled candidate.')
    pair.add_argument('baseline', type=Path)
    pair.add_argument('study', type=Path)
    pair.add_argument('--label-before', required=True)
    pair.add_argument('--label-after', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'snapshot':
            total = snapshot(args.study, args.baseline, args.region, args.sweep)
            print(f'Captured {total} named keyframes in {args.baseline}.')
        else:
            total, changed = compare(args.baseline, args.study, args.label_before, args.label_after)
            print(f'Compared {total} named keyframes. {changed} scan files have different bytes.')
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
