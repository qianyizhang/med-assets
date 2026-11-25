// Read-only loopback preview of the built Site. Serve only manifest-bound bytes.
import http from 'node:http';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFile, realpath } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { gunzipSync } from 'node:zlib';
import path from 'node:path';
import { readRetainedProjection } from '../../../reviews/trachea/2026-10-29-open-airway-r06/restore-projections.mjs';

const site = fileURLToPath(new URL('../', import.meta.url));
const repo = await realpath(path.resolve(site, '../..'));
const project = path.resolve(process.argv[2] || path.join(site, '.local/gallery-candidate'));
const html = await readFile(path.join(project, 'dist/index.html'));
const content = path.join(project, 'src/content');
const projectJson = async (name) => JSON.parse(await readFile(path.join(content, name), 'utf8'));
const release = await projectJson('assets/gallery-release.json');
const manifest = await projectJson('assets/delivery-index.json');
const { createAssetDelivery } = await import(pathToFileURL(path.join(content, 'shared/r2-assets.js')));
const serve = createAssetDelivery(manifest, async () => false);
const port = Number(process.argv[3] || 8858);
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

async function repoFile(relative) {
  try {
    const expected = path.join(repo, relative);
    if (!expected.startsWith(repo + path.sep) || await realpath(expected) !== expected) return null;
    return await readFile(expected);
  } catch (error) {
    if (['ENOENT', 'EACCES', 'EPERM', 'EISDIR'].includes(error.code)) return null;
    throw error;
  }
}

const previews = new Map();
let seed = {};
if (release.previewSnapshotSha256) {
  const expected = release.previewSnapshotSha256;
  if (!/^[a-f0-9]{64}$/u.test(expected)) throw Error('Invalid preview snapshot identity.');
  const raw = await repoFile('sites/anatomy-gallery/.local/preview/dist/snapshot.' + expected + '.json');
  if (raw) {
    if (sha256(raw) !== expected) throw Error('Original preview seed identity differs.');
    seed = JSON.parse(raw);
  }
}
for (const p of Object.values(seed.previewGallery ?? {})) {
  for (const image of [p.thumb, p.image]) {
    if (image?.startsWith('data:image/webp;base64,')) {
      const bytes = Buffer.from(image.split(',')[1], 'base64');
      previews.set(sha256(bytes), bytes);
    }
  }
}

const indexed = new Map();
const optional = new Map();
for (const asset of [...manifest.assets, ...release.resources]) {
  const map = asset.localOnly ? optional : indexed;
  if (!map.has(asset.sha256)) map.set(asset.sha256, []);
  map.get(asset.sha256).push(asset);
}

async function trackedPayload(asset) {
  for (const p of [...(asset.paths ?? [asset.path]), ...(asset.historicalPaths ?? [])]) {
    if (!p) continue;
    const bytes = await repoFile(p);
    if (bytes?.length === asset.bytes && sha256(bytes) === asset.sha256) return bytes;
    const projection = await readRetainedProjection(p, asset);
    if (projection) return projection;
    if (/^experiments\/dental-video-treatments\/fonts\/DejaVuSans(?:-Bold)?\.ttf$/u.test(p)) {
      const font = await repoFile('sources/fonts/dejavu/' + path.basename(p));
      if (font?.length === asset.bytes && sha256(font) === asset.sha256) return font;
    }
    if (/^heart\/Cardiac_Atlas\/exports\/anatomy_(meshes|details)\.json$/u.test(p)) {
      const packed = await repoFile(p + '.gz');
      if (packed) {
        const original = gunzipSync(packed, { maxOutputLength: asset.bytes });
        if (original.length === asset.bytes && sha256(original) === asset.sha256) return original;
      }
    }
  }
  return null;
}

// A retained public address may outlive the working-tree path of its LFS payload.
let lfsDirectory;
async function publishedLfsBytes(asset) {
  if (!/^[a-f0-9]{64}$/u.test(asset.sha256)) return null;
  if (lfsDirectory === undefined) {
    try {
      const env = execFileSync('git', ['lfs', 'env'], { cwd: repo, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
      lfsDirectory = /^LocalMediaDir=(.+)$/mu.exec(env)?.[1] || null;
    } catch { lfsDirectory = null; }
  }
  if (!lfsDirectory) return null;
  const hash = asset.sha256;
  const file = path.join(lfsDirectory, hash.slice(0, 2), hash.slice(2, 4), hash);
  try {
    if (await realpath(file) !== file) return null;
    const bytes = await readFile(file);
    return bytes.length === asset.bytes && sha256(bytes) === hash ? bytes : null;
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    return null;
  }
}

async function payload(key, index) {
  const hash = key.split('/').at(-1);
  const entries = index.get(hash);
  if (!entries) return null;
  if (previews.has(hash)) return previews.get(hash);
  if (index === optional) {
    const dental = await repoFile('sites/anatomy-gallery/.local/legacy-dental/' + hash);
    if (dental?.length === entries[0].bytes && sha256(dental) === hash) return dental;
  }
  for (const asset of entries) {
    const bytes = await trackedPayload(asset);
    if (bytes) return bytes;
  }
  return release.selection === 'published' ? publishedLfsBytes(entries[0]) : null;
}

// Reuse verified bytes only within one request so HEAD and range reads agree.
function readOnlyBucket(index) {
  const reads = new Map();
  function read(key) {
    if (!reads.has(key)) reads.set(key, payload(key, index));
    return reads.get(key);
  }
  return {
    async head(key) {
      const data = await read(key);
      return data && { size: data.length, customMetadata: { sha256: key.split('/').at(-1) } };
    },
    async get(key, options) {
      const data = await read(key);
      const r = options?.range;
      return data && { body: r ? data.subarray(r.offset, r.offset + r.length) : data };
    },
  };
}

const server = http.createServer(async (req, res) => {
  try {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(req.method)) return res.writeHead(405).end();
    const request = new Request('http://127.0.0.1:' + server.address().port + req.url, {
      method: req.method, headers: req.headers,
    });
    const pathname = new URL(request.url).pathname;
    let response = await serve(request, {
      BUCKET: readOnlyBucket(indexed), LOCAL_GALLERY_FILES: readOnlyBucket(optional),
    });
    if (!response) {
      const home = ['/', '/index.html'].includes(pathname);
      response = new Response(home && req.method === 'GET' ? html : null, {
        status: home ? 200 : 404, headers: { 'content-type': 'text/html; charset=utf-8' },
      });
    }
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
  } catch (error) {
    console.error(error.message);
    res.writeHead(500).end();
  }
}).listen(port, '127.0.0.1', () =>
  console.log('Gallery preview: http://127.0.0.1:' + server.address().port + '/'));
