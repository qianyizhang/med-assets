import { colorVelocityAt, duplexSample, duplexStations, icaCcaRatio, registeredAcquisition } from './duplex.js';
import { createReconstruction, showSpectrum } from './survey-visuals.js';

const $ = (id) => document.getElementById(id);
const sides = ['right', 'left'];
const sideName = (side) => side[0].toUpperCase() + side.slice(1);
const sideButtons = [...document.querySelectorAll('[data-side]')];
const modeButtons = [...document.querySelectorAll('[data-mode]')];
const cameraButtons = [...document.querySelectorAll('[data-camera]')];
const media = new Map();
const sessionKey = 'ultrasound-carotid-exam-v1';
const svgNS = 'http://www.w3.org/2000/svg';
const modeName = { transverse: 'Transverse', longitudinal: 'Long axis', color: 'Color Doppler', spectral: 'Spectral Doppler' };
const state = {
  side: 'right', station: null, mode: 'transverse', track: 0, tracking: false, request: 0,
  desiredReference: null, shownReference: null, pendingReference: null,
  view: null, geometry: null, captured: new Set(), samples: new Set(), records: new Map(),
  distances: [null, null], calipers: false, branches: false, branchLabels: [], branchRequest: 0,
  recording: false, angle: null, reconstruction: null,
  spectrum: null, coverage: new Map(), captureView: null, stackRun: null, examRun: null, examIndex: 0,
};
let protocol;
let stations;

const setPressed = (button, pressed) => button.setAttribute('aria-pressed', String(pressed));
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
const dot = (a, b) => a.reduce((sum, value, i) => sum + value * b[i], 0);
const reference = (id) => typeof abdomenReferences === 'undefined' ? undefined : abdomenReferences[id];
const urlFor = (path) => new URL(path, document.baseURI).href;
const announce = (message) => { $('announcement').textContent = message; };

function resource(path, useGallery = false) {
  const url = urlFor((useGallery ? '../' : './data/') + path);
  if (!media.has(url)) {
    const image = new Image();
    image.src = url;
    media.set(url, image.decode().then(() => image, () => {
      media.delete(url);
      return null;
    }));
  }
  return media.get(url);
}

function restore() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(sessionKey));
    if (!saved || saved.dataset !== protocol.datasetId) return;
    state.captured = new Set(saved.captured);
    state.samples = new Set(saved.samples);
    state.records = new Map(saved.records);
  } catch { /* The exam is still usable when session storage is unavailable. */ }
}

function persist() {
  try {
    sessionStorage.setItem(sessionKey, JSON.stringify({
      dataset: protocol.datasetId, captured: [...state.captured], samples: [...state.samples], records: [...state.records],
    }));
  } catch { /* Measurements remain usable in memory for this page. */ }
}

function sideStations(side = state.side) {
  return stations.filter((station) => station.side === side);
}

function trackFrames() { return protocol.tracking[state.side]; }

function stationFrame(station) {
  const frames = trackFrames();
  if (station.trackId) {
    const byId = frames.findIndex((frame) => frame.id === station.trackId);
    if (byId >= 0) return byId;
  }
  const byPath = frames.findIndex((frame) => frame.path === station.views?.transverse?.path);
  if (byPath >= 0) return byPath;
  return Math.max(0, frames.findIndex((frame) => frame.segment === station.segment));
}

function requestedView() {
  if (state.mode !== 'transverse') return { view: state.station.views?.longitudinal, track: null };
  const track = state.tracking ? trackFrames()[state.track] : null;
  return { view: track ?? state.station.views?.transverse, track };
}

function changeStation(station, keepExam = false) {
  if (!keepExam) stopExam();
  stopStack();
  state.side = station.side;
  state.station = station;
  state.track = stationFrame(station);
  state.tracking = false;
  resetMeasurement();
  updateStationControl();
  return render();
}

function selectTracking(index) {
  state.track = index;
  state.tracking = true;
  const frame = trackFrames()[index];
  const station = sideStations().find((station) => station.id === frame.stationId)
    ?? sideStations().filter((station) => frame.segment === 'cca' ? station.segment.startsWith('cca-')
      : ['bulb', 'ica-prox', 'ica-mid', 'ica-dist'].includes(station.segment))
      .reduce((best, candidate) => !best || Math.abs(stationFrame(candidate) - index) < Math.abs(stationFrame(best) - index)
        ? candidate : best, null);
  if (station) state.station = station;
  $('station').value = state.station.id;
  resetMeasurement();
  return render();
}

function stopStack() {
  state.stackRun = null;
  setPressed($('acquireStack'), false);
  $('acquireStack').textContent = 'Acquire stack';
}

async function acquireStack() {
  stopExam();
  if (state.stackRun) { stopStack(); return; }
  const walk = Symbol('transverse acquisition');
  state.stackRun = walk;
  setPressed($('acquireStack'), true);
  $('acquireStack').textContent = 'Stop acquisition';
  for (let index = 0; index < trackFrames().length && state.stackRun === walk; index += 1) {
    await selectTracking(index);
    if (state.stackRun !== walk) break;
    await new Promise((resolve) => setTimeout(resolve, 62));
  }
  if (state.stackRun === walk) {
    stopStack();
    announce($('reconstructionSummary').textContent);
  }
}

function setExamPhase(text) {
  if ($('examPhase').textContent === text) return;
  $('examPhase').hidden = !text;
  $('examPhase').textContent = text;
}

