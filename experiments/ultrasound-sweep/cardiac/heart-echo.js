// B-mode styling is illustrative. The tissue/blood interfaces come from heartSection.
import {largestContour, polygonArea} from './heart-slice.js';
import {BMODE_RASTER, bmodeCalibration} from './heart-poses.js';

const {width: RASTER_WIDTH, height: RASTER_HEIGHT} = BMODE_RASTER;
const CM = 10;
const RIGHT_HEART = {fill: 'rgba(45,196,207,0.18)', edge: '#81e1eb'};
const LEFT_HEART = {fill: 'rgba(242,117,107,0.19)', edge: '#ffb1a2'};
const STRUCTURES = {
  'right-parasternal': ['Ao', 'LVOT', 'RVOT', 'LA'],
  plax: ['LV', 'RVOT', 'LA', 'Ao'], 'psax-av': ['Ao', 'RA', 'RVOT', 'PA'],
  'psax-mv': ['LV', 'RV'], 'psax-papillary': ['LV', 'RV'], 'psax-apical': ['LV', 'RV'],
  a4c: ['LV', 'RV', 'LA', 'RA'], a5c: ['LV', 'RV', 'LA', 'RA', 'LVOT'],
  a2c: ['LV', 'LA'], a3c: ['LV', 'LA', 'LVOT', 'Ao'],
  'rv-focused': ['LV', 'RV', 'LA', 'RA'], 'rv-inflow': ['RV', 'RA'],
  'rv-outflow': ['RVOT', 'PA'], 'subcostal-4c': ['LV', 'RV', 'LA', 'RA'],
  'subcostal-ivc': ['IVC', 'RA'], 'subcostal-aorta': ['DescAo'], 'subcostal-sax': ['RVOT', 'PA', 'LV'],
  'suprasternal-arch': ['Arch'],
};

export function chamberColor(name) {
  return name.startsWith('R') || ['PA', 'IVC', 'SVC'].includes(name) ? RIGHT_HEART : LEFT_HEART;
}

export function sectorPath({halfAngle, depth}, near = 0) {
  const path = new Path2D();
  path.moveTo(-Math.sin(halfAngle) * near, Math.cos(halfAngle) * near);
  path.lineTo(-Math.sin(halfAngle) * depth, Math.cos(halfAngle) * depth);
  path.arc(0, 0, depth, Math.PI / 2 + halfAngle, Math.PI / 2 - halfAngle, true);
  path.lineTo(Math.sin(halfAngle) * near, Math.cos(halfAngle) * near);
  if (near > 0) path.arc(0, 0, near, Math.PI / 2 - halfAngle, Math.PI / 2 + halfAngle);
  path.closePath();
  return path;
}

export function contourPath(points) {
  const path = linePath(points);
  if (points.length) path.closePath();
  return path;
}

export function linePath(points) {
  const path = new Path2D();
  if (points.length) path.moveTo(...points[0]);
  for (let index = 1; index < points.length; index += 1) path.lineTo(...points[index]);
  return path;
}

function makeSurface(width, height, options) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  return {canvas, ink: canvas.getContext('2d', options)};
}

function randomField(width, height, seed) {
  const values = new Float32Array(width * height);
  let value = seed;
  for (let index = 0; index < values.length; index += 1) {
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    values[index] = (value >>> 0) / 4294967296;
  }
  return (x, y) => {
    const col = Math.floor(x);
    const row = Math.floor(y);
    const c = ((col % (width - 1)) + width - 1) % (width - 1);
    const r = ((row % (height - 1)) + height - 1) % (height - 1);
    const f = x - col;
    const g = y - row;
    const start = r * width + c;
    const low = values[start] * (1 - f) + values[start + 1] * f;
    const high = values[start + width] * (1 - f) + values[start + width + 1] * f;
    return low * (1 - g) + high * g;
  };
}

