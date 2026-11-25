// All distances are in millimetres: x patient left, y depth, z sweep direction.
// z runs caudally for the aorta and cranially for each carotid.
export const split = 170;
export const sacPeak = 106;
export const plaquePeak = 77;
export const distalICA = 119;
export const stations = {
  'proximal-cca': {label: 'Proximal CCA', vessel: 'CCA', z: 21},
  'distal-cca': {label: 'Distal CCA', vessel: 'CCA', z: 48},
  'proximal-ica': {label: 'Proximal ICA', vessel: 'ICA', z: 77},
  'distal-ica': {label: 'Distal ICA', vessel: 'ICA', z: distalICA},
  eca: {label: 'ECA', vessel: 'ECA', z: 84},
  vertebral: {label: 'Vertebral artery', vessel: 'VA', z: 40},
  before: {label: 'Before the stenosis', vessel: 'ICA', z: 68},
  jet: {label: 'At the proximal ICA stenosis', vessel: 'ICA', z: plaquePeak},
  beyond: {label: 'Just beyond the stenosis', vessel: 'ICA', z: 91},
};

const velocities = {
  Right: [[87, 17, 55], [72, 16, 58], [84, 26, 55], [79, 28, 58], [94, 9, 56], [44, 13, 54]],
  Left: [[91, 19, 54], [76, 17, 56], [92, 29, 58], [86, 27, 57], [103, 10, 56], [49, 14, 53]],
};
const focalVelocities = [[94, 27, 56], [207, 67, 58], [122, 39, 58]];

export function lerp(start, end, progress) {
  return start + (end - start) * progress;
}

function smooth(t) {
  const p = Math.min(1, Math.max(0, t));
  return p * p * (3 - 2 * p);
}

function profile(z, knots) {
  for (let i = 1; i < knots.length; i++) {
    const [nextZ, nextValue] = knots[i];
    if (z <= nextZ) {
      const [previousZ, previousValue] = knots[i - 1];
      return lerp(previousValue, nextValue, smooth((z - previousZ) / (nextZ - previousZ)));
    }
  }
  return knots.at(-1)[1];
}

function tube(name, x, y, rx, ry, wall, color = 1, lumen = {}) {
  return {
    name, x, y, rx, ry, color,
    lx: x + (lumen.dx ?? 0), ly: y + (lumen.dy ?? 0),
    lrx: lumen.rx ?? rx - wall, lry: lumen.ry ?? ry - wall,
    wall, mural: lumen.mural,
  };
}

function aorticTrunk(positive, z) {
  const ap = positive ? profile(z, [[3, 24], [55, 21], [77, 24], [sacPeak, 43], [145, 22], [165, 18]])
    : profile(z, [[3, 24], [60, 19], [142, 17], [165, 16]]);
  const width = positive ? profile(z, [[3, 25], [55, 22], [77, 25], [sacPeak, 46], [145, 23], [165, 19]])
    : profile(z, [[3, 23], [60, 19], [142, 17], [165, 17]]);
  const thrombus = positive ? profile(z, [[77, 0], [sacPeak, 1], [145, 0]]) : 0;
  return tube('Aorta', 0, 47, width / 2, ap / 2, 1, 1, {
    mural: thrombus > .001 ? 'Mural thrombus' : undefined,
    dx: thrombus * 1.8, dy: thrombus * -4.9,
    rx: width / 2 - 1 - thrombus * 4.7,
    ry: ap / 2 - 1 - thrombus * 7.5,
  });
}

