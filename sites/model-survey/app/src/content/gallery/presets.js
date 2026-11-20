import { parts, revisions } from './catalog.js';

// A preset version freezes the scene recipe as well as its model identity.
export const sceneVersion = 'adrenal-v1';
export function baseView(revision, part = 'All structures') {
  return {
    version: sceneVersion,
    revision,
    sha256: revisions[revision].sha256,
    part,
    material: 'Tissue',
    light: 1,
    camera: null,
  };
}
function vector(v) {
  return Array.isArray(v) && v.length === 3 && v.every((n) => Number.isFinite(n) && Math.abs(n) <= 100);
}
export function validView(v) {
  return (
    v &&
    v.version === sceneVersion &&
    Object.hasOwn(revisions, v.revision) &&
    revisions[v.revision].sha256 === v.sha256 &&
    ['All structures', ...parts].includes(v.part) &&
    ['Tissue', 'Neutral'].includes(v.material) &&
    [0.75, 1, 1.25].includes(v.light) &&
    (v.camera === null ||
      (vector(v.camera.position) &&
        vector(v.camera.target) &&
        v.camera.position.some((n, i) => Math.abs(n - v.camera.target[i]) > 1e-7) &&
        Number.isFinite(v.camera.height) &&
        v.camera.height >= 0.00001 &&
        v.camera.height <= 100))
  );
}
export function stagePath(v) {
  if (!validView(v)) throw Error('This scene has no shareable preset.');
  return 'stage/' + sceneVersion + '?view=' + encodeURIComponent(JSON.stringify(v));
}
export function readView(query) {
  const raw = new URLSearchParams(query).get('view');
  if (!raw || raw.length > 1600) return null;
  try {
    const view = JSON.parse(raw);
    return validView(view) ? view : null;
  } catch {
    return null;
  }
}