function stopExam() {
  if (!state.examRun) return;
  const { manualPrf, phase } = state.examRun;
  state.examRun = null;
  $('scale').value = manualPrf;
  setPressed($('playExam'), false);
  $('playExam').textContent = 'Resume exam';
  setExamPhase('Paused · ' + phase);
  updateDoppler();
}

function examSteps() {
  return sides.flatMap((side) => [
    ...protocol.tracking[side].map((_, track) => ({ side, track })),
    ...sideStations(side).flatMap((station) => progressModes(station).map((mode) => ({ side, station, mode }))),
  ]);
}

async function playExam() {
  if (state.examRun) { stopExam(); return; }
  stopStack();
  const steps = examSteps();
  if (state.examIndex >= steps.length) state.examIndex = 0;
  const run = { manualPrf: $('scale').value, phase: '' };
  state.examRun = run;
  setPressed($('playExam'), true);
  $('playExam').textContent = 'Pause exam';
  while (state.examIndex < steps.length && state.examRun === run) {
    const step = steps[state.examIndex];
    const tracking = Number.isInteger(step.track);
    run.phase = sideName(step.side) + ' · ' + (tracking ? 'Transverse stack' : step.station.label + ' · ' + modeName[step.mode]);
    setExamPhase(run.phase);
    if (tracking) {
      state.mode = 'transverse';
      if (state.side !== step.side) {
        state.side = step.side;
        state.station = sideStations()[0];
        updateStationControl();
      }
      await selectTracking(step.track);
    } else {
      state.mode = step.mode;
      if (step.mode === 'spectral') $('scale').value = '6500';
      await changeStation(step.station, true);
    }
    if (state.examRun !== run) return;
    if (step.mode === 'spectral') {
      if (state.spectrum?.status === 'aliased') {
        $('scale').value = '9000';
        updateDoppler();
      }
      recordWaveform(false);
    } else if (!$('capture').disabled) {
      recordCapture(true);
      $('capture').textContent = 'Image captured';
    }
    state.examIndex += 1;
    await new Promise((resolve) => setTimeout(resolve, tracking ? 53 : 490));
  }
  if (state.examRun !== run) return;
  state.examRun = null;
  $('scale').value = run.manualPrf;
  updateDoppler();
  setPressed($('playExam'), false);
  $('playExam').textContent = 'Replay exam';
  const remaining = steps.filter((step) => Number.isInteger(step.track)
    ? !state.samples.has(step.side + '/' + protocol.tracking[step.side][step.track].id)
    : !state.captured.has(key(step.station, step.mode))).length;
  setExamPhase(remaining ? 'Playback complete · ' + remaining + ' acquisitions unavailable' : 'Exam playback complete');
}

function resetMeasurement() {
  state.distances = [null, null];
  $('caliperPoint').value = '0';
  state.angle = null;
  $('gate').value = '0';
}

function updateStationControl() {
  const select = $('station');
  select.replaceChildren(...sideStations().map((station) => new Option(station.label, station.id)));
  select.value = state.station.id;
  sideButtons.forEach((button) => setPressed(button, button.dataset.side === state.side));
  $('sweepsLink').href = '../index.html?sweep=carotid-' + state.side;
  $('openVolume').href = './volume.html?side=' + state.side;
  $('track').max = String(Math.max(0, trackFrames().length - 1));
}

function modeAvailable(mode, station) {
  const candidate = gateForMode(station, mode);
  const gate = candidate && candidate.steeringSupported !== false;
  if (mode === 'spectral') return Boolean(station.waveform && gate && station.views?.longitudinal);
  if (mode === 'color') return Boolean(colorStation(station) && gate
    && (station.segment === 'bulb' ? station.forkEvidence?.arterialMaskPaths?.longitudinal?.cca
      : station.views?.longitudinal?.dopplerMaskPath || station.views?.longitudinal?.lumenMaskPath));
  return Boolean(station.views?.[mode]);
}

function gateForMode(station, mode) {
  return mode === 'color' ? station.colorGate ?? station.gate : station.gate;
}

function colorStation(station) {
  return station.waveform ? station : station.segment === 'bulb'
    ? sideStations(station.side).find((candidate) => candidate.segment === 'cca-dist' && candidate.waveform) : null;
}

function progressModes(station) { return Object.keys(modeName).filter((mode) => modeAvailable(mode, station)); }
function key(station, mode) { return station.id + '/' + mode; }

function recordCapture(silent = false) {
  if (!state.captureView) return;
  const { station, mode, track } = state.captureView;
  if (!track) state.captured.add(key(station, mode));
  if (track) state.samples.add(station.side + '/' + track.id);
  if (!silent) announce(sideName(station.side) + ' ' + station.label + ' ' + modeName[mode] + ' captured.');
  persist();
  updateProgress();
  updateReconstruction();
}

function createCoverage() {
  for (const side of sides) {
    const group = document.createElement('section');
    group.className = 'coverageSide';
    const heading = document.createElement('h3');
    heading.textContent = sideName(side);
    const list = document.createElement('div');
    list.className = 'coverageList';
    for (const station of sideStations(side)) {
      const control = document.createElement('button');
      control.type = 'button';
      control.onclick = () => changeStation(station);
      state.coverage.set(station.id, control);
      list.append(control);
    }
    group.append(heading, list);
    $('coverage').append(group);
  }
}

