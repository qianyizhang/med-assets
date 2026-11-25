import * as THREE from './vendor/build/three.module.js';

const vec = (x, y, z) => new THREE.Vector3(x, y, z);
const vector = (xyz) => new THREE.Vector3().fromArray(xyz);
const DEFAULT_PRESS_SETTLE_MM = 30;

async function readAsset(path, format) {
  const url = new URL(path, import.meta.url);
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await fetch(url);
      if (attempt === 0 && response.status === 503) continue;
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response[format]();
    } catch (cause) {
      if (attempt === 0 && cause instanceof TypeError) continue;
      throw new Error(`Could not load ${url.href}. ${cause.message}`, { cause });
    }
  }
}

export async function loadMesh(name, path = `scenes/${name}.mesh`) {
  const data = await readAsset(path, 'arrayBuffer');
  const header = new DataView(data);
  if (header.byteLength < 8) throw new Error(`Incomplete mesh: ${name}`);
  const vertices = header.getUint32(0, true);
  const faces = header.getUint32(4, true);
  const indicesAt = 8 + vertices * 12;
  if (!vertices || !faces || indicesAt + faces * 12 !== data.byteLength) {
    throw new Error(`Invalid mesh size: ${name}`);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(data, 8, vertices * 3), 3));
  geometry.setIndex(new THREE.BufferAttribute(new Uint32Array(data, indicesAt, faces * 3), 1));
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  return geometry;
}

function orientationMarker() {
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(0, 1, 1, 0, -1, 1);
  const axes = [
    { label: 'R', color: '#f3ba91', vector: vec(1, 0, 0) },
    { label: 'A', color: '#92e5c3', vector: vec(0, 1, 0) },
    { label: 'S', color: '#a8daf4', vector: vec(0, 0, 1) },
  ].map((axis) => {
    const textureCanvas = document.createElement('canvas');
    textureCanvas.width = textureCanvas.height = 64;
    const ink = textureCanvas.getContext('2d');
    ink.fillStyle = axis.color;
    ink.font = 'bold 47px system-ui';
    ink.textAlign = 'center';
    ink.textBaseline = 'middle';
    ink.fillText(axis.label, 32, 34);
    const texture = new THREE.CanvasTexture(textureCanvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const label = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthTest: false }));
    label.scale.set(18, 18, 1);
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([vec(0, 0, 0), vec(0, 0, 0)]),
      new THREE.LineBasicMaterial({ color: axis.color, depthTest: false }),
    );
    line.frustumCulled = false;
    scene.add(line, label);
    return { ...axis, texture, line, label };
  });

  return {
    render(renderer, view, width, height) {
      camera.right = width;
      camera.top = height;
      camera.updateProjectionMatrix();
      const inverseView = view.quaternion.clone().invert();
      for (const axis of axes) {
        const endpoint = axis.vector.clone().applyQuaternion(inverseView).multiplyScalar(28);
        axis.line.visible = axis.label.visible = Math.hypot(endpoint.x, endpoint.y) > 3;
        const x = width - 44;
        const y = 44;
        // Draw near axes above far axes when a view makes them overlap.
        const order = Math.round(endpoint.z * 10);
        const coordinates = axis.line.geometry.attributes.position;
        coordinates.setXYZ(0, x, y, 0);
        coordinates.setXYZ(1, x + endpoint.x, y + endpoint.y, 0);
        coordinates.needsUpdate = true;
        axis.line.renderOrder = order;
        axis.label.renderOrder = order;
        endpoint.z = 0;
        endpoint.setLength(endpoint.length() + 8);
        axis.label.position.set(x + endpoint.x, y + endpoint.y, 0);
      }
      renderer.autoClear = false;
      renderer.clearDepth();
      renderer.render(scene, camera);
      renderer.autoClear = true;
    },
    dispose() {
      for (const { line, label, texture } of axes) {
        line.geometry.dispose();
        line.material.dispose();
        label.material.dispose();
        texture.dispose();
      }
    },
  };
}

