"""Restore the Site's pinned viewer inputs and prepare its gallery overlay."""
import argparse
import hashlib
import io
import json
import mimetypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from itertools import chain
from urllib.parse import quote
from urllib.request import urlopen

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE.parents[1] / 'lib'))
sys.path.insert(0, str(SITE.parents[1] / 'transport/tools'))
from delivery_catalog import assets_by_path
from med_assets.artifacts import (
    POINTER_PREFIX, claim_identity, install_verified, parse_pointer, unique_keys, verify_bytes,
)
from med_assets.derivatives import display_derivatives
from med_assets.teaching import CurrentTeaching, check_promotion_journal, locked_store, validate_teaching_axes

DEFAULT_VENDOR = SITE / '.local/viewer-inputs'
DISPLAY_ENCODERS = {'11.3.0': '1.5.0', '12.2.0': '1.6.0'}
TEACHING_REVIEW = 'reviews/teaching-assessments/2026-11-21-library-pilot/assessments.json'


def resources(site: Path):
    return json.loads((site / 'viewer.lock.json').read_text())['resources']


def delivery_by_path(index):
    return assets_by_path(json.loads(index.read_text(), object_pairs_hook=unique_keys))


def validate_display_paths(source, target):
    output_dir = target.parent.parent
    if (source.suffix != '.png' or target.name != source.with_suffix('.webp').name
            or target.parent.name != 'display'
            or source.parent not in (output_dir, output_dir / 'media')):
        raise ValueError(f'Display destination does not match its source: {target}')


def prepare_display_images(repo, by_path, *, offline=True):
    repo = repo.resolve()
    derivatives = display_derivatives(repo)
    if not derivatives:
        raise ValueError('Missing display derivative declarations.')
    pending_by_encoder = {}
    for binding in derivatives.values():
        pillow = binding['recipe'].removeprefix('pillow-webp-')
        if not binding['recipe'].startswith('pillow-webp-') or pillow not in DISPLAY_ENCODERS:
            raise ValueError(f"Unknown display encoder: {binding['recipe']}")
        original, display = binding['source'], binding['output']
        for claim in (original, display):
            published = by_path.get(claim['path'])
            if not published or claim_identity(claim) != (published['sha256'], published['bytes']):
                raise ValueError(f"Delivery differs from the declared display binding: {claim['path']}")
        source, target = repo / original['path'], repo / display['path']
        if display_input(source, target, original, display) is not None:
            pending_by_encoder.setdefault(pillow, []).append([str(source), str(target), original, display])

    for pillow, pending in pending_by_encoder.items():
        if encoder_available(pillow):
            for source, target, original, display in pending:
                generate_display(Path(source), Path(target), original, display, pillow)
            continue
        uv_flags = ['--offline'] if offline else []
        result = subprocess.run(
            ['uv', 'run', *uv_flags, '--no-project', '--python', '3.12',
             '--with', f'Pillow=={pillow}', 'python', '-I', str(Path(__file__).resolve()),
             '--encode-displays', pillow],
            input=json.dumps(pending), text=True,
        )
        if result.returncode:
            raise ValueError(f'Display replay with Pillow {pillow} failed. See the Gallery build recipe.')


def encoder_available(pillow):
    try:
        from PIL import features, __version__
    except ImportError:
        return False
    return (__version__, features.version('webp')) == (pillow, DISPLAY_ENCODERS[pillow])


def display_input(source, target, original, display):
    if source.resolve() != source or target.resolve() != target:
        raise ValueError(f'Display recipe paths must not traverse links: {target}')
    validate_display_paths(source, target)
    raw = source.read_bytes()
    hydrated = not raw.startswith(POINTER_PREFIX)
    if hydrated:
        verify_bytes(raw, original)
    elif parse_pointer(raw) != claim_identity(original):
        raise ValueError(f"Display source identity mismatch for {original['path']}")
    if target.exists():
        verify_bytes(target.read_bytes(), display)
        return None
    return raw if hydrated else None  # A pointer-only checkout can still build the Gallery shell.


