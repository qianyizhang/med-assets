'use strict';

const $ = (id) => document.getElementById(id);
const long = 12;
const last = sweep.length - 1;
const frameDuration = 110;
const imageFile = (kind, frame) => 'media/' + kind + '-' + String(frame).padStart(2, '0') + '.webp';
const referenceFor = (frame) => (frame <= (long + last) / 2 ? 'long' : 'short');
const refFile = (frame) => 'media/acquired-' + referenceFor(frame) + '.webp';
const axisName = (frame) => (referenceFor(frame) === 'long' ? 'Long axis' : 'Short axis');
const on = (id, value) => $(id).setAttribute('aria-pressed', String(value));
const state = {
  frame: location.hash === '#guided' ? 0 : long,
  shownFrame: null,
  section: false,
  assets: false,
  group: 0,
  ready: false,
  playback: null,
  viewRequest: 0,
  assetRequest: 0,
  scene: null,
};

const images = new Map();
function prepare(path) {
  if (!images.has(path)) {
    const image = new Image();
    image.src = path;
    const record = { image: null, finished: false, pending: null };
    record.pending = image.decode().then(
      () => { record.image = image; },
      () => {},
    ).finally(() => { record.finished = true; });
    images.set(path, record);
  }
  return images.get(path);
}

async function prepareSequence(kind, start) {
  const paths = sweep.map((_, i) => imageFile(kind, (start + i) % sweep.length));
  for (let offset = 0; offset < paths.length; offset += 8) {
    await Promise.all(paths.slice(offset, offset + 8).map((path) => prepare(path).pending));
  }
}

function showImage(areaId, id, record, alt, error) {
  const area = $(areaId);
  const previous = $(id);
  const status = $(id + 'Status');
  area.setAttribute('aria-busy', 'false');
  if (!record.image) {
    previous?.remove();
    status.hidden = false;
    status.textContent = error;
    return;
  }
  const img = record.image;
  img.alt = alt;
  if (img !== previous) {
    img.id = id;
    img.draggable = false;
    if (previous) previous.replaceWith(img);
    else area.append(img);
  }
  status.hidden = true;
}

function phaseName(frame) {
  if (frame < long) return 'Find window';
  if (frame === long || frame === last) return axisName(frame);
  return 'Rotate probe';
}

function drawReadout(frame) {
  const name = phaseName(frame);
  const angle = Math.round(sweep[frame].degrees) + '°';
  $('position').value = frame;
  $('position').setAttribute('aria-valuetext', name + ', ' + angle + ', frame ' + frame + ' of ' + last);
  $('readout').textContent = name;
  $('angle').textContent = angle;
  $('frameNumber').textContent = frame + ' / ' + last;
  $('frameNumber').setAttribute('aria-label', 'Frame ' + frame + ' of ' + last);
  $('longTick').setAttribute('aria-current', String(frame === long));
  $('shortTick').setAttribute('aria-current', String(frame === last));
}

function renderFrame(frame, scenePosition = frame) {
  state.frame = frame;
  updatePlay();
  const request = ++state.viewRequest;
  const kind = state.section ? 'section' : 'scan';
  const scan = prepare(imageFile(kind, frame));
  const reference = prepare(refFile(frame));
  const commit = () => {
    if (request !== state.viewRequest) return;
    const currentAxis = axisName(frame);
    state.scene?.setFrame(scenePosition);
    drawReadout(frame);
    $('scanTitle').textContent = state.section ? 'Anatomical section' : 'Simulated scan';
    $('scanDetail').hidden = state.section;
    $('legend').hidden = !state.section;
    on('section', state.section);
    showImage('scanArea', 'scan', scan, $('scanTitle').textContent + ' at frame ' + frame + '.', 'Scan unavailable for this frame.');
    showImage('referenceArea', 'ref', reference, 'Acquired ' + currentAxis.toLowerCase() + ' gallbladder ultrasound in a different case.', 'Clinical reference unavailable.');
    $('referenceNote').textContent = frame === long || frame === last
      ? currentAxis + ' reference'
      : 'Nearest reference · ' + currentAxis;
    state.shownFrame = frame;
  };
  if (scan.finished && reference.finished) commit();
  else {
    $('scanArea').setAttribute('aria-busy', 'true');
    $('referenceArea').setAttribute('aria-busy', 'true');
    Promise.all([scan.pending, reference.pending]).then(commit);
  }
}

