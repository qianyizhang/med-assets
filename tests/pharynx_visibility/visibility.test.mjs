import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createInspection, mountInspection, SOURCE_SHA256} from '../../gallery/pharynx_larynx/visibility-r01/pharynx-inspection.mjs';

const deps = process.env.PHARYNX_TEST_DEPS;
assert.ok(deps, 'Set PHARYNX_TEST_DEPS to the isolated directory containing pinned three and jsdom packages');
const require = createRequire(pathToFileURL(resolve(deps, 'package.json')));
const {JSDOM} = require('jsdom');
const {GLTFLoader} = await import(pathToFileURL(require.resolve('three/examples/jsm/loaders/GLTFLoader.js')));
const record = JSON.parse(readFileSync(new URL('./fixtures/record-excerpt.json', import.meta.url)));
const raw = readFileSync(new URL('../../models/pharynx_larynx/exports/r03/pharynx_larynx.glb', import.meta.url));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
assert.equal(raw.length, 5050088);
assert.equal(sha(raw), SOURCE_SHA256, 'Hydrate the exact existing GLB; pointers are not payloads');
const {scene: imported} = await new GLTFLoader().parseAsync(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength), '');
const meshes = scene => {const rows = []; scene.traverse(o => {if (o.isMesh) rows.push(o);}); return rows;};
const visible = scene => meshes(scene).filter(o => o.visible).map(o => o.userData.source_file_id).sort();
const visibility = scene => {const result = []; scene.traverse(o => result.push(o.visible)); return result;};
const renderIdentity = scene => meshes(scene).map(o => ({
  name: o.name, extras: JSON.stringify(o.userData),
  matrix: o.matrix.toArray(), world: o.matrixWorld.toArray(), position: o.position.toArray(),
  rotation: o.quaternion.toArray(), scale: o.scale.toArray(),
  geometry: Object.fromEntries(Object.entries(o.geometry.attributes).map(([key, attribute]) => [key, sha(Buffer.from(attribute.array.buffer))])),
  indices: sha(Buffer.from(o.geometry.index.array.buffer)), material: JSON.stringify(o.material.toJSON()),
}));
const copy = () => imported.clone(true);

test('actual r03 GLB selects five cartilages, 30 context parts, and restores all 33 without other render changes', () => {
  const scene = copy(), before = renderIdentity(scene), original = visibility(scene), controller = createInspection(record, scene);
  const cartilage = ['FJ2769', 'FJ2770', 'FJ2775', 'FJ2792', 'FJ2808'];
  const excludedSupport = ['FJ2749', 'FJ2771', 'FJ2807'];
  controller.select('cartilage');
  assert.deepEqual(visible(scene), cartilage);
  controller.select('muscles');
  assert.equal(visible(scene).length, 30);
  assert.ok(excludedSupport.every(id => !visible(scene).includes(id)));
  assert.ok(cartilage.every(id => visible(scene).includes(id)));
  controller.select('cartilage');
  controller.select('all');
  assert.deepEqual(visibility(scene), original);
  assert.deepEqual(renderIdentity(scene), before);
});

test('reset restores original hidden states, including parent visibility', () => {
  const scene = copy(), hidden = meshes(scene).find(o => o.userData.source_file_id === 'FJ2770');
  hidden.visible = false;
  const original = visibility(scene), controller = createInspection(record, scene);
  controller.select('cartilage');
  assert.equal(controller.items().filter(item => item.visible).length, 4);
  scene.visible = false;
  controller.select('all');
  assert.deepEqual(visibility(scene), original);
});

test('unrelated candidates receive no controller or DOM changes', () => {
  const scene = copy(), original = visibility(scene), other = {...record, id: 'other__r01'};
  assert.equal(createInspection(other, scene), null);
  const dom = new JSDOM('<head></head><body><div id="viewport"></div></body>');
  assert.equal(mountInspection(other, scene, dom.window.document.querySelector('#viewport')), null);
  assert.equal(dom.window.document.querySelector('.pharynx-inspection'), null);
  assert.deepEqual(visibility(scene), original);
});

test('wrong source hash, disputed-label omissions and conflicting visibility contracts fail before mutation', () => {
  for (const changed of [
    {...record, source: {...record.source, sha256: '0'.repeat(64)}},
    {...record, displayLabelOverrides: {}},
    {...record, cameraContract: {sourceViews: true}},
  ]) {
    const scene = copy(), original = visibility(scene);
    assert.throws(() => createInspection(changed, scene));
    assert.deepEqual(visibility(scene), original);
  }
});

test('missing, duplicate, unexpected and nameless source meshes fail before mutation', () => {
  for (const change of [
    scene => scene.remove(meshes(scene)[0]),
    scene => {meshes(scene)[1].userData.source_file_id = meshes(scene)[0].userData.source_file_id;},
    scene => {meshes(scene)[0].userData.source_file_id = 'unknown';},
    scene => {delete meshes(scene)[0].userData.source_name;},
  ]) {
    const scene = copy(); change(scene); const original = visibility(scene);
    assert.throws(() => createInspection(record, scene));
    assert.deepEqual(visibility(scene), original);
  }
});

test('invalid mode leaves the current scene and selected mode unchanged', () => {
  const scene = copy(), controller = createInspection(record, scene);
  controller.select('cartilage'); const original = visibility(scene);
  assert.throws(() => controller.select('arbitrary'));
  assert.equal(controller.mode, 'cartilage');
  assert.deepEqual(visibility(scene), original);
});

test('real module DOM handlers change visibility, expose selected state, retain neutral labels and survive language repaint', () => {
  const scene = copy(), dom = new JSDOM('<head></head><body><div id="viewport"></div></body>');
  const doc = dom.window.document, ui = mountInspection(record, scene, doc.querySelector('#viewport'));
  const button = mode => doc.querySelector(`[data-layer="${mode}"]`);
  assert.equal(button('all').getAttribute('aria-pressed'), 'true');
  button('cartilage').click();
  assert.equal(visible(scene).length, 5);
  assert.match(doc.querySelector('[role="status"]').textContent, /5 \/ 33/);
  ui.paint('zh');
  assert.equal(button('cartilage').textContent, '软骨');
  assert.equal(button('cartilage').getAttribute('aria-pressed'), 'true');
  button('muscles').click();
  assert.equal(visible(scene).length, 30);
  for (const [id, label] of Object.entries(record.displayLabelOverrides)) {
    assert.ok([...doc.querySelectorAll('li')].some(li => li.textContent === `${id} · ${label}`));
  }
  button('all').click(); ui.paint('en');
  assert.equal(visible(scene).length, 33);
  assert.equal(button('all').getAttribute('aria-pressed'), 'true');
  assert.match(doc.querySelector('[role="status"]').textContent, /Original source visibility restored/);
  assert.match(doc.querySelector('.pharynx-inspection').textContent, /source epiglottic openings are retained/);
});
