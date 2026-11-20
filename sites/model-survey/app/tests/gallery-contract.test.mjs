import test from 'node:test';
import assert from 'node:assert/strict';
import { createAssetDelivery } from '../src/content/shared/r2-assets.js';
import { baseView, readView, stagePath } from '../src/content/gallery/presets.js';
import { studies } from '../src/content/gallery/catalog.js';

test('rubric and study links work without a bucket or write access', async () => {
  const handle = createAssetDelivery({ assets: [] }, () => false);
  const request = (p, method = 'GET') => handle(new Request('https://example.test' + p, { method }), {});
  assert.equal(
    (await request('/rubric')).headers.get('location'),
    'https://example.test/?view=1#/rubric',
  );
  assert.deepEqual(await (await request('/api/gallery/v1/studies')).json(), studies);
  assert.equal(await (await request('/api/gallery/v1/studies', 'HEAD')).text(), '');
  assert.equal((await request('/api/gallery/v1/studies', 'POST')).status, 405);
  assert.equal(await request('/api/snapshot'), null);
});
test('a shared view pins the model, part, appearance and finite camera', () => {
  const v = {
    ...baseView('r04', 'Right adrenal gland'),
    material: 'Neutral',
    light: 0.75,
    camera: { position: [0.1, 0.2, 0.3], target: [0, 0, 0], height: 0.04 },
  };
  const query = stagePath(v).split('?')[1];
  assert.deepEqual(readView(query), v);
  const asQuery = (x) => 'view=' + encodeURIComponent(JSON.stringify(x));
  for (const change of [
    { revision: 'r900' },
    { revision: 'constructor' },
    { sha256: 'bad' },
    { light: -1 },
    { version: 'v2' },
    { part: 'absent' },
    { camera: { position: [1, 2, 3], target: [1, 2, 3], height: 1 } },
    { camera: { position: [1, 2, 3], target: [0, 0, 0], height: -1 } },
  ]) {
    assert.equal(readView(asQuery({ ...v, ...change })), null);
  }
  assert.equal(readView('view=bad'), null);
  assert.equal(readView('view=' + 'x'.repeat(1700)), null);
});
