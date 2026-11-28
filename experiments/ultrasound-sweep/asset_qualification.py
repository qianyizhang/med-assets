"""Assemble the Development workbench from the teaching delivery and retained reviews."""
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil

from med_assets.ultrasound_review import RUBRIC_PATH, chapter_mesh_bindings, recipe_hashes, validate_reviews

from delivery import validate_mesh


HERE = Path(__file__).resolve().parent
RUBRIC = HERE.parents[1] / RUBRIC_PATH


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
            chapters = [{k: chapter[k] for k in ('id', 'title', 'evidenceFrame', 'sourceSweep', 'exemplar') if k in chapter} for chapter in evidence[key]]
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
                    recipeHashes=recipe_hashes(destination, {row['owner'] for row in records}, records, rubric=RUBRIC))
    chapter_meshes = chapter_mesh_bindings(destination, evidence, validate_mesh=validate_mesh)
    if chapter_meshes:
        manifest['chapterMeshBindings'] = chapter_meshes
    (target / 'asset-inventory.json').write_text(json.dumps(manifest, separators=(',', ':')) + '\n')
