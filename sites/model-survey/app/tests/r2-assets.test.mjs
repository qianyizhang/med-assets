import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createAssetDelivery } from '../src/content/shared/r2-assets.js';

const data = Buffer.from('glTF-public-model');
const hash = createHash('sha256').update(data).digest('hex');
const manifest = { assets: [{ name: 'model.glb', sha256: hash, bytes: data.length, mediaType: 'model/gltf-binary' }] };
const url = `https://trial.test/assets/${hash}/model.glb`;
function fixture() {
  const objects = new Map();
  const calls = [];
  const env = { BUCKET: {
    async head(key) { return objects.get(key) ?? null; },
    async put(key, body, options) {
      calls.push(options);
      const bytes = Buffer.from(await new Response(body).arrayBuffer());
      if (createHash('sha256').update(bytes).digest('hex') !== options.sha256) throw Error('R2 checksum mismatch');
      const object = { size: bytes.length, customMetadata: options.customMetadata, bytes };
      objects.set(key, object); return object;
    },
    async get(key, options) {
      const object = objects.get(key);
      if (!object) return null;
      const range = options?.range;
      const bytes = range ? object.bytes.subarray(range.offset, range.offset + range.length) : object.bytes;
      return { ...object, body: new Response(bytes).body };
    },
  } };
  const serve = createAssetDelivery(manifest, async request => request.headers.get('test-owner') === 'yes');
  const upload = (bytes = data) => serve(new Request(url, { method: 'PUT', headers: {
    'test-owner': 'yes', 'content-length': String(data.length),
  }, body: bytes }), env);
  return { env, serve, upload, calls, objects };
}

test('owner upload, anonymous full/HEAD/ranged reads, immutable caching and idempotency', async () => {
  const f = fixture();
  assert.equal((await f.upload()).status, 200);
  const response = await f.serve(new Request(url), f.env);
  assert.equal(response.status, 200);
  assert.deepEqual(Buffer.from(await response.arrayBuffer()), data);
  assert.equal(response.headers.get('access-control-allow-origin'), '*');
  assert.match(response.headers.get('cache-control'), /immutable/);
  assert.equal((await f.serve(new Request(url, { method: 'HEAD' }), f.env)).body, null);
  const part = await f.serve(new Request(url, { headers: { range: 'bytes=2-5' } }), f.env);
  assert.equal(part.status, 206);
  assert.equal(part.headers.get('content-range'), `bytes 2-5/${data.length}`);
  assert.deepEqual(Buffer.from(await part.arrayBuffer()), data.subarray(2, 6));
  assert.equal((await f.upload()).status, 200);
  assert.equal(f.calls.length, 1);
  assert.equal(f.calls[0].sha256, hash);
  assert.deepEqual(f.calls[0].onlyIf, { etagDoesNotMatch: '*' });
  assert.equal((await f.serve(new Request(url, { headers: { 'if-none-match': `"${hash}"` } }), f.env)).status, 304);
});

test('anonymous writes and cross-origin owner writes are denied without changing storage', async () => {
  const f = fixture();
  assert.equal((await f.serve(new Request(url, { method: 'PUT', body: data }), f.env)).status, 403);
  assert.equal((await f.serve(new Request(url, { method: 'PUT', headers: {
    'test-owner': 'yes', origin: 'https://attacker.test', 'content-length': String(data.length),
  }, body: data }), f.env)).status, 403);
  assert.equal(f.calls.length, 0);
  assert.equal((await f.serve(new Request(url, { method: 'DELETE' }), f.env)).status, 405);
});

test('bad checksum, wrong size, and unsupported encoding cannot publish an object', async () => {
  const f = fixture();
  assert.equal((await f.upload(Buffer.alloc(data.length))).status, 400);
  assert.equal(f.objects.size, 0);
  assert.equal((await f.serve(new Request(url, { method: 'PUT', headers: {
    'test-owner': 'yes', 'content-length': String(data.length), 'content-encoding': 'gzip',
  }, body: data }), f.env)).status, 400);
  assert.equal((await f.serve(new Request(url, { method: 'PUT', headers: {
    'test-owner': 'yes', 'content-length': '1',
  }, body: data }), f.env)).status, 400);
});

test('public reads fail explicitly for missing/corrupt storage and unlisted objects', async () => {
  const f = fixture();
  assert.equal((await f.serve(new Request(url), f.env)).status, 503);
  assert.equal((await f.serve(new Request('https://trial.test/assets/data-app/snapshot/anything'), f.env)).status, 404);
  assert.equal((await f.serve(new Request(url + '?key=private'), f.env)).status, 400);
  assert.equal(await f.serve(new Request('https://trial.test/api/snapshot'), f.env), null);
  await f.upload();
  f.objects.get(`assets/sha256/${hash}`).customMetadata.sha256 = '0'.repeat(64);
  assert.equal((await f.serve(new Request(url), f.env)).status, 503);
  assert.equal((await f.upload()).status, 409);
});

test('invalid ranges fail and expired/wrong tokens cannot write', async () => {
  const f = fixture(); await f.upload();
  for (const range of ['bytes=-4', 'bytes=100-', 'bytes=5-2', 'bytes=0-1,3-4']) {
    assert.equal((await f.serve(new Request(url, { headers: { range } }), f.env)).status, 416);
  }
  const token = 'random-trial-token';
  f.env.ASSET_UPLOAD_TOKEN_SHA256 = createHash('sha256').update(token).digest('hex');
  f.env.ASSET_UPLOAD_TOKEN_EXPIRES_AT = new Date(Date.now() - 1000).toISOString();
  const request = () => new Request(url, { method: 'PUT', headers: {
    'x-asset-upload-token': token, 'content-length': String(data.length),
  }, body: data });
  assert.equal((await f.serve(request(), f.env)).status, 403);
  f.env.ASSET_UPLOAD_TOKEN_EXPIRES_AT = new Date(Date.now() + 60000).toISOString();
  assert.equal((await f.serve(request(), f.env)).status, 200);
});
