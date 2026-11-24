'use strict';

const $ = (id) => document.getElementById(id);
const frameDuration = 110;
const cameraPresets = [['oblique', 'Oblique'], ['axial', 'Axial'], ['coronal', 'Coronal'], ['sagittal', 'Sagittal']];
const unavailableImage = { image: null, finished: true, pending: Promise.resolve() };
let selectedTour;
let poses;
let last;
let keyframes;
let phases;
const imageFile = (kind, frame) =>
  selectedTour.assetRoot + 'media/' + kind + '-' + String(frame).padStart(2, '0') + '.webp';
const nearestKeyframe = (frame) => keyframes.reduce((nearest, candidate) =>
  Math.abs(candidate.frame - frame) < Math.abs(nearest.frame - frame) ? candidate : nearest);
const acquiredFor = (keyframe) => typeof abdomenReferences === 'undefined' ? null : abdomenReferences[keyframe.referenceId];
const usesAtlas = (tour) => (tour.exterior ?? (tour.id === 'gallbladder' ? 'fitted-atlas' : 'case-ct')) === 'fitted-atlas';
const referenceLabel = (keyframe) => keyframe.referenceLabel ?? acquiredFor(keyframe)?.label ?? keyframe.label;
const referenceNote = (frame, keyframe) => {
  const label = referenceLabel(keyframe);
  if (frame !== keyframe.frame) return 'Nearest reference · ' + label;
  return label === keyframe.label ? label + ' reference' : 'Comparison · ' + label;
};
const on = (id, value) => $(id).setAttribute('aria-pressed', String(value));
const state = {
  frame: 0,
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
  if (!path) return unavailableImage;
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
  const paths = poses.map((_, i) => imageFile(kind, (start + i) % poses.length));
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
  return keyframes.find((key) => key.frame === frame)?.label ??
    phases.findLast((phase) => phase.frame <= frame)?.label ?? '';
}

function drawReadout(frame) {
  const name = phaseName(frame);
  const angle = Math.round(poses[frame].degrees) + '°';
  $('position').value = frame;
  $('position').setAttribute('aria-valuetext', name + ', ' + angle + ', frame ' + frame + ' of ' + last);
  $('readout').textContent = name;
  $('angle').textContent = angle;
  $('frameNumber').textContent = frame + ' / ' + last;
  $('frameNumber').setAttribute('aria-label', 'Frame ' + frame + ' of ' + last);
  for (const button of $('ticks').children) {
    button.setAttribute('aria-current', String(Number(button.dataset.frame) === frame));
  }
}

function renderFrame(frame, scenePosition = frame) {
  state.frame = frame;
  updatePlay();
  const request = ++state.viewRequest;
  const kind = state.section ? 'section' : 'scan';
  const scan = prepare(imageFile(kind, frame));
  const keyframe = nearestKeyframe(frame);
  const acquired = acquiredFor(keyframe);
  const reference = prepare(acquired?.path);
  const commit = () => {
    if (request !== state.viewRequest) return;
    state.scene?.setFrame(scenePosition);
    drawReadout(frame);
    $('scanTitle').textContent = state.section ? 'Anatomical section' : 'Simulated scan';
    $('scanDetail').hidden = state.section;
    $('legend').hidden = !state.section;
    on('section', state.section);
    showImage('scanArea', 'scan', scan, $('scanTitle').textContent + ' at frame ' + frame + '.', 'Scan unavailable for this frame.');
    showImage('referenceArea', 'ref', reference, acquired?.title ?? 'Acquired ultrasound.', 'Clinical reference unavailable.');
    $('referenceNote').textContent = acquired ? referenceNote(frame, keyframe) : 'Reference unavailable';
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
    state.scene = await createSweepScene({ canvas, frames: poses, config: selectedTour });
    state.scene.setFrame(state.shownFrame ?? state.frame);
    updateTorsoOpacity();
    status.hidden = true;
    $('sceneHelp').hidden = false;
    $('cameraPresets').disabled = false;
    torsoOpacity.disabled = false;
  } catch (error) {
    state.scene?.dispose();
    state.scene = null;
    canvas.hidden = true;
    status.textContent = '3D probe and scan plane unavailable.';
    console.warn('Ultrasound sweep 3D view unavailable.', error);
  }
}

