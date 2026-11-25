import {
  distalICA, getAcquisition, getDopplerSample, getTube, measure, plaquePeak, sacPeak, split, stations, tubesAt,
} from './playable-model.js';

const ink = '#e7f0f4';
const muted = '#abc0ca';
const marker = '#f4c66b';

function addChapter(list, record, id, plate, title, start, key, end, config) {
  const view = record.views.find(item => item.image === `${record.id}-${plate}.svg`);
  if (!view) throw new Error(`Missing vascular plate ${record.id}/${plate}`);
  const chapter = {
    id, title, viewImage: view.image, frames: 29, evidenceFrame: 14,
    start, key, end, side: null, mode: 'short', observation: view.caption, ...config,
  };
  const dimensions = measure(record, chapter, chapter.evidenceFrame);
  const sample = getDopplerSample(record, chapter, chapter.evidenceFrame);
  if (dimensions.length) {
    const format = ({hi, lo, transverse}) => {
      const suffix = transverse ? ' transverse' : chapter.caliper === 'lumen' ? ' residual AP lumen' : ' AP';
      return `${Number((hi - lo).toFixed(1))} mm${suffix}`;
    };
    chapter.measurement = dimensions.map(format).join(' × ');
  } else if (sample) {
    chapter.measurement = `${sample.psv.toFixed(0)} / ${sample.edv.toFixed(0)} cm/s PSV / EDV · ${sample.angle.toFixed(0)}°`;
  }
  list.push(chapter);
}

function aorticChapters(record) {
  const list = [];
  const add = (...args) => addChapter(list, record, ...args);
  const positive = record.kind === 'abnormal';
  const limited = record.kind === 'limited';
  const stationsPlate = limited ? 'visible' : 'stations';
  const diameter = {target: 'Aorta', caliper: 'ap'};
  add('proximal-aorta', stationsPlate, 'Proximal suprarenal aorta', 0, 3, 31, {
    ...diameter, observation: 'The suprarenal aortic walls are visible. The outer-wall AP span is measured anterior to the vertebral body.',
  });
  add('mid-aorta', stationsPlate, positive ? 'Proximal infrarenal reference' : 'Mid aorta at the renal level',
    31, positive ? 55 : 60, 77, diameter);
  if (positive) {
    add('sac-maximum', 'sac', 'Sweep the aneurysm in transverse', 77, sacPeak, 132, {
      ...diameter, caliper: 'both', mode: 'short', showThrombus: true,
    });
  }
  if (limited) {
    add('anterior-distal-attempt', 'anterior', 'Attempt the distal aorta from anterior', 77, 139, split + 2, {
      ...diameter, blind: 'distal-aorta',
    });
    add('lateral-distal-repeat', 'retry', 'Repeat from the left lateral window', 88, 147, split + 5, {
      ...diameter, blind: 'distal-aorta', window: 'lateral',
    });
    return list;
  }
  add('distal-aorta', stationsPlate, positive ? 'Distal neck below the sac' : 'Distal infrarenal aorta',
    positive ? 132 : 77, positive ? 145 : 142, 156, diameter);
  add('iliac-bifurcation', 'split', 'Follow the aorta through its bifurcation', 156, split + 8, 194, {
    observation: 'One lumen separates into two as the scan continues past the aortic bifurcation.',
  });
  if (positive) add('sac-long-axis', 'long', 'Diagnostic long axis through the sac', 84, sacPeak, 128, {
    ...diameter, mode: 'long', color: true, showThrombus: true,
  });
  for (const side of ['Right', 'Left']) {
    const target = `${side} common iliac`;
    add(`${side.toLowerCase()}-iliac-short`, 'split', `${target} · transverse`, 188, 197, 212, {
      target, caliper: 'ap', observation: 'Measure the proximal common iliac outer wall to outer wall.',
    });
    if (positive) add(`${side.toLowerCase()}-iliac-long`, 'iliacs', `${target} · longitudinal`, 184, 198, 213, {
      target, caliper: 'ap', mode: 'long', color: true,
    });
  }
  return list;
}

