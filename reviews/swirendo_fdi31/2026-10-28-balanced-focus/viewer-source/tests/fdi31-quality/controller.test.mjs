// Renderless controller checks, NOT browser/WebGL evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
import {setImmediate} from 'node:timers/promises';
import * as THREE from '../../dist/review/uff-tomo1b/payload/viewer/vendor/three.module.js';
import * as contract from '../../dist/fdi31/model-contract.mjs';
import * as views from '../../dist/fdi31/view-state.mjs';

const source = await readFile(new URL('../../dist/fdi31/viewer.mjs', import.meta.url), 'utf8');
class Element {
  constructor(dataset = {}) { this.dataset = dataset; this.handlers = new Map(); this.attributes = new Map(); this.children = []; this.clientWidth = 740; this.clientHeight = 510; }
  addEventListener(name, callback) { this.handlers.set(name, callback); }
  emit(name, event = {}) { return this.handlers.get(name)?.(event); }
  setAttribute(name, value) { this.attributes.set(name, value); }
  getAttribute(name) { return this.attributes.get(name); }
  append(child) { this.children.push(child); child.parent = this; }
  remove() { if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this); }
}

async function harness({stallImports = false, stallModel = false, webglFailure = false, deferModels = false, rejectQuality = null} = {}) {
  const elements = new Map(['context-title', 'context-description', 'visible-labels', 'viewport', 'language', 'status', 'integrity', 'layer-controls', 'load', 'retry', 'placeholder', 'restore', 'quality', 'quality-note', 'download-size', 'model-metrics', 'model-hash', 'model-download'].map(id => ['#' + id, new Element()]));
  const buttons = Object.keys(views.MODES).map(mode => new Element({mode}));
  const window = new Element();
  const document = {documentElement: {}, querySelector: selector => elements.get(selector), querySelectorAll: selector => selector === '[data-mode]' ? buttons : []};
  const timers = new Map(); let timerID = 0;
  const state = {renderers: [], cameras: [], signals: [], qualities: [], requests: [], parseCount: 0, rejectQuality, timers, window, elements, buttons, document};
  const store = new Map();
  const context = vm.createContext({
    document, window, location: {origin: 'http://localhost:8000'}, devicePixelRatio: 1,
    localStorage: {getItem: key => store.get(key), setItem: (key, value) => store.set(key, value)},
    AbortController, ResizeObserver: class {observe() {} disconnect() {}},
    setTimeout: callback => { timers.set(++timerID, callback); return timerID; },
    clearTimeout: id => timers.delete(id),
  });
  class Renderer {
    constructor() { if (webglFailure) throw new Error('Synthetic unavailable WebGL'); this.domElement = new Element(); state.renderers.push(this); }
    setPixelRatio() {} setSize() {} dispose() { this.disposed = true; }
    render(scene, camera) { state.scene = scene; state.cameras.push(camera); }
  }
  class Controls {
    constructor(camera) { this.target = new THREE.Vector3(); state.controls = this; state.camera = camera; }
    update() {} addEventListener() {} dispose() { this.disposed = true; }
  }
  class Loader {
    async parseAsync() {
      state.parseCount++;
      const scene = new THREE.Group(); const associations = new Map(); const nodes = [];
      for (const key of contract.LAYERS) {
        const object = new THREE.Mesh(new THREE.BoxGeometry(.01, .01, .02), new THREE.MeshStandardMaterial());
        object.name = 'synthetic_' + key;
        scene.add(object); associations.set(object, {nodes: nodes.length}); nodes.push({name: `SWIRendo_31_T2/${key}`});
      }
      state.asset = {scene, parser: {associations, json: {nodes}}};
      return state.asset;
    }
  }
  async function modelLoader(origin, signal, quality) {
    state.signals.push(signal);
    state.qualities.push(quality);
    if (quality === state.rejectQuality) throw new Error('Exact model SHA-256 mismatch');
    if (deferModels) return new Promise(resolve => state.requests.push({quality, signal, resolve}));
    if (stallModel) return new Promise((resolve, reject) => signal.addEventListener('abort', () => reject(new Error('Synthetic abort'))));
    return new Uint8Array(16);
  }
  const modules = new Map();
  async function synthetic(name, exports) {
    if (!modules.has(name)) {
      const module = new vm.SyntheticModule(Object.keys(exports), function () { for (const [key, value] of Object.entries(exports)) this.setExport(key, value); }, {context});
      await module.link(() => {}); await module.evaluate(); modules.set(name, module);
    }
    return modules.get(name);
  }
  const module = new vm.SourceTextModule(source, {context, importModuleDynamically: async specifier => {
    if (stallImports) return new Promise(() => {});
    if (specifier === 'three') return synthetic('three', {...THREE, WebGLRenderer: Renderer});
    if (specifier.endsWith('GLTFLoader.js')) return synthetic('loader', {GLTFLoader: Loader});
    if (specifier.endsWith('OrbitControls.js')) return synthetic('controls', {OrbitControls: Controls});
    throw new Error('Unexpected dynamic import');
  }});
  await module.link(specifier => synthetic(specifier, specifier.includes('model-contract') ? {...contract, loadExactModel: modelLoader} : views));
  await module.evaluate();
  state.get = id => elements.get('#' + id);
  state.clickMode = mode => buttons.find(button => button.dataset.mode === mode).emit('click');
  state.selectQuality = quality => { state.get('quality').value = quality; return state.get('quality').emit('change'); };
  state.visible = () => Object.entries(contract.bindLayers(state.asset)).filter(([, node]) => node.visible).map(([key]) => key);
  return state;
}