function viewport(canvas, { pivot, presets, shadowTarget, onViewPresetChange, probe, torso, onProbeDrag }) {
  const context = canvas.getContext('webgl2', { alpha: false, antialias: true });
  if (!context) throw new Error('This browser could not start WebGL 2 for the orbitable views.');
  const renderer = new THREE.WebGLRenderer({ canvas, context });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#142224');
  scene.add(new THREE.HemisphereLight('#dce6ed', '#64616a', 1.45));
  const key = new THREE.DirectionalLight('#fff6e8', 1.85);
  key.target.position.copy(shadowTarget);
  key.position.copy(shadowTarget).add(vec(-150, 340, 220));
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -110, right: 110, top: 110, bottom: -110, near: 10, far: 650 });
  key.shadow.normalBias = .32;
  key.shadow.intensity = .36;
  scene.add(key, key.target);
  const fill = new THREE.DirectionalLight('#9dc8d4', 0.78);
  fill.position.set(-335, -260, 210);
  scene.add(fill);

  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.25, 1900);
  let presetName = 'oblique';
  let preset = presets[presetName];
  let activePreset;
  let magnification = 1;
  let pending = 0;
  let pointer = null;
  let previousWidth = 0;
  let previousHeight = 0;
  const events = new AbortController();
  const marker = orientationMarker();
  const raycaster = onProbeDrag ? new THREE.Raycaster() : null;

  function render() {
    pending = 0;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height || context.isContextLost()) return;
    if (width !== previousWidth || height !== previousHeight) {
      renderer.setSize(width, height, false);
      previousWidth = width;
      previousHeight = height;
    }
    const aspect = width / height;
    const halfHeight = Math.max(preset.halfHeight, preset.halfWidth / aspect) / magnification;
    camera.top = halfHeight;
    camera.bottom = -halfHeight;
    camera.left = -halfHeight * aspect;
    camera.right = -camera.left;
    camera.updateProjectionMatrix();
    renderer.render(scene, camera);
    marker.render(renderer, camera, width, height);
  }

  function invalidate() {
    if (!pending) pending = requestAnimationFrame(render);
  }

  function reportPreset(name) {
    if (name === activePreset) return;
    activePreset = name;
    onViewPresetChange?.(name);
  }

  function reset() {
    camera.up.copy(preset.up);
    camera.position.copy(preset.target).addScaledVector(preset.direction, 650);
    camera.lookAt(preset.target);
    magnification = 1;
    reportPreset(presetName);
    invalidate();
  }

  function setViewPreset(name) {
    if (!Object.hasOwn(presets, name)) return;
    presetName = name;
    preset = presets[name];
    reset();
  }

  function orbit(yaw, pitch) {
    if (!yaw && !pitch) return;
    const aroundUp = new THREE.Quaternion().setFromAxisAngle(camera.up, yaw);
    const heading = camera.quaternion.clone().premultiply(aroundUp);
    const right = vec(1, 0, 0).applyQuaternion(heading);
    const outward = vec(0, 0, 1).applyQuaternion(heading);
    const polar = Math.acos(THREE.MathUtils.clamp(outward.dot(camera.up), -1, 1));
    const nextPolar = THREE.MathUtils.clamp(polar + pitch, .02, Math.PI - .02);
    const rotation = new THREE.Quaternion().setFromAxisAngle(right, nextPolar - polar).multiply(aroundUp);
    // Apply the same rigid rotation to the camera's position and orientation about the
    // selected point. Its camera-space coordinates, including depth, then stay fixed.
    camera.position.sub(pivot).applyQuaternion(rotation).add(pivot);
    camera.quaternion.premultiply(rotation).normalize();
    reportPreset(null);
    invalidate();
  }

  function zoom(scale) {
    const next = THREE.MathUtils.clamp(magnification * scale, .65, 3.2);
    const right = vec(1, 0, 0).applyQuaternion(camera.quaternion);
    const vertical = vec(0, 1, 0).applyQuaternion(camera.quaternion);
    const offset = pivot.clone().sub(camera.position);
    const shift = 1 - magnification / next;
    camera.position.addScaledVector(right, shift * offset.dot(right));
    camera.position.addScaledVector(vertical, shift * offset.dot(vertical));
    magnification = next;
    invalidate();
  }

  function listen(type, handler, options = {}) {
    canvas.addEventListener(type, handler, { ...options, signal: events.signal });
  }

  function hitsProbe(event) {
    if (!raycaster) return false;
    const bounds = canvas.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return false;
    const cursor = new THREE.Vector2(
      (event.clientX - bounds.left) / bounds.width * 2 - 1,
      1 - (event.clientY - bounds.top) / bounds.height * 2,
    );
    camera.updateMatrixWorld();
    probe.updateWorldMatrix(true, true);
    raycaster.setFromCamera(cursor, camera);
    const [hit] = raycaster.intersectObject(probe, true);
    if (!hit) return false;
    if (!torso.visible) return true;
    const [skin] = raycaster.intersectObject(torso, false);
    return !skin || hit.distance < skin.distance;
  }

  function finishPointer(event, useLastPosition = false) {
    if (pointer?.id !== event.pointerId) return;
    const gesture = pointer;
    pointer = null;
    if (gesture.steering) {
      const x = useLastPosition ? gesture.x : event.clientX;
      const y = useLastPosition ? gesture.y : event.clientY;
      onProbeDrag({ phase: 'end', dx: x - gesture.startX, dy: y - gesture.startY });
    }
    canvas.style.cursor = !useLastPosition && event.pointerType === 'mouse' && hitsProbe(event) ? 'move' : '';
  }

  listen('webglcontextrestored', invalidate);
  listen('pointerdown', (event) => {
    if (!event.isPrimary || event.button !== 0) return;
    const steering = hitsProbe(event) && onProbeDrag({ phase: 'start', dx: 0, dy: 0 }) !== false;
    pointer = { id: event.pointerId, x: event.clientX, y: event.clientY,
      startX: event.clientX, startY: event.clientY, steering };
    canvas.setPointerCapture(pointer.id);
    if (steering) canvas.style.cursor = 'move';
  });
  listen('pointermove', (event) => {
    if (pointer?.id !== event.pointerId) {
      if (!pointer && raycaster && event.pointerType === 'mouse') {
        canvas.style.cursor = hitsProbe(event) ? 'move' : '';
      }
      return;
    }
    if (pointer.steering) {
      onProbeDrag({ phase: 'move', dx: event.clientX - pointer.startX, dy: event.clientY - pointer.startY });
    } else {
      const scale = Math.PI / Math.max(1, canvas.clientHeight);
      orbit(-(event.clientX - pointer.x) * scale, -(event.clientY - pointer.y) * scale);
    }
    pointer.x = event.clientX;
    pointer.y = event.clientY;
  });
  listen('pointerup', finishPointer);
  listen('pointercancel', (event) => finishPointer(event, true));
  listen('lostpointercapture', (event) => finishPointer(event, true));
  listen('pointerleave', () => { if (!pointer) canvas.style.cursor = ''; });
  listen('wheel', (event) => {
    event.preventDefault();
    const step = event.deltaMode === WheelEvent.DOM_DELTA_LINE ? .075 : .0015;
    zoom(Math.exp(-event.deltaY * step));
  }, { passive: false });
  listen('keydown', (event) => {
    if (event.altKey || event.metaKey || event.ctrlKey) return;
    switch (event.key) {
      case 'ArrowLeft': orbit(.16, 0); break;
      case 'ArrowRight': orbit(-.16, 0); break;
      case 'ArrowUp': orbit(0, .16); break;
      case 'ArrowDown': orbit(0, -.16); break;
      case '+':
      case '=': zoom(1.16); break;
      case '-': zoom(1 / 1.16); break;
      case 'Home': reset(); break;
      default: return;
    }
    event.preventDefault();
    event.stopPropagation();
  });
  const resize = new ResizeObserver(invalidate);
  resize.observe(canvas);
  reset();

  return {
    scene, invalidate, reset, setViewPreset,
    dispose() {
      resize.disconnect();
      cancelAnimationFrame(pending);
      if (pointer && canvas.hasPointerCapture(pointer.id)) canvas.releasePointerCapture(pointer.id);
      events.abort();
      scene.traverse((object) => {
        object.geometry?.dispose();
        object.material?.dispose();
      });
      marker.dispose();
      renderer.dispose();
    },
  };
}

