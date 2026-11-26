import * as THREE from '../vendor/build/three.module.js';
import { loadMesh } from '../scene.js';
import { classifyAsset, geometryDigest, regionFor, regions } from './assets-identity.js';
import { abdomenReferenceNotice, abdomenRequirements, missingDonor } from './assets-abdomen.js';

import { examRequirements, selectsRetained } from './assets-exams.js';

export const axes = [
  ['fidelity', 'Fidelity to evidence'], ['form', 'Form and surface'],
  ['readability', 'Teaching readability'], ['economy', 'Mesh economy'],
];
const study = new URL('../', location.href);
export const studyURL = (path) => new URL(path.replace(/^\.\.\//, ''), study).href;
export { regions };
let teachingTours = [];
let sweepInventory;

export function setTeachingTours(tours = []) {
  teachingTours = tours;
  sweepInventory = undefined;
}

export async function read(url, type = 'json') {
  const response = await fetch(url);
  if (!response.ok) throw Error(response.status + ' · ' + new URL(url, location.href).pathname);
  return response[type]();
}

export function dispose(object) {
  const geometries = new Set(), materials = new Set();
  object?.traverse((node) => {
    if (node.geometry) geometries.add(node.geometry);
    for (const material of [].concat(node.material ?? [])) materials.add(material);
  });
  geometries.forEach((geometry) => geometry.dispose());
  materials.forEach((material) => material.dispose());
}

function childMeshes(node, skin, parent = '', path = '', inSkin = false) {
  if (!node.visible) return [];
  const exterior = node === skin || inSkin;
  const context = node.name || parent;
  if (!node.isMesh) return node.children.flatMap((child, i) => childMeshes(child, skin, context, path + '/' + i, exterior));
  if (!node.geometry?.attributes?.position?.count || node.material?.isMeshBasicMaterial) return [];
  const name = node.name || (exterior ? 'Patient exterior' : '');
  return [{ node, path, name, skin: exterior, label: name || (context ? context + ' · mesh ' : 'Unnamed anatomical mesh ') + path.slice(1),
    triangles: Math.floor((node.geometry.index?.count ?? node.geometry.attributes.position.count) / 3) }];
}

export function meshParts(model) {
  const seen = new Map();
  return childMeshes(model.anatomy, model.skin).map((part) => {
    const occurrence = part.name ? (seen.get(part.name) ?? 0) + 1 : 1;
    seen.set(part.name, occurrence);
    return { ...part, occurrence, part: part.name || part.path };
  });
}

async function caseRecord(entry) {
  const url = studyURL(entry.url);
  return entry.record ?? await read(url.replace(/\.html(?:[?#].*)?$/, '-sweep.html'), 'text').then((html) =>
    JSON.parse(new DOMParser().parseFromString(html, 'text/html').querySelector('#record').textContent));
}

export async function caseModel(entry, chapterId) {
  if (entry.family === 'abdomen') throw Error('This workbench uses original abdomen reference anatomy.');
  const record = await caseRecord(entry);
  const modules = new URL('cases/' + entry.owner + '/', study);
  const [{ chapters }, { createCaseModel }] = await Promise.all([
    import(new URL('playable.js', modules)), import(new URL('playable-scene.js', modules)),
  ]);
  const sections = chapters(record);
  return { sections, model: await createCaseModel(record, sections.find(({ id }) => id === chapterId) ?? sections[0]) };
}

function rowBase(source, entry, chapter = {}) {
  const relevant = teachingTours.filter((tour) => source === 'sweep' ? tour.sweepIds?.includes(entry.id)
    : (tour.caseId ?? tour.id) === entry.id);
  const region = relevant[0]?.region ?? regionFor(entry.family);
  const teachingSelections = relevant.map((tour) => {
    const url = new URL(studyURL(tour.url));
    const section = tour.sections?.find(({ sweep }) => sweep === entry.id);
    if (section) {
      url.searchParams.set('chapter', section.id);
      url.searchParams.set('frame', section.start);
    }
    return { id: tour.id, label: tour.title, url: url.href, kind: tour.sweepIds ? 'orientation' : 'case',
      ...(tour.sweepIds ? {} : { family: entry.family }) };
  });
  if (source === 'sweep' || !teachingSelections.length) {
    const kind = source === 'sweep' ? 'sweep' : 'case';
    teachingSelections.push({ id: source === 'sweep' ? 'sweep:' + entry.id : entry.id, label: entry.title,
      url: studyURL(entry.url), kind, ...(kind === 'case' ? { family: entry.family } : {}) });
  }
  return { source, case: entry.id, family: entry.family, title: entry.title, chapter: chapter.id ?? '',
    chapterTitle: chapter.title ?? '', url: studyURL(entry.url), frame: chapter.evidenceFrame,
    region, regionLabel: regions[region], teachingSelections };
}

const packedDigests = new Map();

function fileDigest(url, scale) {
  const key = url + '\n' + scale;
  if (!packedDigests.has(key)) {
    const pending = read(url, 'arrayBuffer').then((bytes) => {
      const view = new DataView(bytes);
      const count = view.getUint32(0, true), faces = view.getUint32(4, true);
      const start = 8 + count * 12;
      if (!count || !faces || start + faces * 12 !== bytes.byteLength) throw Error('Invalid mesh structure.');
      return geometryDigest(count,
        (vertex, axis) => Math.fround(view.getFloat32(8 + (vertex * 3 + axis) * 4, true) * scale),
        faces * 3, (i) => view.getUint32(start + i * 4, true));
    });
    packedDigests.set(key, pending.catch((error) => {
      packedDigests.delete(key);
      throw error;
    }));
  }
  return packedDigests.get(key);
}

const geometryCache = new WeakMap();

function liveDigest(node) {
  const geometry = node.geometry;
  const { position } = geometry.attributes;
  const index = geometry.index;
  const m = node.matrixWorld.elements;
  const linear = [m[0], m[4], m[8], m[1], m[5], m[9], m[2], m[6], m[10]];
  const key = [position.version ?? position.data?.version, index?.version, ...linear].join('/');
  if (!geometryCache.has(geometry)) geometryCache.set(geometry, { position, index, uses: new Map() });
  let cache = geometryCache.get(geometry);
  if (cache.position !== position || cache.index !== index) {
    cache = { position, index, uses: new Map() };
    geometryCache.set(geometry, cache);
  }
  if (!cache.uses.has(key)) {
    cache.uses.set(key, geometryDigest(position.count,
      (vertex, axis) => position.getComponent(vertex, axis),
      index?.count ?? position.count, (i) => index?.getX(i) ?? i, linear));
  }
  return cache.uses.get(key);
}

// Registered tours can point straight to an original sweep's part. Resolve that
// declared reference before assigning a case-model identity to the geometry.
let sweepSources;
function sweepSource(mesh, part) {
  if (!sweepSources) {
    sweepSources = new Map();
    for (const config of typeof abdomenTours === 'undefined' ? [] : abdomenTours) {
      for (const id of ['torso', ...config.parts.map(({id}) => id)]) {
        const path = config.meshPaths?.[id] ?? new URL('scenes/' + id + '.mesh', new URL(config.assetRoot, study));
        sweepSources.set(new URL(path, study).href + '#' + id, config);
      }
    }
  }
  return sweepSources.get(mesh + '#' + part);
}

async function bind(row, skin, config, digest) {
  const donor = row.source === 'aaa' && sweepSource(row.mesh, row.part);
  const identity = donor
    ? classifyAsset({ ...row, source: 'sweep', region: regionFor(donor.bodyRegion), family: donor.bodyRegion }, skin, donor)
    : classifyAsset(row, skin, config);
  let meshDigest = null;
  let identityIssue;
  try {
    meshDigest = await digest;
  } catch (error) {
    identityIssue = error.message;
  }
  const variantId = [identity.assetId, identity.partId, meshDigest ?? ('unavailable/' + rowID(row))].join('/');
  const original = donor && {
    source: 'sweep', case: donor.id, part: row.part, chapter: '', occurrence: 1,
    url: studyURL('index.html?sweep=' + donor.id), label: donor.title, assetId: identity.assetId, assetRevision: identity.assetRevision,
    sourceSpace: donor.case ?? 's1233', meshDigest, registration: 'registered-exact',
  };
  return { ...row, ...identity, meshDigest, identityIssue, variantId, binding: variantId,
    ...(original ? { donor: original } : {}) };
}

async function fileParts(source, entry, config, base, chapter) {
  const items = [{ id: 'torso', label: 'Patient exterior', color: '#be9885', opacity: .32 }, ...config.parts];
  return Promise.all(items.map(({ id, label, color, opacity }, order) => {
    const mesh = new URL(config.meshPaths?.[id] ?? new URL('scenes/' + id + '.mesh', new URL(config.assetRoot, base)), base).href;
    const scale = config.voxelMm ?? 1.5;
    const surfacePart = Boolean(config.surfaceParts?.includes(id));
    const renderOrder = id === 'torso' ? 4 : surfacePart ? 5 + (order - 1) / config.parts.length : order / items.length * 2;
    return bind({ ...rowBase(source, entry, chapter), part: id, label, occurrence: 1, color, mesh, scale, renderOrder,
      surfacePart, opacity: surfacePart ? .32 : opacity ?? 1, skin: id === 'torso',
      ...(source === 'sweep' ? { sourceSpace: config.case ?? 's1233' } : {}) },
      id === 'torso', config, fileDigest(mesh, scale));
  }));
}

async function buildSweepInventory() {
  if (typeof abdomenTours === 'undefined') throw Error('Sweep catalogue unavailable.');
  const sweeps = await Promise.all(abdomenTours.map((sweep) => fileParts('sweep', {
    ...sweep, family: sweep.bodyRegion ?? 'Abdomen', url: 'index.html?sweep=' + sweep.id,
  }, sweep, study)));
  return sweeps.flat();
}

export function sweepRows() {
  sweepInventory ??= buildSweepInventory();
  return sweepInventory;
}

export async function aaaRows() {
  const base = new URL('tours/aaa/', study);
  const { chapters } = await import('../cases/vascular/playable.js');
  const records = await Promise.allSettled(['aaa-negative', 'aaa-positive', 'aaa-indeterminate'].map(async (id) => {
    const record = await read(new URL(id + '.json', base));
    const entry = { id, family: 'aaa', title: record.title, url: 'tours/aaa/' + id + '.html',
      chapters: chapters(record) };
    const scene = await read(new URL(id + '.scene.json', base)).catch(() => ({}));
    const packed = await Promise.all(entry.chapters.map(async (chapter) => {
      const item = scene[chapter.id];
      return item ? fileParts('aaa', entry, item.config, base, chapter) : [];
    }));
    return reconcileRows(entry, packed.flat());
  }));
  return { rows: records.flatMap((entry) => entry.status === 'fulfilled' ? entry.value : []),
    issues: records.filter((entry) => entry.status === 'rejected').map(({ reason }) => reason.message) };
}

export async function caseRows(entry) {
  if (entry.family === 'abdomen') return abdomenRows(entry);
  const references = new Map(entry.chapters.map((chapter) => [chapter.id, examRequirements(entry, chapter)]));
  if (![...references.values()].some((items) => items.some((item) => item.source === 'retained'))) {
    return reconcileRows(entry, [], references);
  }
  const loaded = await caseModel(entry).catch((error) => ({ error }));
  if (loaded.error) return reconcileRows(entry, [], references, loaded.error.message);
  const { sections, model } = loaded;
  try {
    const rows = sections.flatMap((chapter) => {
      const items = references.get(chapter.id) ?? [];
      if (!items.some((item) => item.source === 'retained')) return [];
      model.update(chapter, chapter.evidenceFrame);
      model.anatomy.updateMatrixWorld(true);
      return meshParts(model).filter(({ part }) => items.some((item) => selectsRetained(item, part)))
        .map(({ node, skin, ...part }) =>
          bind({ ...rowBase('case', entry, chapter), ...part, skin, color: node.material?.color?.getStyle() },
            skin, undefined, liveDigest(node)));
    });
    return reconcileRows(entry, await Promise.all(rows), references);
  } finally {
    if (model.dispose) model.dispose();
    else dispose(model.anatomy);
  }
}

function gapRow(entry, chapter, detail) {
  const assetId = detail.assetId?.replace(/^(library\/[^/]+)\/.+$/, '$1');
  return { ...rowBase('requirement', entry, chapter), ...detail, assetId,
    partId: detail.partId ?? detail.part, partLabel: detail.partLabel ?? detail.label, occurrence: 1 };
}

function referenceRow(entry, chapter, reference, part) {
  const sourceSpace = part.sourceSpace ?? part.assetId.split(':').slice(0, 2).join(':');
  const donor = {
    source: part.source, case: part.case, part: part.part, chapter: part.chapter, occurrence: part.occurrence,
    url: part.url, label: part.title ?? part.label, sourceSpace, assetId: part.assetId, assetRevision: part.assetRevision,
    sourceNode: part.sourceNode, sourceSha256: part.sourceSha256, meshDigest: part.meshDigest,
  };
  return { ...part, ...rowBase('case', entry, chapter), donor, sourceSpace, legacyParts: reference.legacyParts,
    referenceScope: reference.referenceScope,
    sourceNotice: entry.family === 'abdomen' ? abdomenReferenceNotice :
      'Independent source anatomy in its original coordinates. This reference is separate from the worked acquisition.' };
}

function unavailableRetained(entry, chapter, part, issue) {
  const identity = classifyAsset({ ...rowBase(entry.family === 'aaa' ? 'aaa' : 'case', entry, chapter),
    part, label: part }, false);
  return gapRow(entry, chapter, { ...identity, status: 'missing', part, label: identity.partLabel,
    missingReason: issue ?? 'This named surface is unavailable in the delivered case model.' });
}

async function reconcileRows(entry, retainedRows, references, retainedIssue) {
  const [sweeps, gallery] = await Promise.all([sweepRows().catch(() => []), galleryRows()]);
  const original = new Map(sweeps.map((row) => [row.case + '/' + row.part, row]));
  const extra = new Map(gallery.map((row) => [row.part, row]));
  const rows = entry.chapters.flatMap((chapter) => {
    const items = references?.get(chapter.id) ?? examRequirements(entry, chapter);
    const acquisitionNotes = items.filter((reference) => reference.source === 'acquisition-note');
    return items.filter((reference) => reference.source !== 'acquisition-note').flatMap((reference) => {
      if (reference.source === 'retained') {
        const matches = retainedRows.filter((row) => row.chapter === chapter.id && row.meshDigest
          && selectsRetained(reference, row.part));
        const bound = matches.map((row) => ({ ...row, referenceKind: 'retained',
          sourceSpace: 'worked:' + entry.id, referenceScope: reference.referenceScope, sourceNotice: reference.referenceScope }));
        const present = new Set(matches.map(({ part }) => part));
        const missing = Array.isArray(reference.parts) ? reference.parts.filter((part) => !present.has(part))
          : matches.length ? [] : [chapter.title];
        return [...bound, ...missing.map((part) => unavailableRetained(entry, chapter, part, retainedIssue))];
      }
      const part = reference.source === 'gallery' ? extra.get(reference.part) : original.get(reference.key + '/' + reference.part);
      if (!part?.meshDigest) return gapRow(entry, chapter, reference.status ? reference : missingDonor(reference,
        part?.identityIssue ?? 'The specified reference mesh is unavailable in this build.', part));
      return referenceRow(entry, chapter, reference, part);
    }).map((row) => acquisitionNotes.length ? { ...row, acquisitionNotes } : row);
  });
  return [...new Map(rows.map((row) => [rowID(row), row])).values()];
}

let galleryInventory;
function galleryRows() {
  galleryInventory ??= read(new URL('development/gallery-donors.json', study)).then((rows) =>
    Promise.all(rows.map(async (row) => {
      const mesh = studyURL(row.mesh);
      let meshDigest;
      let identityIssue;
      try {
        meshDigest = await fileDigest(mesh, row.scale);
      } catch (error) {
        identityIssue = error.message;
      }
      const assetId = row.assetId.replace(/^(library\/[^/]+)\/.+$/, '$1');
      const variantId = meshDigest ? [assetId, row.partId, meshDigest].join('/') : undefined;
      return { ...row, assetId, mesh, meshDigest, identityIssue, variantId, binding: variantId };
    }))).catch(() => []);
  return galleryInventory;
}

async function abdomenRows(entry) {
  if (!entry.chapters?.length) throw Error('The abdomen case has no delivered chapter list.');
  const references = new Map(entry.chapters.map((chapter) => [chapter.id, abdomenRequirements(chapter.id)]));
  return reconcileRows(entry, [], references);
}

export function rowID(row) {
  return [row.source, row.case, row.chapter ?? '', row.part, row.occurrence ?? 1].map(encodeURIComponent).join('/');
}

export async function isolatedMesh(row, entries) {
  if (row.source === 'requirement') throw Error(row.missingReason);
  if (row.mesh) {
    const geometry = await loadMesh(row.part, row.mesh);
    geometry.scale(row.scale, row.scale, row.scale);
    return geometry;
  }
  const { model, sections } = await caseModel(entries.get(row.case), row.chapter);
  try {
    const chapter = sections.find(({ id }) => id === row.chapter);
    model.update(chapter, chapter.evidenceFrame);
    const part = meshParts(model).find((item) => item.path === row.path);
    if (!part) throw Error('The mesh is no longer present at the evidence frame.');
    model.anatomy.updateMatrixWorld(true);
    return part.node.geometry.clone().applyMatrix4(part.node.matrixWorld);
  } finally {
    if (model.dispose) model.dispose();
    else dispose(model.anatomy);
  }
}

export function assessmentScore(record, key) {
  const value = record?.scores?.[key];
  return !record?.prior && record?.task && record?.reviewer && record?.reviewedOn && record?.rubric && record?.revision &&
    record?.scoreEvidence?.[key] && Number.isInteger(value) && value >= 0 && value <= 4 ? value : null;
}

export function bufferBytes(geometry) {
  const arrays = new Set();
  const attributes = Object.values(geometry.attributes);
  for (const attribute of [...attributes, geometry.index].filter(Boolean)) {
    arrays.add(attribute.array ?? attribute.data.array);
  }
  return [...arrays].reduce((total, array) => total + array.byteLength, 0);
}

export function meshTopology(geometry) {
  const position = geometry.getAttribute('position');
  const index = geometry.getIndex();
  const welds = new Map();
  const ids = new Uint32Array(position.count);
  for (let i = 0; i < position.count; i++) {
    const key = [position.getX(i), position.getY(i), position.getZ(i)].join('/');
    if (!welds.has(key)) welds.set(key, welds.size);
    ids[i] = welds.get(key);
  }
  const count = welds.size;
  const parents = Uint32Array.from({ length: count }, (_, i) => i);
  const used = new Uint8Array(count);
  function root(value) {
    while (parents[value] !== value) {
      parents[value] = parents[parents[value]];
      value = parents[value];
    }
    return value;
  }
  const edges = new Map();
  function edge(a, b) {
    const key = Math.min(a, b) * count + Math.max(a, b);
    edges.set(key, (edges.get(key) ?? 0) + 1);
  }
  let collapsed = 0;
  const vertex = (i) => ids[index ? index.getX(i) : i];
  for (let i = 0, length = index?.count ?? position.count; i + 2 < length; i += 3) {
    const a = vertex(i), b = vertex(i + 1), c = vertex(i + 2);
    if (a === b || b === c || a === c) {
      collapsed++;
      continue;
    }
    used[a] = used[b] = used[c] = 1;
    parents[root(b)] = root(a);
    parents[root(c)] = root(a);
    edge(a, b);
    edge(b, c);
    edge(c, a);
  }
  const components = new Set();
  let open = 0;
  let nonmanifold = 0;
  for (let i = 0; i < count; i++) if (used[i]) components.add(root(i));
  for (const faces of edges.values()) {
    if (faces === 1) open++;
    if (faces > 2) nonmanifold++;
  }
  return { components: components.size, open, nonmanifold, collapsed };
}
