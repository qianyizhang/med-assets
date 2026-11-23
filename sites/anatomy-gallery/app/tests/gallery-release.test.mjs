import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { createGalleryDelivery } from '../src/content/shared/release-delivery.js';
import { compileResources } from '../src/content/shared/release-resources.js';

const expected = Buffer.from('exact fixture bytes');
const sha256 = createHash('sha256').update(expected).digest('hex');
const make = (path, mediaType) => ({ path, mediaType, sha256, bytes: expected.length });
const model = make('models/current.glb', 'model/gltf-binary');
const evidence = { ...make('reviews/witness.webp', 'image/webp'), url: '/review-evidence/' + sha256 + '/witness.webp' };
const receipt = make('reviews/receipt.json', 'application/json');
const archive = make('experiments/film.mp4', 'video/mp4');
const older = { ...make('models/older.glb', 'model/gltf-binary'), name: 'older.glb' };
const publicIndex = { assets: [older] };
const inputs = { publicIndex, localDelivery: { assets: [model], receipts: [receipt] },
  legacyDental: { assets: [] }, archive: [archive], reviews: { campaign: [{ sources: [], views: [evidence] }] } };

test('a selected release combines pin-verified reads while leaving public listing and write admission independent', async () => {
  const resources = compileResources({ selection: 'candidate', ...inputs });
  const studies = { version: 1, lessons: [{ id: 'fixture' }] };
  const handle = createGalleryDelivery(publicIndex, () => true, { resources, studies });
  const instances = resources.filter(resource => !resource.localOnly);
  assert.equal(instances.length, 3);
  let available = false;
  const bucket = {
    head: async () => available && { size: expected.length, customMetadata: { sha256 } },
    get: async (key, options) => ({ body: options?.range
      ? expected.subarray(options.range.offset, options.range.offset + options.range.length) : expected }),
    put: () => assert.fail('Selected release granted a write'),
  };
  const request = (path, options) => new Request('https://fixture.test' + path, options);
  const fetch = (path, options, env = { BUCKET: bucket }) => handle(request(path, options), env);
  for (const entry of instances) {
    assert.equal((await fetch(entry.url)).status, 503);
    available = true;
    assert.deepEqual(Buffer.from(await (await fetch(entry.url)).arrayBuffer()), expected);
    const head = await fetch(entry.url, { method: 'HEAD' });
    assert.equal(head.headers.get('content-length'), String(expected.length));
    assert.equal(await head.text(), '');
    const range = await fetch(entry.url, { headers: { range: 'bytes=0-3' } });
    assert.equal(range.status, 206);
    assert.deepEqual(Buffer.from(await range.arrayBuffer()), expected.subarray(0, 4));
    assert.equal((await fetch(entry.url, { method: 'PUT' })).status, 405);
    available = false;
  }
  const film = resources.find(resource => resource.localOnly);
  available = true;
  assert.equal((await fetch(film.url)).status, 503);
  assert.equal((await fetch(film.url, undefined, { LOCAL_GALLERY_FILES: bucket })).status, 200);
  assert.equal((await fetch('/assets/' + sha256 + '/excluded.glb')).status, 404);
  assert.deepEqual(await (await fetch('/assets/index.json')).json(), publicIndex);
  assert.deepEqual(await (await fetch('/api/gallery/v1/studies')).json(), studies);
  assert.deepEqual(compileResources({ selection: 'published', ...inputs }), []);
  assert.throws(() => compileResources({ selection: 'candidate', ...inputs,
    localDelivery: { assets: [model], receipts: [{ ...receipt, bytes: undefined }] } }), /verified identity/);
});