function solid(geometry, color, opacity = 1) {
  return new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
    color, roughness: .85, transparent: opacity < 1, opacity, depthWrite: opacity === 1,
  }));
}

function imagingWireframe(border, grid) {
  const group = new THREE.Group();
  for (const [points, opacity] of [[border, .98], [grid, .46]]) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));
    const material = new THREE.LineBasicMaterial({
      color: '#8ad8f8', transparent: true, opacity, depthWrite: false, toneMapped: false,
    });
    const lines = new THREE.LineSegments(geometry, material);
    lines.renderOrder = 3;
    group.add(lines);
  }
  return group;
}

function sectorGeometry({ voxelMm, lensRadiusMm, sectorDepthMm, sectorHalfAngleDeg }) {
  const angle = THREE.MathUtils.degToRad(sectorHalfAngleDeg);
  const radii = [lensRadiusMm, ...[.25, .5, .75].map((fraction) => lensRadiusMm + sectorDepthMm * fraction),
    lensRadiusMm + sectorDepthMm];
  const grid = [];
  const border = [];
  function point(radius, a) {
    // Local +Z points away from the body, so positive scan depth is -Z.
    return [radius * Math.sin(a) / voxelMm, 0, -(radius * Math.cos(a) - lensRadiusMm) / voxelMm];
  }
  for (const [index, radius] of radii.entries()) {
    const lines = index === 0 || index === radii.length - 1 ? border : grid;
    for (let i = 0; i < 36; i++) {
      lines.push(...point(radius, angle * (i / 18 - 1)), ...point(radius, angle * ((i + 1) / 18 - 1)));
    }
  }
  for (let i = -3; i <= 3; i++) {
    const lines = Math.abs(i) === 3 ? border : grid;
    lines.push(...point(radii[0], angle * i / 3), ...point(radii.at(-1), angle * i / 3));
  }
  return imagingWireframe(border, grid);
}

function rectangleGeometry({ voxelMm, fieldWidthMm, sectorDepthMm }) {
  const halfWidth = fieldWidthMm / voxelMm / 2;
  const depth = sectorDepthMm / voxelMm;
  const frontLeft = [-halfWidth, 0, 0];
  const frontRight = [halfWidth, 0, 0];
  const backLeft = [-halfWidth, 0, -depth];
  const backRight = [halfWidth, 0, -depth];
  const border = [...frontLeft, ...frontRight, ...frontRight, ...backRight, ...backRight, ...backLeft, ...backLeft, ...frontLeft];
  const grid = [];
  for (let i = 1; i < 6; i++) {
    const x = halfWidth * (i / 3 - 1);
    grid.push(x, 0, 0, x, 0, -depth);
  }
  for (let i = 1; i < 4; i++) {
    const z = -depth * i / 4;
    grid.push(-halfWidth, 0, z, halfWidth, 0, z);
  }
  return imagingWireframe(border, grid);
}

function curvedTransducer(meshes, dimensions) {
  const group = new THREE.Group();
  group.add(solid(meshes.lens, '#172f33'), solid(meshes.housing, '#e4ece7'), solid(meshes.relief, '#172f33'));
  const pip = solid(new THREE.SphereGeometry(1, 24, 12), '#31b5a2');
  pip.position.fromArray(dimensions.pipPosition);
  pip.scale.fromArray(dimensions.pipScale);
  group.add(pip);
  return group;
}

