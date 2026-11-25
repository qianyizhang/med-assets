import { chapters, render } from '../../cases/vascular/playable.js';
import { getAcquisition, measure } from '../../cases/vascular/playable-model.js';

const byId = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const embedded = params.get('embed') === '1';
const playButton = byId('play');
const position = byId('position');
const scanCanvas = byId('scanCanvas');
const scan = scanCanvas.getContext('2d');
const overlayButton = byId('section');
const colorButton = byId('colorFlow');
const cameraPresets = [['oblique', 'Oblique'], ['axial', 'Axial'], ['coronal', 'Coronal'], ['sagittal', 'Sagittal']];
const opacity = byId('torsoOpacity');
const images = new Map();
let record;
let chapter;
let presentation;
let scene;
let fallback = false;
let frame = 0;
let animation = 0;
let lastTick = 0;
let mode = 'scan';
let ready = false;

if (embedded) {
  document.documentElement.classList.add('embeddedSweep');
  document.querySelector('.mast').hidden = true;
}

function notify(status) {
  if (embedded) parent.postMessage({ type: 'sweep-status', status, frame }, location.origin);
}

function updatePlay() {
  playButton.disabled = !ready;
  playButton.textContent = animation ? 'Pause' : frame === chapter.frames - 1 ? 'Replay sweep' : 'Play sweep';
}

function legend(id, entries) {
  byId(id).replaceChildren(...entries.map(({ label, color }) => {
    const li = document.createElement('li');
    if (color) li.style.setProperty('--part-color', color);
    li.textContent = label;
    return li;
  }));
}

function syncLinks() {
  if (embedded) return;
  const target = new URL(record.id + '.html', location.href);
  target.searchParams.set('chapter', chapter.id);
  target.searchParams.set('frame', frame);
  target.hash = 'exam';
  byId('tourLink').href = target.href;
}

function prepare(kind, index) {
  const key = kind + '-' + String(index).padStart(2, '0');
  if (!images.has(key)) {
    const entry = { image: null };
    images.set(key, entry);
    if (!presentation?.mediaRoot) return entry;
    const image = new Image();
    image.src = new URL(key + '.webp', new URL(presentation.mediaRoot, document.baseURI));
    entry.pending = image.decode().then(() => { entry.image = image; }, () => {});
  }
  return images.get(key);
}

async function prepareSequence() {
  const frames = Array.from({ length: chapter.frames }, (_, index) => index);
  const kinds = presentation?.hasColor ? ['scan', 'section', 'color'] : ['scan', 'section'];
  for (let start = 0; start < frames.length; start += 6) {
    const batch = frames.slice(start, start + 6);
    await Promise.all(batch.flatMap((index) => kinds.map((kind) => prepare(kind, index).pending)));
  }
}

function drawCalipers(calipers) {
  scan.save();
  scan.strokeStyle = '#fff5cf';
  scan.lineWidth = 1.4;
  scan.setLineDash([3, 3]);
  for (const { endpointsPx: [[x1, y1], [x2, y2]] } of calipers) {
    scan.beginPath();
    scan.moveTo(x1, y1);
    scan.lineTo(x2, y2);
    scan.stroke();
  }
  scan.setLineDash([]);
  for (const { endpointsPx } of calipers) {
    for (const [x, y] of endpointsPx) {
      scan.beginPath();
      scan.moveTo(x - 4, y);
      scan.lineTo(x + 4, y);
      scan.moveTo(x, y - 4);
      scan.lineTo(x, y + 4);
      scan.stroke();
    }
  }
  scan.restore();
}

