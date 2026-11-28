'use strict';

const container = document.getElementById('player');
const transport = document.getElementById('playTour');
const timeline = document.getElementById('tourPosition');
const sectionPicker = document.getElementById('tourSection');
const casePlayer = container.hasAttribute('data-case-player');
const frameNumber = document.getElementById('tourFrameNumber');
const progress = document.getElementById('tourProgress');
const openSweep = document.getElementById('openSweep');
const sweepURL = new URL(container.dataset.sweepUrl ?? '../index.html', location.href);
const chapterParam = container.dataset.sweepChapterParam ?? 'sweep';
const frameDuration = Number(container.dataset.frameMs) || (chapterParam === 'chapter' ? 100 : 110);

let totalFrames = 0;
const sections = [...document.querySelectorAll('.chapters a[data-chapter]')].map((link) => {
  const id = link.dataset.chapter;
  const start = Number(link.dataset.start ?? 0);
  const end = Number(link.dataset.end ?? (chapterParam === 'chapter' ? 28 : 48));
  const content = document.getElementById(id);
  const label = link.dataset.label ?? content.querySelector('h2').textContent;
  const section = { id, start, end, link, content, label, sourceSweep: content.dataset.sourceSweep, sweep: link.dataset.sweep ?? id, offset: totalFrames };
  totalFrames += end - start + 1;
  return section;
});
const last = totalFrames - 1;

for (const section of sections) {
  section.link.style.setProperty('--marker-position', (last ? section.offset / last * 100 : 0) + '%');
}
timeline.min = 0;
timeline.max = last;
timeline.step = 1;

let active;
let mountedSweep;
let player;
let observer;
let target = 0;
let displayed = -1;
let requestId = 0;
let pending;
let ready = false;
let rangeEnabled = false;
let playing = false;
let animation = 0;
let lastTick = 0;
let shownQuery;
let scrubbing = false;

function sourceFrame(section, index) {
  return section.start + index - section.offset;
}

function sectionAt(index) {
  return sections.findLast(({ offset }) => offset <= index);
}

function positionFromURL(url) {
  const chapter = url.searchParams.get('chapter');
  const view = !chapter && url.searchParams.get('view');
  const section = sections.find(({ id, content }) => id === chapter || (view && content.dataset.viewImage === view)) ?? sections[0];
  const value = url.searchParams.get('frame');
  if (casePlayer) {
    const fallback = view ? Number(section.content.dataset.evidenceFrame) : section.start;
    const parsed = Number.parseInt(value, 10);
    const frame = Number.isFinite(parsed) ? Math.max(section.start, Math.min(section.end, parsed)) : fallback;
    return section.offset + frame - section.start;
  }
  const frame = Number(value);
  return /^\d+$/.test(value ?? '') && frame >= section.start && frame <= section.end
    ? section.offset + frame - section.start : section.offset;
}

function updateHistory(action, hash = location.hash) {
  const url = new URL(location.href);
  url.searchParams.set('chapter', active.id);
  url.searchParams.set('frame', sourceFrame(active, target));
  url.hash = hash;
  shownQuery = url.search;
  if (url.href !== location.href) history[action + 'State'](null, '', url);
}

function standalone(section, index) {
  const url = new URL(section.sourceSweep ? '../../index.html' : sweepURL, location.href);
  url.searchParams.set(section.sourceSweep ? 'sweep' : chapterParam, section.sourceSweep ?? section.sweep);
  url.searchParams.set('frame', sourceFrame(section, index));
  return url;
}

function updateTransport() {
  const finished = displayed === last && target === last;
  transport.disabled = !playing && (!ready || displayed !== target);
  transport.textContent = playing ? 'Pause tour' : finished ? 'Replay tour' : 'Play tour';
  timeline.disabled = !rangeEnabled;
}

function updatePosition() {
  const frame = sourceFrame(active, target);
  timeline.value = target;
  timeline.setAttribute('aria-valuetext', active.label + ', frame ' + frame + ', tour frame ' + (target + 1) + ' of ' + totalFrames);
  if (frameNumber) frameNumber.textContent = (target + 1) + ' / ' + totalFrames;

  for (const evidence of active.content.querySelectorAll('.evidence a')) {
    const saved = new URL(evidence.href).searchParams.get('frame');
    if (saved !== null && Number(saved) === frame) evidence.setAttribute('aria-current', 'true');
    else evidence.removeAttribute('aria-current');
  }
}

function activate(section) {
  if (active === section) return;
  if (active) {
    active.link.removeAttribute('aria-current');
    active.content.hidden = true;
  }
  active = section;
  if (sectionPicker) sectionPicker.value = section.id;
  active.link.setAttribute('aria-current', 'step');
  active.content.hidden = false;
  progress.textContent = section.label;
  if (player) player.title = section.label + ' · Probe and scan';
}

function playerKey(section) {
  return section.sourceSweep ?? (casePlayer ? 'worked-case' : section.sweep);
}