function updateProgress() {
  let total = 0;
  let count = 0;
  for (const station of stations) {
    const modes = progressModes(station);
    const done = modes.filter((mode) => state.captured.has(key(station, mode))).length;
    total += modes.length;
    count += done;
    const button = state.coverage.get(station.id);
    const coverage = modes.length ? done + '/' + modes.length : 'Unavailable';
    button.textContent = station.label + ' · ' + coverage;
    button.dataset.captured = String(Boolean(modes.length) && done === modes.length);
    setPressed(button, station.id === state.station.id);
    button.setAttribute('aria-label', sideName(station.side) + ' ' + station.label + ', ' + (modes.length ? done + ' of ' + modes.length + ' captures' : 'acquisition unavailable'));
  }
  $('progress').value = count;
  $('progress').max = total || 1;
  const progress = count + ' / ' + total + ' captures';
  if ($('progressText').textContent !== progress) $('progressText').textContent = progress;
  $('reconstructionSummary').textContent = sides.map((side) => {
    const count = protocol.tracking[side].filter((frame) => state.samples.has(side + '/' + frame.id)).length;
    return sideName(side) + ' ' + count + '/' + protocol.tracking[side].length;
  }).join(' · ') + ' transverse samples';
  const complete = trackFrames().every((frame) => state.samples.has(state.side + '/' + frame.id));
  $('openVolume').hidden = !complete;
  $('volumeHint').hidden = complete;
}

function updateReconstruction() {
  state.reconstruction?.update(state.samples, state.view, state.side);
  $('exportMesh').disabled = !state.reconstruction || !state.samples.size;
}

function setSkinOpacity() {
  const value = Number($('skinOpacity').value);
  $('skinValue').textContent = value + '%';
  $('skinOpacity').setAttribute('aria-valuetext', value + '%');
  state.reconstruction?.setOpacity(value / 100);
}

function annotation(tag, attrs) {
  const node = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  $('annotations').append(node);
}
function line(x1, y1, x2, y2, color, width = 2) {
  annotation('line', { x1, y1, x2, y2, stroke: color, 'stroke-width': width, 'vector-effect': 'non-scaling-stroke' });
}

function updateCalipers() {
  const view = state.view;
  const allowed = Boolean(view && ['transverse', 'longitudinal'].includes(state.mode));
  $('calipers').disabled = !allowed;
  $('caliperTools').hidden = !state.calipers || !allowed;
  $('scanPlane').classList.toggle('isMeasuring', state.calipers && allowed);
  setPressed($('calipers'), state.calipers && allowed);
  if (!allowed || !state.calipers) return;
  const point = state.distances[Number($('caliperPoint').value)];
  const x = $('caliperX');
  const y = $('caliperY');
  x.max = String(view.widthPx);
  y.max = String(view.heightPx);
  x.value = point?.[0] ?? view.widthPx / 2;
  y.value = point?.[1] ?? view.heightPx / 2;
  x.setAttribute('aria-valuetext', ((Number(x.value) - view.centerPx[0]) * view.mmPerPx).toFixed(1) + ' mm across center');
  y.setAttribute('aria-valuetext', ((Number(y.value) - view.centerPx[1]) * view.mmPerPx).toFixed(1) + ' mm depth');
  const [a, b] = state.distances;
  const distance = a && b ? Math.hypot(a[0] - b[0], a[1] - b[1]) * view.mmPerPx : null;
  $('caliperDistance').textContent = distance === null ? 'Place A and B' : distance.toFixed(1) + ' mm';
  $('saveDistance').disabled = !(distance > 0);
  if (a && b) line(...a, ...b, '#ffd98f', 1.25);
  for (const [index, at] of state.distances.entries()) {
    if (!at) continue;
    const [x, y] = at;
    line(x - 7, y, x + 7, y, '#ffd98f');
    line(x, y - 7, x, y + 7, '#ffd98f');
    annotation('text', { x: x + 8, y: y - 8, fill: '#ffd98f', 'font-family': 'system-ui', 'font-size': '15' });
    $('annotations').lastElementChild.textContent = ['A', 'B'][index];
  }
}

function measureAt(event, end = false) {
  if (!state.calipers || !state.view || $('caliperTools').hidden) return;
  const matrix = $('annotations').getScreenCTM();
  if (!matrix) return;
  const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
  const view = state.view;
  if (point.x < 0 || point.y < 0 || point.x > view.widthPx || point.y > view.heightPx) return;
  const index = Number($('caliperPoint').value);
  state.distances[index] = [point.x, point.y];
  if (end && index === 0 && !state.distances[1]) $('caliperPoint').value = '1';
  redrawAnnotations();
}

function chosenAcquisition() {
  const gate = gateForMode(state.station, state.mode);
  const offset = Number($('gate').value);
  let angleDeg = state.angle;
  if (angleDeg === null && gate?.beamDirection && gate?.flowDirection) {
    const normal = Math.hypot(...gate.beamDirection) * Math.hypot(...gate.flowDirection);
    angleDeg = Math.acos(clamp(Math.abs(dot(gate.beamDirection, gate.flowDirection) / normal), 0, 1)) * 180 / Math.PI;
  }
  return registeredAcquisition(gate, { radiusFraction: Math.abs(offset) / 100, angleDeg: angleDeg ?? undefined,
    prfHz: Number($('scale').value) });
}