function updatePlay() {
  $('play').disabled = !state.ready;
  $('play').textContent = state.playback ? 'Pause' : state.frame === last ? 'Replay sweep' : 'Play sweep';
}

function pause() {
  if (!state.playback) return;
  cancelAnimationFrame(state.playback.request);
  state.playback = null;
  state.scene?.setFrame(state.frame);
  updatePlay();
}

function play() {
  if (state.playback) {
    pause();
    return;
  }
  if (state.frame === last) renderFrame(0);
  const playback = { origin: state.frame, started: null, request: null };
  state.playback = playback;
  function advance(now) {
    playback.started ??= now;
    const position = Math.min(last, playback.origin + (now - playback.started) / frameDuration);
    const frame = Math.round(position);
    if (frame !== state.frame) renderFrame(frame, position);
    else state.scene?.setFrame(position);
    if (position === last) pause();
    else playback.request = requestAnimationFrame(advance);
  }
  playback.request = requestAnimationFrame(advance);
  updatePlay();
}

function selectFrame(frame) {
  pause();
  renderFrame(frame);
  if (state.assets) drawAssets();
}

$('play').onclick = play;
$('longTick').onclick = () => selectFrame(long);
$('shortTick').onclick = () => selectFrame(last);
$('position').oninput = (event) => selectFrame(event.currentTarget.valueAsNumber);
$('section').onclick = async () => {
  const next = !state.section;
  $('section').disabled = true;
  if (next) await prepareSequence('section', state.frame);
  state.section = next;
  renderFrame(state.frame);
  $('section').disabled = false;
};
document.addEventListener('visibilitychange', () => {
  if (document.hidden) pause();
});

const scenePanel = $('scenePanel');
const torsoOpacity = $('torsoOpacity');

async function startScene() {
  const canvas = $('sceneCanvas');
  const status = $('sceneStatus');
  try {
    const { createSweepScene } = await import('./scene.js');
    canvas.hidden = false;
    state.scene = await createSweepScene({ canvas, frames: sweep });
    state.scene.setFrame(state.shownFrame ?? state.frame);
    state.scene.setTorsoOpacity(torsoOpacity.valueAsNumber / 100);
    status.hidden = true;
    $('sceneHelp').hidden = false;
    $('resetView').disabled = false;
    $('orbitCenters').disabled = false;
    torsoOpacity.disabled = false;
  } catch (error) {
    state.scene?.dispose();
    state.scene = null;
    canvas.hidden = true;
    status.textContent = '3D probe and scan plane unavailable.';
    console.warn('Gallbladder 3D view unavailable.', error);
  }
}

$('orbitCenters').onchange = (event) => {
  if (event.target.checked) state.scene?.setOrbitCenter(event.target.value);
};
$('resetView').onclick = () => state.scene?.resetView();
torsoOpacity.oninput = () => {
  const value = torsoOpacity.value + '%';
  $('torsoOpacityValue').value = value;
  torsoOpacity.setAttribute('aria-valuetext', value);
  state.scene?.setTorsoOpacity(torsoOpacity.valueAsNumber / 100);
};

const groups = ['Probe pose', 'Scan plane', 'Simulated scan', 'Acquired ultrasound'];

groups.forEach((label, i) => {
  const button = document.createElement('button');
  button.textContent = label;
  button.onclick = () => {
    state.group = i;
    drawAssets();
  };
  $('assetControls').append(button);
});

function restoreScenePanel() {
  const stage = $('stage');
  if (scenePanel.parentElement !== stage) stage.prepend(scenePanel);
}

