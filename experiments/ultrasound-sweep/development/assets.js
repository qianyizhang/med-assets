import * as THREE from '../vendor/build/three.module.js';
import { viewport } from '../scene.js';
import { aaaRows, axes, assessmentScore, bufferBytes, caseRows, dispose, isolatedMesh, meshTopology, read, rowID, sweepRows } from './assets-data.js';

const $ = (id) => document.getElementById(id);
const make = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
const entries = new Map();
const inventory = new Map();
const uses = new Map();
const reviews = new Map();
const uniqueReviews = new Map();
const failures = [];
const pageSize = 36;
let index = 0;
let selection;
let matches = [];
let current;
let linkedSelection = false;
let selectedRequest = 0;
let viewer;
let portrait;
let remaining = 0;
let pendingAAA = true;
let thumbnailRenderer;
const thumbnailCache = new Map();
const waitingThumbnails = [];
let makingThumbnail = false;

const filters = ['query', 'source', 'family', 'assessment', 'expand-uses'];
const familyLabels = {
  aaa: 'AAA screening', abdomen: 'Abdomen and urinary tract', breast: 'Breast and axilla',
  carotid: 'Carotid duplex', thyroid: 'Thyroid and cervical nodes', echo: 'Adult echocardiography',
  'pregnancy-early': 'Early pregnancy', 'pregnancy-first': '11–14-week scan',
  'pregnancy-mid': 'Mid-trimester anatomy', 'pregnancy-late': 'Third-trimester growth',
};
const frameKey = (row) => [row.source, row.case, row.chapter, row.part].join('/');
const counts = new Map();
const assessed = (record) => axes.some(([axis]) => assessmentScore(record, axis) !== null);
const qualified = (record) => axes.every(([axis]) => assessmentScore(record, axis) === 4);
function matchesAssessment(record, rating) {
  switch (rating) {
    case 'assessed': return assessed(record);
    case 'qualified': return qualified(record);
    case 'below': return axes.some(([axis]) => {
      const score = assessmentScore(record, axis);
      return score !== null && score < 4;
    });
    case 'exemplar': return assessed(record) && record.exemplar === true;
    case 'unrated': return !assessed(record);
    default: return true;
  }
}
function linked(row) {
  const caseScope = { ...row, chapter: '' };
  const unique = counts.get(frameKey(row)) === 1;
  return reviews.get(rowID(row)) ?? (unique ? uniqueReviews.get(frameKey(row)) : undefined) ??
    reviews.get(rowID(caseScope)) ?? (unique ? uniqueReviews.get(frameKey(caseScope)) : undefined);
}
const group = (row) => row.source + '/' + row.family;

function recordRows(rows) {
  for (const row of rows) {
    const key = rowID(row);
    if (inventory.has(key)) continue;
    inventory.set(key, row);
    row.binding ??= [row.source, row.case, row.part, row.mesh, row.scale].join('/');
    if (!uses.has(row.binding)) uses.set(row.binding, []);
    uses.get(row.binding).push(row);
    const identity = frameKey(row);
    counts.set(identity, (counts.get(identity) ?? 0) + 1);
  }
}

function rateLabel(record) {
  if (!assessed(record)) return record?.prior ? 'Unrated · prior review' : 'Unrated';
  const values = axes.map(([axis]) => assessmentScore(record, axis));
  const complete = values.every((value) => value !== null);
  if (qualified(record)) return '16/16';
  return complete ? values.reduce((sum, value) => sum + value, 0) + '/16' : 'Partly assessed';
}

function status() {
  const matched = matches.length.toLocaleString();
  const reviewedParts = new Set();
  const qualifiedParts = new Set();
  let reviewedUses = 0;
  let qualifiedUses = 0;
  for (const row of inventory.values()) {
    const record = linked(row);
    if (assessed(record)) {
      reviewedParts.add(row.binding);
      reviewedUses++;
    }
    if (qualified(record)) {
      qualifiedParts.add(row.binding);
      qualifiedUses++;
    }
  }
  const coverage = uses.size.toLocaleString() + ' isolated parts across ' + inventory.size.toLocaleString() + ' acquisition uses';
  const reviews = reviewedParts.size.toLocaleString() + ' assessed parts (' + reviewedUses.toLocaleString() + ' uses)';
  const qualification = qualifiedParts.size.toLocaleString() + ' qualified parts (' + qualifiedUses.toLocaleString() + ' uses)';
  const pending = remaining + Number(pendingAAA);
  $('inventory-status').textContent = [matched + ' matching', coverage, reviews, qualification].join(' · ') +
    (pending ? ' · indexing ' + pending + ' sources' : '');
  $('issues').hidden = failures.length === 0;
  $('issues').querySelector('ul').replaceChildren(...failures.map((failure) => make('li', failure)));
}