function drawGate(acquisition, spectral) {
  const view = state.view;
  const gate = gateForMode(state.station, state.mode);
  if (!view || !gate?.centerPx || !acquisition) return;
  const [gx, gy] = gate.centerPx;
  const [fx, fy] = [dot(gate.flowDirection, view.width), dot(gate.flowDirection, view.beam)];
  const flowScale = Math.hypot(fx, fy) || 1;
  const [bx, by] = [dot(gate.beamDirection, view.width), dot(gate.beamDirection, view.beam)];
  const beamScale = Math.hypot(bx, by) || 1;
  const offset = spectral ? Number($('gate').value) / 100 * gate.diameterMm / (2 * view.mmPerPx) : 0;
  const x = gx - fy / flowScale * offset;
  const y = gy + fx / flowScale * offset;
  const axialPx = acquisition.gate.lengthMm / (2 * view.mmPerPx);
  const dx = bx * axialPx / beamScale, dy = by * axialPx / beamScale;
  const [originX, originY] = gate.steeredOriginPx ?? [x - bx * 31 / beamScale, y - by * 31 / beamScale];
  line(originX, originY, x + bx * 12 / beamScale, y + by * 12 / beamScale, spectral ? '#e9e9d3' : '#92aa9f', 1);
  if (!spectral) return;
  const flowSign = bx * fx + by * fy >= 0 ? 1 : -1;
  const turn = bx * fy - by * fx >= 0 ? flowSign : -flowSign;
  const angle = turn * (acquisition.angleDeg ?? 0) * Math.PI / 180;
  const ax = (bx * Math.cos(angle) - by * Math.sin(angle)) / beamScale * 20;
  const ay = (bx * Math.sin(angle) + by * Math.cos(angle)) / beamScale * 20;
  line(x - ax, y - ay, x + ax, y + ay, '#aee7d6', 1);
  for (const [ax, ay] of [[x - dx, y - dy], [x + dx, y + dy]]) {
    line(ax + by * 5 / beamScale, ay - bx * 5 / beamScale, ax - by * 5 / beamScale, ay + bx * 5 / beamScale, '#ffdf9d', 2);
  }
}

function redrawAnnotations() {
  $('annotations').replaceChildren();
  if (state.view) $('annotations').setAttribute('viewBox', '0 0 ' + state.view.widthPx + ' ' + state.view.heightPx);
  updateCalipers();
  if (['color', 'spectral'].includes(state.mode) && state.view) drawGate(chosenAcquisition(), state.mode === 'spectral');
  for (const label of state.branchLabels) {
    annotation('text', { x: label.x, y: label.y, fill: label.color, stroke: '#102021',
      'stroke-width': '3', 'paint-order': 'stroke', 'font-family': 'system-ui', 'font-size': '15',
      'font-weight': '700', 'text-anchor': 'middle', 'dominant-baseline': 'central' });
    $('annotations').lastElementChild.textContent = label.name;
  }
}

async function drawBranches(request) {
  const ticket = ++state.branchRequest;
  const namedView = state.mode === 'longitudinal' || (state.mode === 'transverse' && !state.tracking);
  const paths = namedView
    ? state.station.forkEvidence?.arterialMaskPaths?.[state.mode] : null;
  $('showBranches').hidden = !paths;
  $('showBranches').disabled = !state.view;
  $('branches').hidden = true;
  state.branchLabels = [];
  setPressed($('showBranches'), Boolean(paths && state.branches));
  redrawAnnotations();
  if (!paths || !state.view || !state.branches) return;
  const { widthPx: width, heightPx: height } = state.view;
  const colors = { cca: [255, 200, 109], ica: [139, 227, 215], eca: [240, 167, 225] };
  const plans = await Promise.all(Object.entries(paths).map(async ([segment, path]) => [segment, await resource(path)]));
  if (request !== state.request || ticket !== state.branchRequest || !state.branches) return;
  const canvas = $('branches');
  canvas.width = width;
  canvas.height = height;
  const draw = canvas.getContext('2d');
  const scratch = document.createElement('canvas');
  scratch.width = width;
  scratch.height = height;
  const maskContext = scratch.getContext('2d', { willReadFrequently: true });
  const overlay = draw.createImageData(width, height);
  for (const [segment, image] of plans) {
    const rgb = colors[segment];
    if (!image || !rgb || image.naturalWidth !== width || image.naturalHeight !== height) continue;
    maskContext.clearRect(0, 0, width, height);
    maskContext.drawImage(image, 0, 0);
    const mask = maskContext.getImageData(0, 0, width, height).data;
    const inside = (x, y) => x >= 0 && y >= 0 && x < width && y < height && mask[(y * width + x) * 4] > 100;
    let count = 0, sumX = 0, sumY = 0;
    for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
      if (!inside(x, y)) continue;
      count += 1;
      sumX += x;
      sumY += y;
      const inner = inside(x - 1, y) && inside(x + 1, y) && inside(x, y - 1) && inside(x, y + 1);
      overlay.data.set([...rgb, inner ? 40 : 235], (y * width + x) * 4);
    }
    if (count) state.branchLabels.push({ name: segment.toUpperCase(), x: sumX / count, y: sumY / count, color: `rgb(${rgb.join(',')})` });
  }
  draw.putImageData(overlay, 0, 0);
  canvas.hidden = !state.branchLabels.length;
  redrawAnnotations();
}

