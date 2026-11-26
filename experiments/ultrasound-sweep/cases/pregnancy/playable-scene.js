import * as THREE from '../../vendor/build/three.module.js';
import { loadSweepPart, sweepConfig } from '../../case-scene.js';
import { chapters, planeAt, rasterParameters } from './playable.js';
import { refineSurface } from './playable-surface-refinement.js';
import { add, cross, dot, ectopicYolk, fluidPocketRadius, landmarks, mul, nativeBiometryAxes, patientEnvelope, sampler, sub, unit, volumeFor } from './playable-model.js';

const stageSweeps = {
  early: 'pregnancy-early',
  first: 'pregnancy-fetus',
  mid: 'pregnancy-mid-brain',
  late: 'pregnancy-late-presentation',
};
const identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
const tissues = [
  ['Uterus', '#bd778d', 0.18, ['uterus', 'cervix', 'cervical_canal']],
  ['Amniotic and gestational fluid', '#61b2c3', 0.11, ['amniotic_fluid', 'amniotic_cavity', 'gestational_sac', 'tubal sac']],
  ['Placenta', '#aa82b4', 0.87, ['placenta']],
  ['Fetal surface', '#edbf91', 0.59, ['fetus', 'embryo', 'posterior skin', 'abdominal skin']],
  ['Skeleton', '#ffedbf', 0.96, ['calvarium', 'calvarial contour', 'nasal_bone', 'spine', 'spinal_echoes',
    'femur', 'ossified shaft', 'forearm / lower-leg bones']],
  ['Heart and great vessels', '#cf758c', 0.91, ['heart', 'model heart', 'cardiac_region', 'right_atrium',
    'left_atrium', 'right_ventricle', 'left_ventricle', 'aortic_outflow', 'pulmonary_outflow', 'superior_vena_cava']],
  ['Umbilical cord', '#7cc8a0', 0.90, ['cord', 'umbilical_cord', 'umbilical_arteries', 'umbilical_vein']],
  ['Bladder', '#68b5c4', 0.55, ['maternal_bladder', 'fetal_bladder']],
  ['Adnexa and sac wall', '#d08a84', 0.82, ['ovary', 'tubal wall', 'gestational_rim']],
  ['Yolk sac', '#ead85f', 0.94, ['yolk_sac', 'ectopic yolk sac']],
  ['Fluid pocket', '#60c8e4', 0.49, ['nearest fluid', 'cul-de-sac fluid', 'NT space']],
  ['Fetal viscera', '#d293a0', 0.68, ['lungs', 'stomach', 'first stomach', 'kidneys', 'diaphragm']],
  ['Fluid pocket boundary', '#d5cd87', 0.40, ['maternal interface']],
];
const edges = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]];
const corners = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]];
const refinedLabels = new Set(['Uterus', 'Amniotic and gestational fluid', 'Placenta', 'Fetal surface', 'Bladder', 'Fetal viscera']);
const overviewLabels = new Set(['Uterus', 'Fetal surface', 'Placenta', 'Umbilical cord']);

function coordinates(volume) {
  const [right, anterior] = volume.axes ?? identity;
  const r = unit(right);
  const a = unit(sub(anterior, mul(r, dot(anterior, r))));
  const axes = [r, a, cross(r, a)];
  const origin = volume.maternalCentre ?? [0, 0, 0];
  return {
    vector: (v) => axes.map((row) => dot(row, v)),
    point: (v) => axes.map((row, i) => dot(row, v) + origin[i]),
    local: (v) => axes[0].map((_, column) => axes.reduce((sum, row, i) =>
      sum + row[column] * (v[i] - origin[i]), 0)),
  };
}

function mesh(geometry, label, color, opacity) {
  const material = new THREE.MeshStandardMaterial({
    color, opacity, transparent: opacity < 1, depthWrite: opacity >= 0.5,
    side: THREE.DoubleSide, roughness: 0.8,
  });
  const part = new THREE.Mesh(geometry, material);
  part.name = label;
  return part;
}

