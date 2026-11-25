import { BEAT_SECONDS, spectra } from './protocol.js';

export function velocity(signal, phase) {
  const { knots } = signal;
  if (phase < knots[0][0] || phase > knots.at(-1)[0]) return 0;
  const index = knots.findIndex((point) => point[0] >= phase);
  if (!index) return knots[0][1];
  const [t0, v0] = knots[index - 1];
  const [t1, v1] = knots[index];
  const t = (phase - t0) / (t1 - t0);
  // Smooth interpolation leaves the declared peaks at their specified times.
  return v0 + (v1 - v0) * t * t * (3 - 2 * t);
}

export function beamGain(mode, degrees, offset) {
  const cosine = Math.cos((degrees * Math.PI) / 180);
  if (cosine < 0.001) return 0;
  if (mode === 'CW') return cosine;
  // A transverse gate offset leaves the finite target. Targets represent blood or tissue.
  const halfWidth = mode === 'TDI' ? 4 : 6;
  return cosine * Math.max(0, 1 - (offset / halfWidth) ** 2);
}

export function aliased(v, limit) {
  if (Math.abs(v) <= limit) return v;
  return ((((v + limit) % (2 * limit)) + 2 * limit) % (2 * limit)) - limit;
}

export function integral(signal, gain = 1, start = signal.knots[0][0], end = signal.knots.at(-1)[0]) {
  let sum = 0,
    pressureSum = 0;
  const n = 300;
  if (start < 0 || end > 1 || !(end > start)) return { vti: NaN, meanGradient: NaN };
  for (let i = 0; i < n; i++) {
    const v = Math.abs(velocity(signal, start + ((end - start) * (i + 0.5)) / n)) * gain;
    sum += v;
    pressureSum += 4 * (v / 100) ** 2;
  }
  return { vti: (sum * BEAT_SECONDS * (end - start)) / n, meanGradient: pressureSum / n };
}

export const peakVelocity = (signal) => Math.max(...signal.knots.map(([, v]) => Math.abs(v)));
const fixed = (n, places = 1) => n.toFixed(places);
export function spectralResults(id, gain, diameterCm, rapMmHg) {
  const signal = spectra[id];
  if (!gain) return ['No sampled signal'];
  const peak = peakVelocity(signal) * gain;
  const { vti, meanGradient } = integral(signal, gain);
  const peakLabel = 'Peak ' + fixed(peak / 100, 2) + ' m/s';
  const vtiLabel = 'VTI ' + fixed(vti) + ' cm';
  switch (signal.type) {
    case 'inflow': {
      const e = velocity(signal, 0.51) * gain,
        a = velocity(signal, 0.91) * gain;
      return ['E ' + fixed(e, 0) + ' cm/s', 'A ' + fixed(a, 0) + ' cm/s', 'E/A ' + fixed(e / a, 2)];
    }
    case 'tissue': {
      const e = Math.abs(velocity(signal, 0.51)) * gain;
      const a = Math.abs(velocity(signal, 0.91)) * gain;
      const s = Math.max(...signal.knots.map(([, v]) => v)) * gain;
      const items = ['s′ ' + fixed(s) + ' cm/s', 'e′ ' + fixed(e) + ' cm/s', 'a′ ' + fixed(a) + ' cm/s'];
      if (id !== 'rvS') {
        const other = id === 'septal' ? spectra.lateral : spectra.septal;
        const avge = (e + Math.abs(velocity(other, 0.51))) / 2;
        items.push('E / mean e′ ' + fixed(velocity(spectra.mitral, 0.51) / avge));
      }
      return items;
    }
    case 'lvot': {
      const sv = Math.PI * (diameterCm / 2) ** 2 * vti;
      return [
        peakLabel,
        vtiLabel,
        'Stroke volume ' + fixed(sv, 0) + ' mL',
        'Cardiac output ' + fixed((sv * 60) / BEAT_SECONDS / 1000) + ' L/min',
      ];
    }
    case 'aortic': {
      const ratio = integral(spectra.lvot).vti / vti;
      return [
        peakLabel,
        vtiLabel,
        'Peak / mean ΔP ' + fixed(4 * (peak / 100) ** 2) + ' / ' + fixed(meanGradient) + ' mmHg',
        'VTI ratio ' + fixed(ratio, 2),
        'Continuity area ' + fixed(Math.PI * (diameterCm / 2) ** 2 * ratio, 2) + ' cm²',
      ];
    }
    case 'semilunar':
      return [peakLabel, vtiLabel, 'Peak ΔP ' + fixed(4 * (peak / 100) ** 2) + ' mmHg'];
    case 'tr':
      return [
        peakLabel,
        'RV–RA ΔP ' + fixed(4 * (peak / 100) ** 2) + ' mmHg',
        'RVSP estimate ' + fixed(4 * (peak / 100) ** 2 + rapMmHg) + ' mmHg',
      ];
    case 'venous':
      return [
        ['S', 0.04, 0.39],
        ['D', 0.43, 0.78],
        ['Ar', 0.82, 0.99],
      ].map(
        ([label, start, end]) =>
          label +
          ' ' +
          fixed(
            Math.max(...signal.knots.filter(([t]) => t >= start && t <= end).map(([, v]) => Math.abs(v))) *
              gain,
            0,
          ) +
          ' cm/s',
      );
    case 'diastolic-jet': {
      const last = Math.abs(signal.knots.at(-1)[1]) * gain;
      return [
        peakLabel,
        'End-diastolic velocity ' + fixed(last / 100, 2) + ' m/s',
        'End-diastolic ΔP ' + fixed(4 * (last / 100) ** 2) + ' mmHg',
      ];
    }
    case 'regurgitation':
      return [peakLabel, 'Peak ΔP ' + fixed(4 * (peak / 100) ** 2) + ' mmHg'];
    case 'arch':
      return [peakLabel];
    default:
      return [peakLabel, vtiLabel];
  }
}

