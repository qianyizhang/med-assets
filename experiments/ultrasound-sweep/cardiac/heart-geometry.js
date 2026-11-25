// Original, illustrative A4C geometry in nominal millimeters. +x is patient left,
// +y is depth from the apex-side probe, and +z is posterior.
import {outletValves, heartVessels} from './heart-vessels.js';
import {probePlane} from './heart-poses.js';
import {heartSection, largestContour} from './heart-slice.js';

export {CARDIAC_VIEWS, probePlane} from './heart-poses.js';
export {heartSection} from './heart-slice.js';
// Each row is [depth, right-patient edge, left-patient edge, z center, z radius].
const HEART_PROFILES = {
  LV: {
    lumen: [
      [24, 0, 0, 0, 0], [29, -5, 10, 0, 10], [39, -8, 24, -1, 17],
      [53, -8, 34, -2, 22], [69, -6, 43, -2, 26], [84, -3, 45, -3, 28],
      [97, 0.5, 44, -4, 25], [108, 5.8, 39, -4, 19],
    ],
    wall: [
      [16, 0, 0, 0, 0], [22, -11, 15, 0, 14], [33, -15, 27, -1, 20],
      [49, -17, 39, -2, 27], [66, -16, 49, -2, 32], [82, -14, 53, -3, 34],
      [96, -7, 51, -4, 32], [107, 1, 45, -4, 26], [113, 8, 37, -4, 19],
    ],
    shorten: 13.4,
    squeeze: [4.5, 13, 0.29],
    outerSqueeze: [0.5, 5.5, 0.10],
    roofShift: 3.5,
  },
  RV: {
    lumen: [
      [42, -13, -13, -6, 0], [50, -22, -12.5, -7, 9], [61, -32, -15, -8, 16],
      [73, -39, -14, -9, 22], [84, -42, -10.8, -7, 24],
      [94, -38, -4.2, -5, 21], [100, -34, -1.6, -4, 18],
    ],
    wall: [
      [36, -12, -12, -6, 0], [46, -23, -8, -8, 11], [58, -32, -8, -9, 19],
      [72, -42, -8, -10, 26], [85, -47, -5, -9, 28], [94, -45, -1, -7, 25],
      [104, -37, 2, -5, 21], [109, -30, -2, -4, 15],
    ],
    shorten: 14.5,
    squeeze: [9, 0.3, 0.24],
    outerSqueeze: [4.7, 0.4, 0.10],
    roofShift: 4.1,
  },
  LA: {
    lumen: [
      [108, 5.8, 39, -4, 19], [116, 5.0, 41, -5, 23], [125, 4.0, 46, -7, 25],
      [133, 8, 42, -8, 20], [139, 17, 36, -8, 13], [143, 26, 26, -8, 0],
    ],
    wall: [
      [103, 2.6, 45, -4, 23], [112, 1.8, 47, -5, 27], [123, 0.5, 51, -6, 29],
      [133, 3, 47, -7, 25], [142, 12, 41, -8, 17], [148, 25, 25, -8, 0],
    ],
  },
  RA: {
    lumen: [
      [100, -34, -1.6, -4, 18], [109, -42, -2.5, -4, 23], [118, -42, 0, -3, 25],
      [127, -36, 2, -4, 21], [134, -23, -2, -4, 14], [137, -11, -11, -4, 0],
    ],
    wall: [
      [94, -42, 0, -5, 23], [106, -50, 3, -4, 28], [116, -49, 5, -3, 29],
      [126, -42, 6, -4, 27], [135, -31, 4, -4, 20],
      [140, -21, -1, -4, 12], [143, -12, -12, -4, 0],
    ],
  },
};

const CONTRACTION = [
  [0, 0], [0.055, 0.03], [0.13, 0.32], [0.25, 0.84], [0.35, 1],
  [0.43, 0.99], [0.51, 0.62], [0.64, 0.27], [0.80, 0.21], [0.92, 0.065], [1, 0],
];
const RESERVOIR = [
  [0, 0], [0.17, 0.35], [0.35, 0.91], [0.43, 1], [0.52, 0.63],
  [0.67, 0.34], [0.83, 0.40], [0.92, 0.18], [1, 0],
];
const MITRAL_OPEN = [
  [0, 0], [0.43, 0], [0.52, 1], [0.63, 0.39], [0.74, 0.20],
  [0.85, 0.46], [0.92, 0.73], [0.965, 0.44], [1, 0],
];
const TRICUSPID_OPEN = [
  [0, 0], [0.446, 0], [0.53, 1], [0.65, 0.40], [0.76, 0.22],
  [0.86, 0.51], [0.935, 0.77], [0.975, 0.38], [1, 0],
];

