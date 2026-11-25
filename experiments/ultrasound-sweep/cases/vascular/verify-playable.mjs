import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

import {chapters, classifyTissue, pose, render} from './playable.js';
import {aorticCamera, aorticLength, aorticSurfaces} from './playable-aorta.js';
import {getAcquisition, getDopplerSample, measure, tubesAt} from './playable-model.js';

const cases = JSON.parse(readFileSync(new URL('cases.json', import.meta.url)));
const visit = id => cases.find(record => record.id === id);
const chapter = (record, id) => chapters(record).find(item => item.id === id);
const acquire = (record, item, delta = 0) => getAcquisition(record, item, item.evidenceFrame + delta);
const dimensions = (record, item, delta = 0) =>
  measure(record, item, item.evidenceFrame + delta).map(({hi, lo}) => hi - lo);
const sample = (record, item, delta = 0) => getDopplerSample(record, item, item.evidenceFrame + delta);

function near(expected, actual, epsilon = 1e-9) {
  assert.ok(Math.abs(expected - actual) < epsilon, `expected ${expected}, received ${actual}`);
}

const normal = visit('aaa-negative');
assert.equal(chapter(normal, 'proximal-aorta').measurement, '24 mm AP');
const split = chapter(normal, 'iliac-bifurcation');
const hasLumen = (z, x, y) => classifyTissue(x, y, tubesAt(normal, null, z)).region === 'lumen';
const aortaFirst = acquire(normal, split, -14);
assert.ok(hasLumen(aortaFirst.z, 0, 47));
const aortaLast = acquire(normal, split, 14);
const branches = tubesAt(normal, null, aortaLast.z).filter(v => v.name.includes('iliac'));
assert.equal(branches.length, 2);
for (const branch of branches) assert.ok(hasLumen(aortaLast.z, branch.x, branch.y));
assert.equal(hasLumen(aortaLast.z, 0, 47), false);
for (const side of ['right', 'left']) assert.match(chapter(normal, `${side}-iliac-short`).measurement, /^(11|10) mm AP$/);

const aneurysm = visit('aaa-positive');
const sac = chapter(aneurysm, 'sac-maximum');
assert.deepEqual(dimensions(aneurysm, sac), [43, 46]);
const long = chapter(aneurysm, 'sac-long-axis');
assert.deepEqual(dimensions(aneurysm, long), [43]);
for (const delta of [-1, 1]) {
  assert.ok(dimensions(aneurysm, sac, delta)[0] < 43 && dimensions(aneurysm, sac, delta)[1] < 46);
}
const {target, z} = acquire(aneurysm, sac);
const sacTubes = tubesAt(aneurysm, null, z);
assert.equal(classifyTissue(target.lx, target.ly, sacTubes).region, 'lumen');
assert.equal(classifyTissue(target.x, target.y + 16, sacTubes).region, 'mural');
assert.equal(classifyTissue(target.x, target.y + 21, sacTubes).region, 'wall');
assert.equal(classifyTissue(target.x, target.y + 22, sacTubes).region, 'tissue');
for (const side of ['right', 'left']) {
  assert.deepEqual(dimensions(aneurysm, chapter(aneurysm, `${side}-iliac-long`)),
    dimensions(aneurysm, chapter(aneurysm, `${side}-iliac-short`)));
}