def generate_display(source, target, original, display, pillow='11.3.0'):
    raw = display_input(source, target, original, display)
    if raw is None:
        return
    libwebp = DISPLAY_ENCODERS[pillow]
    requirement = f'Preparing review WebPs requires Pillow {pillow} with libwebp {libwebp}.'
    try:
        from PIL import Image, features, __version__
    except ImportError:
        raise ValueError(requirement) from None
    if (__version__, features.version('webp')) != (pillow, libwebp):
        raise ValueError(requirement)
    with Image.open(io.BytesIO(raw)) as image:
        output = io.BytesIO()
        image.convert('RGBA').save(output, format='WEBP', lossless=True, exact=True, method=6)
    encoded = output.getvalue()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent) as staged:
        staged.write(encoded)
        staged.flush()
        os.fchmod(staged.fileno(), source.stat().st_mode & 0o666)
        install_verified(Path(staged.name), target, display)


def restore_viewer(site: Path, output: Path):
    if output.exists() or output.is_symlink():
        raise ValueError('Viewer input directory already exists. Choose a fresh --output.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gallery-viewer-', dir=output.parent) as temporary:
        staged = Path(temporary) / 'inputs'
        for resource in resources(site):
            with urlopen(resource['url'], timeout=30) as response:
                raw = verify_bytes(response.read(resource['bytes'] + 1), resource)
            destination = staged / resource['path']
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        if output.exists() or output.is_symlink():
            raise ValueError('Viewer input directory was created meanwhile.')
        staged.rename(output)


def airway_export_bindings(repo: Path):
    """Read the exact export identities retained by the four Airway studies."""
    for manifest in (
        '82e41092aa325de95435e2488126d7dd70ab971f40ca2a993b95366caa6613d3',  # bronchial r13
        '9b98f353ee334e953d6ba5a81d4d6367337d1ebefab8ce77d4dc0a0d0ee251bb',  # nasal airspace r01
        '8b443938d5dea33128fe52fe7ee664b1801992705704e04703a05714ba110bc8',  # trachea r05
    ):
        record = json.loads((repo / 'transport/manifests' / f'{manifest}.json').read_text())
        yield from (entry for entry in record['objects'] if entry['file'].endswith('.glb'))

    record = json.loads((repo / 'reviews/trachea/2026-10-29-open-airway-r06/build-record.json').read_text())
    for variant in record['variants']:
        yield {**variant, 'file': 'models/trachea/exports/open-airway-r06/' + variant['file']}


def check_delivery_identity(by_path, expected):
    path = expected.get('file', expected.get('path'))
    asset = by_path.get(path)
    if not asset or (asset['sha256'], asset['bytes']) != (expected['sha256'], expected['bytes']):
        raise ValueError(f'Delivery index differs from the pinned review: {path}')


def check_local_delivery(repo: Path, index: Path):
    heart = json.loads((repo / 'reviews/heart_exterior/2026-11-21-static-repack/checks.json').read_text())
    bronchial = 'reviews/bronchial_tree/2026-11-21-distal-simplification-trial'
    geometry = json.loads((repo / bronchial / 'geometry.json').read_text())
    pixels = json.loads((repo / bronchial / 'pixels.json').read_text())
    public = delivery_by_path(index)
    local_index = index.with_name('local-delivery.json')
    local = delivery_by_path(local_index)
    for receipt in json.loads(local_index.read_text())['receipts']:
        path = repo / receipt['path']
        if path.resolve(strict=True) != path or not path.is_relative_to(repo):
            raise ValueError(f'Invalid release receipt path: {path}')
        verify_bytes(path.read_bytes(), receipt)
    check_delivery_identity(public, {
        **heart['baseline'], 'path': 'heart/exterior-presentation-r01/exports/static-opaque-exterior.glb',
    })
    check_delivery_identity(local, {
        **heart['candidate'], 'path': 'heart/exterior-presentation-r02/exports/static-opaque-exterior-repacked.glb',
    })
    bronchial_exports = 'models/bronchial_tree/exports'
    check_delivery_identity(public, {
        **geometry['original'], 'path': f'{bronchial_exports}/authored-central-fairing-r13/bronchial_central_fairing.glb',
    })
    check_delivery_identity(local, {
        **geometry['updated'], 'path': f'{bronchial_exports}/distal-sampling-r14/bronchial_distal_sampling.glb',
    })
    sheet = f'{bronchial}/evidence/close.webp'
    if local.get(sheet, {}).get('sha256') != pixels['close']['sheetSha256']:
        raise ValueError(f'Delivery index differs from the pinned review: {sheet}')
    public_hashes = {asset['sha256'] for asset in public.values()}
    for path, asset in local.items():
        if path in public or asset['sha256'] in public_hashes:
            raise ValueError(f'Local delivery also appears in the public index: {path}')


