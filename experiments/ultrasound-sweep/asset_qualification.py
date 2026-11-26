"""Assemble the Development workbench from the teaching delivery and retained reviews."""
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
RUBRIC = HERE.parents[1] / 'docs/guides/asset-quality.md'


def recipe_hashes(destination, owners, records):
    """Invalidate scores if the modeled family, a fitted surface or the rubric changes."""
    hashes = {}

    def digest(paths):
        for path in paths:
            if path not in hashes:
                hashes[path] = sha256(path.read_bytes()).hexdigest()
        return sorted((str(path.relative_to(destination)), hashes[path]) for path in paths)

    regional_meshes = {}
    for path in destination.rglob('*.mesh'):
        relative = path.relative_to(destination)
        group = relative.parts[1] if relative.parts[0] == 'sweeps' else relative.parts[0]
        regional_meshes.setdefault(group, []).append(path)

    result = {}
    for owner in sorted(owners):
        modules = list((destination / 'cases' / owner).glob('playable*.js'))
        inputs = [destination / 'case-scene.js', destination / 'scene.js']
        if owner == 'echo':
            inputs += list((destination / 'cardiac').rglob('*.js'))
            inputs += list((destination / 'cardiac/torso').glob('*.raw'))
        else:
            groups = {
                'organs': ('scenes', 'liver', 'breast', 'axilla', 'thyroid', 'carotid', 'kidney'),
                'vascular': ('thyroid', 'carotid', 'scenes'),
                'pregnancy': ('pregnancy', 'scenes'),
            }[owner]
            for group, paths in regional_meshes.items():
                if group.startswith(groups):
                    inputs.extend(paths)
            if owner == 'vascular':
                inputs.append(destination / 'cases/organs/playable-scene-skin.js')
        fingerprint = dict(modules=digest(set(modules + inputs)), rubric=sha256(RUBRIC.read_bytes()).hexdigest(),
                           cases=[row['record'] for row in records if row['owner'] == owner])
        result[owner] = sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
    return result


AXES = {'fidelity', 'form', 'readability', 'economy'}


def validate_reviews(path):
    """Validate retained assessments and their witnesses, independent of qualification status."""
    document = json.loads(path.read_text())
    if document.get('version') != 1 or not isinstance(document.get('records'), list):
        raise ValueError(f'Invalid asset review package: {path}')
    files = {}
    bindings = []
    for record in document['records']:
        if not all(record.get(key) for key in ('case', 'part', 'task', 'revision', 'rubric', 'reviewer', 'reviewedOn')):
            raise ValueError(f'Incomplete asset review identity: {path}')
        extra = record.get('additionalUses', [])
        base = {key: value for key, value in record.items() if key != 'additionalUses'}
        bindings.append(base)
        for use in extra:
            if not use.get('case') or use.keys() - {'case', 'chapter'}:
                raise ValueError(f'Invalid additional asset review use: {path}')
            bindings.append(base | use)
        scores = record.get('scores', {})
        if scores.keys() - AXES:
            raise ValueError(f'Unknown asset review axis: {path}')
        for axis, grade in scores.items():
            if grade is not None and (type(grade) is not int or grade not in range(5)
                                      or not record.get('scoreEvidence', {}).get(axis)):
                raise ValueError(f'Unsubstantiated asset review score: {path} / {axis}')
        comparison = record.get('comparison', {})
        for view in [comparison, *comparison.get('views', [])]:
            for field in ('baseline', 'candidate', 'original'):
                if field not in view:
                    continue
                media = (path.parents[2] / view[field]).resolve()
                if not media.is_relative_to(path.parent.resolve()) or not media.is_file():
                    raise ValueError(f'Missing or unbound asset review image: {view[field]}')
                if media not in files:
                    files[media] = sha256(media.read_bytes()).hexdigest()
    expected = document.get('evidenceSha256', {})
    actual = {f.relative_to(path.parent.resolve()).as_posix(): digest for f, digest in files.items()}
    if expected != actual:
        raise ValueError(f'Asset review evidence identity mismatch: {path}')
    return document | {'records': bindings}