function abdominalTubes(record, z) {
  const positive = record.kind === 'abnormal';
  const aorta = [];
  const forkStart = split - 14;
  const trunk = aorticTrunk(positive, z);
  if (z <= forkStart) aorta.push(trunk);
  else {
    // The two lobes start coincident with the same artery and diverge continuously.
    // The union changes from a single opening to two, with no central tube ending at the fork.
    const opening = smooth((z - forkStart) / 33);
    const separation = lerp(0, 18, opening);
    const depth = trunk.y + 2 * smooth((z - split) / 26);
    const lobes = [[-1, 'Right common iliac', positive ? 13 : 11],
      [1, 'Left common iliac', positive ? 12 : 10]].map(([sign, name, diameter]) => {
      return tube(name, sign * separation, depth, lerp(trunk.rx, diameter / 2, opening),
        lerp(trunk.ry, diameter / 2, opening), lerp(trunk.wall, .75, opening));
    });
    const lumenConnected = 2 * separation <= lobes[0].lrx + lobes[1].lrx;
    for (const lobe of lobes) {
      aorta.push(lumenConnected ? {...lobe, name: 'Aorta'} : lobe);
    }
  }
  if (z < 144) aorta.push(tube('IVC', -31, 49, 8, 5.5, .6, -1));
  return aorta;
}

function carotidTubes(record, side, z) {
  const sign = side === 'Right' ? -1 : 1;
  const vessels = [];
  if (z <= 64) {
    const bulb = smooth((z - 47) / 12);
    const taper = 1 - .42 * smooth((z - 58) / 6);
    vessels.push(tube('CCA', sign * 1.2, 19, (3.7 + bulb * 1.1) * taper,
      (3.6 + bulb) * taper, .5));
  }
  if (z >= 57) {
    const fork = smooth((z - 57) / 27);
    const rx = profile(z, [[57, 3.4], [66, 4.05], [77, 3.68], [93, 3.54], [119, 3.55]]);
    const ry = profile(z, [[57, 3.5], [67, 4.06], [77, 3.9], [94, 3.55]]);
    const plaque = side === 'Right' && record.kind === 'abnormal'
      ? profile(z, [[65, 0], [69, .24], [plaquePeak, 1], [86, .32], [93, 0]]) : 0;
    const deepICA = record.kind === 'limited' && side === 'Left' ? 7 * smooth((z - 101) / 21) : 0;
    vessels.push(tube('ICA', sign * (1.2 + 4.4 * fork), 19 + 2.3 * fork + deepICA, rx, ry, .5, 1, {
      mural: plaque > .001 ? 'Carotid plaque' : undefined,
      dy: -1.3 * plaque, rx: rx - .5 - 1.55 * plaque, ry: ry - .5 - 2.05 * plaque,
    }));
    vessels.push(tube('ECA', sign * (1.2 - 6.5 * fork), 18.7 - 3.2 * fork, 2.5, 2.45, .42));
  }
  if (z < 101) vessels.push(tube('IJV', sign * 13, 18.7, 4.1, 3.2, .45, -1));
  vessels.push(tube('VA', sign * 14, 35, 1.85, 1.75, .36));
  return vessels;
}

export function tubesAt(record, side, z) {
  return record.family === 'aaa' ? abdominalTubes(record, z) : carotidTubes(record, side, z);
}

export function ellipseFactor(x, y, cx, cy, rx, ry) {
  return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2;
}

function isMural(vessel, outerFactor) {
  return vessel.mural && outerFactor <= (1 - vessel.wall / Math.max(vessel.rx, vessel.ry)) ** 2;
}

export function classifyTissue(x, y, tubes) {
  let region = 'tissue';
  let vessel;
  for (const candidate of tubes) {
    if (Math.abs(x - candidate.x) > candidate.rx || Math.abs(y - candidate.y) > candidate.ry) continue;
    const outer = ellipseFactor(x, y, candidate.x, candidate.y, candidate.rx, candidate.ry);
    if (outer > 1) continue;
    if (ellipseFactor(x, y, candidate.lx, candidate.ly, candidate.lrx, candidate.lry) <= 1) {
      return {region: 'lumen', vessel: candidate};
    }
    if (!isMural(candidate, outer)) region = 'wall';
    else if (region !== 'wall') region = 'mural';
    vessel = candidate;
  }
  return {region, vessel};
}

