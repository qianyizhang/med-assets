'use strict';

const $ = (id) => document.getElementById(id);
const tours = typeof abdomenTours === 'undefined' ? [] : abdomenTours;
const references = typeof abdomenReferences === 'undefined' ? {} : abdomenReferences;
const batch = typeof ultrasoundRenderComparison === 'undefined' ? null : ultrasoundRenderComparison;
const studyRoot = new URL('../', location.href);
const params = new URLSearchParams(location.search);
const view = params.get('view') === 'bmode' ? 'bmode' : 'motion';
const regionOf = (tour) => tour.bodyRegion ?? 'Abdomen';
const choice = (label, value) => new Option(label, value);
const clipPath = (tour, extension) => 'clips/' + tour.id + '.' + extension;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function link(text, href, className) {
  const result = node('a', text, className);
  result.href = href;
  return result;
}

function studyLink(tour, key) {
  const target = new URL('index.html', studyRoot);
  target.searchParams.set('sweep', tour.id);
  if (key) target.searchParams.set('frame', key.frame);
  return target.href;
}

function reviewLink({ mode = view, region = $('region').value, sweep = '', pair = $('batch').value }) {
  const query = new URLSearchParams({ view: mode });
  if (region) query.set('region', region);
  if (sweep) query.set('sweep', sweep);
  if (mode === 'bmode' && pair === 'batch') query.set('renders', pair);
  return '?' + query;
}

function scanPath(tour, frame) {
  return new URL(tour.assetRoot + 'media/scan-' + String(frame).padStart(2, '0') + '.webp', studyRoot);
}

function mediaImage(path, title, unavailable, { eager = false } = {}) {
  const slot = node('div', null, 'image-slot');
  const missing = node('span', unavailable, 'missing');
  if (!path) {
    slot.append(missing);
    return slot;
  }
  const image = node('img');
  image.alt = title;
  image.width = 500;
  image.height = 350;
  image.decoding = 'async';
  if (eager) image.fetchPriority = 'high';
  else image.loading = 'lazy';
  image.addEventListener('error', () => slot.replaceChildren(missing), { once: true });
  image.src = path;
  slot.append(image);
  return slot;
}

function clipPlayer(tour, title, { detail = false, lazy = false } = {}) {
  const slot = node('div', null, 'clip-slot');
  const video = node('video');
  video.controls = true;
  video.playsInline = true;
  video.preload = detail ? 'metadata' : 'none';
  video.width = 960;
  video.height = 416;
  video.setAttribute('aria-labelledby', title.id);
  if (lazy) video.setAttribute('loading', 'lazy');
  video.poster = clipPath(tour, 'webp');
  const missing = node('p', 'Motion clip unavailable', 'missing');
  missing.setAttribute('role', 'status');
  video.addEventListener('error', () => slot.replaceChildren(missing), { once: true });
  video.src = clipPath(tour, 'mp4');
  video.append('This browser cannot play the motion clip.');
  slot.append(video);
  return slot;
}

function renderMotion(visible) {
  const output = node('div', null, 'motion-grid');
  for (const [index, tour] of visible.entries()) {
    const card = node('article', null, 'motion-card');
    const href = reviewLink({ sweep: tour.id });
    const caption = node('div', null, 'card-caption');
    const title = node('h2', tour.title);
    title.id = 'clip-title-' + tour.id;
    const actions = node('div', null, 'clip-actions');
    actions.append(link('Clip detail', href, 'open-sweep'), link('Open sweep', studyLink(tour), 'open-sweep'));
    caption.append(title, node('p', regionOf(tour)), actions);
    card.append(clipPlayer(tour, title, { lazy: index >= 4 }), caption);
    output.append(card);
  }
  return output;
}

function renderMotionDetail(tour) {
  const detail = node('article', null, 'motion-detail');
  const header = node('div', null, 'detail-head');
  const title = node('h2', tour.title);
  title.id = 'clip-title';
  header.append(title, link('Back to motion collection', reviewLink({})));
  detail.append(header, clipPlayer(tour, title, { detail: true }), link('Open sweep', studyLink(tour), 'open-sweep'));
  return detail;
}

function comparisonImage(label, path, alt, unavailable, eager) {
  const figure = node('figure');
  const caption = node('figcaption');
  caption.append(node('p', label, 'figure-title'));
  figure.append(caption, mediaImage(path, alt, unavailable, { eager }));
  return figure;
}

function appendCredit(figure, acquired) {
  if (!acquired) return;
  const line = node('p', null, 'source-credit');
  if (acquired.url) line.append(link(acquired.credit ?? 'Acquired image source', acquired.url));
  else if (acquired.credit) line.append(acquired.credit);
  if (acquired.license) {
    if (line.textContent) line.append(' · ');
    line.append(acquired.licenseUrl ? link(acquired.license, acquired.licenseUrl) : acquired.license);
  }
  if (line.textContent) figure.append(line);
}

