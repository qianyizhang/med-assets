// Read-only loopback preview of the built Site. Serve only manifest-bound bytes.
import http from 'node:http';
import { createHash } from 'node:crypto';
import { readFile, realpath } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { createAssetDelivery } from '../app/src/content/shared/r2-assets.js';
import manifest from '../app/src/content/assets/r2-trial.json' with { type: 'json' };
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
const indexed = new Map(manifest.assets.map((a) => [a.sha256, a]));
async function payload(key) {
  const hash = key.split('/').at(-1),
    asset = indexed.get(hash);
  if (!asset) return null;
  if (previews.has(hash)) return previews.get(hash);
  for (const p of asset.paths ?? [asset.path]) {
    if (!p) continue;
    try {
      const local = await realpath(path.join(repo, p));
      if (!local.startsWith(repo + path.sep)) continue;
      const bytes = await readFile(local);
      if (bytes.length === asset.bytes && digest(bytes) === hash) return bytes;
    } catch (e) {
      if (e.code !== 'ENOENT') throw e;
    }
  }
  return null;
}
const assets = createAssetDelivery(manifest, async () => false);
const env = {
  BUCKET: {
    async head(key) {
      const data = await payload(key);
      return data ? { size: data.length, customMetadata: { sha256: digest(data) } } : null;
    },
    async get(key, options) {
      const data = await payload(key);
      const r = options?.range;
      return data && { body: r ? data.subarray(r.offset, r.offset + r.length) : data };
    },
  },
};
http
  .createServer(async (req, res) => {
    try {
      if (!['GET', 'HEAD'].includes(req.method)) {
        res.writeHead(405).end();
        return;
      }
      const request = new Request('http://127.0.0.1:' + port + req.url, {
        method: req.method,
        headers: req.headers,
      });
      let response = await assets(request, env);
      if (!response) {
        const home = ['/', '/index.html'].includes(new URL(request.url).pathname);
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
    console.log('Gallery preview: http://127.0.0.1:' + port + '/?view=1'),
  );
