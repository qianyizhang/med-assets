import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, readFile, rm, realpath, rename, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { checkedObjects, uploadRepositoryAssets } from '../transport/tools/r2_upload.mjs';
import { createAssetDelivery } from '../sites/anatomy-gallery/app/src/content/shared/asset-delivery.js';
import { assetRoute, assetsByPath } from '../sites/anatomy-gallery/app/src/content/shared/asset-index.mjs';

const planner = fileURLToPath(new URL('../transport/tools/r2_migration.py', import.meta.url));
const uploader = fileURLToPath(new URL('../transport/tools/r2_upload.mjs', import.meta.url));
const python = process.env.MED_ASSETS_TEST_PYTHON ?? 'python3.12';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const origin = 'https://med-assets-model-survey.landy123007.chatgpt.site';
const receipt = { revision: 'a'.repeat(40), count: 694, paths: 694, bytes: 976485579 };

async function fixture(t, count = 3) {
  const root = await realpath(await mkdtemp(join(tmpdir(), 'r2-upload-test-')));
  t.after(() => rm(root, { recursive: true, force: true }));
  const git = (...args) => execFileSync('git', ['-C', root, ...args], { encoding: 'utf8' }).trim();
  const commit = () => {
    git('add', '-A', '--', '*.glb');
    git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture');
  };
  git('init', '-q');
  const names = [];
  const lfsBytes = Buffer.from('glTF-payload-LFS');
  const pointer = data => `version https://git-lfs.github.com/spec/v1\noid sha256:${hash(data)}\nsize ${data.length}\n`;
  for (let i = 0; i < count; i++) {
    const name = 'model-' + i + '.glb';
    await writeFile(join(root, name), i === 0 ? pointer(lfsBytes) : 'glTF-payload-' + i);
    names.push(name);
  }
  const unselected = 'unselected.glb';
  await writeFile(join(root, unselected), pointer(Buffer.from('unhydrated')));
  commit();
  await writeFile(join(root, names[0]), lfsBytes);
  await rm(join(root, unselected)); // The planner must never open this unselected payload.

  let writes = 0;
  const generate = async ({ paths = names, retire = [], catalog = { assets: [], repositoryPayloads: receipt } } = {}) => {
    const index = ++writes;
    const catalogInput = join(root, 'input-' + index + '.json');
    const planPath = join(root, 'plan-' + index + '.json');
    const catalogPath = join(root, 'catalog-' + index + '.json');
    await writeFile(catalogInput, JSON.stringify(catalog));
    execFileSync(python, [planner, '--root', root, '--catalog', catalogInput, '--catalog-output', catalogPath,
      '--plan-output', planPath, ...paths.flatMap(path => ['--path', path]),
      ...retire.flatMap(path => ['--retire-path', path])], { encoding: 'utf8' });
    return { plan: JSON.parse(await readFile(planPath)), catalog: JSON.parse(await readFile(catalogPath)), planPath, catalogPath };
  };
  const token = 'fixture-token-'.repeat(4);
  const calls = [];
  const objects = new Map();
  const load = (catalog) => {
    const serve = createAssetDelivery(catalog, async () => false);
    const env = {
      ASSET_UPLOAD_TOKEN_SHA256: hash(token),
      ASSET_UPLOAD_TOKEN_EXPIRES_AT: new Date(Date.now() + 120_000).toISOString(),
      BUCKET: {
        async head(key) { return objects.get(key) ?? null; },
        async put(key, body, options) {
          const bytes = Buffer.from(await new Response(body).arrayBuffer());
          assert.equal(hash(bytes), options.sha256);
          assert.equal(options.onlyIf.etagDoesNotMatch, '*');
          assert.equal(objects.has(key), false);
          const object = { size: bytes.length, customMetadata: options.customMetadata, bytes };
          objects.set(key, object);
          return object;
        },
        async get(key) { return { body: objects.get(key).bytes }; },
      },
    };
    return async (url, options) => {
      calls.push({ url, method: options.method ?? 'GET' });
      assert.equal(options.redirect, 'error');
      if (!options.method) {
        assert.equal(options.cache, 'no-store');
        assert.equal(options.headers['x-asset-upload-token'], undefined);
      }
      return serve(new Request(url, options), env);
    };
  };
  const generated = await generate();
  return { root, names, git, commit, generate, load, ...generated, objects, calls, fetchImpl: load(generated.catalog),
    statePath: join(root, 'state.json'), token };
}

