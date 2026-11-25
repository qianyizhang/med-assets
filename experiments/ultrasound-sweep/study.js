'use strict';

const $ = (id) => document.getElementById(id);
const frameDuration = 110;
const atlasSource = 'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/desc.html';
const cameraPresets = [['oblique', 'Oblique'], ['axial', 'Axial'], ['coronal', 'Coronal'], ['sagittal', 'Sagittal']];
const unavailableImage = { image: null, finished: true, pending: Promise.resolve() };
let selectedTour;
let poses;
let last;
let keyframes;
let phases;
let steering;
function anatomySource() {
  const caseId = selectedTour.case ?? 's1233';
  return selectedTour.anatomySource ?? {
    label: 'TotalSegmentator ' + caseId + ', Jakob Wasserthal and colleagues',
    shortLabel: 'TotalSegmentator ' + caseId + ' anatomy',
    url: 'https://zenodo.org/records/10047263',
    license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
  };
}
const isLinear = () => selectedTour.probeType === 'linear';
const fieldLabel = () => selectedTour.fieldShape === 'rectangle' ? 'Imaging field' : 'Imaging sector';
const imageFile = (kind, frame) =>
  selectedTour.assetRoot + 'media/' + (state.compressed ? 'press-' : '') + kind + '-' + String(frame).padStart(2, '0') + '.webp';
const nearestKeyframe = (frame) => steering?.referenceFor(frame, keyframes) ?? keyframes.reduce((nearest, candidate) =>
  Math.abs(candidate.frame - frame) < Math.abs(nearest.frame - frame) ? candidate : nearest);
