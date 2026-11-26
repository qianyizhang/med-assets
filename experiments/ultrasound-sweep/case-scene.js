// Case adapters supply the same physical sample as their B-mode renderer in RAS millimetres.
// The player, probe assets and camera do not own acquisition or diagnostic state.
import * as THREE from './vendor/build/three.module.js';
import {
  curvedTransducer,
  imagingWireframe,
  linearCasing,
  linearTransducer,
  loadMesh,
  readAsset,
  rectangleGeometry,
  sectorGeometry,
  transformForFrame,
  viewport,
} from './scene.js';

export function sweepConfig(id) {
  return abdomenTours.find((entry) => entry.id === id);
}

export function loadSweepPart(id, name = 'torso') {
  const config = sweepConfig(id);
  if (!config) throw new Error('The fitted ' + id + ' anatomy is unavailable in this study.');
  const path =
    config.meshPaths?.[name] ??
    new URL('scenes/' + name + '.mesh', new URL(config.assetRoot, import.meta.url));
  return loadMesh(name, path);
}

const vector = (values) => new THREE.Vector3().fromArray(values);

function endocavitaryProbe() {
  const group = new THREE.Group();
  // Distal lens, narrow shaft and external handgrip, measured in the case scene's mm.
  for (const [color, profile] of [
    [
      '#243c40',
      [
        [0, 5, 4, 1],
        [2, 8, 7, 1],
        [8, 9, 8, 1],
      ],
    ],
    [
      '#e4ece7',
      [
        [8, 9, 8, 1],
        [16, 8, 7, 1],
        [75, 7, 7, 1],
        [94, 11, 10, 0.8],
        [112, 15, 12, 0.8],
        [152, 11, 9, 1],
        [158, 5, 5, 1],
      ],
    ],
  ])
    group.add(
      new THREE.Mesh(linearCasing(profile, 1), new THREE.MeshStandardMaterial({ color, roughness: 0.8 })),
    );
  return group;
}

function caseField(pose) {
  if (pose.probe === 'linear')
    return rectangleGeometry({ voxelMm: 1, fieldWidthMm: pose.fieldWidth, sectorDepthMm: pose.depth });
  if (pose.fieldWidth && !pose.lensRadius) {
    // Some acquisition recipes clip a flat-topped, widening field before cropping.
    const border = [],
      grid = [];
    const edge = pose.fieldWidth / 2;
    const far = edge + pose.depth * Math.tan(THREE.MathUtils.degToRad(pose.halfAngle));
    for (let i = -3; i <= 3; i++) {
      (Math.abs(i) === 3 ? border : grid).push((edge * i) / 3, 0, 0, (far * i) / 3, 0, -pose.depth);
    }
    for (let i = 0; i <= 4; i++) {
      const x = THREE.MathUtils.lerp(edge, far, i / 4);
      (i === 0 || i === 4 ? border : grid).push(-x, 0, (-pose.depth * i) / 4, x, 0, (-pose.depth * i) / 4);
    }
    return imagingWireframe(border, grid);
  }
  return sectorGeometry({
    voxelMm: 1,
    lensRadiusMm: pose.lensRadius ?? 0,
    sectorDepthMm: pose.depth,
    sectorHalfAngleDeg: pose.halfAngle,
  });
}

