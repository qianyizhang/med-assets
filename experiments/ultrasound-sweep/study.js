'use strict';
const $ = (id) => document.getElementById(id);
const long = 12,
  last = sweep.length - 1;
const stops = [
  [0, 'Find the window'],
  [long, 'Long axis'],
  [last, 'Short axis'],
];
const source = {
  case: 'https://zenodo.org/records/10047263',
  long: 'https://doi.org/10.3390/life15060941',
  short: 'https://www.thepocusatlas.com/pedsbiliary',
};
const guided = () => $('variant').value === 'guide';
const state = {
  frame: long,
  section: false,
  compare: false,
  exercise: false,
  assets: false,
  group: 0,
  timer: null,
};
const imageFile = (kind, frame) => 'media/' + kind + '-' + String(frame).padStart(2, '0') + '.webp';
const anchor = () => (state.frame <= (long + last) / 2 ? 'long' : 'short');
const refFile = () => 'media/acquired-' + anchor() + '.webp';
const axisName = () => (anchor() === 'long' ? 'Long axis' : 'Short axis');
const on = (id, value) => $(id).setAttribute('aria-pressed', String(value));
const refCredit = () =>
  anchor() === 'long'
    ? 'Claudia Lucius et al. · Fig. 2 · CC BY 4.0'
    : 'Kathryn Pade, MD · The POCUS Atlas · adolescent case · 1.2 s · CC BY-NC 4.0';