const AORTIC_OPEN = [[0, 0], [0.055, 0], [0.096, 1], [0.25, 0.91], [0.35, 0], [1, 0]];
const PULMONARY_OPEN = [[0, 0], [0.055, 0], [0.105, 1], [0.26, 0.91], [0.35, 0], [1, 0]];

export const CARDIAC_STAGES = Object.freeze([
  {start: 0, key: 'isovolumetric-contraction', label: 'Isovolumetric contraction'},
  {start: 0.055, key: 'ejection', label: 'Ventricular ejection'},
  {start: 0.35, key: 'isovolumetric-relaxation', label: 'Isovolumetric relaxation'},
  {start: 0.43, key: 'early-filling', label: 'Early ventricular filling'},
  {start: 0.65, key: 'diastasis', label: 'Diastasis'},
  {start: 0.83, key: 'atrial-filling', label: 'Atrial contraction'},
]);

const RING_SIZE = 44;
const PROFILE_SUBDIVISIONS = 3;
const FULL_TURN = 2 * Math.PI;
const ringAngles = Array.from({length: RING_SIZE}, (_, index) => {
  const angle = index * FULL_TURN / RING_SIZE;
  return [Math.cos(angle), Math.sin(angle)];
});

const mix = (a, b, weight) => a + (b - a) * weight;
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

function slope(keys, at) {
  if (at === 0 || at === keys.length - 1) return 0;
  const [beforeTime, before] = keys[at - 1];
  const [time, value] = keys[at];
  const [afterTime, after] = keys[at + 1];
  const entering = (value - before) / (time - beforeTime);
  const leaving = (after - value) / (afterTime - time);
  return entering * leaving > 0 ? 2 / (1 / entering + 1 / leaving) : 0;
}

function curve(keys, phase) {
  const index = keys.findIndex(([time]) => time >= phase);
  if (index < 1) return keys[0][1];
  const [start, v0] = keys[index - 1];
  const [end, v1] = keys[index];
  const duration = end - start;
  const t = (phase - start) / duration;
  const near = (1 + 2 * t) * (1 - t) ** 2 * v0 + t * (1 - t) ** 2 * duration * slope(keys, index - 1);
  const far = t ** 2 * (3 - 2 * t) * v1 + t ** 2 * (t - 1) * duration * slope(keys, index);
  return near + far;
}

export function cardiacMotion(value) {
  const phase = ((value % 1) + 1) % 1;
  return {
    phase,
    stage: CARDIAC_STAGES.findLast(({start}) => phase >= start),
    contraction: curve(CONTRACTION, phase),
    reservoir: curve(RESERVOIR, phase),
    mitralOpen: curve(MITRAL_OPEN, phase),
    tricuspidOpen: curve(TRICUSPID_OPEN, phase),
    aorticOpen: curve(AORTIC_OPEN, phase),
    pulmonaryOpen: curve(PULMONARY_OPEN, phase),
  };
}

function profileValue(before, start, end, after, fraction) {
  const f2 = fraction * fraction;
  const f3 = f2 * fraction;
  let leftSlope = (end - before) * 0.5;
  let rightSlope = (after - start) * 0.5;
  // Avoid a radius reversal between profile landmarks, including near either tip.
  const difference = end - start;
  if (difference * leftSlope <= 0) leftSlope = 0;
  if (difference * rightSlope <= 0) rightSlope = 0;
  return (2 * f3 - 3 * f2 + 1) * start + (f3 - 2 * f2 + fraction) * leftSlope
    + (-2 * f3 + 3 * f2) * end + (f3 - f2) * rightSlope;
}

