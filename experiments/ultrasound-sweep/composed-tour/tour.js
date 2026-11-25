'use strict';

const chapters = [...document.querySelectorAll('.chapters a')];
const container = document.getElementById('player');
const transport = document.getElementById('playTour');
const progress = document.getElementById('tourProgress');
const openSweep = document.getElementById('openSweep');
let active;
let player;
let observer;
let standaloneURL;
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
  if (active) {
    active.removeAttribute('aria-current');
    document.getElementById(active.dataset.chapter).hidden = true;
  }
  active = link;
  active.setAttribute('aria-current', 'step');
  chapter.hidden = false;
  ready = false;
  updateTransport();

  let frame = '0';
  for (const evidence of chapter.querySelectorAll('.evidence a')) {
    const savedFrame = new URL(evidence.href).searchParams.get('frame');
    if (savedFrame === requestedFrame) {
      frame = savedFrame;
      evidence.setAttribute('aria-current', 'true');
    } else {
      evidence.removeAttribute('aria-current');
    }
  }

  standaloneURL = new URL('../index.html', location.href);
  standaloneURL.searchParams.set('sweep', chapter.id);
  standaloneURL.searchParams.set('frame', frame);
  openSweep.href = standaloneURL.href;
  document.getElementById('restart').href = active.href;

  const next = chapters[chapters.indexOf(active) + 1];
  const advance = document.getElementById('advance');
  advance.href = next?.href ?? chapters[0].href;
  advance.textContent = next ? 'Next chapter · ' + next.textContent.slice(3) : 'Return to first chapter';
  document.querySelector('.chapterControls').hidden = false;

  observer?.disconnect();
  const viewer = document.createElement('iframe');
  viewer.title = chapter.querySelector('h2').textContent + ' · Probe and scan';
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
  progress.textContent = active.textContent + ' · ' + chapter.querySelector('h2').textContent;
}

function advanceTour(link) {
  history.replaceState(null, '', link.href);
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

window.addEventListener('message', ({ source, origin, data }) => {
  if (source !== player?.contentWindow || origin !== location.origin || data?.type !== 'sweep-status') return;
  if (data.status === 'ready') {
    ready = true;
    if (playing) send('play');
  } else if (data.status === 'frame') {
    standaloneURL.searchParams.set('frame', data.frame);
    openSweep.href = standaloneURL.href;
  } else if (data.status === 'paused' || data.status === 'error') {
    playing = false;
  } else if (data.status === 'ended' && playing) {
    const next = chapters[chapters.indexOf(active) + 1];
    if (next) {
      advanceTour(next);
    } else {
      playing = false;
      finished = true;
      progress.textContent = 'Tour complete';
    }
  }
  updateTransport();
});

const params = new URLSearchParams(location.search);
showChapter(chapters.find((link) => link.dataset.chapter === params.get('chapter')) ?? chapters[0], params.get('frame'));