for (const record of [normal, aneurysm]) {
  const openings = new Set();
  let previous = 1;
  for (let z = 155; z <= 190; z += .125) {
    const arteries = tubesAt(record, null, z).filter(v => v.color > 0);
    const y = arteries[0].ly;
    const intervals = arteries.map(v => [v.lx - v.lrx, v.lx + v.lrx]).sort(([a], [b]) => a - b);
    let count = 0;
    let end = -Infinity;
    for (const [lo, hi] of intervals) {
      if (lo > end) count++;
      end = Math.max(hi, end);
    }
    assert.ok(count >= previous, 'the common lumen opens into two branches only once');
    for (const artery of arteries) assert.equal(classifyTissue(artery.lx, y, arteries).region, 'lumen');
    openings.add(count);
    previous = count;
  }
  assert.deepEqual([...openings], [1, 2]);

  for (const {kind, vertices, faces} of aorticSurfaces(record).filter(mesh => mesh.kind !== 'vein')) {
    const adjacency = Array.from({length: vertices.length}, () => []);
    const edges = new Map();
    for (let triangle = 0; triangle < faces.length; triangle += 3) {
      for (let edge = 0; edge < 3; edge++) {
        const a = faces[triangle + edge];
        const b = faces[triangle + (edge + 1) % 3];
        adjacency[a].push(b);
        adjacency[b].push(a);
        const pair = Math.min(a, b) * vertices.length + Math.max(a, b);
        const [count, winding] = edges.get(pair) ?? [0, 0];
        edges.set(pair, [count + 1, winding + Math.sign(b - a)]);
      }
    }
    const component = new Set([0]);
    for (const index of component) for (const other of adjacency[index]) component.add(other);
    assert.equal(component.size, vertices.length, `${record.id} ${kind} is continuous into both iliacs`);
    const boundary = new Map();
    for (const [pair, [count, winding]] of edges) {
      assert.ok(count <= 2, `${record.id} ${kind} has a manifold surface`);
      if (count === 2) assert.equal(winding, 0, 'neighboring facets have consistent orientation');
      if (count !== 1) continue;
      const a = Math.floor(pair / vertices.length);
      const b = pair % vertices.length;
      assert.ok(Math.max(vertices[a].z, vertices[b].z) < 2 ||
        Math.min(vertices[a].z, vertices[b].z) > aorticLength - 2, 'open edges occur only at the volume limits');
      for (const [from, to] of [[a, b], [b, a]]) boundary.set(from, [...(boundary.get(from) ?? []), to]);
    }
    let openings = 0;
    for (const first of boundary.keys()) {
      openings++;
      const rim = new Set([first]);
      for (const vertex of rim) {
        assert.equal(boundary.get(vertex).length, 2);
        for (const neighbor of boundary.get(vertex)) rim.add(neighbor);
        boundary.delete(vertex);
      }
    }
    assert.equal(openings, 3, 'one proximal opening and two iliac openings');
  }
}

const limitedAorta = visit('aaa-indeterminate');
const firstAttempt = chapter(limitedAorta, 'anterior-distal-attempt');
const secondAttempt = chapter(limitedAorta, 'lateral-distal-repeat');
assert.notEqual(acquire(limitedAorta, firstAttempt).angle, acquire(limitedAorta, secondAttempt).angle);
for (const item of [firstAttempt, secondAttempt]) {
  assert.ok(acquire(limitedAorta, item).blind);
  assert.deepEqual(dimensions(limitedAorta, item), []);
}

const plaque = visit('carotid-plaque');
const transverse = chapter(plaque, 'right-transverse');
const distal = chapter(plaque, 'right-distal-lumen');
near(2.7, dimensions(plaque, transverse)[0]);
near(6.1, dimensions(plaque, distal)[0]);
assert.equal(Math.round(100 * (1 - dimensions(plaque, transverse)[0] / dimensions(plaque, distal)[0])), 56);
for (const offset of [-1, 1]) assert.ok(dimensions(plaque, transverse, offset)[0] > 2.7);
const plaquePlane = acquire(plaque, transverse);
const plaqueTubes = tubesAt(plaque, 'Right', plaquePlane.z);
assert.equal(classifyTissue(plaquePlane.target.x, plaquePlane.target.y + 2.7, plaqueTubes).region, 'mural');