function linearCasing(profile, voxelMm) {
  const segments = 32;
  const vertices = [];
  const indices = [];
  for (const [z, halfWidth, halfThickness, roundness] of profile) {
    for (let i = 0; i < segments; i++) {
      const angle = i / segments * Math.PI * 2;
      const x = Math.cos(angle);
      const y = Math.sin(angle);
      vertices.push(
        Math.sign(x) * Math.abs(x) ** roundness * halfWidth / voxelMm,
        Math.sign(y) * Math.abs(y) ** roundness * halfThickness / voxelMm,
        z / voxelMm,
      );
    }
  }
  const top = (profile.length - 1) * segments;
  const bottomCenter = top + segments;
  const topCenter = bottomCenter + 1;
  vertices.push(0, 0, profile[0][0] / voxelMm, 0, 0, profile.at(-1)[0] / voxelMm);
  for (let i = 0; i < segments; i++) {
    const next = (i + 1) % segments;
    indices.push(bottomCenter, next, i, topCenter, top + i, top + next);
    for (let ring = 0; ring < top; ring += segments) {
      const above = ring + segments;
      indices.push(ring + i, ring + next, above + i, ring + next, above + next, above + i);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function linearTransducer({ voxelMm, fieldWidthMm }, contactRig) {
  const group = new THREE.Group();
  const half = fieldWidthMm / 2;
  const grip = half * .45;
  const faceThickness = contactRig ? contactRig.faceElevationMm / 2 : 6.5;
  const lens = linearCasing([
    [contactRig ? .8 : 0, half, faceThickness, .35],
    [1.2, half, 7.8, .38],
    [3.4, half + .5, 8.5, .4],
  ], voxelMm);
  const housing = linearCasing([
    [3.2, half + .6, 8.3, .4],
    [5.6, half + 1, 10.7, .45],
    [11, half + .8, 12.0, .47],
    [18, half * .91, 12.8, .52],
    [26, half * .72, 13, .61],
    [35, grip + 1.5, 13.4, .78],
    [42, grip, 13.5, .87],
    [56, grip, 13.2, .87],
    [66, grip - 1.1, 11.8, .91],
    [72, grip - 3, 9.7, .93],
    [75, 7.0, 7.7, .95],
    [76, 5.0, 5.5, 1],
  ], voxelMm);
  const relief = new THREE.CylinderGeometry(2.8 / voxelMm, 4.7 / voxelMm, 9 / voxelMm, 20);
  relief.rotateX(Math.PI / 2);
  relief.translate(0, 0, 79.5 / voxelMm);
  const pip = new THREE.SphereGeometry(1.5 / voxelMm, 20, 12);
  pip.translate((half - 8) / voxelMm, -10 / voxelMm, 8.5 / voxelMm);
  group.add(solid(lens, '#172f33'), solid(housing, '#e4ece7'), solid(relief, '#273235'), solid(pip, '#31b5a2'));
  if (contactRig) {
    const contactFace = new THREE.BoxGeometry(fieldWidthMm / voxelMm, contactRig.faceElevationMm / voxelMm, .8 / voxelMm);
    contactFace.translate(0, 0, .4 / voxelMm);
    group.add(solid(contactFace, '#172f33'));
  }
  return group;
}

function transformForFrame(frame) {
  const position = vector(frame.contact);
  const width = vector(frame.width).normalize();
  const outward = vector(frame.beam).negate().normalize();
  const cross = outward.clone().cross(width).normalize();
  const basis = new THREE.Matrix4().makeBasis(width, cross, outward);
  return { position, orientation: new THREE.Quaternion().setFromRotationMatrix(basis) };
}

function readContactRig(frames, dimensions) {
  const first = frames[0].contactRig;
  if (!first && frames.every(({ contactRig }) => contactRig === undefined)) return null;
  if (!first) throw new Error('The initial pose lacks a registered contact field.');
  const { lateralMm, elevationMm, faceWidthMm, faceElevationMm, featherMm, settleDepthMm } = first;
  const axes = [lateralMm, elevationMm];
  const same = (a, b) => Math.abs(a - b) < 1e-5;
  if (axes.some((axis) => !Array.isArray(axis) || axis.length < 2 ||
      axis.some((value, i) => !Number.isFinite(value) || !same(value, axis[0] + i * (axis[1] - axis[0]))) ||
      axis[1] <= axis[0]) || !same(faceWidthMm, dimensions.fieldWidthMm) ||
      ![faceWidthMm, faceElevationMm, featherMm, settleDepthMm].every((value) => Number.isFinite(value) && value > 0) ||
      !same(lateralMm[0], -faceWidthMm / 2) || !same(lateralMm.at(-1), faceWidthMm / 2) ||
      !same(elevationMm[0], -faceElevationMm / 2) || !same(elevationMm.at(-1), faceElevationMm / 2)) {
    throw new Error('The registered contact field has invalid grid coordinates.');
  }
  const samples = frames.map(({ contactRig: pose }) => {
    if (!pose || axes.some((axis, i) => {
      const actual = i === 0 ? pose.lateralMm : pose.elevationMm;
      return actual?.length !== axis.length || axis.some((value, j) => !same(value, actual[j]));
    }) || ['faceWidthMm', 'faceElevationMm', 'featherMm', 'settleDepthMm'].some((key) => !same(pose[key], first[key])) ||
      pose.surfaceMm?.length !== elevationMm.length ||
      pose.surfaceMm.some((row) => row?.length !== lateralMm.length || !row.every(Number.isFinite))) {
      throw new Error('A pose lacks the shared contact footprint or surface samples.');
    }
    return Float32Array.from(pose.surfaceMm.flat());
  });
  const size = new THREE.Vector2(lateralMm.length, elevationMm.length);
  const texture = new THREE.DataTexture(samples[0].slice(), size.x, size.y, THREE.RedFormat, THREE.FloatType);
  texture.needsUpdate = true;
  return {
    texture, samples, size, faceElevationMm, featherMm, settleDepthMm,
    start: new THREE.Vector2(lateralMm[0], elevationMm[0]),
    step: new THREE.Vector2(lateralMm[1] - lateralMm[0], elevationMm[1] - elevationMm[0]),
  };
}

function breastCompression(materials, dimensions, rig) {
  const uniforms = {
    pressMm: { value: 0 },
    pressOrigin: { value: vec(0, 0, 0) },
    pressBeam: { value: vec(0, 0, 0) },
    pressWidth: { value: vec(0, 0, 0) },
    pressElevation: { value: vec(0, 0, 0) },
    pressVoxelMm: { value: dimensions.voxelMm },
    pressHalfWidthMm: { value: dimensions.fieldWidthMm / 2 },
    pressSettleMm: { value: rig?.settleDepthMm ?? dimensions.pressSettleMm },
  };
  if (rig) Object.assign(uniforms, {
    pressSkin: { value: rig.texture },
    pressGridSize: { value: rig.size },
    pressGridStart: { value: rig.start },
    pressGridStep: { value: rig.step },
    pressHalfElevationMm: { value: rig.faceElevationMm / 2 },
    pressFeatherMm: { value: rig.featherMm },
  });
  const registeredField = rig ? `
    uniform sampler2D pressSkin;
    uniform vec2 pressGridSize, pressGridStart, pressGridStep;
    uniform float pressHalfElevationMm, pressFeatherMm;

    float pressSkinAt(vec2 xy) {
      // DataTexture uses nearest sampling, so bilinear interpolation is explicit
      // and does not depend on float-linear texture support.
      vec2 grid = clamp((xy - pressGridStart) / pressGridStep, vec2(0.0), pressGridSize - 1.0);
      vec2 low = floor(grid);
      vec2 high = min(low + 1.0, pressGridSize - 1.0);
      vec2 t = grid - low;
      float a = texture2D(pressSkin, (low + .5) / pressGridSize).r;
      float b = texture2D(pressSkin, (vec2(high.x, low.y) + .5) / pressGridSize).r;
      float c = texture2D(pressSkin, (vec2(low.x, high.y) + .5) / pressGridSize).r;
      float d = texture2D(pressSkin, (high + .5) / pressGridSize).r;
      return mix(mix(a, b, t.x), mix(c, d, t.x), t.y);
    }

    float pressDisplacement(vec3 p) {
      vec2 halfFace = vec2(pressHalfWidthMm, pressHalfElevationMm);
      if (any(greaterThanEqual(abs(p.xy), halfFace + pressFeatherMm))) return 0.0;
      vec2 feather = 1.0 - smoothstep(halfFace, halfFace + pressFeatherMm, abs(p.xy));
      float skin = pressSkinAt(p.xy);
      float shallow = 1.0 - smoothstep(0.0, pressSettleMm, max(0.0, p.z - skin));
      return max(pressMm - skin, 0.0) * feather.x * feather.y * shallow;
    }
  ` : `
    float pressDisplacement(vec3 p) {
      if (pressMm == 0.0) return 0.0;
      float shallow = smoothstep(-9.0, -3.0, p.z) * (1.0 - smoothstep(0.0, pressSettleMm, p.z));
      float across = 1.0 - smoothstep(pressHalfWidthMm, pressHalfWidthMm + 10.0, abs(p.x));
      float offPlane = 1.0 - smoothstep(6.5, 18.0, abs(p.y));
      return pressMm * shallow * across * offPlane;
    }
  `;
  for (const material of materials) {
    material.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, uniforms);
      shader.vertexShader = `
        uniform float pressMm, pressVoxelMm, pressHalfWidthMm, pressSettleMm;
        uniform vec3 pressOrigin, pressBeam, pressWidth, pressElevation;

        vec3 pressCoordinates(vec3 position) {
          vec3 offsetMm = (position - pressOrigin) * pressVoxelMm;
          return vec3(dot(offsetMm, pressWidth), dot(offsetMm, pressElevation), dot(offsetMm, pressBeam));
        }
      ` + registeredField + shader.vertexShader.replace('#include <begin_vertex>', `
        #include <begin_vertex>
        transformed += pressBeam * (pressDisplacement(pressCoordinates(position)) / pressVoxelMm);
      `);
      if (material.isMeshStandardMaterial) {
        shader.vertexShader = shader.vertexShader.replace('#include <beginnormal_vertex>', `
          #include <beginnormal_vertex>
          vec3 localMm = pressCoordinates(position);
          const float sampleMm = 0.2;
          // The map is a beam-axis displacement. Its Jacobian's cofactor
          // carries the original surface normal through the deformation.
          float initialDisplacement = pressDisplacement(localMm);
          vec3 derivative = (vec3(
            pressDisplacement(localMm + vec3(sampleMm, 0.0, 0.0)),
            pressDisplacement(localMm + vec3(0.0, sampleMm, 0.0)),
            pressDisplacement(localMm + vec3(0.0, 0.0, sampleMm))
          ) - initialDisplacement) / sampleMm;
          vec3 gradient = pressWidth * derivative.x + pressElevation * derivative.y + pressBeam * derivative.z;
          objectNormal = normalize((1.0 + derivative.z) * objectNormal - gradient * dot(pressBeam, objectNormal));
        `);
      }
    };
    material.customProgramCacheKey = () => 'breast-contact-' + (rig ? 'registered' : 'unregistered');
  }
  return (frame, amount, contact, orientation) => {
    if (rig) {
      rig.texture.image.data.set(rig.samples[frame]);
      rig.texture.needsUpdate = true;
    }
    uniforms.pressMm.value = amount;
    uniforms.pressOrigin.value.copy(contact);
    uniforms.pressBeam.value.set(0, 0, -1).applyQuaternion(orientation);
    uniforms.pressWidth.value.set(1, 0, 0).applyQuaternion(orientation);
    uniforms.pressElevation.value.set(0, -1, 0).applyQuaternion(orientation);
  };
}

function surveyRoute(transforms, dimensions) {
  const { voxelMm, fieldWidthMm } = dimensions;
  const lift = 1 / voxelMm;
  const points = transforms.map(({ position, orientation }) =>
    position.clone().addScaledVector(vec(0, 0, 1).applyQuaternion(orientation), lift));
  const group = new THREE.Group();
  const unvisited = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineDashedMaterial({
    color: '#d6dfd8', transparent: true, opacity: .58, depthWrite: false,
    dashSize: 3 / voxelMm, gapSize: 2 / voxelMm,
  }));
  unvisited.computeLineDistances();
  const unvisitedPositions = unvisited.geometry.getAttribute('position');
  const unvisitedDistances = unvisited.geometry.getAttribute('lineDistance');
  const allDistances = unvisitedDistances.array.slice();
  const visitedGeometry = new THREE.BufferGeometry().setFromPoints(points);
  const visited = new THREE.Line(visitedGeometry, new THREE.LineBasicMaterial({
    color: '#eff3df', transparent: true, opacity: .95, depthWrite: false,
  }));
  const visitedPositions = visitedGeometry.getAttribute('position');
  const allPositions = visitedPositions.array.slice();
  const half = fieldWidthMm / 2 / voxelMm;
  const edge = 7 / voxelMm;
  const outline = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints([
    vec(-half, -edge, 0), vec(half, -edge, 0), vec(half, edge, 0), vec(-half, edge, 0),
  ]), new THREE.LineBasicMaterial({ color: '#eadfbe', transparent: true, opacity: .68, depthWrite: false }));
  unvisited.renderOrder = 5;
  visited.renderOrder = 6;
  outline.renderOrder = 6;
  group.add(unvisited, visited, outline);

  return {
    group,
    setFrame(frame, contact, orientation) {
      const lo = Math.floor(frame);
      const hi = Math.ceil(frame);
      visitedPositions.array.set(allPositions);
      unvisitedPositions.array.set(allPositions);
      unvisitedDistances.array.set(allDistances);
      if (lo !== hi) {
        const partial = points[lo].clone().lerp(points[hi], frame - lo);
        visitedPositions.setXYZ(hi, partial.x, partial.y, partial.z);
        unvisitedPositions.setXYZ(lo, partial.x, partial.y, partial.z);
        unvisitedDistances.setX(lo, THREE.MathUtils.lerp(allDistances[lo], allDistances[hi], frame - lo));
      }
      visitedPositions.needsUpdate = true;
      unvisitedPositions.needsUpdate = true;
      unvisitedDistances.needsUpdate = true;
      visitedGeometry.setDrawRange(0, hi + 1);
      unvisited.geometry.setDrawRange(lo, points.length - lo);
      outline.position.copy(contact).addScaledVector(vec(0, 0, 1).applyQuaternion(orientation), lift);
      outline.quaternion.copy(orientation);
    },
  };
}

