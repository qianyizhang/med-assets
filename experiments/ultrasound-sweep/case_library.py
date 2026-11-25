"""Compile the worked ultrasound visits into ordinary, deep-linkable reading pages."""
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

from exam_tours import evidence_index, evidence_url, tour_path, write_exam_tours

ROOT = Path(__file__).with_name('cases')
FAMILIES = {
    'aaa': ('Abdominal aortic aneurysm', 'vascular', 'aortic-screening'),
    'carotid': ('Bilateral carotid duplex', 'vascular', 'carotid-right'),
    'abdomen': ('Abdomen and urinary tract', 'organs', 'gallbladder'),
    'thyroid': ('Thyroid and cervical nodes', 'organs', 'thyroid-right'),
    'breast': ('Breast and axilla', 'organs', 'breast'),
    'pregnancy-early': ('Early pregnancy', 'pregnancy', 'pregnancy-early'),
    'pregnancy-first': ('11–14-week scan', 'pregnancy', 'pregnancy-fetus'),
    'pregnancy-mid': ('Mid-trimester anatomy', 'pregnancy', 'pregnancy-mid-brain'),
    'pregnancy-late': ('Third-trimester growth', 'pregnancy', 'pregnancy-late-biometry'),
    'echo': ('Adult transthoracic echo', 'echo', None),
}
KINDS = {'normal': 'Normal', 'abnormal': 'Finding', 'limited': 'Limited study'}


def link(url, label):
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def document(title, crumb, content):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Ultrasound anatomy</title><link rel="stylesheet" href="../cases/cases.css"></head>
<body><header><nav aria-label="Breadcrumb">{link('../index.html', 'Ultrasound anatomy')} <span>/</span> {crumb}</nav></header>
<main>{content}</main></body></html>
'''


def load_cases(root):
    grouped = {family: [] for family in FAMILIES}
    seen = set()
    for package in dict.fromkeys(owner for _, owner, _ in FAMILIES.values()):
        folder = root / package
        for case in json.loads((folder / 'cases.json').read_text()):
            key, family = case['id'], case['family']
            if (not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', key) or key == 'index'
                    or key in seen or family not in FAMILIES or FAMILIES[family][1] != package):
                raise ValueError(f'Invalid case identity: {key} ({family})')
            seen.add(key)
            if case['kind'] not in KINDS or not case['views'] or not case['sources']:
                raise ValueError(f'Missing worked case evidence: {key}')
            for view in case['views']:
                path = (folder / view['image']).resolve()
                if (Path(view['image']).is_absolute() or '..' in Path(view['image']).parts
                        or not path.is_relative_to(folder.resolve()) or not path.is_file()
                        or path.suffix not in {'.svg', '.webp', '.png'}):
                    raise ValueError(f'Missing or invalid case image: {key}/{view["image"]}')
                if 'illustration' in view:
                    art = view['illustration']
                    file = Path(art['file'])
                    asset = (folder / file).resolve()
                    if (file.is_absolute() or '..' in file.parts or file.suffix not in {'.webp', '.svg'}
                            or not asset.is_relative_to(folder.resolve())
                            or not asset.is_file() or sha256(asset.read_bytes()).hexdigest() != art['sha256']):
                        raise ValueError(f'Invalid case illustration: {key}/{file}')
            for source in case['sources']:
                if urlsplit(source['url']).scheme not in {'https', 'http'}:
                    raise ValueError(f'Invalid clinical source: {key}')
            grouped[family].append(case)
    for family, records in grouped.items():
        if {row['kind'] for row in records} != KINDS.keys():
            raise ValueError(f'Missing case pathway in {family}')
    return grouped


def paragraph(value):
    return ''.join(f'<p>{escape(line)}</p>' for line in (value if isinstance(value, list) else [value]))


def finding_comparisons(root, grouped):
    folder = root / 'acquired'
    records = json.loads((folder / 'references.json').read_text())
    cases = {case['id']: case for family in grouped.values() for case in family}
    for key, row in records.items():
        if key not in cases or row['afterView'] not in {Path(v['image']).name for v in cases[key]['views']}:
            raise ValueError(f'Acquired comparison has no matching case view: {key}')
        for media, digest in [('path', 'sha256'), ('poster', 'posterSha256')]:
            if media == 'poster' and not row.get('poster'):
                continue
            filename = Path(row[media])
            path = (folder / filename).resolve()
            if (filename.is_absolute() or '..' in filename.parts or not path.is_relative_to(folder.resolve())
                    or not path.is_file() or sha256(path.read_bytes()).hexdigest() != row[digest]):
                raise ValueError(f'Unexpected acquired case image identity: {key}/{media}')
        for field in ('title', 'credit', 'license', 'note'):
            if not row[field].strip():
                raise ValueError(f'Missing acquired comparison {field}: {key}')
        if any(urlsplit(row[field]).scheme not in {'http', 'https'} for field in ('url', 'licenseUrl')):
            raise ValueError(f'Invalid acquired comparison source: {key}')
    return records


def acquired_comparison(ref, description, anchor=None):
    if not ref:
        return ''
    src = '../' + escape(ref['path'])
    preview = '../' + escape(ref.get('poster') or ref['path'])
    action = link('../' + ref['path'], 'Play the original clip') if ref.get('poster') else ''
    alt = escape(ref.get('alt') or ref['title'])
    fragment = f' id="{anchor}"' if anchor else ''
    return f'''<figure class="comparison"{fragment}><a href="{src}" aria-label="Open original figure · {escape(ref['title'])}">