function organized(rows) {
  const first = rows.filter((row) => linked(row));
  const buckets = new Map();
  for (const row of rows) {
    if (linked(row)) continue;
    const category = group(row);
    if (!buckets.has(category)) buckets.set(category, []);
    buckets.get(category).push(row);
  }
  const lists = [...buckets.values()];
  for (const list of lists) {
    const context = (row) => /exterior|skin|torso|unnamed/i.test(row.label) ? 1 : 0;
    list.sort((left, right) => context(left) - context(right));
  }
  const longest = Math.max(0, ...lists.map((list) => list.length));
  for (let i = 0; i < longest; i++) {
    for (const list of lists) if (list[i]) first.push(list[i]);
  }
  return first;
}

function thumbnailImage(geometry) {
  if (!thumbnailRenderer) {
    thumbnailRenderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    thumbnailRenderer.setSize(144, 112);
    thumbnailRenderer.setClearColor('#142224');
    thumbnailRenderer.toneMapping = THREE.NeutralToneMapping;
  }
  geometry.computeBoundingBox();
  const center = geometry.boundingBox.getCenter(v(0, 0, 0));
  const size = geometry.boundingBox.getSize(v(0, 0, 0));
  geometry.translate(...center.negate().toArray());
  const radius = Math.max(size.x, size.y, size.z, .001) * .67;
  const image = new THREE.Scene();
  const material = new THREE.MeshStandardMaterial({ color: '#ded3bc', roughness: .72, side: THREE.DoubleSide });
  image.add(new THREE.Mesh(geometry, material), new THREE.HemisphereLight('#e4edef', '#606768', 1.7));
  const key = new THREE.DirectionalLight('#fff1da', 2.0);
  key.position.set(20, 15, 40);
  image.add(key);
  const camera = new THREE.OrthographicCamera(-radius * 1.29, radius * 1.29, radius, -radius, .001, radius * 12);
  camera.position.set(radius * 1.7, radius * 2.6, radius * 1.1);
  camera.up.set(0, 0, 1);
  camera.lookAt(0, 0, 0);
  thumbnailRenderer.render(image, camera);
  material.dispose();
  return thumbnailRenderer.domElement.toDataURL('image/webp', .8);
}

async function pumpThumbnails() {
  if (makingThumbnail) return;
  makingThumbnail = true;
  while (waitingThumbnails.length) {
    const slot = waitingThumbnails.shift();
    if (!slot.isConnected) continue;
    const key = slot.dataset.part;
    const row = inventory.get(key);
    if (!thumbnailCache.has(key)) {
      let geometry;
      try {
        geometry = await isolatedMesh(row, entries);
        thumbnailCache.set(key, thumbnailImage(geometry));
        if (thumbnailCache.size > 90) thumbnailCache.delete(thumbnailCache.keys().next().value);
      } catch {
        thumbnailCache.delete(key);
      } finally {
        geometry?.dispose();
      }
    }
    if (!slot.isConnected) continue;
    const source = thumbnailCache.get(key);
    if (source) {
      const image = make('img');
      image.alt = '';
      image.src = source;
      slot.replaceChildren(image);
    } else {
      slot.textContent = 'Unavailable';
    }
  }
  makingThumbnail = false;
}

const thumbnailObserver = new IntersectionObserver((items) => {
  for (const item of items) {
    if (!item.isIntersecting) continue;
    thumbnailObserver.unobserve(item.target);
    waitingThumbnails.push(item.target);
  }
  pumpThumbnails();
}, { rootMargin: '120px' });
let shownRows = '';

