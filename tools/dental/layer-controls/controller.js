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
  function createController(parts, contract = {labels:LABELS, offsets:OFFSETS}, clock = () => performance.now()) {
    if (typeof clock !== 'function') throw new Error('Invalid clock.');
    if (!contract || !Array.isArray(contract.labels) || contract.labels.length === 0 ||
        Array.from(contract.labels).some(label => typeof label !== 'string' || !label.trim()) ||
        new Set(contract.labels).size !== contract.labels.length) throw new Error('Invalid source label contract.');
    const labels = [...contract.labels];
    if (!contract.offsets || Object.keys(contract.offsets).length !== labels.length) throw new Error('Missing or extra editorial offsets.');
    const offsets = new Map(labels.map(label => {
      const offset = Object.hasOwn(contract.offsets, label) && contract.offsets[label];
      if (!Array.isArray(offset) || offset.length !== 3 || !Array.from(offset).every(Number.isFinite)) throw new Error('Invalid editorial offset.');
      return [label, [...offset]];
    }));
    if (!Array.isArray(parts) || parts.length !== labels.length) throw new Error('Exactly the contracted source-labelled parts are required.');
    const baseline = new Map();
    for (const part of parts) {
      if (!part || !labels.includes(part.label) || baseline.has(part.label)) throw new Error('Missing, duplicate or unsupported source label.');
      const matrix = part.matrix === undefined ? IDENTITY : part.matrix;
      if (!Array.isArray(matrix) || matrix.length !== 16 || !Array.from(matrix).every(Number.isFinite)) throw new Error('Invalid source transform.');
      baseline.set(part.label, Object.freeze([...matrix]));
    }
    let current = Object.freeze({reveal:0, isolate:null});
    let frames = null, position = 0, playing = false, anchor = null;
    function playback() { return {position, playing, duration:frames ? frames[frames.length-1].time : 0}; }
    function time() {
      const value = clock();
      if (!Number.isFinite(value) || (anchor !== null && value < anchor)) throw new Error('Clock must be finite and monotonic.');
      return value;
    }
    function sample(value) {
      let index = 0;
      while (index + 1 < frames.length && frames[index+1].time <= value) index++;
      const left = frames[index], right = frames[index+1];
      const fraction = right ? (value-left.time)/(right.time-left.time) : 0;
      current = Object.freeze({reveal:right ? left.reveal+(right.reveal-left.reveal)*fraction : left.reveal, isolate:left.isolate});
      position = value;
    }
    function setTimeline(input) {
      if (!Array.isArray(input) || input.length < 2) throw new Error('At least two keyframes required.');
      const copy = Array.from(input, (frame, index) => {
        if (!frame || !Number.isFinite(frame.time) || frame.time < 0 ||
            (index === 0 ? frame.time !== 0 : frame.time <= input[index-1].time) ||
            !Number.isFinite(frame.reveal) || frame.reveal < 0 || frame.reveal > 1 ||
            (frame.isolate !== null && !labels.includes(frame.isolate))) throw new Error('Invalid timeline keyframe.');
        return {time:frame.time,reveal:frame.reveal,isolate:frame.isolate};
      });
      frames = copy; playing = false; anchor = null; sample(0);
      return playback();
    }
    function requireTimeline() { if (!frames) throw new Error('No timeline configured.'); }
    function tick() {
      if (!playing) return playback();
      const next = time(), end = frames[frames.length-1].time;
      sample(Math.min(end, position + (next-anchor)));
      anchor = next;
      if (position === end) { playing = false; anchor = null; }
      return playback();
    }
    function play() {
      requireTimeline();
      if (playing) return playback();
      const next = time();
      if (position === frames[frames.length-1].time) position = 0;
      sample(position); anchor = next; playing = true;
      return playback();
    }
    function pause() {
      tick(); playing = false; anchor = null;
      return playback();
    }
    function scrub(value) {
      requireTimeline();
      if (!Number.isFinite(value) || value < 0 || value > frames[frames.length-1].time) throw new Error('Scrub outside timeline.');
      playing = false; anchor = null; sample(value);
      return playback();
    }
    function snapshot() { return {...current}; }
    function dispatch(action) {
      if (!action || typeof action.type !== 'string') throw new Error('Invalid control action.');
      let next = {...current};
      if (action.type === 'reveal') {
        if (!Number.isFinite(action.value) || action.value < 0 || action.value > 1) throw new Error('Reveal must be finite and between 0 and 1.');
        next.reveal = action.value;
      } else if (action.type === 'isolate') {
        if (!labels.includes(action.label)) throw new Error('Unknown source label.');
        next.isolate = action.label;
      } else if (action.type === 'all') next.isolate = null;
      else if (action.type === 'reset') next = {reveal:0,isolate:null};
      else throw new Error('Unknown control action.');
      playing = false; anchor = null;
      if (action.type === 'reset') position = 0;
      current = Object.freeze(next);
      return snapshot();
    }
    function resolve() {
      return labels.map(label => {
        const matrix = [...baseline.get(label)];
        if (current.reveal !== 0) for (let k=0;k<3;k++) matrix[12+k] += offsets.get(label)[k] * current.reveal;
        return {label, visible:current.isolate === null || current.isolate === label, matrix};
      });
    }
    function timeline() { return frames ? frames.map(frame => ({...frame})) : null; }
    return Object.freeze({snapshot,dispatch,resolve,setTimeline,timeline,playback,play,pause,scrub,tick});
  }
  return Object.freeze({LABELS, OFFSETS, IDENTITY, createController});
});