function renderComparison(tour, key, eager, showBatch) {
  const row = node('article', null, showBatch ? 'comparison batch' : 'comparison');
  const facts = node('div', null, 'row-meta');
  const acquired = references[key.referenceId];
  const record = showBatch ? batch.rows[tour.id + '/' + key.frame] : null;
  const referenceMatch = acquired && record?.referenceId === key.referenceId;
  facts.append(node('h3', key.label), node('p', 'Frame ' + key.frame),
    link('Open keyframe', studyLink(tour, key), 'open-sweep'));
  if (acquired) {
    const context = [tour.referenceContext, acquired.depthLabel].filter(Boolean);
    facts.append(node('p', ['Different case', ...context].join(' · ')));
  }
  if (showBatch) {
    const status = !referenceMatch ? 'Outside this batch' : record.changed ? 'Render updated' : 'Identical render file';
    facts.append(node('p', status));
  }
  row.append(facts);
  if (showBatch) {
    row.append(comparisonImage(batch.beforeLabel, referenceMatch ? record.before : null,
      'Previous render for ' + key.label, 'Previous render unavailable', eager && referenceMatch));
  }
  row.append(comparisonImage(showBatch ? batch.afterLabel : 'Current render',
    showBatch ? (referenceMatch ? record.after : null) : scanPath(tour, key.frame),
    'Simulated B-mode for ' + key.label, 'Simulated frame unavailable', eager && !showBatch));
  const acquiredPath = showBatch ? (referenceMatch ? record.reference : null)
    : (acquired?.path ? new URL(acquired.path, studyRoot) : null);
  const comparison = comparisonImage('Acquired ultrasound', acquiredPath,
    acquired?.title ?? key.label, 'Acquired reference unavailable', eager && !showBatch);
  if (acquired) {
    const referenceLabel = key.referenceLabel ?? acquired.label ?? acquired.title;
    if (referenceLabel) comparison.append(node('p', referenceLabel, 'figure-title status-note'));
    if (acquired.note) comparison.append(node('p', acquired.note, 'status-note'));
  }
  appendCredit(comparison, acquired);
  row.append(comparison);
  return row;
}

function renderBMode(visible, showBatch) {
  const output = document.createDocumentFragment();
  const overview = !$('sweep').value && !showBatch;
  let first = true;
  for (const tour of visible) {
    const group = node('section', null, overview ? 'sweep-group overview' : 'sweep-group');
    const heading = node('div', null, 'sweep-heading');
    const title = node('h2');
    if (overview) title.append(link(tour.title, reviewLink({ sweep: tour.id })));
    else title.textContent = tour.title;
    heading.append(title, node('small', regionOf(tour)));
    group.append(heading);
    for (const key of tour.keyframes) {
      group.append(renderComparison(tour, key, first, showBatch));
      first = false;
    }
    output.append(group);
  }
  return output;
}

function setSweeps(requested) {
  const region = $('region').value;
  const scoped = tours.filter((tour) => !region || regionOf(tour) === region);
  $('sweep').replaceChildren(choice('All sweeps', ''), ...scoped.map((tour) => choice(tour.title, tour.id)));
  if (scoped.some((tour) => tour.id === requested)) $('sweep').value = requested;
  return scoped;
}

function update(writeUrl = false) {
  const region = $('region').value;
  const sweep = $('sweep').value;
  const showBatch = view === 'bmode' && batch && $('batch').value === 'batch';
  $('motion-link').href = reviewLink({ mode: 'motion', pair: 'current', sweep });
  $('bmode-link').href = reviewLink({ mode: 'bmode', sweep });
  if (writeUrl) history.replaceState(null, '', reviewLink({ sweep }));
  const visible = tours.filter((tour) => (!region || regionOf(tour) === region) && (!sweep || tour.id === sweep));
  if (view === 'motion') {
    $('count').textContent = visible.length + (visible.length === 1 ? ' sweep' : ' sweeps');
    $('context').textContent = 'Review probe contact and the imaging field alongside the synchronized B-mode at a fixed camera angle.';
    $('collection').replaceChildren(sweep ? renderMotionDetail(visible[0]) : renderMotion(visible));
    return;
  }
  const keyCount = visible.reduce((count, tour) => count + tour.keyframes.length, 0);
  $('count').textContent = keyCount + (keyCount === 1 ? ' keyframe' : ' keyframes');
  $('context').textContent = showBatch
    ? 'Fixed case, pose, field and acquired image across runs. Compare the two synthetic renders at the same display scale.'
    : 'Compare named keyframes across sweeps. Acquired images are from different cases and retain their original plane and scale.';
  if (showBatch) {
    const matched = visible.flatMap(tour => tour.keyframes.flatMap(key => {
      const row = batch.rows[tour.id + '/' + key.frame];
      return row?.referenceId === key.referenceId ? [row] : [];
    }));
    $('count').textContent = matched.length + ' / ' + keyCount + ' keyframes in batch · ' +
      matched.filter(row => row.changed).length + ' updated';
  }
  $('collection').replaceChildren(renderBMode(visible, showBatch));
}

$(view + '-link').setAttribute('aria-current', 'page');
if (tours.length) {
  const regions = [...new Set(tours.map(regionOf))];
  $('region').replaceChildren(choice('All regions', ''), ...regions.map((region) => choice(region, region)));
  const requestedRegion = params.get('region');
  if (regions.includes(requestedRegion)) $('region').value = requestedRegion;
  setSweeps(params.get('sweep'));
  $('filters').hidden = false;
  $('batch-filter').hidden = view !== 'bmode' || !batch;
  if (batch && params.get('renders') === 'batch') $('batch').value = 'batch';
  $('region').addEventListener('change', () => {
    setSweeps($('sweep').value);
    update(true);
  });
  $('sweep').addEventListener('change', () => update(true));
  $('batch').addEventListener('change', () => update(true));
  update();
} else {
  $('collection').replaceChildren(node('p', 'Sweep catalogue unavailable. Open Development from an assembled ultrasound study.'));
}