function carotidChapters(record) {
  const list = [];
  const add = (...args) => addChapter(list, record, ...args);
  for (const side of ['Right', 'Left']) {
    const tag = side.toLowerCase();
    const rightPlaque = side === 'Right' && record.kind === 'abnormal';
    const leftLimited = side === 'Left' && record.kind === 'limited';
    const blind = leftLimited ? 'high-ica' : undefined;
    add(`${tag}-transverse`, `${tag}-short`, `${side} · transverse CCA to ICA and ECA`, 20, rightPlaque ? plaquePeak : 67, 103, {
      side, target: rightPlaque ? 'ICA' : null, caliper: rightPlaque ? 'lumen' : null,
      observation: rightPlaque ? 'Sweep through the bifurcation into eccentric proximal ICA plaque and measure the residual AP lumen.' :
        'Track the common carotid continuously into the internal and external branches.',
    });
    if (rightPlaque) add('right-distal-lumen', 'right-short', 'Right · unaffected distal ICA lumen', 104, distalICA, 127, {
      side, target: 'ICA', caliper: 'lumen', observation: 'The unaffected distal ICA provides the reference lumen for the paired short-axis plaque estimate.',
    });
    for (const [id, title, target, start, key, end] of [
      ['cca-gray', 'CCA long-axis grayscale', 'CCA', 26, 40, 52],
      ['bifurcation-gray', 'bifurcation long-axis grayscale', 'ICA', 57, 64, 72],
      ['ica-gray', 'ICA long-axis grayscale', 'ICA', 72, 80, 101],
    ]) {
      add(`${tag}-${id}`, `${tag}-gray`, `${side} · ${title}`, start, key, end,
        {side, target, mode: 'long', blind});
    }
    add(`${tag}-color`, `${tag}-color`, `${side} · long-axis color Doppler`, 45, 77, 120, {
      side, target: 'ICA', mode: 'long', color: true, blind,
      observation: rightPlaque ? 'The flow channel narrows at the plaque. Color aliasing and downstream disturbance localize the pulsed-wave gate.' :
        'Color fill confirms detectable flow where each cervical window is visible.',
    });
    for (const [id, station] of Object.entries(stations).slice(0, 6)) {
      if (rightPlaque && id === 'proximal-ica') {
        for (const focused of ['before', 'jet', 'beyond']) {
          const {label, z, vessel} = stations[focused];
          add(`right-${focused}`, 'right-triplet', `Right · ${label} · PW Doppler`, z - 4, z, z + 4, {
            side, target: vessel, mode: 'pw', color: true,
            observation: focused === 'jet' ? 'At the narrowed lumen, the centered gate records maximum acceleration.' :
              focused === 'before' ? 'Measure the waveform upstream of the plaque before flow accelerates.' :
                'Sample the broadened waveform in the post-stenotic segment.',
          });
        }
        continue;
      }
      const {label, z, vessel} = station;
      add(`${tag}-${id}`, `${tag}-spectra`, `${side} · ${label} · PW Doppler`, z - 4, z, z + 4, {
        side, target: vessel, mode: 'pw', color: true, blind,
        observation: leftLimited && id === 'distal-ica' ? 'The mandible obscures the distal ICA. No reproducible waveform or velocity is saved.' :
          `Center the pulsed-wave gate in the ${label}. The saved trace records its angle, PSV and EDV.`,
      });
    }
    if (leftLimited) add('left-distal-ica-retry', 'retry', 'Left distal ICA · posterolateral repeat', 111, distalICA, 126, {
      side, target: 'ICA', mode: 'pw', window: 'posterolateral', blind: 'high-ica',
      observation: 'Reposition the probe posterolaterally. Residual mandibular shadow prevents reliable distal ICA sampling.',
    });
  }
  return list;
}

export function chapters(record) {
  return record.family === 'aaa' ? aorticChapters(record) : carotidChapters(record);
}

function line(ctx, x1, y1, x2, y2, color, width = 1) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

function text(ctx, value, x, y, size = 15, color = ink) {
  ctx.fillStyle = color;
  ctx.font = `${size}px system-ui, sans-serif`;
  ctx.fillText(value, x, y);
}

