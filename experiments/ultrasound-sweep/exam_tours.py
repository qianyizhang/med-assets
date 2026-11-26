"""Assemble the playable visit pages and their adjacent worked material."""
import json
from html import escape
import shutil
import subprocess
from urllib.parse import urlencode

from aaa_tours import write_aaa_tours
from exam_sweep import sweep_page
from tour_timeline import timeline_controls


def evidence_index(root, groups, families):
    visits = [{'owner': families[family][1], 'record': record} for family, records in groups.items() for record in records]
    result = subprocess.run(['node', str(root.parent / 'tours/case-evidence.mjs')], input=json.dumps(visits),
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def tour_path(record):
    return f"tours/{record['family']}/{record['id']}.html"


def evidence_url(page, chapter):
    query = urlencode({'chapter': chapter['id'], 'frame': chapter['evidenceFrame']})
    return f'{page}?{query}#exam'


def exam_page(record, family_title, chapters):
    key = record['id']
    title = escape(record['title'])
    panels = []
    findings = []
    sections = []
    for chapter in chapters:
        chapter_id = chapter['id']
        heading = escape(chapter['title'])
        observation = escape(chapter['observation'])
        frame = chapter['evidenceFrame']
        href = escape(evidence_url(key + '.html', chapter))
        measure = escape(chapter.get('measurement') or '')
        sections.append(dict(id=chapter_id, sweep=chapter_id, label=chapter['title'],
                             start=0, end=chapter['frames'] - 1))
        panels.append(f'''<section class="chapter" id="{escape(chapter_id)}" hidden
          data-view-image="{escape(chapter['viewImage'])}" data-evidence-frame="{frame}">
          <div><h2>{heading}</h2><p>{observation}</p></div>
          <div class="evidence"><a href="{href}">Show saved frame</a></div></section>''')
        findings.append(f'<li><a href="{href}">{heading}</a> · {measure or observation}</li>')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Ultrasound tour</title><link rel="stylesheet" href="../../study.css">
<link rel="stylesheet" href="../../composed-tour/tour.css"><script defer src="../../composed-tour/tour.js"></script></head>
<body><header class="mast"><div class="bar"><nav aria-label="Breadcrumb">
<a class="caseLink" href="../../index.html">Ultrasound anatomy</a>
<a class="caseLink" href="../index.html#{record['family']}">Tours</a>
<span>{escape(family_title)}</span></nav></div></header>
<main><header class="introduction"><h1>{title}</h1><p><strong>Referral</strong> {escape(record['indication'])}</p>
<p><a href="../../cases/{key}.html">Worked views and acquired comparisons</a> · <a href="#impression">Impression and report</a></p></header>
<section id="exam" aria-label="Acquisitions">{timeline_controls(sections, acquisition_picker=True)}
<p id="tourProgress" class="sr" role="status"></p>{''.join(panels)}
<div id="player" data-sweep-url="{key}-sweep.html" data-sweep-chapter-param="chapter" data-case-player></div>
<noscript><p>Enable JavaScript to play the acquisitions. The <a href="../../cases/{key}.html">worked case</a> includes the saved views.</p></noscript>
<p class="standaloneLink"><a id="openSweep">Open standalone sweep</a></p></section>
<section class="reading" id="impression"><h2>Impression</h2><p>{escape(record['impression'])}</p>
<h3 id="evidence">Acquisition evidence</h3><ol id="reportEvidence">{''.join(findings)}</ol>
<h3>Limits</h3><p>{escape(record['limitations'])}</p></section>
</main></body></html>
'''


def legacy_handoff(target, *, index=False):
    # The old address can identify a specific measurement by chapter, frame and fragment.
    dest = json.dumps(target)
    resolve = f"new URL({dest}, location.href)"
    if index:
        resolve = f"location.hash === '#aaa' ? new URL('../tours/aaa/index.html', location.href) : {resolve}"
    keep_hash = "if (location.hash !== '#aaa') " if index else ""
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Ultrasound tours</title>
<script>const target = {resolve};
target.search = location.search;
{keep_hash}target.hash = location.hash;
location.replace(target.href);</script>
<p><a href="{escape(target)}">Open the ultrasound tour</a></p></html>'''


def write_exam_tours(destination, root, grouped, families, catalog, evidence, shared_aaa=False):
    exams = destination / 'exams'
    exams.mkdir(exist_ok=True)
    tours = destination / 'tours'
    tours.mkdir(exist_ok=True)
    for filename in ('case-sweep.js', 'case-sweep.css'):
        shutil.copyfile(root.parent / 'tours' / filename, tours / filename)
    for family, records in grouped.items():
        name, owner, _ = families[family]
        modules = sorted((root / owner).glob('playable*.js'))
        if not (root / owner / 'playable.js').is_file():
            raise ValueError(f'Missing acquisition module: {owner}')
        for module in modules:
            shutil.copyfile(module, destination / 'cases' / owner / module.name)
        if family == 'aaa':
            write_aaa_tours(destination, records, evidence, shared_aaa=shared_aaa)
        else:
            family_dir = tours / family
            family_dir.mkdir(exist_ok=True)
            for record in records:
                key = record['id']
                (family_dir / (key + '.html')).write_text(exam_page(record, name, evidence[key]))
                (family_dir / (key + '-sweep.html')).write_text(sweep_page(record, owner, name))
        for record in records:
            old = exams / (record['id'] + '.html')
            old.write_text(legacy_handoff('../' + tour_path(record)))
    (tours / 'index.html').write_text(catalog)
    (exams / 'index.html').write_text(legacy_handoff('../tours/index.html', index=True))
