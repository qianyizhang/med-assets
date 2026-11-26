import * as THREE from '../vendor/build/three.module.js';
import { loadMesh } from '../scene.js';

export const axes = [
  ['fidelity', 'Fidelity to evidence'], ['form', 'Form and surface'],
  ['readability', 'Teaching readability'], ['economy', 'Mesh economy'],
];
const study = new URL('../', location.href);
export const studyURL = (path) => new URL(path.replace(/^\.\.\//, ''), study).href;

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

function childMeshes(node, skin, parent = '', path = '') {
  if (!node.visible) return [];
  const context = node.name || parent;
  if (!node.isMesh) return node.children.flatMap((child, i) => childMeshes(child, skin, context, path + '/' + i));
  if (!node.geometry?.attributes?.position || node.material?.isMeshBasicMaterial) return [];
  const name = node.name || (node === skin ? 'Patient exterior' : '');
  return [{ node, path, name, label: name || (context ? context + ' · mesh ' : 'Unnamed anatomical mesh ') + path.slice(1),
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

export async function caseModel(entry, chapterId) {
  const url = studyURL(entry.url);
  const record = entry.record ?? await read(url.replace(/\.html(?:[?#].*)?$/, '-sweep.html'), 'text').then((html) =>
    JSON.parse(new DOMParser().parseFromString(html, 'text/html').querySelector('#record').textContent));
  const modules = new URL('cases/' + entry.owner + '/', study);
  const [{ chapters }, { createCaseModel }] = await Promise.all([
    import(new URL('playable.js', modules)), import(new URL('playable-scene.js', modules)),
  ]);
  const sections = chapters(record);
  return { sections, model: await createCaseModel(record, sections.find(({ id }) => id === chapterId) ?? sections[0]) };
}

function rowBase(source, entry, chapter = {}) {
  return { source, case: entry.id, family: entry.family, title: entry.title, chapter: chapter.id ?? '',
    chapterTitle: chapter.title ?? '', url: studyURL(entry.url), frame: chapter.evidenceFrame };
}

function fileParts(source, entry, config, base, chapter) {
  const items = [{ id: 'torso', label: 'Patient exterior' }, ...config.parts];
  return items.map(({ id, label, color }) => ({
    ...rowBase(source, entry, chapter), part: id, label, occurrence: 1, color,
    mesh: new URL(config.meshPaths?.[id] ?? new URL('scenes/' + id + '.mesh', new URL(config.assetRoot, base)), base).href,
    scale: config.voxelMm ?? 1.5,
  }));
}

export function sweepRows() {
  if (typeof abdomenTours === 'undefined') throw Error('Sweep catalogue unavailable.');
  return abdomenTours.flatMap((sweep) => fileParts('sweep', {
    ...sweep, family: sweep.bodyRegion ?? 'Abdomen', url: 'index.html?sweep=' + sweep.id,
  }, sweep, study));
}

export async function aaaRows() {
  const base = new URL('tours/aaa/', study);
  const records = await Promise.allSettled(['aaa-negative', 'aaa-positive', 'aaa-indeterminate'].map(async (id) => {
    const [scene, record] = await Promise.all([read(new URL(id + '.scene.json', base)), read(new URL(id + '.json', base))]);
    return Object.entries(scene).flatMap(([chapter, { config }]) => fileParts('aaa', {
      id, family: 'aaa', title: record.title, url: 'tours/aaa/' + id + '.html',
    }, config, base, { id: chapter, title: chapter.replaceAll('-', ' '), evidenceFrame: 14 }));
  }));
  return { rows: records.flatMap((entry) => entry.status === 'fulfilled' ? entry.value : []),
    issues: records.filter((entry) => entry.status === 'rejected').map(({ reason }) => reason.message) };
}

export async function caseRows(entry) {
  const { sections, model } = await caseModel(entry);
  try {
    return sections.flatMap((chapter) => {
      model.update(chapter, chapter.evidenceFrame);
      model.anatomy.updateMatrixWorld(true);
      return meshParts(model).map(({ node, ...part }) => {
        const { geometry } = node;
        const { position } = geometry.attributes;
        const binding = [
          entry.id, part.path, part.part, geometry.id, position.uuid ?? '', position.version,
          geometry.index?.version ?? '', ...node.matrixWorld.elements,
        ].join('/');
        return { ...rowBase('case', entry, chapter), ...part, binding, color: node.material?.color?.getStyle() };
      });
    });
  } finally {
    if (model.dispose) model.dispose();
    else dispose(model.anatomy);
  }
}

export function rowID(row) {
  return [row.source, row.case, row.chapter ?? '', row.part, row.occurrence ?? 1].map(encodeURIComponent).join('/');
}

export async function isolatedMesh(row, entries) {
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