function rowsView(showPageWith) {
  const query = $('query').value.trim().toLowerCase();
  const candidates = [...inventory.values()].filter((row) => {
    const grade = linked(row);
    const rating = $('assessment').value;
    return (!$('source').value || row.source === $('source').value) &&
      (!$('family').value || row.family === $('family').value) &&
      (!query || query.split(/\s+/).every((token) => [row.label, row.title, row.chapterTitle, row.case].join(' ').toLowerCase().includes(token))) &&
      matchesAssessment(grade, rating);
  });
  if ($('expand-uses').checked) {
    matches = organized(candidates);
  } else {
    const unique = new Map();
    const preferred = selection ?? location.hash.slice(1);
    for (const row of candidates) {
      const previous = unique.get(row.binding);
      if (!previous || rowID(row) === preferred ||
          (rowID(previous) !== preferred && !linked(previous) && linked(row))) unique.set(row.binding, row);
    }
    matches = organized([...unique.values()]);
  }
  const total = Math.max(1, Math.ceil(matches.length / pageSize));
  const selectedIndex = showPageWith ? matches.findIndex((row) => rowID(row) === showPageWith) : -1;
  index = selectedIndex >= 0 ? Math.floor(selectedIndex / pageSize) : Math.min(index, total - 1);
  const visible = matches.slice(pageSize * index, pageSize * (index + 1));
  const signature = [selection, ...visible.map((row) => rowID(row) + rateLabel(linked(row)))].join('|');
  if (signature !== shownRows) {
    shownRows = signature;
    const rows = visible.map((row) => {
      const tile = make('li');
      const key = rowID(row);
      const part = make('a');
      part.href = '#' + key;
      part.ariaLabel = [row.label, row.title, row.chapterTitle, rateLabel(linked(row))].filter(Boolean).join(' · ');
      if (key === selection) part.setAttribute('aria-current', 'true');
      const specimen = make('span', undefined, 'specimen');
      specimen.dataset.part = key;
      const record = linked(row);
      const candidate = !record?.prior && record?.comparison?.candidate;
      if (candidate) {
        const image = make('img');
        image.alt = '';
        image.loading = 'lazy';
        image.src = candidate;
        image.addEventListener('error', () => {
          image.remove();
          thumbnailObserver.observe(specimen);
        });
        specimen.append(image);
      } else {
        thumbnailObserver.observe(specimen);
      }
      const grade = make('small', rateLabel(linked(row)), assessed(linked(row)) ? 'rated' : 'unrated');
      part.append(specimen, make('strong', row.label), grade);
      tile.append(part);
      return tile;
    });
    const focused = $('rows').contains(document.activeElement) ? document.activeElement.hash : null;
    $('rows').replaceChildren(...rows);
    if (focused) [...$('rows').querySelectorAll('a')].find((link) => link.hash === focused)?.focus({ preventScroll: true });
  }
  $('empty').hidden = matches.length > 0 || remaining > 0 || pendingAAA;
  $('pagination').hidden = total < 2;
  $('previous').disabled = index === 0;
  $('next').disabled = index + 1 === total;
  $('page').textContent = (index + 1) + ' / ' + total;
  status();
}

function refresh() {
  const family = $('family');
  const value = family.value;
  const names = [...new Set([...inventory.values()].map((row) => row.family))].sort();
  if (names.join() !== [...family.options].slice(1).map((option) => option.value).join()) {
    family.replaceChildren(new Option('All families', ''), ...names.map((name) => new Option(familyLabels[name] ?? name, name)));
    family.value = value || '';
  }
  rowsView();
  const deep = location.hash.slice(1);
  if (deep && selection !== deep && inventory.has(deep)) {
    showPart(deep, true);
  } else if (deep && !remaining && !pendingAAA && !inventory.has(deep)) {
    $('selection').textContent = 'Part unavailable';
    $('selection-context').textContent = 'This link does not resolve to a part in the current inventory.';
    $('preview').hidden = true;
    $('evidence').hidden = true;
  }
}