function cross(ctx, x, y) {
  line(ctx, x - 5, y, x + 5, y, marker, 2);
  line(ctx, x, y - 5, x, y + 5, marker, 2);
}

function planeSlope(record, chapter, acquisition) {
  if (!acquisition.long || !chapter.target) return 0;
  const {z, target} = acquisition;
  const previous = getTube(record, chapter.side, z - 2, chapter.target);
  const next = getTube(record, chapter.side, z + 2, chapter.target);
  return previous && next && target ? (next.x - previous.x) / 4 : 0;
}

// The image axes are orthogonal unit vectors in the same millimetre coordinates as the vessels.
function planeAxes(acq, slope) {
  const sine = Math.sin(acq.angle);
  const cosine = Math.cos(acq.angle);
  const normalizer = Math.hypot(slope, 1);
  const xFactor = acq.long ? slope / normalizer : 1;
  return {
    horizontal: {x: xFactor * cosine, y: -xFactor * sine, z: acq.long ? 1 / normalizer : 0},
    depth: {x: sine, y: cosine, z: 0},
  };
}

function samplePoint(acquisition, offset, depth, slope) {
  const axes = planeAxes(acquisition, slope);
  return {
    z: acquisition.z + offset * axes.horizontal.z,
    x: acquisition.anchorX + offset * axes.horizontal.x + depth * axes.depth.x,
    y: offset * axes.horizontal.y + depth * axes.depth.y,
  };
}

function scanViewport(record, chapter, acq) {
  const bounds = chapter.mode === 'pw'
    ? {x: 26, y: 67, w: 476, h: 306}
    : {x: 36, y: 65, w: 716, h: 324};
  const pxPerMm = Math.min(bounds.w / acq.width, bounds.h / acq.depth);
  // The raster pads subpixel edges to full 2x2 cells. Projection still uses one physical scale.
  const w = Math.ceil(pxPerMm * acq.width / 2) * 2;
  const h = Math.ceil(pxPerMm * acq.depth / 2) * 2;
  const x = bounds.x + Math.floor((bounds.w - w) / 2);
  const y = bounds.y + Math.floor((bounds.h - h) / 2);
  return {x, y, w, h, centerX: x + w / 2, pxPerMm, axes: planeAxes(acq, planeSlope(record, chapter, acq))};
}

function project(acq, rect, z, x, y) {
  const dx = x - acq.anchorX;
  const dz = z - acq.z;
  const {horizontal, depth} = rect.axes;
  const offsetMm = dx * horizontal.x + y * horizontal.y + dz * horizontal.z;
  const depthMm = dx * depth.x + y * depth.y;
  return [rect.centerX + offsetMm * rect.pxPerMm, rect.y + depthMm * rect.pxPerMm];
}

function elliptical(x, y, cx, cy, rx, ry) {
  return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2;
}

export function classifyTissue(x, y, tubes) {
  let region = 'tissue';
  let vessel;
  for (const candidate of tubes) {
    if (Math.abs(x - candidate.x) > candidate.rx || Math.abs(y - candidate.y) > candidate.ry) continue;
    const outer = elliptical(x, y, candidate.x, candidate.y, candidate.rx, candidate.ry);
    if (outer > 1) continue;
    if (elliptical(x, y, candidate.lx, candidate.ly, candidate.lrx, candidate.lry) <= 1) {
      return {region: 'lumen', vessel: candidate};
    }
    if (!candidate.mural || outer > (1 - candidate.wall / Math.max(candidate.rx, candidate.ry)) ** 2) region = 'wall';
    else if (region !== 'wall') region = 'mural';
    vessel = candidate;
  }
  return {region, vessel};
}

const overlayPalette = {
  'Aortic wall': [245, 175, 94],
  'Aortic lumen': [65, 210, 192],
  'Residual lumen': [65, 210, 192],
  'Mural thrombus': [208, 126, 224],
  'Carotid plaque': [233, 162, 93],
  'Right common iliac': [116, 199, 244],
  'Left common iliac': [158, 217, 132],
  'CCA': [120, 205, 242],
  'ICA': [73, 220, 183],
  'ECA': [234, 181, 118],
  'VA': [204, 153, 240],
  'IVC': [129, 167, 228],
  'IJV': [129, 167, 228],
  'Vertebral body': [226, 212, 121],
};