function buildSpeckle(plane, {scale, tip, center}) {
  const seed = 182467;
  const fine = randomField(153, 143, seed);
  const middle = randomField(178, 194, seed + 451);
  const broad = randomField(51, 74, seed + 997);
  const gain = new Float32Array(RASTER_WIDTH * RASTER_HEIGHT);
  const interfaceGain = new Float32Array(gain.length);
  const tissue = new Uint8Array(gain.length);
  const pattern = new Float32Array(gain.length);
  for (let viewY = 0; viewY < RASTER_HEIGHT; viewY += 1) {
    for (let viewX = 0; viewX < RASTER_WIDTH; viewX += 1) {
      const index = viewY * RASTER_WIDTH + viewX;
      const x = (viewX - center) / scale;
      const y = (viewY - tip) / scale;
      const radius = Math.hypot(x, y);
      const angle = Math.atan2(x, y);
      if (y < 0 || radius < 5 || radius > plane.depth || Math.abs(angle) > plane.halfAngle) continue;
      const ray = angle * 77;
      const fineSample = fine(ray * 3.1 + x * 0.60, radius * 2.6);
      const midSample = middle(ray * 1.25 + x * 0.23, radius * 1.06 + x * 0.09);
      const broadSample = broad(x * 0.19 + y * 0.08, y * 0.24);
      const edgeLoss = 1 - 0.27 * (Math.abs(angle) / plane.halfAngle) ** 4;
      const depthLoss = 0.95 - 0.26 * (radius / plane.depth) ** 2;
      const lateralGain = 1 - 0.30 * Math.exp(-((angle - 0.43) ** 2) / 0.055);
      const dropout = 1 - 0.31 * Math.exp(-((angle + 0.43) ** 2) / 0.009 - ((radius - 71) ** 2) / 680);
      const fascia = 17 * Math.exp(-((y - 10 - x * 0.07 - x * x * 0.005) ** 2) / 4.6)
        + 18 * Math.exp(-((y - 20 - Math.cos(x * 0.16) * 0.9) ** 2) / 28.5);
      const field = 22 * Math.exp(-((radius - 149 - x * 0.09) ** 2) / 100 - ((x + 21) ** 2) / 3500);
      tissue[index] = Math.round(11 * broadSample + 6 * midSample + fascia + field);
      gain[index] = edgeLoss * depthLoss * lateralGain * dropout;
      const lateralLoss = (plane.id.startsWith('a') || plane.id === 'rv-focused' ? 0.65 : 0.29) * Math.exp(-((x - 39) ** 2) / 770 - ((y - 74) ** 2) / 1600);
      const nearLoss = 0.44 * Math.exp(-((y - 24) ** 2) / 395);
      interfaceGain[index] = (1 - lateralLoss) * (1 - nearLoss) * (0.71 + 0.52 * broadSample);
      pattern[index] = 0.23 + fineSample * 0.38 + midSample ** 2 * 0.96 + broadSample ** 2 * 1.20;
    }
  }
  return {pattern, tissue, gain, interfaceGain};
}

function boundsOf(points) {
  return points.reduce(([left, top, right, bottom], [x, y]) => [
    Math.min(left, x), Math.min(top, y), Math.max(right, x), Math.max(bottom, y),
  ], [Infinity, Infinity, -Infinity, -Infinity]);
}

function inside(points, x, y) {
  let inPath = false;
  for (let i = 0, j = points.length - 1; i < points.length; j = i, i += 1) {
    const a = points[i], b = points[j];
    if ((a[1] > y) !== (b[1] > y) && x < a[0] + (b[0] - a[0]) * ((y - a[1]) / (b[1] - a[1]))) inPath = !inPath;
  }
  return inPath;
}

function paintLoops(ink, contours, width, brightness) {
  const display = contours.map(points => ({points, bounds: boundsOf(points)}));
  const paths = Array.from({length: 5}, () => new Path2D());
  for (const contour of display) {
    const {points} = contour;
    const neighbors = display.filter(other => {
      const a = contour.bounds, b = other.bounds;
      return other !== contour && a[0] <= b[2] + 0.3 && a[2] + 0.3 >= b[0]
        && a[1] <= b[3] + 0.3 && a[3] + 0.3 >= b[1];
    });
    for (let index = 1; index < points.length; index += 1) {
      const [x, y] = points[index];
      const [priorX, priorY] = points[index - 1];
      const mx = (x + priorX) * 0.5;
      const my = (y + priorY) * 0.5;
      const dx = x - priorX;
      const dy = y - priorY;
      const length = Math.hypot(dx, dy);
      if (length < 0.0001 || my < 0) continue;
      const nx = dy * 0.24 / length;
      const ny = -dx * 0.24 / length;
      const adjoining = neighbors.some(({points: other, bounds: [left, top, right, bottom]}) =>
        mx >= left - 0.3 && mx <= right + 0.3 && my >= top - 0.3 && my <= bottom + 0.3
        && (inside(other, mx + nx, my + ny) || inside(other, mx - nx, my - ny)));
      if (adjoining) continue;
      const shiver = Math.sin(mx * 0.54 + my * 0.32) * Math.cos(my * 0.32) * 0.40;
      const incidence = Math.abs(dx * my - dy * mx) / (length * Math.max(1, Math.hypot(mx, my)));
      const bin = Math.min(paths.length - 1, Math.max(0, Math.round((incidence * 0.74 + shiver) * 4)));
      paths[bin].moveTo(priorX, priorY);
      paths[bin].lineTo(x, y);
    }
  }
  for (let index = 0; index < paths.length; index += 1) {
    ink.lineWidth = width * (1 + index * 0.20);
    ink.strokeStyle = `rgb(${brightness + index * 23},${brightness + index * 23},${brightness + index * 23})`;
    ink.stroke(paths[index]);
  }
}

