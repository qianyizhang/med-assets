#!/usr/bin/env node
// Upload only reviewed routes and Git-pinned local bytes. Tokens arrive through stdin.
import { createHash, randomUUID } from 'node:crypto';
import { createReadStream, constants } from 'node:fs';
import { readFile, rename, mkdir, lstat, realpath, open, unlink } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  assetsByPath, assetsByRoute, assetRoute, HASH, MAX_ASSET_BYTES,
} from '../../sites/anatomy-gallery/app/src/content/shared/asset-index.mjs';

const ROOT = fileURLToPath(new URL('../../', import.meta.url));
const INDEX = 'sites/anatomy-gallery/app/src/content/assets/delivery-index.json';
const ORIGIN = 'https://med-assets-model-survey.landy123007.chatgpt.site';
const MAX_OBJECTS = 32;
const MAX_PLAN_BYTES = 64_000_000;
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const fileStream = (path, options) => createReadStream(path, {
  flags: constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK, ...options,
});
const pointerPrefix = Buffer.from('version https://git-lfs.github.com/spec/v1');
const pointer = /^version https:\/\/git-lfs.github.com\/spec\/v1\noid sha256:([a-f0-9]{64})\nsize ([1-9][0-9]*)\n$/u;

function fields(value, keys) {
  return value && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
}

function validatedPlan(plan, catalog) {
  if (!fields(plan, ['schemaVersion', 'revision', 'objectCount', 'totalBytes', 'objects'])
      || plan.schemaVersion !== 1 || typeof plan.revision !== 'string' || !/^[a-f0-9]{40}$/u.test(plan.revision)) {
    throw Error('A versioned upload plan with an exact source revision is required');
  }
  const objects = plan.objects;
  if (!Array.isArray(objects) || objects.length < 1 || objects.length > MAX_OBJECTS
      || plan.objectCount !== objects.length) throw Error('Upload plan object count differs or exceeds the bound');

  const routes = assetsByRoute(catalog);
  const paths = assetsByPath(catalog);
  const seen = new Set(), sources = new Set();
  let bytes = 0;
  for (const object of objects) {
    if (!fields(object, ['sourcePath', 'sha256', 'bytes', 'name', 'mediaType'])) {
      throw Error('Invalid upload plan object fields');
    }
    const path = object.sourcePath;
    if (typeof path !== 'string' || path.length < 1 || path.length > 4096 || /[\\\x00-\x1f\x7f]/u.test(path)
        || path.split('/').some(part => ['', '.', '..', '.git'].includes(part.toLowerCase()))) throw Error('Unsafe payload source path');
    if (typeof object.sha256 !== 'string' || !HASH.test(object.sha256)
        || !Number.isSafeInteger(object.bytes) || object.bytes < 1 || object.bytes > MAX_ASSET_BYTES) {
      throw Error('Invalid transport identity');
    }
    const route = assetRoute(object);
    const declared = routes.get(route), binding = paths.get(path);
    if (!declared || declared.bytes !== object.bytes || declared.mediaType !== object.mediaType
        || !binding || assetRoute(binding) !== route) throw Error('Undeclared upload destination or source binding');
    if (seen.has(object.sha256) || sources.has(path)) throw Error('Duplicate payload object or source');
    seen.add(object.sha256); sources.add(path);
    bytes += object.bytes;
  }
  if (bytes !== plan.totalBytes || bytes > MAX_PLAN_BYTES) throw Error('Upload plan byte total differs or exceeds the bound');
  return objects;
}

async function checkedPath(root, name) {
  const path = resolve(root, name);
  if (await realpath(path) !== path || !(await lstat(path)).isFile()) {
    throw Error('Payload path is not a regular unlinked file: ' + name);
  }
  return path;
}

async function streamIdentity(body, size) {
  const hash = createHash('sha256');
  let count = 0;
  for await (const chunk of body) {
    count += chunk.length;
    if (count > size) throw Error('Payload exceeds pinned size');
    hash.update(chunk);
  }
  return { count, sha256: hash.digest('hex') };
}

