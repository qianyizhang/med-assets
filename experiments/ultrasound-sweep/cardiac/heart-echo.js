// B-mode styling is illustrative. The tissue/blood interfaces come from heartSection.
const RASTER_WIDTH = 396;
const RASTER_HEIGHT = 322;
const TIP = 9;
const CENTER = RASTER_WIDTH / 2;
const CM = 10;
const RIGHT_HEART = {fill: 'rgba(45,196,207,0.18)', edge: '#81e1eb'};
const LEFT_HEART = {fill: 'rgba(242,117,107,0.19)', edge: '#ffb1a2'};

export function chamberColor(name) {
  return name[0] === 'R' ? RIGHT_HEART : LEFT_HEART;
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

export function contourPath(rows) {
  const path = new Path2D();
  if (!rows.length) return path;
  path.moveTo(rows[0][1], rows[0][0]);
  for (const [depth, left] of rows) path.lineTo(left, depth);
  for (let index = rows.length - 1; index >= 0; index -= 1) path.lineTo(rows[index][2], rows[index][0]);
  path.closePath();
  return path;
}

export function linePath(points) {
  const path = new Path2D();
  if (points.length) path.moveTo(...points[0]);
  for (let index = 1; index < points.length; index += 1) path.lineTo(...points[index]);
  return path;
}

export function pairedLumen(chambers, ventricle, atrium) {
  const v = chambers[ventricle].lumen;
  const a = chambers[atrium].lumen;
  return v.length && a.length && Math.abs(v.at(-1)[0] - a[0][0]) < 0.001 ? [v.concat(a.slice(1))] : [v, a];
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

function buildSpeckle(plane, scale) {
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
      const x = (viewX - CENTER) / scale;
      const y = (viewY - TIP) / scale;
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
      const lateralLoss = 0.65 * Math.exp(-((x - 39) ** 2) / 770 - ((y - 74) ** 2) / 1600);
      const nearLoss = 0.44 * Math.exp(-((y - 24) ** 2) / 395);
      interfaceGain[index] = (1 - lateralLoss) * (1 - nearLoss) * (0.71 + 0.52 * broadSample);
      pattern[index] = 0.23 + fineSample * 0.38 + midSample ** 2 * 0.96 + broadSample ** 2 * 1.20;
    }
  }
  return {pattern, tissue, gain, interfaceGain};
}

function visibleExterior(chambers, owner, x, y) {
  for (const [name, chest] of Object.entries(chambers)) {
    if (name === owner) continue;
    const rows = chest.wall;
    for (let index = 1; index < rows.length; index += 1) {
      const [depth, left, right] = rows[index];
      if (y > depth) continue;
      const [before, previousLeft, previousRight] = rows[index - 1];
      if (y < before) break;
      const f = (y - before) / (depth - before);
      if (x > previousLeft + (left - previousLeft) * f && x < previousRight + (right - previousRight) * f) return false;
      break;
    }
  }
  return true;
}