function draw(next) {
  const overlay = mode === 'section';
  const color = mode === 'color';
  const { image } = prepare(mode, next);
  const acquisition = getAcquisition(record, chapter, next);
  const frameData = presentation?.frames[next];
  const calipers = fallback ? measure(record, chapter, next, acquisition)
    .map(({ hi, lo, transverse }) => ({ millimetres: hi - lo, transverse }))
    : frameData?.calipers ?? [];
  if (fallback && scan) {
    scan.save();
    try {
      const entries = render(scan, chapter, next, record, { overlay });
      if (overlay) legend('legend', entries ?? []);
    } finally {
      scan.restore();
    }
  } else if (image && scan) {
    scan.drawImage(image, 0, 0, scanCanvas.width, scanCanvas.height);
    drawCalipers(calipers);
  } else if (scan) {
    scan.clearRect(0, 0, scanCanvas.width, scanCanvas.height);
  }

  scanCanvas.hidden = (!image && !fallback) || !scan;
  byId('scanStatus').hidden = !scanCanvas.hidden;
  byId('scanStatus').textContent = 'Scan unavailable for this frame.';
  const scanTitle = fallback ? 'Modeled ultrasound' : 'Simulated scan';
  byId('scanTitle').textContent = overlay ? 'Anatomical section' : color ? 'Modeled color flow' : scanTitle;
  overlayButton.setAttribute('aria-pressed', String(overlay));
  colorButton.setAttribute('aria-pressed', String(color));
  byId('legend').hidden = !overlay || scanCanvas.hidden;

  scene?.setFrame(next);
  frame = next;
  const measurement = calipers
    .map(({ millimetres, transverse }, index) => {
      const axis = (transverse ?? (index > 0)) ? 'transverse' : 'AP';
      return `${Number(millimetres.toFixed(1))} mm ${axis}`;
    })
    .join(' × ');
  const limited = frameData?.limited ?? acquisition.blind;
  byId('measurement').textContent = limited ? 'Limited window · measurement withheld' : measurement;
  position.value = frame;
  position.setAttribute('aria-valuetext', `Frame ${frame} of ${chapter.frames - 1}`);
  byId('frameNumber').textContent = `${frame} / ${chapter.frames - 1}`;
  byId('observation').hidden = frame !== chapter.evidenceFrame;
  syncLinks();
  notify('frame');
}

function setCameraPreset(active) {
  for (const [id] of cameraPresets) byId('cameraPreset-' + id).setAttribute('aria-pressed', String(id === active));
}

for (const [id, label] of cameraPresets) {
  const button = document.createElement('button');
  button.id = 'cameraPreset-' + id;
  button.className = 'viewButton';
  button.type = 'button';
  button.textContent = label;
  button.onclick = () => scene?.setViewPreset(id);
  byId('cameraPresets').append(button);
}

function updateOpacity() {
  byId('torsoOpacityValue').value = opacity.value + '%';
  opacity.setAttribute('aria-valuetext', opacity.value + '%');
  scene?.setTorsoOpacity(opacity.valueAsNumber / 100);
}

async function startScene() {
  const canvas = byId('sceneCanvas');
  if (fallback) {
    byId('sceneStatus').textContent = 'The shared torso and sector acquisition are not included in this build.';
    return;
  }
  try {
    if (!presentation) throw new Error('Case scene unavailable.');
    const { createSweepScene } = await import('../../scene.js');
    const { config, frames } = presentation;
    const meshPaths = Object.fromEntries(Object.entries(config.meshPaths ?? {})
      .map(([name, path]) => [name, new URL(path, document.baseURI).href]));
    canvas.hidden = false;
    scene = await createSweepScene({
      canvas, frames, config: { ...config, meshPaths }, onViewPresetChange: setCameraPreset,
    });
    scene.setFrame(frame);
    updateOpacity();
    byId('sceneStatus').hidden = true;
    byId('sceneHelp').hidden = false;
    byId('cameraPresets').disabled = false;
    opacity.disabled = false;
  } catch (error) {
    scene?.dispose();
    scene = null;
    canvas.hidden = true;
    byId('sceneStatus').textContent = '3D probe and scan plane unavailable.';
    console.warn('AAA sweep 3D scene unavailable.', error);
  }
}

function stop(status) {
  if (!animation) return;
  cancelAnimationFrame(animation);
  animation = 0;
  updatePlay();
  if (status) notify(status);
}

function fail(error) {
  stop();
  ready = false;
  byId('exam').hidden = true;
  byId('status').hidden = false;
  byId('status').textContent = 'This modeled sweep is unavailable.';
  notify('error');
  console.error(error);
}

function tick(time) {
  if (time - lastTick >= 100) {
    try {
      draw(frame + 1);
    } catch (error) {
      fail(error);
      return;
    }
    lastTick = time;
    if (frame === chapter.frames - 1) {
      stop('ended');
      return;
    }
  }
  animation = requestAnimationFrame(tick);
}

