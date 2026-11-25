// Local mm frame: +X toward patient left across the heart, +Y apex to base, +Z posterior.
// Targets determine the beam. Right vectors fix the display orientation at neutral rotation.
// Origins are the registered skin contacts in the shared torso frame.
export const CARDIAC_VIEWS = Object.freeze({
  plax: {group: 'Parasternal', label: 'Parasternal long axis',
    origin: [-16.801, 72.553, -77.728], target: [14.8, 88.8, -10.6],
    right: [-0.07094, 0.97661, -0.20297], depth: 146},
  'psax-av': {group: 'Parasternal', label: 'Short axis · aortic valve',
    origin: [-1.191, 50.264, -66.916], target: [10, 117, -22],
    right: [0.99046, -0.11454, -0.07659], depth: 140},
  'psax-mv': {group: 'Parasternal', label: 'Short axis · mitral valve',
    origin: [-8.949, 62.73, -74.144], target: [21, 100, -2],
    right: [0.79884, 0.33072, -0.50248], depth: 120},
  'psax-papillary': {group: 'Parasternal', label: 'Short axis · papillary muscles',
    origin: [-39.191, 62.532, -66.306], target: [21, 65.5, -2],
    right: [0.72867, 0.03818, -0.6838], depth: 132},
  'psax-apical': {group: 'Parasternal', label: 'Short axis · apex',
    origin: [-32.434, 75.468, -74.721], target: [10, 40, 0],
    right: [0.88961, 0.2113, -0.40491], depth: 162},
  a4c: {group: 'Apical', label: 'Apical four chamber',
    origin: [0, 0, 0], target: [0, 95, 0],
    right: [1, 0, 0], depth: 158},
  a5c: {group: 'Apical', label: 'Apical five chamber',
    origin: [-8.082, -3.334, 1.959], target: [0, 117, -20.9],
    right: [0.99198, -0.08449, -0.09403], depth: 162},
  a2c: {group: 'Apical', label: 'Apical two chamber',
    origin: [0.435, 7.643, -23.92], target: [32.5, 109, -9],
    right: [0.00497, -0.14717, 0.9891], depth: 151, halfAngle: 48},
  a3c: {group: 'Apical', label: 'Apical three chamber',
    origin: [-9.071, -4.546, 3.222], target: [17.2, 94.2, -9.4],
    right: [-0.72204, 0.10468, -0.68388], depth: 165},
  'rv-focused': {group: 'Apical', label: 'RV-focused four chamber',
    origin: [1.396, 0.332, -0.225], target: [-13, 96, -2],
    right: [0.95889, 0.14878, 0.24166], depth: 158},
  'rv-inflow': {group: 'Parasternal', label: 'Right ventricular inflow',
    origin: [-1.135, 74.903, -79.558], target: [-29, 99, -7],
    right: [-0.07774, 0.93685, -0.34098], depth: 153},
  'rv-outflow': {group: 'Parasternal', label: 'Right ventricular outflow',
    origin: [-6.138, 63.472, -74.521], target: [-8, 111, -28],
    right: [0.0965, 0.69817, -0.7094], depth: 138},
  'subcostal-4c': {group: 'Subcostal', label: 'Subcostal four chamber',
    origin: [-80.714, 28.961, -18.651], target: [-5, 98, -3],
    right: [0.66307, -0.7446, 0.07681], depth: 163},
  'subcostal-ivc': {group: 'Subcostal', label: 'Subcostal IVC',
    origin: [-76.102, 21.757, -15.278], target: [-43, 94, 10],
    right: [-0.25038, 0.41995, -0.87232], depth: 142},
  'subcostal-sax': {group: 'Subcostal', label: 'Subcostal short axis · RV outflow',
    origin: [-80.714, 28.961, -18.651], target: [-19, 98, -33],
    right: [-0.55512, 0.33829, -0.75987], depth: 149},
  'subcostal-aorta': {group: 'Subcostal', label: 'Subcostal abdominal aorta',
    origin: [-75.447, 19.334, -13.818], target: [-36, 49, 46],
    right: [0.2773, 0.77535, -0.56739], depth: 127},
  'suprasternal-arch': {group: 'Suprasternal', label: 'Suprasternal aortic arch',
    origin: [13.244, 191.937, -106.372], target: [9, 165, -8],
    right: [0.36129, 0.89526, 0.26073], depth: 140},
});

const DEGREE = Math.PI / 180;
export const BMODE_RASTER = Object.freeze({width: 396, height: 322, margin: 9, depthLabels: 19});

export function bmodeCalibration({depth, halfAngle}) {
  const {width, height, margin, depthLabels} = BMODE_RASTER;
  const scale = Math.min((height - 2 * margin) / depth, (width / 2 - depthLabels) / (Math.sin(halfAngle) * depth));
  const tip = (height - depth * scale) / 2;
  return {width, height, scale, tip, center: width / 2};
}

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = vector => {
  const length = Math.hypot(...vector);
  return vector.map(value => value / length);
};
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

export function probePlane(tilt, viewId = 'a4c') {
  const id = Object.hasOwn(CARDIAC_VIEWS, viewId) ? viewId : 'a4c';
  return directedPlane(tilt, id, CARDIAC_VIEWS[id]);
}

export function directedPlane(tilt, id, {origin, target, right: rightHint, depth, halfAngle = 36}) {
  const down = norm(target.map((value, axis) => value - origin[axis]));
  const candidate = norm(rightHint.map((value, axis) => value - dot(rightHint, down) * down[axis]));
  const front = cross(candidate, down);
  const cos = Math.cos(tilt * DEGREE);
  const sin = Math.sin(tilt * DEGREE);
  const right = candidate.map((value, axis) => value * cos + front[axis] * sin);
  const normal = cross(right, down);
  const rightOffset = dot(origin, right);
  const downOffset = dot(origin, down);
  const normalOffset = dot(origin, normal);
  return {
    id, tilt, origin, right, down, normal, halfAngle: halfAngle * DEGREE, depth,
    distance: point => dot(point, normal) - normalOffset,
    section: point => [dot(point, right) - rightOffset, dot(point, down) - downOffset],
    world: (u, y, offset = 0) => origin.map((value, axis) => value + u * right[axis] + y * down[axis] + offset * normal[axis]),
  };
}