function paintReflectors(ink, plane, slice, {scale, tip, center}) {
  ink.setTransform(1, 0, 0, 1, 0, 0);
  ink.fillStyle = '#111';
  ink.fillRect(0, 0, RASTER_WIDTH, RASTER_HEIGHT);
  ink.save();
  ink.setTransform(scale, 0, 0, scale, center, tip);
  ink.clip(sectorPath(plane, 5));
  const {chambers, valveCuts, muscleCuts} = slice;
  const walls = Object.values(chambers).flatMap(region => region.wall);
  const lumens = Object.values(chambers).flatMap(region => region.lumen);
  ink.lineCap = 'round';
  ink.lineJoin = 'round';
  ink.fillStyle = '#414141';
  for (const wall of walls) ink.fill(contourPath(wall));
  paintLoops(ink, walls, 1.35, 65);
  ink.fillStyle = '#0a0a0a';
  for (const lumen of lumens) ink.fill(contourPath(lumen));
  paintLoops(ink, lumens, 0.93, 58);
  for (const outline of muscleCuts) {
    const path = contourPath(outline);
    ink.fillStyle = '#434343';
    ink.fill(path);
    ink.strokeStyle = '#696969';
    ink.lineWidth = 0.85;
    ink.stroke(path);
  }
  for (const {name, points} of valveCuts) {
    const path = linePath(points);
    ink.strokeStyle = ['MV', 'AV'].includes(name) ? '#7a7a7a' : '#585858';
    ink.lineWidth = 2.5;
    ink.stroke(path);
    ink.strokeStyle = ['MV', 'AV'].includes(name) ? '#c4c4c4' : '#9c9c9c';
    ink.lineWidth = 1.10;
    ink.stroke(path);
  }
  ink.restore();
}

function poolCenter(points, plane) {
  // Segment midpoints crossing sampled image rows give a stable in-sector label anchor.
  let best = null;
  let visibleArea = 0;
  const [, low, , high] = boundsOf(points);
  const widthScale = Math.tan(plane.halfAngle);
  for (let y = Math.max(5, low + 3); y < Math.min(plane.depth, high - 3); y += 2) {
    const hits = [];
    for (let index = 1; index < points.length; index += 1) {
      const [x0, y0] = points[index - 1], [x1, y1] = points[index];
      if ((y0 < y) === (y1 < y)) continue;
      hits.push(x0 + (x1 - x0) * (y - y0) / (y1 - y0));
    }
    if (hits.length < 2) continue;
    hits.sort((a, b) => a - b);
    const edge = Math.min(y * widthScale, Math.sqrt(plane.depth ** 2 - y ** 2)) - 3;
    for (let index = 0; index + 1 < hits.length; index += 2) {
      const left = Math.max(hits[index], -edge), right = Math.min(hits[index + 1], edge);
      visibleArea += Math.max(0, right - left) * 2;
      const score = right - left - Math.abs(y - (low + high) / 2) * 0.45;
      if (right - left > 7 && (!best || score > best.score)) best = {x: (left + right) / 2, y, score};
    }
  }
  return visibleArea >= 60 ? best : null;
}