function play() {
  if (!ready || animation) return;
  if (frame === chapter.frames - 1) draw(0);
  lastTick = performance.now();
  animation = requestAnimationFrame(tick);
  updatePlay();
}

function seek(target) {
  if (!ready) return;
  stop('paused');
  draw(target);
  updatePlay();
  if (!embedded) {
    const url = new URL(location.href);
    url.searchParams.set('chapter', chapter.id);
    url.searchParams.set('frame', frame);
    history.replaceState(null, '', url);
  }
}

playButton.onclick = () => animation ? stop('paused') : play();
position.oninput = () => seek(position.valueAsNumber);
byId('evidence').onclick = () => seek(chapter.evidenceFrame);
function toggleMode(next) {
  if (!ready) return;
  mode = mode === next ? 'scan' : next;
  draw(frame);
}

overlayButton.onclick = () => toggleMode('section');
colorButton.onclick = () => toggleMode('color');
opacity.oninput = updateOpacity;
document.addEventListener('visibilitychange', () => {
  if (document.hidden) stop('paused');
});

if (embedded) {
  window.addEventListener('message', ({ source, origin, data }) => {
    if (source !== parent || origin !== location.origin || data?.type !== 'sweep-transport') return;
    if (data.command === 'play') play();
    if (data.command === 'pause') stop();
  });
}

async function loadSceneData(id) {
  try {
    const response = await fetch(id + '.scene.json');
    if (!response.ok) throw new Error('Case scene data unavailable.');
    const data = (await response.json())[chapter.id];
    if (!data?.config || !data?.mediaRoot || data?.frames?.length !== chapter.frames)
      throw new Error('Case scene data does not bind to the chapter frames.');
    return data;
  } catch (error) {
    console.warn('AAA sweep acquisition media unavailable.', error);
    return null;
  }
}

try {
  const id = params.get('case');
  if (!/^aaa-[a-z-]+$/.test(id ?? '')) throw new Error('Invalid AAA case ID.');
  const response = await fetch(id + '.json');
  if (!response.ok) throw new Error('AAA case record unavailable.');
  record = await response.json();
  if (record.id !== id || record.family !== 'aaa') throw new Error('AAA case record does not match the link.');

  const available = chapters(record);
  chapter = available.find(({ id }) => id === params.get('chapter')) ?? available[0];
  const requested = params.get('frame');
  frame = /^\d+$/.test(requested ?? '') && Number(requested) < chapter.frames ? Number(requested) : 0;
  position.max = chapter.frames - 1;
  position.value = frame;

  document.title = chapter.title + ' · Ultrasound anatomy';
  byId('caseTitle').textContent = record.title;
  byId('chapterTitle').textContent = chapter.title;
  byId('observation').textContent = chapter.observation;
  byId('caseLink').href = '../../cases/' + record.id + '.html';
  byId('sweepLinks').hidden = embedded;
  byId('exam').hidden = false;
  byId('status').hidden = true;
  byId('evidence').disabled = true;
  overlayButton.disabled = true;
  position.disabled = true;
  updatePlay();
  syncLinks();

  fallback = record.sharedSweepAvailable === false;
  byId('anatomySources').hidden = fallback;
  presentation = fallback ? null : await loadSceneData(id);
  if (fallback) {
    scanCanvas.width = 800;
    scanCanvas.height = 440;
  }
  const config = presentation?.config;
  colorButton.hidden = !presentation?.hasColor;
  if (config) {
    legend('sceneLegend', [{ label: 'Imaging sector', color: '#84b5d1' }, ...config.parts]);
    legend('legend', config.overlayParts ?? config.parts);
  }

  const sceneReady = startScene();
  await prepare('scan', frame).pending;
  draw(frame);
  await Promise.all([sceneReady, prepareSequence()]);
  position.disabled = false;
  byId('evidence').disabled = false;
  overlayButton.disabled = false;
  colorButton.disabled = !presentation?.hasColor;
  ready = true;
  updatePlay();
  notify('ready');
} catch (error) {
  fail(error);
}
