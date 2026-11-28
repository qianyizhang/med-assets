"""Assemble the three modeled AAA screening tours from worked records and playback evidence."""
from html import escape
import json
from pathlib import Path
import shutil
from urllib.parse import urlencode

from survey_exemplars import companion_html
from tour_timeline import timeline_controls

CASES = {
    'aaa-negative': ('Negative screen', 'aaa-negative-stations.svg'),
    'aaa-positive': ('Positive screen with diagnostic views', 'aaa-positive-sac.svg'),
    'aaa-indeterminate': ('Indeterminate screen', 'aaa-indeterminate-anterior.svg'),
}
CHAPTER_LABELS = {
    'proximal-aorta': 'Proximal',
    'mid-aorta': 'Mid aorta',
    'distal-aorta': 'Distal aorta',
    'iliac-bifurcation': 'Bifurcation',
    'right-iliac-short': 'Right iliac transverse',
    'left-iliac-short': 'Left iliac transverse',
    'sac-maximum': 'Sac transverse',
    'sac-long-axis': 'Sac long axis',
    'right-iliac-long': 'Right iliac long axis',
    'left-iliac-long': 'Left iliac long axis',
    'anterior-distal-attempt': 'Anterior attempt',
    'lateral-distal-repeat': 'Lateral repeat',
}
DIAGNOSTIC_START = 'sac-long-axis'
CT_SWEEP = '../../index.html?sweep=aortic-screening'


def link(url: str, title: str) -> str:
    return f'<a href="{escape(url, quote=True)}">{escape(title)}</a>'


def chapter_url(chapter: dict, *, frame: bool = False, anchor: str = '') -> str:
    query = {'chapter': chapter['id']}
    if frame:
        query['frame'] = str(chapter['evidenceFrame'])
    return '?' + urlencode(query) + anchor


def shell(title: str, content: str, *, case: bool = False) -> str:
    script = '<script defer src="../../composed-tour/tour.js"></script>' if case else ''
    screening = link('index.html', 'AAA screening') if case else '<span aria-current="page">AAA screening</span>'
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · Ultrasound Anatomy</title>
  <link rel="stylesheet" href="../../study.css">
  <link rel="stylesheet" href="../../composed-tour/tour.css">
  <link rel="stylesheet" href="tours.css">
  {script}
</head>
<body class="aaa">
  <header class="mast">
    <div class="bar">
      <nav class="aaa-breadcrumb" aria-label="Breadcrumb">
        {link('../../index.html', 'Ultrasound Anatomy')} <span aria-hidden="true">/</span>
        {link('../index.html', 'Tours')} <span aria-hidden="true">/</span> {screening}
      </nav>
    </div>
  </header>
  <main>{content}</main>