function mount(section) {
  mountedSweep = playerKey(section);
  ready = false;
  displayed = -1;
  pending = null;
  delete timeline.dataset.displayed;
  openSweep.removeAttribute('href');
  observer?.disconnect();
  progress.textContent = section.label;

  const viewer = document.createElement('iframe');
  viewer.title = section.label + ' · Probe and scan';
  const url = standalone(section, target);
  url.searchParams.set('embed', '1');
  url.searchParams.set('transport', 'tour');
  const layout = section.sourceSweep ? 'probe-scan' : container.dataset.embedLayout;
  if (layout) url.searchParams.set('layout', layout);
  viewer.src = url.href;
  viewer.addEventListener('load', () => {
    if (viewer !== player) return;
    const body = viewer.contentDocument?.body;
    if (!body?.querySelector('input#position[type="range"]')) {
      unavailable();
      return;
    }
    observer = new ResizeObserver(() => {
      viewer.style.height = Math.ceil(body.getBoundingClientRect().height) + 'px';
    });
    observer.observe(body);
  });
  player = viewer;
  container.replaceChildren(player);
}

function requestFrame() {
  if (!ready || pending?.index === target || (!pending && displayed === target)) return;
  const frame = sourceFrame(active, target);
  pending = { id: ++requestId, index: target, frame };
  player.contentWindow.postMessage({ type: 'sweep-transport', command: 'seek', sweep: active.sweep, frame, request: pending.id }, location.origin);
}

function seek(index) {
  const previous = active;
  target = Math.max(0, Math.min(last, index));
  const section = sectionAt(target);
  activate(section);
  if (playerKey(section) !== mountedSweep) mount(section);
  if (displayed !== target) {
    container.setAttribute('aria-busy', 'true');
  }
  requestFrame();
  updatePosition();
  updateTransport();
  return previous !== active;
}

function pause() {
  playing = false;
  cancelAnimationFrame(animation);
  animation = 0;
  updateTransport();
}

function unavailable() {
  ready = false;
  mountedSweep = null;
  pending = null;
  displayed = -1;
  rangeEnabled = true;
  delete timeline.dataset.displayed;
  container.setAttribute('aria-busy', 'false');
  openSweep.href = standalone(active, target).href;
  progress.textContent = active.label + ' is unavailable';
  pause();
}

function tick(time) {
  if (!playing) return;
  if (displayed === target && !pending && time - lastTick >= frameDuration) {
    if (target < last) {
      lastTick = time;
      if (seek(target + 1)) updateHistory('replace');
    }
  }
  if (playing) animation = requestAnimationFrame(tick);
}

transport.addEventListener('click', () => {
  if (playing) {
    pause();
    updateHistory('replace');
    return;
  }
  playing = true;
  lastTick = performance.now();
  if (target === last && displayed === last) {
    seek(0);
    updateHistory('replace');
  }
  animation = requestAnimationFrame(tick);
  updateTransport();
});

sectionPicker?.addEventListener('change', () => {
  sections.find(({ id }) => id === sectionPicker.value).link.click();
});

timeline.addEventListener('input', () => {
  if (!scrubbing) updateHistory('replace');
  pause();
  seek(timeline.valueAsNumber);
  updateHistory(scrubbing ? 'replace' : 'push');
  scrubbing = true;
});
timeline.addEventListener('change', () => { scrubbing = false; });

document.addEventListener('click', (event) => {
  if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const link = event.target.closest('a[href]');
  if (!link || link.target || link.hasAttribute('download')) return;
  const url = new URL(link.href);
  if (url.origin !== location.origin || url.pathname !== location.pathname ||
      !sections.some(({ id }) => id === url.searchParams.get('chapter'))) return;
  if (playing) updateHistory('replace');
  pause();
  seek(positionFromURL(url));
  updateHistory('push', url.hash);
  if (url.hash) {
    document.getElementById(url.hash.slice(1))?.scrollIntoView();
    if (url.hash === '#exam') timeline.focus({ preventScroll: true });
  }
  event.preventDefault();
});

document.addEventListener('visibilitychange', () => {
  if (document.hidden && playing) {
    pause();
    updateHistory('replace');
  }
});

window.addEventListener('message', ({ source, origin, data }) => {
  if (source !== player?.contentWindow || origin !== location.origin || data?.type !== 'sweep-status') return;
  if (data.status === 'ready') {
    ready = true;
    requestFrame();
  } else if (data.status === 'frame' && pending && data.request === pending.id && data.frame === pending.frame) {
    displayed = pending.index;
    pending = null;
    rangeEnabled = true;
    timeline.dataset.displayed = displayed;
    lastTick = performance.now();
    if (displayed === target) {
      container.setAttribute('aria-busy', 'false');
      openSweep.href = standalone(active, displayed).href;
      if (playing && displayed === last) {
        pause();
        progress.textContent = 'Tour complete';
        updateHistory('replace');
      }
    }
  } else if (data.status === 'error') {
    unavailable();
  }
  updateTransport();
});

function showLocation() {
  if (location.search === shownQuery) return;
  pause();
  shownQuery = location.search;
  seek(positionFromURL(new URL(location.href)));
}

window.addEventListener('popstate', showLocation);
showLocation();
