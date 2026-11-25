import { loadSurfaces, sectionLayer } from './volume-contours.js';

const side = new URLSearchParams(location.search).get('side') === 'left' ? 'left' : 'right';
const byId = (id) => document.getElementById(id);
const definitions = [
  { name: 'Transverse', axes: [0, 1, 2], labels: ['R', 'L', 'A', 'P'] },
  { name: 'Coronal', axes: [0, 2, 1], labels: ['R', 'L', 'S', 'I'] },
  { name: 'Sagittal', axes: [1, 2, 0], labels: ['A', 'P', 'S', 'I'] },
];

async function loaded(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error('Unavailable scan data');
  return response;
}

async function loadVolume(info) {
  const bytes = new Uint8Array(await (await loaded('data/' + info.path)).arrayBuffer());
  let start = -1;
  for (let i = 1; i < Math.min(bytes.length, 8192); i++) {
    if (bytes[i - 1] === 10 && bytes[i] === 10) { start = i + 1; break; }
  }
  const header = new TextDecoder().decode(bytes.subarray(0, start));
  if (start < 0 || !header.startsWith('NRRD0005\n') ||
      !header.split('\n').includes('sizes: ' + info.size.join(' '))) throw new Error('Volume header mismatch');
  const stream = new Blob([bytes.subarray(start)]).stream().pipeThrough(new DecompressionStream('gzip'));
  const values = new Int16Array(await new Response(stream).arrayBuffer());
  if (values.length !== info.size.reduce((a, b) => a * b, 1)) throw new Error('Incomplete volume');
  return values;
}

function createPlane(definition, info, values, cursor, focalPoint, comparison, redraw) {
  const {name, axes: [u, v, depth], labels} = definition;
  const [nx, ny] = info.size;
  const strides = [1, nx, nx * ny];
  const width = info.size[u], height = info.size[v];
  const figure = document.createElement('figure');
  figure.className = 'volumePlane';
  figure.innerHTML = '<figcaption class="planeHead"><strong></strong><span></span></figcaption>' +
    '<canvas></canvas><label class="planeAxis"><input type="range"><output></output></label>';
  const canvas = figure.querySelector('canvas');
  const slider = figure.querySelector('input');
  figure.querySelector('strong').textContent = name;
  figure.querySelector('.planeHead span').textContent = labels[0] + '–' + labels[1] + ' / ' + labels[2] + '–' + labels[3];
  canvas.setAttribute('aria-label', name + ' section with linked crosshairs');
  slider.setAttribute('aria-label', name + ' slice');
  Object.assign(slider, {min:0, max:info.size[depth] - 1, step:1});
  const layers = document.createElement('canvas');
  layers.width = width; layers.height = height;
  const layer = layers.getContext('2d');
  const ctx = canvas.getContext('2d');
  const pixels = layer.createImageData(width, height);
  let previous = -1;
  let rect;
  let overlay;
  let overlaySlice = -1;
  function draw() {
    const d = cursor[depth];
    slider.value = d;
    figure.querySelector('output').textContent = (d + 1) + ' / ' + info.size[depth];
    if (previous !== d) {
      for (let j = 0; j < height; j++) {
        for (let i = 0; i < width; i++) {
          const n = (j * width + i) * 4;
          const val = values[d * strides[depth] + (width - i - 1) * strides[u] + (height - j - 1) * strides[v]];
          const hatch = (i + j) % 9 < 2 ? 32 : 22;
          pixels.data[n] = val < 0 ? hatch : val;
          pixels.data[n + 1] = val < 0 ? hatch + 10 : val;
          pixels.data[n + 2] = val < 0 ? hatch + 9 : val;
          pixels.data[n + 3] = 255;
        }
      }
      layer.putImageData(pixels, 0, 0);
      previous = d;
    }
    const length = Math.max(240, Math.round(canvas.clientWidth * Math.min(devicePixelRatio || 1, 2)));
    if (canvas.width !== length || canvas.height !== length) canvas.width = canvas.height = length;
    const fullExtent = Math.max(width * info.spacingMm[u], height * info.spacingMm[v]);
    const detail = byId('field').value === 'detail';
    const scale = length / (detail ? Math.min(fullExtent, depth === 2 ? 52 : 92) : fullExtent);
    const w = width * info.spacingMm[u] * scale, h = height * info.spacingMm[v] * scale;
    const cx = detail ? (width - focalPoint[u] - .5) / width : .5;
    const cy = detail ? (height - focalPoint[v] - .5) / height : .5;
    rect = {x:length / 2 - cx * w, y:length / 2 - cy * h, w, h};
    ctx.fillStyle = '#0d1919'; ctx.fillRect(0, 0, length, length);
    ctx.drawImage(layers,rect.x,rect.y,w,h);
    if (comparison.visible && comparison.surfaces) {
      if (d !== overlaySlice) {
        overlay = sectionLayer(comparison.surfaces, info, definition.axes, d);
        overlaySlice = d;
      }
      ctx.drawImage(overlay, rect.x, rect.y, w, h);
    }
    const x = rect.x + (width - cursor[u] - .5) / width * w;
    const y = rect.y + (height - cursor[v] - .5) / height * h;
    ctx.strokeStyle = '#aed9c7'; ctx.lineWidth = Math.max(1, length / 450);
    ctx.beginPath();
    ctx.moveTo(rect.x, y); ctx.lineTo(x-4, y); ctx.moveTo(x+4, y); ctx.lineTo(rect.x+w, y);
    ctx.moveTo(x, rect.y); ctx.lineTo(x, y-4); ctx.moveTo(x, y+4); ctx.lineTo(x, rect.y+h);
    ctx.stroke();
  }
  slider.oninput = () => {cursor[depth] = Number(slider.value); redraw();};
  canvas.onclick = (event) => {
    const box = canvas.getBoundingClientRect();
    const x = ((event.clientX - box.left) / box.width * canvas.width - rect.x) / rect.w;
    const y = ((event.clientY - box.top) / box.height * canvas.height - rect.y) / rect.h;
    if (x < 0 || y < 0 || x >= 1 || y >= 1) return;
    cursor[u] = width - 1 - Math.floor(x * width); cursor[v] = height - 1 - Math.floor(y * height);
    redraw();
  };
  byId('planes').append(figure);
  return draw;
}