function echoLayer(record, chapter, acq, {x, y, z}, depth, vessels) {
  const seed = Math.imul(Math.floor(x * 3.8), 0x9e3779b1) ^
    Math.imul(Math.floor(y * 4.5), 0x85ebca77) ^ Math.imul(Math.floor(z * 3.7), 0xc2b2ae3d);
  const grain = (Math.imul(seed ^ (seed >>> 14), 0x27d4eb2f) >>> 24) / 128 - 1;
  const texture = grain * 17 + Math.sin(y * 2.3 + x * .9) * 6;
  const abdomen = record.family === 'aaa';
  const shadowX = acq.angle ? 27 : 0;
  const gasSurface = 25 + 2.3 * Math.cos((x - shadowX) * .5 + z * .11);
  if (acq.blind && abdomen && Math.abs(x - (acq.angle ? 16 : 0)) < 35 && y > gasSurface) {
    const echo = y < gasSurface + 2.2 || (y < gasSurface + 11 && Math.cos(y * 1.5) > .78);
    return {rgb: [echo ? 145 + texture : 17 + texture * .4]};
  }
  if (chapter.blind === 'high-ica' && z >= 108 && Math.abs(x - 5) < 6.7 && y > 13) {
    return {rgb: [y < 14.4 ? 219 + texture : 9 + texture * .21]};
  }
  const {region, vessel} = classifyTissue(x, y, vessels);
  if (vessel) {
    const label = region === 'mural' ? vessel.mural :
      vessel.name !== 'Aorta' ? vessel.name : region === 'wall' ? 'Aortic wall' :
        vessel.mural ? 'Residual lumen' : 'Aortic lumen';
    return {label, rgb: vesselEcho(record, chapter, x, y, z, depth, vessel, region, grain, texture)};
  }
  if (abdomen && Math.abs(x) < 20 && y > 65 + x * x * .013) {
    return y < 67 + x * x * .013 ? {label: 'Vertebral body', rgb: [209 + texture]} : {rgb: [14 + texture * .42]};
  }
  if (depth < 4) return {rgb: [102 + texture * 1.7]};
  return {rgb: [Math.max(12, 72 - depth * .71 + texture * 1.6 + 12 * Math.sin(y * .62 + x * .14))]};
}

function vesselEcho(record, chapter, x, y, z, depth, vessel, region, grain, texture) {
  const abdomen = record.family === 'aaa';
  if (region === 'lumen') {
    if (chapter.color && vessel.color === 1) {
      const disturbance = !abdomen && record.kind === 'abnormal' && chapter.side === 'Right'
        && vessel.name === 'ICA' && z >= 73 && z <= 99;
      const pulse = Math.sin(z * .55 + depth * .24) * 18 + grain * 19;
      if (disturbance && Math.sin(z * .83 + depth * 1.6) > .2) return [57, 103 + pulse, 204 + pulse];
      if (disturbance) return [232 + pulse, 109 + pulse, 32];
      return [166 + pulse, 63 + pulse, 45];
    }
    return [7 + texture * .13];
  }
  if (region === 'wall') return [171 + texture * 2];
  return [90 + texture * 1.8];
}

function byte(value) {
  return Math.max(0, Math.min(255, value)) | 0;
}

