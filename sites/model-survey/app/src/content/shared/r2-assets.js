const MAX_ASSET_BYTES = 64_000_000;
const FORMATS = {
  'model/gltf-binary': /\.glb$/iu, 'image/png': /\.png$/iu,
  'image/webp': /\.webp$/iu, 'image/jpeg': /\.(jpg|jpeg)$/iu,
  'application/zip': /\.zip$/iu, 'application/gzip': /\.nii\.gz$/iu,
  'application/octet-stream': /\.(blend|raw|nii|nrrd|npz|svg|json)$/iu,
  'audio/wav': /\.wav$/iu, 'video/mp4': /\.mp4$/iu, 'font/ttf': /\.ttf$/iu,
  'model/stl': /\.stl$/iu, 'model/obj': /\.obj$/iu,
};
const HASH = /^[a-f0-9]{64}$/u;
const headers = { 'access-control-allow-origin': '*', 'x-content-type-options': 'nosniff' };

function reply(value, status = 200, extra = {}) {
  return new Response(JSON.stringify(value), { status, headers: {
    ...headers, 'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store', ...extra,
  } });
}

export function createAssetDelivery(manifest, ownerCanEdit) {
  const entries = new Map();
  for (const asset of manifest.assets) {
    if (!HASH.test(asset.sha256) || !Number.isSafeInteger(asset.bytes) || asset.bytes < 1
      || asset.bytes > MAX_ASSET_BYTES || !/^[a-zA-Z0-9_.-]+$/u.test(asset.name)
      || !Object.hasOwn(FORMATS, asset.mediaType)) throw new Error('Invalid published asset.');
    if (asset.mediaType === 'application/zip' && !asset.name.endsWith('.zip')) throw new Error('ZIP assets need a .zip filename.');
    if (!FORMATS[asset.mediaType].test(asset.name)) throw new Error('Asset type and extension differ.');
    const route = `/assets/${asset.sha256}/${asset.name}`;
    if (entries.has(route)) throw new Error('Duplicate published asset.');
    entries.set(route, { ...asset, key: `assets/sha256/${asset.sha256}` });
  }
  async function mayUpload(request, env) {
    const origin = request.headers.get('origin');
    if (origin && origin !== new URL(request.url).origin) return false;
    if (await ownerCanEdit(request, env)) return true;
    const token = request.headers.get('x-asset-upload-token');
    const expected = env.ASSET_UPLOAD_TOKEN_SHA256;
    const expiry = Date.parse(env.ASSET_UPLOAD_TOKEN_EXPIRES_AT);
    if (!token || token.length > 256 || !HASH.test(expected ?? '')
      || !Number.isFinite(expiry) || Date.now() >= expiry) return false;
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
    return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('') === expected;
  }
  return async function assetResponse(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith('/assets/')) return null;
    if (url.search) return reply({ error: 'Asset query parameters are not supported.' }, 400);
    if (url.pathname === '/assets/index.json') {
      if (!['GET', 'HEAD'].includes(request.method)) return reply({ error: 'Read only.' }, 405);
      const response = reply(manifest);
      return request.method === 'HEAD' ? new Response(null, response) : response;
    }
    const asset = entries.get(url.pathname);
    if (!asset) return reply({ error: 'Unknown published asset.' }, 404);
    const key = asset.key;
    if (request.method === 'PUT') {
      if (!(await mayUpload(request, env))) return reply({ error: 'Owner upload authorization is required.' }, 403);
      if (request.headers.get('content-length') !== String(asset.bytes)
        || !['identity', null].includes(request.headers.get('content-encoding')) || !request.body) {
        return reply({ error: 'Asset size or encoding does not match.' }, 400);
      }
      try {
        const existing = await env.BUCKET.head(key);
        if (existing) {
          if (existing.size !== asset.bytes || existing.customMetadata?.sha256 !== asset.sha256) {
            return reply({ error: 'Existing immutable object conflicts with the published asset.' }, 409);
          }
          return reply({ sha256: asset.sha256, bytes: asset.bytes, reused: true });
        }
        // R2 checks the streamed SHA-256 before storing; no whole-file Worker buffer.
        const result = await env.BUCKET.put(key, request.body, {
          sha256: asset.sha256, onlyIf: { etagDoesNotMatch: '*' },
          httpMetadata: { contentType: asset.mediaType }, customMetadata: { sha256: asset.sha256 },
        });
        if (!result || result.size !== asset.bytes) return reply({ error: 'Asset upload did not complete.' }, 409);
        return reply({ sha256: asset.sha256, bytes: result.size });
      } catch { return reply({ error: 'Asset upload failed integrity or storage validation.' }, 400); }
    }
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) return reply({ error: 'Method not allowed.' }, 405);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: {
      ...headers, 'access-control-allow-methods': 'GET, HEAD, OPTIONS',
      'access-control-allow-headers': 'Range',
    } });
    try {
      const metadata = await env.BUCKET.head(key);
      if (!metadata || metadata.size !== asset.bytes || metadata.customMetadata?.sha256 !== asset.sha256) {
        return reply({ error: 'Published asset is unavailable.' }, 503);
      }
      const responseHeaders = { ...headers, 'content-type': asset.mediaType,
        'content-length': String(asset.bytes), etag: `"${asset.sha256}"`,
        'cache-control': 'public, max-age=31536000, immutable', 'accept-ranges': 'bytes',
        'access-control-expose-headers': 'Content-Length, Content-Range, ETag',
        ...(asset.mediaType.startsWith('application/') ? { 'content-disposition': `attachment; filename="${asset.name}"` } : {}),
      };
      if (request.headers.get('if-none-match') === responseHeaders.etag) {
        delete responseHeaders['content-length'];
        return new Response(null, { status: 304, headers: responseHeaders });
      }
      if (request.method === 'HEAD') return new Response(null, { headers: responseHeaders });
      let range;
      if (request.headers.has('range')) {
        const match = /^bytes=(\d+)-(\d*)$/u.exec(request.headers.get('range'));
        const offset = match ? Number(match[1]) : NaN;
        const end = match?.[2] ? Number(match[2]) : asset.bytes - 1;
        if (!Number.isSafeInteger(offset) || !Number.isSafeInteger(end) || offset > end || offset >= asset.bytes) {
          return reply({ error: 'Unsupported byte range.' }, 416, { 'content-range': `bytes */${asset.bytes}` });
        }
        range = { offset, length: Math.min(end, asset.bytes - 1) - offset + 1 };
        responseHeaders['content-length'] = String(range.length);
        responseHeaders['content-range'] = `bytes ${offset}-${offset + range.length - 1}/${asset.bytes}`;
      }
      const object = await env.BUCKET.get(key, range ? { range } : undefined);
      if (!object?.body) return reply({ error: 'Published asset is unavailable.' }, 503);
      return new Response(object.body, { status: range ? 206 : 200, headers: responseHeaders });
    } catch { return reply({ error: 'Asset storage is unavailable.' }, 503); }
  };
}
