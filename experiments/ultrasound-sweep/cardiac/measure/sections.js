import { bmodeCalibration } from '../heart-poses.js';
import * as geometry from '../heart-geometry.js';
import { diskTrace, diskVolume, distance, fractionalChange, polygonArea } from './calculations.js';
import { caliperTargets } from './protocol.js';

function ringIntersections(ring, plane) {
  const cut = [];
  for (let i = 0; i < ring.length; i++) {
    const a = ring[i],
      b = ring[(i + 1) % ring.length],
      da = plane.distance(a),
      db = plane.distance(b);
    if (Math.abs(da) < 1e-8) cut.push(plane.section(a));
    if (da * db < 0) cut.push(plane.section(a.map((v, j) => v + ((b[j] - v) * da) / (da - db))));
  }
  return cut;
}
function ringCut(phase, id, name) {
  const plane = geometry.probePlane(0, id);
  const rings = geometry.heartFrame(phase).chambers[name].lumen;
  return ringIntersections(name.endsWith('V') ? rings.at(-1) : rings[0], plane);
}
function chamberTrace(phase, id, name) {
  const poly = geometry.measurementContour(phase, id, name);
  const annulus = ringCut(phase, id, name);
  if (!poly?.length || annulus.length < 2) return null;
  const base = annulus.reduce((a, p) => [a[0] + p[0] / annulus.length, a[1] + p[1] / annulus.length], [0, 0]);
  return diskTrace(poly, base);
}
function drawContour(g, t, box, caption, showDisks, zoom) {
  const [x, y, w, h] = box;
  const allX = t.poly.map((p) => p[0]),
    allY = t.poly.map((p) => p[1]);
  const l = Math.min(...allX),
    r = Math.max(...allX),
    top = Math.min(...allY),
    bot = Math.max(...allY);
  const point = (p) => [
    x + w / 2 + (p[0] - (l + r) / 2) * zoom,
    y + 17 + h / 2 + (p[1] - (top + bot) / 2) * zoom,
  ];
  g.beginPath();
  t.poly.forEach((p, i) => (i ? g.lineTo(...point(p)) : g.moveTo(...point(p))));
  g.closePath();
  g.fillStyle = '#173c45';
  g.fill();
  g.strokeStyle = '#89d8cb';
  g.lineWidth = 2;
  g.stroke();
  if (showDisks) {
    g.strokeStyle = 'rgba(147,207,216,.56)';
    g.lineWidth = 1;
    g.beginPath();
    for (const [a, b] of t.segments) {
      g.moveTo(...point(a));
      g.lineTo(...point(b));
    }
    g.stroke();
  }
  g.strokeStyle = '#edbd80';
  g.beginPath();
  g.moveTo(...point(t.base));
  g.lineTo(...point(t.tip));
  g.stroke();
  g.fillStyle = '#d9e7e3';
  g.font = '15px system-ui';
  g.fillText(caption, x + 8, y + 19);
}
function printValues(host, items) {
  host.replaceChildren(
    ...items.map((item) => {
      const span = document.createElement('span');
      span.textContent = item;
      return span;
    }),
  );
}
export function volumePanel(host, id, context) {
  host.innerHTML = `<p class="mw-guide"></p><div class="mw-switch"></div><canvas class="mw-plot" width="760" height="248" aria-label="Endocardial borders and chamber axes used for measurement"></canvas><output class="mw-values"></output><p class="mw-explain"></p>`;
  const name = id.toUpperCase(),
    isLV = id === 'lv',
    isLA = id === 'la',
    isRV = id === 'rv';
  const biplane = isLV || isLA;
  const field = host.querySelector('.mw-switch'),
    c = host.querySelector('canvas'),
    g = c.getContext('2d');
  host.querySelector('.mw-guide').textContent = biplane
    ? 'Inspect the paired A4C and A2C endocardial contours and the 20 perpendicular disk diameters.'
    : isRV
      ? 'Compare the traced RV cavity area at end diastole and end systole in the RV-focused window.'
      : 'Inspect the right atrial contour at end systole. The basal chord closes the tracing at the tricuspid annulus.';
  let phase = isLA || id === 'ra' ? 0.35 : 0;
  const pair = (p) =>
    biplane
      ? ['a4c', 'a2c'].map((v) => chamberTrace(p, v, name))
      : [chamberTrace(p, isRV ? 'rv-focused' : context.state.viewId, name)];
  const ed = pair(0),
    es = pair(0.35);
  if (es.some((t) => !t) || ((isLV || isRV) && ed.some((t) => !t))) {
    host.replaceChildren(
      document.createTextNode(
        'The required model contour or annular intersection is unavailable for this measurement.',
      ),
    );
    return;
  }
  const allTraces = [...ed, ...es].filter(Boolean);
  const bounds = allTraces.map((trace) => {
    const xs = trace.poly.map((p) => p[0]),
      ys = trace.poly.map((p) => p[1]);
    return [Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
  });
  // Use a common scale for the different views and both phases.
  const zoom = Math.min(
    300 / Math.max(...bounds.map((b) => b[0])),
    194 / Math.max(...bounds.map((b) => b[1])),
  );
  let bsa = 1.8;
  if (isLV || isRV)
    for (const [label, v] of [
      ['End diastole', 0],
      ['End systole', 0.35],
    ]) {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.dataset.phase = v;
      b.onclick = () => {
        phase = v;
        context.onSeek(v);
        draw();
      };
      field.append(b);
    }
  if (isLA || id === 'ra') {
    const label = document.createElement('label'),
      input = document.createElement('input');
    label.textContent = 'Example body surface area ';
    input.type = 'number';
    input.min = '.4';
    input.max = '4';
    input.step = '.01';
    input.value = bsa;
    input.setAttribute('aria-label', 'Example body surface area in square meters');
    input.oninput = () => {
      bsa = input.validity.valid && input.value !== '' ? Number(input.value) : NaN;
      draw();
    };
    label.append(input, ' m²');
    field.append(label);
  }
  function draw() {
    for (const b of field.querySelectorAll('button'))
      b.setAttribute('aria-pressed', Number(b.dataset.phase) === phase);
    const t = phase === 0 ? ed : es;
    g.fillStyle = '#0e1a20';
    g.fillRect(0, 0, c.width, c.height);
    if (biplane) {
      drawContour(g, t[0], [18, 0, 340, 236], 'Apical four chamber', true, zoom);
      drawContour(g, t[1], [399, 0, 340, 236], 'Apical two chamber', true, zoom);
    } else if (isRV) {
      drawContour(g, ed[0], [18, 0, 340, 236], 'End diastole', false, zoom);
      drawContour(g, es[0], [399, 0, 340, 236], 'End systole', false, zoom);
    } else drawContour(g, es[0], [194, 0, 370, 236], 'End systole', true, zoom);
    let result = [];
    if (isLV) {
      const full = diskVolume(...ed),
        empty = diskVolume(...es);
      result = [
        'EDV ' + full.toFixed(0) + ' mL',
        'ESV ' + empty.toFixed(0) + ' mL',
        'EF ' + fractionalChange(full, empty).toFixed(0) + '%',
      ];
    } else if (isRV) {
      const full = polygonArea(ed[0].poly) / 100,
        empty = polygonArea(es[0].poly) / 100;
      result = [
        'ED area ' + full.toFixed(1) + ' cm²',
        'ES area ' + empty.toFixed(1) + ' cm²',
        'FAC ' + fractionalChange(full, empty).toFixed(0) + '%',
      ];
    } else {
      const volume = isLA ? diskVolume(...es) : diskVolume(es[0], es[0]);
      result = (isLA ? [] : ['Area ' + (polygonArea(es[0].poly) / 100).toFixed(1) + ' cm²']).concat([
        'ES volume ' + volume.toFixed(1) + ' mL',
        Number.isFinite(bsa)
          ? 'Volume index ' + (volume / bsa).toFixed(1) + ' mL/m²'
          : 'Enter a body surface area to index volume',
      ]);
    }
    printValues(host.querySelector('output'), result);
    let note = 'Borders come from the neutral model planes at the indicated phases. ';
    note += isRV
      ? 'FAC = (ED area − ES area) / ED area.'
      : id === 'ra'
        ? 'Single-plane disk summation assumes circular disks.'
        : 'Disk volumes use the long axis and paired endocardial widths in millimetres.';
    if (biplane) note += ' Long axes ' + t.map((a) => (a.length / 10).toFixed(1)).join(' / ') + ' cm.';
    if (isLA && Math.abs(t[0].length - t[1].length) > 5)
      note += ' The LA axes differ by more than 5 mm. A clinical volume would require improved views.';
    host.querySelector('.mw-explain').textContent = note;
  }
  draw();
}
export function movementPanel(host, id, context) {
  const ivc = id === 'ivc',
    c = document.createElement('canvas');
  c.width = 760;
  c.height = 224;
  c.className = 'mw-plot';
  c.setAttribute(
    'aria-label',
    ivc
      ? 'Modeled IVC diameter changes during a six-second respiratory cycle'
      : 'Model tricuspid annulus distance from the transducer over one cardiac cycle',
  );
  const g = c.getContext('2d');
  host.innerHTML =
    '<p class="mw-guide"></p><div class="mw-motion"></div><output class="mw-values"></output><p class="mw-explain"></p>';
  host.querySelector('.mw-motion').append(c);
  host.querySelector('.mw-guide').textContent = ivc
    ? 'Inspect the IVC caliber as inspiration lowers intrathoracic pressure. This separate six-second example has its own respiratory clock.'
    : 'Follow the lateral tricuspid annulus from end diastole to maximal systolic excursion along its direction of motion.';
  const yAt = (p) => {
    const ends = ringCut(p, 'rv-focused', 'RV');
    return ends.length ? ends.reduce((a, b) => (a[0] < b[0] ? a : b)) : null;
  };
  const ed = ivc ? null : yAt(0),
    es = ivc ? null : yAt(0.35);
  if (!ivc && (!ed || !es)) {
    host.textContent = 'The lateral annulus is unavailable in the focused plane.';
    return;
  }
  const excursion = ivc ? 0 : distance(ed, es);
  const direction = ivc || !excursion ? [0, 1] : [(ed[0] - es[0]) / excursion, (ed[1] - es[1]) / excursion];
  const samples = ivc
    ? null
    : Array.from({ length: 101 }, (_, i) => {
        const p = yAt(i / 100);
        return p ? (p[0] - ed[0]) * direction[0] + (p[1] - ed[1]) * direction[1] : NaN;
      });
  let minimum = 7;
  if (ivc) {
    const wrap = document.createElement('label'),
      input = document.createElement('input'),
      v = document.createElement('span');
    wrap.className = 'mw-slider';
    wrap.textContent = 'Inspiratory diameter ';
    input.type = 'range';
    input.min = 3;
    input.max = 17;
    input.value = minimum;
    wrap.append(input, v);
    v.textContent = minimum + ' mm';
    input.oninput = () => {
      minimum = Number(input.value);
      v.textContent = minimum + ' mm';
      draw();
    };
    host.querySelector('.mw-motion').append(wrap);
  }
  function draw() {
    g.fillStyle = '#0e1a20';
    g.fillRect(0, 0, 760, 224);
    g.font = '15px system-ui';
    g.fillStyle = '#c3d7d2';
    g.fillText(ivc ? 'Diameter · mm' : 'Annular displacement · mm', 18, 22);
    const map = (v) => (ivc ? 169 - v * 5.2 : 60 - v * 5.0);
    for (const tick of ivc ? [0, 10, 20] : [0, -10, -20]) {
      g.fillText(String(tick), 14, map(tick) + 4);
      g.strokeStyle = '#344a50';
      g.beginPath();
      g.moveTo(55, map(tick));
      g.lineTo(726, map(tick));
      g.stroke();
    }
    g.strokeStyle = '#a4e7d5';
    g.lineWidth = 2.4;
    g.beginPath();
    for (let i = 0; i <= 100; i++) {
      const p = i / 100,
        v = ivc ? 18 - (18 - minimum) * Math.sin(Math.PI * p) ** 4 : samples[i];
      const x = 55 + 671 * p;
      if (i) g.lineTo(x, map(v));
      else g.moveTo(x, map(v));
    }
    g.stroke();
    g.fillStyle = '#c3d7d2';
    g.fillText(ivc ? 'Expiration' : 'ED', 55, 207);
    g.fillText(ivc ? 'Inspiration' : 'ES', ivc ? 349 : 283, 207);
    g.fillText(ivc ? '6 s' : '980 ms', 669, 207);
    printValues(
      host.querySelector('output'),
      ivc
        ? [
            'Expiration 18 mm',
            'Inspiration ' + minimum + ' mm',
            'Collapse ' + fractionalChange(18, minimum).toFixed(0) + '%',
          ]
        : ['TAPSE ' + excursion.toFixed(1) + ' mm'],
    );
    host.querySelector('.mw-explain').textContent = ivc
      ? 'Prescribed respiratory diameters illustrate (maximum − minimum) / maximum. The gallery heart has no measured respiratory cine. Clinical pressure estimates consider caliber, sniff response, respiratory support and other findings.'
      : 'The curve projects the moving model hinge onto its ED-to-ES axis. A clinical M-mode recording requires a cursor aligned along lateral annular excursion.';
  }
  draw();
}

const savedMeasures = {
  'LV internal diameter · ED': ['lvidd', 0, 'End diastole'],
  'LV internal diameter · ES': ['lvids', 0.35, 'End systole'],
  'Septal thickness': ['ivs', 0, 'End diastole'],
  'Posterior wall thickness': ['pw', 0, 'End diastole'],
  'LVOT diameter': ['lvot', 0.17, 'Mid systole'],
};
function linearResults(m) {
  const items = [];
  if (m.lvidd && m.lvids)
    items.push('Fractional shortening ' + fractionalChange(m.lvidd, m.lvids).toFixed(0) + '%');
  if (m.lvidd && m.pw) items.push('Relative wall thickness ' + ((2 * m.pw) / m.lvidd).toFixed(2));
  if (m.lvidd && m.ivs && m.pw) {
    const cavity = m.lvidd / 10,
      outer = (m.lvidd + m.ivs + m.pw) / 10;
    const mass = 0.8 * 1.04 * (outer ** 3 - cavity ** 3) + 0.6;
    items.push('Linear LV mass ' + mass.toFixed(0) + ' g');
  }
  return items;
}
export function caliperPanel(host, context) {
  host.innerHTML = `<div class="mw-actions"><label>Structure <select></select></label><button type="button" data-freeze>Freeze current section</button><button type="button" data-phase hidden></button></div><p class="mw-guide"></p>
    <canvas class="mw-plot mw-calipers" width="660" height="365" tabindex="0" aria-label="Frozen section. Click two points, or use arrow keys and Enter to place calipers"></canvas>
    <output class="mw-values"></output><div class="mw-actions"><button type="button" data-clear>Clear points</button><button type="button" data-save hidden></button></div><p data-linear></p><p class="mw-explain">Click two endpoints. With the image focused, use arrow keys and Enter. Shift moves in larger steps.</p>`;
  const opts = caliperTargets[context.state.viewId] || {
    Distance:
      'Choose the required phase and tissue boundaries, freeze the section, then place the two calipers.',
  };
  const select = host.querySelector('select');
  for (const label of Object.keys(opts)) select.add(new Option(label, label));
  const canvas = host.querySelector('canvas'),
    g = canvas.getContext('2d');
  const frozen = document.createElement('canvas');
  frozen.width = canvas.width;
  frozen.height = canvas.height;
  let points = [],
    cross = [330, 160],
    saved,
    scale = 0,
    result = 0,
    field,
    tipX,
    tipY;
  function render() {
    g.drawImage(frozen, 0, 0);
    g.strokeStyle = '#ffd58b';
    g.fillStyle = '#ffd58b';
    g.lineWidth = 2;
    if (points.length === 2) {
      g.beginPath();
      g.moveTo(...points[0]);
      g.lineTo(...points[1]);
      g.stroke();
    }
    for (const [x, y] of points) {
      g.beginPath();
      g.moveTo(x - 6, y);
      g.lineTo(x + 6, y);
      g.moveTo(x, y - 6);
      g.lineTo(x, y + 6);
      g.stroke();
    }
    if (document.activeElement === canvas) {
      const [x, y] = cross;
      g.strokeStyle = '#8ee9e1';
      g.strokeRect(x - 4, y - 4, 8, 8);
    }
    result = points.length === 2 ? distance(points[0], points[1]) / scale : 0;
    const out = host.querySelector('output');
    out.textContent =
      (result ? 'Distance ' + result.toFixed(1) + ' mm · ' : '') +
      (saved
        ? 'Frozen at ' + Math.round(saved.phase * 100) + '% phase, ' + saved.tilt + '° rotation'
        : 'Section unavailable');
    const accept = host.querySelector('[data-save]');
    const task = savedMeasures[select.value];
    accept.hidden = !task || !result;
    if (task && result) {
      const [key, phase, label] = task,
        delta = Math.abs(saved.phase - phase);
      const phaseOk = Math.min(delta, 1 - delta) <= 0.025;
      const sizeOk = key !== 'lvot' || (result >= 8 && result <= 35);
      accept.disabled = !phaseOk || !sizeOk;
      accept.textContent = key === 'lvot' ? 'Use as LVOT diameter' : 'Save ' + select.value;
      if (!phaseOk) out.textContent += ' · Freeze at ' + label.toLowerCase() + ' to save';
      else if (!sizeOk) out.textContent += ' · The outflow exercise accepts 8–35 mm diameters';
    }
    host.querySelector('[data-linear]').textContent = linearResults(context.linear).join(' · ');
  }
  function freeze() {
    const state = context.getState();
    const source = context.section,
      fg = frozen.getContext('2d');
    fg.fillStyle = '#000';
    fg.fillRect(0, 0, frozen.width, frozen.height);
    saved = null;
    scale = 0;
    points = [];
    if (source.width > 0 && source.height > 0 && source.clientWidth > 0) {
      // Crop only the letterbox. Display the same 396 × 322 virtual sector on
      // a fixed calibration grid, independent of device pixel ratio.
      field = geometry.probePlane(state.tilt, state.viewId);
      const raster = bmodeCalibration(field);
      const fit = Math.min(source.width / raster.width, source.height / raster.height);
      const w = raster.width * fit,
        h = raster.height * fit;
      const dest = Math.min(canvas.width / raster.width, canvas.height / raster.height);
      const x = (canvas.width - raster.width * dest) / 2,
        y = (canvas.height - raster.height * dest) / 2;
      fg.drawImage(
        source,
        (source.width - w) / 2,
        (source.height - h) / 2,
        w,
        h,
        x,
        y,
        raster.width * dest,
        raster.height * dest,
      );
      scale = raster.scale * dest;
      tipX = x + raster.center * dest;
      tipY = y + raster.tip * dest;
      saved = { ...state };
    }
    render();
  }
  function recordPoint(point) {
    if (!saved) return;
    const lateral = (point[0] - tipX) / scale,
      depth = (point[1] - tipY) / scale;
    if (
      depth < 0 ||
      Math.atan2(Math.abs(lateral), depth) > field.halfAngle ||
      Math.hypot(lateral, depth) > field.depth
    ) {
      host.querySelector('output').textContent = 'Place the endpoint inside the scanned sector.';
      return;
    }
    if (points.length === 2) points = [];
    points.push([...point]);
    render();
  }
  canvas.onclick = (e) => {
    const box = canvas.getBoundingClientRect();
    cross = [
      ((e.clientX - box.left) * canvas.width) / box.width,
      ((e.clientY - box.top) * canvas.height) / box.height,
    ];
    recordPoint(cross);
  };
  canvas.onkeydown = (e) => {
    const step = e.shiftKey ? 10 : 1,
      keys = { ArrowRight: [step, 0], ArrowLeft: [-step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      recordPoint(cross);
      return;
    } else if (keys[e.key])
      cross = cross.map((v, i) =>
        Math.max(0, Math.min(i ? canvas.height : canvas.width, v + keys[e.key][i])),
      );
    else return;
    e.preventDefault();
    render();
  };
  canvas.onfocus = canvas.onblur = render;
  host.querySelector('[data-freeze]').onclick = freeze;
  host.querySelector('[data-clear]').onclick = () => {
    points = [];
    render();
  };
  host.querySelector('[data-save]').onclick = () => {
    const [key] = savedMeasures[select.value];
    if (key === 'lvot') context.diameter = Number((result / 10).toFixed(2));
    else context.linear[key] = result;
    render();
    host.querySelector('output').textContent += ' · Saved for this session';
  };
  const phaseButton = host.querySelector('[data-phase]');
  phaseButton.onclick = () => {
    context.onSeek(savedMeasures[select.value][1]);
    freeze();
  };
  function configure() {
    host.querySelector('.mw-guide').textContent = opts[select.value];
    points = [];
    render();
    const task = savedMeasures[select.value];
    phaseButton.hidden = !task;
    if (task) phaseButton.textContent = 'Freeze at ' + task[2].toLowerCase();
  }
  select.onchange = configure;
  configure();
  freeze();
}
