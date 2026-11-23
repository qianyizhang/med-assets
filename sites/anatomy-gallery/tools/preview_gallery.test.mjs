import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { once } from 'node:events';
import { cp, mkdir, mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { brotliCompressSync } from 'node:zlib';
import delivery from '../app/src/content/assets/delivery-index.json' with { type: 'json' };
import { compileResources } from '../app/src/content/shared/release-resources.js';
import localDelivery from '../app/src/content/assets/local-delivery.json' with { type: 'json' };

const repo = fileURLToPath(new URL('../../../', import.meta.url));
const site = fileURLToPath(new URL('../', import.meta.url));
const trachea = 'reviews/trachea/2026-10-29-open-airway-r06';

async function withPreview(script, project, check) {
  const server = spawn(process.execPath, [script, project, '0']);
  let stderr = '';
  server.stderr.on('data', (chunk) => { stderr += chunk; });
  try {
    const [message] = await Promise.race([
      once(server.stdout, 'data'),
      once(server, 'close').then(([code]) => { throw Error('Preview exited with ' + code + '\n' + stderr); }),
    ]);
    const origin = new URL(message.toString().trim().replace('Gallery preview: ', '')).origin;
    const rubric = await fetch(origin + '/rubric', { redirect: 'manual' });
    assert.equal(rubric.headers.get('location'), origin + '/#/rubric');
    await check(origin);
  } finally {
    if (server.exitCode === null && server.signalCode === null) {
      const exit = once(server, 'exit');
      server.kill();
      await exit;
    }
  }
}

async function prepareProject(project) {
  const content = path.join(project, 'src/content');
  await cp(path.join(site, 'app/src/content'), content, { recursive: true });
  await writeFile(path.join(project, 'package.json'), JSON.stringify({ type: 'module' }));
}

async function release(project, { archive = [], reviews = {} } = {}) {
  const resources = compileResources({ selection: 'candidate', publicIndex: delivery,
    localDelivery, legacyDental: { assets: [] }, archive, reviews });
  await writeFile(path.join(project, 'src/content/assets/gallery-release.json'),
    JSON.stringify({ selection: 'candidate', resources, studies: {} }));
}

async function fixtureCheckout(t, prefix) {
  const scratch = path.join(repo, '.artifacts');
  await mkdir(scratch, { recursive: true });
  const checkout = await mkdtemp(path.join(scratch, prefix));
  t.after(() => rm(checkout, { recursive: true, force: true }));
  const fixtureSite = path.join(checkout, 'sites/anatomy-gallery');
  await prepareProject(checkout);
  await mkdir(fixtureSite, { recursive: true });
  await cp(path.join(site, 'snapshot-reference.json'), path.join(fixtureSite, 'snapshot-reference.json'));
  for (const name of ['projection-bindings.json', 'restore-projections.mjs']) {
    await cp(path.join(repo, trachea, name), path.join(checkout, trachea, name));
  }
  const script = path.join(fixtureSite, 'tools/preview_gallery.mjs');
  await cp(path.join(site, 'tools/preview_gallery.mjs'), script);
  await mkdir(path.join(checkout, 'dist'));
  await writeFile(path.join(checkout, 'dist/index.html'), 'fixture');
  return { checkout, script };
}

test('a restored film becomes available without restarting or publishing its local route', async (t) => {
  const scratch = path.join(repo, '.artifacts');
  await mkdir(scratch, { recursive: true });
  const project = await mkdtemp(path.join(scratch, 'preview-restore-test-'));
  t.after(() => rm(project, { recursive: true, force: true }));

  await prepareProject(project);
  const bytes = Buffer.from('retained film fixture');
  const sha256 = createHash('sha256').update(bytes).digest('hex');
  const name = 'film.mp4';
  const file = path.join(project, name);
  const inputs = path.join(project, 'src/content/gallery/teaching-inputs');
  await mkdir(inputs, { recursive: true });
  await release(project, { archive: [
    { path: path.relative(repo, file), name, sha256, bytes: bytes.length, mediaType: 'video/mp4' },
  ] });
  await mkdir(path.join(project, 'dist'));
  await writeFile(path.join(project, 'dist/index.html'), 'fixture');

  await withPreview(path.join(site, 'tools/preview_gallery.mjs'), project, async (origin) => {
    const url = origin + '/assets/' + sha256 + '/' + name;
    assert.equal((await fetch(url)).status, 503);
    await writeFile(file, bytes);
    const range = await fetch(url, { headers: { range: 'bytes=0-3' } });
    assert.equal(range.status, 206);
    assert.deepEqual(Buffer.from(await range.arrayBuffer()), bytes.subarray(0, 4));
    await writeFile(file, Buffer.alloc(bytes.length));
    assert.equal((await fetch(url)).status, 503);
    await writeFile(file, bytes);
    assert.deepEqual(Buffer.from(await (await fetch(url)).arrayBuffer()), bytes);
    const index = await (await fetch(origin + '/assets/index.json')).json();
    assert.ok(!index.assets.some((asset) => asset.sha256 === sha256));
  });
});

test('local model delivery rejects missing or corrupt bytes and retains exact routes after recovery', async (t) => {
  const { checkout, script } = await fixtureCheckout(t, 'model-preview-restore-test-');

  await release(checkout);
  await withPreview(script, checkout, async (origin) => {
    for (const { path: reviewPath } of localDelivery.receipts) {
      const receiptUrl = origin + '/' + reviewPath;
      assert.equal((await fetch(receiptUrl)).status, 503);
      const receiptFile = path.join(checkout, reviewPath);
      await mkdir(path.dirname(receiptFile), { recursive: true });
      await writeFile(receiptFile, '{}');
      assert.equal((await fetch(receiptUrl)).status, 503);
      await cp(path.join(repo, reviewPath), receiptFile);
      const receipt = await fetch(receiptUrl);
      assert.equal(receipt.headers.get('content-type'), 'application/json');
      assert.deepEqual(await receipt.json(), JSON.parse(await readFile(receiptFile)));
    }
    const index = await (await fetch(origin + '/assets/index.json')).json();
    for (const asset of localDelivery.assets) {
      const url = origin + `/assets/${asset.sha256}/${asset.name}`;
      assert.equal((await fetch(url)).status, 503);
      const restored = path.join(checkout, asset.path);
      await mkdir(path.dirname(restored), { recursive: true });
      await writeFile(restored, Buffer.alloc(asset.bytes));
      assert.equal((await fetch(url)).status, 503);
      const bytes = await readFile(path.join(repo, asset.path));
      assert.equal(createHash('sha256').update(bytes).digest('hex'), asset.sha256);
      await writeFile(restored, bytes);
      const response = await fetch(url);
      assert.equal(response.status, 200);
      assert.deepEqual(Buffer.from(await response.arrayBuffer()), bytes);
      assert.ok(!index.assets.some((entry) => entry.sha256 === asset.sha256));
    }
  });
});

test('trachea projection routes serve verified SVG bytes from bounded local storage', async (t) => {
  const { checkout, script } = await fixtureCheckout(t, 'projection-preview-test-');
  const projections = delivery.assets.filter(({ path: file }) => file?.startsWith(trachea + '/') && file.endsWith('.svg'));
  assert.equal(projections.length, 2);
  const revision = '503c33f1dadf403faaec373c1a11a8b40dc523d6';

  await release(checkout);
  await withPreview(script, checkout, async (origin) => {
    assert.deepEqual(await (await fetch(origin + '/assets/index.json')).json(), delivery);
    for (const asset of projections) {
      const url = origin + `/assets/${asset.sha256}/${asset.name}`;
      const restored = path.join(checkout, asset.path);
      const packed = restored + '.br';
      const packedSource = path.join(repo, asset.path) + '.br';
      assert.ok(asset.source.includes(revision));
      const original = execFileSync('git', ['--no-lazy-fetch', 'show', revision + ':' + asset.path],
        { cwd: repo, maxBuffer: 10_000_000 });
      assert.equal(original.length, asset.bytes);
      assert.equal(createHash('sha256').update(original).digest('hex'), asset.sha256);

      assert.equal((await fetch(url)).status, 503);
      await symlink(packedSource, packed);
      assert.equal((await fetch(url)).status, 503);
      await rm(packed);
      for (const wrong of [Buffer.from('not Brotli'), Buffer.alloc(1_000_001),
        brotliCompressSync(Buffer.alloc(asset.bytes)), brotliCompressSync(Buffer.alloc(asset.bytes + 1))]) {
        await writeFile(packed, wrong);
        assert.equal((await fetch(url)).status, 503);
      }
      await cp(packedSource, packed);
      const response = await fetch(url);
      assert.equal(response.status, 200);
      assert.equal(response.headers.get('content-type'), 'application/octet-stream');
      assert.equal(response.headers.get('content-disposition'), `attachment; filename="${asset.name}"`);
      assert.equal(response.headers.get('content-encoding'), null);
      assert.deepEqual(Buffer.from(await response.arrayBuffer()), original);

      const head = await fetch(url, { method: 'HEAD' });
      assert.equal(head.status, 200);
      assert.equal(head.headers.get('content-length'), String(asset.bytes));
      assert.equal(head.headers.get('etag'), '"' + asset.sha256 + '"');
      const range = await fetch(url, { headers: { range: 'bytes=20000-20255' } });
      assert.equal(range.status, 206);
      assert.equal(range.headers.get('content-range'), `bytes 20000-20255/${asset.bytes}`);
      assert.deepEqual(Buffer.from(await range.arrayBuffer()), original.subarray(20000, 20256));

      await writeFile(restored, original);
      await writeFile(packed, 'invalid fallback');
      assert.deepEqual(Buffer.from(await (await fetch(url)).arrayBuffer()), original);
      await writeFile(restored, 'invalid direct copy');
      await cp(packedSource, packed);
      assert.deepEqual(Buffer.from(await (await fetch(url)).arrayBuffer()), original);
    }
  });
});

test('refinement downloads use the declared files and retire superseded candidate filenames', async (t) => {
  const { checkout, script } = await fixtureCheckout(t, 'promoted-export-');
  const bytes = Buffer.from('exact reviewed file');
  const sha256 = createHash('sha256').update(bytes).digest('hex');
  const retained = { path: 'models/selected.glb', bytes: bytes.length, sha256 };
  const build = Buffer.from('recipe-only reviewed file');
  const digest = createHash('sha256').update(build).digest('hex');
  const unpromoted = { path: '.artifacts/candidate.glb', name: 'trial.glb', sha256: digest, bytes: build.length, download: true };
  const common = { sources: [], views: [] };
  await release(checkout, { reviews: { campaign: [
    { ...common, refinement: { candidate: { ...retained, name: 'selected.glb', download: true } } },
    { ...common, maintained: {}, export: retained },
    { ...common, refinement: { candidate: unpromoted } },
  ] } });
  await mkdir(path.join(checkout, 'models'));
  await mkdir(path.join(checkout, '.artifacts'));
  await withPreview(script, checkout, async (origin) => {
    const retired = origin + '/assets/' + sha256 + '/earlier-name.glb';
    assert.equal((await fetch(retired)).status, 404);
    for (const [entry, name, expected] of [[retained, 'selected.glb', bytes], [unpromoted, unpromoted.name, build]]) {
      const file = path.join(checkout, entry.path);
      const url = origin + '/assets/' + entry.sha256 + '/' + name;
      assert.equal((await fetch(url)).status, 503);
      await writeFile(file, Buffer.alloc(expected.length));
      assert.equal((await fetch(url)).status, 503);
      await writeFile(file, expected);
      assert.deepEqual(Buffer.from(await (await fetch(url)).arrayBuffer()), expected);
    }
    assert.equal((await fetch(retired)).status, 404);
  });
});