function boundsCorners(bounds) {
  const { min, max } = bounds;
  return [min.x, max.x].flatMap((x) => [min.y, max.y].flatMap((y) =>
    [min.z, max.z].map((z) => vec(x, y, z))));
}

function neckFraming(pivot, bodyBounds, voxelMm, obliqueDirection) {
  const contextBounds = bodyBounds.clone();
  // Keep superior and inferior case context, and focus laterally on the probed side.
  const width = 66 / voxelMm;
  contextBounds.min.x = Math.max(contextBounds.min.x, pivot.x - width);
  contextBounds.max.x = Math.min(contextBounds.max.x, pivot.x + width);
  contextBounds.min.y = Math.max(contextBounds.min.y, pivot.y - 42 / voxelMm);
  contextBounds.min.z = Math.max(contextBounds.min.z, pivot.z - 72 / voxelMm);
  contextBounds.max.z = Math.min(contextBounds.max.z, pivot.z + 96 / voxelMm);
  const side = pivot.x < bodyBounds.getCenter(vec(0, 0, 0)).x ? -1 : 1;
  const direction = obliqueDirection ? vector(obliqueDirection) : vec(.92 * side, .94, .43);
  return { contextBounds, padding: 5 / voxelMm, direction };
}

function axillaFraming(pivot, voxelMm) {
  const contextBounds = new THREE.Box3(
    pivot.clone().addScaledVector(vec(-60, -27, -65), 1 / voxelMm),
    pivot.clone().addScaledVector(vec(77, 30, 71), 1 / voxelMm),
  );
  return { contextBounds, padding: 10 / voxelMm, direction: vec(.95, .1, .22) };
}