const jet = chapter(plaque, 'right-jet');
assert.deepEqual(sample(plaque, jet), {psv: 207, edv: 67, angle: 58, disturbed: true});
for (const delta of [-1, 1]) assert.ok(sample(plaque, jet, delta).psv < 207);
assert.equal(sample(plaque, jet, -14), null);
assert.equal(sample(plaque, chapter(plaque, 'right-before')).psv, 94);
assert.equal(sample(plaque, chapter(plaque, 'right-beyond')).psv, 122);
assert.equal((207 / sample(plaque, chapter(plaque, 'right-distal-cca')).psv).toFixed(2), '2.88');

const limitedCarotid = visit('carotid-limited');
const initial = chapter(limitedCarotid, 'left-distal-ica');
const retry = chapter(limitedCarotid, 'left-distal-ica-retry');
assert.notEqual(acquire(limitedCarotid, retry).angle, acquire(limitedCarotid, initial).angle);
assert.equal(sample(limitedCarotid, initial), null);
assert.equal(sample(limitedCarotid, retry), null);
assert.equal(sample(limitedCarotid, chapter(limitedCarotid, 'left-proximal-ica')).psv, 92);

function sampleCanvas() {
  const calls = [];
  const rasters = [];
  const locators = [];
  const lines = [];
  const labels = [];
  let path;
  const ctx = new Proxy({
    createImageData: (width, height) => ({width, height, data: new Uint8ClampedArray(width * height * 4)}),
    putImageData(image, x, y) {
      assert.equal(image.data[3], 255);
      assert.equal(image.data.at(-1), 255);
      if (image.width === 366 && image.height === 183) {
        locators.push({x, y, width: image.width, height: image.height, data: image.data.slice()});
        return;
      }
      calls.push(image.data);
      rasters.push({width: image.width, height: image.height, x, y});
    },
    beginPath() { path = []; },
    moveTo(x, y) { path.push([x, y]); },
    lineTo(x, y) { path.push([x, y]); },
    stroke() {
      if (this.lineWidth === 1.4) lines.push(path);
    },
    fillText(value) { labels.push(value); },
  }, {
    get(object, key) {
      return key in object ? object[key] : () => {};
    },
  });
  return {calls, rasters, locators, lines, labels, ctx};
}

let count = 0;
for (const record of cases) {
  const selected = chapters(record);
  assert.equal(new Set(selected.map(item => item.id)).size, selected.length);
  assert.equal(new Set(selected.map(item => item.viewImage)).size, record.views.length);
  for (const item of selected) {
    assert.ok(record.views.some(view => view.image === item.viewImage));
    assert.ok(item.evidenceFrame > 0 && item.evidenceFrame < item.frames - 1);
    const {calls, rasters, ctx} = sampleCanvas();
    for (const frame of [item.frames - 1, item.evidenceFrame, 0, item.evidenceFrame]) {
      render(ctx, item, frame, record);
      pose(ctx, item, frame, record);
    }
    const acq = getAcquisition(record, item, item.evidenceFrame);
    const screen = rasters[1];
    // A raster is serialized in 2 × 2 cells, so each extent may have less than two padding pixels.
    assert.ok(Math.abs(screen.width - screen.height / acq.depth * acq.width) < 2 + 2 * acq.width / acq.depth);
    assert.deepEqual(calls[1], calls[3], `seeking must reproduce ${record.id}/${item.id}`);
    assert.notDeepEqual(calls[0], calls[2], `sweep must change ${record.id}/${item.id}`);
    count++;
  }
}
console.log(`Verified ${cases.length} vascular visits and ${count} independently seekable chapters.`);

function sampledFrame(record, item, frame, overlay) {
  const {ctx, calls, rasters, lines, labels} = sampleCanvas();
  const legend = render(ctx, item, frame, record, {overlay});
  return {legend: legend.map(entry => entry.label), pixels: calls[0], raster: rasters[0], lines, labels};
}

