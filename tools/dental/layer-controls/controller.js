/* Deterministic editorial control state. No mesh mutation, physiology or clinical claim. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.DentalControls = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const LABELS = Object.freeze(['enamel', 'dentin', 'pulp', 'bone']);
  const OFFSETS = Object.freeze(Object.fromEntries(Object.entries({enamel:[.012,0,0],dentin:[0,0,0],pulp:[.006,.006,0],bone:[-.012,0,0]}).map(([key,value])=>[key,Object.freeze(value)])));
  const IDENTITY = Object.freeze([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
  function createController(parts) {
    if (!Array.isArray(parts) || parts.length !== LABELS.length) throw new Error('Exactly four source-labelled parts are required.');
    const baseline = new Map();
    for (const part of parts) {
      if (!LABELS.includes(part.label) || baseline.has(part.label)) throw new Error('Missing, duplicate or unsupported source label.');
      const matrix = part.matrix || IDENTITY;
      if (!Array.isArray(matrix) || matrix.length !== 16 || !matrix.every(Number.isFinite)) throw new Error('Invalid source transform.');
      baseline.set(part.label, Object.freeze([...matrix]));
    }
    let current = Object.freeze({reveal:0, isolate:null});
    function snapshot() { return {...current}; }
    function dispatch(action) {
      if (!action || typeof action.type !== 'string') throw new Error('Invalid control action.');
      let next = {...current};
      if (action.type === 'reveal') {
        if (!Number.isFinite(action.value) || action.value < 0 || action.value > 1) throw new Error('Reveal must be finite and between 0 and 1.');
        next.reveal = action.value;
      } else if (action.type === 'isolate') {
        if (!LABELS.includes(action.label)) throw new Error('Unknown source label.');
        next.isolate = action.label;
      } else if (action.type === 'all') next.isolate = null;
      else if (action.type === 'reset') next = {reveal:0,isolate:null};
      else throw new Error('Unknown control action.');
      current = Object.freeze(next);
      return snapshot();
    }
    function resolve() {
      return LABELS.map(label => {
        const matrix = [...baseline.get(label)];
        if (current.reveal !== 0) for (let k=0;k<3;k++) matrix[12+k] += OFFSETS[label][k] * current.reveal;
        return {label, visible:current.isolate === null || current.isolate === label, matrix};
      });
    }
    return Object.freeze({snapshot,dispatch,resolve});
  }
  return Object.freeze({LABELS, OFFSETS, IDENTITY, createController});
});