function cameraPresets(organ, pivot, fitBounds, transforms, probe, sector, framing = {}) {
  const { contextBounds, padding = 8 } = framing;
  const keyframe = transforms[Math.min(12, transforms.length - 1)];
  const points = boundsCorners(fitBounds);
  if (contextBounds) points.push(...boundsCorners(contextBounds));
  const probeCorners = boundsCorners(new THREE.Box3().setFromObject(probe));
  const fieldOutline = sector.children[0].geometry.getAttribute('position');
  const localPoints = [
    ...probeCorners,
    ...Array.from({ length: fieldOutline.count }, (_, index) =>
      vec(0, 0, 0).fromBufferAttribute(fieldOutline, index)),
  ];
  for (const pose of transforms) {
    for (const point of localPoints) {
      points.push(point.clone().applyQuaternion(pose.orientation).add(pose.position));
    }
  }

  function fitted(direction, up) {
    direction.normalize();
    up.addScaledVector(direction, -up.dot(direction)).normalize();
    const right = up.clone().cross(direction);
    const min = new THREE.Vector2(Infinity, Infinity);
    const max = new THREE.Vector2(-Infinity, -Infinity);
    for (const point of points) {
      const x = point.dot(right);
      const y = point.dot(up);
      min.set(Math.min(min.x, x), Math.min(min.y, y));
      max.set(Math.max(max.x, x), Math.max(max.y, y));
    }
    const target = pivot.clone()
      .addScaledVector(right, (min.x + max.x) / 2 - pivot.dot(right))
      .addScaledVector(up, (min.y + max.y) / 2 - pivot.dot(up));
    return {
      target, direction, up,
      halfWidth: (max.x - min.x) * .58 + padding,
      halfHeight: (max.y - min.y) * .58 + padding,
    };
  }

  const outward = vec(0, 0, 1).applyQuaternion(keyframe.orientation);
  const normal = vec(0, 1, 0).applyQuaternion(keyframe.orientation);
  // Use the side of the plane that leaves the probe on the near side of the target.
  const viewDirection = framing.direction ?? outward.clone().addScaledVector(normal, normal.y >= 0 ? .7 : -.7);
  return {
    oblique: organ === 'gallbladder' ? {
      target: pivot.clone().lerp(keyframe.position, .35).add(vec(-8, 2, 48)),
      direction: vec(.57, .94, .22).normalize(),
      up: vec(-.63, .04, .78).normalize(),
      halfHeight: 109.5, halfWidth: 109.5 / 1.22,
    } : fitted(viewDirection, vec(0, 0, 1)),
    // RAS patient coordinates. Radiological axial looks up from the feet,
    // coronal looks in from the front, sagittal looks in from patient left.
    axial: fitted(vec(0, 0, -1), vec(0, 1, 0)),
    coronal: fitted(vec(0, 1, 0), vec(0, 0, 1)),
    sagittal: fitted(vec(-1, 0, 0), vec(0, 0, 1)),
  };
}

