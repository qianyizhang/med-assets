import { adrenalComparison, adrenalLesson, adrenalScene } from './adrenal-study.js';
import { comparePath, lessonPath, libraryPath, revisions } from './catalog.js';
import { localModels, teachingScenes, trachealLessonScenes } from './local-models.js';

// A preset version freezes the scene recipe as well as its model identity.
export const sceneVersion = adrenalScene.version;
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
export function localView(model) {
  return {
    version: model.scene.version,
    revision: model.revision,
    sha256: model.exports[0].sha256,
    part: model.scene.initialPart ?? 'All structures',
    ...(model.scene.clip ? { phase: 0 } : {}),
    material: model.scene.material ?? 'Tissue',
    light: 1,
    camera: model.scene.camera ?? null,
  };
}

export function localScene(view) {
  return [...localModels, ...teachingScenes, ...trachealLessonScenes]
    .find((model) => model.scene.version === view.version && model.revision === view.revision);
}

export function viewAsset(view) {
  if (view.version === sceneVersion && Object.hasOwn(revisions, view.revision)) return revisions[view.revision];
  return localScene(view)?.exports[0];
}

function vector(v) {
  return Array.isArray(v) && v.length === 3 && v.every((n) => Number.isFinite(n) && Math.abs(n) <= 100);
}
export function validView(v) {
  const asset = v && viewAsset(v);
  const model = asset && localScene(v);
  return (
    !!asset && asset.sha256 === v.sha256 &&
    (model?.scene.groups ? Object.hasOwn(model.scene.groups, v.part) : (v.part === 'All structures' || (model
      ? !model.scene.singleMesh && typeof v.part === 'string' && v.part.length > 0 && v.part.length <= 128
       : adrenalScene.parts.includes(v.part)))) &&
    (model?.scene.clip ? Number.isFinite(v.phase) && v.phase >= 0 && v.phase <= 1 : v.phase === undefined) &&
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
export function stageReturn(path, view) {
  const model = localScene(view);
  if (model) {
    if (path === model.library) return { path, label: 'Return to asset record' };
    if (model.lesson && path === model.lesson) return { path, label: model.returnLabel ?? 'Return to first-fork lesson' };
    return null;
  }
  const { revision } = view;
  if (path === libraryPath(revision)) return { path, label: 'Return to asset record' };
  if (revision === adrenalLesson.revision) {
    const stop = adrenalLesson.stops.find(({ id }) => path === lessonPath + '/' + id);
    if (stop) return { path, label: stop.returnLabel };
  }
  const [record, query] = path?.split('?') ?? [];
  if (
    adrenalComparison.pair.some((input) => input.revision === revision) && record === comparePath &&
    (!query || /^finish=(tissue|neutral)&order=(ab|ba)$/.test(query))
  ) {
    return { path: query ? record + '?' + query : record, label: 'Return to comparison' };
  }
  return null;
}

export function stagePath(v, origin) {
  if (!validView(v)) throw Error('This scene has no shareable preset.');
  const from = stageReturn(origin, v);
  return 'stage/' + v.version + '?view=' + encodeURIComponent(JSON.stringify(v)) +
    (from ? '&from=' + encodeURIComponent(from.path) : '');
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