def check_review_delivery(repo: Path, index: Path):
    by_path = delivery_by_path(index)
    review = json.loads((repo / 'reviews/adrenals/2026-10-23-bp3d-bounded-migration/bounded-record.json').read_text())
    witnesses = [image for image in review['evidence'] if image['reviewPhase'] == 'candidate']
    salivary = json.loads((repo / 'reviews/salivary_glands/2026-10-26-native-scoped-r02/decision.json').read_text())
    for expected in chain([review['artifact']], witnesses, salivary['media'], airway_export_bindings(repo)):
        check_delivery_identity(by_path, expected)
    folder = 'models/lymph-collecting-routes/source-context-refined-r01'
    lymph = json.loads((repo / folder / 'projection-binding.json').read_text())
    for lang, digest in lymph['input_plate_sha256'].items():
        path = f'{folder}/comparison-{lang}.png'
        if by_path.get(path, {}).get('sha256') != digest:
            raise ValueError(f'Delivery index differs from the retained lymph plate: {path}')
    skeletal = json.loads((repo / 'reviews/skeletal_teaching/2026-10-23/record.json').read_text())
    for study in skeletal['studies']:
        path = study['file']
        asset = by_path.get(path, {})
        if (asset.get('sha256'), asset.get('bytes')) != (study['sha256'], study['bytes']):
            raise ValueError(f'Delivery index differs from the retained skeletal export: {path}')
        for plate in study['evidence']:
            path = plate['file']
            if (plate['sourceSha256'] != study['sha256'] or
                    by_path.get(path, {}).get('sha256') != plate['sha256']):
                raise ValueError(f'Delivery index or export binding differs for the retained skeletal plate: {path}')