function evidenceImage(set, name, label) {
  if (!set?.[name]) return null;
  const container = make('figure');
  const caption = make('figcaption', label);
  const image = make('img');
  image.src = set[name];
  image.loading = 'lazy';
  image.alt = label;
  const anchor = make('a');
  anchor.href = image.src;
  anchor.append(image);
  image.addEventListener('error', () => anchor.replaceWith(make('p', 'Evidence image unavailable.', 'unrated')));
  container.append(caption, anchor);
  return container;
}

function evidenceView(row) {
  const section = $('evidence');
  section.replaceChildren(make('h3', 'Assessment'));
  section.hidden = false;
  const record = linked(row);
  const rubric = make('a', 'Scoring rubric');
  rubric.href = 'asset-rubric.md';
  section.append(make('p', rateLabel(record), 'rating'), rubric);
  if (!record) return;
  const task = make('p', record.task);
  const by = [record.reviewer, record.reviewedOn, record.revision].filter(Boolean).join(' · ');
  section.append(task, make('p', by, 'muted'));
  if (record.note) section.append(make('p', record.note));
  if (record.prior) section.append(make('p', 'This record refers to an earlier geometry recipe.', 'muted'));
  const scale = make('dl', undefined, 'scores');
  for (const [key, label] of axes) {
    const rating = assessmentScore(record, key);
    const term = make('dt', label);
    const value = make('dd', rating === null ? 'Unrated' : rating + '/4');
    const before = record.beforeScores?.[key];
    if (Number.isInteger(before) && before >= 0 && before <= 4 && record.beforeEvidence?.[key]) {
      value.append(make('small', 'Baseline ' + before + '/4 · ' + record.beforeEvidence[key]));
    }
    if (record.scoreEvidence?.[key]) value.append(make('small', record.scoreEvidence[key]));
    scale.append(term, value);
  }
  section.append(scale);
  if (record.baseline) section.append(make('p', 'Baseline revision · ' + record.baseline, 'muted'));
  if (record.links?.length) {
    const references = make('div', undefined, 'link-row');
    for (const { label, href } of record.links) {
      const anchor = make('a', label);
      anchor.href = href;
      references.append(anchor);
    }
    section.append(references);
  }
  const sets = [record.comparison, ...(record.comparison?.views ?? [])];
  for (const set of sets) {
    const frames = Object.entries({ baseline: 'Baseline', candidate: record.prior ? 'Reviewed candidate' : 'Candidate', original: 'Original sweep' })
      .map(([name, label]) => evidenceImage(set, name, set?.[name + 'Label'] ?? label)).filter(Boolean);
    if (!frames.length) continue;
    const view = make('div', undefined, 'comparison');
    view.append(...frames);
    if (set?.label) section.append(make('h4', set.label));
    section.append(view);
  }
}

const v = (x, y, z) => new THREE.Vector3(x, y, z);
const directions = [
  ['Oblique', v(1, 1.6, .9), v(0, 0, 1)], ['Front', v(0, 1, 0), v(0, 0, 1)],
  ['Side', v(1, 0, 0), v(0, 0, 1)], ['Above', v(0, 0, 1), v(0, 1, 0)],
];
const cameraNames = ['oblique', 'coronal', 'sagittal', 'axial'];
for (const [i, [label]] of directions.entries()) {
  const button = make('button', label);
  button.type = 'button';
  button.dataset.camera = cameraNames[i];
  button.onclick = () => viewer?.setViewPreset(cameraNames[i]);
  $('views').append(button);
}

function mount(geometry) {
  geometry.computeBoundingBox();
  const { boundingBox: bounds } = geometry;
  if (bounds.isEmpty()) throw Error('This mesh has empty bounds.');
  const size = bounds.getSize(v(0, 0, 0));
  // Normalize only the viewport transform. Geometry checks use native millimetres.
  const scale = 180 / Math.max(size.x, size.y, size.z, .001);
  const center = bounds.getCenter(v(0, 0, 0));
  const pivot = v(0, 0, 0);
  const presets = Object.fromEntries(directions.map(([, direction, up], i) => [
    cameraNames[i], { direction: direction.clone().normalize(), up: up.clone(), target: pivot.clone(), halfWidth: 112, halfHeight: 112 },
  ]));
  if (!viewer) {
    viewer = viewport($('mesh'), { pivot, presets, shadowTarget: pivot, onViewPresetChange(name) {
      for (const button of $('views').children) button.setAttribute('aria-pressed', String(button.dataset.camera === name));
    } });
  }
  if (portrait) {
    viewer.scene.remove(portrait);
    dispose(portrait);
  }
  portrait = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
    color: '#ded3bc', roughness: .72, side: THREE.DoubleSide,
  }));
  portrait.scale.setScalar(scale);
  portrait.position.copy(center).multiplyScalar(-scale);
  viewer.scene.add(portrait);
  viewer.reframe(pivot, presets);
  viewer.setViewPreset('oblique');
  return size.toArray().map((value) => value.toFixed(1)).join(' × ') + ' mm';
}

