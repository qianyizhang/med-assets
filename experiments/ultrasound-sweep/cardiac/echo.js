const el = id => document.getElementById(id);
const state = { phase: 0, tilt: 0, overlay: false, yaw: 43, pitch: -14 };
const home = { yaw: state.yaw, pitch: state.pitch };
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
let view, reference, atlas, motionAt;
let playing = false;
let lastTime = null;
let request = 0;
let frameShown = -1;
const cycleMs = 980;

const flowByStage = {
  'isovolumetric-contraction': 'Inlet and outlet valves are closed as ventricular pressure rises.',
  ejection: 'Blood leaves the ventricles through the outflow tracts, outside this plane.',
  'isovolumetric-relaxation': 'Inlet and outlet valves are closed as ventricular pressure falls.',
  'early-filling': 'The inlet valves reopen as blood moves from atria to ventricles.',
  diastasis: 'Forward inflow slows as atrial and ventricular pressures approach each other.',
  'atrial-filling': 'The atria deliver the final portion of ventricular filling.',
};

function phaseDescription(p) {
  if (!motionAt) return [Math.round(p * 100) + '%', ''];
  const {stage} = motionAt(p);
  if (p === 0 || p === 1) return ['End diastole', 'Ventricles full. The inlet leaflets have come together.'];
  if (Math.abs(p - .35) < .0001) return ['End systole', 'Ejection has ended. The inlet valves are still closed.'];
  return [stage.label, flowByStage[stage.key]];
}

// Align reader-selected landmarks across cases while preserving all acquired frames in order.
function showReference() {
  if (!atlas || el('reference-view').hidden) return;
  const {landmarks, frameCount, tileWidth, tileHeight, columns} = reference;
  const upper = landmarks.findIndex(([p], i) => i > 0 && p >= state.phase);
  const [p0, f0] = landmarks[upper - 1], [p1, f1] = landmarks[upper];
  const f = Math.round(f0 + (f1 - f0) * (state.phase - p0) / (p1 - p0)) % frameCount;
  if (f === frameShown) return;
  el('reference').getContext('2d').drawImage(atlas, (f % columns) * tileWidth,
    Math.floor(f / columns) * tileHeight, tileWidth, tileHeight, 0, 0, tileWidth, tileHeight);
  frameShown = f;
  el('reference').dataset.frame = f;
}

function draw() {
  view?.render(state);
  showReference();
  const [stage, flow] = phaseDescription(state.phase);
  el('phase').value = Math.round(state.phase * 1000);
  el('phase').setAttribute('aria-valuetext', Math.round(state.phase * 100) + '% · ' + stage);
  el('phase-name').textContent = stage;
  el('flow-note').textContent = flow;
  el('degrees').textContent = state.tilt + '°';
  el('tilt').setAttribute('aria-valuetext', state.tilt + ' degrees');
}

function tick(time) {
  if (!playing) return;
  if (lastTime !== null) state.phase = (state.phase + (time - lastTime) / cycleMs) % 1;
  lastTime = time;
  draw();
  request = requestAnimationFrame(tick);
}
function playback(on) {
  cancelAnimationFrame(request);
  playing = on;
  lastTime = null;
  el('play').textContent = on ? 'Pause beat' : 'Play beat';
  if (on) request = requestAnimationFrame(tick);
}
function seek(value) {
  playback(false);
  state.phase = value / 1000;
  draw();
}

el('play').onclick = () => playback(!playing);
el('phase').oninput = e => seek(Number(e.target.value));
for (const button of el('stops').querySelectorAll('button')) {
  button.onclick = () => seek(Number(button.dataset.phase));
}
el('tilt').oninput = e => { state.tilt = Number(e.target.value); draw(); };
el('reset').onclick = () => { state.tilt = 0; el('tilt').value = 0; draw(); };
el('overlay').onclick = () => {
  state.overlay = !state.overlay;
  el('overlay').setAttribute('aria-pressed', state.overlay);
  draw();
};
el('flow').onchange = () => { el('flow-note').hidden = !el('flow').checked; };

