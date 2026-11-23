export const MAX_ASSET_BYTES = 64_000_000;
export const HASH = /^[a-f0-9]{64}$/u;
const FORMATS = {
  'model/gltf-binary': /\.glb$/iu, 'image/png': /\.png$/iu,
  'image/webp': /\.webp$/iu, 'image/jpeg': /\.(jpg|jpeg)$/iu,
  'application/zip': /\.zip$/u, 'application/gzip': /\.nii\.gz$/iu,
  'application/octet-stream': /\.(blend|raw|nii|nrrd|npz|svg|json)$/iu,
  'audio/wav': /\.wav$/iu, 'video/mp4': /\.mp4$/iu, 'font/ttf': /\.ttf$/iu,
  'model/stl': /\.stl$/iu, 'model/obj': /\.obj$/iu,
};

export const assetRoute = (asset) => `/assets/${asset.sha256}/${asset.name}`;
export function currentPaths(asset) {
  const paths = asset.paths ?? (asset.path ? [asset.path] : []);
  if (!Array.isArray(paths) || paths.some(path => typeof path !== 'string' || !path)) {
    throw new Error('Invalid current delivery paths.');
  }
  return paths;
}

export function assetsByPath(...catalogs) {
  const paths = new Map();
  for (const { assets } of catalogs) {
    for (const asset of assets) {
      for (const path of currentPaths(asset)) {
        if (paths.has(path)) throw new Error('Ambiguous current delivery path: ' + path);
        paths.set(path, path === asset.path ? asset : { ...asset, path });
      }
    }
  }
  return paths;
}

export function assetsByRoute({ assets }) {
  const routes = new Map();
  for (const asset of assets) {
    if (typeof asset.sha256 !== 'string' || !HASH.test(asset.sha256)
      || !Number.isSafeInteger(asset.bytes) || asset.bytes < 1 || asset.bytes > MAX_ASSET_BYTES
      || typeof asset.name !== 'string' || /[^a-zA-Z0-9_.-]/u.test(asset.name)
      || !Object.hasOwn(FORMATS, asset.mediaType)) throw new Error('Invalid published asset.');
    if (!FORMATS[asset.mediaType].test(asset.name)) {
      throw new Error(asset.mediaType === 'application/zip'
        ? 'ZIP assets need a .zip filename.' : 'Asset type and extension differ.');
    }
    const route = assetRoute(asset);
    if (routes.has(route)) throw new Error('Duplicate published asset.');
    routes.set(route, asset);
  }
  return routes;
}