function coordinateSelection(row) {
  const grade = linked(row);
  $('query').value = '';
  $('source').value = row.source;
  $('family').value = row.family;
  if (!$('assessment').value || !matchesAssessment(grade, $('assessment').value)) {
    $('assessment').value = assessed(grade) ? 'assessed' : 'unrated';
  }
}

function selectionEvidence(row) {
  $('selection-context').textContent = [row.title, row.chapterTitle, rateLabel(linked(row))].filter(Boolean).join(' · ');
  evidenceView(row);
}

async function showPart(key, fromLink = false) {
  const row = inventory.get(key);
  if (!row) return;
  if (fromLink) coordinateSelection(row);
  linkedSelection = fromLink;
  current = row;
  selection = key;
  const request = ++selectedRequest;
  $('selection').textContent = row.label;
  $('inspector').scrollTop = 0;
  $('preview').hidden = false;
  $('mesh').hidden = true;
  delete $('mesh').dataset.ready;
  $('views').hidden = true;
  $('mesh-help').hidden = true;
  $('mesh-status').textContent = 'Loading isolated mesh…';
  $('geometry-checks').hidden = true;
  $('geometry-topology').textContent = '';
  $('topology').disabled = false;
  const route = new URL(row.url);
  if (row.chapter) {
    route.searchParams.set('chapter', row.chapter);
    route.searchParams.set('frame', row.frame);
    route.hash = 'exam';
  }
  $('route').href = route.href;
  $('mesh-file').hidden = false;
  $('mesh-file').textContent = row.mesh ? 'Open source mesh' : 'Open geometry recipe';
  $('mesh-file').href = row.mesh ?? '../cases/' + entries.get(row.case).owner + '/playable-scene.js';
  selectionEvidence(row);
  const list = uses.get(row.binding);
  $('part-uses').hidden = list.length < 2;
  $('part-uses').querySelector('summary').textContent = list.length + ' acquisition uses';
  $('part-uses').querySelector('ul').replaceChildren(...list.map((use) => {
    const item = make('li');
    const link = make('a', use.chapterTitle || use.title);
    link.href = '#' + rowID(use);
    if (rowID(use) === key) link.setAttribute('aria-current', 'true');
    item.append(link);
    return item;
  }));
  rowsView(key);
  let geometry;
  try {
    geometry = await isolatedMesh(row, entries);
    if (request !== selectedRequest) {
      geometry.dispose();
      return;
    }
    $('mesh').hidden = false;
    $('views').hidden = false;
    $('mesh-help').hidden = false;
    const size = mount(geometry);
    const triangles = Math.floor((geometry.index?.count ?? geometry.attributes.position.count) / 3);
    $('mesh').dataset.ready = key;
    $('mesh-status').textContent = 'Bounds · ' + size;
    $('geometry-buffers').textContent = triangles.toLocaleString() + ' triangles · ' +
      bufferBytes(geometry).toLocaleString() + ' geometry buffer bytes';
    $('geometry-checks').hidden = false;
  } catch (cause) {
    geometry?.dispose();
    if (request !== selectedRequest) return;
    $('mesh').hidden = true;
    $('views').hidden = true;
    $('mesh-help').hidden = true;
    $('mesh-status').textContent = 'Isolated mesh unavailable. The acquisition link remains available.';
    console.warn(cause);
  }
}