function showAssets(visible) {
  pause();
  state.assets = visible;
  $('tour').hidden = visible;
  $('assets').hidden = !visible;
  on('assetTab', visible);
  on('tourTab', !visible);
  if (visible) drawAssets();
  else restoreScenePanel();
}

$('assetTab').onclick = () => showAssets(true);
$('tourTab').onclick = () => showAssets(false);
$('return').onclick = () => {
  showAssets(false);
  $('position').focus();
};
$('assetFrame').options[0].disabled = true;
$('assetFrame').onchange = (event) => selectFrame(Number(event.currentTarget.value));

function drawAssets() {
  const frame = state.frame;
  const request = ++state.assetRequest;
  const { group } = state;
  const title = groups[group];
  const useLong = referenceFor(frame) === 'long';
  const bindings = [
    'BodyParts3D exterior · s1233 contact window',
    'TotalSegmentator s1233 · gallbladder, liver and right ribs',
    'Frame ' + frame + ' of 0–' + last + ' · 13.3 cm modeled depth · 72° sector',
    (frame === long || frame === last ? axisName(frame) + ' reference' : 'Nearest reference · ' + axisName(frame))
      + (useLong ? ' · Figure 2' : ' · Cine frame at 1.2 s'),
  ];
  const context = [
    'The fitted atlas supplies the body silhouette. Near the probe, its abdominal surface follows the CT-derived contact window.',
    'The wireframe shows the sampled field. Its intersection with the gallbladder changes as the probe rotates.',
    'Compare the lumen boundary and surrounding echoes. The simulated wall still blends into adjacent tissue.',
    'The acquired image shows a different case and a fixed imaging plane.',
  ];
  $('assetFrame').value = frame === long || frame === last ? String(frame) : '-1';
  $('assetName').textContent = title;
  $('binding').textContent = bindings[group];
  $('assetFinding').textContent = context[group];
  const acquired = useLong ? 'https://doi.org/10.3390/life15060941' : 'https://www.thepocusatlas.com/pedsbiliary';
  $('assetSource').href = ['https://dbarchive.biosciencedbc.jp/en/bodyparts3d/desc.html', 'https://zenodo.org/records/10047263', acquired, acquired][group];
  $('assetSource').textContent = group < 2 ? 'Anatomy source ↗' : 'Acquired image source ↗';
  [...$('assetControls').children].forEach((button, i) => button.setAttribute('aria-pressed', String(i === group)));

  const evidence = $('assetEvidence');
  if (group < 2 && scenePanel.parentElement === evidence) return;
  restoreScenePanel();
  evidence.replaceChildren();
  evidence.className = group === 2 ? 'paired' : '';
  if (group < 2) {
    evidence.append(scenePanel);
    return;
  }
  const kinds = group === 2 ? [imageFile('scan', frame), refFile(frame)] : [refFile(frame)];
  Promise.all(kinds.map((path) => prepare(path).pending)).then(() => {
    if (!state.assets || request !== state.assetRequest) return;
    kinds.forEach((path) => {
      const record = prepare(path);
      const label = path === refFile(frame) ? axisName(frame) + ' acquired ultrasound' : 'Simulated scan';
      if (!record.image) {
        const note = document.createElement('p');
        note.textContent = label + ' unavailable.';
        evidence.append(note);
        return;
      }
      const image = record.image.cloneNode();
      image.className = 'evidenceImage';
      image.removeAttribute('id');
      image.alt = label;
      evidence.append(image);
    });
  });
}

window.addEventListener('hashchange', () => {
  if (location.hash === '#probe' || location.hash === '#guided') {
    showAssets(false);
    selectFrame(location.hash === '#guided' ? 0 : long);
  }
});

renderFrame(state.frame);
startScene();
Promise.all([
  prepareSequence('scan', state.frame),
  prepare(refFile(long)).pending,
  prepare(refFile(last)).pending,
]).then(() => {
  state.ready = true;
  updatePlay();
  return prepareSequence('section', state.frame);
});
