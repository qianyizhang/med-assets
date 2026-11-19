export const FDI31_ID = 'swirendo_fdi31';
const BALANCED_NAME = 'FDI31-balanced.glb';
const BALANCED_PATH = `models/${FDI31_ID}/exports/balanced-20261028/${BALANCED_NAME}`;
const GLB_TYPE = 'model/gltf-binary';

export function findBalancedExport(media) {
  return media.find(file => file.path === BALANCED_PATH);
}

export async function fetchBalancedGlb(file, signal) {
  const options = { signal, redirect: 'error' };
  const index = await fetch('/assets/index.json', options);
  if (!index.ok) throw new Error('Asset index unavailable.');

  const { assets } = await index.json();
  const asset = assets.find(entry => entry.path === BALANCED_PATH);
  if (asset?.name !== BALANCED_NAME || asset.mediaType !== GLB_TYPE
      || asset.bytes !== file.bytes || asset.sha256 !== file.sha256
      || !/^[a-f0-9]{64}$/u.test(asset.sha256)) {
    throw new Error('Balanced export has no matching public delivery entry.');
  }

  const response = await fetch(`/assets/${asset.sha256}/${asset.name}`, { ...options, cache: 'reload' });
  if (!response.ok || response.headers.get('content-type') !== GLB_TYPE) {
    throw new Error('Balanced GLB unavailable.');
  }

  const blob = await response.blob();
  if (blob.size !== asset.bytes) throw new Error('Balanced GLB has an unexpected size.');
  const digest = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer());
  const sha256 = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
  if (sha256 !== asset.sha256) throw new Error('Balanced GLB failed its integrity check.');
  return { blob, name: asset.name };
}