function loftRows(profile) {
  const rows = [];
  for (let index = 0; index < profile.length - 1; index += 1) {
    const before = profile[Math.max(0, index - 1)];
    const start = profile[index];
    const end = profile[index + 1];
    const after = profile[Math.min(index + 2, profile.length - 1)];
    const roundedStart = start[4] === 0;
    const roundedEnd = end[4] === 0;
    const subdivisions = roundedStart || roundedEnd ? 7 : PROFILE_SUBDIVISIONS;
    for (let step = 0; step < subdivisions; step += 1) {
      const f = step / subdivisions;
      const depthFraction = roundedStart ? f ** 2 : roundedEnd ? 1 - (1 - f) ** 2 : f;
      rows.push(start.map((value, column) => {
        if (column === 0) return mix(value, end[0], depthFraction);
        if (roundedStart || roundedEnd) return mix(value, end[column], f);
        return profileValue(before[column], value, end[column], after[column], f);
      }));
    }
  }
  rows.push(profile.at(-1));
  return rows;
}

const lofts = Object.fromEntries(Object.entries(HEART_PROFILES).map(([name, profile]) => [name, {
  ...profile,
  wall: loftRows(profile.wall),
  lumen: loftRows(profile.lumen),
}]));

function deformVentricle([depth, left, right, z, radius], source, profile, material, motion) {
  const {contraction, reservoir} = motion;
  const [apex] = source[0];
  const annularDepth = profile.lumen.at(-1)[0];
  const t = clamp((depth - apex) / (annularDepth - apex), 0, 1);
  const shortening = contraction * (material === 'wall' ? 0.91 : 1);
  const [leftSqueeze, rightSqueeze, zSqueeze] = material === 'wall'
    ? profile.outerSqueeze : profile.squeeze;
  const squeeze = contraction * Math.sin(Math.PI * t * 0.72) * (1 - 0.39 * t ** 4);
  const twist = contraction * 1.65 * Math.sin(Math.PI * (1 - t));
  return [depth + shortening * (2.4 * (1 - t) - profile.shorten * t ** 1.24)
      + reservoir * clamp((depth - annularDepth) / 8, 0, 1),
    left + leftSqueeze * squeeze, right - rightSqueeze * squeeze,
    z + twist, radius * (1 - zSqueeze * squeeze)];
}

function deformAtrium([depth, left, right, z, radius], source, ventricle, annulus, motion) {
  const {contraction, reservoir} = motion;
  const [base] = source[0];
  const t = (depth - base) / (source.at(-1)[0] - base);
  const expanded = Math.sin(Math.PI * t) * reservoir;
  const [depthShift, leftShift, rightShift, zShift, radiusShift] = annulus;
  return [depth + (1 - t) * depthShift + t * ventricle.roofShift * reservoir,
    left + (1 - t) * leftShift - 2.3 * expanded,
    right + (1 - t) * rightShift + 2.9 * expanded,
    z + (1 - t) * zShift - 1.8 * Math.sin(Math.PI * t) * contraction,
    radius + (1 - t) * radiusShift + 2.7 * expanded];
}

function rvCrescent(depth, half, sin) {
  const wrap = clamp((112 - depth) / 36, 0, 1);
  return half * (0.17 * sin * sin - 0.37 * sin + 1.42 * wrap * Math.min(0, sin) ** 2);
}

function surfaceRing(row, shape, lateralLift = 0) {
  const [depth, left, right, z, radius] = row;
  const middle = (left + right) / 2;
  const half = (right - left) / 2;
  return ringAngles.map(([cos, sin]) => {
    // The RV is skewed anteriorly off-axis, while its septal border bends toward the LV.
    const crescent = shape === 'RV' ? rvCrescent(depth, half, sin) : 0;
    return [middle + half * cos + crescent, depth - lateralLift * (1 - cos) * 0.5, z + radius * sin];
  });
}