for (const [id, label] of cameraPresets) {
  const button = document.createElement('button');
  button.id = 'cameraPreset-' + id;
  button.className = 'viewButton';
  button.type = 'button';
  button.textContent = label;
  button.onclick = () => state.scene?.setViewPreset(id);
  $('cameraPresets').append(button);
}

function updateTorsoOpacity() {
  const value = torsoOpacity.value + '%';
  $('torsoOpacityValue').value = value;
  torsoOpacity.setAttribute('aria-valuetext', value);
  state.scene?.setTorsoOpacity(torsoOpacity.valueAsNumber / 100);
}
torsoOpacity.oninput = updateTorsoOpacity;

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
  const keyframe = nearestKeyframe(frame);
  const acquired = acquiredFor(keyframe);
  const partNames = selectedTour.parts.map((part) => part.label).join(', ');
  const bindings = [
    selectedTour.region ?? selectedTour.title,
    partNames,
    'Frame ' + frame + ' of 0–' + last + ' · ' + (selectedTour.sectorDepthMm ?? 133) / 10 + ' cm modeled depth',
    referenceNote(frame, keyframe),
  ];
  const context = [
    selectedTour.sourceNote ?? '',
    'The wireframe marks the sampled plane at this probe pose.',
    'The simulation and acquired image represent different cases.',
    acquired?.note ?? acquired?.title ?? 'Clinical reference unavailable.',
  ];
  $('assetFrame').value = keyframes.some((key) => key.frame === frame) ? String(frame) : '-1';
  $('assetName').textContent = title;
  $('binding').textContent = bindings[group];
  $('assetFinding').textContent = context[group];
  $('assetFinding').hidden = !context[group];
  const ctSource = 'https://zenodo.org/records/10047263';
  const exteriorSource = usesAtlas(selectedTour)
    ? 'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/desc.html'
    : ctSource;
  $('assetSource').href = [exteriorSource, ctSource, acquired?.url, acquired?.url][group] ?? '';
  $('assetSource').hidden = group >= 2 && !acquired?.url;
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
  const reference = [acquired?.path, acquired?.title ?? 'Acquired ultrasound'];
  const kinds = group === 2 ? [[imageFile('scan', frame), 'Simulated scan'], reference] : [reference];
  Promise.all(kinds.map(([path]) => prepare(path).pending)).then(() => {
    if (!state.assets || request !== state.assetRequest) return;
    kinds.forEach(([path, label]) => {
      const record = prepare(path);
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

function configureTimeline() {
  $('position').max = last;
  $('position').disabled = false;
  const split = phases[1]?.frame / last || 0;
  const timeline = $('position').parentElement;
  timeline.style.setProperty('--first-phase', split * 100 + '%');
  timeline.style.setProperty('--phase-thumb-offset', (0.5 - split) * 18 + 'px');
  for (const phase of phases) {
    const item = document.createElement('li');
    item.textContent = phase.label;
    $('phases').append(item);
  }
  keyframes.forEach((keyframe, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'tick';
    button.id = index === 0 ? 'longTick' : index === keyframes.length - 1 ? 'shortTick' : 'tick-' + keyframe.frame;
    button.dataset.frame = keyframe.frame;
    button.textContent = keyframe.label;
    button.setAttribute('aria-label', keyframe.label + ' reference keyframe');
    button.style.setProperty('--tick-point', (keyframe.frame / last) * 100 + '%');
    if (keyframe.frame === 0 || keyframe.frame === last) button.classList.add('edge');
    button.onclick = () => selectFrame(keyframe.frame);
    $('ticks').append(button);
    $('assetFrame').add(new Option(keyframe.label, keyframe.frame));
  });
}

function configureLegend(list, parts) {
  for (const part of parts) {
    const item = document.createElement('li');
    item.textContent = part.label;
    if (part.color) item.style.setProperty('--part-color', part.color);
    list.append(item);
  }
}

function addSourceLink(parent, label, href) {
  const link = document.createElement('a');
  link.textContent = label;
  link.href = href;
  parent.append(link);
}

function configureSources() {
  $('atlasSource').hidden = !usesAtlas(selectedTour);
  $('tourSourceNote').textContent = selectedTour.sourceNote ?? '';
  $('tourSourceNote').hidden = !selectedTour.sourceNote;
  for (const id of new Set(keyframes.map((key) => key.referenceId))) {
    const reference = acquiredFor({ referenceId: id });
    if (!reference) continue;
    const item = document.createElement('p');
    if (reference.title) item.append(reference.title + ' · ');
    if (reference.url) addSourceLink(item, reference.credit ?? 'Acquired image source', reference.url);
    else if (reference.credit) item.append(reference.credit);
    if (reference.license) {
      item.append(' · ');
      if (reference.licenseUrl) addSourceLink(item, reference.license, reference.licenseUrl);
      else item.append(reference.license);
    }
    if (reference.note) item.append('. ' + reference.note);
    $('referenceSources').append(item);
  }
}

function loadPoses(assetRoot) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = assetRoot + 'sweep.js';
    script.onload = () => {
      if (typeof sweep !== 'undefined' && Array.isArray(sweep) && sweep.length > 1) resolve(sweep);
      else reject(new Error('Sweep frames unavailable.'));
    };
    script.onerror = () => reject(new Error('Sweep frames failed to load.'));
    document.head.append(script);
  });
}

function legacyInitialFrame() {
  return selectedTour.id === 'gallbladder' && location.hash === '#guided' ? 0 : keyframes[0].frame;
}

async function startTour() {
  const tours = typeof abdomenTours === 'undefined' ? [] : abdomenTours;
  if (!tours.length) throw new Error('Tour catalogue unavailable.');
  const currentURL = new URL(location.href);
  const requested = currentURL.searchParams.get('sweep');
  selectedTour = tours.find((tour) => tour.id === requested) ??
    tours.find((tour) => tour.id === 'gallbladder') ?? tours[0];
  if (requested && requested !== selectedTour.id) {
    currentURL.searchParams.delete('sweep');
    history.replaceState(null, '', currentURL);
  }
  const picker = $('sweepPicker');
  for (const tour of tours) picker.add(new Option(tour.title, tour.id));
  picker.value = selectedTour.id;
  picker.disabled = false;
  picker.onchange = () => {
    const url = new URL(location.href);
    url.searchParams.set('sweep', picker.value);
    url.hash = '';
    location.assign(url);
  };
  window.addEventListener('pageshow', () => {
    picker.value = selectedTour.id;
    updateTorsoOpacity();
  });
  $('tourTitle').textContent = selectedTour.title;
  document.title = selectedTour.title + ' · Ultrasound Anatomy';
  poses = await loadPoses(selectedTour.assetRoot);
  last = poses.length - 1;
  keyframes = selectedTour.keyframes.filter((key) => key.frame >= 0 && key.frame <= last).sort((a, b) => a.frame - b.frame);
  if (!keyframes.length) throw new Error('Reference keyframes unavailable.');
  phases = selectedTour.phases ?? [{ frame: 0, label: 'Find window' }, { frame: keyframes[0].frame, label: 'Rotate probe' }];
  configureTimeline();
  $('scanDetail').textContent = 'Curved array · ' + (selectedTour.sectorDepthMm ?? 133) / 10 + ' cm depth';
  configureLegend($('sceneLegend'), [{ label: 'Imaging sector', color: '#84b5d1' }, ...selectedTour.parts]);
  configureLegend($('legend'), selectedTour.overlayParts ?? selectedTour.parts);
  configureSources();
  state.frame = legacyInitialFrame();
  drawReadout(state.frame);
  const currentKeyframe = nearestKeyframe(state.frame);
  $('referenceNote').textContent = acquiredFor(currentKeyframe) ? referenceNote(state.frame, currentKeyframe) : 'Reference unavailable';
  $('tour').hidden = false;
  $('assetTab').disabled = false;
  $('tourTab').disabled = false;
  renderFrame(state.frame);
  startScene();
  await Promise.all([
    prepareSequence('scan', state.frame),
    ...keyframes.map((key) => prepare(acquiredFor(key)?.path).pending),
  ]);
  state.ready = true;
  updatePlay();
  prepareSequence('section', state.frame);
}

window.addEventListener('hashchange', () => {
  if (selectedTour?.id === 'gallbladder' && keyframes &&
      (location.hash === '#probe' || location.hash === '#guided')) {
    showAssets(false);
    selectFrame(legacyInitialFrame());
  }
});

startTour().catch((error) => {
  $('tourStatus').textContent = 'This sweep is unavailable. Select another sweep if available.';
  $('tourStatus').hidden = false;
  console.warn('Ultrasound sweep unavailable.', error);
});