function atTransverse(record, item, frame, x, y, overlay) {
  const acq = getAcquisition(record, item, frame);
  const {pixels, raster: {width, height}} = sampledFrame(record, item, frame, overlay);
  const scale = Math.min(width / acq.width, height / acq.depth);
  const column = Math.floor(width / 2 + (x - acq.anchorX) * scale);
  const row = Math.floor(y * scale);
  return [...pixels.slice((row * width + column) * 4, (row * width + column) * 4 + 3)];
}

const maximumFrame = sac.evidenceFrame;
const max = sampledFrame(aneurysm, sac, maximumFrame, true);
assert.ok(max.labels.some(label => label.includes('TISSUE OVERLAY')));
assert.equal(max.lines.length, 2);
const screenLengths = max.lines.map(([[x1, y1], [x2, y2]]) => Math.hypot(x2 - x1, y2 - y1));
near(46 / 43, screenLengths[1] / screenLengths[0]);
const {width: rasterWidth, height: rasterHeight, x: rasterX, y: rasterY} = max.raster;
const atWall = (column, row) => {
  const i = (row * rasterWidth + column) * 4;
  const [r, g, b] = max.pixels.slice(i, i + 3);
  return r > g && g - b > 15 && r - b > 50;
};
const [[apX, apY], [, apEndY]] = max.lines[0];
const [[trX, trY], [trEndX]] = max.lines[1];
const testRasterChord = (horizontal) => {
  const fixed = horizontal ? Math.floor(trY - rasterY) : Math.floor(apX - rasterX);
  const start = horizontal ? trX - rasterX : apY - rasterY;
  const end = horizontal ? trEndX - rasterX : apEndY - rasterY;
  const limit = horizontal ? rasterWidth : rasterHeight;
  const found = [];
  for (let varying = Math.max(0, Math.floor(start) - 2); varying < Math.min(limit, Math.ceil(end) + 2); varying++) {
    if (horizontal ? atWall(varying, fixed) : atWall(fixed, varying)) found.push(varying);
  }
  return found.at(-1) - found[0] + 1;
};
near(46 / 43, testRasterChord(true) / testRasterChord(false), .025);
for (const label of ['Aortic wall', 'Mural thrombus', 'Residual lumen']) assert.ok(max.legend.includes(label));
assert.deepEqual(sampledFrame(aneurysm, sac, maximumFrame, false).legend, []);
const sampleWall = atTransverse(aneurysm, sac, maximumFrame, 0, 47 - 21, true);
const sampleThrombus = atTransverse(aneurysm, sac, maximumFrame, 0, 47 + 16, true);
const sampleLumen = atTransverse(aneurysm, sac, maximumFrame, target.lx, target.ly, true);
assert.ok(sampleWall[0] > sampleWall[1] && sampleWall[1] > sampleWall[2]);
assert.ok(sampleThrombus[2] > sampleThrombus[0] && sampleThrombus[0] > sampleThrombus[1]);
assert.ok(sampleLumen[1] > sampleLumen[2] && sampleLumen[2] > sampleLumen[0]);
for (const offset of [-1, 0, 1]) {
  const frame = maximumFrame + offset;
  const acq = getAcquisition(aneurysm, sac, frame);
  const [ap, width] = measure(aneurysm, sac, frame);
  for (const [x, y] of [[ap.x, ap.lo], [ap.x, ap.hi], [width.lo, width.y], [width.hi, width.y]]) {
    const wallFactor = ((x - acq.target.x) / acq.target.rx) ** 2 + ((y - acq.target.y) / acq.target.ry) ** 2;
    near(1, wallFactor);
  }
  const [grayA, grayB] = [atTransverse(aneurysm, sac, frame, 0, 47 + 16, false),
    atTransverse(aneurysm, sac, frame, 35, 45, false)];
  const grayLumen = atTransverse(aneurysm, sac, frame, acq.target.lx, acq.target.ly, false);
  assert.ok(grayA[0] > grayLumen[0], 'grayscale separates thrombus from lumen independently of the overlay');
  assert.deepEqual(atTransverse(aneurysm, sac, frame, 35, 45, true), grayB, 'unlabeled tissue is unchanged');
}