<img loading="lazy" src="{preview}" alt="{alt}"></a>
<figcaption><h3>{escape(ref['title'])}</h3><p>{escape(description)}</p>
<p>{link(ref['url'], ref['credit'])} · {link(ref['licenseUrl'], ref['license'])}</p>{paragraph(ref['note'])}{action}</figcaption></figure>'''


def case_page(case, related, owner, tour_link, finding, refs, evidence):
    family = case['family']
    name = FAMILIES[family][0]
    case_tour = '../' + tour_path(case)
    views = []
    contents = []
    for index, view in enumerate(case['views']):
        anchor = f'view-{index + 1}'
        bindings = [c for c in evidence if c['viewImage'] == view['image']]
        links = [link(evidence_url(case_tour, c), c['title']) for c in bindings]
        replay = ('<details class="replays"><summary>Replay acquisitions</summary><ul>' +
                  ''.join('<li>' + item + '</li>' for item in links) + '</ul></details>') if len(links) > 1 else (
                      link(evidence_url(case_tour, bindings[0]), 'Replay acquisition'))
        contents.append(f"<li>{link('#' + anchor, view['title'])}</li>")
        image = escape(f"{owner}/{view['image']}", quote=True)
        loading = 'loading="lazy"' if index else ''
        measurement = paragraph(view['measurement']) if view.get('measurement') else ''
        paired = [refs[ref_id] for ref_id in view.get('referenceIds', []) if ref_id in refs]
        examples = ''
        if paired:
            examples = '<details class="paired"><summary>Acquired comparisons</summary>' + ''.join(
                acquired_comparison(ref, 'Separate acquired examination.') for ref in paired) + '</details>'
        views.append(f'''<figure id="{anchor}"><a class="plate" href="{image}" aria-label="Open full-size image · {escape(view['title'])}">
<img src="{image}" {loading} alt="{escape(view['title'])}"></a><figcaption>
<h3>{escape(view['title'])}</h3>{paragraph(view['caption'])}<div class="measure">{measurement}</div>{replay}</figcaption></figure>{examples}''')
        if 'illustration' in view:
            art = view['illustration']
            src = escape(f"{owner}/{art['file']}")
            art_replay = replay
            if 'chapterId' in art:
                chapter = next((c for c in bindings if c['id'] == art['chapterId']), None)
                if chapter is None:
                    raise ValueError(f"Unbound illustration acquisition: {case['id']}/{art['chapterId']}")
                art_replay = link(evidence_url(case_tour, chapter), 'Replay acquisition')
            download = f'<p><a href="{src}" download>Download editable SVG</a></p>' if src.endswith('.svg') else ''
            views.append(f'''<figure id="{anchor}-illustration"><a class="plate" href="{src}" aria-label="Open full-size illustration">
<img src="{src}" loading="lazy" alt="{escape(art['alt'])}"></a><figcaption>
<h3>{escape(art['title'])}</h3>{paragraph(art['caption'])}{art_replay}{download}</figcaption></figure>''')
        if finding and Path(view['image']).name == finding['afterView']:
            views.append(acquired_comparison(finding, 'Acquired finding from a separate examination.', 'finding'))
    finding_link = link('#finding', 'Acquired finding') if finding else ''
    sources = ''.join(f"<li>{link(s['url'], s['title'])}</li>" for s in case['sources'])
    others = ''.join(f"<li>{link(c['id'] + '.html', c['title'])}</li>" for c in related if c['id'] != case['id'])
    navigation = f'''<div class="jump"><details><summary>Views in this case ({len(contents)})</summary>
<ol>{''.join(contents)}</ol></details>{finding_link}{link('#impression', 'Impression')}{link('#sources', 'Sources')}</div>'''
    body = f'''<p class="category">{escape(name)} · {KINDS[case['kind']]}</p><h1>{escape(case['title'])}</h1>