def prepare_gallery(site: Path, inputs: Path, target: Path, *, offline=True):
    repo = site.parents[1]
    index = target.parent / 'assets/delivery-index.json'
    check_review_delivery(repo, index)
    check_local_delivery(repo, index)
    for resource in resources(site):
        name = Path(resource['path'])
        try:
            raw = (inputs / name).read_bytes()
        except FileNotFoundError as error:
            raise ValueError(
                f'Missing viewer input {name}. Run tools/gallery_runtime.py to restore the pinned inputs.'
            ) from error
        raw = verify_bytes(raw, resource)
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if 'examples' in name.parts:
            module = os.path.relpath(target / 'vendor/build/three.module.js', destination.parent)
            raw = raw.replace(b"from 'three';", f"from '{module}';".encode())
        destination.write_bytes(raw)
    shutil.copyfile(repo / 'docs/guides/asset-quality.md', target / 'rubric.md')
    for lesson, config, destination in (
        ('right-arm-parts', 'arm-lesson-layers.json', 'arm-lesson-layers.json'),
        ('salivary-practice', 'views.json', 'salivary-views.json'),
    ):
        owner = repo / 'lessons' / lesson
        shutil.copyfile(owner / config, target / destination)
        plates = sorted((owner / 'plates').glob('*.webp'))
        if len(plates) != 6:
            raise ValueError(f'Missing lesson layers or answers: {lesson}')
        for plate in plates:
            with plate.open('rb') as stream:
                if stream.read(12)[8:] != b'WEBP':
                    raise ValueError(f'Expected hydrated lesson plate: {plate.name}')
            shutil.copyfile(plate, target / 'part-images' / plate.name)
    uv_flags = ['--offline'] if offline else []
    subprocess.run(['uv', 'run', *uv_flags, 'python', '-m', 'assetkit.body_systems'],
                   cwd=repo, check=True)
    system_index = repo / 'lessons/body-systems/display/index.json'
    stops = json.loads((repo / 'lessons/body-systems/reviewed-stops.json').read_text())
    systems = json.loads(system_index.read_text())
    if hashlib.sha256(system_index.read_bytes()).hexdigest() != stops['displayIndexSha256']:
        raise ValueError('Body Systems teaching views changed since the collection review')
    checks = {c['system']: c for c in stops['stops']}
    if set(checks) != {s['id'] for s in systems} or len(checks) != len(stops['stops']):
        raise ValueError('Missing or duplicate Body Systems check')
    for system in systems:
        check = checks[system['id']]
        if (check['detail'] not in {p['id'] for p in system['plates'] if p['kind'] == 'detail'}
                or check['status'] not in ('passed', 'blocked')):
            raise ValueError(f"Unknown reviewed stop in {system['id']}")
        system['check'] = check
    deliveries = delivery_by_path(index)
    plate_paths = {frame['path'] for system in systems
                   for plate in system['plates'] for frame in plate['frames']}
    for path in sorted(plate_paths):
        if path not in deliveries:
            raise ValueError(f'Body Systems display has no Gallery delivery: {path}')
        verify_bytes((repo / path).read_bytes(), {**deliveries[path], 'path': path})
    (target / 'body-systems.json').write_text(json.dumps(systems, ensure_ascii=False))
    prepare_display_images(repo, deliveries, offline=offline)
    teaching = target / 'teaching-inputs'
    teaching.mkdir()
    prepare_teaching_assessments(repo, index, teaching)
    prepare_ovary_lesson(repo, teaching)
    ultrasound_pose = repo / 'lessons/ultrasound-anatomy/abdomen-gallbladder.json'
    locator = json.loads(ultrasound_pose.read_text())['locator']
    locator_path = repo / locator['path']
    if not locator_path.is_relative_to(repo) or locator_path.resolve(strict=True) != locator_path:
        raise ValueError('Invalid ultrasound locator path.')
    atlas = locator_path.read_bytes()
    if hashlib.sha256(atlas).hexdigest() != locator['sha256']:
        raise ValueError('The ultrasound locator differs from its pinned atlas source.')
    (teaching / 'ultrasound-body-locator.svg').write_bytes(atlas)
    shutil.copyfile(ultrasound_pose, teaching / 'ultrasound-abdomen.json')
    shutil.copyfile(repo / 'reviews/teaching-assessments/use-case-checks.json', teaching / 'use-case-checks.json')
    shutil.copyfile(repo / 'models/lymph-collecting-routes/source-context-refined-r01/projection-binding.json',
                    teaching / 'lymph-projection.json')
    readability = json.loads((repo / 'reviews/testis_pathway/2026-10-29-r02/readability.json').read_text())
    for result in readability['results']:
        display = result['artifacts']['display']
        original = repo / display['current']
        raw = verify_bytes(original.read_bytes(), {'path': display['current'], 'bytes': display['bytes'],
                                                   'sha256': display['current_sha256']})
        (teaching / original.name).write_bytes(raw)
    prepare_retained_lesson(repo, teaching, 'arch-identification', ('ui.mjs', 'plate.mjs'))
    shutil.copyfile(repo / 'docs/dental-atlas/set-coverage.json', teaching / 'arch-identification/set-coverage.json')
    prepare_retained_lesson(repo, teaching, 'kidney-location', ('source.js', 'view.js'))
    dental_stills = {
        'lessons/dental-layer-controls/media/control-review-sheet.jpg': 'control-review-sheet.jpg',
        'lessons/dental-animation/fdi31-layer-reveal/source-pose.jpg': 'source-pose.jpg',
        'lessons/dental-animation/fdi31-layer-reveal/editorial-reveal.jpg': 'editorial-reveal.jpg',
        'lessons/dental-animation/caries-restoration/poster.svg': 'caries-poster.svg',
        'lessons/dental-animation/periodontal-cleaning/poster.svg': 'periodontal-poster.svg',
    }
    for original, name in dental_stills.items():
        shutil.copyfile(repo / original, teaching / name)
    prepare_archive_films(repo, teaching)