export async function checkedObjects(root, plan, catalog) {
  const objects = validatedPlan(plan, catalog);
  root = await realpath(root);
  const git = (...args) => execFileSync('git', ['--no-lazy-fetch', ...args], { cwd: root, maxBuffer: MAX_ASSET_BYTES + 1024 });
  if (git('rev-parse', 'HEAD').toString().trim() !== plan.revision) {
    throw Error('Upload plan revision differs from checkout HEAD');
  }
  for (const object of objects) {
    const name = object.sourcePath;
    const row = git('--literal-pathspecs', 'ls-tree', '-lz', plan.revision, '--', name).toString();
    const entry = /^100(?:644|755) blob ([a-f0-9]{40}) +([0-9]+)\t/u.exec(row);
    if (!entry || row.slice(entry[0].length) !== name + '\0') {
      throw Error('Source is not a regular file at the selected Git revision: ' + name);
    }
    if (Number(entry[2]) > MAX_ASSET_BYTES) throw Error('Committed payload exceeds the byte bound: ' + name);
    const committed = git('cat-file', 'blob', entry[1]);
    const match = committed.length <= 1024 && pointer.exec(committed.toString('utf8'));
    if (committed.subarray(0, pointerPrefix.length).equals(pointerPrefix) && !match) {
      throw Error('Malformed committed LFS pointer');
    }
    const expectedHash = match ? match[1] : digest(committed);
    const expectedSize = match ? Number(match[2]) : committed.length;
    if (expectedHash !== object.sha256 || expectedSize !== object.bytes) {
      throw Error('Plan does not match the pinned Git payload: ' + name);
    }
    const path = await checkedPath(root, name);
    if ((await lstat(path)).size !== object.bytes) throw Error('Local payload changed: ' + name);
    const actual = await streamIdentity(fileStream(path), object.bytes);
    if (actual.count !== object.bytes || actual.sha256 !== object.sha256) throw Error('Local payload changed: ' + name);
  }
  return objects;
}

async function loadProgress(path, revision, fingerprint, objects) {
  const state = { revision, planSha256: fingerprint, verified: [] };
  await mkdir(dirname(path), { recursive: true });
  if (await realpath(dirname(path)) !== dirname(path)) throw Error('Upload state directory traverses a link');
  try {
    const info = await lstat(path);
    if (!info.isFile() || info.isSymbolicLink() || info.size > 16_384) throw Error('Unsafe upload state file');
    const saved = JSON.parse(await readFile(path, { encoding: 'utf8', flag: constants.O_RDONLY | constants.O_NOFOLLOW }));
    if (saved.planSha256 !== fingerprint || saved.revision !== revision) throw Error('Upload state belongs to another plan');
    const allowed = new Set(objects.map(x => x.sha256));
    if (!Array.isArray(saved.verified) || saved.verified.some(x => !allowed.has(x))
        || new Set(saved.verified).size !== saved.verified.length) throw Error('Invalid upload state objects');
    return saved;
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    return state;
  }
}

async function persistProgress(path, state) {
  // A killed process may leave this temporary file. A later run can read the last complete receipt.
  const temporary = path + '.' + randomUUID() + '.tmp';
  const handle = await open(temporary, 'wx', 0o600);
  try {
    try {
      await handle.writeFile(JSON.stringify(state, null, 2) + '\n');
      await handle.sync();
    } finally {
      await handle.close();
    }
    await rename(temporary, path);
  } finally {
    await unlink(temporary).catch(error => {
      if (error.code !== 'ENOENT') throw error;
    });
  }
}