function sampledAnatomy(volume, model) {
  const step = Math.max(1.25, volume.spacing * 1.5);
  const origin = volume.origin.map((value) => value - step);
  const size = volume.size.map((count) => Math.ceil((count - 1) * volume.spacing / step) + 3);
  const [nx, ny, nz] = size;
  const field = new Uint16Array(nx * ny * nz);
  const classification = new Uint16Array(model.names.length);
  tissues.forEach(([, , , labels], index) => {
    for (const label of labels) {
      const id = model.ids[label];
      if (id) classification[id] |= 1 << index;
    }
  });
  // Internal tissues are part of the fetal volume as well as separately
  // visible structures. They must not leave artificial holes in the skin.
  const fetus = 1 << tissues.findIndex(([label]) => label === 'Fetal surface');
  const internalGroups = new Set(['Skeleton', 'Heart and great vessels', 'Fetal viscera']);
  const internal = tissues.filter(([label]) => internalGroups.has(label)).flatMap(([, , , labels]) => labels);
  for (const name of [...internal,
    'fetal_bladder', 'orbits', 'falx', 'ventricles', 'choroid', 'choroid_plexus',
    'cavum', 'thalami', 'cerebellum', 'cisterna_magna', 'upper_lip', 'nares', 'hands', 'feet']) {
    if (model.ids[name]) classification[model.ids[name]] |= fetus;
  }
  let present = 0;
  for (let z = 1; z < nz - 1; z++) {
    for (let y = 1; y < ny - 1; y++) {
      for (let x = 1; x < nx - 1; x++) {
        const source = model.scan(origin[0] + x * step, origin[1] + y * step, origin[2] + z * step);
        const group = classification[source];
        if (group) {
          field[(z * ny + y) * nx + x] = group;
          present |= group;
        }
      }
    }
  }
  return { step, origin, size, field, present };
}

function sampledPocket(model, l) {
  if (!l.fluid || !Number.isFinite(l.shape.dvp)) return null;
  // Re-evaluate the case labels in a tight physical box instead of smoothing
  // across the boundary between fluid and adjacent sampled tissues.
  const step = 0.9;
  const extent = l.vertical.map((axis) => Math.abs(axis) * (l.shape.dvp / 2 + 5) + 14);
  const origin = l.fluid.map((value, axis) => value - extent[axis]);
  const size = extent.map((radius) => Math.ceil(2 * radius / step) + 1);
  const [nx, ny, nz] = size;
  const field = new Uint16Array(nx * ny * nz);
  const pocket = model.ids['nearest fluid'];
  const boundary = model.ids['maternal interface'];
  for (let z = 1; z < nz - 1; z++) {
    for (let y = 1; y < ny - 1; y++) {
      for (let x = 1; x < nx - 1; x++) {
        const id = model.scan(origin[0] + x * step, origin[1] + y * step, origin[2] + z * step);
        if (id === pocket || id === boundary) field[(z * ny + y) * nx + x] = id === pocket ? 1 : 2;
      }
    }
  }
  return { step, origin, size, field };
}