def prepare_teaching_assessments(repo, index, teaching):
    owners = sorted((repo / 'reviews').glob('*/*/teaching-assessment.json'))
    by_path = delivery_by_path(index)
    assessments = {}
    for file in (repo / TEACHING_REVIEW, *owners):
        review = json.loads(file.read_text())
        if review['schemaVersion'] != 1:
            raise ValueError(f'Unsupported teaching assessment schema: {file.relative_to(repo)}')
        metadata = {key: review[key] for key in ('evaluator', 'date', 'rubric')}
        for assessment in review['assessments']:
            route = assessment['route']
            if route in assessments:
                raise ValueError(f'Duplicate teaching assessment for {route}')
            validate_teaching_axes(assessment, route)
            if not assessment['views']:
                raise ValueError(f'Missing reviewed views for {route}')
            for evidence in (assessment['export'], *assessment['views']):
                check_delivery_identity(by_path, evidence)
            assessments[route] = {**assessment, **metadata}
    campaign = prepare_campaign_reviews(repo, index)
    output = {'assessments': list(assessments.values()), 'campaign': campaign}
    (teaching / 'teaching-assessments.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')


def prepare_campaign_reviews(repo, index):
    """Attach delivery metadata to the accepted teaching reviews."""
    with locked_store(repo.resolve()):
        check_promotion_journal(repo)
        current = CurrentTeaching(repo)
        current.validate_current()
        gallery = tuple(current.gallery())
        maintained_files = current.maintained_exports()
    deliveries = {**delivery_by_path(index), **delivery_by_path(index.with_name('local-delivery.json'))}
    root = repo.resolve()
    result = {}
    evidence = {}

    def local_file(relative):
        path = (root / relative).resolve(strict=True)
        if path != root / relative or not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'Invalid assessment evidence path: {relative}')
        if relative not in evidence:
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            kind = mimetypes.guess_type(path.name)[0]
            media_type = kind if kind in ('image/webp', 'image/png', 'image/jpeg', 'application/json') else 'text/plain'
            evidence[relative] = {'path': relative, 'bytes': len(raw), 'sha256': digest,
                                  'mediaType': media_type, 'url': f'/review-evidence/{digest}/{quote(path.name)}'}
        return evidence[relative]

    for accepted in gallery:
        row = accepted.row
        export = row['export']
        path = export['path']
        if (row.get('route') or row.get('target') or path in current.selections) and path not in deliveries:
            source = (root / path).resolve(strict=True)
            if source != root / path or not source.is_relative_to(root) or path.split('/')[0] not in ('models', 'body', 'heart', 'assemblies', 'lessons'):
                raise ValueError(f'Invalid maintained teaching export: {path}')
            with source.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            check_delivery_identity({path: {'sha256': actual, 'bytes': source.stat().st_size}}, export)
        else:
            check_delivery_identity(deliveries, export)
        views = []
        for view in row['views']:
            entry = local_file(view['path'])
            check_delivery_identity({view['path']: entry}, view)
            views.append({**view, **entry})
        sources = []
        for source in row['sources']:
            if 'path' in source:
                entry = local_file(source['path'].split('#', 1)[0])
                sources.append({**source, **entry})
            elif source.get('url', '').startswith('https://'):
                sources.append(source)
            else:
                raise ValueError(f'Missing source reference for {path}')
        if path in current.selections:
            selection = current.selections[path]
            maintained = {'collection': selection.collection, 'family': selection.family,
                          'familyId': selection.family_id, 'taskId': selection.task_id}
            if selection.shared_owner:
                maintained.update(label=selection.label, sharedOwner=selection.shared_owner)
            row = {**row, 'maintained': maintained}
        refinement = row.get('refinement')
        candidate = refinement.get('candidate') if refinement else None
        if candidate and candidate.get('download'):
            digest = candidate['sha256']
            canonical = maintained_files.get((digest, candidate['bytes']))
            if canonical:
                candidate = {**candidate, 'path': canonical, 'name': Path(canonical).name}
            else:
                expected_store = f'.artifacts/teaching-refinements/candidates/{digest}.glb'
                if candidate['path'] != expected_store:
                    check_delivery_identity(deliveries, candidate)
            name = candidate['name']
            if (not name.endswith('.glb') or not all(c.isascii() and (c.isalnum() or c in '._-') for c in name)):
                raise ValueError(f'Invalid recipe-built download: {name}')
            recipe = local_file(candidate['recipe'])
            download = {**candidate, 'url': f'/assets/{digest}/{name}', 'recipeUrl': recipe['url']}
            row = {**row, 'releaseEvidence': [recipe], 'refinement': {**refinement, 'candidate': download}}
        result[path] = {**row, **accepted.attribution, 'taskId': accepted.task_id, 'sources': sources, 'views': views}
    return list(result.values())