function framing(model, pose, probe) {
  const contact = vector(pose.contact),
    beam = vector(pose.beam).normalize();
  const aim = pose.corners
    ? pose.corners.reduce((v, p) => v.add(vector(p)), new THREE.Vector3()).multiplyScalar(0.25)
    : contact.clone().addScaledVector(beam, pose.depth * 0.55);
  const pivot = aim.clone();
  const points = [
    aim,
    contact,
    contact.clone().addScaledVector(beam, -probe),
    contact.clone().addScaledVector(beam, pose.depth),
  ];
  for (const p of pose.corners ?? []) points.push(vector(p));
  const farWidth =
    pose.probe === 'linear'
      ? pose.fieldWidth / 2
      : pose.fieldWidth && !pose.lensRadius
        ? pose.fieldWidth / 2 + pose.depth * Math.tan(THREE.MathUtils.degToRad(pose.halfAngle))
        : ((pose.lensRadius ?? 0) + pose.depth) * Math.sin(THREE.MathUtils.degToRad(pose.halfAngle));
  const lateral = vector(pose.width);
  const far = contact.clone().addScaledVector(beam, pose.depth);
  points.push(
    far.clone().addScaledVector(lateral, farWidth),
    far.clone().addScaledVector(lateral, -farWidth),
  );
  const extent = Math.min(model.radius, Math.max(85, pose.depth * 0.75));
  for (const direction of [
    [1, 0, 0],
    [-1, 0, 0],
    [0, 1, 0],
    [0, -1, 0],
    [0, 0, 1],
    [0, 0, -1],
  ]) {
    points.push(aim.clone().addScaledVector(vector(direction), extent));
  }
  function fit(direction, up) {
    direction.normalize();
    up.addScaledVector(direction, -direction.dot(up)).normalize();
    const right = up.clone().cross(direction);
    const box = new THREE.Box2().setFromPoints(points.map((p) => new THREE.Vector2(p.dot(right), p.dot(up))));
    const center = box.getCenter(new THREE.Vector2()),
      size = box.getSize(new THREE.Vector2());
    const target = pivot
      .clone()
      .addScaledVector(right, center.x - pivot.dot(right))
      .addScaledVector(up, center.y - pivot.dot(up));
    return { direction, up, target, halfWidth: size.x * 0.6 + 14, halfHeight: size.y * 0.6 + 14 };
  }
  // Keep the external window recognizable from an anterior (or posterior)
  // three-quarter view. A small offset normal to the fan exposes its face.
  const outward = beam.clone().negate();
  const side = Math.abs(outward.x) > 0.35 ? Math.sign(outward.x) : 1;
  const anterior = outward.y < -0.35 ? -1 : 1;
  const preferred = vector([0.68 * side, anterior, 0.6]);
  const normal = lateral.clone().cross(beam).normalize();
  if (normal.dot(preferred) < 0) normal.negate();
  // A face-on component keeps the fan readable. The outward component lets
  // the learner see the probe sitting on the surface rather than down its shaft.
  const oblique = normal
    .multiplyScalar(0.85)
    .addScaledVector(outward, 0.56)
    .addScaledVector(lateral, lateral.dot(preferred) < 0 ? -0.22 : 0.22);
  return {
    pivot,
    presets: {
      oblique: fit(oblique, vector([0, 0, 1])),
      axial: fit(vector([0, 0, -1]), vector([0, 1, 0])),
      coronal: fit(vector([0, 1, 0]), vector([0, 0, 1])),
      sagittal: fit(vector([-1, 0, 0]), vector([0, 0, 1])),
    },
  };
}