$('topology').onclick = () => {
  const request = selectedRequest;
  const geometry = portrait.geometry;
  $('topology').disabled = true;
  $('geometry-topology').textContent = 'Checking topology…';
  setTimeout(() => {
    if (request !== selectedRequest) return;
    const { components, open, nonmanifold, collapsed } = meshTopology(geometry);
    $('geometry-topology').textContent = [
      components.toLocaleString() + (components === 1 ? ' component' : ' components'),
      open.toLocaleString() + ' open edges', nonmanifold.toLocaleString() + ' nonmanifold edges',
      ...(collapsed ? [collapsed.toLocaleString() + ' collapsed triangles excluded'] : []),
    ].join(' · ') + '. Exact coincident vertices welded. Boundaries and splits may be intentional.';
  }, 0);
};

$('filters').onsubmit = (event) => event.preventDefault();
for (const id of filters) $(id).addEventListener('input', () => { index = 0; rowsView(); });
$('filters').onreset = () => setTimeout(() => { index = 0; rowsView(); }, 0);
$('previous').onclick = () => { index--; rowsView(); };
$('next').onclick = () => { index++; rowsView(); };
window.addEventListener('hashchange', () => {
  if (!location.hash) {
    ++selectedRequest;
    selection = current = undefined;
    $('selection').textContent = 'Select a part';
    $('preview').hidden = $('evidence').hidden = $('part-uses').hidden = true;
  }
  refresh();
});
$('rows').addEventListener('click', (event) => {
  const link = event.target.closest('a');
  if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  const key = link.hash.slice(1);
  if (location.hash !== link.hash) history.pushState(null, '', link.hash);
  showPart(key);
});

async function start() {
  remaining = 1;
  try {
    recordRows(sweepRows());
  } catch (cause) {
    failures.push('Original sweeps · ' + cause.message);
  }
  refresh();
  const aaa = aaaRows().then(({ rows, issues }) => {
    pendingAAA = false;
    recordRows(rows);
    failures.push(...issues.map((issue) => 'AAA · ' + issue));
    refresh();
  });
  const manifest = await read('asset-inventory.json');
  manifest.cases.filter(({ family }) => family !== 'aaa').forEach((entry) => entries.set(entry.id, entry));
  remaining = entries.size;
  await Promise.allSettled((manifest.reviews ?? []).map(async (path) => {
    try {
      const { records, recipeHash, rubricHash } = await read(path);
      for (const record of records) {
        const owner = entries.get(record.case)?.owner ?? (record.source === 'aaa' ? 'vascular' : undefined);
        const emittedMesh = manifest.sweepHashes?.[record.case]?.[record.part];
        const prior = record.source === 'sweep'
          ? (manifest.sweepHashes && (!emittedMesh || emittedMesh !== record.meshSha256)) ||
            (manifest.rubricHash && manifest.rubricHash !== rubricHash)
          : owner && manifest.recipeHashes?.[owner] && manifest.recipeHashes[owner] !== recipeHash;
        if (record.occurrence) reviews.set(rowID(record), { ...record, prior });
        else uniqueReviews.set(frameKey({ ...record, chapter: record.chapter ?? '' }), { ...record, prior });
      }
    } catch (cause) {
      failures.push('Assessment · ' + cause.message);
    }
  }));
  if (current) {
    if (linkedSelection) coordinateSelection(current);
    selectionEvidence(current);
    rowsView(selection);
  }
  const requested = inventory.has(location.hash.slice(1)) ? undefined : location.hash.slice(1).split('/')[1];
  const reviewedCases = new Set([...reviews.values(), ...uniqueReviews.values()].map((record) => record.case));
  const ordered = [...entries.values()];
  ordered.sort((left, right) => Number(right.id === requested) - Number(left.id === requested) ||
    Number(reviewedCases.has(right.id)) - Number(reviewedCases.has(left.id)));
  // The renderer geometry is temporary. Only traversal records are kept in the table.
  for (const entry of ordered) {
    try {
      recordRows(await caseRows(entry));
    } catch (cause) {
      failures.push(entry.title + ' · ' + cause.message);
    }
    remaining--;
    refresh();
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  await aaa;
  refresh();
  if (current) selectionEvidence(current);
}

start().catch((cause) => {
  remaining = 0;
  failures.push('Case inventory · ' + cause.message);
  refresh();
});
