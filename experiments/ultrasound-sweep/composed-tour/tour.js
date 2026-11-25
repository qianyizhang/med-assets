'use strict';

const chapters = [...document.querySelectorAll('.chapters a')];
const container = document.getElementById('player');
const transport = document.getElementById('playTour');
const progress = document.getElementById('tourProgress');
const openSweep = document.getElementById('openSweep');
const restart = document.getElementById('restart');
const sweepURL = new URL(container.dataset.sweepUrl ?? '../index.html', location.href);
const chapterParam = container.dataset.sweepChapterParam ?? 'sweep';
let active;
let player;
let observer;
let standaloneURL;
let shownQuery;
let ready = false;
let playing = false;
let finished = false;

function updateTransport() {
  transport.disabled = !playing && !ready;
  transport.textContent = playing ? 'Pause tour' : finished ? 'Replay tour' : 'Play tour';
}

function send(command) {
  player.contentWindow.postMessage({ type: 'sweep-transport', command }, location.origin);
}

function showChapter(link, requestedFrame) {
  const chapter = document.getElementById(link.dataset.chapter);
  const heading = chapter.querySelector('h2').textContent;
  shownQuery = location.search;
  if (active) {
    active.removeAttribute('aria-current');
    document.getElementById(active.dataset.chapter).hidden = true;
  }
  active = link;
  active.setAttribute('aria-current', 'step');
  chapter.hidden = false;
  ready = false;
  updateTransport();

  const numericFrame = Number(requestedFrame);
  const frame = /^\d+$/.test(requestedFrame ?? '') && Number.isSafeInteger(numericFrame) ? String(numericFrame) : '0';
  for (const evidence of chapter.querySelectorAll('.evidence a')) {
    const savedFrame = new URL(evidence.href).searchParams.get('frame');
    if (savedFrame === frame) {
      evidence.setAttribute('aria-current', 'true');
    } else {
      evidence.removeAttribute('aria-current');
    }
  }

  standaloneURL = new URL(sweepURL);
  standaloneURL.searchParams.set(chapterParam, chapter.id);
  standaloneURL.searchParams.set('frame', frame);
  openSweep.href = standaloneURL.href;
  restart.href = active.href;

  const next = chapters[chapters.indexOf(active) + 1];
  const advance = document.getElementById('advance');
  advance.href = next?.href ?? chapters[0].href;
  advance.textContent = next ? 'Next chapter · ' + (next.dataset.label ?? next.textContent.trim().replace(/^\d+\.\s*/, '')) : 'Return to first chapter';
  document.querySelector('.chapterControls').hidden = false;

  observer?.disconnect();
  const viewer = document.createElement('iframe');
  viewer.title = heading + ' · Probe and scan';
  const embedURL = new URL(standaloneURL);
  embedURL.searchParams.set('embed', '1');
  viewer.src = embedURL.href;
  viewer.addEventListener('load', () => {
    const body = viewer.contentDocument?.body;
    if (!body || viewer !== player) return;
    observer = new ResizeObserver(() => {
      viewer.style.height = Math.ceil(body.getBoundingClientRect().height) + 'px';
    });
    observer.observe(body);
  });
  player = viewer;
  container.replaceChildren(player);
  progress.textContent = heading;
}

function advanceTour(link) {
  const url = new URL(link.href);
  if (location.hash === '#exam') url.hash = '#exam';
  history.replaceState(null, '', url);
  showChapter(link);
}

transport.addEventListener('click', () => {
  playing = !playing;
  if (!playing) send('pause');
  else if (finished) {
    finished = false;
    advanceTour(chapters[0]);
  } else if (ready) {
    send('play');
  }
  updateTransport();
});

restart.addEventListener('click', (event) => {
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  if (location.href !== active.href) history.pushState(null, '', active.href);
  playing = false;
  finished = false;
  showChapter(active);
});

window.addEventListener('message', ({ source, origin, data }) => {
  if (source !== player?.contentWindow || origin !== location.origin || data?.type !== 'sweep-status') return;
  if (data.status === 'ready') {
    ready = true;
    if (playing) send('play');
  } else if (data.status === 'frame' && Number.isInteger(data.frame) && data.frame >= 0) {
    standaloneURL.searchParams.set('frame', data.frame);
    openSweep.href = standaloneURL.href;
  } else if (data.status === 'error') {
    ready = false;
    playing = false;
  } else if (data.status === 'paused') {
    playing = false;
  } else if (data.status === 'ended' && playing) {
    const next = chapters[chapters.indexOf(active) + 1];
    if (next) {
      advanceTour(next);
    } else {
      playing = false;
      finished = true;
      progress.textContent = 'Tour complete';
      if (document.getElementById('impression')) {
        const advance = document.getElementById('advance');
        advance.href = '#impression';
        advance.textContent = 'Read the impression';
      }
    }
  }
  updateTransport();
});

function showLocation() {
  const params = new URLSearchParams(location.search);
  playing = false;
  finished = false;
  showChapter(chapters.find((link) => link.dataset.chapter === params.get('chapter')) ?? chapters[0], params.get('frame'));
}

window.addEventListener('popstate', () => {
  if (location.search !== shownQuery) showLocation();
});
showLocation();