</body>
</html>
'''


def index_page(cases: dict, normal_sweep: bool, shared_aaa: bool) -> str:
    cards = []
    for index, (case_id, (title, image)) in enumerate(CASES.items()):
        summary = escape(cases[case_id]['summary'])
        priority = 'fetchpriority="high"' if index == 0 else ''
        cards.append(f'''
    <article class="scenario">
      <img src="../../cases/vascular/{image}" alt="" width="800" height="420" {priority}>
      <div>
        <h2>{link(case_id + '.html', title)}</h2>
        <p>{summary}</p>
      </div>
    </article>''')
    context = ('Compare the original CT-based sweep with these case variants. They share its fitted torso, '
               'probe and tissue context. The vessel geometry and measurements belong to each case.'
               if shared_aaa else 'Inspect the s1233 CT anatomy and its acquired comparisons.')
    related = f'''
  <aside class="ct-note" aria-labelledby="ct-title">
    <h2 id="ct-title">CT-based normal aortic sweep</h2>
    <p>{context}</p>
    {link(CT_SWEEP, 'Open the CT-based sweep')}
  </aside>''' if normal_sweep else ''
    return shell('AAA screening', f'''
  <header class="aaa-intro">
    <h1>AAA screening</h1>
    <p>Follow the probe from referral to impression in three modeled screening cases.</p>
  </header>
  <div class="scenario-grid">{''.join(cards)}
  </div>{related}''')


def chapter_sections(case_id: str, chapters: list) -> tuple[list[dict], str, str]:
    sections = []
    panels = []
    report = []
    diagnostic = False
    for chapter in chapters:
        chapter_id = chapter['id']
        key = escape(chapter_id, quote=True)
        title = escape(chapter['title'])
        cue = escape(chapter['observation'])
        measurement = chapter.get('measurement')
        phase_start = case_id == 'aaa-positive' and chapter_id == DIAGNOSTIC_START
        diagnostic = diagnostic or phase_start
        sections.append({
            'id': chapter_id,
            'sweep': chapter_id,
            'label': CHAPTER_LABELS.get(chapter_id, chapter['title']),
            'start': 0,
            'end': chapter['frames'] - 1,
            'phaseStart': phase_start,
        })
        saved_frame = link(chapter_url(chapter, frame=True), 'Show saved frame')
        value = f'<p class="chapter-value">{escape(measurement)}</p>' if measurement else ''
        phase_name = '<p class="phase-name">Diagnostic continuation</p>' if diagnostic else ''
        panels.append(f'''
    <section class="chapter" id="{key}" aria-labelledby="{key}-title" hidden>
      <div>{phase_name}<h2 id="{key}-title">{title}</h2><p>{cue}</p></div>
      <div class="evidence">{saved_frame}{value}</div>{companion_html(chapter)}
    </section>''')
        report_link = link(chapter_url(chapter, frame=True, anchor='#exam'), chapter['title'])
        report.append(f'<li>{report_link}{f" · {escape(measurement)}" if measurement else ""}</li>')
    return sections, ''.join(panels), ''.join(report)


def case_page(record: dict, chapters: list, shared_aaa: bool) -> str:
    case_id = record['id']
    title = CASES[case_id][0]
    sections, panels, report = chapter_sections(case_id, chapters)
    worked_url = f'../../cases/{case_id}.html'
    worked = link(worked_url, 'Worked case')
    continuation = ''
    if case_id == 'aaa-positive':
        chapter = next(chapter for chapter in chapters if chapter['id'] == DIAGNOSTIC_START)
        continuation = link(chapter_url(chapter, anchor='#exam'), 'Diagnostic continuation')
    placement_note = ''
    if shared_aaa and case_id == 'aaa-positive':
        placement_note = '<p>The modeled aneurysm sits slightly anterior to the native CT artery to clear the spine. Its cross-sectional dimensions are preserved.</p>'
    return shell(title, f'''
  <header class="aaa-intro aaa-case-intro">
    <h1>{escape(title)}</h1>
    <p>{escape(record['summary'])}</p>
    <p class="referral" id="referral"><strong>Referral</strong> {escape(record['indication'])}</p>
    <nav class="case-jumps" aria-label="Case material">
      {link('#impression', 'Impression and report')} {worked} {continuation}
    </nav>
  </header>

  <section id="exam" aria-label="Acquisition">
    {timeline_controls(sections)}
    <p id="tourProgress" class="sr" role="status"></p>
    {panels}
    <div id="player" data-sweep-url="sweep.html?case={case_id}" data-sweep-chapter-param="chapter"></div>
    <noscript><p>The sweep player requires JavaScript. Open the {worked} for the saved views.</p></noscript>
    <p class="standaloneLink"><a id="openSweep">Open standalone sweep</a></p>
  </section>

  <section class="aaa-report" id="impression">
    <h2>Impression</h2>
    <p>{escape(record['impression'])}</p>
    <h3 id="evidence">Acquisition evidence</h3>
    <ol id="reportEvidence">{report}</ol>
    <h3>Limits</h3>
    <p>{escape(record['limitations'])}</p>{placement_note}
    <p>{link(worked_url, 'Read worked views and comparisons')}</p>
  </section>
''', case=True)


def write_aaa_tours(destination: Path, records: list, evidence: dict, *, shared_aaa=False) -> None:
    cases = {record['id']: record for record in records}
    if cases.keys() != CASES.keys() or any(not evidence.get(key) for key in CASES):
        raise ValueError('AAA tours require the three worked cases and their acquisition evidence.')
    target = destination / 'tours/aaa'
    target.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_name('tours') / 'aaa'
    for name in ('tours.css', 'sweep.html', 'sweep.css', 'sweep.js'):
        shutil.copyfile(source / name, target / name)
    normal_sweep = (destination / 'sweeps/aortic-screening/sweep.js').is_file()
    (target / 'index.html').write_text(index_page(cases, normal_sweep, shared_aaa), encoding='utf-8')
    for case_id, record in cases.items():
        (target / (case_id + '.html')).write_text(case_page(record, evidence[case_id], shared_aaa), encoding='utf-8')
        (target / (case_id + '.json')).write_text(json.dumps(record | {'sharedSweepAvailable': shared_aaa}, ensure_ascii=False) + '\n', encoding='utf-8')