<p class="referral"><strong>Referral</strong> {escape(case['indication'])}</p>{paragraph(case['summary'])}
<p class="playLink">{link(case_tour, 'Open exam tour' if family == 'aaa' else 'Open full exam tour')}</p>
{navigation}<section class="views" aria-label="Worked views">{''.join(views)}</section>
<section class="report" id="impression"><h2>Impression</h2>{paragraph(case['impression'])}<h3>Limits</h3>{paragraph(case['limitations'])}</section>
<section id="sources"><h2>Sources</h2><ul>{sources}</ul>{tour_link}</section>
<nav class="related" aria-label="More in this family"><h2>Other {escape(name.lower())} cases</h2><ul>{others}</ul></nav>'''
    return document(case['title'], link('index.html#' + family, 'Worked cases'), body)


def family_section(family, records, *, tours=False):
    rows = []
    for record in records:
        href = '../' + tour_path(record) if tours else record['id'] + '.html'
        rows.append(f"<li><span>{KINDS[record['kind']]}</span>{link(href, record['title'])}</li>")
    return f'<section class="family" id="{family}"><h2>{escape(FAMILIES[family][0])}</h2><ul>{"".join(rows)}</ul></section>'


def write_case_library(destination, tours, refs, root=ROOT, *, aaa_acquisitions=None):
    grouped = load_cases(root)
    findings = finding_comparisons(root, grouped)
    evidence = evidence_index(root, grouped, FAMILIES)
    if aaa_acquisitions is not None:
        from aaa_delivery import install_acquisitions
        normal = next((tour for tour in tours if tour['id'] == 'aortic-screening'), None)
        install_acquisitions(aaa_acquisitions, destination, normal,
                             {case['id']: evidence[case['id']] for case in grouped['aaa']})
    target = destination / 'cases'
    target.mkdir(exist_ok=True)
    shutil.copyfile(root / 'cases.css', target / 'cases.css')
    for row in findings.values():
        for field in ('path', 'poster'):
            if not row.get(field):
                continue
            relative = Path('acquired') / row[field]
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, path)
            row[field] = (Path('cases') / relative).as_posix()
    echo_refs = json.loads((root.parent / 'cardiac/reference/sources.json').read_text())
    refs = dict(refs)
    for panels in echo_refs['panels'].values():
        for panel in panels:
            number = panel['number']
            refs[f'bse-{number}'] = {**echo_refs['bse'], 'title': panel['label'],
                'path': f'cardiac/reference/bse/ERP-20-0026inf{number}.jpg',
                'note': 'Original published panel, reproduced unchanged from Table 1.'}
    available = {tour['id'] for tour in tours}
    cards = []
    tour_groups = []
    for family, (name, owner, sweep) in FAMILIES.items():
        records = sorted(grouped[family], key=lambda row: list(KINDS).index(row['kind']))
        tour_link = ''
        if sweep in available:
            tour_link = link('../index.html?sweep=' + sweep, 'Open the anatomy sweep and acquired comparisons')
        if family == 'echo':
            tour_link = link('../cardiac/?view=plax', 'Explore the 17 echo windows and acquired examples')
        if family == 'carotid' and (destination / 'carotid-survey/protocol.json').is_file():
            tour_link = link('../carotid-survey/', 'Open the bilateral duplex acquisition')
        for case in records:
            for view in case['views']:
                relative = Path(owner, view['image'])
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / relative, path)
                if 'illustration' in view:
                    art = Path(owner, view['illustration']['file'])
                    (target / art).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(root / art, target / art)
            page = case_page(case, records, owner, tour_link, findings.get(case['id']), refs, evidence[case['id']])
            (target / (case['id'] + '.html')).write_text(page)
        cards.append(family_section(family, records))
        if family != 'aaa':
            tour_groups.append(family_section(family, records, tours=True))
    body = ('<h1>Worked ultrasound cases</h1><p class="intro">Follow a referral through the imaging views, '
            'measurements and impression of a modeled exam.</p><p><a href="../tours/index.html">Browse tours</a></p>'
            '<div class="catalog">' + ''.join(cards) + '</div>')
    (target / 'index.html').write_text(document('Worked ultrasound cases', 'Worked cases', body))
    tours_body = ('<h1>Ultrasound tours</h1>'
                  '<div class="catalog"><section class="family" id="aaa">'
                  '<h2><a href="aaa/index.html">AAA screening</a></h2>'
                  '<p>Follow a negative, positive or indeterminate case from referral to impression.</p></section>'
                  '<section class="family"><h2><a href="../composed-tour/">Abdominal orientation</a></h2>'
                  '<p>Explore the liver, portal vein and gallbladder on one CT anatomy.</p></section></div>'
                  '<h2>Other exam tours</h2><div class="catalog">' + ''.join(tour_groups) + '</div>')
    write_exam_tours(destination, root, grouped, FAMILIES,
                     document('Ultrasound tours', 'Tours', tours_body), evidence, aaa_acquisitions is not None)
