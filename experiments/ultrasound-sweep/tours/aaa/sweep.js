import { chapters, pose, render } from '../../cases/vascular/playable.js';
import { getAcquisition, measure } from '../../cases/vascular/playable-model.js';

const byId = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const embedded = params.get('embed') === '1';
const playButton = byId('play');
const position = byId('position');
const scan = byId('scanCanvas').getContext('2d');
const locator = byId('sceneCanvas').getContext('2d');
const overlayButton = byId('section');
const orbit = byId('orbit');
let record;
let chapter;
let frame = 0;
let animation = 0;
let lastTick = 0;
let overlay = false;
let yaw = 0;
let ready = false;

if (embedded) {
  document.documentElement.classList.add('embeddedSweep');
  document.querySelector('.mast').hidden = true;
}

function notify(status) {
  if (embedded) parent.postMessage({ type: 'sweep-status', status, frame }, location.origin);
}

function updatePlay() {
  playButton.textContent = animation ? 'Pause' : frame === chapter.frames - 1 ? 'Replay sweep' : 'Play sweep';
}

function drawLegend(entries) {
  const legend = byId('legend');
  legend.hidden = !overlay;
  if (!overlay) return;
  legend.replaceChildren(...(entries.length ? entries : [{ label: 'No identifiable tissue in this frame' }]).map(({ label, color }) => {
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

function draw(next) {
  frame = next;
  scan.save();
  locator.save();
  try {
    drawLegend(render(scan, chapter, frame, record, { overlay }) ?? []);
    pose(locator, chapter, frame, record, { yaw });
  } finally {
    scan.restore();
    locator.restore();
  }

  const acquisition = getAcquisition(record, chapter, frame);
  const measurement = measure(record, chapter, frame, acquisition)
    .map(({ hi, lo, transverse }) => `${Number((hi - lo).toFixed(1))} mm ${transverse ? 'transverse' : 'AP'}`)
    .join(' × ');
  byId('measurement').textContent = acquisition.blind ? 'Limited window · measurement withheld' : measurement;
  position.value = frame;
  position.setAttribute('aria-valuetext', `Frame ${frame} of ${chapter.frames - 1}`);
  byId('frameNumber').textContent = `${frame} / ${chapter.frames - 1}`;
  byId('observation').hidden = frame !== chapter.evidenceFrame;
  syncLinks();
  notify('frame');
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
overlayButton.onclick = () => {
  overlay = !overlay;
  overlayButton.setAttribute('aria-pressed', String(overlay));
  draw(frame);
};
orbit.oninput = () => {
  yaw = orbit.valueAsNumber * Math.PI / 180;
  byId('yaw').value = orbit.value + '°';
  draw(frame);
};
byId('resetView').onclick = () => {
  orbit.value = 0;
  orbit.oninput();
};
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

try {
  const id = params.get('case');
  if (!/^aaa-[a-z-]+$/.test(id ?? '')) throw new Error('Invalid AAA case ID.');
  const response = await fetch(id + '.json');
  if (!response.ok) throw new Error('AAA case record unavailable.');
  record = await response.json();
  if (record.id !== id || record.family !== 'aaa') throw new Error('AAA case record does not match the link.');

  const available = chapters(record);
  chapter = available.find(({ id }) => id === params.get('chapter')) ?? available[0];
  position.max = chapter.frames - 1;
  const requested = params.get('frame');
  const initial = /^\d+$/.test(requested ?? '') && Number(requested) < chapter.frames ? Number(requested) : 0;

  document.title = chapter.title + ' · Ultrasound anatomy';
  byId('caseTitle').textContent = record.title;
  byId('chapterTitle').textContent = chapter.title;
  byId('observation').textContent = chapter.observation;
  byId('caseLink').href = '../../cases/' + record.id + '.html';
  byId('sweepLinks').hidden = embedded;
  byId('exam').hidden = false;
  byId('status').hidden = true;
  draw(initial);
  updatePlay();
  ready = true;
  notify('ready');
} catch (error) {
  fail(error);
}