function drawScan(ctx, record, chapter, acq, rect, overlay) {
  // Compute each sampled strip once and enlarge each acoustic sample to a 2x2 pixel cell.
  const image = ctx.createImageData(rect.w, rect.h);
  const pixels = new Uint32Array(image.data.buffer);
  const {horizontal, depth: depthAxis} = rect.axes;
  const visibleLabels = new Set();
  for (let col = 0; col < rect.w; col += 2) {
    const offset = (rect.x + col + 1 - rect.centerX) / rect.pxPerMm;
    const z = acq.z + offset * horizontal.z;
    const startX = acq.anchorX + offset * horizontal.x;
    const startY = offset * horizontal.y;
    const vessels = tubesAt(record, chapter.side, z);
    for (let row = 0; row < rect.h; row += 2) {
      const depth = (row + 1) / rect.pxPerMm;
      const point = {x: startX + depth * depthAxis.x, y: startY + depth * depthAxis.y, z};
      const {label, rgb} = echoLayer(record, chapter, acq, point, depth, vessels);
      let [red, green = red, blue = red] = rgb;
      if (overlay && label) {
        const [r, g, b] = overlayPalette[label];
        visibleLabels.add(label);
        red = red * .44 + r * .56;
        green = green * .44 + g * .56;
        blue = blue * .44 + b * .56;
      }
      const rgba = 0xff000000 | (byte(blue) << 16) | (byte(green) << 8) | byte(red);
      const i = row * rect.w + col;
      pixels[i] = rgba;
      pixels[i + 1] = rgba;
      pixels[i + rect.w] = rgba;
      pixels[i + rect.w + 1] = rgba;
    }
  }
  ctx.putImageData(image, rect.x, rect.y);
  return Object.entries(overlayPalette).filter(([label]) => visibleLabels.has(label))
    .map(([label, rgb]) => ({label, color: `rgb(${rgb.join(', ')})`}));
}

function drawCalipers(ctx, dimensions, acq, rect) {
  for (const dimension of dimensions) {
    const {z, x, y, lo, hi, transverse} = dimension;
    const a = project(acq, rect, z, transverse ? lo : x, transverse ? y : lo);
    const b = project(acq, rect, z, transverse ? hi : x, transverse ? y : hi);
    line(ctx, ...a, ...b, marker, 1.4);
    cross(ctx, ...a);
    cross(ctx, ...b);
    const value = Number((hi - lo).toFixed(1));
    const lx = transverse ? b[0] + 9 : a[0] + 9;
    const ly = transverse ? b[1] + 5 : a[1] - 7;
    ctx.fillStyle = '#191713';
    ctx.fillRect(lx - 3, ly - 15, 68, 19);
    text(ctx, `${value} mm`, lx, ly, 14, marker);
  }
}

function traceVelocity(phase, sample) {
  const peakPhase = .14;
  const fraction = phase < peakPhase ? Math.sin(phase / peakPhase * Math.PI / 2) :
    Math.exp(-4.5 * (phase - peakPhase)) * (1 - phase) / (1 - peakPhase);
  return sample.edv + (sample.psv - sample.edv) * fraction;
}

function spectrum(ctx, sample, frame) {
  const left = 566;
  const right = 775;
  const top = 132;
  const baseline = 339;
  line(ctx, left, baseline, right, baseline, '#8094a0');
  line(ctx, left, top, left, baseline, '#8094a0');
  text(ctx, 'PW spectral Doppler', left - 10, 83, 16);
  text(ctx, 'cm/s', left - 10, 105, 13, muted);
  for (const tick of [0, 50, 100, 150, 200, 250]) {
    const y = baseline - tick / 250 * (baseline - top);
    text(ctx, String(tick), left - (tick >= 100 ? 31 : 22), y + 4, 12, muted);
    line(ctx, left, y, right, y, '#30444d');
  }
  if (!sample) {
    text(ctx, 'No usable spectral envelope', left + 8, 208, 13, marker);
    text(ctx, 'Velocity withheld', left + 8, 230, 13, muted);
    return;
  }
  const time = (frame % 13) / 26;
  for (const band of [1, .96, .9, sample.disturbed ? .67 : .84]) {
    ctx.beginPath();
    ctx.strokeStyle = band === 1 ? '#b1ece0' : '#6d9a8d';
    ctx.lineWidth = band === 1 ? 1.8 : .75;
    // Include the exact sampled peak in each visible beat, independent of the display grid.
    const fractions = Array.from({length: 211}, (_, i) => i / 210);
    for (let beat = 0; beat <= 2; beat++) {
      const p = (beat + .14 - time) / 2;
      if (p >= 0 && p <= 1) fractions.push(p);
    }
    fractions.sort((a, b) => a - b);
    fractions.forEach((t, i) => {
      const phase = (t * 2 + time) % 1;
      const velocity = traceVelocity(phase, sample) * band;
      const point = [left + (right - left) * t, baseline - velocity / 250 * (baseline - top)];
      if (i === 0) ctx.moveTo(...point);
      else ctx.lineTo(...point);
    });
    ctx.stroke();
  }
  text(ctx, `PSV ${sample.psv.toFixed(0)}   EDV ${sample.edv.toFixed(0)} cm/s`, left - 10, 373, 14, marker);
  text(ctx, `Angle correction ${sample.angle.toFixed(0)}°`, left - 10, 399, 14, muted);
}

