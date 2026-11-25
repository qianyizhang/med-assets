import {chamberColor, contourPath, linePath, sectorPath} from './heart-echo.js';
import {probePlane} from './heart-poses.js';

const DEGREE = Math.PI / 180;
const KEY_LIGHT = [-0.45, -0.62, 0.64];
const FILL_LIGHT = [0.64, -0.38, -0.62];
const CUT_FILLS = {LV: '#9c605a', RV: '#965b53', LA: '#9c665e', RA: '#8a5653'};
const MUSCLE_COLOR = [165, 91, 82];
const ARTERIES = ['Ao', 'LVOT', 'Arch', 'DescAo', 'Arch branches'];
const CAP_LAYER = new WeakMap();
const SHELL_COLORS = {
  LV: [168, 86, 77], RV: [149, 79, 70], LA: [160, 88, 84], RA: [141, 75, 71],
};
const LUMEN_COLORS = {
  LV: [108, 50, 51], RV: [97, 58, 56], LA: [106, 53, 56], RA: [81, 47, 49],
};

function minus(a, b) {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function cross(a, b) {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function dot(a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function projection(width, height, yaw, pitch, plane) {
  const sy = Math.sin(yaw * DEGREE);
  const cy = Math.cos(yaw * DEGREE);
  const sp = Math.sin(pitch * DEGREE);
  const cp = Math.cos(pitch * DEGREE);
  // Open each window at an oblique view of its neutral fan. Probe rotation
  // moves the live fan through the heart while the observer stays fixed.
  const neutral = probePlane(0, plane.id);
  const focus = neutral.world(0, plane.depth * 0.55, -4);
  const zoom = Math.min(width / (plane.depth * 1.27 + 18), height / (plane.depth + 83));
  const cameraRight = neutral.right.map((value, axis) => value * cy - neutral.normal[axis] * sy);
  const axial = neutral.right.map((value, axis) => value * sy + neutral.normal[axis] * cy);
  const cameraDown = neutral.down.map((value, axis) => value * cp - axial[axis] * sp);
  const towardCamera = axial.map((value, axis) => value * cp + neutral.down[axis] * sp);
  const centerX = width / 2 - zoom * dot(focus, cameraRight);
  const centerY = height / 2 - zoom * dot(focus, cameraDown);
  const centerDepth = dot(focus, towardCamera);
  return {
    zoom,
    towardCamera,
    point(point) {
      return [centerX + zoom * dot(point, cameraRight), centerY + zoom * dot(point, cameraDown),
        dot(point, towardCamera) - centerDepth];
    },
  };
}

function rearHalf(points, plane) {
  if (!plane) return points;
  const cuts = points.map(plane.distance);
  if (cuts.every((distance) => distance <= 0)) return points;
  if (cuts.every((distance) => distance > 0)) return [];
  const result = [];
  for (let index = 0; index < points.length; index += 1) {
    const next = (index + 1) % points.length;
    const a = cuts[index];
    const b = cuts[next];
    if (a <= 0) result.push(points[index]);
    if ((a <= 0) !== (b <= 0)) {
      const f = a / (a - b);
      result.push(points[index].map((value, axis) => value + (points[next][axis] - value) * f));
    }
  }
  return result;
}

function colorFor(base, normal, lighting, material) {
  const key = Math.max(0, lighting * dot(KEY_LIGHT, normal));
  const fill = Math.max(0, lighting * dot(FILL_LIGHT, normal));
  const light = 0.16 + key + 0.52 * fill;
  const lit = material === 'wall' ? 0.56 + light * 0.74 : 0.66 + light * 0.78;
  return `rgb(${base.map((channel) => Math.round(channel * lit)).join(',')})`;
}

function meshFaces(faces, shape, project, plane) {
  const {name, material, rings} = shape;
  const {towardCamera} = project;
  const leaflet = material === 'leaflet';
  const doubleSided = leaflet;
  const closeRing = !leaflet;
  const direction = material === 'lumen' ? -1 : 1;
  const artery = ARTERIES.includes(name);
  const base = material === 'wall' ? (SHELL_COLORS[name] ?? (artery ? [164, 85, 76] : [134, 102, 103]))
    : material === 'lumen' ? (LUMEN_COLORS[name] ?? (artery ? [100, 53, 54] : [76, 59, 65]))
      : leaflet ? [198, 139, 114] : MUSCLE_COLOR;
  for (let row = 0; row < rings.length - 1; row += 1) {
    const shapeRow = rings[row];
    const following = rings[row + 1];
    for (let column = 0; column < shapeRow.length - (closeRing ? 0 : 1); column += 1) {
      const next = (column + 1) % shapeRow.length;
      const a = shapeRow[column];
      const b = following[column];
      const c = following[next];
      const d = shapeRow[next];
      const normal = cross(minus(c, a), minus(d, b));
      const size = Math.hypot(...normal);
      if (size <= 0.002) continue;
      const orientation = dot(normal, towardCamera) * direction;
      if (!doubleSided && orientation <= 0) continue;
      const polygon = rearHalf([a, b, c, d], plane);
      if (polygon.length < 3) continue;
      const points = polygon.map(project.point);
      const depth = points.reduce((sum, point) => sum + point[2], 0) / points.length;
      const lighting = (orientation < 0 ? -direction : direction) / size;
      faces.push({points, depth, color: colorFor(base, normal, lighting, material)});
    }
  }
}

function fillFaces(ink, faces) {
  faces.sort((a, b) => a.depth - b.depth);
  ink.lineJoin = 'round';
  ink.lineWidth = 0.75;
  for (const {points, color} of faces) {
    ink.beginPath();
    ink.moveTo(points[0][0], points[0][1]);
    for (let index = 1; index < points.length; index += 1) ink.lineTo(points[index][0], points[index][1]);
    ink.closePath();
    ink.fillStyle = ink.strokeStyle = color;
    ink.fill();
    ink.stroke();
  }
}

function inPlane(ink, plane, project, paint) {
  const origin = project.point(plane.world(0, 0));
  const across = project.point(plane.world(1, 0));
  const down = project.point(plane.world(0, 1));
  ink.save();
  ink.transform(across[0] - origin[0], across[1] - origin[1], down[0] - origin[0], down[1] - origin[1], origin[0], origin[1]);
  paint();
  ink.restore();
}

function cap(ink, plane, project, cut, overlay, width, height) {
  const {chambers, muscleCuts, valveCuts} = cut;
  const sector = sectorPath(plane);
  inPlane(ink, plane, project, () => {
    ink.fillStyle = '#55b8d317';
    ink.fill(sector);
  });
  let layer = CAP_LAYER.get(ink);
  if (!layer) {
    const canvas = document.createElement('canvas');
    layer = {canvas, ink: canvas.getContext('2d')};
    CAP_LAYER.set(ink, layer);
  }
  const layerWidth = Math.ceil(width), layerHeight = Math.ceil(height);
  if (layer.canvas.width !== layerWidth) layer.canvas.width = layerWidth;
  if (layer.canvas.height !== layerHeight) layer.canvas.height = layerHeight;
  const surface = layer.ink;
  surface.clearRect(0, 0, layerWidth, layerHeight);
  inPlane(surface, plane, project, () => {
    surface.clip(sector);
    for (const [name, {wall}] of Object.entries(chambers)) {
      surface.fillStyle = CUT_FILLS[name] ?? (ARTERIES.includes(name) ? '#9e6e63' : '#8a7376');
      for (const contour of wall) surface.fill(contourPath(contour));
    }
    surface.globalCompositeOperation = 'destination-out';
    surface.fillStyle = '#fff';
    for (const {lumen} of Object.values(chambers)) {
      for (const contour of lumen) surface.fill(contourPath(contour));
    }
  });
  ink.drawImage(layer.canvas, 0, 0, width, height);
  inPlane(ink, plane, project, () => {
    ink.save();
    ink.clip(sector);
    ink.lineCap = 'round';
    ink.lineJoin = 'round';
    for (const outline of muscleCuts) {
      ink.fillStyle = '#a57060';
      ink.fill(contourPath(outline));
    }
    for (const {points} of valveCuts) {
      ink.lineWidth = 0.86;
      ink.strokeStyle = '#e8b998';
      ink.stroke(linePath(points));
    }
    if (overlay) {
      for (const [name, {lumen}] of Object.entries(chambers)) {
        const color = chamberColor(name);
        for (const contour of lumen) {
          const intersection = contourPath(contour);
          ink.fillStyle = color.fill;
          ink.fill(intersection);
          ink.strokeStyle = color.edge;
          ink.lineWidth = 0.53;
          ink.stroke(intersection);
        }
      }
    }
    ink.restore();
    ink.strokeStyle = '#78cee19f';
    ink.lineWidth = 0.53;
    ink.stroke(sector);
  });
}

function probeBody(ink, plane, project) {
  const footprint = Array.from({length: 20}, (_, index) => 2 * Math.PI * index / 20);
  const rings = [[-18, 4.2, 4.2], [-14, 6.6, 5.5], [-8, 8.2, 5.4], [-3, 8.6, 4.5], [0, 7, 2.8]];
  const material = [115, 154, 171];
  const faces = [];
  const mesh = rings.map(([y, width, span]) => footprint.map((angle) => plane.world(width * Math.cos(angle), y, span * Math.sin(angle))));
  for (let row = 0; row < mesh.length - 1; row += 1) {
    for (let column = 0; column < footprint.length; column += 1) {
      const next = (column + 1) % footprint.length;
      const a = mesh[row][column];
      const b = mesh[row + 1][column];
      const c = mesh[row + 1][next];
      const d = mesh[row][next];
      const normal = cross(minus(c, a), minus(d, b));
      const length = Math.hypot(...normal);
      if (dot(normal, project.towardCamera) <= 0) continue;
      const points = [a, b, c, d].map(project.point);
      const depth = points.reduce((sum, point) => sum + point[2], 0) / 4;
      faces.push({points, depth, color: colorFor(row === mesh.length - 2 ? [129, 199, 214] : material, normal, 1 / length, 'wall')});
    }
  }
  const connector = project.point(plane.world(0, -17));
  const cable = project.point(plane.world(-12, -26, -6));
  ink.beginPath();
  ink.moveTo(connector[0], connector[1]);
  ink.quadraticCurveTo(connector[0], cable[1], cable[0], cable[1]);
  ink.strokeStyle = '#57717e';
  ink.lineWidth = 1.7;
  ink.stroke();
  fillFaces(ink, faces);
}

export function renderScene(ink, width, height, frame, plane, cut, overlay, yaw, pitch) {
  const project = projection(width, height, yaw, pitch, plane);
  const wash = ink.createRadialGradient(width * 0.46, height * 0.42, 1,
    width * 0.48, height * 0.50, Math.max(width * 0.63, height * 0.73));
  wash.addColorStop(0, '#17232d');
  wash.addColorStop(1, '#0c1218');
  ink.fillStyle = wash;
  ink.fillRect(0, 0, width, height);
  const capInFront = dot(plane.normal, project.towardCamera) >= 0;
  if (!capInFront) cap(ink, plane, project, cut, overlay, width, height);
  const faces = [];
  for (const {name, wall, lumen} of Object.values(frame.chambers)) {
    meshFaces(faces, {name, material: 'wall', rings: wall}, project, plane);
    meshFaces(faces, {name, material: 'lumen', rings: lumen}, project, plane);
  }
  for (const {name, wall, lumen} of Object.values(frame.vessels)) {
    for (const rings of wall) meshFaces(faces, {name, material: 'wall', rings}, project, plane);
    for (const rings of lumen) meshFaces(faces, {name, material: 'lumen', rings}, project, plane);
  }
  for (const mesh of frame.details) meshFaces(faces, mesh, project, plane);
  fillFaces(ink, faces);
  if (capInFront) cap(ink, plane, project, cut, overlay, width, height);
  probeBody(ink, plane, project);
}
