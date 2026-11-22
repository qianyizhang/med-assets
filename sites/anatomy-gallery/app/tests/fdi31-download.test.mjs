import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { fetchBalancedGlb, findBalancedExport } from '../src/content/shared/fdi31-download.js';

const payload = Buffer.from('example GLB bytes');
const file = {
  path: 'models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb',
  name: 'FDI31-balanced.glb',
  mediaType: 'model/gltf-binary',
  bytes: payload.length,
  sha256: createHash('sha256').update(payload).digest('hex'),
};
const route = `/assets/${file.sha256}/${file.name}`;

test('only the prepared Balanced variant is selected and its exact public bytes are downloaded', async t => {
  const differentExport = { ...file, path: 'models/swirendo_fdi31/Detailed.glb' };
  assert.equal(findBalancedExport([differentExport]), undefined);
  assert.equal(findBalancedExport([differentExport, file]), file);
  const calls = [];
  const { signal } = new AbortController();
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(options.redirect, 'error');
    assert.equal(options.signal, signal);
    calls.push(url);
    if (url === '/assets/index.json') return Response.json({ assets: [differentExport, file] });
    return new Response(payload, { headers: { 'content-type': file.mediaType } });
  });
  const { blob, name } = await fetchBalancedGlb(file, signal);
  assert.deepEqual(calls, ['/assets/index.json', route]);
  assert.deepEqual(Buffer.from(await blob.arrayBuffer()), payload);
  assert.equal(name, file.name);
});

test('missing or stale manifest entries are rejected before the binary request', async t => {
  for (const assets of [[], [{ ...file, bytes: file.bytes + 1 }]]) {
    const fetchMock = t.mock.method(globalThis, 'fetch', async () => Response.json({ assets }));
    try {
      await assert.rejects(fetchBalancedGlb(file), /no matching public delivery entry/);
      assert.equal(fetchMock.mock.callCount(), 1);
    } finally {
      fetchMock.mock.restore();
    }
  }
});

test('an unavailable or corrupted asset does not download and a retry requests fresh bytes', async t => {
  let reply = new Response(null, { status: 503 });
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    if (url === '/assets/index.json') return Response.json({ assets: [file] });
    assert.equal(url, route);
    assert.equal(options.cache, 'reload');
    return reply;
  });
  await assert.rejects(fetchBalancedGlb(file), /GLB unavailable/);
  reply = new Response(Buffer.alloc(file.bytes), { headers: { 'content-type': file.mediaType } });
  await assert.rejects(fetchBalancedGlb(file), /integrity check/);
  reply = new Response(payload, { headers: { 'content-type': file.mediaType } });
  assert.equal((await fetchBalancedGlb(file)).blob.size, file.bytes);
});
