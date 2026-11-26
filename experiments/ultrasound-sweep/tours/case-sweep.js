const byId = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const embedded = params.get('embed') === '1';
const tourControlled = embedded && params.get('transport') === 'tour';
const scan = byId('scan').getContext('2d');
const locator = byId('pose').getContext('2d');
const seek = byId('position');
const play = byId('play');
const orbit = byId('orbit');
const overlayButton = byId('overlay');
const status = byId('status');
let record;
let chapter;
let chapterById;
let acquisition;
let current = 0;
let animation = 0;
let lastTime = 0;
let overlay = false;
let yaw = 0;
let previousLegend = '';
let ready = false;

document.documentElement.classList.toggle('embeddedSweep', embedded);
document.documentElement.classList.toggle('tourControlled', tourControlled);

function notify(status, request) {
  if (embedded) parent.postMessage({ type: 'sweep-status', status, sweep: chapter?.id, frame: current, request }, location.origin);
}

function updateLegend(entries = []) {
  const list = byId('legend');
  list.hidden = !overlay;
  if (!overlay) return;

  const items = entries?.length ? entries : [{ label: 'No identifiable tissue in this frame', color: 'transparent' }];
  const key = JSON.stringify(items);
  if (key === previousLegend) return;
  previousLegend = key;
  list.replaceChildren(...items.map(({ label, color }) => {
    const li = document.createElement('li');
    const dot = document.createElement('i');
    dot.style.backgroundColor = color;
    dot.setAttribute('aria-hidden', 'true');
    li.append(dot, document.createTextNode(label));
    return li;
  }));
}

function updatePlay() {
  play.textContent = animation ? 'Pause' : current === chapter?.frames - 1 ? 'Replay sweep' : 'Play sweep';
}

function stop(message) {
  if (!animation) return;
  cancelAnimationFrame(animation);
  animation = 0;
  updatePlay();
  if (message) notify(message);
}

function syncLinks() {
  if (embedded) return;
  const tour = new URL(record.id + '.html', location.href);
  tour.searchParams.set('chapter', chapter.id);
  tour.searchParams.set('frame', current);
  tour.hash = 'exam';
  byId('tourLink').href = tour.href;
}

function show(frame, request) {
  for (const [context, render] of [[scan, acquisition.render], [locator, acquisition.pose]]) {
    context.save();
    try {
      context.fillStyle = '#101c22';
      context.fillRect(0, 0, context.canvas.width, context.canvas.height);
      const entries = render(context, chapter, frame, record, { overlay, yaw });
      if (context === scan) updateLegend(entries);
    } finally {
      context.restore();
    }
  }
  current = frame;
  const saved = frame === chapter.evidenceFrame;
  seek.value = frame;
  seek.setAttribute('aria-valuetext', chapter.title + ', frame ' + frame + ' of ' + (chapter.frames - 1));
  byId('frameNumber').textContent = frame + ' / ' + (chapter.frames - 1);
  byId('value').textContent = saved ? chapter.measurement || 'Saved evidence frame' : '';
  byId('observed').hidden = !saved;
  updatePlay();
  syncLinks();
  notify('frame', request);
}

function failed(error) {
  stop();
  ready = false;
  byId('exam').hidden = true;
  status.hidden = false;
  status.textContent = 'This acquisition could not be displayed. The worked views and case tour remain available.';
  console.error(error);
  notify('error');
}

function render(frame, request) {
  try {
    show(frame, request);
    return true;
  } catch (error) {
    failed(error);
    return false;
  }
}

function tick(time) {
  if (time - lastTime >= 100) {
    if (!render(current + 1)) return;
    lastTime = time;
    if (current >= chapter.frames - 1) {
      stop('ended');
      return;
    }
  }
  animation = requestAnimationFrame(tick);
}

function start() {
  if (!ready || animation) return;
  if (current === chapter.frames - 1 && !render(0)) return;
  lastTime = performance.now();
  animation = requestAnimationFrame(tick);
  updatePlay();
}

function jump(frame, request) {
  if (!ready) return;
  stop('paused');
  if (!render(frame, request) || embedded) return;
  const url = new URL(location.href);
  url.searchParams.set('chapter', chapter.id);
  url.searchParams.set('frame', frame);
  history.replaceState(null, '', url);
}

function selectChapter(next) {
  if (chapter === next) return;
  chapter = next;
  seek.max = chapter.frames - 1;
  byId('view').textContent = chapter.title;
  byId('observed').textContent = chapter.observation;
}

play.onclick = () => animation ? stop('paused') : start();
seek.oninput = () => jump(seek.valueAsNumber);
byId('keyframe').onclick = () => jump(chapter.evidenceFrame);
overlayButton.onclick = () => {
  overlay = !overlay;
  overlayButton.setAttribute('aria-pressed', String(overlay));
  render(current);
};
orbit.oninput = () => {
  yaw = orbit.valueAsNumber * Math.PI / 180;
  byId('yaw').value = orbit.value + '°';
  render(current);
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
    if (source !== parent || origin !== location.origin || data?.type !== 'sweep-transport' || !ready) return;
    if (tourControlled) {
      const next = data.sweep === undefined ? chapter : chapterById.get(data.sweep);
      if (data.command === 'seek' && next && Number.isInteger(data.request) && Number.isInteger(data.frame) &&
          data.frame >= 0 && data.frame < next.frames) {
        selectChapter(next);
        jump(data.frame, data.request);
      }
      return;
    }
    if (data.command === 'play') start();
    if (data.command === 'pause') stop();
  });
}

try {
  record = JSON.parse(byId('record').textContent);
  const owner = document.querySelector('main').dataset.owner;
  acquisition = await import('../cases/' + owner + '/playable.js');
  const chapters = acquisition.chapters(record);
  chapterById = new Map(chapters.map((entry) => [entry.id, entry]));
  if (!chapters.length || chapterById.size !== chapters.length)
    throw new Error('Invalid chapter IDs');

  const boundViews = new Set(chapters.map(({ viewImage }) => viewImage));
  const workedViews = new Set(record.views.map(({ image }) => image));
  if ([...boundViews].some((image) => !workedViews.has(image)) || [...workedViews].some((image) => !boundViews.has(image)))
    throw new Error('Unmapped worked view');
  for (const { id, frames, evidenceFrame } of chapters) {
    if (!Number.isInteger(frames) || frames < 3 || !Number.isInteger(evidenceFrame) || evidenceFrame < 0 || evidenceFrame >= frames)
      throw new Error('Invalid chapter ' + id);
  }

  const requested = params.get('chapter');
  const view = params.get('view');
  selectChapter((requested ? chapterById.get(requested) : chapters.find(({ viewImage }) => viewImage === view)) ?? chapters[0]);
  const rawFrame = params.get('frame');
  const initial = /^\d+$/.test(rawFrame ?? '') && Number(rawFrame) < chapter.frames
    ? Number(rawFrame) : !requested && view ? chapter.evidenceFrame : 0;

  show(initial);
  ready = true;
  byId('exam').hidden = false;
  status.hidden = true;
  notify('ready');
} catch (error) {
  failed(error);
}