function drawGate(ctx, sample, acq, rect) {
  if (!acq.gate || acq.blind) return;
  const [x, y] = project(acq, rect, acq.z, acq.gate.x, acq.gate.y);
  const angle = (sample?.angle ?? 58) * Math.PI / 180;
  const side = 19 * Math.cos(angle);
  const rise = 19 * Math.sin(angle);
  line(ctx, x - side, y - rise, x + side, y + rise, marker, 1.5);
  line(ctx, x - 12, y, x + 12, y, '#f2f7f8', 1.25);
  line(ctx, x - 5, y + 3, x, y - 5, marker, 2);
  line(ctx, x + 2, y + 7, x + 7, y - 1, marker, 2);
}

function anatomyLabels(ctx, record, chapter, acq, rect) {
  if (acq.blind) {
    text(ctx, record.family === 'aaa' ? 'Distal wall obscured by bowel gas' : 'Mandibular shadow obscures distal ICA',
      rect.x + 16, rect.y + rect.h - 15, 15, marker);
    return;
  }
  if (chapter.showThrombus && acq.target && acq.target.ry - acq.target.lry > 3) {
    const {x, y, ry} = acq.target;
    const [px, py] = project(acq, rect, acq.z, x, y + ry * .79);
    const labelY = Math.min(py + 25, rect.y + rect.h - 12);
    line(ctx, px - 11, py, px - 48, labelY - 5, ink);
    ctx.fillStyle = '#131a21';
    ctx.fillRect(px - 168, labelY - 16, 122, 20);
    text(ctx, 'Mural thrombus', px - 162, labelY - 1, 14);
  }
  const vessels = tubesAt(record, chapter.side, acq.z);
  const explained = chapter.target ? vessels.filter(v => v.name === chapter.target) :
    vessels.filter(v => !['VA', 'IVC', 'IJV'].includes(v.name));
  const targetX = chapter.target && acq.target ? acq.target.lx : 0;
  for (const vessel of explained) {
    const [x, y] = project(acq, rect, acq.z, vessel.x, vessel.y);
    const labelOffset = Math.min(14, rect.w - (x - rect.x) - 84);
    if (!chapter.caliper && chapter.mode !== 'pw') {
      text(ctx, vessel.name, x + labelOffset, y + 6 + 12 * Math.sign(vessel.x - targetX), 13);
    }
  }
}