const referenceById = (id) => typeof abdomenReferences === 'undefined' ? null : abdomenReferences[id];
const acquiredFor = (keyframe) => referenceById(keyframe.referenceId);
const usesBodyParts3D = (tour) => (tour.exterior ?? (tour.id === 'gallbladder' ? 'fitted-atlas' : 'case-ct')) === 'fitted-atlas';
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
  shownCompressed: false,
  section: false,
  compressed: false,
  magnified: false,
  assets: false,
  group: 'anatomy',
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
  for (let offset = 0; offset < paths.length; offset += 2) {
    await Promise.all(paths.slice(offset, offset + 2).map((path) => prepare(path).pending));
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

function drawApSpan(frame, hasScan) {
  if (!selectedTour.showApSpan) return;
  const span = poses[frame]?.apSpan;
  const visible = hasScan && span && $('apToggle').getAttribute('aria-pressed') === 'true';
  $('apMarks').hidden = !visible;
  $('apReadout').hidden = !visible;
  if (!visible) return;
  const [[x1, y1], [x2, y2]] = span.endpointsPx;
  const distance = Math.hypot(x2 - x1, y2 - y1);
  const dx = 5 * (y2 - y1) / distance;
  const dy = 5 * (x1 - x2) / distance;
  $('apChord').setAttribute('d', `M ${x1} ${y1} L ${x2} ${y2}`);
  $('apEnds').setAttribute('d', span.endpointsPx.map(([x,y]) => `M ${x-dx} ${y-dy} L ${x+dx} ${y+dy}`).join(' '));
  $('apReadout').textContent = 'Modeled AP span · ' + span.millimetres.toFixed(1) + ' mm';
}

$('apToggle').onclick = () => {
  on('apToggle', $('apToggle').getAttribute('aria-pressed') !== 'true');
  drawApSpan(state.shownFrame, Boolean($('scan')));
};

function drawReadout(frame) {
  const name = phaseName(frame);
  const angle = (steering ? Number(steering.rotationAt(frame).toFixed(1)) : Math.round(poses[frame].degrees)) + '°';
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

function scanDimensions(frame, bounds) {
  if (bounds) {
    const [left, near, right, far] = bounds;
    const cm = (mm) => Number((mm / 10).toFixed(1));
    return 'Magnified area · ' + cm(right - left) + ' × ' + cm(far - near) + ' cm';
  }
  const probe = isLinear() ? 'High-frequency linear array' : 'Curved array';
  return probe + ' · ' + Number(scanDepth(frame).toFixed(2)) + ' cm depth';
}

function renderFrame(frame, scenePosition = frame) {
  state.frame = frame;
  updatePlay();
  const request = ++state.viewRequest;
  const compressed = state.compressed;
  const kind = state.section ? 'section' : 'scan';
  const keyframe = nearestKeyframe(frame);
  const detail = frame === keyframe.frame && keyframe.detail;
  if (frame !== state.shownFrame || !detail) state.magnified = false;
  const full = prepare(imageFile(kind, frame));
  const enlarged = state.magnified ? prepare(imageFile('detail-' + kind, frame)) : null;
  const acquired = acquiredFor(keyframe);
  const reference = prepare(acquired?.path);
  const commit = () => {
    if (request !== state.viewRequest) return;
    state.scene?.setFrame(poses[frame].contactRig ? frame : scenePosition, compressed);
    steering?.sync(frame);
    drawReadout(frame);
    const zoomFailed = enlarged && !enlarged.image;
    if (zoomFailed) state.magnified = false;
    state.scene?.setMagnifiedBounds(state.magnified ? detail.boundsMm : null);
    $('scanZoom').disabled = !detail;
    on('scanZoom', state.magnified);
    $('scanZoom').textContent = state.magnified ? 'Full field' : 'Magnify section';
    $('scanTitle').textContent = state.section ? 'Anatomical section' : 'Simulated scan';
    if (state.magnified) $('scanTitle').textContent += ' · magnified';
    if (zoomFailed) $('scanTitle').textContent += ' · detail unavailable';
    $('scanDetail').textContent = scanDimensions(frame, state.magnified ? detail.boundsMm : null);
    $('scanDetail').hidden = state.section;
    $('legend').hidden = !state.section;
    on('section', state.section);
    showImage('scanArea', 'scan', state.magnified ? enlarged : full, $('scanTitle').textContent + ' at frame ' + frame + '.', 'Scan unavailable for this frame.');
    drawApSpan(frame, Boolean(full.image) && !state.magnified);
    showImage('referenceArea', 'ref', reference, acquired?.title ?? 'Acquired ultrasound.', 'Clinical reference unavailable.');
    $('referenceDepth').textContent = [selectedTour.referenceContext ?? 'Different case', acquired?.depthLabel].filter(Boolean).join(' · ');
    $('referenceNote').textContent = acquired ? referenceNote(frame, keyframe) : 'Reference unavailable';
    const finding = selectedTour.pregnancyStage && frame === keyframe.frame && acquired?.reason;
    $('comparisonFinding').textContent = finding || '';
    $('comparisonFinding').hidden = !finding;
    state.shownFrame = frame;
    state.shownCompressed = compressed;
  };
  if (full.finished && (!enlarged || enlarged.finished) && reference.finished) commit();
  else {
    $('scanArea').setAttribute('aria-busy', 'true');
    $('referenceArea').setAttribute('aria-busy', 'true');
    Promise.all([full.pending, enlarged?.pending, reference.pending]).then(commit);
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
  if (state.shownFrame !== null) state.scene?.setFrame(state.shownFrame, state.shownCompressed);
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
    else if (!poses[frame].contactRig && state.shownFrame === frame) state.scene?.setFrame(position, state.shownCompressed);
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
$('scanZoom').onclick = () => {
  pause();
  state.magnified = !state.magnified;
  renderFrame(state.frame);
};
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
    state.scene = await createSweepScene({ canvas, frames: poses, config: selectedTour, onViewPresetChange: showCameraPreset, onProbeDrag: steering?.drag });
    const shown = state.shownFrame ?? state.frame;
    state.scene.setFrame(shown, state.shownCompressed);
    if (state.magnified) state.scene.setMagnifiedBounds(nearestKeyframe(shown).detail?.boundsMm);
    if (selectedTour.showRoute) $('showRoute').disabled = false;
    updateTorsoOpacity();
    status.hidden = true;
    $('sceneHelp').hidden = false;
    $('cameraPresets').disabled = false;
    torsoOpacity.disabled = false;
  } catch (error) {
    state.scene?.dispose();
    state.scene = null;
    showCameraPreset(null);
    canvas.hidden = true;
    status.textContent = '3D probe and scan plane unavailable.';
    console.warn('Ultrasound sweep 3D view unavailable.', error);
  }
}

function showCameraPreset(active) {
  for (const [id] of cameraPresets) on('cameraPreset-' + id, id === active);
}

for (const [id, label] of cameraPresets) {
  const button = document.createElement('button');
  button.id = 'cameraPreset-' + id;
  button.className = 'viewButton';
  button.type = 'button';
  button.textContent = label;
  button.setAttribute('aria-pressed', 'false');
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

const assetGroups = [
  ['anatomy', '3D anatomy'],
  ['simulation', 'Simulated scan'],
  ['acquired', 'Acquired ultrasound'],
];
for (const [id, label] of assetGroups) {
  const button = document.createElement('button');
  button.type = 'button';
  button.dataset.asset = id;
  button.textContent = label;
  button.onclick = () => {
    if (state.group === id) return;
    state.group = id;
    drawAssets();
  };
  $('assetControls').append(button);
}

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
  if (visible) {
    drawAssets();
    loadRelatedPlates();
  } else {
    state.assetRequest += 1;
    relatedRequest += 1;
    $('relatedPlates').setAttribute('aria-busy', 'false');
    restoreScenePanel();
  }
}

$('assetTab').onclick = () => showAssets(true);
$('tourTab').onclick = () => showAssets(false);
$('return').onclick = () => {
  showAssets(false);
  $('position').focus();
};
$('assetFrame').options[0].disabled = true;
$('assetFrame').onchange = (event) => selectFrame(Number(event.currentTarget.value));

function describeAsset(frame, group) {
  const source = anatomySource();
  const anatomyLink = [source.shortLabel ?? source.label, source.url];
  const additionalLinks = (selectedTour.additionalAnatomySources ?? []).map((item) => [item.shortLabel ?? item.label, item.url]);
  if (group === 'anatomy') {
    const partNames = selectedTour.parts.map((part) => part.label).join(', ');
    const region = selectedTour.region ?? selectedTour.title;
    return {
      binding: region + ' · ' + partNames,
      note: selectedTour.sourceNote ?? '',
      sources: usesBodyParts3D(selectedTour)
        ? [['BodyParts3D exterior', atlasSource], anatomyLink, ...additionalLinks]
        : [anatomyLink, ...additionalLinks],
    };
  }
  if (group === 'simulation') {
    return {
      path: imageFile('scan', frame),
      alt: 'Simulated scan at frame ' + frame,
      binding: 'Frame ' + frame + ' of 0–' + last + ' · ' + Number(scanDepth(frame).toFixed(2)) + ' cm modeled depth' + (state.compressed ? ' · Firmer pressure' : ''),
      note: selectedTour.simulationNote ?? 'Illustrative ultrasound derived from the CT anatomy.',
      sources: [anatomyLink, ...additionalLinks],
    };
  }
  const keyframe = nearestKeyframe(frame);
  const acquired = acquiredFor(keyframe);
  return {
    path: acquired?.path,
    alt: acquired?.title ?? 'Acquired ultrasound',
    binding: acquired ? referenceNote(frame, keyframe) : 'Reference unavailable',
    note: acquired?.note ?? '',
    reference: acquired,
  };
}

function assetImage(record, alt) {
  if (!record.image) {
    const status = document.createElement('p');
    status.setAttribute('role', 'status');
    status.textContent = 'Image unavailable.';
    return status;
  }
  const image = record.image.cloneNode();
  image.className = 'evidenceImage';
  image.removeAttribute('id');
  image.alt = alt;
  return image;
}

function drawAssets() {
  const frame = state.frame;
  const request = ++state.assetRequest;
  const { group } = state;
  const asset = describeAsset(frame, group);
  $('assetFrame').value = keyframes.some((key) => key.frame === frame) ? String(frame) : '-1';
  $('assetName').textContent = assetGroups.find(([id]) => id === group)[1];
  $('binding').textContent = asset.binding;
  $('assetFinding').textContent = asset.note;
  $('assetFinding').hidden = !asset.note;

  const sources = $('assetSources');
  sources.replaceChildren();
  if (asset.reference) appendReferenceCredit(sources, asset.reference);
  asset.sources?.forEach(([label, href], i) => {
    if (i) sources.append(' · ');
    if (href) addSourceLink(sources, label, href);
    else if (label) sources.append(label);
  });
  sources.hidden = !sources.childNodes.length;
  for (const button of $('assetControls').children) {
    button.setAttribute('aria-pressed', String(button.dataset.asset === group));
  }

  const evidence = $('assetEvidence');
  if (group === 'anatomy') {
    evidence.setAttribute('aria-busy', 'false');
    if (scenePanel.parentElement !== evidence) evidence.replaceChildren(scenePanel);
    return;
  }
  restoreScenePanel();
  evidence.replaceChildren();
  const record = prepare(asset.path);
  evidence.setAttribute('aria-busy', String(!record.finished));
  const commit = () => {
    if (!state.assets || request !== state.assetRequest) return;
    evidence.replaceChildren(assetImage(record, asset.alt));
    evidence.setAttribute('aria-busy', 'false');
  };
  if (record.finished) commit();
  else {
    const status = document.createElement('p');
    status.textContent = 'Loading image…';
    evidence.append(status);
    record.pending.then(commit);
  }
}

let relatedReferences = [];
let relatedRequest = 0;
let relatedReady = false;
let relatedSharedLicense = false;
const relatedAnatomy = $('relatedAnatomy');

function configureRelatedPlates() {
  const acquiredPaths = keyframes.map((key) => acquiredFor(key)?.path).filter(Boolean);
  const paths = new Set(acquiredPaths.map((path) => new URL(path, document.baseURI).href));
  for (const id of selectedTour.landmarks ?? []) {
    const reference = referenceById(id);
    if (!reference?.path) continue;
    const path = new URL(reference.path, document.baseURI).href;
    if (paths.has(path)) continue;
    paths.add(path);
    relatedReferences.push(reference);
  }
  relatedAnatomy.hidden = !relatedReferences.length;
  const first = relatedReferences[0];
  relatedSharedLicense = relatedReferences.length > 1 && Boolean(first.license) &&
    relatedReferences.every(({ license, licenseUrl }) => license === first.license && licenseUrl === first.licenseUrl);
  if (relatedSharedLicense) {
    const license = $('relatedLicense');
    license.append('Plate license · ');
    if (first.licenseUrl) addSourceLink(license, first.license, first.licenseUrl);
    else license.append(first.license);
    license.hidden = false;
  }
}

function relatedPlate(reference, record) {
  const figure = document.createElement('figure');
  const caption = document.createElement('figcaption');
  const name = document.createElement('h3');
  name.textContent = reference.label ?? reference.title ?? 'Normal anatomy';
  caption.append(name);
  const context = reference.reason ?? reference.note;
  if (context) {
    const note = document.createElement('p');
    note.textContent = context;
    caption.append(note);
  }
  const credit = document.createElement('p');
  credit.className = 'assetSources';
  appendReferenceCredit(credit, reference, !relatedSharedLicense);
  if (credit.childNodes.length) caption.append(credit);
  figure.append(assetImage(record, reference.title ?? name.textContent), caption);
  return figure;
}

async function loadRelatedPlates() {
  if (!state.assets || !relatedAnatomy.open || relatedReady || !relatedReferences.length) return;
  const request = ++relatedRequest;
  const target = $('relatedPlates');
  target.setAttribute('aria-busy', 'true');
  const placeholder = document.createElement('p');
  placeholder.textContent = 'Loading related anatomy…';
  target.replaceChildren(placeholder);
  const records = relatedReferences.map((reference) => prepare(reference.path));
  await Promise.all(records.map((record) => record.pending));
  if (!state.assets || !relatedAnatomy.open || request !== relatedRequest) return;
  target.replaceChildren(...relatedReferences.map((reference, i) => relatedPlate(reference, records[i])));
  target.setAttribute('aria-busy', 'false');
  relatedReady = true;
}

relatedAnatomy.addEventListener('toggle', () => {
  if (relatedAnatomy.open) loadRelatedPlates();
  else {
    relatedRequest += 1;
    $('relatedPlates').setAttribute('aria-busy', 'false');
  }
});

function scanDepth(frame) {
  const depth = poses[frame]?.imagingDepthMm ?? selectedTour.sectorDepthMm ?? 133;
  return (depth - (state.compressed ? selectedTour.compressionMm : 0)) / 10;
}

function configureSiblingRoutes(tours) {
  const group = selectedTour.routeGroup;
  if (!group) return;
  const regionTours = tours.filter((tour) => tour.routeGroup === group);
  if (regionTours.length < 2) return;
  const nav = $('siblingRoutes');
  nav.setAttribute('aria-label', group + ' scan routes');
  for (const tour of regionTours) {
    const url = new URL(location.href);
    url.searchParams.set('sweep', tour.id);
    url.hash = '';
    const link = document.createElement('a');
    link.href = url.href;
    link.textContent = tour.routeLabel ?? tour.title;
    if (tour.id === selectedTour.id) link.setAttribute('aria-current', 'page');
    nav.append(link);
  }
  nav.hidden = false;
}

$('showRoute').onclick = () => {
  const visible = $('showRoute').getAttribute('aria-pressed') !== 'true';
  on('showRoute', visible);
  state.scene?.setRouteVisible(visible);
};

$('compression').onclick = () => {
  state.compressed = !state.compressed;
  on('compression', state.compressed);
  selectFrame(state.frame);
};

function pregnancyNavigation(tours) {
  if (!selectedTour.pregnancyStage) return;
  const stages = new Map();
  for (const tour of tours.filter((tour) => tour.pregnancyStage)) {
    const age = tour.pregnancyStage.age;
    if (!stages.has(age)) stages.set(age, []);
    stages.get(age).push(tour);
  }
  const links = (tour, parent) => {
    const target = new URL(location.href);
    target.searchParams.set('sweep', tour.id);
    target.hash = '';
    const link = document.createElement('a');
    link.href = target.href;
    parent.append(link);
    return link;
  };
  for (const [age, routes] of stages) {
    const active = age === selectedTour.pregnancyStage.age;
    const first = active ? selectedTour : routes[0];
    const stage = links(first, $('pregnancyStages'));
    const ageLabel = document.createElement('strong');
    ageLabel.textContent = age;
    stage.append(ageLabel, first.pregnancyStage.focus);
    stage.setAttribute('aria-label', first.pregnancyStage.name + ', ' + age + ', ' + first.pregnancyStage.focus);
    if (!active) continue;
    stage.setAttribute('aria-current', 'step');
    if (routes.length > 1) {
      for (const route of routes) {
        const link = links(route, $('pregnancyRoutes'));
        link.textContent = route.title.replace(/ sweep$/, '');
        if (route.id === selectedTour.id) link.setAttribute('aria-current', 'page');
      }
    }
  }
  $('pregnancyRoutes').hidden = !$('pregnancyRoutes').childElementCount;
  $('pregnancyNavigation').hidden = false;
}

function configureTimeline() {
  const ticks = $('ticks');
  if (selectedTour.pregnancyStage && keyframes.length > 2) {
    ticks.classList.add('pregnancyTicks');
    ticks.style.setProperty('--stop-count', keyframes.length);
    const edges = [0, ...keyframes.slice(1).map((key, i) => (key.frame + keyframes[i].frame) / 2), last];
    ticks.style.setProperty('--stop-columns', edges.slice(1).map((end, i) =>
      'minmax(max-content, ' + (end - edges[i]) + 'fr)').join(' '));
    const marks = document.createElement('div');
    marks.className = 'keyMarks';
    marks.setAttribute('aria-hidden', 'true');
    for (const key of keyframes) {
      const mark = document.createElement('span');
      mark.style.left = (key.frame / last) * 100 + '%';
      marks.append(mark);
    }
    ticks.before(marks);
  }
  $('scanZoom').hidden = !keyframes.some((key) => key.detail);
  if (keyframes.length === 3 && keyframes[0].frame === 0 && keyframes[2].frame === last) {
    ticks.classList.add('with-start-keyframe');
    ticks.style.setProperty('--start-tick-gap', keyframes[1].frame / last * 100 + '%');
  }
  $('position').max = last;
  $('position').disabled = false;
  const phaseLengths = phases.map((phase, i) => (phases[i + 1]?.frame ?? last) - phase.frame);
  $('phases').style.gridTemplateColumns = phaseLengths.map(n => 'minmax(0,' + n + 'fr)').join(' ');
  const stops = phases.map((phase, i) => {
    const start = phase.frame / last;
    const end = (phase.frame + phaseLengths[i]) / last;
    const point = (fraction) => 'calc(' + (fraction * 100) + '% + ' + ((.5 - fraction) * 18) + 'px)';
    return (i % 2 ? 'var(--turn)' : 'transparent') + ' ' + point(start) + ' ' + point(end);
  });
  $('position').style.setProperty('--phase-track', 'linear-gradient(to right,' + stops.join(',') + '), var(--hatch)');
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
    button.textContent = keyframe.tickLabel ?? keyframe.label;
    button.setAttribute('aria-label', keyframe.label + ' reference keyframe');
    button.style.setProperty('--tick-point', (keyframe.frame / last) * 100 + '%');
    if (keyframe.frame === 0 || keyframe.frame === last) button.classList.add('edge');
    button.onclick = () => selectFrame(keyframe.frame);
    ticks.append(button);
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

function appendReferenceCredit(parent, reference, includeLicense = true) {
  if (reference.url) addSourceLink(parent, reference.credit ?? 'Acquired image source', reference.url);
  else if (reference.credit) parent.append(reference.credit);
  if (includeLicense && reference.license) {
    if (parent.childNodes.length) parent.append(' · ');
    if (reference.licenseUrl) addSourceLink(parent, reference.license, reference.licenseUrl);
    else parent.append(reference.license);
  }
}

function configureSources() {
  const anatomy = $('anatomySource');
  anatomy.append('Anatomy source · ');
  const sources = [anatomySource(), ...(selectedTour.additionalAnatomySources ?? [])];
  sources.forEach((source, index) => {
    if (index) anatomy.append(' · ');
    const credit = document.createElement('span');
    appendReferenceCredit(credit, { ...source, credit: source.label });
    anatomy.append(credit);
  });
  anatomy.append('. The transducer and tissue appearance are authored.');
  anatomy.hidden = false;
  $('atlasSource').hidden = !usesBodyParts3D(selectedTour);
  if (selectedTour.bodyRegion === 'Neck') $('atlasFitScope').textContent = 'the BodyParts3D adult skin model';
  $('tourSourceNote').textContent = selectedTour.sourceNote ?? '';
  $('tourSourceNote').hidden = !selectedTour.sourceNote;
  const comparisonIds = new Set(keyframes.map((key) => key.referenceId));
  const comparisons = [...comparisonIds].map(referenceById).filter(Boolean);
  for (const reference of [...comparisons, ...relatedReferences]) {
    const item = document.createElement('p');
    if (reference.title) item.append(reference.title + ' · ');
    appendReferenceCredit(item, reference);
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

function initialTourFrame() {
  if (selectedTour.id === 'gallbladder' && location.hash === '#guided') return 0;
  const frame = selectedTour.initialFrame;
  return Number.isInteger(frame) && frame >= 0 && frame <= last ? frame : keyframes[0].frame;
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
  pregnancyNavigation(tours);
  configureStudyPicker($('sweepPicker'), tours, selectedTour.id, new URL('.', location.href));
  window.addEventListener('pageshow', updateTorsoOpacity);
  $('tourTitle').textContent = selectedTour.title;
  document.title = selectedTour.title + ' · Ultrasound Anatomy';
  poses = await loadPoses(selectedTour.assetRoot);
  last = poses.length - 1;
  keyframes = selectedTour.keyframes.filter((key) => key.frame >= 0 && key.frame <= last).sort((a, b) => a.frame - b.frame);
  if (!keyframes.length) throw new Error('Reference keyframes unavailable.');
  phases = selectedTour.phases ?? [
    { frame: 0, label: 'Find window' },
    { frame: keyframes.find(({ frame }) => frame > 0)?.frame ?? last, label: 'Rotate probe' },
  ];
  configureTimeline();
  $('apToggle').hidden = !selectedTour.showApSpan;
  configureSiblingRoutes(tours);
  if (selectedTour.steering) {
    const { probeSteering } = await import('./probe-steering.js');
    steering = probeSteering(selectedTour.steering, $('steering'), selectFrame, pause);
    $('sceneHelp').textContent = 'Drag the probe to slide or rock · Drag the body to orbit';
    $('sceneHelp').classList.add('steerHelp');
    $('compression').hidden = !selectedTour.compressionMm;
  }
  $('showRoute').hidden = !selectedTour.showRoute;
  $('scanDetail').textContent = scanDimensions(initialTourFrame());
  if (selectedTour.pregnancyStage) {
    $('sceneCanvas').setAttribute('aria-label', 'Probe, scan sector and maternal and fetal anatomy at ' + selectedTour.pregnancyStage.age.toLowerCase());
  }
  if (isLinear()) {
    $('surfaceOpacityLabel').textContent = 'Skin opacity';
    $('sceneCanvas').setAttribute('aria-label', `Linear probe, rectangular imaging field, ${selectedTour.region.toLowerCase()} and internal anatomy with patient orientation`);
  }
  configureLegend($('sceneLegend'), [{ label: fieldLabel(), color: '#84b5d1' }, ...selectedTour.parts]);
  configureLegend($('legend'), selectedTour.overlayParts ?? selectedTour.parts);
  configureRelatedPlates();
  configureSources();
  state.frame = initialTourFrame();
  drawReadout(state.frame);
  const currentKeyframe = nearestKeyframe(state.frame);
  $('referenceNote').textContent = acquiredFor(currentKeyframe) ? referenceNote(state.frame, currentKeyframe) : 'Reference unavailable';
  $('tour').hidden = false;
  $('assetTab').disabled = false;
  $('tourTab').disabled = false;
  renderFrame(state.frame);
  const sceneReady = startScene();
  await prepareSequence('scan', state.frame);
  for (const key of keyframes) await prepare(acquiredFor(key)?.path).pending;
  state.ready = true;
  updatePlay();
  await sceneReady;
  prepareSequence('section', state.frame);
}

window.addEventListener('hashchange', () => {
  if (selectedTour?.id === 'gallbladder' && keyframes &&
      (location.hash === '#probe' || location.hash === '#guided')) {
    showAssets(false);
    selectFrame(initialTourFrame());
  }
});

startTour().catch((error) => {
  $('tourStatus').textContent = 'This sweep is unavailable. Select another sweep if available.';
  $('tourStatus').hidden = false;
  console.warn('Ultrasound sweep unavailable.', error);
});
