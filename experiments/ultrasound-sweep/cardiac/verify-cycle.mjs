// Exercise the exact chamber and vessel lofts, leaflets, and plane sampler used by the viewer.
import assert from 'node:assert/strict';
import {CARDIAC_VIEWS, heartFrame, heartSection, probePlane, measurementContour} from './heart-geometry.js';
import {bmodeCalibration} from './heart-poses.js';
import {polygonArea} from './heart-slice.js';

const area = contours => contours.reduce((total, contour) => total + polygonArea(contour), 0);
const dot = (a, b) => a.reduce((total, value, axis) => total + value * b[axis], 0);
const distance = (a, b) => Math.hypot(...a.map((value, axis) => value - b[axis]));
const isInSector = (plane, [x, y]) => y > 5 && Math.hypot(x, y) < plane.depth
  && Math.abs(x) < Math.tan(plane.halfAngle) * y;

function horizontalSpan(contours, y) {
  const hits = [];
  for (const path of contours) {
    for (let i = 1; i < path.length; i += 1) {
      const [x0, y0] = path[i - 1], [x1, y1] = path[i];
      if ((y0 < y) !== (y1 < y)) hits.push(x0 + (x1 - x0) * (y - y0) / (y1 - y0));
    }
  }
  return Math.max(...hits) - Math.min(...hits);
}

const a4c = phase => heartSection(heartFrame(phase), probePlane(0));
const frames = [0, 0.35, 0.52].map(heartFrame);
const [ed, es, filling] = [0, 0.35, 0.52].map(a4c);
assert.deepEqual(ed, a4c(1));
const results = {};
for (const name of ['LV', 'RV', 'LA', 'RA']) {
  const samples = [ed, es, filling].map(s => area(s.chambers[name].lumen));
  if (name.endsWith('V')) {
    assert.ok(samples[0] > samples[2] && samples[2] > samples[1], name);
    assert.ok(frames[1].chambers[name].lumen.at(-1)[0][1] < frames[0].chambers[name].lumen.at(-1)[0][1]);
  } else assert.ok(samples[1] > samples[2] && samples[2] > samples[0], name);
  results[name] = samples.map(Math.round);
}
for (const frame of frames) {
  const {LV, RV, LA, RA} = frame.chambers;
  assert.ok(LV.lumen[0][0][1] < RV.lumen[0][0][1]);
  assert.ok(RV.lumen.at(-1)[0][1] < LV.lumen.at(-1)[0][1]);
  for (const [v, a] of [[LV, LA], [RV, RA]]) {
    assert.ok(v.lumen.at(-1).every((point, index) => distance(point, a.lumen[0][index]) < 1e-6));
  }
}
const rvAnnuli = frames.map(({chambers: {RV}}) => RV.lumen.at(-1));
const lateral = rvAnnuli[0].length / 2;
const lateralExcursion = rvAnnuli[0][lateral][1] - rvAnnuli[1][lateral][1];
const septalExcursion = rvAnnuli[0][0][1] - rvAnnuli[1][0][1];
assert.ok(lateralExcursion >= 18 && lateralExcursion <= 21);
assert.ok(septalExcursion < lateralExcursion);
const lvWallSpan = ({chambers: {LV}}) => horizontalSpan(LV.wall, 70) - horizontalSpan(LV.lumen, 70);
assert.ok(lvWallSpan(es) > lvWallSpan(ed));
for (const valve of ['MV', 'TV', 'AV', 'PV']) {
  function gap(frame) {
    const tips = frame.details.filter(({name}) => name === valve).map(({rings}) => {
      const freeEdge = rings.at(-1);
      return freeEdge[Math.floor(freeEdge.length / 2)];
    });
    return distance(tips[0], tips[1]);
  }
  const inlet = ['MV', 'TV'].includes(valve);
  assert.ok(gap(frames[0]) < 0.01 && gap(frames[1]) < 0.01, valve);
  assert.ok(gap(inlet ? frames[2] : heartFrame(0.18)) > 5, valve);
}

