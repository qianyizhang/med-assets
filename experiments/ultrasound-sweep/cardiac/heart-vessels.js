// Schematic continuity from the chamber pools to the great vessels. Control points
// are [x, y, z, lumen radius] in the same frame as the chamber lofts.
const VESSEL_PATHS = {
  LVOT: [[21, 82, -13, 12], [17, 97, -16, 13], [12, 109, -20, 12], [10, 120, -24, 12]],
  Ao: [[10, 116, -22, 11], [9, 124, -26, 14], [7, 138, -36, 12], [6, 158, -39, 12], [9, 171, -32, 12]],
  Arch: [[6, 158, -39, 12], [9, 171, -32, 12], [14, 179, -19, 11], [21, 178, 0, 11], [22, 169, 16, 11],
    [20, 152, 27, 10], [16, 130, 31, 9]],
  DescAo: [[20, 152, 27, 10], [16, 130, 31, 9], [13, 113, 32, 9], [1, 96, 38, 8.8],
    [-12, 80, 43, 8.5], [-23, 64, 46, 8.3], [-36, 49, 46, 8.1], [-46, 34, 43, 8],
    [-53, 20, 41, 7.8]],
  RVOT: [[-25, 76, -16, 11], [-24, 87, -23, 13], [-19, 98, -33, 11], [-13, 111, -41, 10],
    [-9, 121, -43, 11]],
  PA: [[-10, 118, -42, 11], [-9, 128, -44, 12], [-7, 140, -41, 13], [0, 148, -31, 13],
    [11, 149, -23, 11], [27, 146, -14, 8], [40, 143, -10, 7]],
  RPA: [[-1, 146, -29, 9], [-13, 147, -22, 8], [-29, 144, -13, 7], [-43, 141, -8, 6]],
  IVC: [[-69, 47, 12, 9], [-58, 66, 16, 9], [-47, 83, 14, 9],
    [-41, 99, 9, 9.5], [-34, 113, 4, 9.5], [-26, 120, 0, 8]],
  SVC: [[-33, 121, -6, 8], [-34, 135, -13, 9], [-32, 151, -17, 9],
    [-31, 168, -19, 9], [-32, 188, -18, 8]],
  'Arch branches': [
    [[9, 167, -34, 5.7], [6, 181, -29, 5.3], [-2, 193, -25, 5], [-13, 208, -26, 4.5]],
    [[15, 177, -19, 4.0], [15, 192, -19, 4], [19, 207, -16, 3.6]],
    [[21, 176, -4, 4.4], [24, 190, -5, 4.2], [31, 196, 2, 3.7], [43, 201, 2, 3.5]],
  ],
};

const count = 28;
const angles = Array.from({length: count}, (_, index) => {
  const angle = index / count * 2 * Math.PI;
  return [Math.cos(angle), Math.sin(angle)];
});
const mix = (a, b, t) => a + (b - a) * t;
const minus = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = a => { const length = Math.hypot(...a); return a.map(n => n / length); };

function curveValue(a, b, c, d, t) {
  return (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2
    + (-a + 3 * b - 3 * c + d) * t ** 3) * 0.5;
}

function centerline(knots) {
  const points = [];
  for (let i = 1; i < knots.length; i += 1) {
    const start = knots[i - 1], end = knots[i];
    const prior = knots[Math.max(0, i - 2)], next = knots[Math.min(i + 1, knots.length - 1)];
    const divisions = Math.max(2, Math.ceil(Math.hypot(...minus(start, end)) / 4.5));
    for (let step = 0; step < divisions; step += 1) {
      points.push(start.map((value, j) => curveValue(prior[j], value, end[j], next[j], step / divisions)));
    }
  }
  points.push(knots.at(-1));
  return points;
}

function frameAxes(tangent) {
  const along = unit(tangent);
  const across = unit(cross(Math.abs(along[0]) > 0.92 ? [0, 0, 1] : [1, 0, 0], along));
  return [across, cross(across, along), along];
}

function tube(knots, wall) {
  const points = centerline(knots);
  return points.map((point, index) => {
    const before = points[Math.max(0, index - 1)];
    const after = points[Math.min(index + 1, points.length - 1)];
    const [xAxis, zAxis] = frameAxes(minus(after, before));
    return angles.map(([cos, sin]) => [0, 1, 2].map(j => point[j]
      + (point[3] + wall) * (cos * xAxis[j] + sin * zAxis[j])));
  });
}

const staticVessels = Object.fromEntries(Object.entries(VESSEL_PATHS)
  .filter(([name]) => !['LVOT', 'RVOT', 'Arch branches'].includes(name))
  .map(([name, knots]) => [name, {name, wall: [tube(knots, 1.9)], lumen: [tube(knots, 0)]}]));
const branches = {
  name: 'Arch branches', wall: VESSEL_PATHS['Arch branches'].map(knots => tube(knots, 1.4)),
  lumen: VESSEL_PATHS['Arch branches'].map(knots => tube(knots, 0)),
};

function ventricularOutflow(name, contraction) {
  const path = VESSEL_PATHS[name];
  const knots = path.map(([x, y, z, radius], index) => {
    const proximal = 1 - index / (path.length - 1);
    return [x, y - 10 * contraction * proximal, z + contraction * proximal * 2,
      radius * (1 - 0.17 * contraction * proximal)];
  });
  return {name, wall: [tube(knots, 2.9)], lumen: [tube(knots, 0)]};
}

function semilunarCusps(name, center, tangent, open, startAngle) {
  const [across, span, along] = frameAxes(tangent);
  const radius = center[3] - 0.25;
  const cusps = [];
  for (let cusp = 0; cusp < 3; cusp += 1) {
    const middle = startAngle + cusp * 2 * Math.PI / 3;
    const rings = [];
    for (let row = 0; row <= 6; row += 1) {
      const edge = row / 6;
      const points = [];
      for (let col = 0; col <= 18; col += 1) {
        const position = col / 9 - 1;
        const delta = position * Math.PI / 3;
        const angle = middle + delta;
        const commissure = middle + Math.sign(position) * Math.PI / 3;
        const fraction = Math.abs(position);
        const rise = Math.max(0, Math.cos(delta * 1.5));
        const openRadius = 1 - rise * 0.21;
        const radialX = mix(fraction * Math.cos(commissure), openRadius * Math.cos(angle), open);
        const radialZ = mix(fraction * Math.sin(commissure), openRadius * Math.sin(angle), open);
        const bow = mix(0.8 * (1 - fraction), 7 * rise, open) * edge
          - Math.sin(edge * Math.PI) * (1.8 - open) * rise;
        points.push([0, 1, 2].map(axis => center[axis] + radius *
          (mix(Math.cos(angle), radialX, edge) * across[axis] + mix(Math.sin(angle), radialZ, edge) * span[axis])
          + bow * along[axis]));
      }
      rings.push(points);
    }
    cusps.push({name, material: 'leaflet', rings});
  }
  return cusps;
}

export function heartVessels(motion) {
  return {...staticVessels, 'Arch branches': branches,
    LVOT: ventricularOutflow('LVOT', motion.contraction), RVOT: ventricularOutflow('RVOT', motion.contraction)};
}

export function outletValves(motion) {
  return [
    ...semilunarCusps('AV', [10, 117, -22, 11.5], [-0.11, 0.85, -0.51], motion.aorticOpen, 0.3),
    ...semilunarCusps('PV', [-10, 119, -42, 11], [0.26, 0.95, -0.17], motion.pulmonaryOpen, -0.35),
  ];
}