export function getTube(record, side, z, name) {
  return tubesAt(record, side, z).find(vessel => vessel.name === name);
}

export function velocityAt(record, side, vessel, z) {
  const entries = Object.entries(stations).slice(0, 6);
  const profileSamples = entries.flatMap(([id, station], index) =>
    station.vessel === vessel ? [{z: station.z, values: velocities[side][index]}] : []);
  if (record.kind === 'abnormal' && side === 'Right' && vessel === 'ICA') {
    profileSamples.shift();
    ['before', 'jet', 'beyond'].forEach((id, i) => {
      profileSamples.push({z: stations[id].z, values: focalVelocities[i]});
    });
  }
  profileSamples.sort((a, b) => a.z - b.z);
  return [0, 1, 2].map(i => profile(z, profileSamples.map(point => [point.z, point.values[i]])));
}

export function framePosition(chapter, frame) {
  const at = Math.min(Math.max(0, frame), chapter.frames - 1);
  if (at <= chapter.evidenceFrame) {
    return lerp(chapter.start, chapter.key, at / chapter.evidenceFrame);
  }
  return lerp(chapter.key, chapter.end, (at - chapter.evidenceFrame) / (chapter.frames - chapter.evidenceFrame - 1));
}

export function getAcquisition(record, chapter, frame) {
  const z = framePosition(chapter, frame);
  const target = chapter.target && getTube(record, chapter.side, z, chapter.target);
  const signed = record.family === 'aaa' ? 1 : chapter.side === 'Right' ? -1 : 1;
  const position = frame / (chapter.frames - 1);
  const search = Math.sin((position - chapter.evidenceFrame / (chapter.frames - 1)) * Math.PI);
  const targetX = target?.x ?? (record.family === 'aaa' ? 0 : signed * 1.2);
  const lateralOffset = chapter.window === 'lateral' ? 45 : chapter.window === 'posterolateral' ? signed * 8 : 0;
  const angle = chapter.window === 'lateral' ? -.56 : chapter.window === 'posterolateral' ? -signed * .31 : 0;
  const anchorX = targetX + lateralOffset;
  return {
    z, target, anchorX, angle, search,
    width: record.family === 'aaa' ? (chapter.mode === 'long' ? 184 : 104) : chapter.mode === 'short' ? 52 : 66,
    depth: record.family === 'aaa' ? 78 : 45,
    long: chapter.mode !== 'short',
    blind: chapter.blind === 'distal-aorta' || (chapter.blind === 'high-ica' && z >= 108),
    gate: chapter.mode === 'pw' && target ? {x: target.lx, y: target.ly + search * target.lry * 1.24} : null,
  };
}

export function getDopplerSample(record, chapter, frame, acquisition = getAcquisition(record, chapter, frame)) {
  const {gate, target, z, blind} = acquisition;
  if (!gate || blind || Math.abs(gate.y - target.ly) >= target.lry) return null;
  const [psv, edv, angle] = velocityAt(record, chapter.side, target.name, z);
  const radial = (gate.y - target.ly) / target.lry;
  const attenuation = 1 - radial * radial * .39;
  return {psv: psv * attenuation, edv: edv * attenuation, angle, disturbed:
    record.kind === 'abnormal' && chapter.side === 'Right' && target.name === 'ICA' && z >= 75 && z <= 100};
}

export function measure(record, chapter, frame, acquisition = getAcquisition(record, chapter, frame)) {
  const {target, blind, z} = acquisition;
  if (!chapter.caliper || blind || !target) return [];
  if (chapter.caliper === 'lumen') {
    return [{z, x: target.lx, lo: target.ly - target.lry, hi: target.ly + target.lry}];
  }
  const ap = {z, x: target.x, lo: target.y - target.ry, hi: target.y + target.ry};
  return chapter.caliper === 'both'
    ? [ap, {z, y: target.y, lo: target.x - target.rx, hi: target.x + target.rx, transverse: true}]
    : [ap];
}
