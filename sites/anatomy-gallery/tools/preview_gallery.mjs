// Read-only loopback preview of the built Site. Serve only manifest-bound bytes.
import http from 'node:http';
import { createHash } from 'node:crypto';
import { readFile, realpath } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { createAssetDelivery } from '../app/src/content/shared/r2-assets.js';
import manifest from '../app/src/content/assets/delivery-index.json' with { type: 'json' };
import localDelivery from '../app/src/content/assets/local-delivery.json' with { type: 'json' };
import legacyDental from '../app/src/content/assets/legacy-dental-assets.json' with { type: 'json' };
import binding from '../snapshot-reference.json' with { type: 'json' };

const site = fileURLToPath(new URL('../', import.meta.url));
const repo = await realpath(path.resolve(site, '../..'));
const project = path.resolve(process.argv[2] || path.join(site, '.local/gallery-work'));
const htmlPath = path.join(project, 'dist/index.html');
await readFile(htmlPath);
const port = Number(process.argv[3] || 8858);
const digest = (b) => createHash('sha256').update(b).digest('hex');
const previews = new Map();
const seed = path.join(
  site,
  '.local/preview/dist',
  'snapshot.' + binding.sourceSnapshotSha256 + '.json',
);
try {
  const bytes = await readFile(seed);
  if (digest(bytes) !== binding.sourceSnapshotSha256)
    throw Error('Original preview seed identity differs.');
  for (const p of Object.values(JSON.parse(bytes).previewGallery)) {
    for (const image of [p.thumb, p.image]) {
      if (image?.startsWith('data:image/webp;base64,')) {
        const b = Buffer.from(image.split(',')[1], 'base64');
        previews.set(digest(b), b);
      }
    }
  }
} catch (e) {
  if (e.code !== 'ENOENT') throw e;
}
async function repoFile(relative) {
  try {
    const local = await realpath(path.join(repo, relative));
    return local.startsWith(repo + path.sep) ? await readFile(local) : null;
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    return null;
  }
}

const archiveRoutes = new Map();
const mediaIndex = path.join(project, 'src/content/gallery/teaching-inputs/image26-media.json');
try {
  for (const entry of JSON.parse(await readFile(mediaIndex, 'utf8'))) {
    archiveRoutes.set('/assets/' + entry.sha256 + '/' + entry.name, entry);
  }
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}
const indexed = new Map(manifest.assets.map((asset) => [asset.sha256, asset]));
const legacyDentalRoutes = new Map(legacyDental.assets.map((file) =>
  ['/assets/' + file.sha256 + '/' + file.name, file]));
const localRoutes = new Map(localDelivery.assets.map((file) =>
  ['/assets/' + file.sha256 + '/' + file.name, file]));
const receiptRoutes = new Map(localDelivery.receipts.map((file) => ['/' + file, file]));
const serveDental = createAssetDelivery(legacyDental, async () => false);
const serveLocal = createAssetDelivery({ assets: localDelivery.assets }, async () => false);
async function dentalPayload(file) {
  const bytes = await repoFile('sites/anatomy-gallery/.local/legacy-dental/' + file.sha256);
  return bytes?.length === file.bytes && digest(bytes) === file.sha256 ? bytes : null;
}
async function trackedPayload(asset) {
  for (const p of asset.paths ?? [asset.path]) {
    if (!p) continue;
    const bytes = await repoFile(p);
    if (bytes?.length === asset.bytes && digest(bytes) === asset.sha256) return bytes;
  }
  return null;
}
async function payload(key) {
  const hash = key.split('/').at(-1);
  const asset = indexed.get(hash);
  if (!asset) return null;
  return previews.get(hash) ?? trackedPayload(asset);
}
const assets = createAssetDelivery(manifest, async () => false);
// Keep verified bytes only for this request so head and range reads agree.
function readOnlyBucket(load) {
  const reads = new Map();
  function read(key) {
    if (!reads.has(key)) reads.set(key, load(key));
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

async function serveArchive(request, entry) {
  const bytes = await repoFile(entry.path).catch((error) => {
    if (!['EACCES', 'EISDIR', 'EPERM'].includes(error.code)) throw error;
    return null;
  });
  if (!bytes || digest(bytes) !== entry.sha256) {
    return new Response('Archived film unavailable.', { status: 503, headers: { 'cache-control': 'no-store' } });
  }
  const asset = { ...entry, bytes: bytes.length, mediaType: 'video/mp4' };
  const serve = createAssetDelivery({ assets: [asset] }, async () => false);
  return serve(request, { BUCKET: readOnlyBucket(() => bytes) });
}
const server = http
  .createServer(async (req, res) => {
    try {
      if (!['GET', 'HEAD'].includes(req.method)) {
        res.writeHead(405).end();
        return;
      }
      const request = new Request('http://127.0.0.1:' + server.address().port + req.url, {
        method: req.method,
        headers: req.headers,
      });
      const pathname = new URL(request.url).pathname;
      const entry = archiveRoutes.get(pathname);
      const dental = legacyDentalRoutes.get(pathname);
      const local = localRoutes.get(pathname);
      const receiptPath = receiptRoutes.get(pathname);
      let response;
      if (receiptPath) {
        const receipt = await repoFile(receiptPath);
        response = new Response(req.method === 'GET' ? receipt : null, {
          status: receipt ? 200 : 404,
          headers: { 'content-type': 'application/json', 'content-length': String(receipt?.length ?? 0) },
        });
      } else if (entry) response = await serveArchive(request, entry);
      else if (dental) response = await serveDental(request, { BUCKET: readOnlyBucket(() => dentalPayload(dental)) });
      else if (local) response = await serveLocal(request, { BUCKET: readOnlyBucket(() => trackedPayload(local)) });
      else response = await assets(request, { BUCKET: readOnlyBucket(payload) });
      if (!response) {
        const home = ['/', '/index.html'].includes(pathname);
        response = new Response(home && req.method === 'GET' ? await readFile(htmlPath) : null, {
          status: home ? 200 : 404,
          headers: { 'content-type': 'text/html; charset=utf-8' },
        });
      }
      res.writeHead(response.status, Object.fromEntries(response.headers));
      res.end(Buffer.from(await response.arrayBuffer()));
    } catch (e) {
      console.error(e.message);
      res.writeHead(500).end();
    }
  })
  .listen(port, '127.0.0.1', () =>
    console.log('Gallery preview: http://127.0.0.1:' + server.address().port + '/#/library'),
  );
