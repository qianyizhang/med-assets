// Page-session state only. Keys use source identities, never translated labels.
function context(node) {
  for (let parent = node.parentElement; parent; parent = parent.parentElement) {
    if (parent.id) return parent;
  }
  return node.ownerDocument.documentElement;
}
function pathWithin(node, root) {
  const parts = [];
  for (let item = node; item && item !== root; item = item.parentElement) {
    const siblings = [...item.parentElement.children].filter(x => x.tagName === item.tagName);
    parts.unshift(`${item.tagName}:${siblings.indexOf(item)}`);
  }
  return parts.join('/');
}
function key(node) {
  if (node.id) return `id:${node.id}`;
  const root = context(node);
  if (node.matches('.comparison[data-evidence-group]')) {
    const group = node.dataset.evidenceGroup;
    const occurrences = [...root.querySelectorAll('.comparison[data-evidence-group]')].filter(x => x.dataset.evidenceGroup === group);
    return JSON.stringify([root.id, 'comparison', group, occurrences.indexOf(node)]);
  }
  const figure = node.closest('figure[data-evidence-id]');
  if (figure && root.contains(figure)) {
    const id = figure.dataset.evidenceId;
    const occurrences = [...root.querySelectorAll('figure[data-evidence-id]')].filter(x => x.dataset.evidenceId === id);
    return JSON.stringify([root.id, 'evidence', id, occurrences.indexOf(figure), pathWithin(node, figure)]);
  }
  return JSON.stringify([root.id, pathWithin(node, root)]);
}
const controlledCandidate = node => node.parentElement?.id === 'candidates';
export function captureComparisonState(document) {
  return {
    disclosures: new Map([...document.querySelectorAll('details')].filter(x => !controlledCandidate(x)).map(x => [key(x), x.open])),
    layouts: new Map([...document.querySelectorAll('.comparison')].map(x => [key(x), x.classList.contains('single')]))
  };
}
export function restoreComparisonState(document, state) {
  for (const node of document.querySelectorAll('details')) {
    if (!controlledCandidate(node) && state.disclosures.has(key(node))) node.open = state.disclosures.get(key(node));
  }
  for (const node of document.querySelectorAll('.comparison')) {
    if (state.layouts.has(key(node))) node.classList.toggle('single', state.layouts.get(key(node)));
  }
}
