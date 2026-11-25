import { heartFrame, probePlane } from '../heart-geometry.js';

const IDS = ['a4c', 'a2c', 'a3c'];
const LABELS = ['Four chamber', 'Two chamber', 'Three chamber'];
const HUES = ['#95dec8', '#e8bf84', '#96bbef'];
const dist = (p, q) => Math.hypot(...p.map((v, i) => v - q[i]));

// At ED, intersect each endocardial ring with a reference view. Store vertex
// identities and interpolation weights, then follow the same material through
// the beat. Re-intersecting the stationary plane would select different tissue.
function materialTracks(reference, id) {
  const plane = probePlane(0, id),
    tracks = [[], []];
  for (const [row, ring] of reference.entries()) {
    const hits = [];
    for (let i = 0; i < ring.length; i++) {
      const j = (i + 1) % ring.length,
        da = plane.distance(ring[i]),
        db = plane.distance(ring[j]);
      if (da > 0 === db > 0) continue;
      const weight = da / (da - db);
      const point = ring[i].map((v, k) => v + (ring[j][k] - v) * weight);
      hits.push({ row, i, j, weight, u: plane.section(point)[0] });
    }
    if (hits.length === 2) {
      hits.sort((a, b) => a.u - b.u);
      tracks[0].push(hits[0]);
      tracks[1].push(hits[1]);
    }
  }
  return tracks;
}
function lengths(track, rings) {
  const points = track.map(({ row, i, j, weight }) =>
    rings[row][i].map((v, k) => v + (rings[row][j][k] - v) * weight),
  );
  return points.slice(1).map((p, i) => dist(p, points[i]));
}
// Distribute each baseline edge over the apical, middle and basal thirds of
// the ED arc, retaining the same fractional edge ownership at later phases.
function segmentWeights(lengths) {
  const extent = lengths.reduce((a, b) => a + b, 0),
    bounds = [0, extent / 3, (2 * extent) / 3, extent];
  let start = 0;
  return lengths.map((len) => {
    const end = start + len,
      w = [0, 1, 2].map((k) =>
        len ? Math.max(0, Math.min(end, bounds[k + 1]) - Math.max(start, bounds[k])) / len : 0,
      );
    start = end;
    return w;
  });
}
function sums(lengths, weights) {
  const total = [0, 0, 0];
  lengths.forEach((v, i) => weights[i].forEach((w, j) => (total[j] += v * w)));
  return total;
}
export function longitudinalCurves(sampleCount = 60) {
  const base = heartFrame(0).chambers.LV.lumen;
  const tracks = IDS.map((id) =>
    materialTracks(base, id).map((track) => {
      const ref = lengths(track, base),
        weights = segmentWeights(ref);
      return { track, weights, initial: sums(ref, weights) };
    }),
  );
  const curves = [];
  for (let i = 0; i <= sampleCount; i++) {
    const rings = heartFrame(i / sampleCount).chambers.LV.lumen;
    const strain = tracks.map((sides) =>
      sides.flatMap(({ track, weights, initial }) => {
        const current = sums(lengths(track, rings), weights);
        return current.map((v, j) => (initial[j] ? 100 * (v / initial[j] - 1) : NaN));
      }),
    );
    curves.push(strain);
  }
  return curves;
}

let cached;
export function strainPanel(host, context) {
  cached ??= longitudinalCurves();
  host.innerHTML = `<p class="mw-guide">Track the same endocardial points in three apical planes. Negative strain indicates shortening relative to end diastole.</p>
  <div class="mw-chart"><canvas width="760" height="230" aria-label="Modeled longitudinal strain over time in three apical planes"></canvas><span class="mw-cursor" aria-hidden="true"></span></div>
  <output class="mw-values"></output><p class="mw-explain">The model follows six equal-length wall segments in each neutral plane. These endocardial geometry curves demonstrate the calculation. Clinical speckle tracking uses acquired images, tracking-quality review and a declared myocardial layer.</p>`;
  const g = host.querySelector('canvas').getContext('2d'),
    cursor = host.querySelector('.mw-cursor');
  const mean = (a) => a.reduce((s, n) => s + n, 0) / a.length;
  const low = Math.min(-25, Math.floor(Math.min(...cached.flat(2)) / 5) * 5);
  const y = (v) => 40 + (v / low) * 134;
  g.fillStyle = '#0e1a20';
  g.fillRect(0, 0, 760, 230);
  g.font = '13px system-ui';
  for (const tick of [0, low / 2, low]) {
    g.fillStyle = '#c5d7d5';
    g.fillText(tick + '%', 12, y(tick) + 5);
    g.strokeStyle = '#354b53';
    g.beginPath();
    g.moveTo(63, y(tick));
    g.lineTo(733, y(tick));
    g.stroke();
  }
  for (let j = 0; j < 3; j++) {
    g.strokeStyle = HUES[j];
    g.lineWidth = 2;
    g.beginPath();
    cached.forEach((frame, i) => {
      const x = 63 + (i / (cached.length - 1)) * 670;
      if (i) g.lineTo(x, y(mean(frame[j])));
      else g.moveTo(x, y(mean(frame[j])));
    });
    g.stroke();
    g.fillStyle = HUES[j];
    g.fillText(LABELS[j], 70 + j * 120, 22);
  }
  g.fillStyle = '#c5d7d5';
  g.fillText('ED', 61, 209);
  g.fillText('ES', 63 + 0.35 * 670, 209);
  g.fillText('980 ms', 688, 209);
  const es = cached[Math.round(0.35 * (cached.length - 1))];
  const out = host.querySelector('output');
  out.textContent = 'End-systolic model mean ' + mean(es.flat()).toFixed(1) + '%';
  const seek = (ev) => {
    const r = ev.target.getBoundingClientRect();
    context.onSeek(Math.max(0, Math.min(1, (((ev.clientX - r.left) / r.width) * 760 - 63) / 670)));
  };
  host.querySelector('canvas').onclick = seek;
  const update = ({ phase }) => {
    cursor.style.left = ((63 + phase * 670) / 760) * 100 + '%';
  };
  update(context.state);
  return update;
}
