import { regions } from './assets-identity.js';

const tourFamilies = {
  aaa: 'AAA screening', abdomen: 'Abdominal tours', breast: 'Breast and axillary tours',
  carotid: 'Carotid duplex', echo: 'Echocardiography', thyroid: 'Thyroid tours',
  'pregnancy-early': 'Early pregnancy tours', 'pregnancy-first': 'First trimester tours',
  'pregnancy-mid': 'Mid-pregnancy tours', 'pregnancy-late': 'Late pregnancy tours',
};

function sweepGroup(tour) {
  const sweep = tour.id.slice('sweep:'.length);
  if (tour.region === 'abdomen') {
    if (/^(aort|ivc)/.test(sweep)) return 'Great vessels';
    if (sweep.startsWith('kidney')) return 'Kidneys';
    if (['gallbladder', 'liver', 'portal-vein'].includes(sweep)) return 'Liver and biliary tract';
    if (['pancreas', 'spleen'].includes(sweep)) return 'Pancreas and spleen';
  }
  if (tour.region === 'pregnancy') {
    if (sweep.startsWith('pregnancy-mid-')) return 'Mid-pregnancy';
    if (sweep.startsWith('pregnancy-late-')) return 'Late pregnancy';
    return 'Pregnancy overview';
  }
  return '';
}

function pathFor(tour, byRegion) {
  const path = byRegion ? [regions[tour.region] ?? tour.region] : [];
  if (tour.kind === 'sweep') {
    path.push('Standalone sweeps');
    const topic = sweepGroup(tour);
    if (topic) path.push(topic);
  } else {
    path.push(tour.kind === 'orientation' ? 'Orientation tours' : tourFamilies[tour.family] ?? 'Case tours');
  }
  return path;
}

function treeFor(tours) {
  const byRegion = new Set(tours.map(tour => tour.region)).size > 1;
  const group = label => ({ label, groups: new Map(), tours: [], ids: [] });
  const root = group('');
  for (const tour of tours) {
    let node = root;
    for (const label of pathFor(tour, byRegion)) {
      if (!node.groups.has(label)) node.groups.set(label, group(label));
      node = node.groups.get(label);
      node.ids.push(tour.id);
    }
    node.tours.push(tour);
  }
  return root;
}

// Inventory arrives in batches. Keep open branches and keyboard focus across
// those updates, and leave the DOM in place when only check states change.
const choosers = new WeakMap();

export function renderTourChooser(container, tours, selection, onChange) {
  const key = JSON.stringify(tours.map(t => [t.id, t.region, t.kind, t.family, t.label]));
  let state = choosers.get(container);
  if (!state || state.key !== key) {
    const open = new Set([...container.querySelectorAll('details[open]')].map(el => el.dataset.path));
    const focus = container.contains(document.activeElement) ? document.activeElement.dataset.key : null;
    const bindings = [];
    const checkbox = (ids, name, count) => {
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.dataset.key = name;
      input.addEventListener('change', () => {
        const next = new Set(tours.filter(t => state.selection === null || state.selection.has(t.id)).map(t => t.id));
        for (const id of ids) {
          if (input.checked) next.add(id);
          else next.delete(id);
        }
        state.onChange(next.size === tours.length ? null : next);
      });
      bindings.push({ input, ids, count });
      return input;
    };
    const branch = (node, path) => {
      const list = document.createDocumentFragment();
      for (const group of [...node.groups.values()].sort((a, b) => a.label.localeCompare(b.label))) {
        const item = document.createElement('div');
        item.className = 'tour-group';
        const name = path + '/' + group.label;
        const count = document.createElement('small');
        const input = checkbox(group.ids, 'check:' + name, count);
        input.setAttribute('aria-label', 'Select all in ' + group.label);
        const disclosure = document.createElement('details');
        disclosure.dataset.path = name;
        disclosure.open = open.has(name);
        const summary = document.createElement('summary');
        summary.dataset.key = 'open:' + name;
        summary.textContent = group.label;
        summary.append(' ', count);
        const children = document.createElement('div');
        children.className = 'tour-group-children';
        children.append(branch(group, name));
        disclosure.append(summary, children);
        item.append(input, disclosure);
        list.append(item);
      }
      for (const tour of node.tours) {
        const label = document.createElement('label');
        label.className = 'tour-choice';
        const input = checkbox([tour.id], tour.id);
        input.name = 'tour';
        input.value = tour.id;
        label.append(input, tour.label);
        list.append(label);
      }
      return list;
    };
    container.replaceChildren(branch(treeFor(tours), ''));
    if (focus) [...container.querySelectorAll('[data-key]')].find(el => el.dataset.key === focus)?.focus();
    state = { key, bindings };
    choosers.set(container, state);
  }
  Object.assign(state, { selection, onChange });
  for (const { input, ids, count } of state.bindings) {
    const n = selection === null ? ids.length : ids.filter(id => selection.has(id)).length;
    input.checked = n === ids.length;
    input.indeterminate = n > 0 && n < ids.length;
    if (count) count.textContent = n === ids.length ? String(n) : n + '/' + ids.length;
  }
}
