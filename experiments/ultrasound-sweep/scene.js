import * as THREE from './vendor/build/three.module.js';

const vec = (x, y, z) => new THREE.Vector3(x, y, z);
const vector = (xyz) => new THREE.Vector3().fromArray(xyz);

async function readAsset(path, format) {
  const response = await fetch(new URL(path, import.meta.url));
  if (!response.ok) throw new Error(`Could not load ${path} (HTTP ${response.status}).`);
  return response[format]();
}

async function loadMesh(name, path = `scenes/${name}.mesh`) {
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

function viewport(canvas, { pivot, presets, shadowTarget, onViewPresetChange }) {
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

  listen('webglcontextrestored', invalidate);
  listen('pointerdown', (event) => {
    if (!event.isPrimary || event.button !== 0) return;
    pointer = { id: event.pointerId, x: event.clientX, y: event.clientY };
    canvas.setPointerCapture(pointer.id);
  });
  listen('pointermove', (event) => {
    if (pointer?.id !== event.pointerId) return;
    const scale = Math.PI / Math.max(1, canvas.clientHeight);
    orbit(-(event.clientX - pointer.x) * scale, -(event.clientY - pointer.y) * scale);
    pointer.x = event.clientX;
    pointer.y = event.clientY;
  });
  listen('lostpointercapture', () => { pointer = null; });
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

function transducer(meshes, dimensions) {
  const group = new THREE.Group();
  group.add(solid(meshes.lens, '#172f33'), solid(meshes.housing, '#e4ece7'), solid(meshes.relief, '#172f33'));
  const pip = solid(new THREE.SphereGeometry(1, 24, 12), '#31b5a2');
  pip.position.fromArray(dimensions.pipPosition);
  pip.scale.fromArray(dimensions.pipScale);
  group.add(pip);
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

function boundsCorners(bounds) {
  const { min, max } = bounds;
  return [min.x, max.x].flatMap((x) => [min.y, max.y].flatMap((y) =>
    [min.z, max.z].map((z) => vec(x, y, z))));
}

function cameraPresets(organ, pivot, fitBounds, transforms, probe, sector) {
  const keyframe = transforms[Math.min(12, transforms.length - 1)];
  const points = boundsCorners(fitBounds);
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
      halfWidth: (max.x - min.x) * .58 + 8,
      halfHeight: (max.y - min.y) * .58 + 8,
    };
  }

  const outward = vec(0, 0, 1).applyQuaternion(keyframe.orientation);
  const normal = vec(0, 1, 0).applyQuaternion(keyframe.orientation);
  // Use the side of the plane that leaves the probe on the near side of the target.
  const viewDirection = outward.clone().addScaledVector(normal, normal.y >= 0 ? .7 : -.7);
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

export async function createSweepScene({ canvas, frames, config, onViewPresetChange }) {
  if (!frames?.length) throw new Error('The sweep has no probe poses.');
  if (!config?.parts?.some(({ id }) => id === config.organ)) {
    throw new Error('The sweep has no configured target mesh.');
  }
  const assetRoot = new URL(config.assetRoot, document.baseURI);
  const names = ['torso', ...config.parts.map(({ id }) => id)];
  const probeNames = ['lens', 'housing', 'relief'];
  const [commonDimensions, geometries, probeGeometries] = await Promise.all([
    readAsset('scenes/geometry.json', 'json'),
    Promise.all(names.map((name) => loadMesh(name, config.meshPaths?.[name]
      ?? new URL(`scenes/${name}.mesh`, assetRoot)))),
    Promise.all(probeNames.map((name) => loadMesh(name))),
  ]);
  const dimensions = { ...commonDimensions, sectorDepthMm: config.sectorDepthMm ?? commonDimensions.sectorDepthMm };
  const meshes = Object.fromEntries(names.map((name, index) => [name, geometries[index]]));
  const probeMeshes = Object.fromEntries(probeNames.map((name, index) => [name, probeGeometries[index]]));
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
  const probe = transducer(probeMeshes, dimensions);
  const sector = sectorGeometry(dimensions);
  const view = viewport(canvas, {
    pivot,
    presets: cameraPresets(config.organ, pivot, fitBounds, transforms, probe, sector),
    shadowTarget: transforms[Math.min(12, transforms.length - 1)].position,
    onViewPresetChange,
  });
  const torso = solid(meshes.torso, '#be9885');
  torso.material.roughness = .95;
  torso.renderOrder = 4;
  torso.receiveShadow = true;
  // At partial opacity composite only the nearest outward-facing skin layer,
  // after anatomical structures and the scan field have rendered.
  const torsoDepth = new THREE.Mesh(meshes.torso, new THREE.MeshBasicMaterial({
    transparent: true, colorWrite: false, depthWrite: true,
  }));
  torsoDepth.renderOrder = 3.5;
  probe.traverse((object) => { if (object.isMesh) object.castShadow = true; });
  const cable = solid(new THREE.BufferGeometry(), '#4c5657');
  const internal = new THREE.Group();
  for (const [index, part] of config.parts.entries()) {
    const mesh = solid(meshes[part.id], part.color, part.opacity);
    mesh.renderOrder = (index + 1) / (config.parts.length + 1) * 2;
    internal.add(mesh);
  }
  internal.add(sector);
  view.scene.add(torso, torsoDepth, probe, cable, internal);
  const last = transforms.length - 1;
  let selected = -1;

  function setFrame(index) {
    const frame = THREE.MathUtils.clamp(index, 0, last);
    if (!Number.isFinite(frame) || frame === selected) return;
    selected = frame;
    const lo = Math.floor(frame);
    const hi = Math.ceil(frame);
    const mix = frame - lo;
    probe.position.copy(transforms[lo].position).lerp(transforms[hi].position, mix);
    probe.quaternion.copy(transforms[lo].orientation).slerp(transforms[hi].orientation, mix);
    sector.position.copy(probe.position);
    sector.quaternion.copy(probe.quaternion);

    const outward = vec(0, 0, 1).applyQuaternion(probe.quaternion);
    const end = probe.position.clone().addScaledVector(outward, 60);
    const path = new THREE.CatmullRomCurve3([
      end,
      end.clone().addScaledVector(outward, 13),
      end.clone().add(vec(-35, 13, -24)),
      end.clone().add(vec(-55, -7, -105)),
    ]);
    cable.geometry.dispose();
    cable.geometry = new THREE.TubeGeometry(path, 24, 1.55, 8, false);
    view.invalidate();
  }

  function setTorsoOpacity(value) {
    if (!Number.isFinite(value)) return;
    const opacity = THREE.MathUtils.clamp(value, 0, 1);
    const transparent = opacity < 1;
    torso.visible = opacity > 0;
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

  setTorsoOpacity(.32);
  setFrame(0);
  return { setFrame, setTorsoOpacity, setViewPreset: view.setViewPreset, resetView: view.reset, dispose: view.dispose };
}