export const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
export function polygonArea(poly) {
  return (
    Math.abs(
      poly.reduce((sum, [x, y], i) => {
        const next = poly[(i + 1) % poly.length];
        return sum + x * next[1] - y * next[0];
      }, 0),
    ) / 2
  );
}

// Reorient a measured cross-section about its annulus-to-tip axis. Measure each
// disk perpendicular to that axis by intersecting the polygon edges.
export function diskTrace(poly, base) {
  if (poly.length < 3) return null;
  const tip = poly.reduce((best, p) => (distance(p, base) > distance(best, base) ? p : best));
  const length = distance(base, tip);
  if (length < 1) return null;
  const ax = (tip[0] - base[0]) / length,
    ay = (tip[1] - base[1]) / length;
  const coords = poly.map(([x, y]) => [
    (x - base[0]) * ax + (y - base[1]) * ay,
    -(x - base[0]) * ay + (y - base[1]) * ax,
  ]);
  const widths = [],
    segments = [];
  function point(t, u) {
    return [base[0] + ax * t - ay * u, base[1] + ay * t + ax * u];
  }
  for (let i = 0; i < 20; i++) {
    const t = (length * (i + 0.5)) / 20;
    const cuts = [];
    for (let j = 0; j < coords.length; j++) {
      const [t0, u0] = coords[j],
        [t1, u1] = coords[(j + 1) % coords.length];
      if (t0 > t !== t1 > t) cuts.push(u0 + ((u1 - u0) * (t - t0)) / (t1 - t0));
    }
    if (cuts.length < 2) return null;
    const a = Math.min(...cuts),
      b = Math.max(...cuts);
    widths.push(b - a);
    segments.push([point(t, a), point(t, b)]);
  }
  return { poly, base, tip, widths, segments, length };
}
export function diskVolume(a, b) {
  if (!a || !b) return NaN;
  const sum = a.widths.reduce((total, width, i) => total + width * b.widths[i], 0);
  return ((Math.PI / 4) * sum * Math.max(a.length, b.length)) / (a.widths.length * 1000);
}
export const fractionalChange = (full, empty) => (full > 0 ? (100 * (full - empty)) / full : NaN);