function echoEdges(ink, rows, width, brightness, accept) {
  const paths = Array.from({length: 5}, () => new Path2D());
  for (let side = 1; side < 3; side += 1) {
    for (let index = 1; index < rows.length; index += 1) {
      const [y, x] = [rows[index][0], rows[index][side]];
      const [priorY, priorX] = [rows[index - 1][0], rows[index - 1][side]];
      const mx = (x + priorX) * 0.5;
      const my = (y + priorY) * 0.5;
      if (!accept(mx, my)) continue;
      const dx = x - priorX;
      const dy = y - priorY;
      const length = Math.hypot(dx, dy) * Math.hypot(mx, my);
      if (length < 0.0001) continue;
      const shiver = Math.sin(mx * 0.54 + my * 0.32) * Math.cos(my * 0.32) * 0.40;
      const incidence = Math.abs(dx * my - dy * mx) / length;
      const bin = Math.min(paths.length - 1, Math.max(0, Math.round((incidence * 0.78 + shiver) * 4)));
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

function paintReflectors(ink, plane, slice, scale) {
  ink.setTransform(1, 0, 0, 1, 0, 0);
  ink.fillStyle = '#111';
  ink.fillRect(0, 0, RASTER_WIDTH, RASTER_HEIGHT);
  ink.save();
  ink.setTransform(scale, 0, 0, scale, CENTER, TIP);
  ink.clip(sectorPath(plane, 5));
  const {chambers, valveCuts, muscleCuts} = slice;
  ink.lineCap = 'round';
  ink.lineJoin = 'round';
  for (const {wall} of Object.values(chambers)) {
    ink.fillStyle = '#414141';
    ink.fill(contourPath(wall));
  }
  for (const [name, {wall}] of Object.entries(chambers)) {
    echoEdges(ink, wall, 1.35, 65, (x, y) => visibleExterior(chambers, name, x, y));
  }
  const lumens = pairedLumen(chambers, 'LV', 'LA').concat(pairedLumen(chambers, 'RV', 'RA'));
  for (const lumen of lumens) {
    ink.fillStyle = '#0a0a0a';
    ink.fill(contourPath(lumen));
  }
  for (const lumen of lumens) echoEdges(ink, lumen, 0.93, 58, () => true);
  for (const rows of muscleCuts) {
    const path = contourPath(rows);
    ink.fillStyle = '#434343';
    ink.fill(path);
    ink.strokeStyle = '#696969';
    ink.lineWidth = 0.85;
    ink.stroke(path);
  }
  for (const {name, points} of valveCuts) {
    const path = linePath(points);
    ink.strokeStyle = name === 'MV' ? '#7a7a7a' : '#585858';
    ink.lineWidth = 2.5;
    ink.stroke(path);
    ink.strokeStyle = name === 'MV' ? '#c4c4c4' : '#9c9c9c';
    ink.lineWidth = 1.10;
    ink.stroke(path);
  }
  ink.restore();
}

function annotation(ink, plane, slice, scale, overlay) {
  ink.save();
  ink.translate(CENTER, TIP);
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
  if (!overlay) return;
  ink.save();
  ink.translate(CENTER, TIP);
  ink.scale(scale, scale);
  ink.clip(sectorPath(plane, 5));
  ink.font = '600 6.1px system-ui';
  ink.textAlign = 'center';
  ink.textBaseline = 'middle';
  ink.lineJoin = 'round';
  for (const [name, {lumen}] of Object.entries(slice.chambers)) {
    if (lumen.length < 3) continue;
    const path = contourPath(lumen);
    const color = chamberColor(name);
    ink.fillStyle = color.fill;
    ink.fill(path);
    ink.lineWidth = 0.53;
    ink.strokeStyle = color.edge;
    ink.stroke(path);
    const [y, left, right] = lumen[Math.round((lumen.length - 1) * (name[1] === 'V' ? 0.62 : 0.49))];
    if (right - left < 11) continue;
    const x = (left + right) / 2;
    ink.strokeStyle = 'rgba(8,11,13,0.82)';
    ink.lineWidth = 1.65;
    ink.strokeText(name, x, y);
    ink.fillStyle = color.edge;
    ink.fillText(name, x, y);
  }
  ink.restore();
}

export function createEchoRenderer() {
  const mask = makeSurface(RASTER_WIDTH, RASTER_HEIGHT, {willReadFrequently: true, alpha: false});
  const picture = makeSurface(RASTER_WIDTH, RASTER_HEIGHT, {alpha: false});
  const image = picture.ink.createImageData(RASTER_WIDTH, RASTER_HEIGHT);
  for (let index = 3; index < image.data.length; index += 4) image.data[index] = 255;
  let speckle;
  return function renderEcho(ink, width, height, plane, slice, motion, overlay) {
    const scale = (RASTER_HEIGHT - TIP - 9) / plane.depth;
    speckle ??= buildSpeckle(plane, scale);
    paintReflectors(mask.ink, plane, slice, scale);
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
    annotation(picture.ink, plane, slice, scale, overlay);
    ink.fillStyle = '#000';
    ink.fillRect(0, 0, width, height);
    const fit = Math.min(width / RASTER_WIDTH, height / RASTER_HEIGHT);
    const displayWidth = RASTER_WIDTH * fit;
    const displayHeight = RASTER_HEIGHT * fit;
    ink.drawImage(picture.canvas, (width - displayWidth) / 2, (height - displayHeight) / 2, displayWidth, displayHeight);
  };
}
