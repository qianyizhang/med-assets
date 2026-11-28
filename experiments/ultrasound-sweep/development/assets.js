import * as THREE from '../vendor/build/three.module.js';
import { viewport } from '../scene.js';
import { aaaRows, axes, assessmentScore, bufferBytes, caseRows, chapterMeshReviewPrior, dispose, isolatedMesh, meshTopology, read, rowID, setTeachingTours, sweepRows } from './assets-data.js';

import { acquireScene } from './assets-scene.js';
import { illustrationFor } from './assets-illustrations.js';
import { bindingProvenance, setProvenanceInventory } from './assets-provenance.js';
import { renderTourChooser } from './assets-tour-chooser.js';

const $ = (id) => document.getElementById(id);
const make = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
const entries = new Map();
const inventory = new Map();
const retiredUses = new Map();
const galleryAssetAliases = new Map([['atlas:skeleton', 'library/skeleton']]);
const retiredAssets = new Set([
  'case:hepatic-model', 'case:renal-model', 'case:biliary-model', 'case:pancreas-model', 'case:abdominal-context',
]);
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
let bindingFilter = '';
let bindingPage = 0;
let activeCoverage = '';
let region = '';
let tourSelection = null;
let mode = 'asset';
let acquisition = '';
let sceneRequest = 0;
let desiredScene = '';
let loadedScene;
const hiddenElements = new Map();
const acquisitionKey = (row) => [row.source, row.case, row.chapter].filter(Boolean).join('/');
const independentReference = (row) => Boolean(row.donor && row.donor.registration !== 'registered-exact');
const viewKey = (row) => independentReference(row) && row.sourceSpace ? acquisitionKey(row) + '@' + row.sourceSpace : acquisitionKey(row);
function acquisitionURL(row) {
  const url = new URL(row.url);
  if (row.chapter) {
    url.searchParams.set('chapter', row.chapter);
    if (row.frame !== undefined) url.searchParams.set('frame', row.frame);
    url.hash = 'exam';
  }
  return url.href;
}
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

const filters = ['query', 'assessment', 'availability', 'reuse'];
const requirementLabel = (row) => row.source === 'requirement' ? ({ rebuild: 'Rebuild required', missing: 'Missing part' })[row.status] : undefined;
const displayStatus = (row) => requirementLabel(row) ?? rateLabel(linked(row));
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
  if (requirementLabel(row) || independentReference(row)) return undefined;
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
    for (const part of row.legacyParts ?? []) {
      const priorKey = rowID({ ...row, source: 'case', part });
      retiredUses.set(priorKey, key);
    }
    row.binding ??= [row.source, row.case, row.part, row.mesh, row.scale].join('/');
    const binding = bindingOf(row);
    if (!uses.has(binding)) uses.set(binding, []);
    uses.get(binding).push(row);
    const asset = assetOf(row);
    if (row.donor?.source === 'gallery' && row.assetRevision && !asset.endsWith('/' + row.assetRevision)) {
      galleryAssetAliases.set(asset + '/' + row.assetRevision, asset);
    }
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
    if (requirementLabel(row)) continue;
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
  const gapRows = [...inventory.values()].filter((row) => inScope(row) && requirementLabel(row));
  const gapAssets = new Set(gapRows.filter((row) => row.status === 'rebuild').map(assetOf)).size;
  const gapParts = new Set(gapRows.map((row) => assetOf(row) + '/' + partOf(row))).size;
  const gaps = [gapAssets && gapAssets + (gapAssets === 1 ? ' rebuild' : ' rebuilds') + ' required',
    gapParts && gapParts + (gapParts === 1 ? ' missing part' : ' missing parts')].filter(Boolean).join(' · ');
  const coverage = scopedAssets.size.toLocaleString() + ' assets in scope · ' + scopedVariants.size.toLocaleString() + ' geometry variants · ' + scopedUses.toLocaleString() + ' part uses';
  const reviews = reviewedParts.size.toLocaleString() + ' assessed variants (' + reviewedUses.toLocaleString() + ' uses)';
  const qualification = qualifiedParts.size.toLocaleString() + ' qualified variants (' + qualifiedUses.toLocaleString() + ' uses)';
  const pending = remaining + Number(pendingAAA);
  $('inventory-status').textContent = [matched + ' matching assets', coverage, gaps, reviews, qualification].filter(Boolean).join(' · ') +
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
  for (const [param, id] of [['q', 'query'], ['assessment', 'assessment'], ['availability', 'availability'], ['reuse', 'reuse']]) {
    if ($(id).value) url.searchParams.set(param, $(id).value);
    else url.searchParams.delete(param);
  }
  if (bindingFilter) url.searchParams.set('binding', bindingFilter);
  else url.searchParams.delete('binding');
  if (mode === 'scene') url.searchParams.set('view', mode);
  else url.searchParams.delete('view');
  if (acquisition) url.searchParams.set('acquisition', acquisition);
  else url.searchParams.delete('acquisition');
  return url;
}

