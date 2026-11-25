import {classifyTissue, ellipseFactor, tubesAt} from './playable-model.js';

export const aorticLength = 218;
export const anatomyBackground = '#152129';
const viewport = {x: 17, y: 65, width: 366, height: 183};
const scale = 1.68;
const worldCenter = [0, 45, aorticLength / 2];
const screenCenter = [200, 155];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const rgba = (r, g, b) => (255 << 24) | ((b | 0) << 16) | ((g | 0) << 8) | (r | 0);
const background = rgba(21, 33, 41);
const surfaces = new Map();

export function aorticCamera(yaw) {
  // Present both common iliacs in the resting view, with the section face visible throughout orbit.
  const sine = Math.sin(yaw - .48);
  const cosine = Math.cos(yaw - .48);
  const rotate = ([x, y, z]) => [x * cosine + y * sine, -x * sine + y * cosine, z];
  const oblique = .52;
  const along = Math.sqrt(1 - oblique ** 2);
  const pitch = .22;
  const level = Math.sqrt(1 - pitch ** 2);
  const right = rotate([oblique, 0, along]);
  const down = rotate([-along * pitch, level, oblique * pitch]);
  const away = rotate([-along * level, -pitch, oblique * level]);
  return {
    right, down, away,
    project(x, y, z) {
      const offset = [x - worldCenter[0], y - worldCenter[1], z - worldCenter[2]];
      return [screenCenter[0] + dot(offset, right) * scale, screenCenter[1] + dot(offset, down) * scale,
        dot(offset, away)];
    },
  };
}

function surfaceField(tubes, x, y, inner) {
  let distance = 16;
  for (const tube of tubes) {
    const factor = inner ? ellipseFactor(x, y, tube.lx, tube.ly, tube.lrx, tube.lry)
      : ellipseFactor(x, y, tube.x, tube.y, tube.rx, tube.ry);
    const radius = inner ? Math.min(tube.lrx, tube.lry) : Math.min(tube.rx, tube.ry);
    distance = Math.min(distance, (Math.sqrt(factor) - 1) * radius);
  }
  return distance;
}

// A surface net places one vertex per voxel crossed by the shared tube boundary.
// Joining four cells around each crossed edge also joins the union at the iliac crotch.
const cubeEdges = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3],
  [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]].map(([a, b]) => [a, b, Math.log2(a ^ b)]);
const step = 1.8;
const minX = -42;
const minY = 22;
const nx = Math.ceil(84 / step) + 1;
const ny = Math.ceil(50 / step) + 1;
const sliceSize = nx * ny;
const cornerIndex = c => (c & 1) + ((c >> 1) & 1) * nx + (c >> 2) * sliceSize;
const cubeNeighbors = [[1, nx, sliceSize], [2, sliceSize, 1], [4, 1, nx]];

function net(record, kind) {
  const inside = kind === 'lumen';
  const artery = kind !== 'vein';
  const end = artery ? aorticLength : 143;
  const nz = Math.ceil(end / step) + 1;
  const dz = end / (nz - 1);
  const field = new Float32Array(sliceSize * nz);
  const cellIndex = new Int32Array(field.length).fill(-1);
  const contours = Array.from({length: nz}, (_, iz) =>
    tubesAt(record, null, iz * dz).filter(v => (v.color > 0) === artery));
  for (let iz = 0; iz < nz; iz++) {
    for (let iy = 0; iy < ny; iy++) {
      for (let ix = 0; ix < nx; ix++) {
        field[iz * sliceSize + iy * nx + ix] =
          surfaceField(contours[iz], minX + ix * step, minY + iy * step, inside);
      }
    }
  }
  const vertices = [];
  const faces = [];
  const stencil = Array.from({length: 8}, (_, index) => cornerIndex(index));
  const values = new Float32Array(8);
  for (let iz = 0; iz < nz - 1; iz++) {
    for (let iy = 0; iy < ny - 1; iy++) {
      for (let ix = 0; ix < nx - 1; ix++) {
        const cell = iz * sliceSize + iy * nx + ix;
        let mask = 0;
        for (let corner = 0; corner < 8; corner++) {
          values[corner] = field[cell + stencil[corner]];
          if (values[corner] <= 0) mask |= 1 << corner;
        }
        if (!mask || mask === 255) continue;
        let count = 0;
        const sum = [0, 0, 0];
        const normal = [0, 0, 0];
        for (const [a, b, axis] of cubeEdges) {
          normal[axis] += values[b] - values[a];
          if (((mask >> a) & 1) === ((mask >> b) & 1)) continue;
          const fraction = values[a] / (values[a] - values[b]);
          for (let k = 0; k < 3; k++) sum[k] += (a & (1 << k)) ? 1 : k === axis ? fraction : 0;
          count++;
        }
        const x = minX + (ix + sum[0] / count) * step;
        const y = minY + (iy + sum[1] / count) * step;
        const z = (iz + sum[2] / count) * dz;
        const normalizer = Math.hypot(...normal) || 1;
        const n = normal.map(value => value / normalizer * (inside ? -1 : 1));
        cellIndex[cell] = vertices.length;
        vertices.push({x, y, z, n});

        // The first edge in each axis can have up to four incident cells.
        // The cells at the ends of the volume have no caps.
        for (const [bit, strideU, strideV] of cubeNeighbors) {
          if (((mask >> bit) & 1) === (mask & 1)) continue;
          const a = cellIndex[cell];
          const b = cellIndex[cell - strideU];
          const c = cellIndex[cell - strideU - strideV];
          const d = cellIndex[cell - strideV];
          if (b >= 0 && c >= 0 && d >= 0) {
            const positive = Boolean(mask & 1) !== inside;
            if (positive) faces.push(a, b, c, a, c, d);
            else faces.push(a, c, b, a, d, c);
          }
        }
      }
    }
  }
  return {kind, vertices, faces};
}