async function start() {
  byId('returnExam').href = './?side=' + side;
  byId('volumeTitle').textContent = (side === 'right' ? 'Right' : 'Left') + ' carotid · Stitched volume';
  const geometry = await (await loaded('data/protocol-geometry.json')).json();
  const info = geometry.volumes[side];
  const values = await loadVolume(info);
  const cursor = info.focusMm.map((x,i) => Math.max(0, Math.min(info.size[i]-1, Math.round((x-info.originMm[i])/info.spacingMm[i]))));
  const focalPoint = [...cursor];
  const panels = [];
  const comparison = {visible:false, surfaces:null};
  const frames = geometry.tracking[side];
  const redraw = () => {
    if (byId('field').value === 'detail') {
      cursor.forEach((step, axis) => {
        const allowance = (axis === 2 ? 92 : 52) * .4 / info.spacingMm[axis];
        const delta = step - focalPoint[axis];
        if (Math.abs(delta) > allowance) focalPoint[axis] = step - Math.sign(delta) * allowance;
      });
    }
    if (comparison.visible) {
      const z = info.originMm[2] + info.spacingMm[2]*cursor[2];
      const nearest = frames.reduce((a,b) => Math.abs(a.contact[2]-z) <= Math.abs(b.contact[2]-z) ? a : b);
      byId('visibility').textContent = 'Nearest recorded transverse section · ' +
        Math.round(nearest.observedSourceFraction*100) + '% of modeled lumen visible';
    }
    panels.forEach(draw => draw());
  };
  byId('compare').onclick = async () => {
    const button = byId('compare');
    const message = byId('compareStatus');
    button.disabled = true;
    message.hidden = true;
    try {
      comparison.surfaces ??= await loadSurfaces(geometry.reconstructions[side]);
      comparison.visible = !comparison.visible;
      button.setAttribute('aria-pressed', String(comparison.visible));
      byId('comparisonKey').hidden = !comparison.visible;
      redraw();
    } catch {
      message.hidden = false;
      message.textContent = 'Comparison unavailable. Select Compare lumen to retry.';
    } finally { button.disabled = false; }
  };
  byId('acquisition').textContent = info.planes + ' tracked transverse sections · ' +
    ((info.size[2]-1)*info.spacingMm[2]).toFixed(0) + ' mm acquired length';
  byId('download').href = 'data/' + info.path;
  byId('viewer').hidden = false; byId('status').hidden = true;
  byId('field').onchange = () => {
    focalPoint.splice(0, 3, ...cursor);
    redraw();
  };
  for (const d of definitions) panels.push(createPlane(d, info, values, cursor, focalPoint, comparison, redraw));
  new ResizeObserver(redraw).observe(byId('planes'));
  redraw();
}

start().catch(() => {
  byId('viewer').hidden = true; byId('status').hidden = false;
  byId('status').textContent = 'The stitched volume could not be opened. ';
  const retry = document.createElement('button');
  retry.textContent = 'Retry'; retry.onclick = () => location.reload();
  byId('status').append(retry);
});