function loadColorMask(image, centerPx) {
  const canvas = $('color');
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.drawImage(image, 0, 0);
  const bytes = context.getImageData(0, 0, canvas.width, canvas.height).data;
  if (centerPx) {
    // Legacy union masks can include neighboring vessels. Start inside the
    // gated lumen and retain only its visible connected component.
    const startX = Math.round(centerPx[0]);
    const startY = Math.round(centerPx[1]);
    let start = -1;
    let closest = Infinity;
    for (let y = Math.max(0, startY - 10); y <= Math.min(canvas.height - 1, startY + 10); y += 1) {
      for (let x = Math.max(0, startX - 10); x <= Math.min(canvas.width - 1, startX + 10); x += 1) {
        const i = y * canvas.width + x;
        const distance = (x - startX) ** 2 + (y - startY) ** 2;
        if (bytes[i * 4] >= 100 && bytes[i * 4 + 3] >= 100 && distance < closest) { start = i; closest = distance; }
      }
    }
    const component = new Uint8Array(canvas.width * canvas.height);
    const visited = start < 0 ? [] : [start];
    if (start >= 0) component[start] = 1;
    for (let position = 0; position < visited.length; position += 1) {
      const i = visited[position];
      const x = i % canvas.width;
      const y = Math.floor(i / canvas.width);
      const neighbors = [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]];
      for (const [nx, ny] of neighbors) {
        if (nx < 0 || ny < 0 || nx >= canvas.width || ny >= canvas.height) continue;
        const k = ny * canvas.width + nx;
        if (component[k] || bytes[4 * k] < 100 || bytes[4 * k + 3] < 100) continue;
        component[k] = 1;
        visited.push(k);
      }
    }
    for (let i = 0; i < component.length; i += 1) if (!component[i]) bytes[4 * i] = 0;
  }
  const columns = Array.from({ length: canvas.width }, () => [canvas.height, -1]);
  for (let y = 0; y < canvas.height; y += 1) {
    for (let x = 0; x < canvas.width; x += 1) {
      const i = (y * canvas.width + x) * 4;
      if (bytes[i] < 100 || bytes[i + 3] < 100) continue;
      columns[x][0] = Math.min(columns[x][0], y);
      columns[x][1] = y;
    }
  }
  return { bytes, columns };
}

function paintColor(acquisition) {
  const canvas = $('color');
  const waveform = colorStation(state.station);
  if (!state.geometry || state.mode !== 'color' || !acquisition || !waveform) return false;
  const { bytes, columns } = state.geometry;
  const context = canvas.getContext('2d');
  const overlay = context.createImageData(canvas.width, canvas.height);
  const phase = Number($('phase').value) / 100;
  const maxVelocity = 100 * 1540 * acquisition.prfHz / (4 * (acquisition.frequencyMHz ?? 5) * 1e6);
  const velocities = Array.from({ length: 101 }, (_, radial) =>
    colorVelocityAt(waveform, acquisition, { phase, radiusFraction: radial / 100 }));
  for (const [x, [low, high]] of columns.entries()) {
    if (high < low) continue;
    const mid = (low + high) / 2;
    const half = Math.max(1, (high - low) / 2);
    for (let y = low; y <= high; y += 1) {
      const i = (y * canvas.width + x) * 4;
      if (bytes[i] < 100 || bytes[i + 3] < 100) continue;
      const radial = Math.min(100, Math.round(100 * Math.abs(y - mid) / half));
      const velocity = velocities[radial];
      const strength = Math.min(1, Math.abs(velocity) / maxVelocity);
      if (!(strength > .03)) continue;
      overlay.data.set(velocity > 0
        ? [238, 55 + 145 * strength, 44 - 18 * strength, 125 + 107 * strength]
        : [30 + 79 * strength, 86 + 133 * strength, 235, 125 + 107 * strength], i);
    }
  }
  context.putImageData(overlay, 0, 0);
  return overlay.data.some((value, index) => index % 4 === 3 && value > 0);
}

function updateDoppler() {
  const active = state.mode === 'color' || state.mode === 'spectral';
  const spectral = state.mode === 'spectral';
  $('dopplerTools').hidden = !active;
  $('phaseControl').hidden = spectral;
  $('gateControl').hidden = !spectral;
  $('angleControl').hidden = !spectral;
  $('angleValue').hidden = !spectral;
  $('spectrum').hidden = true;
  $('spectralPanel').hidden = !spectral;
  $('saveWaveform').disabled = true;
  $('gate').disabled = !spectral || !state.view;
  $('angle').disabled = !spectral || !state.view;
  $('phase').disabled = !state.geometry || !state.view;
  $('scale').disabled = !state.view;
  $('color').hidden = true;
  $('velocityKey').hidden = true;
  state.spectrum = null;
  $('velocityReadout').textContent = '';
  if (!active) return;
  const acquisition = chosenAcquisition();
  const angleDeg = acquisition?.angleDeg;
  const offset = Number($('gate').value);
  if (Number.isFinite(angleDeg)) $('angle').value = String(Math.round(angleDeg));
  $('angleValue').textContent = Number.isFinite(angleDeg) ? Math.round(angleDeg) + '°' : '—';
  $('angle').setAttribute('aria-valuetext', $('angleValue').textContent);
  $('gate').setAttribute('aria-valuetext', offset + '% of lumen radius');
  $('phase').setAttribute('aria-valuetext', $('phase').value + '% of cardiac cycle');
  if (!state.view) { $('dopplerStatus').textContent = 'Acquisition image unavailable.'; return; }
  if (!spectral) {
    const painted = paintColor(acquisition);
    $('color').hidden = !painted;
    $('velocityKey').hidden = !painted;
    $('dopplerStatus').textContent = painted ? (state.station.segment === 'bulb' ? 'Modeled flow in the CCA portion of the bulb'
      : 'Modeled axial flow · Color scale shows direction relative to probe') : 'Registered color data unavailable.';
    return;
  }
  const sample = duplexSample(state.station, acquisition);
  state.spectrum = sample;
  if (sample.power) {
    showSpectrum($('spectrum'), sample);
    $('spectrum').hidden = false;
  }
  if (sample.measurements) {
    const { psvCmS, edvCmS } = sample.measurements;
    const values = 'PSV ' + psvCmS.toFixed(1) + ' · EDV ' + edvCmS.toFixed(1) + ' cm/s';
    $('velocityReadout').textContent = values;
    $('spectrum').setAttribute('aria-label', 'Modeled spectral Doppler waveform. ' + values);
    $('saveWaveform').disabled = false;
  }
  $('dopplerStatus').textContent = sample.status === 'aliased'
    ? 'Aliasing at this PRF. Increase PRF to measure velocities.'
    : sample.reason ?? 'Modeled flow ' + sample.beamDirection + ' the probe · Beam angle ' + Math.round(sample.actualAngleDeg) + '°';
}