test('planner output passes uploader CLI preflight, Worker upload, and anonymous fresh readback', async t => {
  const f = await fixture(t);
  const preflight = JSON.parse(execFileSync(process.execPath, [uploader, '--check', f.planPath, f.catalogPath, f.root]));
  assert.deepEqual(preflight, { revision: f.plan.revision, objects: 3, bytes: f.plan.totalBytes, transferred: false });
  const result = await uploadRepositoryAssets(f);
  assert.equal(result.verified, 3);
  assert.equal(result.bytes, f.plan.totalBytes);
  assert.equal(f.objects.size, 3);
  const state = JSON.parse(await readFile(f.statePath));
  assert.equal(state.verified.length, 3);
  assert.equal(state.planSha256, result.planSha256);
  f.calls.length = 0;
  assert.equal((await uploadRepositoryAssets(f)).verified, 3);
  assert.equal(f.calls.length, 3);
  assert.ok(f.calls.every(x => x.method === 'GET'));
});

test('one catalog admits add, rename, replace and removal while serving retained exact addresses', async t => {
  const f = await fixture(t);
  await uploadRepositoryAssets(f);
  const [renamed, replaced, removed] = f.catalog.assets;
  // Restore the committed LFS pointer to move it through Git without changing identity.
  await writeFile(join(f.root, renamed.path), f.git('show', 'HEAD:' + renamed.path) + '\n');
  await rename(join(f.root, renamed.path), join(f.root, 'renamed.glb'));
  await writeFile(join(f.root, 'alias.glb'), await readFile(join(f.root, 'renamed.glb')));
  await writeFile(join(f.root, replaced.path), 'glTF-new-replacement');
  await rm(join(f.root, removed.path));
  await writeFile(join(f.root, 'new file.glb'), 'glTF-added');
  // Keep the unselected committed pointer in Git without hydrating it.
  await writeFile(join(f.root, 'unselected.glb'), f.git('show', 'HEAD:unselected.glb') + '\n');
  f.commit();
  for (const name of ['renamed.glb', 'alias.glb']) await writeFile(join(f.root, name), 'glTF-payload-LFS');

  const next = await f.generate({ paths: ['renamed.glb', 'alias.glb', replaced.path, 'new file.glb'],
    retire: [renamed.path, removed.path], catalog: f.catalog });
  assert.deepEqual(next.catalog.repositoryPayloads, receipt);
  assert.equal(next.catalog.assets.length, 5);
  const paths = assetsByPath(next.catalog);
  assert.equal(paths.get('renamed.glb').path, 'renamed.glb');
  assert.equal(assetRoute(paths.get('renamed.glb')), assetRoute(renamed));
  assert.equal(assetRoute(paths.get('alias.glb')), assetRoute(renamed));
  assert.ok(!paths.has(renamed.path));
  assert.ok(!paths.has(removed.path));
  assert.notEqual(paths.get(replaced.path).sha256, replaced.sha256);
  assert.deepEqual(next.catalog.assets[0].historicalPaths, [renamed.path]);
  assert.deepEqual(next.catalog.assets[1].historicalPaths, [replaced.path]);
  assert.deepEqual(next.catalog.assets[2].historicalPaths, [removed.path]);
  assert.equal(next.plan.objectCount, 3);
  assert.equal(next.plan.objects.find(row => row.sha256 === renamed.sha256).sourcePath, 'alias.glb');
  const fetchImpl = f.load(next.catalog);
  assert.equal((await uploadRepositoryAssets({ ...f, ...next, fetchImpl, statePath: undefined })).verified, 3);
  assert.equal(f.objects.size, 5);
  for (const retained of [renamed, replaced, removed]) {
    const response = await fetchImpl(origin + assetRoute(retained), { redirect: 'error', cache: 'no-store', headers: {} });
    assert.equal(response.status, 200);
    assert.equal(hash(Buffer.from(await response.arrayBuffer())), retained.sha256);
  }
});