export async function uploadRepositoryAssets({ root, plan, catalog, token, origin = ORIGIN,
                                               statePath, fetchImpl = fetch, onProgress = () => {} }) {
  if (origin.replace(/\/$/u, '') !== ORIGIN) throw Error('Unexpected R2 destination');
  if (typeof token !== 'string' || token.length < 32 || token.length > 256 || /[^!-~]/u.test(token)) {
    throw Error('A bounded upload lease is required');
  }
  root = await realpath(root);
  const objects = await checkedObjects(root, plan, catalog);
  const fingerprint = digest(JSON.stringify(plan));
  const journal = statePath && resolve(statePath);
  const state = journal ? await loadProgress(journal, plan.revision, fingerprint, objects) : null;
  const verified = new Set(state?.verified);
  let completed = 0, completeBytes = 0;

  async function one(object) {
    const url = ORIGIN + assetRoute(object);
    if (!verified.has(object.sha256)) {
      const local = await checkedPath(root, object.sourcePath);
      const body = fileStream(local, { end: object.bytes - 1 });
      let response;
      try {
        response = await fetchImpl(url, {
          method: 'PUT', redirect: 'error', body, duplex: 'half',
          headers: { 'content-length': String(object.bytes), 'content-type': object.mediaType, 'x-asset-upload-token': token },
        });
      } finally {
        body.destroy();
      }
      if (response.status !== 200) throw Error('R2 upload HTTP ' + response.status + ' for ' + object.sourcePath);
      const receipt = await response.json();
      if (receipt.sha256 !== object.sha256 || receipt.bytes !== object.bytes) throw Error('Upload receipt identity differs');
    }
    const response = await fetchImpl(url, {
      redirect: 'error', cache: 'no-store', headers: { 'accept-encoding': 'identity', 'cache-control': 'no-cache' },
    });
    if (response.status !== 200 || !['identity', null].includes(response.headers.get('content-encoding')) || !response.body) {
      throw Error('R2 readback status/encoding differs');
    }
    const { count, sha256 } = await streamIdentity(response.body, object.bytes);
    if (count !== object.bytes || sha256 !== object.sha256) throw Error('R2 fresh readback checksum/size differs');
    verified.add(object.sha256);
    completed++;
    completeBytes += count;
  }

  for (let start = 0; start < objects.length; start += 4) {
    const outcomes = await Promise.allSettled(objects.slice(start, start + 4).map(one));
    if (state) await persistProgress(journal, { ...state, verified: [...verified] });
    const failed = outcomes.find(outcome => outcome.status === 'rejected');
    if (failed) throw failed.reason;
    onProgress({ verified: completed, total: objects.length, bytes: completeBytes });
  }
  return { verified: completed, bytes: completeBytes, revision: plan.revision, planSha256: fingerprint };
}

async function planFiles(root, planPath, catalogPath = resolve(root, INDEX)) {
  const info = await lstat(planPath);
  if (!info.isFile() || info.size > 512_000) throw Error('Upload plan file exceeds the read bound or is not a regular file');
  return {
    plan: JSON.parse(await readFile(planPath, 'utf8')),
    catalog: JSON.parse(await readFile(catalogPath, 'utf8')),
  };
}

async function main() {
  const [, , mode, planPath, catalogPath, checkout = ROOT] = process.argv;
  if (mode === '--check' && planPath) {
    const { plan, catalog } = await planFiles(checkout, planPath, catalogPath);
    await checkedObjects(checkout, plan, catalog);
    console.log(JSON.stringify({ revision: plan.revision, objects: plan.objectCount, bytes: plan.totalBytes, transferred: false }));
    return;
  }
  if (mode !== undefined) throw Error('Use --check PLAN [CATALOG [CHECKOUT]] or send one upload JSON line on stdin');
  if (process.stdin.isTTY) process.stdin.setRawMode(true);
  process.stdout.write('Ready for hidden R2 upload JSON on stdin\n');
  const input = await new Promise((accept, reject) => {
    let body = '';
    const read = chunk => {
      body += chunk;
      const end = body.indexOf('\n');
      if (end < 0 && body.length < 16_384) return;
      process.stdin.off('data', read);
      process.stdin.pause();
      try {
        if (end < 0 || end > 16_384) throw Error('Request exceeds input bound');
        accept(JSON.parse(body.slice(0, end)));
      } catch {
        reject(Error('Invalid upload request JSON'));
      }
    };
    process.stdin.on('data', read);
    process.stdin.once('end', () => reject(Error('Upload request ended before its JSON line')));
  });
  const root = input.root ?? ROOT;
  const { plan, catalog } = await planFiles(root, input.planPath, input.catalogPath);
  const result = await uploadRepositoryAssets({
    root, plan, catalog, token: input.token, statePath: input.statePath,
    onProgress: value => console.log(JSON.stringify(value)),
  });
  console.log(JSON.stringify(result));
  if (process.stdin.isTTY) process.stdin.setRawMode(false);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => {
    if (process.stdin.isTTY) process.stdin.setRawMode(false);
    console.error('R2 migration stopped: ' + error.message);
    process.exitCode = 1;
    process.stdin.pause();
  });
}
