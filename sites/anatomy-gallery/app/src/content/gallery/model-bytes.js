import { assetUrl } from './catalog.js';

export async function fetchModelBytes(asset, signal) {
  const response = await fetch(assetUrl(asset), { signal, redirect: 'error' });
  if (!response.ok) throw Error('The pinned export is unavailable.');
  const bytes = await response.arrayBuffer();
  if (bytes.byteLength !== asset.bytes) throw Error('The export has a different size.');
  const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (b) =>
    b.toString(16).padStart(2, '0'),
  ).join('');
  if (hash !== asset.sha256) throw Error('The export differs from the pinned revision.');
  return bytes;
}