test('controller keeps camera on isolation, repeats safely, switches language and fully restores', async () => {
  const ui = await harness();
  assert.equal(ui.get('layer-controls').disabled, true);
  await ui.get('load').emit('click');
  assert.equal(ui.get('status').dataset.phase, 'ready');
  const position = ui.camera.position.toArray();
  for (const mode of Object.keys(views.MODES)) {
    ui.clickMode(mode); ui.clickMode(mode);
    assert.deepEqual(ui.visible(), [...views.MODES[mode]]);
    assert.deepEqual(ui.camera.position.toArray(), position);
  }
  ui.clickMode('pulp'); ui.get('language').emit('click');
  assert.equal(ui.document.documentElement.lang, 'zh');
  assert.equal(ui.get('context-title').textContent, '牙髓空间标签 · 单独显示');
  assert.deepEqual(ui.visible(), ['pulp']);
  assert.equal(ui.buttons.find(button => button.dataset.mode === 'pulp').getAttribute('aria-pressed'), 'true');
  ui.camera.position.set(2, 3, 4); ui.camera.zoom = 4;
  ui.get('restore').emit('click');
  assert.deepEqual(ui.visible(), contract.LAYERS);
  assert.deepEqual(ui.camera.position.toArray(), position);
  assert.equal(ui.camera.zoom, 1);
  assert.equal(ui.get('context-title').textContent, '完整标本 · 4 个来源标签');
});

test('WebGL failure exposes retry with controls disabled, without model transfer', async () => {
  const ui = await harness({webglFailure: true});
  await ui.get('load').emit('click');
  assert.equal(ui.get('status').dataset.phase, 'failed');
  assert.equal(ui.get('retry').hidden, false);
  assert.equal(ui.get('layer-controls').disabled, true);
  assert.equal(ui.signals.length, 0);
  ui.clickMode('pulp');
  assert.equal(ui.get('viewport').dataset.mode, 'all');
});

test('context loss while fetch is pending aborts the attempt and never reports ready', async () => {
  const ui = await harness({stallModel: true});
  const loading = ui.get('load').emit('click');
  await setImmediate();
  assert.equal(ui.get('status').dataset.phase, 'loading');
  ui.renderers[0].domElement.emit('webglcontextlost', {preventDefault() {}});
  await loading;
  assert.equal(ui.get('status').dataset.phase, 'lost');
  assert.equal(ui.signals[0].aborted, true);
  assert.equal(ui.renderers[0].disposed, true);
  assert.equal(ui.get('retry').hidden, false);
  assert.equal(ui.get('layer-controls').disabled, true);
});

test('watchdog exits stalled imports and exposes retry instead of permanent loading', async () => {
  const ui = await harness({stallImports: true});
  ui.get('load').emit('click');
  const watchdog = [...ui.timers.values()][0];
  watchdog();
  assert.equal(ui.get('status').dataset.phase, 'failed');
  assert.equal(ui.get('retry').hidden, false);
  assert.equal(ui.get('layer-controls').disabled, true);
});

test('Back/Forward disposal clears timers, returns idle, and old watchdog cannot abort new loading', async () => {
  const ui = await harness({stallModel: true});
  const oldLoading = ui.get('load').emit('click'); await setImmediate();
  const staleWatchdog = [...ui.timers.values()][0];
  ui.window.emit('pagehide'); await oldLoading;
  assert.equal(ui.timers.size, 0);
  ui.window.emit('pageshow', {persisted: true});
  assert.equal(ui.get('status').dataset.phase, 'idle');
  assert.equal(ui.get('layer-controls').disabled, true);
  const newLoading = ui.get('load').emit('click'); await setImmediate();
  staleWatchdog();
  assert.equal(ui.get('status').dataset.phase, 'loading');
  assert.equal(ui.signals[1].aborted, false);
  ui.window.emit('pagehide'); await newLoading;
});