const landmarks = {
  plax: ['LV', 'LA', 'Ao', 'MV', 'AV'], 'psax-av': ['Ao', 'RVOT', 'AV'],
  'psax-mv': ['LV', 'RV', 'MV'], 'psax-papillary': ['LV', 'papillary'], 'psax-apical': ['LV'],
  a4c: ['LV', 'LA', 'RV', 'RA', 'MV', 'TV'], a5c: ['LV', 'LA', 'RV', 'RA', 'LVOT', 'AV', 'MV', 'TV'],
  a2c: ['LV', 'LA', 'MV'], a3c: ['LV', 'LA', 'Ao', 'LVOT', 'MV', 'AV'],
  'rv-focused': ['LV', 'LA', 'RV', 'RA', 'TV'], 'rv-inflow': ['RV', 'RA', 'TV'], 'rv-outflow': ['RVOT', 'PA', 'PV'],
  'subcostal-4c': ['LV', 'LA', 'RV', 'RA', 'TV'], 'subcostal-ivc': ['RA', 'IVC'],
  'subcostal-sax': ['RVOT', 'PA', 'PV'], 'subcostal-aorta': ['DescAo'], 'suprasternal-arch': ['Arch'],
};
const angles = [-28, 0, 28];
const phases = Array.from({length: 21}, (_, index) => index / 20);
for (const id of Object.keys(CARDIAC_VIEWS)) {
  const hits = new Set();
  for (const angle of angles) {
    const plane = probePlane(angle, id);
    const {origin, right, down, normal} = plane;
    assert.ok([right, down, normal].every(axis => Math.abs(dot(axis, axis) - 1) < 1e-9));
    assert.ok(Math.abs(dot(right, down)) < 1e-9);
    assert.ok(Math.abs(dot(normal, right)) < 1e-9);
    assert.ok(Math.abs(dot(normal, down)) < 1e-9);
    assert.deepEqual(plane.world(0, 0), origin);
    const point = plane.world(11, 80);
    assert.ok(Math.abs(plane.distance(point)) < 1e-9);
    assert.ok(distance(plane.section(point), [11, 80]) < 1e-9);
    for (const phase of phases) {
      const sample = heartSection(heartFrame(phase), plane);
      for (const [name, {wall, lumen}] of Object.entries(sample.chambers)) {
        for (const path of wall.concat(lumen)) {
          assert.ok(path.every(point => point.every(Number.isFinite)), `${id} ${name}`);
          assert.ok(distance(path[0], path.at(-1)) < 1e-4, `${id} ${name} has an open tissue contour`);
        }
        if (angle === 0 && lumen.some(outline => polygonArea(outline) > 30
          && outline.filter(p => isInSector(plane, p)).length >= 5)) hits.add(name);
      }
      if (angle !== 0) continue;
      for (const {name, points} of sample.valveCuts) if (points.some(p => isInSector(plane, p))) hits.add(name);
      if (sample.muscleCuts.filter(outline => outline.some(p => isInSector(plane, p))).length >= 2) hits.add('papillary');
    }
  }
  for (const landmark of landmarks[id]) assert.ok(hits.has(landmark), `${id} does not intersect ${landmark} in its sector`);
}
for (const [id, chamber] of [['a4c', 'LV'], ['a2c', 'LA'], ['rv-focused', 'RV']]) {
  assert.ok(measurementContour(0, id, chamber).length > 12, `${id} ${chamber}`);
}
for (const id of ['a4c', 'a2c']) {
  const plane = probePlane(0, id);
  const {width, height, scale, tip, center} = bmodeCalibration(plane);
  assert.ok(center + scale * plane.depth * Math.sin(plane.halfAngle) < width);
  assert.ok(tip + scale * plane.depth < height);
  for (const name of ['LV', 'LA']) {
    for (const phase of phases) {
      const contour = measurementContour(phase, id, name);
      assert.ok(contour.length > 12 && contour.every(point => isInSector(plane, point)), `${id} clips the ${name} measurement contour`);
    }
  }
}
assert.notDeepEqual(ed.chambers.RV.lumen, heartSection(frames[0], probePlane(28)).chambers.RV.lumen);
console.log('ED, ES, early filling · modeled section areas in square model units', results);
console.log(`${Object.keys(CARDIAC_VIEWS).length} modeled windows and phases intersect expected valve and vessel landmarks.`);
