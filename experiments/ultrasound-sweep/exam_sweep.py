"""Page shell for one section of a modeled ultrasound acquisition."""

from html import escape
import json


def sweep_page(record, owner, family_title):
    case_id = record['id']
    title = escape(record['title'])
    data = json.dumps(record, ensure_ascii=False).replace('<', r'\u003c')
    work = escape(f'../../cases/{case_id}.html', quote=True)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} · Modeled ultrasound sweep</title>
  <link rel="stylesheet" href="../../cases/cases.css">
  <link rel="stylesheet" href="../case-sweep.css">
  <script type="module" src="../case-sweep.js"></script>
</head>
<body>
  <header class="sweep-header"><nav aria-label="Case links">
    <a id="tourLink" href="{escape(case_id, quote=True)}.html">Case tour</a> · <a href="{work}">Worked case</a>
  </nav></header>
  <main data-owner="{escape(owner, quote=True)}">
    <p class="category standalone">{escape(family_title)} · Modeled acquisition</p>
    <h1 class="standalone">{title}</h1>
    <p id="status" role="status">Loading acquisition…</p>
    <noscript>Enable JavaScript to play the sweep.</noscript>
    <section id="exam" aria-labelledby="view" hidden>
      <h2 id="view"></h2>
      <div class="transport">
        <button type="button" id="play">Play sweep</button>
        <button type="button" id="keyframe">Show evidence frame</button>
        <div class="timeline">
          <label for="position">Sweep position</label>
          <input type="range" id="position" min="0" step="1" value="0">
          <output id="frameNumber" for="position"></output>
        </div>
      </div>
      <div class="monitors">
        <figure>
          <figcaption><h3>Modeled ultrasound</h3><button type="button" id="overlay" aria-pressed="false">Tissue overlay</button></figcaption>
          <canvas id="scan" width="800" height="440" aria-label="Modeled ultrasound acquisition"></canvas>
        </figure>
        <figure>
          <figcaption><h3>3D anatomy and probe</h3></figcaption>
          <canvas id="pose" width="400" height="300" aria-label="Probe position and anatomy at the current frame"></canvas>
          <div class="orbit">
            <label for="orbit">Orbit</label><input id="orbit" type="range" min="-90" max="90" value="0" aria-label="Orbit 3D anatomy">
            <output id="yaw" for="orbit">0°</output><button type="button" id="resetView">Reset</button>
          </div>
        </figure>
      </div>
      <ul id="legend" aria-label="Tissue overlay legend" hidden></ul>
      <output id="value" for="position"></output>
      <p id="observed" class="standalone" hidden></p>
    </section>
    <script id="record" type="application/json">{data}</script>
  </main>
</body>
</html>
'''
