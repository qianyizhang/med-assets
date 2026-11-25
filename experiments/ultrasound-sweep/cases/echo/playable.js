import { heartFrame, heartSection } from '../../cardiac/heart-geometry.js';
import { bmodeCalibration, BMODE_RASTER, CARDIAC_VIEWS, directedPlane } from '../../cardiac/heart-poses.js';
import { createEchoRenderer } from '../../cardiac/heart-echo.js';
import { outletValves } from '../../cardiac/heart-vessels.js';
import { renderScene } from '../../cardiac/heart-scene.js';
import { sectorPath } from '../../cardiac/heart-echo.js';
import { axialFlow } from '../../cardiac/measure/color-section.js';
import { integral, velocity } from '../../cardiac/measure/calculations.js';
import { spectra, BEAT_SECONDS } from '../../cardiac/measure/protocol.js';
import { apical, flowCase, lvotPW } from './playable-signals.js';

// Centimetres in the report, millimetres in the heart frame. The right upper
// parasternal contact projects to (-44,1304,177.47) on the shipped torso skin.
const alternate = {
  origin: [-40.4272, 163.0661, -116.3605],
  target: [10, 117, -22],
  right: [1, 0, 0],
  depth: 150,
};
const descriptions = {
  a4c: 'Capture end systole and diastole at the true apex, following the mitral annulus and LV endocardium.',
  a2c: 'Turn to the orthogonal apical cut. Compare the anterior and inferior walls across the same cardiac clock.',
  'rv-focused': 'Keep the RV apex in plane and follow the cavity area through contraction.',
  'psax-av': 'Rotate through the aortic root to capture systolic cusp excursion.',
  plax: 'Follow the contiguous LV inlet, outflow tract and proximal aorta.',
  'subcostal-4c': 'Sweep the subcostal window along the cardiac border and inspect the pericardial space.',
};
const normalChapters = [
  ['plax', 'great-vessels'],
  ['rv-inflow', 'right-heart'],
  ['rv-outflow', 'right-flow'],
  ['psax-av', 'outflow'],
  ['psax-mv', 'filling'],
  ['psax-papillary', 'biplane'],
  ['psax-apical', 'biplane'],
  ['a4c', 'biplane'],
  ['a2c', 'axes'],
  ['rv-focused', 'right-heart'],
  ['a5c', 'outflow'],
  ['a3c', 'great-vessels'],
  ['subcostal-4c', 'pericardium'],
  ['subcostal-ivc', 'ivc'],
  ['subcostal-sax', 'right-flow'],
  ['subcostal-aorta', 'great-vessels'],
  ['suprasternal-arch', 'great-vessels'],
];
const sampleSites = {
  mitral: [21, 99, -4],
  tricuspid: [-19, 97, -6],
  aortic: [10, 117, -22],
  lvot: [14, 105, -18],
  pulmonary: [-10, 119, -42],
  tr: [-19, 97, -6],
};
function chapter(record, view, image, mode = 'section', signal = null, caption = null, value = null) {
  const v = record.views.find((x) => x.image === image + '.svg');
  const title = caption || CARDIAC_VIEWS[view]?.label || 'Right parasternal';
  const measurement =
    value ??
    (mode === 'section' && ['a4c', 'rv-focused', 'a2c', 'subcostal-ivc'].includes(view) ? v.measurement : '');
  return {
    id: [view, mode, signal].filter(Boolean).join('-'),
    title,
    viewImage: v.image,
    frames: 39,
    evidenceFrame:
      mode === 'doppler'
        ? 38
        : view === 'subcostal-ivc'
          ? 30
          : view === 'psax-av' || mode === 'diameter'
            ? 24
            : mode === 'color'
              ? ['mitral', 'tricuspid'].includes(signal)
                ? 30
                : 23
              : 27,
    observation:
      mode === 'section'
        ? descriptions[view] || 'Sweep through the named window and follow its landmarks through the beat.'
        : v.caption,
    measurement: measurement || '',
    view,
    mode,
    signal,
  };
}
export function chapters(record) {
  if (record.kind === 'normal') {
    const rows = normalChapters.map(([v, i]) => chapter(record, v, i));
    for (const [site, window, image] of [
      ['mitral', 'a4c', 'filling'],
      ['tricuspid', 'rv-inflow', 'filling'],
      ['lvot', 'a5c', 'outflow'],
      ['aortic', 'a5c', 'outflow'],
      ['pulmonary', 'rv-outflow', 'right-flow'],
      ['tr', 'rv-focused', 'right-flow'],
    ]) {
      if (!['lvot', 'tr'].includes(site))
        rows.push(chapter(record, window, image, 'color', site, spectra[site].label + ' · color flow'));
      rows.push(
        chapter(
          record,
          window,
          image,
          'doppler',
          site,
          spectra[site].label + ' · ' + spectra[site].mode,
          {
            mitral: 'E 79 / A 54 cm/s',
            tricuspid: 'E 57 / A 38 cm/s',
            lvot: 'Peak 1.02 m/s',
            aortic: 'Peak 1.31 m/s · mean gradient 3.7 mmHg',
            pulmonary: 'Peak 0.96 m/s',
            tr: 'TR peak 2.20 m/s · RV–RA gradient 19 mmHg',
          }[site],
        ),
      );
    }
    return rows;
  }
  const poor = record.kind === 'limited',
    cw = poor ? 'limited-cw' : 'as-windows';
  const rows = [
    chapter(record, 'psax-av', 'valve-opening'),
    chapter(record, 'plax', 'valve-opening', 'section', null, 'Parasternal long axis · restricted valve'),
  ];
  if (!poor)
    rows.push(
      chapter(record, 'plax', 'lvot-gate', 'diameter', null, 'LVOT inner-edge diameter', '21 mm, mid systole'),
      chapter(
        record,
        'a5c',
        'lvot-gate',
        'doppler',
        'lvot',
        'Pulsed-wave sample proximal to valve',
        'LVOT VTI ' + integral(lvotPW).vti.toFixed(1) + ' cm',
      ),
    );
  rows.push(
    chapter(
      record,
      'a5c',
      cw,
      'doppler',
      'aortic',
      'Apical continuous-wave acquisition',
      poor ? 'Envelope incomplete' : 'Peak 3.59 m/s',
    ),
    chapter(
      record,
      'right-parasternal',
      cw,
      'doppler',
      'aortic',
      'Right parasternal ' + (poor ? 'repeat' : 'continuous-wave acquisition'),
      poor
        ? 'Peak and gradient withheld'
        : 'Peak 4.54 m/s · mean gradient ' +
            integral(flowCase).meanGradient.toFixed(0) +
            ' mmHg · valve VTI ' +
            integral(flowCase).vti.toFixed(1) +
            ' cm',
    ),
  );
  return rows;
}
const vector = (a, b) => a.map((v, i) => v - b[i]);
const mean = (ring) => ring.reduce((s, p) => s.map((v, i) => v + p[i] / ring.length), [0, 0, 0]);
function resizeVessel(tube, diameter) {
  const lumen = tube.lumen[0],
    wall = tube.wall[0];
  for (let i = 0; i < lumen.length; i++) {
    const center = mean(lumen[i]),
      radius = Math.hypot(...vector(lumen[i][0], center));
    for (const [ring, target] of [
      [lumen[i], diameter / 2],
      [wall[i], diameter / 2 + 1.4],
    ]) {
      const radiusBefore = ring === lumen[i] ? radius : Math.hypot(...vector(ring[0], center));
      ring.forEach((p, j) => {
        ring[j] = p.map((v, k) => center[k] + ((v - center[k]) * target) / radiusBefore);
      });
    }
  }
}
let previous, latest, echo;
export function sample(c, n, r) {
  const key = [r.id, c.id, n].join('/');
  if (key === previous) return latest;
  const t = n / (c.frames - 1),
    phase = c.mode === 'doppler' ? (2 * t) % 1 : (n % 20) / 20;
  const settings = c.view === 'right-parasternal' ? alternate : CARDIAC_VIEWS[c.view];
  const settling = Math.max(0, 1 - n / 10);
  const frame = heartFrame(phase);
  if (r.kind !== 'normal') {
    frame.details = frame.details
      .filter((d) => d.name !== 'AV')
      .concat(
        outletValves({ ...frame.motion, aorticOpen: frame.motion.aorticOpen * 0.22 }).filter(
          (d) => d.name === 'AV',
        ),
      );
    // Ventricle outflow geometry is generated for this phase. The modeled
    // orthogonal inner diameter used for continuity is 21 mm.
    resizeVessel(frame.vessels.LVOT, 21);
  }
  if (c.view === 'subcostal-ivc') {
    // Static atlas vessels are shared across frames. Clone the IVC before
    // applying this visit's respiratory cycle.
    frame.vessels.IVC = structuredClone(frame.vessels.IVC);
    resizeVessel(frame.vessels.IVC, 12 + 5 * Math.cos((n * Math.PI) / 10));
  }
  const diameterSite = c.mode === 'diameter' ? 'LVOT' : c.view === 'subcostal-ivc' ? 'IVC' : null;
  const tube = diameterSite ? frame.vessels[diameterSite].lumen[0] : null;
  const aim = tube
    ? mean(tube[Math.floor(tube.length * (diameterSite === 'IVC' ? 0.5 : 0.78))])
    : c.mode === 'doppler'
      ? sampleSites[c.signal]
      : settings.target;
  const plane = directedPlane(12 * settling + 2 * Math.sin(Math.PI * 2 * t) * settling, c.view, {
    ...settings,
    target: aim.map((v, i) => v + settling * [9, -2, 5][i]),
  });
  const cut = heartSection(frame, plane);
  previous = key;
  latest = { frame, plane, cut, phase, settling };
  return latest;
}
function text(ctx, x, y, s, color = '#e1efec', font = 15) {
  ctx.font = font + 'px system-ui';
  ctx.fillStyle = color;
  ctx.fillText(s, x, y);
}
function line(ctx, points, color, width = 1) {
  if (!points.length) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.moveTo(...points[0]);
  for (const p of points.slice(1)) ctx.lineTo(...p);
  ctx.stroke();
}
function transform(plane, w, h) {
  const { scale, tip, center } = bmodeCalibration(plane);
  const fit = Math.min(w / BMODE_RASTER.width, h / BMODE_RASTER.height);
  const dx = (w - BMODE_RASTER.width * fit) / 2,
    dy = (h - BMODE_RASTER.height * fit) / 2;
  return { dx, dy, fit, point: ([u, v]) => [dx + fit * (center + scale * u), dy + fit * (tip + scale * v)] };
}
function convexHull(points) {
  const sorted = points.toSorted((a, b) => a[0] - b[0] || a[1] - b[1]);
  const side = (list) => {
    const result = [];
    for (const p of list) {
      while (result.length > 1) {
        const a = result.at(-2),
          b = result.at(-1);
        if ((b[0] - a[0]) * (p[1] - a[1]) > (b[1] - a[1]) * (p[0] - a[0])) break;
        result.pop();
      }
      result.push(p);
    }
    return result.slice(0, -1);
  };
  return side(sorted).concat(side(sorted.reverse()));
}
function overlayColor(ctx, s, map) {
  const flow = axialFlow(s.frame, s.plane, s.phase),
    w = BMODE_RASTER.width / 2;
  for (let i = 0; i < flow.length; i++) {
    const v = flow[i];
    if (Math.abs(v) < 5) continue;
    ctx.fillStyle = v > 0 ? 'rgba(227,83,49,.78)' : 'rgba(68,142,220,.78)';
    ctx.fillRect(
      map.dx + map.fit * 2 * (i % w),
      map.dy + map.fit * 2 * Math.floor(i / w),
      map.fit * 2 + 0.2,
      map.fit * 2 + 0.2,
    );
  }
}
function drawWave(ctx, c, n, r) {
  const abnormal = r.kind !== 'normal',
    incomplete = r.kind === 'limited';
  let sig = spectra[c.signal];
  if (abnormal) sig = c.signal === 'lvot' ? lvotPW : c.view === 'right-parasternal' ? flowCase : apical;
  const range =
    abnormal && c.signal === 'aortic'
      ? 500
      : Math.ceil(Math.max(...sig.knots.map((k) => Math.abs(k[1]))) / 50) * 50;
  const left = 420,
    base = 310,
    width = 346,
    height = 150;
  for (const f of [0, 0.5, 1]) {
    const y = base - f * height;
    line(
      ctx,
      [
        [left, y],
        [left + width, y],
      ],
      '#374c54',
    );
    text(ctx, left - 31, y + 4, ((range * f) / 100).toFixed(1), '#d7e4e0', 12);
  }
  text(ctx, left, 114, 'Spectral velocity magnitude (m/s)');
  text(ctx, left, 346, '0');
  text(ctx, left + width - 39, 346, (2 * BEAT_SECONDS).toFixed(2) + ' s');
  let pts = [];
  const total = 320,
    limit = Math.floor((n / (c.frames - 1)) * total);
  for (let i = 0; i <= limit; i++) {
    const t = (i / total) * 2,
      phase = t % 1;
    if (incomplete && phase > 0.13 && phase < 0.3) {
      line(ctx, pts, '#ecba71', 2.5);
      pts = [];
      continue;
    }
    // The first trace is captured while steering onto the jet. The second
    // beat has a stable aligned sample and supports the recorded values.
    const acquisitionFrame = (i / total) * (c.frames - 1);
    const gain = 1 - 0.42 * Math.max(0, 1 - acquisitionFrame / 10);
    const v = Math.abs(velocity(sig, phase)) * gain;
    pts.push([left + (width * i) / total, base - (height * v) / range]);
  }
  line(ctx, pts, incomplete ? '#ecba71' : '#78ddd4', 2.5);
  text(
    ctx,
    left,
    77,
    c.signal === 'lvot' ? 'PW · LVOT' : spectra[c.signal].mode + ' · ' + spectra[c.signal].label,
    '#e8bd77',
    17,
  );
  if (incomplete) text(ctx, left, 382, 'Peak envelope lost during ejection', '#edc283');
}
export function render(ctx, c, n, r, { overlay = false } = {}) {
  const s = sample(c, n, r),
    doppler = c.mode === 'doppler',
    w = doppler ? 378 : 800,
    h = 410;
  echo ??= createEchoRenderer();
  const labels = echo(ctx, w, h, s.plane, s.cut, s.frame.motion, overlay);
  const map = transform(s.plane, w, h);
  if (c.mode === 'color') {
    overlayColor(ctx, s, map);
    text(ctx, 14, 35, 'Color Doppler · toward + / away −');
  }
  if (overlay) {
    const { scale, tip, center } = bmodeCalibration(s.plane);
    ctx.save();
    ctx.translate(map.dx + map.fit * center, map.dy + map.fit * tip);
    ctx.scale(map.fit * scale, map.fit * scale);
    ctx.clip(sectorPath(s.plane, 5));
    for (const { name, points } of s.cut.valveCuts) {
      const color = name === 'AV' ? '#ffc063' : '#c9dc9d';
      line(ctx, points, color, 1.8);
      if (!labels.some((item) => item.label === name + ' leaflets'))
        labels.push({ label: name + ' leaflets', color });
    }
    ctx.restore();
  }
  if (
    r.kind === 'normal' &&
    ['a4c', 'a2c', 'rv-focused'].includes(c.view) &&
    c.mode === 'section' &&
    [0, 0.35].includes(s.phase)
  ) {
    const chamber = c.view === 'rv-focused' ? 'RV' : 'LV';
    const contours = s.cut.chambers[chamber].lumen;
    for (const ring of contours) {
      const points = ring.map(map.point);
      line(ctx, points.concat([points[0]]), '#e2b960', 2);
    }
    text(ctx, 14, 28, (s.phase === 0 ? 'End diastole' : 'End systole') + ' · ' + chamber + ' endocardium');
  }
  if (doppler) {
    const aim = map.point(s.plane.section(sampleSites[c.signal]));
    line(ctx, [map.point([0, 0]), aim], '#a8cbca', 1);
    if (spectra[c.signal].mode === 'PW')
      line(
        ctx,
        [
          [aim[0] - 8, aim[1] - 2],
          [aim[0] + 8, aim[1] - 2],
        ],
        '#ffcf7d',
        3,
      );
    else line(ctx, [aim, map.point([0, s.plane.depth * 0.95])], '#d9bc84', 1);
    drawWave(ctx, c, n, r);
  }
  if (c.mode === 'diameter' || c.view === 'subcostal-ivc') {
    const vessel = c.mode === 'diameter' ? 'LVOT' : 'IVC';
    const tube = s.frame.vessels[vessel].lumen[0];
    const ring = tube[c.mode === 'diameter' ? Math.floor(tube.length * 0.78) : Math.floor(tube.length / 2)];
    // Project the physical cross-section chord perpendicular to its tube axis.
    const hits = [];
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i],
        b = ring[(i + 1) % ring.length],
        da = s.plane.distance(a),
        db = s.plane.distance(b);
      if (da > 0 !== db > 0)
        hits.push(map.point(s.plane.section(a.map((v, k) => v + ((b[k] - v) * da) / (da - db)))));
    }
    if (hits.length >= 2) {
      line(ctx, hits, '#ffd185', 2);
      for (const [x, y] of hits)
        line(
          ctx,
          [
            [x - 3, y - 4],
            [x + 3, y + 4],
          ],
          '#ffd185',
          2,
        );
    }
  }
  if (c.view === 'subcostal-4c') {
    const points = ['LV', 'RV', 'LA', 'RA'].flatMap((k) => s.cut.chambers[k].wall.flat());
    const hull = convexHull(points);
    if (hull.length) {
      const center = hull.reduce((a, p) => [a[0] + p[0] / hull.length, a[1] + p[1] / hull.length], [0, 0]);
      const edge = hull.map((p) => map.point(p.map((v, i) => center[i] + 1.018 * (v - center[i]))));
      line(ctx, edge.concat([edge[0]]), '#b9cbc6', 1.4);
    }
  }
  const caption =
    c.view === 'subcostal-ivc'
      ? `Respiratory IVC model · ${(12 + 5 * Math.cos((n * Math.PI) / 10)).toFixed(1)} mm`
      : c.view === 'right-parasternal'
        ? 'CW only · anatomy inset illustrates the beam path'
        : `Cardiac cycle · ${Math.round(s.phase * 100)}%`;
  text(ctx, 18, 431, caption, '#d3e1da', 15);
  return labels;
}
export function pose(ctx, c, n, r, { yaw = 0 } = {}) {
  const { frame, plane, cut } = sample(c, n, r);
  renderScene(ctx, 400, 300, frame, plane, cut, false, 28 + (yaw * 180) / Math.PI, -13);
  text(ctx, 12, 22, 'Probe and cardiac section', '#dae4df', 14);
  text(
    ctx,
    12,
    286,
    c.view === 'right-parasternal' ? 'Right parasternal CW' : CARDIAC_VIEWS[c.view].label,
    '#dcf0e6',
    14,
  );
}