export async function createCaseScene(canvas, model, initialChapter, onViewPresetChange) {
  const start = model.update(initialChapter, initialChapter.evidenceFrame);
  const instruments = model.probeTypes ?? [start.probe];
  let dimensions, phasedTransducer;
  const curvedParts = {};
  if (instruments.includes('curved')) {
    dimensions = await readAsset('scenes/geometry.json', 'json');
    await Promise.all(['lens', 'housing', 'relief'].map(async (name) => {
      curvedParts[name] = await loadMesh(name);
    }));
  }
  if (instruments.includes('phased')) {
    ({ phasedTransducer } = await import('./cardiac/torso/torso-view.js'));
  }
  const rig = new THREE.Group(),
    fieldMount = new THREE.Group(),
    probeMount = new THREE.Group();
  rig.add(probeMount, fieldMount);
  const probes = new Map();
  function instrument(pose) {
    const key = pose.probe === 'linear' ? 'linear-' + (pose.probeWidth ?? pose.fieldWidth) : pose.probe;
    if (!probes.has(key)) {
      let mesh;
      switch (pose.probe) {
        case 'curved':
          mesh = curvedTransducer(curvedParts, dimensions);
          mesh.scale.setScalar(dimensions.voxelMm);
          break;
        case 'linear':
          mesh = linearTransducer({ voxelMm: 1, fieldWidthMm: pose.probeWidth ?? pose.fieldWidth });
          break;
        case 'phased':
          mesh = phasedTransducer();
          mesh.rotation.x = Math.PI / 2;
          break;
        case 'endocavitary':
          mesh = endocavitaryProbe();
          break;
        default:
          throw Error('Unknown acquisition probe: ' + pose.probe);
      }
      if (pose.probe !== 'phased') {
        const z = pose.probe === 'endocavitary' ? 158 : pose.probe === 'linear' ? 84 : 60;
        const cord = new THREE.CatmullRomCurve3([
          vector([0, 0, z]),
          vector([0, 0, z + 12]),
          vector([-18, 6, z + 25]),
          vector([-38, 14, z + 16]),
        ]);
        mesh.add(
          new THREE.Mesh(
            new THREE.TubeGeometry(cord, 20, 1.6, 8, false),
            new THREE.MeshStandardMaterial({ color: '#263537', roughness: 0.9 }),
          ),
        );
      }
      probes.set(key, mesh);
      probeMount.add(mesh);
    }
    for (const [id, mesh] of probes) mesh.visible = id === key;
  }

  const lensHeight = (pose) => (pose.probe === 'endocavitary' ? 158 : pose.probe === 'phased' ? 72 : 84);
  const { pivot, presets } = framing(model, start, lensHeight(start));
  const view = viewport(canvas, { pivot, presets, shadowTarget: pivot, onViewPresetChange });
  const crop = new THREE.LineLoop(
    new THREE.BufferGeometry(),
    new THREE.LineBasicMaterial({ color: '#f7cf81', depthTest: false }),
  );
  crop.geometry.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(12), 3));
  crop.frustumCulled = false;
  view.scene.add(model.anatomy, rig, crop);
  let previousChapter = initialChapter,
    fieldKey;
  function setFrame(chapter, frame) {
    if (chapter !== previousChapter) {
      const reference = model.update(chapter, chapter.evidenceFrame);
      const next = framing(model, reference, lensHeight(reference));
      view.reframe(next.pivot, next.presets);
      previousChapter = chapter;
    }
    const pose = model.update(chapter, frame);
    const { position, orientation } = transformForFrame(pose);
    instrument(pose);
    const key = [pose.probe, pose.fieldWidth, pose.depth, pose.lensRadius, pose.halfAngle].join('/');
    if (fieldKey !== key) {
      fieldMount.traverse((obj) => {
        obj.geometry?.dispose();
        obj.material?.dispose();
      });
      fieldMount.clear();
      fieldMount.add(caseField(pose));
      fieldKey = key;
    }
    rig.position.copy(position);
    rig.quaternion.copy(orientation);
    crop.visible = Boolean(pose.corners);
    if (pose.corners) {
      const points = crop.geometry.getAttribute('position');
      pose.corners.forEach((point, i) => points.setXYZ(i, ...point));
      points.needsUpdate = true;
    }
    view.invalidate();
  }
  function setSkinOpacity(opacity) {
    model.skin.visible = opacity > 0;
    model.skin.traverse((obj) => {
      if (!obj.isMesh) return;
      obj.material.opacity = opacity;
      obj.material.transparent = opacity < 1;
      obj.material.depthWrite = opacity === 1;
      obj.material.needsUpdate = true;
    });
    view.invalidate();
  }
  setSkinOpacity(0.32);
  return {
    setFrame,
    setSkinOpacity,
    setViewPreset: view.setViewPreset,
    legend: (chapter) => (typeof model.legend === 'function' ? model.legend(chapter) : (model.legend ?? [])),
    dispose() {
      model.dispose?.();
      view.dispose();
      for (const geometry of Object.values(curvedParts)) geometry.dispose();
    },
  };
}
