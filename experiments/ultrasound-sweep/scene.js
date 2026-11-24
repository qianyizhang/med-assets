import * as THREE from './vendor/build/three.module.js';

const vec = (x, y, z) => new THREE.Vector3(x, y, z);
const vector = (xyz) => new THREE.Vector3().fromArray(xyz);

async function readAsset(path, format) {
  const response = await fetch(new URL(path, import.meta.url));
  if (!response.ok) throw new Error(`Could not load ${path} (HTTP ${response.status}).`);
  return response[format]();
}

async function loadMesh(name) {
  const data = await readAsset(`scenes/${name}.mesh`, 'arrayBuffer');
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

function viewport(canvas, { target, direction, up, span, showOrientation = false }) {
  const context = canvas.getContext('webgl2', { alpha: false, antialias: true });
  if (!context) throw new Error('This browser could not start WebGL 2 for the orbitable views.');
  const renderer = new THREE.WebGLRenderer({ canvas, context });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#142426');
  scene.add(new THREE.HemisphereLight('#e7f6ff', '#513633', 1.9));
  const key = new THREE.DirectionalLight('#fff6e8', 2.05);
  key.position.set(370, 490, 560);
  scene.add(key);
  const fill = new THREE.DirectionalLight('#8baebc', 0.65);
  fill.position.set(-335, -260, 210);
  scene.add(fill);

  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.25, 1900);
  camera.up.copy(up);
  const toYUp = new THREE.Quaternion().setFromUnitVectors(up, vec(0, 1, 0));
  const fromYUp = toYUp.clone().invert();
  const initial = new THREE.Spherical().setFromVector3(
    direction.clone().normalize().multiplyScalar(650).applyQuaternion(toYUp),
  );
  const orbit = initial.clone();
  let magnification = 1;
  let pending = 0;
  let pointer = null;
  let previousWidth = 0;
  let previousHeight = 0;
  const events = new AbortController();
  const marker = showOrientation ? orientationMarker() : null;

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
    const halfHeight = span / (2 * Math.min(1, aspect * 1.22) * magnification);
    camera.top = halfHeight;
    camera.bottom = -halfHeight;
    camera.left = -halfHeight * aspect;
    camera.right = -camera.left;
    orbit.makeSafe();
    camera.position.copy(vec(0, 0, 0).setFromSpherical(orbit).applyQuaternion(fromYUp).add(target));
    camera.lookAt(target);
    camera.updateProjectionMatrix();
    renderer.render(scene, camera);
    marker?.render(renderer, camera, width, height);
  }

  function invalidate() {
    if (!pending) pending = requestAnimationFrame(render);
  }

  function reset() {
    orbit.copy(initial);
    magnification = 1;
    invalidate();
  }

  function zoom(scale) {
    magnification = THREE.MathUtils.clamp(magnification * scale, .65, 3.2);
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
    orbit.theta -= (event.clientX - pointer.x) * scale;
    orbit.phi -= (event.clientY - pointer.y) * scale;
    pointer.x = event.clientX;
    pointer.y = event.clientY;
    invalidate();
  });
  listen('lostpointercapture', () => { pointer = null; });
  listen('wheel', (event) => {
    event.preventDefault();
    const step = event.deltaMode === WheelEvent.DOM_DELTA_LINE ? .075 : .0015;
    zoom(Math.exp(-event.deltaY * step));
    invalidate();
  }, { passive: false });
  listen('keydown', (event) => {
    if (event.altKey || event.metaKey || event.ctrlKey) return;
    switch (event.key) {
      case 'ArrowLeft': orbit.theta += .16; break;
      case 'ArrowRight': orbit.theta -= .16; break;
      case 'ArrowUp': orbit.phi += .16; break;
      case 'ArrowDown': orbit.phi -= .16; break;
      case '+':
      case '=': zoom(1.16); break;
      case '-': zoom(1 / 1.16); break;
      case 'Home': reset(); break;
      default: return;
    }
    event.preventDefault();
    event.stopPropagation();
    invalidate();
  });
  const resize = new ResizeObserver(invalidate);
  resize.observe(canvas);
  invalidate();

  return {
    scene, invalidate, reset,
    dispose() {
      resize.disconnect();
      cancelAnimationFrame(pending);
      if (pointer && canvas.hasPointerCapture(pointer.id)) canvas.releasePointerCapture(pointer.id);
      events.abort();
      scene.traverse((object) => {
        object.geometry?.dispose();
        object.material?.dispose();
      });
      marker?.dispose();
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
  const radii = [lensRadiusMm, ...[33, 66, 99].map((depth) => lensRadiusMm + depth),
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
      color: '#84d4f3', transparent: true, opacity, depthTest: false, depthWrite: false,
    });
    const lines = new THREE.LineSegments(geometry, material);
    lines.renderOrder = 10;
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

export async function createSweepScenes({ poseCanvas, planeCanvas, frames }) {
  if (!frames?.length) throw new Error('The sweep has no probe poses.');
  const names = ['torso', 'ribs', 'liver', 'gallbladder', 'lens', 'housing', 'relief'];
  const [dimensions, ...geometries] = await Promise.all([
    readAsset('scenes/geometry.json', 'json'), ...names.map(loadMesh),
  ]);
  const meshes = Object.fromEntries(names.map((name, index) => [name, geometries[index]]));
  const transforms = frames.map(transformForFrame);
  const reference = transforms[Math.floor(transforms.length / 2)];
  const start = transforms[0].position;
  const target = meshes.gallbladder.boundingBox.getCenter(vec(0, 0, 0));
  const pose = viewport(poseCanvas, {
    target: vec(141, 149, 193), direction: vec(.43, .86, .19), up: vec(0, 0, 1), span: 433,
    showOrientation: true,
  });
  let plane;
  try {
    const outward = vec(0, 0, 1).applyQuaternion(reference.orientation);
    const normal = vec(0, 1, .1).normalize().applyQuaternion(reference.orientation);
    const up = outward.clone().addScaledVector(normal, -outward.dot(normal)).normalize();
    plane = viewport(planeCanvas, {
      target: target.clone().lerp(start, .16), direction: normal, up, span: 183,
    });
  } catch (error) {
    pose.dispose();
    throw error;
  }
  pose.scene.add(solid(meshes.torso, '#bf866d'));
  const probe = transducer(meshes, dimensions);
  const cable = solid(new THREE.BufferGeometry(), '#2a3a3b');
  pose.scene.add(probe, cable);
  plane.scene.add(
    solid(meshes.gallbladder, '#3fbf9e'),
    solid(meshes.liver, '#ad6155', .30),
    solid(meshes.ribs, '#dacaad', .28),
  );
  const sector = sectorGeometry(dimensions);
  plane.scene.add(sector);
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
    pose.invalidate();
    plane.invalidate();
  }

  setFrame(0);
  return {
    setFrame,
    resetView(which) {
      if (which !== 'plane') pose.reset();
      if (which !== 'pose') plane.reset();
    },
    dispose() {
      pose.dispose();
      plane.dispose();
    },
  };
}