test('Balanced is default; changing the unopened quality does not load either model', async () => {
  const ui = await harness();
  assert.equal(ui.get('quality').value, 'balanced');
  assert.equal(ui.get('model-hash').textContent, contract.MODELS.balanced.sha256);
  assert.match(ui.get('quality-note').textContent, /105,370.*0.89 MB/);
  await ui.selectQuality('detailed');
  assert.deepEqual(ui.qualities, []);
  assert.equal(ui.renderers.length, 0);
  assert.equal(ui.get('status').dataset.phase, 'idle');
  assert.match(ui.get('quality-note').textContent, /1,328,980.*7.65 MB/);
  await ui.get('load').emit('click');
  assert.deepEqual(ui.qualities, ['detailed']);
  assert.equal(ui.get('status').dataset.sha256, contract.MODELS.detailed.sha256);
});

test('quality switch preserves isolated layer and camera; restore keeps quality but resets all layers/view', async () => {
  const ui = await harness();
  await ui.get('load').emit('click');
  const defaultPosition = ui.camera.position.toArray();
  ui.clickMode('pulp');
  ui.camera.position.set(.02, -.03, .04); ui.camera.zoom = 3;
  ui.controls.target.set(.001, .002, .003);
  const position = ui.camera.position.toArray(), target = ui.controls.target.toArray();
  await ui.selectQuality('detailed');
  assert.deepEqual(ui.qualities, ['balanced', 'detailed']);
  assert.deepEqual(ui.visible(), ['pulp']);
  assert.deepEqual(ui.camera.position.toArray(), position);
  assert.deepEqual(ui.controls.target.toArray(), target);
  assert.equal(ui.camera.zoom, 3);
  assert.equal(ui.get('status').dataset.quality, 'detailed');
  await ui.selectQuality('detailed');
  assert.equal(ui.qualities.length, 2);
  ui.get('language').emit('click');
  assert.equal(ui.get('quality').value, 'detailed');
  assert.match(ui.get('quality-note').textContent, /详细候选/);
  ui.get('restore').emit('click');
  assert.deepEqual(ui.visible(), contract.LAYERS);
  assert.deepEqual(ui.camera.position.toArray(), defaultPosition);
  assert.equal(ui.camera.zoom, 1);
  assert.equal(ui.get('quality').value, 'detailed');
});

test('hash failure during a switch never labels old geometry as new; retry preserves selection/view', async () => {
  const ui = await harness({rejectQuality: 'detailed'});
  await ui.get('load').emit('click');
  ui.clickMode('dentin'); ui.camera.zoom = 2;
  await ui.selectQuality('detailed');
  assert.equal(ui.get('status').dataset.phase, 'failed');
  assert.equal(ui.get('status').dataset.sha256, undefined);
  assert.equal(ui.get('layer-controls').disabled, true);
  assert.equal(ui.get('viewport').children.length, 0);
  assert.equal(ui.get('viewport').dataset.mode, 'dentin');
  assert.equal(ui.get('quality').value, 'detailed');
  ui.rejectQuality = null;
  await ui.get('retry').emit('click');
  assert.deepEqual(ui.visible(), ['dentin']);
  assert.equal(ui.camera.zoom, 2);
  assert.equal(ui.get('status').dataset.sha256, contract.MODELS.detailed.sha256);
});

test('rapid quality switch aborts old loading; a late old result cannot replace the selected model', async () => {
  const ui = await harness({deferModels: true});
  const oldLoading = ui.get('load').emit('click'); await setImmediate();
  const nextLoading = ui.selectQuality('detailed'); await setImmediate();
  assert.equal(ui.requests[0].signal.aborted, true);
  ui.requests[0].resolve(new Uint8Array(16)); await oldLoading;
  assert.equal(ui.get('status').dataset.phase, 'loading');
  assert.equal(ui.parseCount, 0);
  ui.requests[1].resolve(new Uint8Array(16)); await nextLoading;
  assert.equal(ui.parseCount, 1);
  assert.equal(ui.get('status').dataset.quality, 'detailed');
  assert.equal(ui.get('status').dataset.sha256, contract.MODELS.detailed.sha256);
});

test('quality selection after unavailable WebGL updates information without another render or download attempt', async () => {
  const ui = await harness({webglFailure: true});
  await ui.get('load').emit('click');
  await ui.selectQuality('detailed');
  assert.equal(ui.get('status').dataset.phase, 'failed');
  assert.equal(ui.get('quality').value, 'detailed');
  assert.deepEqual(ui.qualities, []);
  assert.equal(ui.get('layer-controls').disabled, true);
});