def prepare_ovary_lesson(repo, teaching):
    owner = 'ovary-tubal-context'
    lesson = json.loads((repo / 'lessons' / owner / 'lesson.json').read_text())
    localization = lesson['localization']
    plate = localization['plate']
    review = json.loads((repo / localization['review']).read_text())
    assessment = next((row for row in review['assessments']
                       if row['export']['path'] == localization['export']), None)
    if not assessment or assessment['teachingView'] != plate['path']:
        raise ValueError(f"Ovary close-ups do not match the reviewed teaching view: {plate['path']}")
    view = next(row for row in assessment['views'] if row['path'] == plate['path'])
    plate.update(width=view['width'], height=view['height'])
    target = teaching / owner
    target.mkdir()
    (target / 'ovary-teaching.webp').write_bytes(verify_bytes((repo / plate['path']).read_bytes(), view))
    (target / 'lesson.json').write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + '\n')


def prepare_retained_lesson(repo, teaching, name, modules):
    owner = repo / 'lessons' / name
    target = teaching / name
    target.mkdir()
    for file in ('index.html', *modules):
        shutil.copyfile(owner / file, target / file)
    # Read the original stylesheet as text and install it only within the lesson's shadow root.
    shutil.copyfile(owner / 'style.css', target / 'style.css.txt')


def prepare_archive_films(repo, teaching):
    image26 = repo / 'experiments/dental-image26'
    story_file = image26 / 'stories.json'
    stories = json.loads(story_file.read_text())['stories']
    results = 'experiments/dental-image26/results/'
    paths = [results + 'dental-condition-to-treatment.mp4']
    paths.extend(results + 'films/' + story['id'] + '.mp4' for story in stories)
    from transport.tools.restore_collection import checksum_members
    collection = json.loads((repo / 'transport/collection-archives.json').read_text())['teaching-media']
    members = checksum_members(repo, collection)
    (teaching / 'image26-media.json').write_text(json.dumps([
        {'path': path, 'name': Path(path).name, 'sha256': members[path]['sha256'],
         'bytes': members[path]['bytes'], 'mediaType': 'video/mp4'} for path in paths
    ], indent=2) + '\n')
    shutil.copyfile(story_file, teaching / 'image26-stories.json')
    shutil.copyfile(image26 / 'audio/narration.srt', teaching / 'image26-narration.srt')
    shutil.copyfile(repo / 'experiments/dental-video-treatments/audio/narration.srt',
                    teaching / 'treatments-narration.srt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_VENDOR)
    parser.add_argument('--encode-displays', choices=DISPLAY_ENCODERS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.encode_displays:
        try:
            for source, target, original, display in json.load(sys.stdin):
                generate_display(Path(source), Path(target), original, display, args.encode_displays)
        except (ValueError, OSError) as error:
            parser.exit(1, f'{error}\n')
        sys.exit()
    try:
        restore_viewer(SITE, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Viewer setup failed: {error}\n')
    print(f'Restored pinned Anatomy Gallery viewer inputs: {args.output}')
