import {LAYERS} from './model-contract.mjs';

export const MODES = Object.freeze({
  all: Object.freeze([...LAYERS]),
  tooth: Object.freeze(['enamel', 'dentin', 'pulp']),
  ...Object.fromEntries(LAYERS.map(key => [key, Object.freeze([key])])),
});

// Every preset contains at least one layer; repeated selections cannot blank the
// specimen. Isolation changes visibility only, never position or camera scale.
export function selectMode(mode) {
  if (!Object.hasOwn(MODES, mode)) throw new Error('Unknown layer view');
  return Object.freeze({mode, visible: MODES[mode]});
}

export function applyVisibility(nodes, state) {
  for (const key of LAYERS) nodes[key].visible = state.visible.includes(key);
}

export function restoreContext(nodes, resetCamera) {
  const state = selectMode('all');
  applyVisibility(nodes, state);
  resetCamera();
  return state;
}