function surface(grid, label, transform) {
  const { step, origin, size: [nx, ny, nz], field } = grid;
  const stride = nx * ny;
  const offsets = [0, 1, nx, nx + 1, stride, stride + 1, stride + nx, stride + nx + 1];
  const lookup = new Int32Array(field.length).fill(-1);
  const vertices = [];
  const faces = [];
  const directions = [[1, nx, stride, 1, 2], [nx, stride, 1, 2, 0], [stride, 1, nx, 0, 1]];
  for (let z = 0; z < nz - 1; z++) {
    for (let y = 0; y < ny - 1; y++) {
      for (let x = 0; x < nx - 1; x++) {
        const index = z * stride + y * nx + x;
        let mask = 0;
        for (let bit = 0; bit < 8; bit++) {
          if (field[index + offsets[bit]] & label) mask |= 1 << bit;
        }
        if (mask === 0 || mask === 255) continue;
        const centre = [0, 0, 0];
        let count = 0;
        for (const [a, b] of edges) {
          if ((mask >> a & 1) === (mask >> b & 1)) continue;
          for (let axis = 0; axis < 3; axis++) centre[axis] += (corners[a][axis] + corners[b][axis]) / 2;
          count++;
        }
        const current = vertices.length / 3;
        lookup[index] = current;
        const coordinate = [x, y, z];
        vertices.push(...transform(coordinate.map((value, axis) => origin[axis] + (value + centre[axis] / count) * step)));
        for (const [forward, lateral, vertical, u, v] of directions) {
          if (coordinate[u] === 0 || coordinate[v] === 0) continue;
          const inside = Boolean(field[index] & label);
          if (inside === Boolean(field[index + forward] & label)) continue;
          const a = lookup[index - lateral];
          const b = lookup[index - lateral - vertical];
          const c = lookup[index - vertical];
          if (a === undefined || b === undefined || c === undefined || Math.min(a, b, c) < 0) continue;
          if (inside) faces.push(current, a, b, current, b, c);
          else faces.push(current, c, b, current, b, a);
        }
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(faces);
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  return geometry;
}

async function fitSkin(record, stage, transform) {
  const id = stageSweeps[stage];
  const config = sweepConfig(id);
  if (!config) throw new Error('Maternal exterior is unavailable for ' + stage);
  const nativeScale = config.voxelMm ?? 1.5;
  const geometry = await loadSweepPart(id);
  const vertices = geometry.attributes.position;
  const envelope = patientEnvelope(stage);
  const contacts = chapters(record).filter((chapter) => !chapter.vaginal).flatMap((chapter) =>
    [0, chapter.evidenceFrame, chapter.frames - 1].map((frame) => unit(planeAt(chapter, frame).contact
      .map((value, axis) => (value - envelope.centre[axis]) / envelope.radii[axis]))));

  // Keep the stage torso's shape away from the contact paths. Locally seat the
  // native surface against the envelope already used by the acquisition recipe.
  for (let i = 0; i < vertices.count; i++) {
    const native = [vertices.getX(i), vertices.getY(i), vertices.getZ(i)].map((value) => value * nativeScale);
    const relative = transform.local(native).map((value, axis) =>
      (value - envelope.centre[axis]) / envelope.radii[axis]);
    const length = Math.hypot(...relative);
    const direction = relative.map((value) => value / (length || 1));
    let nearest = -1;
    for (const [x, y, z] of contacts) nearest = Math.max(nearest, x * direction[0] + y * direction[1] + z * direction[2]);
    const blend = THREE.MathUtils.smoothstep(nearest, 0.90, 0.982);
    if (blend === 0) {
      vertices.setXYZ(i, ...native);
      continue;
    }
    const fitted = THREE.MathUtils.lerp(length, 1, blend);
    vertices.setXYZ(i, ...transform.point(direction.map((value, axis) =>
      envelope.centre[axis] + value * envelope.radii[axis] * fitted)));
  }
  vertices.needsUpdate = true;
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return mesh(geometry, 'Maternal exterior', '#bb8d76', 0.25);
}

async function registeredPart(sweep, part) {
  try {
    const catalog = sweepConfig(sweep);
    if (!catalog) return null;
    const geometry = await loadSweepPart(sweep, part);
    const scale = catalog.voxelMm ?? 1.5;
    geometry.scale(scale, scale, scale);
    return geometry;
  } catch (error) {
    console.warn('Registered pregnancy part unavailable; using case labels.', error);
    return null;
  }
}

async function fetalExterior(stage, kind, l, transform) {
  if (stage === 'early' && kind === 'normal') {
    const geometry = await registeredPart(stageSweeps.early, 'embryo');
    if (!geometry) return null;
    const min = geometry.boundingBox.min.z;
    const max = geometry.boundingBox.max.z;
    const scale = (l.crown[2] - l.rump[2]) / (max - min);
    return geometry.scale(1, 1, scale).translate(0, 0, l.rump[2] - min * scale);
  }
  if (stage === 'first' && kind === 'normal') {
    const geometry = await registeredPart(stageSweeps.first, 'fetus');
    return geometry?.scale(1, 1, l.scale) ?? null;
  }
  const nativeAxes = nativeBiometryAxes[stage];
  if (!nativeAxes || l.omphalocele) return null;
  const geometry = await registeredPart(stageSweeps[stage], 'fetus');
  if (geometry) {
    const vertices = geometry.attributes.position;
    const distal = (l.limbs ?? []).flatMap((limb) => limb.slice(-2));
    const bands = [
      { centre: l.head, measured: l.hcAxes, native: nativeAxes.head, inner: 8, outer: stage === 'late' ? 31 : 21 },
      { centre: l.abdomen, measured: l.acAxes, native: nativeAxes.abdomen, inner: 6, outer: stage === 'late' ? 42 : 17 },
    ];
    for (let i = 0; i < vertices.count; i++) {
      const local = transform.local([vertices.getX(i), vertices.getY(i), vertices.getZ(i)]);
      let distance = Infinity;
      for (const [x, y, z] of distal) distance = Math.min(distance, Math.hypot(local[0] - x, local[1] - y, local[2] - z));
      const protectedWeight = THREE.MathUtils.smoothstep(distance, 8, 13);
      for (const { centre, measured, native, inner, outer } of bands) {
        const radial = Math.hypot((local[0] - centre[0]) / native[0], (local[1] - centre[1]) / native[1]);
        const weight = protectedWeight * (1 - THREE.MathUtils.smoothstep(radial, 1.25, 1.6))
          * (1 - THREE.MathUtils.smoothstep(Math.abs(local[2] - centre[2]), inner, outer));
        for (let axis = 0; axis < 2; axis++) {
          local[axis] += (local[axis] - centre[axis]) * (measured[axis] / native[axis] - 1) * weight;
        }
      }
      vertices.setXYZ(i, ...transform.point(local));
    }
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
  }
  return geometry;
}

function closedRoundSurface(sides, rings, layers) {
  const points = [];
  const faces = [];
  for (const [map, invert] of layers) {
    const north = points.length / 3;
    const south = north + 1 + (rings - 1) * sides;
    const ring = (latitude, longitude) => north + 1 + (latitude - 1) * sides + longitude % sides;
    const face = (a, b, c) => faces.push(a, invert ? c : b, invert ? b : c);
    points.push(...map([0, 1, 0]));
    for (let latitude = 1; latitude < rings; latitude++) {
      const pitch = Math.PI * latitude / rings;
      for (let longitude = 0; longitude < sides; longitude++) {
        const angle = 2 * Math.PI * longitude / sides;
        const radial = Math.sin(pitch);
        points.push(...map([radial * Math.cos(angle), Math.cos(pitch), radial * Math.sin(angle)]));
        const here = ring(latitude, longitude);
        const next = ring(latitude, longitude + 1);
        if (latitude === 1) face(north, next, here);
        if (latitude === rings - 1) face(here, next, south);
        else {
          const below = ring(latitude + 1, longitude);
          face(here, next, below);
          face(next, ring(latitude + 1, longitude + 1), below);
        }
      }
    }
    points.push(...map([0, -1, 0]));
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));
  geometry.setIndex(faces);
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  return geometry;
}

function ectopicShell() {
  return closedRoundSurface(22, 14, [[ectopicYolk.outer, false], [ectopicYolk.inner, true]]
    .map(([radius, invert]) => [(point) => add(ectopicYolk.centre, mul(point, radius)), invert]));
}

function verifiedFluidExterior(model, l, transform) {
  if (!l.fluid || !Number.isFinite(l.shape.dvp)) return null;
  const vertical = unit(l.vertical);
  const across = unit(cross(vertical, [1, 0, 0]));
  const out = cross(across, vertical);
  const map = ([x, y, z]) => add(l.fluid, add(mul(vertical, y * l.shape.dvp / 2),
    add(mul(across, x * fluidPocketRadius), mul(out, z * fluidPocketRadius))));
  for (let row = 0; row <= 20; row++) {
    const pitch = row / 20 * Math.PI;
    for (let column = 0; column < 32; column++) {
      const angle = column / 32 * Math.PI * 2;
      const direction = [Math.sin(pitch) * Math.cos(angle), Math.cos(pitch), Math.sin(pitch) * Math.sin(angle)];
      for (const radius of [0.3, 0.65, 0.985, 1.015]) {
        const inside = model.scan(...map(mul(direction, radius))) === model.ids['nearest fluid'];
        if (inside !== (radius < 1)) return null;
      }
    }
  }
  return closedRoundSurface(32, 20, [[(point) => transform(map(point)), false]]);
}

function addWallDefect(anatomy, defect, transform) {
  const points = [];
  const faces = [];
  const rings = 20;
  const sides = 40;
  for (let ring = 0; ring < rings; ring++) {
    for (let side = 0; side < sides; side++) {
      points.push(...transform(defect.membranePoint(ring / rings, side / sides * Math.PI * 2)));
      const a = ring * sides + side;
      const b = ring * sides + (side + 1) % sides;
      if (ring === rings - 1) faces.push(a, b, rings * sides);
      else faces.push(a, b, a + sides, b, b + sides, a + sides);
    }
  }
  points.push(...transform(defect.apex));
  const membrane = new THREE.BufferGeometry();
  membrane.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));
  membrane.setIndex(faces);
  membrane.computeVertexNormals();
  anatomy.add(mesh(membrane, 'Omphalocele membrane', '#ee92b7', 0.42));
  const bowel = new THREE.CatmullRomCurve3(defect.bowel.points.map((point) => new THREE.Vector3(...transform(point))));
  anatomy.add(mesh(new THREE.TubeGeometry(bowel, 40, defect.bowel.radius, 10), 'Herniated bowel', '#e8d064', 0.96));
}

