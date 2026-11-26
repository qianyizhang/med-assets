import * as THREE from '../vendor/build/three.module.js';
import { viewport } from '../scene.js';
import { aaaRows, axes, assessmentScore, bufferBytes, caseRows, dispose, isolatedMesh, meshTopology, read, rowID, setTeachingTours, sweepRows } from './assets-data.js';

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
const assets = new Map();
const reviews = new Map();
const uniqueReviews = new Map();
const failures = [];
const pageSize = 36;
let index = 0;
let selection;
let matches = [];
let current;
let openAsset;
let region = '';
let tourSelection = null;
let tourKey = '';
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

const filters = ['query', 'assessment'];
const assetFragment = (id) => 'asset/' + encodeURIComponent(id);
const regionOf = (row) => row.region ?? row.family;
const toursOf = (row) => row.teachingSelections ?? [{ id: row.case, label: row.title, url: row.url }];
const assetOf = (row) => row.assetId ?? row.source + '/' + row.case;
const partOf = (row) => row.partId ?? row.part;
const bindingOf = (row) => row.variantId ?? row.binding;
const byText = (left, right) => left.localeCompare(right, undefined, { numeric: true });
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
function recordRows(rows) {
  for (const row of rows) {
    const key = rowID(row);
    if (inventory.has(key)) continue;
    inventory.set(key, row);
    row.binding ??= [row.source, row.case, row.part, row.mesh, row.scale].join('/');
    const binding = bindingOf(row);
    if (!uses.has(binding)) uses.set(binding, []);
    uses.get(binding).push(row);
    const asset = assetOf(row);
    if (!assets.has(asset)) assets.set(asset, []);
    assets.get(asset).push(row);
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
  const scopedAssets = new Set();
  const scopedVariants = new Set();
  let scopedUses = 0;
  const reviewedParts = new Set();
  const qualifiedParts = new Set();
  let reviewedUses = 0;
  let qualifiedUses = 0;
  for (const row of inventory.values()) {
    if (!inScope(row)) continue;
    scopedAssets.add(assetOf(row));
    scopedVariants.add(bindingOf(row));
    scopedUses++;
    const record = linked(row);
    if (assessed(record)) {
      reviewedParts.add(bindingOf(row));
      reviewedUses++;
    }
    if (qualified(record)) {
      qualifiedParts.add(bindingOf(row));
      qualifiedUses++;
    }
  }
  const coverage = scopedAssets.size.toLocaleString() + ' assets in scope · ' + scopedVariants.size.toLocaleString() + ' geometry variants · ' + scopedUses.toLocaleString() + ' part uses';
  const reviews = reviewedParts.size.toLocaleString() + ' assessed variants (' + reviewedUses.toLocaleString() + ' uses)';
  const qualification = qualifiedParts.size.toLocaleString() + ' qualified variants (' + qualifiedUses.toLocaleString() + ' uses)';
  const pending = remaining + Number(pendingAAA);
  $('inventory-status').textContent = [matched + ' matching assets', coverage, reviews, qualification].join(' · ') +
    (pending ? ' · indexing ' + pending + ' sources' : '');
  $('issues').hidden = failures.length === 0;
  $('issues').querySelector('ul').replaceChildren(...failures.map((failure) => make('li', failure)));
}

function inScope(row) {
  return (!region || regionOf(row) === region) &&
    (tourSelection === null || toursOf(row).some(({ id }) => tourSelection.has(id)));
}

function filterState() {
  const url = new URL(location.href);
  if (region) url.searchParams.set('region', region);
  else url.searchParams.delete('region');
  url.searchParams.delete('tour');
  if (tourSelection !== null) {
    if (!tourSelection.size) url.searchParams.append('tour', '');
    else for (const id of [...tourSelection].sort()) url.searchParams.append('tour', id);
  }
  for (const [param, id] of [['q', 'query'], ['assessment', 'assessment']]) {
    if ($(id).value) url.searchParams.set(param, $(id).value);
    else url.searchParams.delete(param);
  }
  return url;
}

function restoreFilters() {
  const params = new URL(location.href).searchParams;
  region = params.get('region') ?? '';
  tourSelection = params.has('tour') ? new Set(params.getAll('tour').filter(Boolean)) : null;
  $('query').value = params.get('q') ?? '';
  $('assessment').value = params.get('assessment') ?? '';
}

function setFilters() {
  const url = filterState();
  if (url.href !== location.href) history.replaceState(null, '', url);
}

function renderScope() {
  const regions = new Map();
  const tours = new Map();
  for (const row of inventory.values()) {
    const key = regionOf(row);
    regions.set(key, row.regionLabel ?? key);
    if (!region || key === region) for (const tour of toursOf(row)) tours.set(tour.id, tour);
  }
  if (region && !regions.has(region)) regions.set(region, region);
  const choices = [...regions].sort((a, b) => byText(a[1], b[1]));
  const regionInput = $('region');
  if (regionInput.dataset.options !== JSON.stringify(choices)) {
    regionInput.dataset.options = JSON.stringify(choices);
    regionInput.replaceChildren(new Option('All body regions', ''), ...choices.map(([id, text]) => new Option(text, id)));
  }
  regionInput.value = region;
  const tourList = [...tours.values()].sort((a, b) => byText(a.label, b.label));
  const selected = tourList.filter(({ id }) => tourSelection === null || tourSelection.has(id)).length;
  $('all-tours').checked = tourList.length > 0 && selected === tourList.length;
  $('all-tours').indeterminate = selected > 0 && selected < tourList.length;
  $('all-tours').disabled = !tourList.length;
  $('tour-count').textContent = tourList.length ? selected + ' of ' + tourList.length + ' selected' : 'No tours available';
  const next = JSON.stringify(tourList.map(({ id, label }) => [id, label]));
  if (next !== tourKey) {
    tourKey = next;
    const focused = $('tour-choices').contains(document.activeElement) ? document.activeElement.value : null;
    $('tour-choices').replaceChildren(...tourList.map(({ id, label }) => {
      const field = make('label', undefined, 'tour-choice');
      const checkbox = make('input');
      checkbox.type = 'checkbox';
      checkbox.name = 'tour';
      checkbox.value = id;
      field.append(checkbox, make('span', label));
      return field;
    }));
    if (focused) [...$('tour-choices').querySelectorAll('input')].find((input) => input.value === focused)?.focus();
  }
  for (const input of $('tour-choices').querySelectorAll('input')) {
    input.checked = tourSelection === null || tourSelection.has(input.value);
  }
}

function grouped(rows, key) {
  const groups = new Map();
  for (const row of rows) {
    const id = key(row);
    if (!groups.has(id)) groups.set(id, []);
    groups.get(id).push(row);
  }
  return groups;
}

function representative(rows) {
  return rows.find((row) => rowID(row) === selection) ??
    rows.find((row) => assessed(linked(row)) && !/exterior|skin|torso/i.test(row.label)) ??
    rows.find((row) => !/exterior|skin|torso|unnamed/i.test(row.label)) ?? rows[0];
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

function specimen(row) {
  const tile = make('span', undefined, 'specimen');
  tile.dataset.part = rowID(row);
  const record = linked(row);
  const candidate = !record?.prior && record?.comparison?.candidate;
  if (candidate) {
    const image = make('img');
    image.alt = '';
    image.loading = 'lazy';
    image.src = candidate;
    image.addEventListener('error', () => {
      image.remove();
      thumbnailObserver.observe(tile);
    });
    tile.append(image);
  } else {
    thumbnailObserver.observe(tile);
  }
  return tile;
}

function partsView(rows) {
  const parts = grouped(rows, partOf);
  const currentPart = current && partOf(current);
  const panel = $('asset-parts');
  const previouslyOpen = new Set(panel.dataset.asset === openAsset
    ? [...panel.querySelectorAll('details[open]')].map((detail) => detail.dataset.part) : []);
  panel.dataset.asset = openAsset;
  const focus = panel.contains(document.activeElement) ? document.activeElement.getAttribute('href') : null;
  const signature = [openAsset, selection, ...rows.map((row) => rowID(row) + rateLabel(linked(row)))].join('|');
  if (panel.dataset.signature === signature) return;
  panel.dataset.signature = signature;
  panel.replaceChildren(...[...parts].map(([id, partRows], partIndex) => {
    const details = make('details', undefined, 'part-group');
    const variants = grouped(partRows, bindingOf);
    const title = partRows[0].partLabel ?? partRows[0].label;
    details.dataset.part = id;
    details.open = id === currentPart || previouslyOpen.has(id) || (!currentPart && !previouslyOpen.size && partIndex === 0);
    const summary = make('summary', title);
    summary.append(make('small', variants.size + (variants.size === 1 ? ' variant' : ' variants')));
    const list = make('ul', undefined, 'variant-list');
    for (const [binding, phaseRows] of variants) {
      const row = representative(phaseRows);
      const item = make('li');
      const link = make('a');
      const key = rowID(row);
      link.href = '#' + key;
      link.dataset.variant = binding;
      if (key === selection) link.setAttribute('aria-current', 'true');
      link.append(make('strong', row.chapterTitle || row.title), make('small', [
        row.chapterTitle && row.title, rateLabel(linked(row)),
        phaseRows.length > 1 ? phaseRows.length + ' acquisition uses' : '',
      ].filter(Boolean).join(' · ')));
      item.append(link);
      list.append(item);
    }
    details.append(summary, list);
    return details;
  }));
  if (focus) [...panel.querySelectorAll('a')].find((link) => link.getAttribute('href') === focus)?.focus({ preventScroll: true });
}

function useView() {
  if (!current) return;
  const list = (uses.get(bindingOf(current)) ?? []).filter((use) => assetOf(use) === openAsset && partOf(use) === partOf(current) && inScope(use));
  $('part-uses').hidden = list.length < 2;
  $('part-uses').querySelector('summary').textContent = list.length + ' acquisition uses in scope';
  const focus = $('part-uses').contains(document.activeElement) ? document.activeElement.getAttribute('href') : null;
  const section = $('part-uses').querySelector('ul');
  const signature = [selection, ...list.map((row) => rowID(row) + rateLabel(linked(row)))].join('|');
  if (section.dataset.signature === signature) return;
  section.dataset.signature = signature;
  section.replaceChildren(...list.map((use) => {
    const item = make('li');
    const link = make('a', use.chapterTitle || use.title);
    link.href = '#' + rowID(use);
    if (rowID(use) === selection) link.setAttribute('aria-current', 'true');
    item.append(link, make('small', [use.chapterTitle && use.title, rateLabel(linked(use))].filter(Boolean).join(' · ')));
    return item;
  }));
  if (focus) [...section.querySelectorAll('a')].find((link) => link.getAttribute('href') === focus)?.focus({ preventScroll: true });
}

function rowMatches(row, query, rating) {
  return inScope(row) && matchesAssessment(linked(row), rating) && query.every((token) =>
    [row.assetLabel, row.partLabel, row.label, row.title, row.chapterTitle, row.case,
      ...toursOf(row).map(({ label }) => label)].join(' ').toLowerCase().includes(token));
}

const searchTerms = () => $('query').value.trim().toLowerCase().split(/\s+/).filter(Boolean);

function rowsView() {
  const query = searchTerms();
  const rating = $('assessment').value;
  const candidates = [...inventory.values()].filter((row) => rowMatches(row, query, rating));
  const groups = grouped(candidates, assetOf);
  matches = [...groups].sort((left, right) =>
    Number(right[1].some((row) => assessed(linked(row)))) - Number(left[1].some((row) => assessed(linked(row)))) ||
    byText(left[1][0].assetLabel ?? left[1][0].title, right[1][0].assetLabel ?? right[1][0].title));
  const total = Math.max(1, Math.ceil(matches.length / pageSize));
  index = Math.min(index, total - 1);
  const visible = matches.slice(pageSize * index, pageSize * (index + 1));
  const signature = visible.map(([id, rows]) => id + rowID(representative(rows)) + '/' + rows.length).join('|');
  if (signature !== shownRows) {
    shownRows = signature;
    const focus = $('rows').contains(document.activeElement) ? document.activeElement.dataset.asset : null;
    $('rows').replaceChildren(...visible.map(([id, rows]) => {
      const row = representative(rows);
      const tile = make('li');
      const anchor = make('a');
      anchor.dataset.asset = id;
      anchor.href = '#' + assetFragment(id);
      const parts = new Set(rows.map(partOf)).size;
      anchor.append(specimen(row), make('strong', row.assetLabel ?? row.title),
        make('small', parts + (parts === 1 ? ' part' : ' parts')));
      tile.append(anchor);
      return tile;
    }));
    if (focus) [...$('rows').querySelectorAll('a')].find((anchor) => anchor.dataset.asset === focus)?.focus({ preventScroll: true });
  }
  $('asset-shelf').hidden = Boolean(openAsset);
  $('asset-detail').hidden = !openAsset;
  $('pagination').hidden = Boolean(openAsset) || total < 2;
  $('previous').disabled = index === 0;
  $('next').disabled = index + 1 === total;
  $('page').textContent = (index + 1) + ' / ' + total;
  $('empty').hidden = Boolean(openAsset) || matches.length > 0 || remaining > 0 || pendingAAA;
  if (openAsset) {
    const all = assets.get(openAsset) ?? [];
    const rows = groups.get(openAsset) ?? [];
    const revisions = [...new Set(rows.map(row => row.assetRevision).filter(Boolean))];
    $('asset-title').textContent = all[0]?.assetLabel ?? all[0]?.title ?? 'Asset unavailable';
    $('asset-summary').textContent = rows.length ? rows.length + ' acquisition uses match the current filters.'
      : 'No acquisition uses match the current filters.';
    $('asset-source').hidden = !revisions.length;
    $('asset-source').textContent = 'Source revision · ' + revisions.join(', ');
    partsView(rows);
    useView();
  }
  status();
}

function clearPart() {
  ++selectedRequest;
  selection = current = undefined;
  delete $('mesh').dataset.ready;
  $('selection').textContent = 'Select a part';
  $('selection-context').textContent = 'Choose an asset, then select a part variant to inspect its mesh and assessment.';
  $('preview').hidden = $('evidence').hidden = $('part-uses').hidden = true;
}

function refresh() {
  const deep = location.hash.slice(1);
  renderScope();
  if (deep.startsWith('asset/')) {
    if (selection) clearPart();
    try {
      openAsset = decodeURIComponent(deep.slice(6));
    } catch {
      openAsset = undefined;
    }
  } else if (deep && inventory.has(deep) && selection !== deep) {
    showPart(deep, true);
    return;
  } else if (!deep) {
    openAsset = undefined;
    if (selection) clearPart();
  } else if (!remaining && !pendingAAA && !inventory.has(deep)) {
    openAsset = undefined;
    clearPart();
    $('selection').textContent = 'Part unavailable';
    $('selection-context').textContent = 'This link does not resolve to a part in the current inventory.';
  }
  rowsView();
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
  if (!record) {
    section.append(make('p', 'No review is recorded for this part and teaching use. Geometry checks alone do not assign a rubric score.', 'muted'));
    const reviewed = (uses.get(bindingOf(row)) ?? []).find((use) => assessed(linked(use)));
    if (reviewed) {
      const other = make('a', 'Review of the same geometry in ' + (reviewed.chapterTitle || reviewed.title));
      other.href = '#' + rowID(reviewed);
      section.append(other);
    }
    return;
  }
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
  const rowRegion = regionOf(row);
  if (region && region !== rowRegion) region = rowRegion;
  if (tourSelection !== null && !toursOf(row).some(({ id }) => tourSelection.has(id))) {
    tourSelection = new Set(toursOf(row).slice(0, 1).map(({ id }) => id));
  }
  if ($('query').value) $('query').value = '';
  if ($('assessment').value && !matchesAssessment(grade, $('assessment').value)) $('assessment').value = '';
  renderScope();
  setFilters();
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
  openAsset = assetOf(row);
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
  const composed = row.source === 'sweep' ? toursOf(row).filter((tour) =>
    !tour.id.startsWith('sweep:') && (tourSelection === null || tourSelection.has(tour.id))) : [];
  const teaching = $('composed-uses');
  teaching.hidden = !composed.length;
  teaching.replaceChildren();
  if (composed.length) {
    teaching.append('Also used in ');
    for (const [index, tour] of composed.entries()) {
      const link = make('a', tour.label);
      link.href = tour.url;
      if (index) teaching.append(', ');
      teaching.append(link);
    }
  }
  $('mesh-file').hidden = false;
  $('mesh-file').textContent = row.mesh ? 'Open source mesh' : 'Open geometry recipe';
  $('mesh-file').href = row.mesh ?? '../cases/' + entries.get(row.case).owner + '/playable-scene.js';
  selectionEvidence(row);
  rowsView();
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

function filtersChanged() {
  index = 0;
  renderScope();
  const url = filterState();
  const query = searchTerms();
  const rating = $('assessment').value;
  if (openAsset && !(assets.get(openAsset) ?? []).some((row) => rowMatches(row, query, rating))) {
    openAsset = undefined;
    clearPart();
    url.hash = '';
  } else if (current && !rowMatches(current, query, rating)) {
    clearPart();
    url.hash = assetFragment(openAsset);
  }
  if (url.href !== location.href) history.replaceState(null, '', url);
  rowsView();
}

$('filters').onsubmit = (event) => event.preventDefault();
for (const id of filters) $(id).addEventListener('input', filtersChanged);
$('region').onchange = () => {
  region = $('region').value;
  tourSelection = null;
  filtersChanged();
};
$('all-tours').onchange = () => {
  tourSelection = $('all-tours').checked ? null : new Set();
  filtersChanged();
};
$('tour-choices').onchange = () => {
  const inputs = [...$('tour-choices').querySelectorAll('input')];
  const selected = inputs.filter((input) => input.checked).map((input) => input.value);
  tourSelection = selected.length === inputs.length ? null : new Set(selected);
  filtersChanged();
};
$('filters').onreset = () => setTimeout(() => {
  region = '';
  tourSelection = null;
  filtersChanged();
}, 0);
$('previous').onclick = () => { index--; rowsView(); };
$('next').onclick = () => { index++; rowsView(); };
window.addEventListener('popstate', () => {
  restoreFilters();
  refresh();
});
window.addEventListener('hashchange', refresh);
function activateLink(event) {
  const link = event.target.closest('a');
  if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
  if (!link.getAttribute('href')?.startsWith('#')) return;
  event.preventDefault();
  const key = link.hash.slice(1);
  if (location.hash !== link.hash) {
    const url = filterState();
    url.hash = key;
    history.pushState(null, '', url);
  }
  if (key && !key.startsWith('asset/')) {
    const row = inventory.get(key);
    if (row) showPart(key, !rowMatches(row, searchTerms(), $('assessment').value));
  } else {
    const from = openAsset;
    refresh();
    if (key) $('asset-title').focus();
    else [...$('rows').querySelectorAll('[data-asset]')].find((anchor) => anchor.dataset.asset === from)?.focus();
  }
}
for (const id of ['rows', 'asset-detail', 'part-uses']) $(id).addEventListener('click', activateLink);

async function start() {
  restoreFilters();
  remaining = 1;
  let manifest;
  try {
    manifest = await read('asset-inventory.json');
  } catch (cause) {
    failures.push('Case inventory · ' + cause.message);
    manifest = { cases: [], teachingTours: [] };
  }
  setTeachingTours(manifest.teachingTours ?? []);
  manifest.cases.filter(({ family }) => family !== 'aaa').forEach((entry) => entries.set(entry.id, entry));
  remaining = entries.size + 1;
  const originals = Promise.resolve().then(sweepRows).then(recordRows).catch((cause) => {
    failures.push('Original sweeps · ' + cause.message);
  }).finally(() => {
    remaining--;
    refresh();
  });
  const aaa = aaaRows().then(({ rows, issues }) => {
    recordRows(rows);
    failures.push(...issues.map((issue) => 'AAA · ' + issue));
  }).finally(() => {
    pendingAAA = false;
    refresh();
  });
  refresh();
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
    rowsView();
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
  await Promise.allSettled([originals, aaa]);
  refresh();
  if (current) selectionEvidence(current);
}

start().catch((cause) => {
  remaining = 0;
  failures.push('Case inventory · ' + cause.message);
  refresh();
});