export function render(ctx, chapter, frame, record, {overlay = false} = {}) {
  const acq = getAcquisition(record, chapter, frame);
  const pw = chapter.mode === 'pw';
  const rect = scanViewport(record, chapter, acq);
  ctx.fillStyle = '#101820';
  ctx.fillRect(0, 0, 800, 440);
  const modality = pw ? 'MODELED COLOR AND PW DOPPLER' : chapter.color ?
    'MODELED COLOR DOPPLER' : 'MODELED GRAYSCALE';
  text(ctx, overlay ? `${modality} + TISSUE OVERLAY` : modality, rect.x, 26, 13, muted);
  text(ctx, acq.long ? (record.family === 'aaa' ? 'Cranial ←       → Caudal' : 'Proximal ←       → Distal')
    : 'Patient right ←       → Patient left', rect.x, 49, 15);
  const legend = drawScan(ctx, record, chapter, acq, rect, overlay);
  for (let depth = 0; depth <= acq.depth; depth += 10) {
    const y = rect.y + depth * rect.pxPerMm;
    line(ctx, rect.x + rect.w - 6, y, rect.x + rect.w + 1, y, '#dbe4e9');
    text(ctx, String(depth), rect.x + rect.w + 4, y + 4, 11, muted);
  }
  if (chapter.color && !overlay) {
    const x = rect.x + rect.w - 124;
    ctx.fillStyle = '#a83f2d';
    ctx.fillRect(x, rect.y - 25, 11, 12);
    text(ctx, record.family === 'aaa' ? 'Patent channel' : 'Modeled flow', x + 15, rect.y - 14, 12, muted);
  }
  const sample = pw ? getDopplerSample(record, chapter, frame, acq) : null;
  if (pw) {
    drawGate(ctx, sample, acq, rect);
    spectrum(ctx, sample, frame);
  }
  anatomyLabels(ctx, record, chapter, acq, rect);
  drawCalipers(ctx, measure(record, chapter, frame, acq), acq, rect);
  const status = acq.blind ? 'Limited window · measurement withheld' :
    pw && !sample ? 'Gate outside the flow channel · continue centering' :
      frame === chapter.evidenceFrame ? 'Saved evidence frame' : 'Sweep in progress';
  text(ctx, status, rect.x, 417, 15, frame === chapter.evidenceFrame ? marker : muted);
  text(ctx, 'Depth in mm', rect.x + rect.w - 79, 417, 13, muted);
  return legend;
}

function locatorTransform(record, yaw) {
  const abdomen = record.family === 'aaa';
  const length = abdomen ? 218 : 128;
  const scale = abdomen ? 1 : 1.47;
  const centerDepth = abdomen ? 40 : 21;
  const sine = Math.sin(yaw);
  const cosine = Math.cos(yaw);
  return {
    length,
    project3d(x, y, z) {
      const rotatedX = x * cosine - (y - centerDepth) * sine;
      const rotatedDepth = x * sine + (y - centerDepth) * cosine;
      return [82 + z / length * 231 + rotatedX * scale * .48,
        128 + (rotatedDepth + centerDepth) * 1.34 - rotatedX * scale];
    },
  };
}

function sectionRing(ctx, vessel, z, project3d) {
  const loop = (x, y, rx, ry) => {
    for (let i = 0; i <= 32; i++) {
      const theta = i / 32 * Math.PI * 2;
      const point = project3d(x + rx * Math.cos(theta), y + ry * Math.sin(theta), z);
      if (i === 0) ctx.moveTo(...point);
      else ctx.lineTo(...point);
    }
    ctx.closePath();
  };
  ctx.beginPath();
  loop(vessel.x, vessel.y, vessel.rx, vessel.ry);
  loop(vessel.lx, vessel.ly, vessel.lrx, vessel.lry);
  ctx.fillStyle = vessel.mural === 'Mural thrombus' ? '#bc71cfb0' :
    vessel.mural ? '#e9a25db0' : '#df9585a0';
  ctx.fill('evenodd');
  ctx.strokeStyle = vessel.name === 'Aorta' ? '#f5af5e' : '#b3e3df';
  ctx.lineWidth = 1.3;
  ctx.stroke();
  ctx.beginPath();
  loop(vessel.lx, vessel.ly, vessel.lrx, vessel.lry);
  ctx.strokeStyle = '#64d2c0';
  ctx.lineWidth = 1.2;
  ctx.stroke();
}

function longCutaway(ctx, record, chapter, acq, slope, project3d) {
  const target = chapter.target;
  if (!target) return;
  for (const inner of [false, true]) {
    const color = inner ? '#68d9c4' : '#efac78';
    const lines = [null, null];
    for (let u = -acq.width / 2; u <= acq.width / 2; u += 1) {
      const {x, z} = samplePoint(acq, u, 0, slope);
      const at = getTube(record, chapter.side, z, target);
      const dx = at && (x - (inner ? at.lx : at.x)) / (inner ? at.lrx : at.rx);
      if (!at || Math.abs(dx) >= 1 || (chapter.blind === 'high-ica' && z >= 108)) {
        lines.fill(null);
        continue;
      }
      const radius = (inner ? at.lry : at.ry) * Math.sqrt(1 - dx * dx);
      const depth = inner ? at.ly : at.y;
      for (const [i, sign] of [-1, 1].entries()) {
        const next = project3d(x, depth + sign * radius, z);
        if (lines[i]) line(ctx, ...lines[i], ...next, color, inner ? 1.25 : 1.75);
        lines[i] = next;
      }
    }
  }
}