function leafletPair(ring, open, isMitral, lateralLift) {
  const [depth, left, right, z, radius] = ring;
  const half = (right - left) / 2;
  const center = (left + right) / 2;
  const coaptation = center - half * (isMitral ? 0.19 : 0.10);
  return [-1, 1].map((side) => {
    const rows = [];
    for (let row = 0; row <= 6; row += 1) {
      const flow = row / 6;
      const points = [];
      for (let col = 0; col <= 20; col += 1) {
        const angle = (col / 20 - 0.5) * Math.PI;
        const rise = Math.cos(angle);
        const sin = Math.sin(angle);
        const width = half * rise;
        const crescent = isMitral ? 0 : rvCrescent(depth, half, sin);
        const hinge = center + side * width + crescent;
        const closedX = mix(center + crescent, coaptation + crescent, rise);
        const tipX = mix(closedX, hinge - side * width * 0.21, open);
        const excursion = open * (side < 0 ? 11.2 : 8.4);
        const camber = Math.sin(Math.PI * flow) * rise * (0.8 + open);
        const x = mix(hinge, tipX, flow);
        const pull = lateralLift * (1 - (x - center - crescent) / half) * 0.5;
        points.push([x, depth - (3.3 + excursion) * flow * rise - camber - pull,
          z + radius * sin]);
      }
      rows.push(points);
    }
    return {name: isMitral ? 'MV' : 'TV', material: 'leaflet', rings: rows};
  });
}

function myocardiumDetails(rows, ventricle, posterior = false) {
  const isLeft = ventricle === 'LV';
  const reference = rows[Math.floor((isLeft ? (posterior ? 0.64 : 0.66) : 0.64) * rows.length)];
  const [depth, left, right, z] = reference;
  const tip = isLeft ? right - (posterior ? 23 : 11) : mix(left, right, 0.57);
  const outer = isLeft ? right - (posterior ? 9 : 0) : left - 0.5;
  const width = isLeft ? 3 : 3.3;
  const length = isLeft ? 17 : 10.8;
  const center = z + (posterior ? 16 : 1);
  const rowsOfMuscle = loftRows([
    [depth - length * 0.66, outer, outer, center + 2.5, 0],
    [depth - length * 0.32, mix(outer, tip, 0.37) - width, mix(outer, tip, 0.37) + width, center + 2.4, 4],
    [depth, tip - width, tip + width, center + 3.3, 4.5],
    [depth + length * 0.34, tip, tip, center + 2.4, 0],
  ]);
  return {name: ventricle, material: 'muscle', rings: rowsOfMuscle.map((row) => surfaceRing(row))};
}

export function heartFrame(phase) {
  const motion = cardiacMotion(phase);
  const chambers = {};
  const details = [];
  for (const [ventricle, atrium, open] of [
    ['LV', 'LA', motion.mitralOpen], ['RV', 'RA', motion.tricuspidOpen],
  ]) {
    const v = lofts[ventricle];
    const a = lofts[atrium];
    const ventricularLumen = v.lumen.map((row) => deformVentricle(row, v.lumen, v, 'lumen', motion));
    const referenceRing = v.lumen.at(-1);
    const activeRing = ventricularLumen.at(-1);
    const annulus = activeRing.map((value, index) => value - referenceRing[index]);
    // Tricuspid free-wall descent exceeds septal excursion. Apply the same
    // deformation at both sides of the junction and at the leaflet attachment.
    const lateralLift = ventricle === 'RV' ? 4.3 * motion.contraction : 0;
    const pull = ([depth]) => lateralLift * Math.exp(-(((depth - activeRing[0]) / 23) ** 2));
    const ring = (row, shape) => surfaceRing(row, shape, pull(row));
    chambers[ventricle] = {
      name: ventricle,
      wall: v.wall.map((row) => ring(deformVentricle(row, v.wall, v, 'wall', motion), ventricle)),
      lumen: ventricularLumen.map((row) => ring(row, ventricle)),
    };
    chambers[atrium] = {
      name: atrium,
      wall: a.wall.map((row) => ring(deformAtrium(row, a.wall, v, annulus, motion), atrium)),
      lumen: a.lumen.map((row) => ring(deformAtrium(row, a.lumen, v, annulus, motion), ventricle)),
    };
    details.push(...leafletPair(activeRing, open, ventricle === 'LV', lateralLift));
    details.push(myocardiumDetails(ventricularLumen, ventricle));
    if (ventricle === 'LV') details.push(myocardiumDetails(ventricularLumen, ventricle, true));
  }
  details.push(...outletValves(motion));
  return {chambers, vessels: heartVessels(motion), details, motion};
}

export function measurementContour(phase, viewId, chamber, tilt = 0) {
  const section = heartSection(heartFrame(phase), probePlane(tilt, viewId));
  return largestContour(section.chambers[chamber]?.lumen ?? []);
}
