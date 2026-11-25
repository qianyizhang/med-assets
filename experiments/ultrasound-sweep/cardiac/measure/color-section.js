import { BMODE_RASTER, bmodeCalibration } from '../heart-poses.js';
import { heartFrame, heartSection, probePlane } from '../heart-geometry.js';
import { aliased, velocity } from './calculations.js';
import { spectra } from './protocol.js';

// Prescribed forward flow along the centers of existing lumen rings. The
// sampling radius is kept inside the ring. Systole and filling are independent
// positive speeds along different 3D paths; the probe determines display sign.
function stream(rings, speed) {
  const points = [];
  for (let i = 0; i < rings.length; i += 2) {
    const ring = rings[i];
    const center = [0, 0, 0];
    for (const p of ring) for (let j = 0; j < 3; j++) center[j] += p[j] / ring.length;
    let radius = Infinity;
    for (const p of ring)
      radius = Math.min(radius, Math.hypot(p[0] - center[0], p[1] - center[1], p[2] - center[2]));
    points.push({ center, radius: radius * 0.8 });
  }
  return { points, speed };
}
function streamSet(frame, phase) {
  const result = [];
  for (const [v, a, id] of [
    ['LV', 'LA', 'mitral'],
    ['RV', 'RA', 'tricuspid'],
  ]) {
    const opening = v === 'LV' ? frame.motion.mitralOpen : frame.motion.tricuspidOpen;
    const speed = opening > 0.01 ? velocity(spectra[id], phase) : 0;
    if (speed < 2) continue;
    const av = frame.chambers[a].lumen,
      vt = frame.chambers[v].lumen;
    // Moving annular ring is shared. Sample only the inlet portion of each chamber.
    result.push(
      stream(
        av
          .slice(0, Math.ceil(av.length * 0.55))
          .reverse()
          .concat(vt.slice(Math.floor(vt.length * 0.4), -1).reverse()),
        speed,
      ),
    );
  }
  for (const [names, id] of [
    [['LVOT', 'Ao', 'Arch', 'DescAo', 'Arch branches'], 'lvot'],
    [['RVOT', 'PA', 'RPA'], 'rvot'],
  ]) {
    const opening = id === 'lvot' ? frame.motion.aorticOpen : frame.motion.pulmonaryOpen;
    const speed = opening > 0.01 ? Math.abs(velocity(spectra[id], phase)) : 0;
    if (speed < 2) continue;
    for (const name of names)
      for (const tube of frame.vessels[name]?.lumen || []) result.push(stream(tube, speed));
  }
  // Systemic venous return has a systolic and diastolic forward component
  // and a small atrial reversal. IVC geometry runs upstream to the RA.
  const venous = -velocity(spectra.hepatic, phase);
  for (const tube of frame.vessels.IVC?.lumen || []) result.push(stream(tube, venous));
  for (const tube of frame.vessels.SVC?.lumen || []) result.push(stream(tube, -venous));
  return result;
}
const WIDTH = BMODE_RASTER.width / 2,
  HEIGHT = BMODE_RASTER.height / 2;
// The color field samples the exact B-mode calibration at half raster resolution.
function colorCalibration(plane) {
  const { scale, tip, center } = bmodeCalibration(plane);
  return { scale: scale / 2, tip: tip / 2, center: center / 2 };
}
export function axialFlow(frame, plane, phase) {
  const grid = new Float32Array(WIDTH * HEIGHT);
  const { scale, tip, center } = colorCalibration(plane);
  for (const { points, speed } of streamSet(frame, phase)) {
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1],
        b = points[i],
        radius = Math.max(a.radius, b.radius);
      const ad = plane.distance(a.center),
        bd = plane.distance(b.center);
      if ((ad > radius && bd > radius) || (ad < -radius && bd < -radius)) continue;
      const [au, av] = plane.section(a.center),
        [bu, bv] = plane.section(b.center);
      const du = bu - au,
        dv = bv - av,
        dn = bd - ad,
        length2 = du * du + dv * dv + dn * dn;
      if (length2 < 1e-6) continue;
      const length = Math.sqrt(length2);
      const x0 = Math.max(0, Math.floor(center + (Math.min(au, bu) - radius) * scale)),
        x1 = Math.min(WIDTH - 1, Math.ceil(center + (Math.max(au, bu) + radius) * scale));
      const y0 = Math.max(0, Math.floor(tip + (Math.min(av, bv) - radius) * scale)),
        y1 = Math.min(HEIGHT - 1, Math.ceil(tip + (Math.max(av, bv) + radius) * scale));
      for (let py = y0; py <= y1; py++)
        for (let px = x0; px <= x1; px++) {
          const u = (px + 0.5 - center) / scale,
            v = (py + 0.5 - tip) / scale,
            range = Math.hypot(u, v);
          if (v <= 0 || Math.abs(Math.atan2(u, v)) > plane.halfAngle || range > plane.depth) continue;
          const projection = ((u - au) * du + (v - av) * dv - ad * dn) / length2;
          if ((projection < 0 && i === 1) || (projection > 1 && i === points.length - 1)) continue;
          // Round the internal joins so changing tangent does not punch seams in the flow field.
          const t = Math.min(1, Math.max(0, projection));
          const r = a.radius + (b.radius - a.radius) * t;
          const d2 = (u - au - du * t) ** 2 + (v - av - dv * t) ** 2 + (ad + dn * t) ** 2;
          if (d2 >= r * r) continue;
          const value = ((-speed * (du * u + dv * v)) / (length * range)) * (1 - d2 / (r * r));
          const k = px + py * WIDTH;
          if (Math.abs(value) > Math.abs(grid[k])) grid[k] = value;
        }
    }
  }
  return grid;
}