export async function createSweepScene({ canvas, frames, config, onViewPresetChange, onProbeDrag }) {
  if (!frames?.length) throw new Error('The sweep has no probe poses.');
  if (!config?.parts?.some(({ id }) => id === config.organ)) {
    throw new Error('The sweep has no configured target mesh.');
  }
  const assetRoot = new URL(config.assetRoot, document.baseURI);
  const names = ['torso', ...config.parts.map(({ id }) => id)];
  const linear = config.probeType === 'linear';
  const probeNames = ['lens', 'housing', 'relief'];
  const requests = [
    () => readAsset('scenes/geometry.json', 'json'),
    ...names.map((name) => () => loadMesh(name, config.meshPaths?.[name]
      ?? new URL(`scenes/${name}.mesh`, assetRoot))),
    ...(linear ? [] : probeNames.map((name) => () => loadMesh(name))),
  ];
  const received = [];
  for (let start = 0; start < requests.length; start += 4) {
    received.push(...await Promise.all(requests.slice(start, start + 4).map((request) => request())));
  }
  const [commonDimensions, ...packedMeshes] = received;
  const geometries = packedMeshes.slice(0, names.length);
  const probeGeometries = packedMeshes.slice(names.length);
  const dimensions = {
    ...commonDimensions,
    voxelMm: config.voxelMm ?? commonDimensions.voxelMm,
    sectorDepthMm: config.sectorDepthMm ?? commonDimensions.sectorDepthMm,
    fieldWidthMm: config.fieldWidthMm,
    pressSettleMm: config.compressionSettleDepthMm ?? DEFAULT_PRESS_SETTLE_MM,
  };
  const rectangular = config.fieldShape === 'rectangle';
  if (linear && !(rectangular && Number.isFinite(dimensions.fieldWidthMm) && dimensions.fieldWidthMm > 0)) {
    throw new Error('The linear probe requires a rectangular field with a positive width.');
  }
  const contactRig = readContactRig(frames, dimensions);
  const settleMm = contactRig?.settleDepthMm ?? dimensions.pressSettleMm;
  const pressureMm = config.compressionMm ?? 0;
  if (pressureMm && !(linear && Number.isFinite(pressureMm) && pressureMm > 0 &&
      Number.isFinite(settleMm) && pressureMm < Math.min(2 * settleMm / 3, dimensions.sectorDepthMm))) {
    throw new Error('Probe compression requires a valid linear imaging depth.');
  }
  const depths = frames.map(({ imagingDepthMm }) => imagingDepthMm ?? dimensions.sectorDepthMm);
  if (depths.some((depth) => !Number.isFinite(depth) || depth <= pressureMm || depth > dimensions.sectorDepthMm) ||
      (!rectangular && depths.some((depth) => depth !== dimensions.sectorDepthMm))) {
    throw new Error('The sweep has an invalid imaging depth.');
  }
  const meshes = Object.fromEntries(names.map((name, index) => [name, geometries[index]]));
  const transforms = frames.map(transformForFrame);
  const bounds = meshes[config.organ].boundingBox;
  const pivot = config.focus ? vector(config.focus) : bounds.getCenter(vec(0, 0, 0));
  let fitBounds = bounds;
  if (config.focus) {
    // A whole-case vessel can extend far beyond the segment under the probe.
    const diameter = (config.focusRadius ?? 44) * 2;
    const localBounds = new THREE.Box3().setFromCenterAndSize(pivot, vec(diameter, diameter, diameter));
    localBounds.intersect(bounds);
    if (!localBounds.isEmpty()) fitBounds = localBounds;
  }
  const probe = linear
    ? linearTransducer(dimensions, contactRig)
    : curvedTransducer(Object.fromEntries(probeNames.map((name, index) => [name, probeGeometries[index]])), dimensions);
  const sector = rectangular ? rectangleGeometry(dimensions) : sectorGeometry(dimensions);
  let detailOutline;
  if (config.keyframes?.some((key) => key.detail)) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(12), 3));
    detailOutline = new THREE.LineLoop(geometry, new THREE.LineBasicMaterial({
      color: '#ffe698', transparent: true, opacity: .98, depthTest: false, depthWrite: false, toneMapped: false,
    }));
    detailOutline.visible = false;
    detailOutline.frustumCulled = false;
    detailOutline.renderOrder = 3;
    sector.add(detailOutline);
  }
  function setMagnifiedBounds(bounds) {
    if (!detailOutline) return;
    detailOutline.visible = Boolean(bounds);
    if (bounds) {
      const [left, near, right, far] = bounds;
      const vertices = detailOutline.geometry.attributes.position;
      [[left, near], [right, near], [right, far], [left, far]].forEach(([x, depth], i) =>
        vertices.setXYZ(i, x / dimensions.voxelMm, 0, -depth / dimensions.voxelMm));
      vertices.needsUpdate = true;
    }
    view.invalidate();
  }
  let framing;
  if (config.bodyRegion === 'Neck') {
    framing = neckFraming(pivot, meshes.torso.boundingBox, dimensions.voxelMm, config.obliqueDirection);
  } else if (config.organ === 'axillary_node') {
    framing = axillaFraming(pivot, dimensions.voxelMm);
  } else if (config.steering) {
    // The lateral and superior tilt reveals the field in both nipple reference planes.
    framing = { direction: vec(.57, .92, .55) };
  } else if (config.obliqueDirection) {
    framing = { direction: vector(config.obliqueDirection) };
  }
  const torso = solid(meshes.torso, '#be9885');
  torso.material.roughness = .95;
  torso.renderOrder = 4;
  torso.receiveShadow = true;
  // At partial opacity composite only the nearest outward-facing skin layer,
  // after anatomical structures and the scan field have rendered.
  const torsoDepth = new THREE.Mesh(meshes.torso, new THREE.MeshBasicMaterial({
    transparent: true, colorWrite: false, depthWrite: true,
    // The color and depth passes use different shader paths. Bias the
    // prepass slightly back to avoid self-rejection from rounding.
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  }));
  torsoDepth.renderOrder = 3.5;
  const view = viewport(canvas, {
    pivot,
    presets: cameraPresets(config.organ, pivot, fitBounds, transforms, probe, sector, framing),
    shadowTarget: transforms[Math.min(12, transforms.length - 1)].position,
    onViewPresetChange,
    probe,
    torso,
    onProbeDrag,
  });
  probe.traverse((object) => { if (object.isMesh) object.castShadow = true; });
  const cable = solid(new THREE.BufferGeometry(), '#4c5657');
  const internal = new THREE.Group();
  const surface = new THREE.Group();
  for (const [index, part] of config.parts.entries()) {
    const mesh = solid(meshes[part.id], part.color, part.opacity);
    if (config.surfaceParts?.includes(part.id)) {
      mesh.material.transparent = true;
      mesh.material.depthWrite = false;
      mesh.material.polygonOffset = true;
      mesh.material.polygonOffsetFactor = -1;
      mesh.material.polygonOffsetUnits = -1;
      mesh.renderOrder = torso.renderOrder + 1 + index / config.parts.length;
      surface.add(mesh);
    } else {
      mesh.renderOrder = (index + 1) / (config.parts.length + 1) * 2;
      internal.add(mesh);
    }
  }
  const deform = pressureMm || contactRig ? breastCompression([
    torso.material, torsoDepth.material, ...internal.children.map((part) => part.material),
    ...surface.children.map((part) => part.material),
  ], dimensions, contactRig) : null;
  internal.add(sector);
  view.scene.add(torso, torsoDepth, probe, cable, internal, surface);
  const route = config.showRoute && linear ? surveyRoute(transforms, dimensions) : null;
  if (route) view.scene.add(route.group);
  let routeVisible = Boolean(route);
  const last = transforms.length - 1;
  let selected = -1;
  let pressed = 0;

  function setFrame(index, compressed = false) {
    const frame = THREE.MathUtils.clamp(contactRig ? Math.round(index) : index, 0, last);
    const amount = compressed ? pressureMm : 0;
    if (!Number.isFinite(frame) || (frame === selected && amount === pressed)) return;
    selected = frame;
    pressed = amount;
    const lo = Math.floor(frame);
    const hi = Math.ceil(frame);
    const mix = frame - lo;
    probe.position.copy(transforms[lo].position).lerp(transforms[hi].position, mix);
    probe.quaternion.copy(transforms[lo].orientation).slerp(transforms[hi].orientation, mix);
    const outward = vec(0, 0, 1).applyQuaternion(probe.quaternion);
    deform?.(frame, pressed, probe.position, probe.quaternion);
    route?.setFrame(frame, probe.position, probe.quaternion);
    probe.position.addScaledVector(outward, -pressed / dimensions.voxelMm);
    sector.position.copy(probe.position);
    sector.quaternion.copy(probe.quaternion);
    const imagingDepth = THREE.MathUtils.lerp(depths[lo], depths[hi], mix);
    sector.scale.z = (imagingDepth - pressed) / dimensions.sectorDepthMm;

    const cableScale = linear ? 1 / dimensions.voxelMm : 1;
    const end = probe.position.clone().addScaledVector(outward, linear ? 84 * cableScale : 60);
    const path = new THREE.CatmullRomCurve3(linear ? [
      end,
      end.clone().addScaledVector(outward, 18 * cableScale),
      end.clone().addScaledVector(vec(-35, 26, -13), cableScale),
      end.clone().addScaledVector(vec(-81, 20, -43), cableScale),
    ] : [
      end,
      end.clone().addScaledVector(outward, 13),
      end.clone().add(vec(-35, 13, -24)),
      end.clone().add(vec(-55, -7, -105)),
    ]);
    cable.geometry.dispose();
    cable.geometry = new THREE.TubeGeometry(path, 24, (linear ? 1.65 : 1.55) * cableScale, 8, false);
    view.invalidate();
  }

  function setTorsoOpacity(value) {
    if (!Number.isFinite(value)) return;
    const opacity = THREE.MathUtils.clamp(value, 0, 1);
    const transparent = opacity < 1;
    torso.visible = opacity > 0;
    if (route) route.group.visible = routeVisible && torso.visible;
    surface.visible = torso.visible;
    for (const patch of surface.children) patch.material.opacity = opacity;
    torsoDepth.visible = torso.visible && transparent;
    // The opaque endpoint represents the external view. The modeled field can
    // extend beyond the sampled body, so hide the entire internal layer here.
    internal.visible = transparent;
    torso.material.opacity = opacity;
    if (torso.material.transparent !== transparent) {
      torso.material.transparent = transparent;
      torso.material.depthWrite = !transparent;
      torso.material.needsUpdate = true;
    }
    view.invalidate();
  }

  function setRouteVisible(value) {
    if (!route) return;
    routeVisible = Boolean(value);
    route.group.visible = routeVisible && torso.visible;
    view.invalidate();
  }

  setTorsoOpacity(.32);
  setFrame(0);
  return {
    setFrame, setTorsoOpacity, setRouteVisible, setMagnifiedBounds, setViewPreset: view.setViewPreset, resetView: view.reset,
    dispose() {
      view.dispose();
      contactRig?.texture.dispose();
    },
  };
}
