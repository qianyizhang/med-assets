import * as THREE from '../vendor/build/three.module.js';
import { loadMesh } from '../scene.js';
import { caseModel, dispose, meshParts } from './assets-data.js';

export function acquisitionKey(row) {
  return JSON.stringify([row.source, row.case, row.chapter ?? '', row.frame ?? null]);
}

async function packagedScene(rows) {
  const object = new THREE.Group();
  const parts = [];
  const issues = [];
  const result = await Promise.allSettled(rows.map(async (row) => {
    const geometry = await loadMesh(row.part, row.mesh);
    const opacity = row.opacity ?? 1;
    const material = new THREE.MeshStandardMaterial({
      color: row.color ?? '#bba58e',
      opacity,
      transparent: opacity < 1 || row.surfacePart,
      depthWrite: opacity === 1 && !row.surfacePart,
      roughness: row.skin ? .95 : .85,
      polygonOffset: Boolean(row.surfacePart),
      polygonOffsetFactor: -1,
      polygonOffsetUnits: -1,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = row.label;
    mesh.scale.setScalar(row.scale);
    mesh.renderOrder = row.renderOrder ?? 0;
    return { row, object: mesh };
  }));
  for (const [i, entry] of result.entries()) {
    if (entry.status === 'rejected') {
      issues.push(rows[i].label + ' · ' + entry.reason.message);
    } else {
      const part = entry.value;
      object.add(part.object);
      parts.push(part);
    }
  }
  return { object, parts, helpers: [], issues, dispose: () => dispose(object) };
}

async function modeledScene(selected, rows, entry) {
  if (!entry) throw Error('The case is unavailable in the assembled inventory.');
  const { model, sections } = await caseModel(entry, selected.chapter);
  const release = () => {
    if (model.dispose) model.dispose();
    else dispose(model.anatomy);
  };
  try {
    const chapter = sections.find(({ id }) => id === selected.chapter);
    if (!chapter) throw Error('The acquisition chapter is unavailable.');
    const pose = model.update(chapter, selected.frame ?? chapter.evidenceFrame);
    model.anatomy.updateMatrixWorld(true);

    const indexed = new Map(rows.map((row) => [row.path, row]));
    const parts = [];
    const issues = [];
    for (const { node, path, part, occurrence } of meshParts(model)) {
      const row = indexed.get(path);
      if (!row || row.part !== part || row.occurrence !== occurrence) {
        issues.push('Unbound acquisition part · ' + part);
        continue;
      }
      parts.push({ row, object: node });
      indexed.delete(path);
    }
    for (const row of indexed.values()) issues.push('Part unavailable at this frame · ' + row.label);
    const bound = new Set(parts.map((part) => part.object));
    const helpers = [];
    model.anatomy.traverseVisible((node) => {
      if ((node.isMesh || node.isLine || node.isPoints) && !bound.has(node)) helpers.push(node);
    });
    // Acquisition annotations remain owned by their source model but are
    // outside the inventory visibility controls used by this inspector.
    for (const helper of helpers) helper.visible = false;
    return { object: model.anatomy, parts, pose, helpers, issues, dispose: release };
  } catch (error) {
    release();
    throw error;
  }
}

// Keep each original node in its parent hierarchy. A scene, an asset and one
// part can therefore share the same camera and acquisition-space coordinates.
export async function acquireScene(selected, inventory, entries) {
  const key = acquisitionKey(selected);
  const rows = [...(inventory instanceof Map ? inventory.values() : inventory)]
    .filter((row) => acquisitionKey(row) === key);
  if (!rows.length) throw Error('No geometry is available for this acquisition.');
  const result = selected.mesh
    ? await packagedScene(rows)
    : await modeledScene(selected, rows, entries.get(selected.case));
  if (!result.parts.length) {
    result.dispose();
    throw Error(result.issues.join(' · ') || 'The acquisition has no available parts.');
  }
  result.object.updateMatrixWorld(true);
  return { ...result, key };
}