function appendLink(parent, title, url) {
  if (!url) return;
  const link = document.createElement('a');
  link.href = url;
  link.textContent = title;
  parent.append(link);
}

async function renderReference() {
  const ids = state.station.referenceIds ?? [];
  const candidates = ids.map(reference).filter(Boolean);
  const kind = (item) => /color doppler/i.test(item.label ?? '') ? 'color'
    : /spectral|waveform/i.test(item.label ?? '') ? 'spectral' : item.plane;
  const row = candidates.find((item) => kind(item) === state.mode) ?? candidates[0];
  state.desiredReference = row;
  $('comparison').hidden = !row;
  const content = $('comparisonContent');
  if (!row || !$('comparison').open || row === state.shownReference || row === state.pendingReference?.row) return;
  const request = { row };
  state.pendingReference = request;
  content.setAttribute('aria-busy', 'true');
  const img = await resource(row.path, true);
  if (state.pendingReference !== request) return;
  state.pendingReference = null;
  content.setAttribute('aria-busy', 'false');
  if (state.desiredReference !== row || !$('comparison').open) return;
  state.shownReference = row;
  content.replaceChildren();
  if (img) {
    const copy = img.cloneNode();
    copy.alt = row.title ?? 'Acquired comparison';
    content.append(copy);
  }
  const copy = document.createElement('p');
  copy.textContent = img ? (row.label ?? row.title ?? '') : 'Comparison image unavailable.';
  content.append(copy);
  const details = document.createElement('details');
  const title = document.createElement('summary');
  title.textContent = 'Source and comparison context';
  details.append(title);
  if (row.note) {
    const note = document.createElement('p');
    note.textContent = row.note;
    details.append(note);
  }
  const credit = document.createElement('p');
  appendLink(credit, row.credit ?? 'Source', row.url);
  if (row.license) credit.append(' · ');
  appendLink(credit, row.license, row.licenseUrl);
  details.append(credit);
  content.append(details);
}

async function render() {
  const request = ++state.request;
  if (!modeAvailable(state.mode, state.station)) state.mode = 'transverse';
  const { view, track } = requestedView();
  const mode = state.mode;
  const station = state.station;
  const captureKey = track ? station.side + '/' + track.id : key(station, mode);
  state.captureView = null;
  $('capture').disabled = true;
  $('calipers').disabled = true;
  $('saveDistance').disabled = true;
  $('saveWaveform').disabled = true;
  $('track').value = String(state.track);
  const position = trackFrames()[state.track];
  const trackingLabel = Number.isFinite(position?.distanceMm) ? position.distanceMm.toFixed(0) + ' mm' : (state.track + 1) + ' / ' + trackFrames().length;
  $('trackReadout').textContent = trackingLabel;
  $('track').setAttribute('aria-valuetext', trackingLabel);
  $('scanHeading').textContent = modeName[mode];
  const context = track ? (track.segment === 'cca' ? 'Common carotid tracking' : 'Bifurcation and branch tracking') : station.label;
  $('scanContext').textContent = sideName(station.side) + ' · ' + context + (!track && station.waveform && !modeAvailable('spectral', station)
    ? ' · Doppler window unavailable' : '');
  modeButtons.forEach((btn) => {
    setPressed(btn, btn.dataset.mode === mode);
    btn.disabled = !(state.tracking && btn.dataset.mode === 'transverse') && !modeAvailable(btn.dataset.mode, station);
  });
  $('recordTracking').hidden = mode !== 'transverse';
  $('acquireStack').hidden = mode !== 'transverse';
  $('track').disabled = mode !== 'transverse';
  $('display').setAttribute('aria-busy', 'true');
  updateProgress();
  renderReference();
  const image = view?.path ? await resource(view.path) : null;
  const targetMask = view?.dopplerMaskPath ?? station.forkEvidence?.arterialMaskPaths?.longitudinal?.cca;
  const maskPath = targetMask ?? view?.lumenMaskPath;
  const mask = image && mode === 'color' && maskPath ? await resource(maskPath) : null;
  if (request !== state.request) return;
  state.view = image ? view : null;
  state.geometry = mask ? loadColorMask(mask, targetMask ? null : gateForMode(station, mode)?.centerPx) : null;
  $('scanPlane').hidden = !image;
  $('scanStatus').hidden = Boolean(image);
  $('orientation').hidden = !image;
  $('scanStatus').textContent = station.reason ?? 'Acquisition image unavailable.';
  if (image) {
    const field = (view.widthPx * view.mmPerPx / 10).toFixed(1) + ' × ' + (view.heightPx * view.mmPerPx / 10).toFixed(1) + ' cm';
    $('orientation').textContent = (mode === 'transverse' ? 'Transverse' : 'Long axis') + ' · ' + field;
    $('scan').src = image.src;
    $('scan').alt = 'Modeled ' + modeName[mode].toLowerCase() + ' image, ' + sideName(station.side) + ' ' + context;
    state.captureView = { mode, station, track, captureKey };
    if (track && (state.recording || state.stackRun)) recordCapture(true);
  }
  $('capture').disabled = !image || mode === 'spectral' || (mode === 'color' && !mask);
  $('capture').textContent = state.samples.has(captureKey) || state.captured.has(captureKey) ? 'Image captured' : 'Capture image';
  $('display').setAttribute('aria-busy', 'false');
  redrawAnnotations();
  drawBranches(request);
  updateDoppler();
  if (mode === 'color' && $('color').hidden) $('capture').disabled = true;
  updateReconstruction();
}