export function aorticSurfaces(record) {
  const dilated = record.kind === 'abnormal';
  if (!surfaces.has(dilated)) {
    surfaces.set(dilated, ['wall', 'lumen', 'vein'].map(kind => net(record, kind)));
  }
  return surfaces.get(dilated);
}

const workspace = new WeakMap();

function buffers(ctx) {
  if (!workspace.has(ctx)) {
    const {width, height} = viewport;
    const image = ctx.createImageData(width, height);
    workspace.set(ctx, {image, pixels: new Uint32Array(image.data.buffer),
      opaqueDepth: new Float32Array(width * height), contextDepth: new Float32Array(width * height),
      contextPixels: new Uint32Array(width * height)});
  }
  return workspace.get(ctx);
}

function capPlane(camera, {anchorX, z}, axes) {
  const {horizontal: h, depth: d} = axes;
  const normal = [-h.z * d.y, h.z * d.x, h.x * d.y - h.y * d.x];
  const facing = dot(normal, camera.away);
  // At edge-on angles the section has no readable area.
  if (Math.abs(facing) < .10) return null;
  const [x0, y0, depth] = camera.project(anchorX, 0, z);
  const dx = -dot(normal, camera.right) / (scale * facing);
  const dy = -dot(normal, camera.down) / (scale * facing);
  const origin = depth - x0 * dx - y0 * dy;
  return {dx, dy, origin};
}

function shade(vertex, kind, camera, light) {
  const highlight = Math.max(0, dot(vertex.n, light));
  const rim = (1 - Math.min(1, Math.abs(dot(vertex.n, camera.away)))) ** 3;
  if (kind === 'wall') return .46 + .48 * highlight + .12 * rim;
  return .38 + .38 * highlight;
}

function drawTriangles(mesh, camera, plane, target) {
  const {x, y, width, height} = viewport;
  const {opaqueDepth, contextDepth, pixels, contextPixels} = target;
  const light = camera.right.map((value, i) => -.33 * value - .53 * camera.down[i] - .78 * camera.away[i]);
  const p = mesh.vertices.map(vertex => {
    const [u, v, depth] = camera.project(vertex.x, vertex.y, vertex.z);
    return {u, v, depth, s: shade(vertex, mesh.kind, camera, light)};
  });
  const solid = mesh.kind === 'wall';
  const vein = mesh.kind === 'vein';
  for (let face = 0; face < mesh.faces.length; face += 3) {
    const a = p[mesh.faces[face]];
    const b = p[mesh.faces[face + 1]];
    const c = p[mesh.faces[face + 2]];
    const left = Math.max(x, Math.floor(Math.min(a.u, b.u, c.u)));
    const right = Math.min(x + width - 1, Math.ceil(Math.max(a.u, b.u, c.u)));
    const top = Math.max(y, Math.floor(Math.min(a.v, b.v, c.v)));
    const bottom = Math.min(y + height - 1, Math.ceil(Math.max(a.v, b.v, c.v)));
    const bu = b.u - a.u;
    const bv = b.v - a.v;
    const cu = c.u - a.u;
    const cv = c.v - a.v;
    const det = bu * cv - cu * bv;
    if (Math.abs(det) < 1e-5) continue;
    for (let row = top; row <= bottom; row++) {
      const v = row + .5 - a.v;
      for (let col = left; col <= right; col++) {
        const u = col + .5 - a.u;
        const wb = (u * cv - v * cu) / det;
        const wc = (v * bu - u * bv) / det;
        const wa = 1 - wb - wc;
        if (wa < -1e-5 || wb < -1e-5 || wc < -1e-5) continue;
        const depth = wa * a.depth + wb * b.depth + wc * c.depth;
        const context = vein || (plane && depth < plane.origin + plane.dx * (col + .5) + plane.dy * (row + .5));
        const i = (row - y) * width + col - x;
        const s = wa * a.s + wb * b.s + wc * c.s;
        if (context) {
          if ((vein || solid) && depth < contextDepth[i]) {
            contextDepth[i] = depth;
            contextPixels[i] = vein ? rgba(25 + s * 40, 41 + s * 45, 54 + s * 53)
              : rgba(47 + s * 91, 35 + s * 51, 44 + s * 52);
          }
        } else if ((plane || solid) && depth < opaqueDepth[i]) {
          opaqueDepth[i] = depth;
          pixels[i] = solid ? rgba(26 + s * 209, 17 + s * 133, 18 + s * 133)
            : rgba(14 + 16 * s, 48 + s * 55, 52 + s * 53);
        }
      }
    }
  }
}