class OrientationSections(HTMLParser):
    """Read the section bindings that the composed player itself uses."""

    def __init__(self):
        super().__init__()
        self.heading = False
        self.title = ''
        self.sections = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.heading = True
        if tag == 'a' and 'data-chapter' in attrs and 'data-sweep' in attrs:
            self.sections.append(dict(id=attrs['data-chapter'], sweep=attrs['data-sweep'],
                                      start=int(attrs['data-start']), end=int(attrs['data-end'])))

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.heading = False

    def handle_data(self, data):
        if self.heading:
            self.title += data


def teaching_tours(destination, cases, sweeps):
    regions = {'aaa': 'abdomen', 'abdomen': 'abdomen', 'thyroid': 'neck', 'carotid': 'neck',
               'breast': 'breast', 'echo': 'heart'}
    visits = [dict(id=case['id'], title=case['title'], url=case['url'], caseId=case['id'],
                   region='pregnancy' if case['family'].startswith('pregnancy-') else regions[case['family']])
              for case in cases]
    available = {sweep['id'] for sweep in sweeps}
    for key, region, url in [('liver-orientation', 'abdomen', 'composed-tour/index.html'),
                             ('thyroid-orientation', 'neck', 'tours/thyroid-orientation/index.html')]:
        page = destination / url
        if not page.is_file():
            continue
        reader = OrientationSections()
        reader.feed(page.read_text())
        sweep_ids = list(dict.fromkeys(section['sweep'] for section in reader.sections))
        if not sweep_ids:  # A partial study can include an availability handoff at an old URL.
            continue
        if not set(sweep_ids) <= available:
            raise ValueError(f'Tour {key} points to a missing sweep: {sweep_ids}')
        visits.append(dict(id=key, title=reader.title.strip(), region=region, url=url,
                           sweepIds=sweep_ids, sections=reader.sections))
    return visits


def write_asset_inventory(destination, grouped, families, evidence, tours):
    target = destination / 'development'
    target.mkdir(exist_ok=True)
    records = []
    for family, cases in grouped.items():
        for case in cases:
            key = case['id']
            chapters = [{k: chapter[k] for k in ('id', 'title', 'evidenceFrame')} for chapter in evidence[key]]
            records.append(dict(id=key, family=family, owner=families[family][1], title=case['title'],
                                url=f'tours/{family}/{key}.html', chapters=chapters, record=case))
    reviews = []
    source = HERE / 'development/asset-reviews'
    for path in sorted(source.glob('*/reviews.json')):
        document = validate_reviews(path)
        relative = path.parent.relative_to(source.parent)
        shutil.copytree(path.parent, target / relative, dirs_exist_ok=True)
        (target / relative / path.name).write_text(json.dumps(document, separators=(',', ':')) + '\n')
        reviews.append((relative / path.name).as_posix())
    shutil.copyfile(RUBRIC, target / 'asset-rubric.md')
    sweep_hashes = {}
    files = {}
    for sweep in tours:
        parts = {}
        for part in ['torso', *(part['id'] for part in sweep['parts'])]:
            default = Path(sweep['assetRoot']) / 'scenes' / (part + '.mesh')
            path = destination / sweep.get('meshPaths', {}).get(part, default)
            if path not in files:
                files[path] = sha256(path.read_bytes()).hexdigest()
            parts[part] = files[path]
        sweep_hashes[sweep['id']] = parts
    manifest = dict(version=1, cases=records, teachingTours=teaching_tours(destination, records, tours),
                    reviews=reviews, sweepHashes=sweep_hashes,
                    rubricHash=sha256(RUBRIC.read_bytes()).hexdigest(),
                    recipeHashes=recipe_hashes(destination, {row['owner'] for row in records}, records))
    (target / 'asset-inventory.json').write_text(json.dumps(manifest, separators=(',', ':')) + '\n')
