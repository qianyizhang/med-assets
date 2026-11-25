"""Assemble the playable visit pages and their adjacent worked material."""
import json
from html import escape
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlencode


def evidence_index(root, groups, families):
    visits = [{'owner': families[family][1], 'record': record} for family, records in groups.items() for record in records]
    result = subprocess.run(['node', str(root.parent / 'exams/evidence.mjs')], input=json.dumps(visits),
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def evidence_url(key, chapter):
    query = urlencode({'chapter': chapter['id'], 'frame': chapter['evidenceFrame']})
    return f'{key}.html?{query}#exam'


def exam_page(record, owner, family_title, evidence):
    key = record['id']
    title = escape(record['title'])
    data = json.dumps(record, ensure_ascii=False).replace('<', r'\u003c')
    rows = []
    for chapter in evidence:
        href = escape(evidence_url(key, chapter))
        finding = escape(chapter.get('measurement') or chapter['observation'])
        rows.append(f'<li><strong>{escape(chapter["title"])}</strong><br><a href="{href}">{finding}</a></li>')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Full ultrasound exam</title><link rel="stylesheet" href="../cases/cases.css">
<link rel="stylesheet" href="exam.css"><script type="module" src="player.js"></script></head>
<body><header><nav aria-label="Breadcrumb"><a href="../index.html">Ultrasound anatomy</a> / <a href="index.html#{record['family']}">Full exams</a></nav></header>
<main data-owner="{owner}"><p class="category">{escape(family_title)} · Modeled exam</p><h1>{title}</h1>
<p class="referral"><strong>Referral</strong> {escape(record['indication'])}</p>
<p><a href="../cases/{key}.html">Worked views and acquired comparisons</a> · <a href="#impression">Exam impression</a></p>
<p id="status" role="status">Loading acquisitions…</p><noscript>Enable JavaScript to play the acquisitions.</noscript>
<section id="exam" aria-label="Playable acquisitions" hidden>
<div class="transport"><button type="button" id="play">Play full exam</button>
<label>Chapter <select id="chapter"></select></label><button type="button" id="replay">Replay chapter</button></div>
<div class="monitors"><figure><figcaption><h2 id="view"></h2><button type="button" id="overlay" aria-pressed="false">Tissue overlay</button></figcaption>
<canvas id="scan" width="800" height="440" aria-label="Modeled ultrasound acquisition"></canvas></figure>
<figure><figcaption><h2>3D anatomy and probe</h2></figcaption><canvas id="pose" width="400" height="300" aria-label="Probe position and anatomy at the current frame"></canvas><label class="orbit">Orbit <input id="orbit" type="range" min="-90" max="90" value="0" aria-label="Orbit 3D anatomy"><output id="yaw">0°</output><button type="button" id="resetView">Reset</button></label></figure></div><ul id="legend" aria-label="Tissue overlay legend" hidden></ul>
<label class="timeline"><span>Exam position</span><input id="seek" type="range" min="0" step="1" value="0"><output id="position" for="seek"></output></label>
<p id="finished" role="status" hidden>Exam complete. <a href="#impression">Read the impression</a></p><p id="observed"><span id="observationCue"></span> <a id="observationLink" href="#exam"></a></p><button type="button" id="keyframe">Show evidence frame</button><output id="value"></output>
</section><section class="report" id="impression"><h2>Impression</h2><p>{escape(record['impression'])}</p>
<h3>Acquisition evidence</h3><ol id="evidence">{"".join(rows)}</ol><h3>Limits</h3><p>{escape(record['limitations'])}</p></section>
<script id="record" type="application/json">{data}</script></main></body></html>
'''


def write_exam_tours(destination, root, grouped, families, catalog, evidence):
    exams = destination / 'exams'
    exams.mkdir(exist_ok=True)
    for filename in ('player.js', 'exam.css'):
        shutil.copyfile(root.parent / 'exams' / filename, exams / filename)
    for family, records in grouped.items():
        name, owner, _ = families[family]
        modules = sorted((root / owner).glob('playable*.js'))
        if not (root / owner / 'playable.js').is_file():
            raise ValueError(f'Missing acquisition module: {owner}')
        for module in modules:
            shutil.copyfile(module, destination / 'cases' / owner / module.name)
        for row in records:
            (exams / (row['id'] + '.html')).write_text(exam_page(row, owner, name, evidence[row['id']]))
    (exams / 'index.html').write_text(catalog)
