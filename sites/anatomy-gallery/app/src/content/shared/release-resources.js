import { assetRoute, assetsByRoute, HASH } from './asset-index.mjs';

export function compileResources({ selection, publicIndex, localDelivery, legacyDental, archive, reviews }) {
  const published = assetsByRoute(publicIndex);
  const resources = new Map();
  if (selection === 'published') return [];
  function add(file, options = {}) {
    const { name = file.path.split('/').at(-1), sha256, bytes, mediaType } = file;
    const url = options.url ?? assetRoute({ sha256, name });
    if (!HASH.test(sha256) || !Number.isSafeInteger(bytes) || bytes < 1 || !mediaType) {
      throw Error('Release resource has no verified identity: ' + file.path);
    }
    if (url.startsWith('/assets/')) {
      assetsByRoute({ assets: [{ name, sha256, bytes, mediaType }] });
    } else if (url !== '/' + file.path && url !== '/review-evidence/' + sha256 + '/' + encodeURIComponent(name)) {
      throw Error('Invalid release resource address: ' + url);
    }
    const previous = resources.get(url) ?? published.get(url);
    if (previous && (previous.sha256 !== sha256 || previous.bytes !== bytes || previous.mediaType !== mediaType)) {
      throw Error('Conflicting resource identities at ' + url);
    }
    // A candidate read must never shadow a published write admission.
    if (!published.has(url)) resources.set(url, { ...file, ...options, url, name, sha256, bytes, mediaType });
  }
  function model(file) {
    if (!file) throw Error('Missing release model identity.');
    const mediaType = ({ glb: 'model/gltf-binary', blend: 'application/octet-stream' })[file.path.split('.').at(-1)];
    add({ ...file, mediaType });
  }

  for (const file of legacyDental.assets) add(file, { localOnly: true });
  for (const file of archive) add(file, { localOnly: true });
  for (const file of localDelivery.assets) add(file);
  for (const file of localDelivery.receipts) add(file, { url: '/' + file.path, immutable: false, inline: true, sandbox: true });
  for (const row of reviews.campaign ?? []) {
    if (row.route || row.target || row.maintained) model(row.export);
    if (row.refinement?.candidate?.download) model(row.refinement.candidate);
    for (const file of [...row.sources, ...row.views, ...(row.releaseEvidence ?? [])]) {
      if (file.url?.startsWith('/review-evidence/')) add(file, { url: file.url, sandbox: true, inline: true });
    }
  }
  return [...resources.values()].sort((a, b) => a.url.localeCompare(b.url));
}
