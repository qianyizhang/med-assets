import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { once } from 'node:events';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import localDelivery from '../app/src/content/assets/local-delivery.json' with { type: 'json' };

const repo = fileURLToPath(new URL('../../../', import.meta.url));
const site = fileURLToPath(new URL('../', import.meta.url));

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

test('a restored film becomes available without restarting or publishing its local route', async (t) => {
  const scratch = path.join(repo, '.artifacts');
  await mkdir(scratch, { recursive: true });
  const project = await mkdtemp(path.join(scratch, 'preview-restore-test-'));
  t.after(() => rm(project, { recursive: true, force: true }));

  const bytes = Buffer.from('retained film fixture');
  const sha256 = createHash('sha256').update(bytes).digest('hex');
  const name = 'film.mp4';
  const file = path.join(project, name);
  const inputs = path.join(project, 'src/content/gallery/teaching-inputs');
  await mkdir(inputs, { recursive: true });
  await writeFile(path.join(inputs, 'image26-media.json'), JSON.stringify([
    { path: path.relative(repo, file), name, sha256 },
  ]));
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
  const scratch = path.join(repo, '.artifacts');
  await mkdir(scratch, { recursive: true });
  const checkout = await mkdtemp(path.join(scratch, 'model-preview-restore-test-'));
  t.after(() => rm(checkout, { recursive: true, force: true }));
  const fixtureSite = path.join(checkout, 'sites/anatomy-gallery');
  await cp(path.join(site, 'app/src/content'), path.join(fixtureSite, 'app/src/content'), { recursive: true });
  await cp(path.join(site, 'snapshot-reference.json'), path.join(fixtureSite, 'snapshot-reference.json'));
  const script = path.join(fixtureSite, 'tools/preview_gallery.mjs');
  await cp(path.join(site, 'tools/preview_gallery.mjs'), script);
  await mkdir(path.join(checkout, 'dist'));
  await writeFile(path.join(checkout, 'dist/index.html'), 'fixture');

  await withPreview(script, checkout, async (origin) => {
    for (const reviewPath of localDelivery.receipts) {
      const receiptUrl = origin + '/' + reviewPath;
      assert.equal((await fetch(receiptUrl)).status, 404);
      const receiptFile = path.join(checkout, reviewPath);
      await mkdir(path.dirname(receiptFile), { recursive: true });
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