function restoreFilters() {
  const params = new URL(location.href).searchParams;
  region = params.get('region') ?? '';
  mode = params.get('view') === 'scene' ? 'scene' : 'asset';
  acquisition = params.get('acquisition') ?? '';
  tourSelection = params.has('tour') ? new Set(params.getAll('tour').filter(Boolean)) : null;
  $('query').value = params.get('q') ?? '';
  $('assessment').value = params.get('assessment') ?? '';
  $('availability').value = params.get('availability') ?? '';
  $('reuse').value = params.get('reuse') ?? '';
  bindingFilter = params.get('binding') ?? '';
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
    if (!region || key === region) for (const tour of toursOf(row)) tours.set(tour.id, { region: key, ...tour });
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
  renderTourChooser($('tour-choices'), tourList, tourSelection, (next) => {
    tourSelection = next;
    filtersChanged();
  });
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
  const renderable = rows.filter((row) => !requirementLabel(row));
  if (renderable.length) rows = renderable;
  else return rows.find((row) => row.status === 'rebuild') ?? rows[0];
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
  if (requirementLabel(row)) {
    tile.classList.add('requirement-placeholder');
    tile.textContent = requirementLabel(row);
    const art = illustrationFor(row);
    if (art && row.status === 'rebuild') {
      const image = make('img');
      image.alt = '';
      image.loading = 'lazy';
      image.src = art.src;
      image.addEventListener('error', () => {
        tile.classList.remove('requirement-illustrated');
        tile.textContent = requirementLabel(row);
      }, { once: true });
      tile.classList.add('requirement-illustrated');
      tile.replaceChildren(image, make('span', 'AI illustration', 'art-badge'));
    }
    return tile;
  }
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

function requirementsView(rows) {
  const panel = $('requirements');
  panel.hidden = !rows.length;
  const list = panel.querySelector('ul');
  const distinct = [...grouped(rows, (row) => [row.case, partOf(row), row.status].join('/')).values()];
  const signature = rows.map(rowID).join('|');
  if (list.dataset.rows === signature) return;
  list.dataset.rows = signature;
  list.replaceChildren(...distinct.map((uses) => {
    const row = uses[0];
    const item = make('li');
    const title = make('a', 'Missing part · ' + (row.partLabel ?? row.label), 'requirement-label');
    title.href = '#' + rowID(row);
    title.dataset.requirementUse = '';
    const reason = [...new Set(uses.map((use) => use.missingReason).filter(Boolean))].join(' ');
    const notes = make('p', reason);
    notes.hidden = !reason;
    const link = make('a', row.title);
    link.href = row.url;
    item.append(title, notes, link);
    const acquisitions = new Map(uses.filter((use) => use.chapter).map((use) => [use.chapter, use]));
    if (acquisitions.size) {
      const detail = make('details');
      detail.append(make('summary', acquisitions.size + (acquisitions.size === 1 ? ' acquisition' : ' acquisitions')));
      const views = make('ul');
      for (const use of acquisitions.values()) {
        const child = make('li');
        const chapter = make('a', use.chapterTitle || use.chapter);
        chapter.href = acquisitionURL(use);
        child.append(chapter);
        views.append(child);
      }
      detail.append(views);
      item.append(detail);
    }
    return item;
  }));
}

function partsView(rows) {
  const parts = grouped(rows, partOf);
  const currentPart = current && partOf(current);
  const panel = $('asset-parts');
  const previouslyOpen = new Set(panel.dataset.asset === openAsset
    ? [...panel.querySelectorAll('details[open]')].map((detail) => detail.dataset.part) : []);
  panel.dataset.asset = openAsset;
  const focus = panel.contains(document.activeElement) ? document.activeElement.getAttribute('href') : null;
  const signature = [openAsset, selection, ...rows.map((row) => rowID(row) + displayStatus(row))].join('|');
  if (panel.dataset.signature === signature) return;
  panel.dataset.signature = signature;
  panel.replaceChildren(...[...parts].map(([id, partRows], partIndex) => {
    const details = make('details', undefined, 'part-group');
    const variants = grouped(partRows, bindingOf);
    const title = partRows[0].partLabel ?? partRows[0].label;
    details.dataset.part = id;
    details.open = id === currentPart || previouslyOpen.has(id) || (!currentPart && !previouslyOpen.size && partIndex === 0);
    const summary = make('summary', title);
    const partStatus = [...new Set(partRows.map(requirementLabel).filter(Boolean))].join(' · ');
    const geometry = new Set(partRows.filter((row) => !requirementLabel(row)).map(bindingOf)).size;
    if (geometry) summary.append(make('small', geometry + (geometry === 1 ? ' variant' : ' variants')));
    if (partStatus) summary.append(make('small', partStatus, 'requirement-label'));
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
        row.chapterTitle && row.title, displayStatus(row),
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
  if (requirementLabel(current)) return;
  const list = (uses.get(bindingOf(current)) ?? []).filter((use) => assetOf(use) === openAsset && partOf(use) === partOf(current) && inScope(use));
  $('part-uses').hidden = list.length < 2;
  $('part-uses').querySelector('summary').textContent = list.length + ' acquisition uses in scope';
  const focus = $('part-uses').contains(document.activeElement) ? document.activeElement.getAttribute('href') : null;
  const section = $('part-uses').querySelector('ul');
  const signature = [selection, ...list.map((row) => rowID(row) + displayStatus(row))].join('|');
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
  const gap = requirementLabel(row);
  const availability = $('availability').value;
  return inScope(row) && (!bindingFilter || bindingOf(row) === bindingFilter) &&
    (!$('reuse').value || (!gap && (uses.get(bindingOf(row))?.length ?? 0) > 1)) && (gap ? !rating && availability !== 'geometry' : availability !== 'gaps' && matchesAssessment(linked(row), rating)) &&
    query.every((token) => [row.assetLabel, row.partLabel, row.label, row.title, row.chapterTitle, row.case, gap,
      ...toursOf(row).map(({ label }) => label)].join(' ').toLowerCase().includes(token));
}

const searchTerms = () => $('query').value.trim().toLowerCase().split(/\s+/).filter(Boolean);

function rowsView() {
  const query = searchTerms();
  const assessment = $('assessment');
  assessment.disabled = $('availability').value === 'gaps';
  if (assessment.disabled) assessment.value = '';
  const rating = assessment.value;
  const candidates = [...inventory.values()].filter((row) => rowMatches(row, query, rating));
  const groups = grouped(candidates, assetOf);
  matches = [...groups].sort((left, right) =>
    Number(right[1].some((row) => row.status === 'rebuild')) - Number(left[1].some((row) => row.status === 'rebuild')) ||
    Number(right[1].some(requirementLabel)) - Number(left[1].some(requirementLabel)) ||
    Number(right[1].some((row) => assessed(linked(row)))) - Number(left[1].some((row) => assessed(linked(row)))) ||
    byText(left[1][0].assetLabel ?? left[1][0].title, right[1][0].assetLabel ?? right[1][0].title));
  const total = Math.max(1, Math.ceil(matches.length / pageSize));
  index = Math.min(index, total - 1);
  const visible = matches.slice(pageSize * index, pageSize * (index + 1));
  const signature = visible.map(([id, rows]) =>
    [id, rowID(representative(rows)), rows.length, ...rows.filter(requirementLabel).map(rowID)].join('/')).join('|');
  if (signature !== shownRows) {
    shownRows = signature;
    const focus = $('rows').contains(document.activeElement) ? document.activeElement.dataset.asset : null;
    $('rows').replaceChildren(...visible.map(([id, rows]) => {
      const row = representative(rows);
      const tile = make('li');
      const anchor = make('a');
      anchor.dataset.asset = id;
      anchor.href = '#' + assetFragment(id);
      const parts = new Set(rows.filter((row) => !requirementLabel(row)).map(partOf)).size;
      const requirements = new Set(rows.filter(requirementLabel).map(partOf)).size;
      anchor.append(specimen(row), make('strong', row.assetLabel ?? row.title), make('small', [
        parts && parts + (parts === 1 ? ' part' : ' parts'),
        requirements && requirements + (requirements === 1 ? ' requirement' : ' requirements'),
      ].filter(Boolean).join(' · ')));
      const statuses = [...new Set(rows.map(requirementLabel).filter((status) =>
        status && (status !== requirementLabel(row) || (row.status === 'rebuild' && illustrationFor(row)))))];
      if (statuses.length) anchor.append(make('small', statuses.join(' · '), 'requirement-label'));
      const requirementTypes = [...new Set(rows.filter(requirementLabel).map((row) => row.status))];
      if (requirementTypes.length) anchor.dataset.requirement = requirementTypes.join(' ');
      tile.append(anchor);
      return tile;
    }));
    if (focus) [...$('rows').querySelectorAll('a')].find((anchor) => anchor.dataset.asset === focus)?.focus({ preventScroll: true });
  }
  for (const link of $('rows').querySelectorAll('[data-asset]')) {
    if (link.dataset.asset === openAsset) link.setAttribute('aria-current', 'true');
    else link.removeAttribute('aria-current');
  }
  $('asset-detail').hidden = !openAsset || !assets.has(openAsset);
  $('pagination').hidden = total < 2;
  $('previous').disabled = index === 0;
  $('next').disabled = index + 1 === total;
  $('page').textContent = (index + 1) + ' / ' + total;
  $('empty').hidden = matches.length > 0 || remaining > 0 || pendingAAA;
  if (openAsset) {
    const all = assets.get(openAsset) ?? [];
    const rows = groups.get(openAsset) ?? [];
    const revisions = [...new Set(rows.map(row => row.assetRevision).filter(Boolean))];
    const title = all[0]?.assetLabel ?? all[0]?.title ?? 'Asset unavailable';
    $('asset-title').textContent = mode === 'scene' ? 'Selected asset · ' + title : title;
    $('asset-title').classList.toggle('visually-hidden', mode === 'asset' && !current);
    const geometryRows = rows.filter((row) => !requirementLabel(row));
    const acquisitions = new Set(geometryRows.map(acquisitionKey)).size;
    const parts = new Set(geometryRows.map(partOf)).size;
    const requirements = new Set(rows.filter(requirementLabel).map(partOf)).size;
    const geometry = parts ? parts + (parts === 1 ? ' part' : ' parts') + ' across ' +
      acquisitions + (acquisitions === 1 ? ' acquisition' : ' acquisitions') : '';
    const gaps = requirements ? requirements + (requirements === 1 ? ' geometry requirement' : ' geometry requirements') : '';
    $('asset-summary').textContent = rows.length
      ? [geometry, gaps].filter(Boolean).join(' · ') + ' in scope.'
      : 'No acquisitions in scope.';
    $('asset-source').hidden = !revisions.length;
    $('asset-source').textContent = 'Source revision · ' + revisions.join(', ');
    partsView(rows);
    useView();
  }
  requirementsView((groups.get(openAsset) ?? []).filter(requirementLabel));
  for (const button of $('workspace-mode').querySelectorAll('button')) {
    button.setAttribute('aria-pressed', String(button.dataset.mode === mode));
  }
  if (!current) assembledView(candidates);
  const filter = $('binding-filter');
  filter.hidden = !bindingFilter;
  if (bindingFilter) {
    const sample = uses.get(bindingFilter)?.[0];
    const reset = filterState();
    reset.searchParams.delete('binding');
    reset.hash = '';
    const clear = make('a', 'Clear binding filter');
    clear.href = reset.href;
    filter.replaceChildren('Binding · ' + (sample?.partLabel ?? sample?.label ?? 'Unavailable') + ' · ', clear);
  }
  provenanceView(current);
  bindingCatalog(candidates);
  status();
}

function clearPart() {
  ++selectedRequest;
  selection = current = undefined;
  delete $('mesh').dataset.ready;
  $('selection').textContent = 'Select an asset';
  $('selection-context').textContent = 'Choose an asset from the shelf.';
  $('preview').hidden = $('evidence').hidden = $('part-uses').hidden = true;
}

function refresh() {
  const hash = location.hash.slice(1);
  const deep = retiredUses.get(hash) ?? hash;
  renderScope();
  if (hash === 'coverage' || hash === 'coverage-bindings') {
    const panel = $(hash);
    if (activeCoverage !== hash) panel.open = true;
    openAsset = undefined;
    if (selection) clearPart();
    rowsView();
    if (activeCoverage !== hash) {
      activeCoverage = hash;
      requestAnimationFrame(() => {
        if (location.hash === '#' + hash) panel.scrollIntoView({ block: 'start' });
      });
    }
    return;
  }
  activeCoverage = '';
  if (deep.startsWith('asset/')) {
    if (selection) clearPart();
    try {
      const asset = decodeURIComponent(deep.slice(6));
      openAsset = galleryAssetAliases.get(asset) ?? asset;
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
    rowsView();
    const original = hash.split('/');
    const retired = original[0] === 'case' && [...inventory.values()].some((row) =>
      row.case === original[1] && (row.donor || requirementLabel(row)));
    $('selection').textContent = retired ? 'Retired geometry' : 'Part unavailable';
    $('selection-context').textContent = retired
      ? 'This bookmark points to geometry retired from this tour. Choose an available source asset or tour requirement from the shelf.'
      : 'This link does not resolve to a part in the current inventory.';
    return;
  }
  rowsView();
}

function scopeLink(tour) {
  const url = new URL('assets.html', location.href);
  url.searchParams.set('tour', tour);
  return url.href;
}

function coverageView(manifest) {
  const panel = $('coverage');
  const content = $('coverage-content');
  const cases = manifest.cases ?? [];
  const sweepFiles = manifest.sweepHashes ?? {};
  const sweeps = Object.keys(sweepFiles).sort(byText);
  const references = Object.values(sweepFiles).flatMap((files) => Object.values(files)).filter(Boolean);
  const distinctFiles = new Set(references).size;
  const chapters = cases.reduce((count, entry) => count + (entry.chapters?.length ?? 0), 0);
  panel.querySelector('summary').textContent =
    'Study coverage · ' + cases.length + ' case tours · ' + chapters + ' chapters · ' + sweeps.length + ' standalone sweeps';
  content.replaceChildren();
  const families = grouped(cases, (entry) => entry.family ?? '');
  const caseTitle = make('h3', 'Case tours');
  content.append(caseTitle);
  for (const [family, entries] of families) {
    const section = make('details');
    const title = { aaa: 'AAA screening', echo: 'Echocardiography' }[family] ??
      family[0]?.toUpperCase() + family.slice(1).replaceAll('-', ' ');
    section.append(make('summary', title + ' · ' + entries.length));
    for (const entry of entries) {
      const tour = make('details');
      tour.append(make('summary', entry.title + ' · ' + entry.chapters.length + ' chapters'));
      const browse = make('a', 'Browse tour assets');
      browse.href = scopeLink(entry.id);
      tour.append(browse);
      const list = make('ul');
      for (const chapter of entry.chapters) {
        const item = make('li');
        const link = make('a', chapter.title);
        link.href = acquisitionURL({ ...chapter, url: new URL('../' + entry.url, location.href), chapter: chapter.id, frame: chapter.evidenceFrame });
        item.append(link); list.append(item);
      }
      tour.append(list); section.append(tour);
    }
    content.append(section);
  }
  const standalone = make('details');
  standalone.append(make('summary', 'Standalone sweeps · ' + sweeps.length));
  standalone.append(make('p', references.length + ' sweep mesh references point to ' +
    distinctFiles + ' distinct files by SHA-256.'));
  const list = make('ul');
  for (const sweep of sweeps) {
    const item = make('li');
    const link = make('a', (typeof abdomenTours !== 'undefined' && abdomenTours.find(({ id }) => id === sweep)?.title) || sweep.replaceAll('-', ' '));
    const url = new URL('../index.html', location.href);
    url.searchParams.set('sweep', sweep);
    link.href = url.href;
    const browse = make('a', 'Browse assets');
    browse.href = scopeLink('sweep:' + sweep);
    item.append(link, ' · ', browse); list.append(item);
  }
  standalone.append(list); content.append(standalone);
}

function bindingCatalog(candidates) {
  const panel = $('coverage-bindings');
  if (!panel.open) return;
  const available = [...grouped(candidates.filter((row) => !requirementLabel(row)), bindingOf).values()]
    .sort(([a], [b]) => byText(a.assetLabel ?? a.title, b.assetLabel ?? b.title) || byText(a.partLabel ?? a.label, b.partLabel ?? b.label));
  const pages = Math.max(1, Math.ceil(available.length / 28));
  bindingPage = Math.min(bindingPage, pages - 1);
  const page = available.slice(bindingPage * 28, (bindingPage + 1) * 28);
  const body = panel.querySelector('tbody');
  const signature = page.map((rows) => rowID(rows[0]) + '/' + rows.length).join('|');
  if (body.dataset.signature !== signature) {
    body.dataset.signature = signature;
    body.replaceChildren(...page.map((rows) => {
      const row = rows.find((candidate) => !candidate.donor) ?? rows[0];
      const provenance = bindingProvenance(row);
      const item = make('tr');
      const detail = make('td');
      const link = make('a', row.partLabel ?? row.label);
      link.href = '#' + rowID(row);
      detail.append(link, make('small', row.assetLabel ?? row.title));
      const source = make('td', provenance.source ?? 'Unavailable');
      if (provenance.revision) source.append(make('small', provenance.revision));
      const count = new Set(rows.map(acquisitionKey)).size;
      const kinds = [...new Set(rows.map(use => bindingProvenance(use).label))];
      item.append(detail, source, make('td', kinds.join(' · ')), make('td', count));
      return item;
    }));
    if (!page.length) {
      const item = make('tr');
      const message = make('td', 'No geometry bindings match these filters.');
      message.colSpan = 4;
      item.append(message); body.append(item);
    }
  }
  $('binding-pagination').hidden = pages <= 1;
  $('binding-page').textContent = (bindingPage + 1) + ' / ' + pages;
  $('binding-previous').disabled = bindingPage === 0;
  $('binding-next').disabled = bindingPage + 1 === pages;
}

$('coverage-bindings').ontoggle = () => rowsView();
$('binding-previous').onclick = () => { bindingPage--; rowsView(); };
$('binding-next').onclick = () => { bindingPage++; rowsView(); };

function provenanceView(row) {
  const panel = $('binding-provenance');
  panel.hidden = !row || Boolean(requirementLabel(row));
  if (panel.hidden) return;
  const binding = bindingOf(row);
  const matched = uses.get(binding) ?? [];
  const content = panel.querySelector('div');
  const signature = [rowID(row), ...matched.map(rowID)].join('|');
  if (content.dataset.signature === signature) return;
  content.dataset.signature = signature;
  content.replaceChildren();
  const provenance = bindingProvenance(row);
  const facts = make('dl');
  const add = (label, value, url) => {
    if (!value) return;
    const term = make('dd', url ? undefined : value);
    if (url) {
      const link = make('a', value);
      link.href = url;
      term.append(link);
    }
    facts.append(make('dt', label), term);
  };
  add('Binding kind', provenance.label ?? provenance.kind);
  add('Geometry source', provenance.source, provenance.url);
  add('Source revision', provenance.revision);
  if (row.mesh) add('Delivered mesh file', new URL(row.mesh, location.href).pathname.split('/').pop(), row.mesh);
  if (row.meshDigest) add('Fitted geometry', row.meshDigest);
  add('Evidence', provenance.evidence);
  if (provenance.origin) {
    add('Original binding kind', provenance.origin.label ?? provenance.origin.kind);
    add('Original source', provenance.origin.source, provenance.origin.url);
    add('Original revision', provenance.origin.revision);
  }
  content.append(facts);
  const filter = make('a', 'Browse this binding');
  const url = new URL('assets.html', location.href);
  url.searchParams.set('binding', binding);
  filter.href = url.href;
  content.append(filter);
  const groupedUses = grouped(matched, (use) => use.source + '/' + use.case);
  const at = make('h4', 'Uses of this binding');
  content.append(at);
  for (const group of groupedUses.values()) {
    const use = group[0];
    const detail = make('details');
    const acquisitions = new Map(group.map((candidate) => [acquisitionKey(candidate), candidate]));
    detail.append(make('summary', use.title + ' · ' + acquisitions.size +
      (acquisitions.size === 1 ? ' acquisition' : ' acquisitions')));
    const list = make('ul');
    for (const candidate of acquisitions.values()) {
      const item = make('li');
      const link = make('a', candidate.chapterTitle || candidate.title);
      link.href = acquisitionURL(candidate);
      const inspect = make('a', 'Inspect use');
      inspect.href = '#' + rowID(candidate);
      item.append(link, ' · ', inspect);
      const useProvenance = bindingProvenance(candidate);
      if (useProvenance.kind !== provenance.kind && useProvenance.label) item.append(' · ' + useProvenance.label);
      list.append(item);
      if (candidate.source === 'sweep') {
        for (const tour of toursOf(candidate).filter(({ kind }) => kind === 'orientation')) {
          const orientation = make('li');
          const link = make('a', tour.label);
          link.href = tour.url;
          orientation.append(link); list.append(orientation);
        }
      }
    }
    detail.append(list); content.append(detail);
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

function releasePortrait() {
  if (!portrait) return;
  viewer.scene.remove(portrait);
  if (loadedScene) {
    loadedScene.dispose();
    loadedScene = undefined;
  } else {
    dispose(portrait);
  }
  portrait = undefined;
  viewer.invalidate();
}

function mount(object, bounds = new THREE.Box3().setFromObject(object)) {
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
  releasePortrait();
  portrait = new THREE.Group();
  portrait.add(object);
  portrait.scale.setScalar(scale);
  portrait.position.copy(center).multiplyScalar(-scale);
  viewer.scene.add(portrait);
  viewer.reframe(pivot, presets);
  viewer.setViewPreset('oblique');
  return size.toArray().map((value) => value.toFixed(1)).join(' × ') + ' mm';
}

function resetRequirementContext() {
  delete $('preview').dataset.requirementContext;
  delete $('mesh').dataset.contextReady;
  $('mesh').setAttribute('aria-label', 'Anatomy viewport');
  $('requirement-art').hidden = $('context-caption').hidden = $('context-source').hidden = true;
}

function showAcquisitionLink(row, text = 'Open acquisition') {
  const route = $('route');
  route.href = acquisitionURL(row);
  route.textContent = text;
  const notes = $('acquisition-notes');
  const labels = [...new Set(row.acquisitionNotes?.map(({ label }) => label) ?? [])];
  notes.hidden = !labels.length;
  notes.textContent = labels.length ? 'On the acquisition · ' + labels.join(' · ') : '';
}

function showIllustration(row, layout = 'art') {
  const art = illustrationFor(row);
  if (!art) return false;
  $('preview').hidden = false;
  $('preview').dataset.requirementContext = layout;
  $('context-caption').hidden = layout === 'art';
  $('mesh').hidden = $('views').hidden = $('mesh-help').hidden = true;
  $('geometry-checks').hidden = $('mesh-file').hidden = $('composed-uses').hidden = $('donor-source').hidden = true;
  showAcquisitionLink(row, 'Open requirement acquisition');
  $('requirement-art').hidden = false;
  $('requirement-art-caption').textContent = art.caption ?? '';
  const image = $('requirement-art-image');
  if (image.getAttribute('src') !== art.src) {
    image.hidden = true;
    $('requirement-art-error').hidden = true;
    image.alt = art.alt;
    image.src = art.src;
  }
  return true;
}

$('requirement-art-image').onload = () => {
  $('requirement-art-image').hidden = false;
  $('requirement-art-error').hidden = true;
};
$('requirement-art-image').onerror = () => {
  $('requirement-art-image').hidden = true;
  $('requirement-art-error').hidden = false;
};

async function showGapContext(row, request) {
  const donor = row.part === 'gallbladder-wall' && [...inventory.values()].find((candidate) =>
    candidate.case === row.case && candidate.chapter === row.chapter &&
    candidate.donor?.source === 'sweep' && candidate.donor.case === 'gallbladder' &&
    candidate.donor.part === 'gallbladder' && candidate.mesh && candidate.meshDigest);
  if (!showIllustration(row, donor ? 'paired' : 'art')) return;
  $('mesh-status').textContent = donor ? 'Loading the original gallbladder mesh…' : '';
  if (!donor) return;
  const origin = inventory.get(rowID(donor.donor));
  const source = $('context-source');
  source.hidden = false;
  const link = make('a', 'Inspect original gallbladder mesh');
  link.href = origin ? '#' + rowID(origin) : donor.donor.url;
  source.replaceChildren(link);
  if (origin) {
    const sweep = make('a', 'Original sweep');
    sweep.href = donor.donor.url;
    source.append(' · ', sweep);
  }
  $('context-caption').textContent = 'Live source mesh · whole gallbladder';
  let geometry;
  try {
    geometry = await isolatedMesh(origin ?? donor, entries);
    if (request !== selectedRequest || current !== row) { geometry.dispose(); return; }
    $('mesh').hidden = $('views').hidden = $('mesh-help').hidden = false;
    $('mesh').setAttribute('aria-label', 'Live whole-gallbladder source mesh');
    const material = new THREE.MeshStandardMaterial({ color: donor.color ?? '#ded3bc', roughness: .72, side: THREE.DoubleSide });
    mount(new THREE.Mesh(geometry, material));
    $('mesh').dataset.contextReady = rowID(origin ?? donor);
    $('mesh-status').textContent = 'The source mesh shows the whole organ. The wall is missing as independent geometry. The illustration labels its location.';
  } catch (cause) {
    geometry?.dispose();
    if (request !== selectedRequest || current !== row) return;
    $('mesh').hidden = $('views').hidden = $('mesh-help').hidden = true;
    $('mesh-status').textContent = 'Original source mesh unavailable.';
    console.warn(cause);
  }
}

function resetAssembled() {
  sceneRequest++;
  desiredScene = '';
  $('acquisition-field').hidden = $('visibility').hidden = true;
  delete $('preview').dataset.assembled;
  resetRequirementContext();
}

function acquisitionLabel(row) {
  const title = row.chapterTitle ? row.title + ' · ' + row.chapterTitle : row.title;
  return independentReference(row) ? title + ' · ' + (row.donor?.label ?? 'Source geometry') : title;
}

function donorLink(row, parts = [row]) {
  const panel = $('donor-source');
  panel.hidden = !row.donor?.url;
  panel.replaceChildren();
  if (!panel.hidden) {
    const link = make('a', row.donor.label ?? 'Open original geometry source');
    link.href = row.donor.url;
    panel.append('Geometry source · ', link);
    if (row.credit) {
      panel.append(make('br'), make('span', row.credit, 'source-credit'));
      if (row.attribution) {
        const attribution = make('a', 'Attribution');
        attribution.href = row.attribution;
        panel.append(' · ', attribution);
      }
    }
    for (const part of parts.filter(({ referenceScope }) => Boolean(referenceScope))) {
      panel.append(make('br'), make('span', (part.partLabel ?? part.label) + ' · ' + part.referenceScope, 'source-credit'));
    }
  }
}

function visibilityView(model, key) {
  const groupBy = mode === 'scene' ? assetOf : partOf;
  const groups = new Map();
  for (const part of model.parts) {
    const id = groupBy(part.row);
    if (!groups.has(id)) groups.set(id, []);
    groups.get(id).push(part);
  }
  const hidden = hiddenElements.get(key) ?? new Set();
  hiddenElements.set(key, hidden);
  const fields = [...groups].map(([id, parts]) => {
    const { row } = parts[0];
    const text = mode === 'scene' ? row.assetLabel ?? row.title : row.partLabel ?? row.label;
    const label = make('label', undefined, 'tour-choice');
    const input = make('input');
    input.type = 'checkbox';
    input.value = id;
    input.checked = !hidden.has(id);
    for (const { object } of parts) object.visible = input.checked;
    input.onchange = () => {
      if (input.checked) hidden.delete(id);
      else hidden.add(id);
      for (const { object } of parts) object.visible = input.checked;
      viewer.invalidate();
    };
    label.append(input, make('span', text));
    return label;
  }).sort((left, right) => byText(left.textContent, right.textContent));
  $('visibility-title').textContent = mode === 'scene' ? 'Visible assets' : 'Visible parts';
  $('visibility-list').replaceChildren(...fields);
  $('visibility').hidden = !fields.length;
  viewer.invalidate();
}

function assembledView(candidates) {
  const gaps = candidates.filter((row) => assetOf(row) === openAsset && requirementLabel(row));
  candidates = candidates.filter((row) => !requirementLabel(row));
  const scoped = openAsset ? candidates.filter((row) => assetOf(row) === openAsset) : mode === 'scene' ? candidates : [];
  if (!scoped.length) {
    resetAssembled();
    releasePortrait();
    delete $('mesh').dataset.ready;
    $('preview').hidden = true;
    $('selection').textContent = openAsset && !remaining && !pendingAAA ? 'Asset unavailable' : 'Select an asset';
    $('selection-context').textContent = openAsset && !remaining && !pendingAAA
      ? 'This asset has no acquisitions in the current scope.'
      : 'Choose an asset from the shelf.';
    if (gaps.length) {
      $('selection').textContent = gaps[0].assetLabel;
      $('selection-context').textContent = gaps.some((row) => row.status === 'rebuild')
        ? 'Rebuild required · Geometry is unavailable for these tour requirements.'
        : 'Geometry is unavailable for these tour requirements.';
      const illustrated = gaps.find((row) => row.status === 'rebuild' && illustrationFor(row));
      if (illustrated && showIllustration(illustrated)) $('mesh-status').textContent = '';
    } else if (!remaining && !pendingAAA && retiredUses.size && retiredAssets.has(openAsset) && !assets.has(openAsset)) {
      $('selection').textContent = 'Retired geometry';
      $('selection-context').textContent = 'This bookmark points to a retired abdominal model. Choose an available source asset or tour requirement from the shelf.';
    }
    return;
  }
  const relevant = openAsset ? (assets.get(openAsset) ?? []).filter(inScope) : scoped;
  const available = new Set(scoped.map(viewKey));
  const groups = [...grouped(relevant, viewKey)].filter(([key]) => available.has(key));
  if (!groups.some(([, rows]) => rows[0].donor)) {
    groups.sort(([, left], [, right]) =>
      new Set(right.map(partOf)).size - new Set(left.map(partOf)).size ||
      (left[0].case === right[0].case ? 0 : byText(acquisitionLabel(left[0]), acquisitionLabel(right[0]))));
  }
  const [key, rows] = groups.find(([id]) => id === acquisition) ?? groups[0];
  const row = rows[0];
  $('acquisition-field').hidden = false;
  const select = $('acquisition');
  const signature = groups.map(([id]) => id).join('|');
  if (select.dataset.options !== signature) {
    select.dataset.options = signature;
    select.replaceChildren(...groups.map(([id, [item]]) => new Option(acquisitionLabel(item), id)));
  }
  select.value = key;
  $('selection').textContent = mode === 'scene'
    ? independentReference(row) ? 'Source geometry' : 'Acquisition scene'
    : row.assetLabel ?? row.title;
  $('selection-context').textContent = independentReference(row) ? 'Source geometry · registration to this tour is unavailable.' : '';
  const sceneKey = [mode, mode === 'asset' ? openAsset : '', key].join('|');
  if (desiredScene === sceneKey) return;
  desiredScene = sceneKey;
  showAssembly(row, sceneKey, key);
}

async function showAssembly(row, sceneKey, key) {
  const request = ++sceneRequest;
  const viewMode = mode;
  const asset = openAsset;
  resetRequirementContext();
  releasePortrait();
  $('visibility').hidden = $('geometry-checks').hidden = $('mesh-file').hidden = $('composed-uses').hidden = true;
  $('preview').hidden = false;
  $('preview').dataset.assembled = '';
  delete $('mesh').dataset.ready;
  $('mesh-status').textContent = 'Loading acquisition geometry…';
  donorLink(row);
  showAcquisitionLink(row);
  let model;
  try {
    model = await acquireScene(row, inventory, entries);
    if (request !== sceneRequest) { model.dispose(); return; }
    const visibleParts = model.parts.filter(({ row: part }) => viewMode === 'scene' || assetOf(part) === asset);
    if (!visibleParts.length) throw Error('No components were loaded for this asset.');
    const visible = new Set(visibleParts);
    for (const part of model.parts) part.object.visible = visible.has(part);
    if (viewMode === 'asset') for (const helper of model.helpers) helper.visible = false;
    model.object.updateMatrixWorld(true);
    const bounds = new THREE.Box3();
    for (const { object } of visibleParts) bounds.expandByObject(object);
    $('mesh').hidden = $('views').hidden = $('mesh-help').hidden = false;
    mount(model.object, bounds);
    loadedScene = model;
    visibilityView({ parts: visibleParts }, sceneKey);
    if (row.donor) donorLink(row, visibleParts.map(({ row }) => row));
    $('mesh').dataset.ready = key;
    $('mesh-status').textContent = [model.sourceNotice ?? row.sourceNotice,
      model.issues.length ? 'Some components are unavailable. ' + model.issues.join(' · ') : ''].filter(Boolean).join(' ');
  } catch (cause) {
    if (model && loadedScene !== model) model.dispose();
    if (request !== sceneRequest) return;
    releasePortrait();
    $('mesh').hidden = $('views').hidden = $('mesh-help').hidden = true;
    $('mesh-status').textContent = 'Acquisition geometry unavailable. The acquisition link remains available.';
    console.warn(cause);
  }
}

$('workspace-mode').onclick = (event) => {
  const button = event.target.closest('button[data-mode]');
  if (!button || (mode === button.dataset.mode && !current)) return;
  if (current && !requirementLabel(current)) acquisition = viewKey(current);
  else if (!$('acquisition-field').hidden) acquisition = $('acquisition').value;
  mode = button.dataset.mode;
  const url = filterState();
  if (current) url.hash = assetFragment(openAsset);
  history.pushState(null, '', url);
  refresh();
};

$('acquisition').onchange = () => {
  acquisition = $('acquisition').value;
  history.pushState(null, '', filterState());
  rowsView();
};

function coordinateSelection(row) {
  const grade = linked(row);
  const rowRegion = regionOf(row);
  if (region && region !== rowRegion) region = rowRegion;
  if (tourSelection !== null && !toursOf(row).some(({ id }) => tourSelection.has(id))) {
    tourSelection = new Set(toursOf(row).slice(0, 1).map(({ id }) => id));
  }
  if ($('query').value) $('query').value = '';
  if (bindingFilter !== bindingOf(row)) bindingFilter = '';
  if ($('reuse').value && (uses.get(bindingOf(row))?.length ?? 0) < 2) $('reuse').value = '';
  if (requirementLabel(row)) $('assessment').value = '';
  if (($('availability').value === 'gaps' && !requirementLabel(row)) ||
      ($('availability').value === 'geometry' && requirementLabel(row))) $('availability').value = '';
  if ($('assessment').value && !matchesAssessment(grade, $('assessment').value)) $('assessment').value = '';
  renderScope();
  setFilters();
}

function selectionEvidence(row) {
  if (requirementLabel(row)) {
    $('selection-context').textContent = requirementLabel(row);
    return;
  }
  $('selection-context').textContent = [row.title, row.chapterTitle, rateLabel(linked(row))].filter(Boolean).join(' · ');
  evidenceView(row);
}

async function showPart(key, fromLink = false) {
  const row = inventory.get(key);
  if (!row) return;
  if (fromLink) coordinateSelection(row);
  resetAssembled();
  releasePortrait();
  $('variants').open = true;
  linkedSelection = fromLink;
  current = row;
  openAsset = assetOf(row);
  selection = key;
  const request = ++selectedRequest;
  $('selection').textContent = row.label;
  $('inspector').scrollTop = 0;
  if (requirementLabel(row)) {
    $('preview').hidden = $('evidence').hidden = $('part-uses').hidden = true;
    delete $('mesh').dataset.ready;
    selectionEvidence(row);
    rowsView();
    showGapContext(row, request);
    return;
  }
  $('preview').hidden = false;
  $('mesh').hidden = true;
  delete $('mesh').dataset.ready;
  $('views').hidden = true;
  $('mesh-help').hidden = true;
  $('mesh-status').textContent = 'Loading isolated mesh…';
  donorLink(row);
  $('geometry-checks').hidden = true;
  $('geometry-topology').textContent = '';
  $('topology').disabled = false;
  showAcquisitionLink(row);
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
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
      color: '#ded3bc', roughness: .72, side: THREE.DoubleSide,
    }));
    const size = mount(mesh);
    const triangles = Math.floor((geometry.index?.count ?? geometry.attributes.position.count) / 3);
    $('mesh').dataset.ready = key;
    $('mesh-status').textContent = 'Bounds · ' + size + (independentReference(row)
      ? ' · Coordinates from the geometry source.' : row.referenceScope ? ' · ' + row.referenceScope : '');
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
  const geometry = portrait?.children[0]?.geometry;
  if (!geometry) return;
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
  index = bindingPage = 0;
  if ($('availability').value === 'gaps') $('assessment').value = '';
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
$('filters').onreset = () => setTimeout(() => {
  region = '';
  tourSelection = null;
  bindingFilter = '';
  filtersChanged();
}, 0);
$('previous').onclick = () => { index--; rowsView(); };
$('next').onclick = () => { index++; rowsView(); };
window.addEventListener('popstate', () => {
  restoreFilters();
  refresh();
});
window.addEventListener('hashchange', refresh);
function focusInspector() {
  $('inspector').scrollTop = 0;
  const target = $('selection');
  const { top, bottom } = target.getBoundingClientRect();
  target.focus({ preventScroll: top >= 0 && bottom <= window.innerHeight });
}

function activateLink(event) {
  const link = event.target.closest('a');
  if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
  if (!link.getAttribute('href')?.startsWith('#')) return;
  event.preventDefault();
  const key = link.hash.slice(1);
  const fromScene = mode === 'scene';
  if (link.dataset.asset) {
    const candidate = $('acquisition').value;
    const sharesAcquisition = (assets.get(link.dataset.asset) ?? []).some((row) =>
      inScope(row) && viewKey(row) === candidate);
    if (fromScene || link.dataset.asset !== openAsset) acquisition = fromScene && sharesAcquisition ? candidate : '';
    mode = 'asset';
  } else if (!key) {
    acquisition = '';
  }
  if (location.hash !== link.hash || (link.dataset.asset && fromScene)) {
    const url = filterState();
    url.hash = key;
    history.pushState(null, '', url);
  }
  if (key && !key.startsWith('asset/')) {
    const row = inventory.get(key);
    if (row) {
      showPart(key, !rowMatches(row, searchTerms(), $('assessment').value));
      focusInspector();
    }
  } else {
    const from = openAsset;
    refresh();
    if (key) focusInspector();
    else [...$('rows').querySelectorAll('[data-asset]')].find((anchor) => anchor.dataset.asset === from)?.focus();
  }
}
for (const id of ['rows', 'asset-detail', 'part-uses', 'requirements', 'context-source', 'binding-provenance', 'coverage-bindings']) $(id).addEventListener('click', activateLink);

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
  coverageView(manifest);
  setProvenanceInventory(manifest);
  setTeachingTours(manifest.teachingTours ?? []);
  manifest.cases.filter(({ family }) => family !== 'aaa').forEach((entry) => entries.set(entry.id, entry));
  remaining = entries.size + 1;
  const originals = Promise.resolve().then(sweepRows).then(recordRows).catch((cause) => {
    failures.push('Original sweeps · ' + cause.message);
  }).finally(() => {
    remaining--;
    refresh();
  });
  const aaa = aaaRows(manifest.cases).then(({ rows, issues }) => {
    recordRows(rows);
    failures.push(...issues.map((issue) => 'AAA · ' + issue));
  }).finally(() => {
    pendingAAA = false;
    refresh();
  });
  refresh();
  const chapterMeshHashes = new Map();
  await Promise.allSettled((manifest.reviews ?? []).map(async (path) => {
    try {
      const { records, recipeHash, rubricHash } = await read(path);
      for (const record of records) {
        const owner = entries.get(record.case)?.owner ?? (record.source === 'aaa' ? 'vascular' : undefined);
        const emittedMesh = manifest.sweepHashes?.[record.case]?.[record.part];
        let prior;
        if (record.source !== 'sweep' && ('meshSha256' in record || 'chapterSha256' in record)) {
          prior = await chapterMeshReviewPrior(manifest, record, rubricHash, chapterMeshHashes);
        } else {
          prior = record.source === 'sweep'
            ? (manifest.sweepHashes && (!emittedMesh || emittedMesh !== record.meshSha256)) ||
              (manifest.rubricHash && manifest.rubricHash !== rubricHash)
            : owner && manifest.recipeHashes?.[owner] && manifest.recipeHashes[owner] !== recipeHash;
        }
        const index = record.occurrence ? reviews : uniqueReviews;
        const key = record.occurrence ? rowID(record) : frameKey({ ...record, chapter: record.chapter ?? '' });
        // An older revision may finish loading after the review for the served mesh.
        if (!prior || !index.has(key) || index.get(key).prior) index.set(key, { ...record, prior });
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
