// Replay with Node 24+. The same ventricular lofts, acquisition planes, disk
// summation and Doppler integration also power the live adult echo study.
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { heartFrame, heartSection, probePlane } from '../../cardiac/heart-geometry.js';
import { chamberTrace } from '../../cardiac/measure/sections.js';
import {
  diskVolume,
  fractionalChange,
  integral,
  peakVelocity,
  polygonArea,
  velocity,
} from '../../cardiac/measure/calculations.js';
import { BEAT_SECONDS, spectra } from '../../cardiac/measure/protocol.js';

const out = resolve(process.argv[2] || dirname(fileURLToPath(import.meta.url)));
mkdirSync(out, { recursive: true });
const teal = '#72dbd0',
  gold = '#ffd38c',
  white = '#e8f1ef';
function label(x, y, text, size = 19, color = white) {
  return `<text x="${x}" y="${y}" font-family="sans-serif" font-size="${size}" fill="${color}">${text}</text>`;
}
function plate(name, heading, content) {
  const file = name + '.svg';
  writeFileSync(
    resolve(out, file),
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 390" role="img"><title>${heading}</title><rect width="800" height="390" fill="#101e24"/>${label(26, 38, heading, 23)}${content}</svg>\n`,
  );
  return file;
}
const coord = (n) => n.toFixed(1);
function path(points, close = false) {
  return 'M' + points.map((p) => p.map(coord).join(' ')).join('L') + (close ? 'Z' : '');
}
function shape(points, color, stroke, close = true, width = 1.4) {
  return `<path d="${path(points, close)}" fill="${color}" stroke="${stroke}" stroke-width="${width}"/>`;
}
function cut(view, phase, x, y, scale) {
  const section = heartSection(heartFrame(phase), probePlane(0, view));
  const point = ([u, v]) => [x + u * scale, y + v * scale];
  let result = '';
  const vessels = {
    a4c: [],
    a2c: [],
    'rv-focused': [],
    'subcostal-4c': ['IVC'],
    plax: ['LVOT', 'Ao'],
    'suprasternal-arch': ['Arch', 'Ao', 'DescAo'],
  };
  for (const name of ['LV', 'LA', 'RV', 'RA', ...vessels[view]]) {
    const organ = section.chambers[name];
    for (const line of organ.wall) result += shape(line.map(point), '#405658', '#72888a');
    for (const line of organ.lumen) result += shape(line.map(point), '#11262f', '#98b7b5');
  }
  for (const line of section.valveCuts) result += shape(line.points.map(point), 'none', gold, false, 2.5);
  for (const name of ['LV', 'LA', 'RV', 'RA']) {
    const polygon = section.chambers[name].lumen.toSorted((a, b) => polygonArea(b) - polygonArea(a))[0];
    if (!polygon || polygonArea(polygon) * scale ** 2 < 520) continue;
    const xs = polygon.map((p) => p[0]),
      ys = polygon.map((p) => p[1]);
    const [cx, cy] = point([(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2]);
    result += label(cx - 10, cy + 4, name, 14);
  }
  return result;
}
const biplane = (phase) => diskVolume(chamberTrace(phase, 'a4c', 'LV'), chamberTrace(phase, 'a2c', 'LV'));
const ed = biplane(0),
  es = biplane(0.35),
  ef = fractionalChange(ed, es);
const lviv = plate(
  'biplane',
  'Apical four chamber · one modeled beat',
  cut('a4c', 0, 207, 35, 2.1) +
    cut('a4c', 0.35, 578, 35, 2.1) +
    label(95, 362, 'End diastole') +
    label(508, 362, 'End systole'),
);
const axes = plate(
  'axes',
  'Orthogonal apical cuts · end diastole',
  cut('a4c', 0, 207, 35, 2.1) +
    cut('a2c', 0, 578, 35, 2.1) +
    label(95, 362, 'Four chamber') +
    label(508, 362, 'Two chamber'),
);
const right = plate(
  'right-heart',
  'Right heart · same scale at both phases',
  cut('rv-focused', 0, 200, 32, 2.15) +
    cut('rv-focused', 0.35, 580, 32, 2.15) +
    label(80, 365, 'RV-focused · end diastole') +
    label(459, 365, 'RV-focused · end systole'),
);
const fac = fractionalChange(...[0, 0.35].map((p) => polygonArea(chamberTrace(p, 'rv-focused', 'RV').poly)));
const atrium = diskVolume(chamberTrace(0.35, 'a4c', 'LA'), chamberTrace(0.35, 'a2c', 'LA'));
const ra = polygonArea(chamberTrace(0.35, 'a4c', 'RA').poly) / 100;

function wave(signal, x, y, w, h, max, seconds, missing = false) {
  // Display speed magnitude above baseline for ease of comparing windows.
  let svg = '';
  for (const frac of [0, 0.5, 1]) {
    const level = y - frac * h;
    svg +=
      shape(
        [
          [x, level],
          [x + w, level],
        ],
        'none',
        '#425960',
        false,
        1,
      ) + label(x - 37, level + 5, ((frac * max) / 100).toFixed(1), 13);
  }
  for (let i = 0; i <= 4; i++) svg += label(x + (w * i) / 4 - 6, y + 22, ((seconds * i) / 4).toFixed(2), 12);
  let pts = [];
  for (let i = 0; i <= 240; i++) {
    const t = (seconds * i) / 240 / BEAT_SECONDS;
    if (missing && t > 0.13 && t < 0.3) {
      if (pts.length) {
        svg += shape(pts, 'none', gold, false, 3);
        pts = [];
      }
      continue;
    }
    pts.push([x + (w * i) / 240, y - (h * Math.abs(velocity(signal, t))) / max]);
  }
  return svg + shape(pts, 'none', missing ? gold : teal, false, 3);
}
function tracePair(id, heading, a, b, max, seconds, missing = false) {
  return plate(
    id,
    heading,
    label(72, 87, a[0], 18) +
      label(466, 87, b[0], 18) +
      label(21, 135, 'm/s', 14) +
      wave(a[1], 62, 295, 285, 142, max, seconds, missing) +
      wave(b[1], 455, 295, 285, 142, max, seconds, missing) +
      label(364, 366, 'Time (s)', 17),
  );
}
import {flowCase, apical, lvotPW} from './playable-signals.js';
const normalJets = tracePair(
  'outflow',
  'Outflow · systolic velocity magnitude',
  ['LVOT · pulsed wave', spectra.lvot],
  ['Aortic valve · continuous wave', spectra.aortic],
  160,
  0.4,
);
const inflow = tracePair(
  'filling',
  'Diastolic filling · velocity magnitude',
  ['Mitral leaflet tips', spectra.mitral],
  ['Tricuspid leaflet tips', spectra.tricuspid],
  100,
  0.98,
);
const pulmonary = tracePair(
  'right-flow',
  'Right heart · spectral interrogation',
  ['Pulmonary outflow', spectra.pulmonary],
  ['Trace tricuspid regurgitation', spectra.tr],
  250,
  0.4,
);
const jet = integral(flowCase);
const asCW = tracePair(
  'as-windows',
  'Aortic jet · same beat, two windows',
  ['Apical five chamber', apical],
  ['Right parasternal · standalone CW', flowCase],
  500,
  0.45,
);
const loss = tracePair(
  'limited-cw',
  'Incomplete systolic envelopes',
  ['Apical attempt', apical],
  ['Parasternal reattempt', flowCase],
  500,
  0.45,
  true,
);

function valveCross(x, y, r, opening, thick) {
  let s = `<circle cx="${x}" cy="${y}" r="${r}" fill="#132d36" stroke="#92aeae" stroke-width="7"/>`;
  for (let i = 0; i < 3; i++) {
    const a = (i * 2 * Math.PI) / 3 - Math.PI / 2;
    const at = (angle, rad) => [x + Math.cos(angle) * rad, y + Math.sin(angle) * rad];
    const p = at(a, r),
      q = at(a + (2 * Math.PI) / 3, r),
      c = at(a + Math.PI / 3, r * (opening * 2 - 0.5));
    s += `<path d="M${p.map(coord)} Q${c.map(coord)} ${q.map(coord)}" fill="none" stroke="${thick ? gold : teal}" stroke-width="${thick ? 8 : 3}"/>`;
  }
  return s;
}
const valves = plate(
  'valve-opening',
  'Aortic short axis · cusp excursion',
  valveCross(219, 208, 91, 0.65, false) +
    valveCross(581, 208, 91, 0.2, true) +
    label(111, 350, 'Mobile reference cusps') +
    label(469, 350, 'Restricted systolic opening'),
);
const lvotSize = 2.1;
function calipers(x, y, diameter) {
  const half = diameter * 4.2;
  return (
    shape(
      [
        [x - half, y],
        [x + half, y],
      ],
      'none',
      gold,
      false,
      2,
    ) +
    shape(
      [
        [x - half, y - 8],
        [x - half, y + 8],
      ],
      'none',
      gold,
      false,
      3,
    ) +
    shape(
      [
        [x + half, y - 8],
        [x + half, y + 8],
      ],
      'none',
      gold,
      false,
      3,
    )
  );
}
const lvotPlate = plate(
  'lvot-gate',
  'LV outflow tract · matched diameter and PW sample',
  shape(
    [
      [75, 88],
      [135, 121],
      [154, 176],
      [149, 284],
      [126, 333],
    ],
    'none',
    '#91abae',
    false,
    8,
  ) +
    shape(
      [
        [345, 91],
        [310, 125],
        [330.4, 176],
        [325.4, 284],
        [360, 325],
      ],
      'none',
      '#91abae',
      false,
      8,
    ) +
    calipers(242.2, 176, 21) +
    label(212, 151, '21 mm', 16, gold) +
    label(102, 365, 'Mid-systolic inner edges', 16) +
    label(459, 97, 'PW just proximal to valve', 18) +
    wave(lvotPW, 455, 295, 285, 139, 120, 0.4) +
    label(480, 360, 'Time (s) · speed in m/s', 15),
);
const vti = integral(lvotPW).vti,
  ratio = vti / jet.vti,
  area = Math.PI * (lvotSize / 2) ** 2 * ratio;
function envelope(x, y, radius, gap = 0) {
  let result = '';
  for (const [d, col] of [
    [0, teal],
    [gap + 3, gold],
  ]) {
    const ps = Array.from({ length: 101 }, (_, i) => {
      const a = (2 * Math.PI * i) / 100;
      return [x + (radius + d) * Math.cos(a), y + (radius * 0.63 + d) * Math.sin(a)];
    });
    result += shape(ps, 'none', col, true, 2);
  }
  return result;
}
const greatVessels = plate(
  'great-vessels',
  'Parasternal and suprasternal windows',
  cut('plax', 0.18, 205, 34, 2.02) +
    cut('suprasternal-arch', 0.18, 570, 35, 1.95) +
    label(66, 359, 'LV outflow and aortic root', 17) +
    label(470, 359, 'Arch and descending aorta', 17),
);
const sac = plate(
  'pericardium',
  'Pericardial survey · worked subcostal view',
  cut('subcostal-4c', 0, 184, 19, 2.0) +
    label(39, 359, 'Subcostal chamber orientation', 17) +
    envelope(580, 211, 110) +
    label(440, 113, 'Parietal and visceral layers', 17) +
    label(458, 324, 'Apposed in this case', 18) +
    label(438, 363, 'Pericardial detail · schematic', 16, gold),
);
const cava = plate(
  'ivc',
  'IVC size and respiratory variation · longitudinal detail',
  [17, 7]
    .map((d, i) => {
      const x = 44 + i * 390,
        y = 200,
        s = d * 4.2;
      return (
        shape(
          [
            [x, y - s / 2],
            [x + 307, y - s / 2 - 5],
          ],
          'none',
          white,
          false,
          4,
        ) +
        shape(
          [
            [x, y + s / 2],
            [x + 307, y + s / 2 - 5],
          ],
          'none',
          white,
          false,
          4,
        ) +
        shape(
          [
            [x + 151, y - s / 2 - 2.5],
            [x + 151, y + s / 2 - 2.5],
          ],
          'none',
          gold,
          false,
          3,
        ) +
        label(x + 163, y + 10, d + ' mm', 19, gold) +
        label(x + 48, 324, i ? 'With inspiration' : 'At end expiration')
      );
    })
    .join(''),
);
const std = [
  {
    title: 'ASE comprehensive adult TTE acquisition protocol',
    url: 'https://www.asecho.org/guideline/comprehensive-tte-in-adults/',
  },
  { title: 'Robinson et al. · acquired examples by window, Table 1', url: 'https://doi.org/10.1530/ERP-20-0026' },
  {
    title: 'ASE standard adult echo report',
    url: 'https://www.asecho.org/guideline/guidelines-for-the-standardization-of-adult-echocardiography-reporting/',
  },
];
const asRef = {
  title:
    'Ring et al. · acquired multiwindow Doppler, Figure 5 E–F; compare the higher right parasternal envelope in a separate case',
  url: 'https://doi.org/10.1530/ERP-20-0035',
};
const view = (title, image, caption, measurement) => ({
  title,
  image,
  caption,
  ...(measurement ? { measurement } : {}),
});
const records = [
  {
    id: 'echo-normal',
    family: 'echo',
    kind: 'normal',
    title: 'A baseline adult echocardiogram',
    indication: 'Characterize chamber size, systolic function and valve flow in an adult with a soft murmur.',
    summary:
      'The paired apical sections come from one modeled heartbeat. The Doppler panels show the separately prescribed flow for this worked visit.',
    views: [
      view(
        'Left ventricular contraction',
        lviv,
        'The endocardium moves inward and the base moves toward the apex between these two frames. The paired two-chamber view supplies the second diameter for each volume disk.',
      ),
      view(
        'Biplane volumes and atrial size',
        axes,
        'Twenty pairs of disk widths across the apical four- and two-chamber contours yield the end-diastolic and end-systolic LV volumes. Atrial size is assessed at ventricular end systole.',
        `LV ${ed.toFixed(0)} → ${es.toFixed(0)} mL · EF ${ef.toFixed(0)}%. LA volume ${atrium.toFixed(0)} mL · RA area ${ra.toFixed(1)} cm².`,
      ),
      view(
        'Right ventricular function',
        right,
        'Trace the RV endocardial area in the same RV-focused plane at end diastole and end systole.',
        `RV fractional area change ${fac.toFixed(0)}%.`,
      ),
      view(
        'Mitral and tricuspid inflow',
        inflow,
        'The first peak is early diastolic filling. The smaller late peak accompanies atrial contraction. Separate septal and lateral annular samples in the echo study illustrate relaxation.',
        'Mitral E/A 79/54 cm/s · E/A ratio 1.46. Tricuspid E/A 57/38 cm/s.',
      ),
      view(
        'From root to arch',
        greatVessels,
        'Follow the outlet through the root in parasternal long axis. The suprasternal cut provides a second window on the arch and descending thoracic segment.',
      ),
      view(
        'Aortic outflow',
        normalJets,
        'Sample proximal outflow with PW and the valve jet with CW. Both traces have a complete systolic envelope.',
        'LVOT peak 1.02 m/s · aortic peak 1.31 m/s · mean aortic gradient 3.7 mmHg.',
      ),
      view(
        'Pulmonary and tricuspid valves',
        pulmonary,
        'The pulmonary outflow and small tricuspid regurgitant jet appear on the same velocity scale. The TR envelope supplies the RV–RA systolic difference.',
        'Pulmonary peak 0.96 m/s · TR peak 2.20 m/s · RV–RA difference 19 mmHg.',
      ),
      view(
        'Systemic venous return',
        cava,
        'The subcostal longitudinal detail follows the same IVC site across breathing. Calipers span the lumen perpendicular to its walls.',
        '17 mm at end expiration → 7 mm on inspiration · 59% collapse.',
      ),
      view(
        'Pericardial space',
        sac,
        'Inspect around the ventricles from subcostal and parasternal windows. The detail models apposed pericardial layers without a fluid stripe.',
      ),
    ],
    impression: `Preserved modeled LV and RV systolic function (EF ${ef.toFixed(0)}%, RV area change ${fac.toFixed(0)}%). No significant outflow obstruction in the displayed spectra. No pericardial effusion in the worked survey.`,
    limitations:
      'Sections are cuts through authored anatomy. Flow, respiratory IVC change and the pericardial detail are prescribed illustrations. The companion 17-window exam supplies parasternal, apical, subcostal and suprasternal acquisition context.',
    sources: std,
  },
  {
    id: 'echo-aortic-stenosis',
    family: 'echo',
    kind: 'abnormal',
    title: 'Aortic stenosis across two Doppler windows',
    indication: 'Characterize a systolic ejection murmur in an adult with exertional dyspnea.',
    summary:
      'In this case the jet is directed toward the right parasternal window. Compare the recorded velocities before integrating the valve, gradient and effective area.',
    views: [
      view(
        'Valve morphology',
        valves,
        'Inspect the reduced central opening and thickened cusp edges in systole. The mobile-cusp example at left provides an orientation comparison.',
      ),
      view(
        'LVOT diameter and flow',
        lvotPlate,
        'Place an inner-edge diameter at cusp insertion and sample just proximal to the acceleration zone. Both enter the continuity calculation.',
        `LVOT diameter 2.10 cm · VTI ${vti.toFixed(1)} cm.`,
      ),
      view(
        'Compare continuous-wave windows',
        asCW,
        'The apical beam samples a lower component of the same jet. The dense right parasternal envelope is complete and reaches a higher peak. The mean gradient averages 4v² over ejection.',
        `Apical ${(peakVelocity(apical) / 100).toFixed(2)} m/s · right parasternal 4.54 m/s · mean gradient ${jet.meanGradient.toFixed(0)} mmHg.`,
      ),
    ],
    impression: `Severe high-gradient aortic stenosis in this modeled visit. The best aligned window yields Vmax 4.54 m/s and mean gradient ${jet.meanGradient.toFixed(0)} mmHg. LVOT VTI ${vti.toFixed(1)} cm ÷ valve VTI ${jet.vti.toFixed(1)} cm gives a dimensionless ratio of ${ratio.toFixed(2)}. Multiplying this ratio by the LVOT area, π × (2.10 cm / 2)², gives an effective valve area of ${area.toFixed(2)} cm².`,
    limitations:
      'The valve detail and smooth Doppler envelopes are authored. The comparison in Figure 5 is a separate acquired exam. The schematic valve opening and effective flow area represent different measurements.',
    sources: [asRef, ...std],
  },
  {
    id: 'echo-limited',
    family: 'echo',
    kind: 'limited',
    title: 'A murmur with an incomplete jet envelope',
    indication: 'Assess suspected valve obstruction when acoustic access is poor.',
    summary:
      'Valve motion raises suspicion, but the spectral signal drops out near peak ejection. A repeat from the right parasternal window also loses the jet.',
    views: [
      view(
        'Restricted cusp motion',
        valves,
        'The right-hand valve schematic establishes a structural reason to interrogate the outflow. Morphology alone cannot grade the obstruction.',
      ),
      view(
        'Apical acquisition and repeat',
        loss,
        'Both attempted alignments have a gap through the expected peak. The visible shoulders cannot supply a valid peak, mean gradient or valve VTI.',
      ),
    ],
    impression:
      'Restricted aortic valve opening. Hemodynamic severity is indeterminate. No reportable maximum velocity, mean gradient or continuity valve area from these acquisitions.',
    limitations:
      'Further diagnostic imaging would be needed to answer the referral. The missing range is deliberately omitted in both illustrations.',
    sources: [asRef, ...std],
  },
];
const acquiredPanels = {
  [lviv]: [44, 45],
  [axes]: [42, 48],
  [right]: [65, 66],
  [inflow]: [51, 88],
  [greatVessels]: [19, 85],
  [normalJets]: [55, 56],
  [pulmonary]: [28],
  [cava]: [82],
  [sac]: [1],
  [lvotPlate]: [18, 56],
  [valves]: [16],
};
for (const record of records) {
  for (const item of record.views) {
    if (acquiredPanels[item.image]) item.referenceIds = acquiredPanels[item.image].map((n) => 'bse-' + n);
  }
}
writeFileSync(resolve(out, 'cases.json'), JSON.stringify(records, null, 2) + '\n');