test('a corrupt fresh read stops the active group and an identical plan safely resumes', async t => {
  const f = await fixture(t, 5);
  const interrupted = async (url, options) => {
    if (!options.method && url.endsWith('model-0.glb')) return new Response('corrupt');
    return f.fetchImpl(url, options);
  };
  await assert.rejects(uploadRepositoryAssets({ ...f, fetchImpl: interrupted }), /readback checksum/);
  assert.equal(f.calls.filter(x => x.method === 'PUT').length, 4);
  const state = JSON.parse(await readFile(f.statePath));
  assert.equal(state.verified.length, 3);
  assert.ok(!f.calls.some(x => x.url.endsWith('model-4.glb')));
  await writeFile(f.statePath + '.abandoned.tmp', 'incomplete write');

  f.calls.length = 0;
  const reordered = { ...f.plan, objects: [...f.plan.objects].reverse() };
  await assert.rejects(uploadRepositoryAssets({ ...f, plan: reordered }), /belongs to another plan/);
  assert.equal(f.calls.length, 0);
  const plan = JSON.parse(await readFile(f.planPath));
  assert.equal((await uploadRepositoryAssets({ ...f, plan })).verified, 5);
  assert.deepEqual(f.calls.filter(x => x.method === 'PUT').map(x => x.url.split('/').at(-1)), ['model-0.glb', 'model-4.glb']);
  assert.equal(f.calls.filter(x => x.method === 'GET').length, 5);
});

test('invalid scope, path, and route declarations are rejected before touching payloads', async t => {
  const f = await fixture(t);
  await rm(join(f.root, f.names[0]));
  await assert.rejects(uploadRepositoryAssets({ ...f, origin: 'https://untrusted.invalid' }), /destination/);
  await assert.rejects(uploadRepositoryAssets({ ...f, plan: f.catalog }), /versioned upload plan/);
  await assert.rejects(checkedObjects(f.root, { ...f.plan, totalBytes: f.plan.totalBytes + 1 }, f.catalog), /byte total/);
  await assert.rejects(checkedObjects(f.root, { ...f.plan, objectCount: 2 }, f.catalog), /object count/);
  for (const [changes, reason] of [[{ sourcePath: '../model.glb' }, /Unsafe/],
    [{ name: 'model-0-undeclared.glb' }, /Undeclared/], [{ mediaType: 'application/zip' }, /Undeclared/],
    [{ sourcePath: f.names[1] }, /Undeclared/]]) {
    const [first, ...rest] = f.plan.objects;
    const plan = { ...f.plan, objects: [{ ...first, ...changes }, ...rest] };
    await assert.rejects(uploadRepositoryAssets({ ...f, plan }), reason);
  }
  assert.equal(f.calls.length, 0);
});

test('changed working bytes, unsafe links and stale HEAD stop before network work', async t => {
  const f = await fixture(t);
  const source = join(f.root, f.names[0]);
  const body = await readFile(source);
  await writeFile(source, Buffer.alloc(body.length));
  await assert.rejects(uploadRepositoryAssets(f), /Local payload changed/);
  await rm(source);
  await symlink(join(f.root, f.names[1]), source);
  await assert.rejects(uploadRepositoryAssets(f), /not a regular unlinked file/);
  await rm(source);
  await writeFile(source, body);
  f.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--allow-empty', '-qm', 'new revision');
  await assert.rejects(uploadRepositoryAssets(f), /revision differs from checkout HEAD/);
  assert.equal(f.calls.length, 0);
});

test('same-revision false Git identity and over-budget plan cannot transfer', async t => {
  const f = await fixture(t);
  const [first, ...others] = f.plan.objects;
  const wrong = { ...first, sha256: '0'.repeat(64) };
  const catalog = { assets: f.catalog.assets.map((asset, i) => i === 0 ? { ...asset, sha256: wrong.sha256 } : asset) };
  await assert.rejects(uploadRepositoryAssets({ ...f, catalog, plan: { ...f.plan, objects: [wrong, ...others] } }), /pinned Git payload/);
  wrong.bytes = 64_000_000;
  catalog.assets[0].bytes = wrong.bytes;
  const totalBytes = wrong.bytes + others.reduce((total, asset) => total + asset.bytes, 0);
  await assert.rejects(uploadRepositoryAssets({ ...f, catalog, plan: { ...f.plan, totalBytes, objects: [wrong, ...others] } }), /exceeds the bound/);
  assert.equal(f.calls.length, 0);
});

test('quota or permission failure has no automatic retry or next group', async t => {
  const f = await fixture(t, 5);
  let calls = 0;
  f.fetchImpl = async () => { calls++; return new Response('denied', { status: 403 }); };
  await assert.rejects(uploadRepositoryAssets(f), /HTTP 403/);
  assert.equal(calls, 4);
});

test('a state symlink cannot redirect progress writes', async t => {
  const f = await fixture(t);
  const outside = join(f.root, 'unrelated.json');
  await writeFile(outside, 'keep this file');
  await symlink(outside, f.statePath);
  await assert.rejects(uploadRepositoryAssets(f), /Unsafe upload state file/);
  assert.equal(await readFile(outside, 'utf8'), 'keep this file');
  assert.equal(f.calls.length, 0);
});