export function colorPanel(host, context) {
  host.innerHTML = `<p class="mw-guide">Find forward inflow and ejection in this plane. Rotation changes the beam-parallel component.</p>
    <canvas class="mw-plot mw-color" width="594" height="360" aria-label="Model B-mode section with geometry-registered directional color flow"></canvas>
    <div class="mw-actions"><button type="button" data-fill>Early inflow</button><button type="button" data-eject>Peak ejection</button>
    <label class="mw-slider">Velocity scale <input type="range" min="15" max="120" step="5" value="55" aria-label="Color Nyquist limit"><output>±55 cm/s</output></label></div>
    <p class="mw-explain">The color box samples prescribed flow inside modeled lumens. Red is toward the probe and blue is away. Beyond the scale, colors wrap. Perpendicular flow can produce little color.</p>`;
  const canvas = host.querySelector('canvas'),
    g = canvas.getContext('2d');
  const off = document.createElement('canvas');
  off.width = WIDTH;
  off.height = HEIGHT;
  const og = off.getContext('2d'),
    image = og.createImageData(WIDTH, HEIGHT);
  const slider = host.querySelector('input'),
    out = host.querySelector('output');
  const mask = document.createElement('canvas');
  mask.width = WIDTH;
  mask.height = HEIGHT;
  const maskInk = mask.getContext('2d');
  function clipToBlood(slice, plane) {
    maskInk.setTransform(1, 0, 0, 1, 0, 0);
    maskInk.clearRect(0, 0, WIDTH, HEIGHT);
    const { scale, tip, center } = colorCalibration(plane);
    maskInk.setTransform(scale, 0, 0, scale, center, tip);
    function fillPath(poly) {
      if (!poly.length) return;
      maskInk.beginPath();
      maskInk.moveTo(...poly[0]);
      for (const p of poly.slice(1)) maskInk.lineTo(...p);
      maskInk.closePath();
      maskInk.fill();
    }
    for (const part of Object.values(slice.chambers)) for (const poly of part.lumen) fillPath(poly);
    maskInk.globalCompositeOperation = 'destination-out';
    for (const poly of slice.muscleCuts) fillPath(poly);
    maskInk.globalCompositeOperation = 'source-over';
    og.globalCompositeOperation = 'destination-in';
    og.drawImage(mask, 0, 0);
    og.globalCompositeOperation = 'source-over';
  }
  let key = '';
  function update(state) {
    const phase = state.phase;
    // Sample at 25 ms or on a pose change. Snapshot the current grayscale and
    // color together so the underlying tissue cannot move beneath a held color frame.
    const bin = [Math.floor(phase * 40), state.viewId, state.tilt, state.overlay, slider.value].join('/');
    if (key === bin) return;
    key = bin;
    const plane = probePlane(state.tilt, state.viewId),
      source = context.section;
    const frame = heartFrame(phase);
    const flow = axialFlow(frame, plane, phase);
    const limit = Number(slider.value);
    image.data.fill(0);
    for (let i = 0; i < flow.length; i++) {
      const v = aliased(flow[i], limit),
        ratio = Math.min(1, Math.abs(v) / limit);
      if (Math.abs(flow[i]) < 2) continue;
      const k = i * 4;
      image.data[k] = v > 0 ? 110 + 145 * ratio : 16 + 58 * ratio;
      image.data[k + 1] = v > 0 ? 25 + 130 * ratio : 57 + 111 * ratio;
      image.data[k + 2] = v > 0 ? 28 + 35 * ratio : 135 + 115 * ratio;
      image.data[k + 3] = 218;
    }
    og.putImageData(image, 0, 0);
    clipToBlood(heartSection(frame, plane), plane);
    g.fillStyle = '#000';
    g.fillRect(0, 0, canvas.width, canvas.height);
    const fit = Math.min(source.width / BMODE_RASTER.width, source.height / BMODE_RASTER.height),
      sw = BMODE_RASTER.width * fit,
      sh = BMODE_RASTER.height * fit;
    const dw = BMODE_RASTER.width * 1.09,
      dh = BMODE_RASTER.height * 1.09,
      dx = (canvas.width - dw) / 2,
      dy = (canvas.height - dh) / 2;
    if (sw && sh)
      g.drawImage(source, (source.width - sw) / 2, (source.height - sh) / 2, sw, sh, dx, dy, dw, dh);
    g.drawImage(off, dx, dy, dw, dh);
    g.font = '13px system-ui';
    g.fillStyle = '#e8eeee';
    g.fillText('cm/s', 8, 24);
    g.fillStyle = '#f7b178';
    g.fillText('+' + limit, 8, 44);
    g.fillStyle = '#74b5ff';
    g.fillText('−' + limit, 8, 110);
    const grd = g.createLinearGradient(0, 49, 0, 97);
    for (const [n, c] of [
      [0, '#ff9b42'],
      [0.46, '#8e161e'],
      [0.5, '#16212b'],
      [0.54, '#10398b'],
      [1, '#78c6ff'],
    ])
      grd.addColorStop(n, c);
    g.fillStyle = grd;
    g.fillRect(10, 49, 12, 48);
  }
  slider.oninput = () => {
    out.textContent = '±' + slider.value + ' cm/s';
    update(context.state);
  };
  host.querySelector('[data-fill]').onclick = () => context.onSeek(0.51);
  host.querySelector('[data-eject]').onclick = () => context.onSeek(0.16);
  update(context.state);
  return update;
}