function media(id, path) {
  const img = $(id);
  if (img.getAttribute('src') === path) return;
  img.hidden = false;
  img.parentElement.querySelector('.error')?.remove();
  img.src = path;
}
for (const id of ['pose', 'scan', 'ref']) {
  $(id).addEventListener('error', () => {
    const img = $(id);
    img.hidden = true;
    const msg = document.createElement('p');
    msg.className = 'error';
    msg.textContent =
      { pose: 'Probe view', scan: 'Scan', ref: 'Clinical reference' }[id] + ' unavailable for this frame.';
    msg.setAttribute('role', 'status');
    img.parentElement.append(msg);
    if (id === 'scan') {
      endExercise();
      $('test').disabled = true;
    }
  });
  if (id === 'scan')
    $(id).addEventListener('load', () => {
      $('test').disabled = ![long, last].includes(state.frame);
      if (state.exercise) drawMarkers();
    });
}
function endExercise() {
  state.exercise = false;
  $('identify').hidden = $('choices').hidden = true;
  $('scanArea')
    .querySelectorAll('.mark')
    .forEach((el) => el.remove());
  $('feedback').textContent = '';
  on('test', false);
}
function setFrame(frame) {
  endExercise();
  state.frame = Math.max(0, Math.min(last, Math.round(frame)));
  draw();
}
function nameOfFrame() {
  const i = state.frame;
  if (i === long) return 'Long axis · 0°';
  if (i === last) return 'Short axis · 90°';
  if (i < long) return 'Finding the window';
  return 'Rotating · ' + sweep[i].degrees + '°';
}
function labelPlay() {
  $('play').textContent = state.timer
    ? 'Pause'
    : guided()
      ? state.frame < long
        ? 'Find long axis'
        : state.frame < last
          ? 'Turn to short axis'
          : 'Restart tour'
      : state.frame === last
        ? 'Replay sweep'
        : 'Play sweep';
}
function pause() {
  clearInterval(state.timer);
  state.timer = null;
  labelPlay();
}
function play() {
  if (state.timer) {
    pause();
    return;
  }
  if (state.frame === last) setFrame(0);
  const end = guided() && state.frame < long ? long : last;
  state.timer = setInterval(() => {
    setFrame(state.frame + 1);
    if (state.frame >= end) pause();
  }, 110);
  labelPlay();
}
function draw() {
  const i = state.frame;
  document.body.className = guided() ? 'guide-mode' : 'probe-mode';
  $('instruction').textContent = guided()
    ? 'Follow the sweep one stop at a time. Playback pauses at each teaching view so you can compare it and identify the organ.'
    : 'Drag across the probe view to find the window and rotate through the gallbladder. Watch its outline change on the monitor.';
  $('gripHint').hidden = guided();
  $('tour').hidden = state.assets;
  $('assets').hidden = !state.assets;
  on('assetTab', state.assets);
  on('tourTab', !state.assets);
  $('position').value = i;
  $('position').setAttribute('aria-valuetext', nameOfFrame());
  $('readout').textContent = nameOfFrame();
  labelPlay();
  $('scanTitle').textContent = state.section ? 'Anatomical section' : 'Simulated scan';
  $('legend').hidden = !state.section;
  $('test').disabled = ![long, last].includes(i) || $('scan').hidden;
  on('section', state.section);
  on('compare', state.compare);
  $('refPanel').hidden = $('referenceNote').hidden = !state.compare;
  $('stage').classList.toggle('comparing', state.compare);
  media('pose', imageFile('pose', i));
  media('scan', imageFile(state.section ? 'section' : 'scan', i));
  if (state.compare) {
    media('ref', refFile());
    $('ref').alt = 'Acquired ' + axisName().toLowerCase() + ' gallbladder ultrasound in a different case.';
    $('referenceNote').textContent =
      (i === long || i === last ? 'Reference for this teaching view' : 'Nearest teaching reference') +
      ' · ' +
      axisName() +
      ' · ' +
      refCredit();
  }
  $('steps')
    .querySelectorAll('button')
    .forEach((b, k) => {
      const active = stops[k][0] === i;
      b.setAttribute('aria-current', active ? 'step' : 'false');
      b.setAttribute('aria-pressed', String(active));
    });
  if (state.assets) drawAssets();
}
stops.forEach(([frame, name]) => {
  const b = document.createElement('button');
  b.textContent = name;
  b.onclick = () => {
    pause();
    setFrame(frame);
  };
  $('steps').append(b);
});
$('play').onclick = play;
$('position').oninput = (e) => {
  pause();
  setFrame(Number(e.target.value));
};
$('variant').value = location.hash === '#guided' ? 'guide' : 'probe';
if (guided()) state.frame = 0;
$('variant').onchange = () => {
  pause();
  endExercise();
  history.replaceState(null, '', guided() ? '#guided' : '#probe');
  draw();
};
window.addEventListener('hashchange', () => {
  pause();
  endExercise();
  $('variant').value = location.hash === '#guided' ? 'guide' : 'probe';
  draw();
});
$('section').onclick = () => {
  pause();
  endExercise();
  state.section = !state.section;
  draw();
};
$('compare').onclick = () => {
  pause();
  state.compare = !state.compare;
  draw();
  if (state.exercise) drawMarkers();
};
function showAssets(visible) {
  pause();
  endExercise();
  state.assets = visible;
  draw();
}
$('assetTab').onclick = () => showAssets(true);
$('tourTab').onclick = $('return').onclick = () => showAssets(false);
let start;
$('drag').onpointerdown = (e) => {
  if (guided() || e.button !== 0 || !e.isPrimary) return;
  pause();
  start = { x: e.clientX, frame: state.frame };
  e.currentTarget.setPointerCapture(e.pointerId);
};
$('drag').onpointermove = (e) => {
  if (!start || !e.currentTarget.hasPointerCapture(e.pointerId)) return;
  setFrame(start.frame + (last * (e.clientX - start.x)) / (e.currentTarget.clientWidth * 0.75));
};
$('drag').onlostpointercapture = () => {
  start = null;
};
document.addEventListener('visibilitychange', () => {
  if (document.hidden) pause();
});