function wallDefectCord(l, transform) {
  const proximal = l.omphalocele.cord;
  const joined = [...proximal.points, ...l.cord.slice(9)].map((point) => new THREE.Vector3(...transform(point)));
  const path = new THREE.CurvePath();
  for (let i = 1; i < joined.length; i++) path.add(new THREE.LineCurve3(joined[i - 1], joined[i]));
  const transition = path.getCurveLengths()[proximal.points.length - 2];
  const length = path.getLength();
  const stations = Math.ceil(length / 0.8);
  const sides = 14;
  const frames = path.computeFrenetFrames(stations, false);
  const positions = [];
  const indices = [];
  for (let i = 0; i <= stations; i++) {
    const t = i / stations;
    const p = path.getPointAt(t);
    // The distal radius is the authored mid-stage Gestation cord radius.
    const radius = THREE.MathUtils.lerp(proximal.radius, 3.65, THREE.MathUtils.smoothstep(t * length, transition, transition + 9));
    for (let j = 0; j < sides; j++) {
      const angle = j / sides * Math.PI * 2;
      positions.push(...p.clone().addScaledVector(frames.normals[i], radius * Math.cos(angle))
        .addScaledVector(frames.binormals[i], radius * Math.sin(angle)).toArray());
      if (i === stations) continue;
      const a = i * sides + j;
      const b = i * sides + (j + 1) % sides;
      indices.push(a, b, a + sides, b, b + sides, a + sides);
    }
  }
  const first = positions.length / 3;
  positions.push(...joined[0].toArray(), ...joined.at(-1).toArray());
  for (let j = 0; j < sides; j++) {
    const next = (j + 1) % sides;
    indices.push(first, next, j, first + 1, stations * sides + j, stations * sides + next);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  return geometry;
}

function fluidCalipers(transform) {
  const marker = new THREE.Group();
  const material = new THREE.MeshBasicMaterial({ color: '#ffe294', transparent: true, depthTest: false, depthWrite: false });
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 1, 8), material);
  const endpoint = new THREE.SphereGeometry(1.55, 12, 8);
  const a = new THREE.Mesh(endpoint, material);
  const b = new THREE.Mesh(endpoint, material);
  marker.add(shaft, a, b);
  marker.traverse((part) => { part.renderOrder = 10; });
  marker.visible = false;
  return {
    marker,
    update(chapter, frame) {
      const measurement = chapter.measure;
      marker.visible = frame === chapter.evidenceFrame && chapter.labels?.includes('nearest fluid') && measurement?.type === 'line';
      if (!marker.visible) return;
      a.position.fromArray(transform(measurement.a));
      b.position.fromArray(transform(measurement.b));
      const direction = b.position.clone().sub(a.position);
      shaft.position.copy(a.position).lerp(b.position, 0.5);
      shaft.scale.y = direction.length();
      shaft.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
    },
  };
}