function addRecord(id, record) {
  state.records.set(id, record);
  persist();
  renderRecords();
  announce('Measurement saved for ' + sideName(record.side) + ' ' + record.label + '.');
}

function recordWaveform(overwrite = true) {
  const sample = state.spectrum;
  const { id, side, segment, label } = state.station;
  const recordId = id + '/spectral';
  if (!overwrite && state.records.has(recordId)) return true;
  if (!sample?.measurements || !state.captureView) return false;
  const { psvCmS, edvCmS } = sample.measurements;
  addRecord(recordId, { side, segment, label, type: 'Modeled waveform',
    value: 'PSV ' + psvCmS.toFixed(1) + ' · EDV ' + edvCmS.toFixed(1) + ' cm/s',
    acquisition: Math.round(sample.angleDeg) + '° correction · ' + Number($('scale').value) / 1000 + ' kHz PRF',
    measurements: sample.measurements });
  recordCapture(true);
  return true;
}

function renderRecords() {
  const records = [...state.records.values()];
  $('emptyRecord').hidden = records.length > 0;
  $('recordTable').hidden = !records.length;
  $('records').replaceChildren();
  for (const record of records) {
    const row = document.createElement('tr');
    for (const value of [sideName(record.side), record.label, record.type, record.value, record.acquisition]) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.append(cell);
    }
    $('records').append(row);
  }
  const ratios = sides.map((side) => ({ side, measurement: icaCcaRatio(records, side) })).filter(({ measurement }) => measurement);
  $('ratios').hidden = !ratios.length;
  $('ratios').textContent = ratios.map(({ side, measurement }) => sideName(side) + ' ICA/CCA PSV ratio ' + measurement.ratio.toFixed(2)).join(' · ');
}