function inside(x, y, polygon) {
  let hit = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [a, b] = polygon[i],
      [c, d] = polygon[j];
    if (b > y !== d > y && x < ((c - a) * (y - b)) / (d - b) + a) hit = !hit;
  }
  return hit;
}
function scanRect() {
  const box = $('scanArea').getBoundingClientRect();
  const scale = Math.min(box.width / 500, box.height / 350);
  return { box, scale, x: (box.width - 500 * scale) / 2, y: (box.height - 350 * scale) / 2 };
}
function answerPoints() {
  const outline = sweep[state.frame].outline;
  const center = outline.reduce(
    (sum, p) => [sum[0] + p[0] / outline.length, sum[1] + p[1] / outline.length],
    [0, 0],
  );
  const liver = [center[0], center[1] - 66];
  return state.frame === long ? [center, liver] : [liver, center];
}
function drawMarkers() {
  $('scanArea')
    .querySelectorAll('.mark')
    .forEach((el) => el.remove());
  const rect = scanRect();
  answerPoints().forEach(([x, y], i) => {
    const span = document.createElement('span');
    span.className = 'mark';
    span.textContent = i ? 'B' : 'A';
    span.style.left = rect.x + x * rect.scale + 'px';
    span.style.top = rect.y + y * rect.scale + 'px';
    $('scanArea').append(span);
  });
}
new ResizeObserver(() => {
  if (state.exercise) drawMarkers();
}).observe($('scanArea'));
function check(x, y) {
  const hit = inside(x, y, sweep[state.frame].outline);
  $('feedback').textContent = hit
    ? 'Correct. You found the gallbladder beside the liver in this view.'
    : 'Try again. Follow the dark lumen to its boundary with the liver.';
}
$('test').onclick = () => {
  pause();
  if (state.exercise) {
    endExercise();
    return;
  }
  state.section = false;
  state.exercise = true;
  draw();
  $('identify').hidden = $('choices').hidden = false;
  on('test', true);
  $('feedback').textContent = 'Point inside the gallbladder, or choose a marked region.';
  drawMarkers();
};
$('identify').onclick = (e) => {
  if (!e.detail) {
    $('choices').querySelector('button').focus();
    return;
  }
  const r = scanRect();
  check((e.clientX - r.box.left - r.x) / r.scale, (e.clientY - r.box.top - r.y) / r.scale);
};
$('choices')
  .querySelectorAll('button')
  .forEach((b, i) => {
    b.onclick = () => check(...answerPoints()[i]);
  });

const groups = ['Patient & probe', 'Internal anatomy', 'Simulated scan', 'Acquired reference'];
groups.forEach((label, i) => {
  const b = document.createElement('button');
  b.textContent = label;
  b.onclick = () => {
    state.group = i;
    drawAssets();
  };
  $('assetControls').append(b);
});
$('assetFrame').onchange = (e) => {
  if (+e.target.value >= 0) setFrame(+e.target.value);
};
function drawAssets() {
  const i = state.frame;
  $('assetFrame').value = [long, last].includes(i) ? String(i) : '-1';
  $('assetFrame').options[0].disabled = true;
  $('assetTitle').textContent = 'Gallbladder · ' + nameOfFrame();
  $('assetIntro').textContent = 'Abdomen tour / Gallbladder sweep / ' + nameOfFrame();
  const groupsData = [
    [
      'Probe contact',
      'The torso surface and beam share the s1233 CT coordinates. The curved housing and orientation dot are authored. Contact and angle still need scanning-technique review.',
      [imageFile('pose', i)],
      source.case,
    ],
    [
      'Liver and gallbladder',
      'The section follows the current probe plane. The gallbladder label supplies its outer silhouette. A separate layered wall was not segmented.',
      [imageFile('section', i)],
      source.case,
    ],
    [
      'Tissue appearance',
      'Compare the lumen, wall brightness, and echoes behind it. The tissue response is illustrative. The two cases differ in depth and shape.',
      [imageFile('scan', i), refFile()],
      anchor() === 'long' ? source.long : source.short,
    ],
    [
      axisName() + ' comparison',
      refCredit() +
        '. The acquired image is a comparison for the named endpoint. The intermediate poses have no registered clinical counterpart.',
      [refFile()],
      anchor() === 'long' ? source.long : source.short,
    ],
  ];
  const [title, note, images, url] = groupsData[state.group];
  const bindings = [
    's1233 external envelope · authored curved array · same-case right ribs 6–10',
    's1233 segmentations · liver, gallbladder, portal and splenic vein',
    'Frame ' + i + ' of 0–48 · 13.3 cm modeled depth · 72° sector',
    anchor() === 'long'
      ? 'Figure 2 · complete frame, resized'
      : 'Cine frame 12 · full frame, converted to WebP',
  ];
  $('binding').textContent = bindings[state.group];
  $('assetName').textContent = title;
  $('assetFinding').textContent = note;
  $('assetSource').href = url;
  $('assetControls')
    .querySelectorAll('button')
    .forEach((b, k) => b.setAttribute('aria-pressed', String(k === state.group)));
  const evidence = $('assetEvidence');
  evidence.replaceChildren();
  evidence.className = images.length > 1 ? 'paired' : '';
  images.forEach((path, k) => {
    const img = document.createElement('img');
    img.className = 'evidenceImage';
    img.src = path;
    img.alt = images.length === 1 ? title : k ? 'Acquired comparison' : 'Simulation';
    img.onerror = () => img.replaceWith(document.createTextNode(img.alt + ' unavailable.'));
    evidence.append(img);
  });
}
draw();
