import {CARDIAC_VIEWS} from './heart-poses.js';
import {contactNotes, readings, viewOrder} from './reading.js';
import {createReferences} from './references.js';

const el = id => document.getElementById(id);
const state = { phase: 0, tilt: 0, overlay: false, yaw: 43, pitch: -14, viewId: 'a4c' };
const home = { yaw: state.yaw, pitch: state.pitch };
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
let view, torso, workbench, motionAt;
let mode = 'pose';
const torsoOrbit = {yaw: 12, pitch: 0};
const torsoDisplay = {close: false, reveal: true};
const references = createReferences();
let playing = false;
let lastTime = null;
let request = 0;

const cycleMs = 980;

const flowByStage = {
  'isovolumetric-contraction': 'Inlet and outlet valves are closed as ventricular pressure rises.',
  ejection: 'Blood leaves the ventricles through the aortic and pulmonary valves.',
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

function draw() {
  const frame = view?.render(state);
  if (mode === 'pose') torso?.render({...state, ...torsoOrbit, ...torsoDisplay, frame});
  references.draw(state.phase);
  workbench?.update(state);
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

function setMode(next) {
  mode = next;
  for (const [key,panel] of [['pose','torso-view'],['model','orbit-view'],['cine','reference-view']]) {
    el(key).setAttribute('aria-pressed', key === mode);
    el(panel).hidden = key !== mode;
  }
  el('orbit-help').hidden = mode === 'cine';
  el('torso-tools').hidden = el('pose-note').hidden = mode !== 'pose';
  el('ref-help').hidden = mode !== 'cine';
  references.show(state.viewId, mode === 'cine');
  draw();
}

function setWindow(id, remember) {
  state.viewId = Object.hasOwn(CARDIAC_VIEWS, id) ? id : 'a4c';
  const spec = CARDIAC_VIEWS[state.viewId];
  el('window').value = state.viewId;
  state.tilt = 0;
  el('tilt').value = 0;
  el('section').setAttribute('aria-label', 'Simulated B-mode · ' + spec.label);
  el('read-view').textContent = readings[state.viewId];
  el('pose-note').textContent = contactNotes[spec.group];
  document.title = spec.label + ' · Adult echocardiography';
  const idx = viewOrder.indexOf(state.viewId);
  el('view-number').textContent = (idx+1) + ' / ' + viewOrder.length;
  el('previous').disabled = idx === 0;
  el('next').disabled = idx === viewOrder.length - 1;
  if (remember) {
    const url = new URL(location.href);
    url.searchParams.set('view', state.viewId);
    history.pushState(null, '', url);
  }
  setMode(mode);
}
for (const [id, key] of [['close-pose', 'close'], ['chest', 'reveal']]) {
  el(id).onclick = () => {
    torsoDisplay[key] = !torsoDisplay[key];
    el(id).setAttribute('aria-pressed', torsoDisplay[key]);
    draw();
  };
}
const options = new Map();
for (const id of viewOrder) {
  const {label,group} = CARDIAC_VIEWS[id];
  if (!options.has(group)) {
    const node = document.createElement('optgroup');
    node.label = group;
    options.set(group, node);
    el('window').append(node);
  }
  options.get(group).append(new Option(label, id));
}
el('window').onchange = e => setWindow(e.target.value, true);
el('previous').onclick = () => setWindow(viewOrder[viewOrder.indexOf(state.viewId)-1], true);
el('next').onclick = () => setWindow(viewOrder[viewOrder.indexOf(state.viewId)+1], true);
window.addEventListener('popstate', () => setWindow(new URL(location.href).searchParams.get('view'), false));
for (const id of ['pose','model','cine']) el(id).onclick = () => setMode(id);

function bindOrbit(canvas, angles, initial) {
  function orbit(dx,dy) {
    angles.yaw = (angles.yaw + dx) % 360;
    angles.pitch = Math.max(-85, Math.min(85, angles.pitch + dy));
    draw();
  }
  let drag;
  canvas.onpointerdown = e => {
    if (!e.isPrimary || e.button !== 0) return;
    canvas.setPointerCapture(e.pointerId);
    drag = [e.clientX, e.clientY];
  };
  canvas.onpointermove = e => {
    if (!drag || !canvas.hasPointerCapture(e.pointerId)) return;
    orbit((e.clientX-drag[0])*.55, (e.clientY-drag[1])*.4);
    drag = [e.clientX,e.clientY];
  };
  canvas.onlostpointercapture = () => { drag = null; };
  canvas.onkeydown = e => {
    const steps = {ArrowLeft:[-8,0],ArrowRight:[8,0],ArrowUp:[0,-8],ArrowDown:[0,8]};
    if (e.key === 'Home') { Object.assign(angles,initial); draw(); }
    else if (steps[e.key]) orbit(...steps[e.key]);
    else return;
    e.preventDefault();
  };
}
bindOrbit(el('scene'),state,home);
bindOrbit(el('torso'),torsoOrbit,{...torsoOrbit});
setWindow(new URL(location.href).searchParams.get('view'),false);

document.addEventListener('visibilitychange', () => {
  if (document.hidden) playback(false);
});
reduceMotion.addEventListener('change', e => { if (e.matches) playback(false); });
async function start() {

  el('study').replaceChildren();
  configureStudyPicker(el('study'), typeof abdomenTours === 'undefined' ? [] : abdomenTours,
    'cardiac-a4c', new URL('../', location.href));
  import('./torso/torso-view.js').then(async ({createTorsoView}) => {
    torso = await createTorsoView(el('torso'));
    el('torso-status').hidden = true;
    draw();
  }).catch(() => { el('torso-status').textContent = 'Torso unavailable. Heart section and acquired examples remain available.'; });
  const [{createHeartView}, {cardiacMotion}] = await Promise.all([
    import('./heart-view.js'), import('./heart-geometry.js'),
  ]);
  motionAt = cardiacMotion;
  view = createHeartView({scene: el('scene'), section: el('section')});
  import('./measure/workbench.js').then(({createMeasureWorkbench}) => {
    workbench = createMeasureWorkbench({root: el('measureWorkbench'), section: el('section'), getState: () => state, onSeek: p => seek(p*1000)});
    workbench.update(state);
  }).catch(() => { el('measureWorkbench').textContent = 'Measurement exercises unavailable.'; });
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
