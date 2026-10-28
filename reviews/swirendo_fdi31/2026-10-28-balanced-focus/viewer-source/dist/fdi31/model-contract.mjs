// Two exact local review files only. No arbitrary URL or upload input.
export const DEFAULT_QUALITY = 'balanced';
export const MODELS = Object.freeze({
  balanced: Object.freeze({
    url: '/review/fdi31-balanced-20261028/FDI31-balanced.glb.gz',
    triangles: 105370,
    compressedBytes: 888210,
    compressedSha256: '182fd3b511e77598bf081a631c3c332ac8a7c14c165212d1d8c2a3a2c037a877',
    bytes: 2052220,
    sha256: '90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7',
  }),
  detailed: Object.freeze({
    url: '/review/fdi31-interface-locked-20261027/A_1_31_T2_SEG_na__layered.glb.gz',
    triangles: 1328980,
    compressedBytes: 7654030,
    compressedSha256: 'fdcdfcceb8816f0cd6f2992a11fb8cfa09331dcbd00a2c7e64f68c832ca2bb1b',
    bytes: 26524356,
    sha256: 'c0884a6bcc8fc6175dd97a99f50e53334024b4eb5e033063c7602358f6da1014',
  }),
});

export function getModel(quality) {
  if (!Object.hasOwn(MODELS, quality)) throw new Error('Unknown model quality');
  return MODELS[quality];
}

export const LAYERS = Object.freeze(['enamel', 'dentin', 'pulp', 'bone']);

export function sourceLayer(name) {
  return LAYERS.find(key => name === `SWIRendo_31_T2/${key}`) ?? null;
}

export async function readBounded(stream, expectedBytes) {
  if (!stream) throw new Error('Missing response body');
  const reader = stream.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > expectedBytes) throw new Error('Exact byte bound exceeded');
      chunks.push(value);
    }
    if (size !== expectedBytes) throw new Error('Exact byte count mismatch');
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    return bytes;
  } catch (error) {
    await reader.cancel().catch(() => {});
    throw error;
  } finally {
    reader.releaseLock();
  }
}

export async function verifyHash(bytes, expected) {
  const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
    value => value.toString(16).padStart(2, '0')).join('');
  if (hash !== expected) throw new Error('Exact model SHA-256 mismatch');
  return hash;
}

export async function loadExactModel(origin, signal, quality = DEFAULT_QUALITY, fetchModel = fetch) {
  const model = getModel(quality);
  const url = new URL(model.url, origin);
  if (url.origin !== origin) throw new Error('Model origin mismatch');
  const response = await fetchModel(url, {credentials: 'omit', redirect: 'error', signal});
  if (!response.ok) throw new Error(`Model HTTP ${response.status}`);
  const compressed = await readBounded(response.body, model.compressedBytes);
  await verifyHash(compressed, model.compressedSha256);
  if (typeof DecompressionStream === 'undefined') throw new Error('Gzip decompression unavailable');
  const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'));
  const bytes = await readBounded(stream, model.bytes);
  await verifyHash(bytes, model.sha256);
  return bytes;
}

export function bindLayers(gltf) {
  const nodes = {};
  // GLTFLoader sanitizes slashes in object names. Bind original JSON node names
  // through loader associations instead of assuming the display name is exact.
  gltf.scene.traverse(object => {
    if (!object.isMesh) return;
    const nodeIndex = gltf.parser.associations.get(object)?.nodes;
    const key = sourceLayer(gltf.parser.json.nodes[nodeIndex]?.name);
    if (!key || nodes[key]) throw new Error('Unexpected or duplicate source layer');
    nodes[key] = object;
  });
  if (Object.keys(nodes).length !== LAYERS.length) throw new Error('Missing source layer');
  return nodes;
}
