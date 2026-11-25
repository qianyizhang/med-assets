// Exercise the same chamber lofts, valve surfaces and plane sampler used by the viewer.
import assert from 'node:assert/strict';
import {heartFrame, heartSection, probePlane} from './heart-geometry.js';

const area = rows => rows.slice(1).reduce((total, [y, l, r], i) => {
  const [y0, l0, r0] = rows[i];
  return total + (y - y0) * (r - l + r0 - l0) / 2;
}, 0);
function width(rows, y) {
  const upper = rows.findIndex(row => row[0] > y);
  const [y0, l0, r0] = rows[upper - 1], [y1, l1, r1] = rows[upper];
  const t = (y - y0) / (y1 - y0);
  return (r0 - l0) * (1 - t) + (r1 - l1) * t;
}
const section = (phase, angle = 0) => heartSection(heartFrame(phase), probePlane(angle));
const ed = section(0), es = section(.35), filling = section(.52);
assert.deepEqual(ed, section(1));
const results = {};
for (const name of ['LV', 'RV', 'LA', 'RA']) {
  const samples = [ed, es, filling].map(s => area(s.chambers[name].lumen));
  if (name.endsWith('V')) {
    assert.ok(samples[0] > samples[2] && samples[2] > samples[1]);
    assert.ok(es.chambers[name].lumen.at(-1)[0] < ed.chambers[name].lumen.at(-1)[0]);
  } else assert.ok(samples[1] > samples[2] && samples[2] > samples[0]);
  results[name] = samples.map(Math.round);
}
for (const state of [ed, es, filling]) {
  assert.ok(state.chambers.LV.lumen[0][0] < state.chambers.RV.lumen[0][0]);
  assert.ok(state.chambers.RV.lumen.at(-1)[0] < state.chambers.LV.lumen.at(-1)[0]);
}
const lvWallSpan = s => width(s.chambers.LV.wall, 70) - width(s.chambers.LV.lumen, 70);
assert.ok(lvWallSpan(es) > lvWallSpan(ed));
for (const valve of ['MV', 'TV']) {
  function tipGap(s) {
    const tips = s.valveCuts.filter(cut => cut.name === valve).map(cut => cut.points.at(-1));
    return Math.hypot(tips[1][0] - tips[0][0], tips[1][1] - tips[0][1]);
  }
  assert.ok(tipGap(ed) < .01 && tipGap(es) < .01 && tipGap(filling) > 5);
}
for (const angle of [-28, 0, 28]) {
  const plane = probePlane(angle);
  const point = plane.world(11, 80);
  assert.ok(Math.abs(plane.distance(point)) < 1e-9);
  assert.ok(Math.abs(plane.section(point)[0] - 11) < 1e-9);
  for (let i = 0; i < 100; i++) {
    const sample = section(i / 100, angle);
    for (const {lumen} of Object.values(sample.chambers)) assert.ok(area(lumen) > 0);
  }
}
assert.notDeepEqual(ed.chambers.RV.lumen, section(0, 28).chambers.RV.lumen);
console.log('ED, ES, early filling · modeled section areas in square model units', results);
