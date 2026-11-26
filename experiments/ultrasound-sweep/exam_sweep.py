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
  <script src="../../abdomen-tours.js"></script>
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
        <figure class="posePanel">
          <figcaption><h3>Probe and scan plane</h3><div id="posePresets" aria-label="Camera view">
            <button data-camera="oblique" aria-pressed="true">Oblique</button>
            <button data-camera="axial" aria-pressed="false">Axial</button>
            <button data-camera="coronal" aria-pressed="false">Coronal</button>
            <button data-camera="sagittal" aria-pressed="false">Sagittal</button>
          </div></figcaption>
          <div class="poseViewport">
            <canvas id="pose" tabindex="0" aria-label="3D patient, probe and imaging field. Use the arrow keys to orbit and plus or minus to zoom."></canvas>
            <div id="poseFeedback" role="status"><span id="poseStatus">Loading case anatomy…</span> <button id="retryPose" hidden>Retry 3D view</button></div>
          </div>
          <ul id="poseLegend" aria-label="3D anatomy"></ul>
          <div class="orbit"><label for="skinOpacity">Skin opacity</label>
            <input id="skinOpacity" type="range" min="0" max="100" step="1" value="32"><output id="skinValue" for="skinOpacity">32%</output>
          </div>
        </figure>
        <figure>
          <figcaption><h3>Modeled ultrasound</h3><button type="button" id="overlay" aria-pressed="false">Tissue overlay</button></figcaption>
          <canvas id="scan" width="800" height="440" aria-label="Modeled ultrasound acquisition"></canvas>
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