function attachControls() {
  $('playExam').onclick = playExam;
  sideButtons.forEach((button) => { button.onclick = () => {
    const stations = sideStations(button.dataset.side);
    changeStation(stations.find((station) => station.segment === state.station.segment) ?? stations[0]);
  }; });
  modeButtons.forEach((button) => { button.onclick = () => {
    stopExam();
    stopStack();
    state.mode = button.dataset.mode;
    if (state.mode !== 'transverse') state.recording = false;
    setPressed($('recordTracking'), state.recording);
    state.distances = [null, null];
    $('caliperPoint').value = '0';
    render();
  }; });
  $('station').onchange = () => changeStation(stations.find((station) => station.id === $('station').value));
  $('track').oninput = () => {
    stopExam();
    stopStack();
    selectTracking(Number($('track').value));
  };
  $('acquireStack').onclick = acquireStack;
  document.addEventListener('visibilitychange', () => { if (document.hidden) { stopExam(); stopStack(); } });
  $('recordTracking').onclick = () => {
    stopExam();
    state.recording = !state.recording;
    setPressed($('recordTracking'), state.recording);
    if (state.recording && state.captureView?.track) {
      recordCapture(true);
      $('capture').textContent = 'Image captured';
    }
  };
  $('capture').onclick = () => {
    stopExam();
    recordCapture();
    $('capture').textContent = 'Image captured';
  };
  $('calipers').onclick = () => {
    stopExam();
    state.calipers = !state.calipers;
    redrawAnnotations();
  };
  $('showBranches').onclick = () => {
    stopExam();
    state.branches = !state.branches;
    drawBranches(state.request);
  };
  $('scanPlane').addEventListener('pointerdown', (event) => {
    if (!state.calipers || !state.view || $('caliperTools').hidden || event.button !== 0) return;
    $('scanPlane').setPointerCapture(event.pointerId);
    measureAt(event);
  });
  $('scanPlane').addEventListener('pointermove', (event) => {
    if ($('scanPlane').hasPointerCapture(event.pointerId)) measureAt(event);
  });
  $('scanPlane').addEventListener('pointerup', (event) => {
    if ($('scanPlane').hasPointerCapture(event.pointerId)) measureAt(event, true);
  });
  $('caliperPoint').onchange = redrawAnnotations;
  for (const id of ['caliperX', 'caliperY']) $(id).oninput = () => {
    state.distances[Number($('caliperPoint').value)] = [Number($('caliperX').value), Number($('caliperY').value)];
    redrawAnnotations();
  };
  $('saveDistance').onclick = () => {
    const view = state.view;
    const [a, b] = state.distances;
    if (!view || !a || !b) return;
    const length = Math.hypot(a[0] - b[0], a[1] - b[1]) * view.mmPerPx;
    const { id, side, segment, label } = state.station;
    const frame = state.mode === 'transverse' ? trackFrames()[state.track].id : state.mode;
    addRecord(id + '/' + frame + '/distance', { side, segment, label: state.captureView?.track ? 'Transverse stack' : label, type: 'B-mode distance',
      value: length.toFixed(1) + ' mm', acquisition: modeName[state.mode], endpointsPx: [a, b], frame });
  };
  $('angle').oninput = () => {
    stopExam();
    state.angle = Number($('angle').value);
    updateDoppler();
    redrawAnnotations();
  };
  for (const id of ['gate', 'scale', 'phase']) $(id).oninput = () => {
    const value = $(id).value;
    stopExam();
    $(id).value = value;
    updateDoppler();
    redrawAnnotations();
  };
  $('saveWaveform').onclick = () => { recordWaveform(); stopExam(); };
  $('comparison').addEventListener('toggle', renderReference);
  for (const button of cameraButtons) {
    button.disabled = true;
    button.onclick = () => state.reconstruction?.setPreset(button.dataset.camera);
  }
  $('skinOpacity').disabled = true;
  $('skinOpacity').oninput = setSkinOpacity;
  $('exportMesh').onclick = () => {
    const mesh = state.reconstruction?.exportMesh();
    if (!mesh) return;
    const url = URL.createObjectURL(new Blob([mesh], { type: 'application/octet-stream' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'captured-carotid-reconstruction.ply';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
}

async function boot() {
  const read = async (path) => {
    const response = await fetch(path);
    if (!response.ok) throw new Error('Exam data failed to load: ' + path);
    return response.json();
  };
  const [manifest, geometry] = await Promise.all([read('./protocol.json'), read('./data/protocol-geometry.json')]);
  const byId = new Map(geometry.stations.map((station) => [station.id, station]));
  protocol = { ...manifest, ...geometry, stations: manifest.stations.map((station) => ({ ...byId.get(station.id), ...station })) };
  if (!protocol.stations?.length || !sides.every((side) => protocol.tracking?.[side]?.length)) throw new Error('Exam acquisitions are unavailable.');
  stations = duplexStations(protocol);
  const requestedSide = new URLSearchParams(location.search).get('side');
  if (sides.includes(requestedSide) && sideStations(requestedSide).length) state.side = requestedSide;
  restore();
  $('gate').min = '-100';
  $('gate').max = '100';
  $('gate').value = '0';
  for (const rate of [2000, 4000, 6500, 9000]) $('scale').add(new Option(rate / 1000 + ' kHz', rate));
  $('scale').value = '6500';
  for (const item of [...(protocol.protocolSources ?? []), ...(protocol.anatomySource ? [protocol.anatomySource] : [])]) {
    const p = document.createElement('p');
    appendLink(p, item.title ?? item.label ?? 'Anatomy source', item.url);
    if (item.licenseUrl) { p.append(' · '); appendLink(p, item.license ?? 'License', item.licenseUrl); }
    $('sources').append(p);
  }
  const scope = document.createElement('p');
  scope.textContent = protocol.scope ?? 'Simulated anatomy and velocities.';
  $('sources').prepend(scope);
  if (protocol.anatomySource) {
    const credit = document.createElement('p');
    credit.textContent = 'Anatomy adapted from Z-Anatomy and BodyParts3D (Database Center for Life Science).';
    $('sources').append(credit);
  }
  const shifts = Object.values(protocol.authoredBranchSeparation ?? {}).map((row) => row.maximumCenterShiftMm);
  if (shifts.length && shifts.every(Number.isFinite)) {
    const note = document.createElement('p');
    const limit = (Math.ceil(Math.max(...shifts) * 10) / 10).toFixed(1);
    note.textContent = 'The atlas’s proximal branch tubes overlap, so each was shifted by up to ' + limit + ' mm to separate them in this teaching model.';
    $('sources').append(note);
  }
  attachControls();
  createCoverage();
  $('loading').hidden = true;
  $('exam').hidden = false;
  changeStation(sideStations()[0]);
  renderRecords();
  try {
    state.reconstruction = await createReconstruction($('reconstruction'), protocol, (preset) => {
      cameraButtons.forEach((button) => setPressed(button, button.dataset.camera === preset));
    });
    $('reconstructionStatus').hidden = true;
    cameraButtons.forEach((button) => { button.disabled = false; });
    $('skinOpacity').disabled = !protocol.context?.skinPath;
    setSkinOpacity();
    updateReconstruction();
  } catch (error) {
    console.warn('Carotid reconstruction unavailable.', error);
    $('reconstruction').hidden = true;
    $('reconstructionStatus').textContent = '3D reconstruction unavailable.';
  }
}

boot().catch((error) => {
  $('loading').hidden = false;
  $('loading').textContent = 'This exam is unavailable.';
  console.warn('Carotid exam unavailable.', error);
});