function cutSurface(record, acq, camera, plane, target) {
  const {x, y, width, height} = viewport;
  const {pixels, opaqueDepth} = target;
  const {right, down, away} = camera;
  const transverse = acq.long ? null : tubesAt(record, null, acq.z).filter(v => v.color > 0);
  // A cap sample is the exact world-space intersection of a view ray and the active scan plane.
  const steps = right.map((value, axis) => value / scale + away[axis] * plane.dx);
  const rows = down.map((value, axis) => value / scale + away[axis] * plane.dy);
  const origin = worldCenter.map((value, axis) => value
    - right[axis] * screenCenter[0] / scale - down[axis] * screenCenter[1] / scale + away[axis] * plane.origin);
  const slices = new Map();
  for (let row = y; row < y + height; row++) {
    let wx = origin[0] + rows[0] * (row + .5) + steps[0] * (x + .5);
    let wy = origin[1] + rows[1] * (row + .5) + steps[1] * (x + .5);
    let wz = origin[2] + rows[2] * (row + .5) + steps[2] * (x + .5);
    let depth = plane.origin + plane.dy * (row + .5) + plane.dx * (x + .5);
    for (let col = x; col < x + width; col++) {
      if (Math.abs(wx) < 26 && wy > 24 && wy < 70 && wz >= -1e-5 && wz <= aorticLength + 1e-5) {
        let tubes = transverse;
        if (!tubes) {
          const slice = Math.round(wz * 4);
          if (!slices.has(slice)) slices.set(slice, tubesAt(record, null, slice / 4).filter(v => v.color > 0));
          tubes = slices.get(slice);
        }
        const i = (row - y) * width + col - x;
        const tissue = classifyTissue(wx, wy, tubes);
        if (depth < opaqueDepth[i] + .12) {
          if (tissue.region === 'wall') pixels[i] = rgba(249, 176, 119);
          if (tissue.region === 'mural') {
            const texture = Math.sin(wx * 2.3 + wy * 4.4 + wz * .6) * 4;
            pixels[i] = rgba(172 + texture, 100 + texture, 176 + texture);
          }
          if (tissue.region === 'lumen') {
            const recess = Math.min(1, Math.max(0, opaqueDepth[i] - depth) / 13);
            pixels[i] = rgba(25 - 12 * recess, 111 - 49 * recess, 105 - 42 * recess);
          }
        }
      }
      wx += steps[0];
      wy += steps[1];
      wz += steps[2];
      depth += plane.dx;
    }
  }
}

export function drawAorticAnatomy(ctx, record, acq, axes, camera) {
  const target = buffers(ctx);
  target.opaqueDepth.fill(Infinity);
  target.contextDepth.fill(Infinity);
  target.pixels.fill(0);
  target.contextPixels.fill(background);
  const plane = acq.blind ? null : capPlane(camera, acq, axes);
  for (const mesh of aorticSurfaces(record)) drawTriangles(mesh, camera, plane, target);
  if (plane) cutSurface(record, acq, camera, plane, target);
  for (let i = 0; i < target.pixels.length; i++) target.pixels[i] ||= target.contextPixels[i];
  ctx.putImageData(target.image, viewport.x, viewport.y);
}
