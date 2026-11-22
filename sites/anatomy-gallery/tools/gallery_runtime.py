"""Restore the Site's pinned viewer inputs and prepare its gallery overlay."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from itertools import chain
from urllib.request import urlopen

SITE = Path(__file__).resolve().parents[1]
DEFAULT_VENDOR = SITE / '.local/viewer-inputs'
TEACHING_REVIEW = 'reviews/teaching-assessments/2026-11-21-library-pilot/assessments.json'
DISPLAY_ENCODERS = {'11.3.0': '1.5.0', '12.2.0': '1.6.0'}


def resources(site: Path):
    return json.loads((site / 'viewer.lock.json').read_text())['resources']


def verified(resource, raw: bytes) -> bytes:
    if len(raw) != resource['bytes'] or hashlib.sha256(raw).hexdigest() != resource['sha256']:
        raise ValueError(f"File differs from its recorded size or SHA-256: {resource['path']}")
    return raw


def prepare_display_images(repo, site, by_path):
    repo = repo.resolve()
    targets = set()
    recipe = json.loads((site / 'display-images.json').read_text())
    for pillow, bindings in recipe.items():
        if pillow not in DISPLAY_ENCODERS:
            raise ValueError(f'Unknown display encoder: {pillow}')
        pending = []
        for source_path, target_path in bindings:
            source, target = repo / source_path, repo / target_path
            if not source.is_relative_to(repo) or not target.is_relative_to(repo) or target in targets:
                raise ValueError(f'Invalid or duplicate display binding: {target_path}')
            targets.add(target)
            original = {**by_path[source_path], 'path': source_path}
            display = {**by_path[target_path], 'path': target_path}
            if pillow == '11.3.0':
                generate_display(source, target, original, display, pillow)
            elif display_input(source, target, original, display) is not None:
                pending.append([str(source), str(target), original, display])
        if pending:
            result = subprocess.run(
                ['uv', 'run', '--offline', '--no-project', '--python', '3.12',
                 '--with', f'Pillow=={pillow}', 'python', '-I', str(Path(__file__).resolve()),
                 '--encode-displays', pillow],
                input=json.dumps(pending), text=True,
            )
            if result.returncode:
                raise ValueError(f'Display replay with Pillow {pillow} failed. See the Gallery build recipe.')


def display_input(source, target, original, display):
    if source.resolve() != source or target.resolve() != target:
        raise ValueError(f'Display recipe paths must not traverse links: {target}')
    output_dir = target.parent.parent
    if (source.suffix != '.png' or target.name != source.with_suffix('.webp').name
            or target.parent.name != 'display'
            or source.parent not in (output_dir, output_dir / 'media')):
        raise ValueError(f'Display destination does not match its source: {target}')
    raw = source.read_bytes()
    pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{original['sha256']}\nsize {original['bytes']}\n"
    hydrated = raw != pointer.encode()
    if hydrated:
        verified(original, raw)
    if target.exists():
        verified(display, target.read_bytes())
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
    encoded = verified(display, output.getvalue())
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent) as staged:
        staged.write(encoded)
        staged.flush()
        os.fchmod(staged.fileno(), source.stat().st_mode & 0o666)
        try:
            os.link(staged.name, target)
        except FileExistsError:
            verified(display, target.read_bytes())


def restore_viewer(site: Path, output: Path):
    if output.exists() or output.is_symlink():
        raise ValueError('Viewer input directory already exists. Choose a fresh --output.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gallery-viewer-', dir=output.parent) as temporary:
        staged = Path(temporary) / 'inputs'
        for resource in resources(site):
            with urlopen(resource['url'], timeout=30) as response:
                raw = verified(resource, response.read(resource['bytes'] + 1))
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


def delivery_by_path(index: Path):
    return {
        path: asset for asset in json.loads(index.read_text())['assets']
        for path in asset.get('paths', [asset.get('path')])
    }


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
    local = delivery_by_path(index.with_name('local-delivery.json'))
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


def prepare_gallery(site: Path, inputs: Path, target: Path):
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
        raw = verified(resource, raw)
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if 'examples' in name.parts:
            module = os.path.relpath(target / 'vendor/build/three.module.js', destination.parent)
            raw = raw.replace(b"from 'three';", f"from '{module}';".encode())
        destination.write_bytes(raw)
    shutil.copyfile(repo / 'docs/guides/asset-quality.md', target / 'rubric.md')
    shutil.copyfile(repo / 'lessons/body-systems/display/index.json', target / 'body-systems.json')
    teaching = target / 'teaching-inputs'
    teaching.mkdir()
    prepare_teaching_assessments(repo, index, teaching)
    shutil.copyfile(repo / 'models/lymph-collecting-routes/source-context-refined-r01/projection-binding.json',
                    teaching / 'lymph-projection.json')
    readability = json.loads((repo / 'reviews/testis_pathway/2026-10-29-r02/readability.json').read_text())
    for result in readability['results']:
        display = result['artifacts']['display']
        original = repo / display['current']
        raw = verified({'path': display['current'], 'bytes': display['bytes'],
                        'sha256': display['current_sha256']}, original.read_bytes())
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
    prepare_display_images(repo, site, delivery_by_path(index))


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
            if not assessment['task'].strip() or not assessment['sources'] or not assessment['views']:
                raise ValueError(f'Missing teaching task or evidence for {route}')
            axes = assessment['axes']
            if len(axes) != 4:
                raise ValueError(f'Expected four teaching assessment axes for {route}')
            for axis in axes:
                score = axis['score']
                if score is not None and (type(score) is not int or not 0 <= score <= 4):
                    raise ValueError(f'Invalid teaching assessment score for {route}')
                if not isinstance(axis['observation'], str) or not axis['observation'].strip():
                    raise ValueError(f'Missing teaching assessment observation for {route}')
            for evidence in (assessment['export'], *assessment['views']):
                check_delivery_identity(by_path, evidence)
            assessments[route] = {**assessment, **metadata}
    output = {'assessments': list(assessments.values())}
    (teaching / 'teaching-assessments.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')


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
    members = {}
    for line in (repo / 'sites/body-systems-survey/backup-sha256.txt').read_text().splitlines():
        digest, path = line.split('  ', 1)
        members[path] = digest
    (teaching / 'image26-media.json').write_text(json.dumps([
        {'path': path, 'name': Path(path).name, 'sha256': members[path]} for path in paths
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