let loading;
async function loadRecord() {
  const response = await fetch('acquisition.json');
  if (!response.ok) throw new Error('Missing acquisition record');
  reference = await response.json();
  const credit = document.createElement('a'), license = document.createElement('a');
  credit.href = reference.url;
  credit.textContent = reference.credit;
  license.href = reference.licenseUrl;
  license.textContent = reference.license;
  el('credit').replaceChildren('Acquired cine. ', credit, '. All 50 frames resized and tiled under ', license, '. Original markings retained.');
}
async function loadReference() {
  if (!reference) await loadRecord();
  const img = new Image();
  img.src = reference.file;
  await img.decode();
  if (img.width !== reference.columns * reference.tileWidth ||
      img.height !== Math.ceil(reference.frameCount / reference.columns) * reference.tileHeight) {
    throw new Error('Unexpected cine dimensions');
  }
  atlas = img;
  el('ref-status').hidden = true;
  showReference();
}
function compare(useCine) {
  el('model').setAttribute('aria-pressed', !useCine);
  el('cine').setAttribute('aria-pressed', useCine);
  el('orbit-view').hidden = el('orbit-help').hidden = useCine;
  el('reference-view').hidden = el('ref-help').hidden = !useCine;
  if (useCine && !atlas && !loading) {
    el('ref-status').hidden = false;
    el('ref-status').textContent = 'Loading acquired cine…';
    loading = loadReference().catch(() => {
      loading = null;
      el('ref-status').textContent = 'Acquired cine unavailable. Reopen this view to retry.';
    });
  }
  draw();
}
el('model').onclick = () => compare(false);
el('cine').onclick = () => compare(true);
const scene = el('scene');
function orbit(dx, dy) {
  state.yaw = (state.yaw + dx) % 360;
  state.pitch = Math.max(-85, Math.min(85, state.pitch + dy));
  draw();
}
let drag;
scene.onpointerdown = e => {
  if (!e.isPrimary || e.button !== 0) return;
  scene.setPointerCapture(e.pointerId);
  drag = [e.clientX, e.clientY];
};
scene.onpointermove = e => {
  if (!drag || !scene.hasPointerCapture(e.pointerId)) return;
  orbit((e.clientX - drag[0]) * .55, (e.clientY - drag[1]) * .4);
  drag = [e.clientX, e.clientY];
};
scene.onlostpointercapture = () => { drag = null; };
scene.onkeydown = e => {
  const steps = {ArrowLeft: [-8, 0], ArrowRight: [8, 0], ArrowUp: [0, -8], ArrowDown: [0, 8]};
  if (e.key === 'Home') { Object.assign(state, home); draw(); }
  else if (steps[e.key]) orbit(...steps[e.key]);
  else return;
  e.preventDefault();
};

document.addEventListener('visibilitychange', () => {
  if (document.hidden) playback(false);
});
reduceMotion.addEventListener('change', e => { if (e.matches) playback(false); });
async function start() {
  loadRecord().catch(() => { el('credit').textContent = 'Acquisition record unavailable.'; });
  el('study').replaceChildren();
  configureStudyPicker(el('study'), typeof abdomenTours === 'undefined' ? [] : abdomenTours,
    'cardiac-a4c', new URL('../', location.href));
  const [{createHeartView}, {cardiacMotion}] = await Promise.all([
    import('./heart-view.js'), import('./heart-geometry.js'),
  ]);
  motionAt = cardiacMotion;
  view = createHeartView({scene, section: el('section')});
  draw();
  el('play').disabled = false;
  playback(!reduceMotion.matches && !document.hidden);
  new ResizeObserver(() => { if (!playing) draw(); }).observe(el('section'));
}
start().catch(() => {
  el('flow').disabled = true;
  el('overlay').disabled = el('tilt').disabled = el('reset').disabled = true;
  el('error').hidden = false;
  el('error').textContent = 'Heart model unavailable. You can still inspect the acquired cine and scrub its cycle.';
});