function annotation(ink, plane, slice, {scale, tip, center: origin}, overlay) {
  ink.save();
  ink.translate(origin, tip);
  ink.scale(scale, scale);
  ink.lineWidth = 0.38;
  ink.lineCap = 'round';
  ink.strokeStyle = '#8b9096';
  ink.fillStyle = '#9ea5ad';
  ink.font = '4.6px system-ui';
  ink.textAlign = 'right';
  ink.textBaseline = 'middle';
  const sin = Math.sin(plane.halfAngle);
  const cos = Math.cos(plane.halfAngle);
  for (let radius = 2 * CM; radius < plane.depth; radius += CM) {
    const x = -radius * sin;
    const y = radius * cos;
    const labeled = radius % (5 * CM) === 0;
    const size = labeled ? 2.2 : 1.2;
    ink.beginPath();
    ink.moveTo(x - cos * 0.8, y - sin * 0.8);
    ink.lineTo(x - cos * (0.8 + size), y - sin * (0.8 + size));
    ink.stroke();
    if (labeled) ink.fillText(`${radius / CM}`, x - 4.5, y - 2.6);
  }
  ink.restore();
  if (!overlay) return [];
  ink.save();
  ink.translate(origin, tip);
  ink.scale(scale, scale);
  ink.clip(sectorPath(plane, 5));
  ink.font = '600 6.1px system-ui';
  ink.textAlign = 'center';
  ink.textBaseline = 'middle';
  ink.lineJoin = 'round';
  const labels = [];
  for (const name of STRUCTURES[plane.id] ?? []) {
    const lumen = slice.chambers[name].lumen;
    const main = largestContour(lumen);
    if (polygonArea(main) < 40) continue;
    const center = poolCenter(main, plane);
    if (!center) continue;
    const color = chamberColor(name);
    ink.fillStyle = color.fill;
    ink.strokeStyle = color.edge;
    ink.lineWidth = 0.53;
    for (const outline of lumen) {
      const path = contourPath(outline);
      ink.fill(path);
      ink.stroke(path);
    }
    if (labels.every(({x, y}) => Math.hypot(x - center.x, y - center.y) > 10)) {
      labels.push({name, color, ...center});
    }
  }
  for (const {name, color, x, y} of labels) {
    ink.strokeStyle = 'rgba(8,11,13,0.82)';
    ink.lineWidth = 1.65;
    ink.strokeText(name, x, y);
    ink.fillStyle = color.edge;
    ink.fillText(name === 'DescAo' || name === 'Arch' ? 'Ao' : name, x, y);
  }
  ink.restore();
  return labels.map(({name, color}) => ({label: name, color: color.edge}));
}

export function createEchoRenderer() {
  const mask = makeSurface(RASTER_WIDTH, RASTER_HEIGHT, {willReadFrequently: true, alpha: false});
  const picture = makeSurface(RASTER_WIDTH, RASTER_HEIGHT, {alpha: false});
  const image = picture.ink.createImageData(RASTER_WIDTH, RASTER_HEIGHT);
  for (let index = 3; index < image.data.length; index += 4) image.data[index] = 255;
  let speckle;
  let viewId;
  return function renderEcho(ink, width, height, plane, slice, motion, overlay) {
    const calibration = bmodeCalibration(plane);
    if (viewId !== plane.id) {
      speckle = buildSpeckle(plane, calibration);
      viewId = plane.id;
    }
    paintReflectors(mask.ink, plane, slice, calibration);
    const reflector = mask.ink.getImageData(0, 0, RASTER_WIDTH, RASTER_HEIGHT).data;
    const {gain, tissue, pattern, interfaceGain} = speckle;
    const drift = motion.contraction * 3;
    const rowOffset = RASTER_WIDTH * Math.floor(drift);
    const driftPart = drift % 1;
    for (let index = 0; index < gain.length; index += 1) {
      if (!gain[index]) continue;
      const pixel = index * 4;
      const level = reflector[pixel] * 0.50 + (reflector[pixel - 4] + reflector[pixel + 4]) * 0.11
        + (reflector[pixel - 8] + reflector[pixel + 8]) * 0.05
        + (reflector[pixel - RASTER_WIDTH * 4] + reflector[pixel + RASTER_WIDTH * 4]) * 0.09;
      const carried = (pattern[index - rowOffset] || pattern[index]) * (1 - driftPart)
        + (pattern[index - rowOffset - RASTER_WIDTH] || pattern[index]) * driftPart;
      const grain = pattern[index] * 0.60 + carried * 0.40;
      const bright = level < 24 ? level + tissue[index] * (level / 50) : level * interfaceGain[index] + tissue[index] * 0.60;
      const exposure = 1.33 * bright * grain * gain[index];
      const lit = Math.max(0, exposure - 3.5);
      image.data[pixel] = lit;
      image.data[pixel + 1] = lit;
      image.data[pixel + 2] = lit;
    }
    picture.ink.putImageData(image, 0, 0);
    const labels = annotation(picture.ink, plane, slice, calibration, overlay);
    ink.fillStyle = '#000';
    ink.fillRect(0, 0, width, height);
    const fit = Math.min(width / RASTER_WIDTH, height / RASTER_HEIGHT);
    const displayWidth = RASTER_WIDTH * fit;
    const displayHeight = RASTER_HEIGHT * fit;
    ink.drawImage(picture.canvas, (width - displayWidth) / 2, (height - displayHeight) / 2, displayWidth, displayHeight);
    return labels;
  };
}