const bifLegend = sampledFrame(normal, split, split.frames - 1, true).legend;
assert.ok(bifLegend.includes('Right common iliac') && bifLegend.includes('Left common iliac'));
assert.ok(!sampledFrame(normal, split, 0, true).legend.includes('Right common iliac'));
assert.equal(sampledFrame(normal, split, 4, false).labels.filter(label => label === 'Aorta').length, 1);
const plaqueView = sampledFrame(plaque, transverse, transverse.evidenceFrame, true);
assert.ok(plaqueView.legend.includes('Carotid plaque'));
assert.ok(!sampledFrame(plaque, distal, distal.evidenceFrame, true).legend.includes('Carotid plaque'));

for (const limitedChapter of [firstAttempt, secondAttempt]) {
  const frame = limitedChapter.evidenceFrame;
  const labels = sampledFrame(limitedAorta, limitedChapter, frame, true).legend;
  assert.ok(!labels.includes('Aortic wall') && !labels.includes('Aortic lumen'));
}
const locator = sampleCanvas();
for (const yaw of [0, -Math.PI / 2, Math.PI / 2, 0]) pose(locator.ctx, sac, maximumFrame, aneurysm, {yaw});
const [front, right, left, restored] = locator.locators;
assert.deepEqual(front.data, restored.data);
assert.notDeepEqual(front.data, right.data);
assert.notDeepEqual(left.data, right.data);
assert.deepEqual(sampledFrame(aneurysm, sac, maximumFrame, true), max);

function locatorPixel(raster, camera, x, y, z) {
  const [col, row] = camera.project(x, y, z).map(Math.floor);
  const index = ((row - raster.y) * raster.width + col - raster.x) * 4;
  return [...raster.data.slice(index, index + 3)];
}

const isTurquoise = ([red, green, blue]) => green > red + 30 && blue > red + 30;
const isMagenta = ([red, green, blue]) => red > green + 45 && blue > green + 45;
for (const [raster, yaw] of [[front, 0], [right, -Math.PI / 2], [left, Math.PI / 2]]) {
  const camera = aorticCamera(yaw);
  assert.ok(isTurquoise(locatorPixel(raster, camera, target.lx, target.ly, z)), 'cap lumen reads as a distinct recess');
  assert.ok(isMagenta(locatorPixel(raster, camera, target.x, target.y + 16, z)), 'cap registers posterior thrombus');
}
for (const yaw of [0, Math.PI / 4]) {
  pose(locator.ctx, long, long.evidenceFrame, aneurysm, {yaw});
  const raster = locator.locators.at(-1);
  const camera = aorticCamera(yaw);
  for (let z = 33; z < 153; z++) {
    const vessel = tubesAt(aneurysm, null, z)[0];
    assert.ok(isTurquoise(locatorPixel(raster, camera, 0, vessel.ly, z)), `long-axis lumen open at z=${z} and yaw=${yaw}`);
  }
  assert.ok(isMagenta(locatorPixel(raster, camera, 0, target.y + 16, z)), 'long-axis cut separates posterior thrombus');
}
for (const item of [firstAttempt, secondAttempt]) {
  pose(locator.ctx, item, item.evidenceFrame, limitedAorta);
  const {data} = locator.locators.at(-1);
  let cutWallPixels = 0;
  for (let i = 0; i < data.length; i += 4) {
    if (data[i] === 249 && data[i + 1] === 176 && data[i + 2] === 119) cutWallPixels++;
  }
  assert.equal(cutWallPixels, 0, 'an obscured acquisition does not display a cut cross-section');
}
console.log('Verified registered overlays, isotropic calipers, shadow masks, connected AAA surfaces and independently orbitable sections.');