export async function createCaseModel(record, chapter) {
  const { stage, kind } = chapter;
  const volume = volumeFor(stage);
  const transform = coordinates(volume);
  const l = landmarks(stage, kind);
  const source = sampler(stage, kind, l);
  const protectedPoints = (l.limbs ?? []).flatMap((limb) => limb.slice(-2).map((point) =>
    ({ point: transform.point(point), radius: 4 })));
  if (l.omphalocele) {
    protectedPoints.push({ point: transform.point(l.omphalocele.target), radius: 17 });
  }
  if (l.nuchal) protectedPoints.push({ point: transform.point(l.nuchal), radius: 7 });
  const cordSweep = { first: 'pregnancy-fetus', mid: 'pregnancy-mid-abdomen', late: 'pregnancy-late-presentation' }[stage];
  const [skin, fetal, placenta, cord] = await Promise.all([
    fitSkin(record, stage, transform),
    fetalExterior(stage, kind, l, transform),
    cordSweep ? registeredPart(stageSweeps[stage], 'placenta') : null,
    cordSweep && !l.omphalocele ? registeredPart(cordSweep, stage === 'first' ? 'umbilical_cord' : 'cord') : null,
  ]);
  const registered = new Map([['Fetal surface', fetal], ['Placenta', placenta], ['Umbilical cord', cord]]);
  if (stage === 'early' && kind === 'abnormal') registered.set('Yolk sac', ectopicShell());
  if (l.omphalocele) registered.set('Umbilical cord', wallDefectCord(l, transform.point));
  const verifiedPocket = verifiedFluidExterior(source, l, transform.point);
  if (verifiedPocket) registered.set('Fluid pocket', verifiedPocket);
  const anatomy = new THREE.Group();
  const grid = sampledAnatomy(volume, source);
  const pocketGrid = sampledPocket(source, l);
  const pocketEnds = pocketGrid
    ? [-1, 1].map((direction) => ({
      point: transform.point(add(l.fluid, mul(l.vertical, direction * l.shape.dvp / 2))),
      radius: 2,
    })) : [];
  const legend = [];
  tissues.forEach(([label, color, opacity, names], index) => {
    const mask = 1 << index;
    if (grid.present & mask) {
      const adopted = registered.get(label);
      const fluidMask = label === 'Fluid pocket' ? 1 : label === 'Fluid pocket boundary' ? 2 : 0;
      const localized = pocketGrid && fluidMask;
      const geometry = adopted || surface(localized ? pocketGrid : grid, localized ? fluidMask : mask, transform.point);
      if (localized && !adopted) refineSurface(geometry, pocketGrid.step, pocketEnds);
      else if (!adopted && refinedLabels.has(label)) refineSurface(geometry, grid.step, protectedPoints);
      anatomy.add(mesh(geometry, label, color, opacity));
      legend.push({ label, color, names });
    }
  });
  if (l.omphalocele) {
    addWallDefect(anatomy, l.omphalocele, transform.point);
    legend.push(
      { label: 'Omphalocele membrane', color: '#ee92b7', names: ['sac membrane'] },
      { label: 'Herniated bowel', color: '#e8d064', names: ['sac contents'] },
    );
  }
  const calipers = fluidCalipers(transform.point);
  anatomy.add(skin, calipers.marker);
  const pocket = anatomy.getObjectByName('Fluid pocket');
  const pocketBoundary = anatomy.getObjectByName('Fluid pocket boundary');
  if (pocket) pocket.material.depthWrite = false;
  let active;

  const envelope = patientEnvelope(stage);
  return {
    anatomy,
    skin,
    probeTypes: ['curved', 'endocavitary'],
    legend(section) {
      const key = legend.filter(({ label, names }) =>
        overviewLabels.has(label) || names.some((name) => section.labels?.includes(name)));
      const entries = key.map(({ label, color }) => ({ label, color }));
      if (section.labels?.includes('nearest fluid') && section.measure?.type === 'line') {
        entries.push({ label: 'Saved DVP calipers', color: '#ffe294' });
      }
      return entries;
    },
    radius: Math.max(envelope.radii[0], envelope.radii[2] * 0.89),
    dispose() {
      anatomy.traverse((part) => {
        part.geometry?.dispose();
        part.material?.dispose();
      });
    },
    update(section, frame) {
      if (section !== active) {
        const fluid = section.labels?.includes('nearest fluid');
        if (pocket) {
          pocket.material.opacity = fluid ? 0.8 : 0.49;
          pocket.renderOrder = fluid ? 4 : 0;
        }
        if (pocketBoundary) {
          pocketBoundary.material.opacity = fluid ? 0.56 : 0.40;
          pocketBoundary.renderOrder = fluid ? 5 : 0;
        }
        active = section;
      }
      calipers.update(section, frame);
      const { contact, target, beam, width } = planeAt(section, frame);
      const { spanX, spanY, halfAperture, tangent } = rasterParameters(section);
      const halfWidth = spanX / 2;
      const halfDepth = spanY / 2;
      const distance = dot(target, beam) - dot(contact, beam);
      const crop = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([x, y]) =>
        transform.point(add(target, add(mul(width, x * halfWidth), mul(beam, y * halfDepth)))));
      return {
        contact: transform.point(contact),
        width: transform.vector(width),
        beam: transform.vector(beam),
        depth: distance + halfDepth,
        probe: section.vaginal ? 'endocavitary' : 'curved',
        fieldWidth: 2 * halfAperture,
        halfAngle: THREE.MathUtils.radToDeg(Math.atan(tangent)),
        corners: crop,
      };
    },
  };
}
