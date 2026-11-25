import { beamGain, integral, spectralResults, velocity } from './calculations.js';
import { BEAT_SECONDS, spectra } from './protocol.js';

const W = 760,
  H = 224,
  X = 68,
  X1 = 735,
  TOP = 23,
  BOTTOM = 188;
const text = (g, s, x, y, color = '#c8d8d5') => {
  g.fillStyle = color;
  g.fillText(s, x, y);
};
function plotBase(canvas) {
  const g = canvas.getContext('2d');
  g.fillStyle = '#0e1a20';
  g.fillRect(0, 0, W, H);
  g.font = '13px system-ui';
  g.lineWidth = 1;
  return g;
}
function line(g, x0, y0, x1, y1, color) {
  g.beginPath();
  g.moveTo(x0, y0);
  g.lineTo(x1, y1);
  g.strokeStyle = color;
  g.stroke();
}
function axis(g, lo, hi, unit) {
  const y = (v) => BOTTOM - ((v - lo) / (hi - lo)) * (BOTTOM - TOP);
  const ticks =
    hi > Math.abs(lo) * 2 ? [0, hi / 2, hi] : Math.abs(lo) > hi * 2 ? [lo, lo / 2, 0] : [lo, 0, hi];
  for (const value of ticks) {
    const ypos = y(value);
    line(g, X, ypos, X1, ypos, '#3c5159');
    text(g, Number(value.toFixed(1)).toString(), 9, ypos + 4);
  }
  line(g, X, y(0), X1, y(0), '#a8beb9');
  text(g, unit, 8, 13);
  for (const [p, label] of [
    [0, '0'],
    [0.25, '245'],
    [0.5, '490'],
    [0.75, '735'],
    [1, '980 ms'],
  ]) {
    const x = X + (X1 - X) * p;
    line(g, x, BOTTOM, x, BOTTOM + 4, '#879a98');
    text(g, label, x - (p === 1 ? 37 : 4), H - 12);
  }
  return y;
}
function spectrum(canvas, signal, gain) {
  const g = plotBase(canvas);
  const unipolar = [
    'outflow',
    'semilunar',
    'aortic',
    'lvot',
    'tr',
    'arch',
    'inflow',
    'regurgitation',
    'diastolic-jet',
  ].includes(signal.type);
  const positive = ['inflow', 'diastolic-jet'].includes(signal.type);
  const lo = unipolar && positive ? -signal.range * 0.12 : -signal.range;
  const hi = unipolar && !positive ? signal.range * 0.12 : signal.range;
  const y = axis(g, lo, hi, 'cm/s');
  const points = [];
  for (let i = 0; i <= 480; i++) {
    const p = i / 480;
    points.push([X + p * (X1 - X), y(velocity(signal, p) * gain)]);
  }
  // Traces are prescribed waveform envelopes, with no manufactured diagnostic texture.
  g.beginPath();
  g.moveTo(X, y(0));
  for (const [x, v] of points) g.lineTo(x, v);
  g.lineTo(X1, y(0));
  g.closePath();
  g.fillStyle = 'rgba(137,216,198,.29)';
  g.fill();
  g.beginPath();
  for (const [i, [x, v]] of points.entries()) {
    if (i) g.lineTo(x, v);
    else g.moveTo(x, v);
  }
  g.strokeStyle = '#a7ead8';
  g.lineWidth = 2;
  g.stroke();
}
export function signalPanel(host, id, context) {
  const s = spectra[id];
  host.innerHTML = `<p class="mw-guide"></p>
    <div class="mw-chart"><canvas width="760" height="224"></canvas><span class="mw-cursor" aria-hidden="true"></span></div>
    <div class="mw-actions"><button type="button" class="mw-peak">Go to peak</button><span class="mw-source"></span><output class="mw-at-cursor"></output></div>
    <output class="mw-values"></output><details class="mw-interval"><summary>Trace calipers</summary><p>Place the beat cursor at each boundary or enter times in milliseconds. Integration follows the displayed envelope.</p><div class="mw-actions">
      <label>Start <input type="number" min="0" max="980" step="1" aria-label="Trace start in milliseconds" data-start></label><button type="button" data-set-start>Mark start</button>
      <label>End <input type="number" min="0" max="980" step="1" aria-label="Trace end in milliseconds" data-end></label><button type="button" data-set-end>Mark end</button>
      </div><output class="mw-interval-result"></output></details><details class="mw-adjust"><summary>Sampling settings</summary><div class="mw-settings"></div></details><p class="mw-explain"></p>`;
  host.querySelector('.mw-guide').textContent = s.site;
  const chart = host.querySelector('canvas'),
    cursor = host.querySelector('.mw-cursor'),
    values = host.querySelector('.mw-values');
  chart.setAttribute(
    'aria-label',
    'Illustrative ' + s.label + ' spectral envelope, velocity over one 980 ms beat',
  );
  let angle = 0,
    offset = 0;
  const peakPhase = s.knots.reduce((best, p) => (Math.abs(p[1]) > Math.abs(best[1]) ? p : best))[0];
  host.querySelector('.mw-peak').onclick = () => context.onSeek(peakPhase);
  chart.onclick = (e) => {
    const r = chart.getBoundingClientRect();
    context.onSeek(Math.min(1, Math.max(0, (((e.clientX - r.left) / r.width) * W - X) / (X1 - X))));
  };
  const settings = host.querySelector('.mw-settings');
  function control(label, min, max, step, value, unit, onChange) {
    const wrap = document.createElement('label'),
      input = document.createElement('input'),
      read = document.createElement('span');
    wrap.append(label + ' ', input, read);
    input.type = 'range';
    input.min = min;
    input.max = max;
    input.step = step;
    input.value = value;
    read.textContent = value + unit;
    input.setAttribute('aria-label', label);
    input.oninput = () => {
      read.textContent = input.value + unit;
      onChange(Number(input.value));
      paint();
    };
    settings.append(wrap);
    return wrap;
  }
  control('Beam–flow angle', 0, 90, 1, angle, '°', (v) => (angle = v));
  if (s.mode !== 'CW') control('Gate offset', -8, 8, 0.5, offset, ' mm', (v) => (offset = v));
  if (s.type === 'aortic' || s.type === 'lvot')
    control('LVOT diameter', 0.8, 3.5, 0.01, context.diameter, ' cm', (v) => (context.diameter = v));
  if (s.type === 'tr')
    control('Assumed RA pressure', 1, 20, 1, context.rap, ' mmHg', (v) => (context.rap = v));
  const description = host.querySelector('.mw-explain');
  const interval = host.querySelector('.mw-interval'),
    start = interval.querySelector('[data-start]'),
    end = interval.querySelector('[data-end]');
  const intervalOutput = interval.querySelector('output'),
    atCursor = host.querySelector('.mw-at-cursor');
  const durationMs = BEAT_SECONDS * 1000;
  start.value = Math.round(s.knots[0][0] * durationMs);
  end.value = Math.round(s.knots.at(-1)[0] * durationMs);
  function measureInterval() {
    const from = start.valueAsNumber,
      to = end.valueAsNumber;
    const gain = beamGain(s.mode, angle, offset);
    if (!gain) {
      intervalOutput.textContent = 'No sampled signal';
      return;
    }
    if (!Number.isFinite(from + to) || from < 0 || to > durationMs || from >= to) {
      intervalOutput.textContent = 'Choose an end after the start within this beat.';
      return;
    }
    const { vti, meanGradient } = integral(s, gain, from / durationMs, to / durationMs);
    intervalOutput.textContent =
      to -
      from +
      ' ms · ' +
      (s.mode === 'TDI' ? 'Integrated tissue speed ' : 'Absolute VTI ') +
      vti.toFixed(2) +
      ' cm';
    if (s.mode === 'CW') intervalOutput.textContent += ' · Mean ΔP ' + meanGradient.toFixed(1) + ' mmHg';
  }
  start.oninput = end.oninput = measureInterval;
  interval.querySelector('[data-set-start]').onclick = () => {
    start.value = Math.round(context.state.phase * durationMs);
    measureInterval();
  };
  interval.querySelector('[data-set-end]').onclick = () => {
    end.value = Math.round(context.state.phase * durationMs);
    measureInterval();
  };

  function paint() {
    const gain = beamGain(s.mode, angle, offset);
    host.querySelector('.mw-source').textContent = s.mode + ' · prescribed velocity envelope';
    spectrum(chart, s, gain);
    const items = spectralResults(id, gain, context.diameter, context.rap);
    values.replaceChildren(
      ...items.map((item) => {
        const span = document.createElement('span');
        span.textContent = item;
        return span;
      }),
    );
    let note =
      s.mode === 'CW'
        ? 'CW collects velocities along the full beam. The source depth is unresolved.'
        : s.mode === 'TDI'
          ? 'Tissue Doppler follows annular motion.'
          : 'PW samples a finite region. Offsetting the gate beyond its target loses the signal.';
    if (id === 'septal' || id === 'lateral')
      note +=
        ' E / mean e′ pairs this site with the other annular site and mitral E at nominal alignment. This single ratio cannot assign a diastolic grade.';
    if (id === 'aortic')
      note +=
        ' Continuity uses the nominal LVOT PW VTI and the selected LVOT diameter. Mean gradient averages 4v² over ejection.';
    if (id === 'lvot')
      note += ' Stroke volume uses circular LVOT area × VTI. Output uses the model beat interval.';
    if (id === 'tr')
      note +=
        ' The modeled RVSP adds the assumed RA pressure to 4v². Interpretation as pulmonary artery systolic pressure requires absence of RV outflow obstruction.';
    description.textContent = note;
    measureInterval();
    update(context.state);
  }
  function update({ phase }) {
    const v = velocity(s, phase) * beamGain(s.mode, angle, offset);
    atCursor.textContent = Math.round(phase * durationMs) + ' ms · ' + v.toFixed(1) + ' cm/s';
    cursor.style.left = ((X + (X1 - X) * phase) / W) * 100 + '%';
  }
  paint();
  update(context.state);
  return update;
}