export function pose(ctx, chapter, frame, record, {yaw = 0} = {}) {
  const acq = getAcquisition(record, chapter, frame);
  const {length, project3d} = locatorTransform(record, yaw);
  const abdomen = record.family === 'aaa';
  const names = abdomen ? ['IVC', 'Aorta', 'Right common iliac', 'Left common iliac'] : ['IJV', 'VA', 'CCA', 'ECA', 'ICA'];
  ctx.fillStyle = '#152129';
  ctx.fillRect(0, 0, 400, 300);
  text(ctx, 'PROBE AND IMAGING PLANE', 21, 27, 13, muted);
  text(ctx, abdomen ? 'Cranial → Caudal' : `${chapter.side} neck · proximal → distal`, 21, 51);
  const slope = planeSlope(record, chapter, acq);
  const half = acq.width / 2;
  const field = [[-half, 0], [half, 0], [half, acq.depth], [-half, acq.depth]].map(([u, v]) => {
    const point = samplePoint(acq, u, v, slope);
    return project3d(point.x, point.y, point.z);
  });
  ctx.save();
  ctx.beginPath();
  ctx.rect(17, 65, 366, 183);
  ctx.clip();
  line(ctx, ...project3d(0, 0, 0), ...project3d(0, 0, length), '#4e606a');
  text(ctx, abdomen ? 'Abdominal surface' : 'Neck surface', 87, 118, 11, muted);
  for (const name of names) {
    let previous;
    for (let z = 0; z <= length; z += 1.5) {
      const vessel = getTube(record, chapter.side, z, name);
      if (!vessel) {
        previous = undefined;
        continue;
      }
      const at = project3d(vessel.x, vessel.y, z);
      const color = vessel.color === -1 ? '#4a7590' : name === chapter.target ? '#d28b84' : '#a95861';
      if (previous) line(ctx, ...previous, ...at, color, Math.min(38, vessel.ry * (abdomen ? 1.55 : 2.8)));
      previous = at;
    }
  }
  ctx.fillStyle = '#438d8c47';
  ctx.strokeStyle = '#6fd1c8';
  ctx.lineWidth = 1.6;
  ctx.beginPath();
  field.forEach((point, i) => i === 0 ? ctx.moveTo(...point) : ctx.lineTo(...point));
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  if (!acq.blind && acq.long) longCutaway(ctx, record, chapter, acq, slope, project3d);
  if (!acq.blind && !acq.long) {
    const tubes = tubesAt(record, chapter.side, acq.z);
    for (const vessel of tubes) {
      if (Math.abs(vessel.x - acq.anchorX) <= half + vessel.rx) sectionRing(ctx, vessel, acq.z, project3d);
    }
  }
  const probe = [-9, 9].map(u => {
    const point = samplePoint(acq, u, 0, slope);
    return project3d(point.x, point.y, point.z);
  });
  ctx.lineCap = 'round';
  line(ctx, ...probe[0], ...probe[1], '#efbc68', 8);
  ctx.lineCap = 'butt';
  if (acq.gate && !acq.blind) cross(ctx, ...project3d(acq.gate.x, acq.gate.y, acq.z));
  ctx.restore();
  text(ctx, 'Probe', 22, 269, 14, marker);
  text(ctx, acq.long ? 'Long axis' : 'Transverse plane', 95, 269, 14, '#6fd1c8');
  text(ctx, chapter.window === 'lateral' ? 'Left lateral window' : chapter.window === 'posterolateral' ?
    'Posterolateral neck window' : chapter.target ?? (abdomen ? 'Aorta and branches' : 'Carotid bifurcation'), 22, 290, 13, muted);
}
