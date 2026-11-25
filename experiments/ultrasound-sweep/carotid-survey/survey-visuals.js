const near = '#ffdb96';

export function showSpectrum(canvas, sample) {
  const { timeSeconds, velocityBinsCmS, power, envelopeCmS, measurements } = sample;
  const width = 720;
  const height = 235;
  canvas.width = width;
  canvas.height = height;
  const draw = canvas.getContext('2d');
  draw.fillStyle = '#081112';
  draw.fillRect(0, 0, width, height);
  if (!timeSeconds?.length || !velocityBinsCmS?.length || !power?.length) return;
  const left = 52, top = 20, right = width - 24, bottom = height - 30;
  const yMin = velocityBinsCmS[0], yMax = velocityBinsCmS.at(-1);
  const xMax = timeSeconds.at(-1);
  const x = (time) => left + time / xMax * (right - left);
  const y = (velocity) => bottom - (velocity - yMin) / (yMax - yMin) * (bottom - top);
  const columns = timeSeconds.length;
  const rows = velocityBinsCmS.length;
  const raster = draw.createImageData(columns, rows);
  for (let column = 0; column < columns; column += 1) {
    for (let row = 0; row < rows; row += 1) {
      const i = ((rows - row - 1) * columns + column) * 4;
      const light = Math.sqrt(Math.max(0, power[column][row]));
      raster.data.set([8 + light * 240, 17 + light * 185, 18 + light * 122, 255], i);
    }
  }
  const pixels = document.createElement('canvas');
  pixels.width = columns;
  pixels.height = rows;
  pixels.getContext('2d').putImageData(raster, 0, 0);
  draw.drawImage(pixels, left, top, right - left, bottom - top);
  draw.font = '13px system-ui';
  draw.textBaseline = 'middle';
  draw.textAlign = 'right';
  draw.fillStyle = '#d8e7e4';
  const tick = Math.max(10, Math.ceil((yMax - yMin) / 70) * 10);
  for (let value = Math.ceil(yMin / tick) * tick; value <= yMax; value += tick) {
    draw.strokeStyle = value === 0 ? '#bac9c7' : '#55706b88';
    draw.beginPath();
    draw.moveTo(left - 3, y(value));
    draw.lineTo(right, y(value));
    draw.stroke();
    draw.fillText(String(value), left - 7, y(value));
  }
  draw.fillText('cm/s', left - 5, 9);
  draw.textAlign = 'center';
  for (let i = 0; i <= 4; i += 1) {
    const value = xMax * i / 4;
    draw.fillText(value.toFixed(1) + ' s', x(value), bottom + 16);
  }
  draw.save();
  draw.beginPath();
  draw.rect(left, top, right - left, bottom - top);
  draw.clip();
  draw.strokeStyle = '#bcebe2';
  draw.lineWidth = 1;
  draw.beginPath();
  timeSeconds.forEach((time, index) => {
    if (index === 0) draw.moveTo(x(time), y(envelopeCmS[index]));
    else draw.lineTo(x(time), y(envelopeCmS[index]));
  });
  draw.stroke();
  for (const [time, velocity] of [
    [measurements?.psvTimeSeconds, measurements?.psvCmS],
    [measurements?.edvTimeSeconds, measurements?.edvCmS],
  ]) {
    if (!Number.isFinite(time) || !Number.isFinite(velocity)) continue;
    draw.fillStyle = near;
    draw.beginPath();
    draw.arc(x(time), y(sample.beamDirection === 'away' ? -velocity : velocity), 3.1, 0, Math.PI * 2);
    draw.fill();
  }
  draw.restore();
}

export async function createReconstruction(canvas, protocol, onPreset) {
  const THREE = await import('../vendor/build/three.module.js');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor('#0d191a');
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, .1, 4000);
  const observed = new THREE.Group();
  const remaining = new THREE.Group();
  const plane = new THREE.Group();
  const canonicalMeshes = new Map();
  const patchCache = new Map();
  scene.add(observed, remaining, plane, new THREE.HemisphereLight('#efeeff', '#293a48', 2.3));
  const light = new THREE.DirectionalLight('#ffefe1', 2.1);
  light.position.set(-70, 180, 135);
  scene.add(light);
  const traces = Object.entries(protocol.tracking);
  const centerOf = (frame) => {
    if (frame.center) return frame.center;
    const points = (frame.contours ?? []).flat();
    if (!points.length) return frame.contact;
    return points.reduce((mean, point) => mean.map((value, axis) => value + point[axis] / points.length), [0, 0, 0]);
  };
  const point = (xyz) => new THREE.Vector3(...xyz);
  const bounds = new THREE.Box3();
  for (const [, frames] of traces) {
    for (const frame of frames) {
      bounds.expandByPoint(point(centerOf(frame)));
      for (const xyz of (frame.contours ?? []).flat()) bounds.expandByPoint(point(xyz));
    }
  }
  for (const station of protocol.stations) {
    for (const view of Object.values(station.views ?? {})) {
      if (view.contact && view.beam) {
        bounds.expandByPoint(point(view.contact));
        bounds.expandByPoint(point(view.contact).addScaledVector(point(view.beam), -40));
      }
    }
  }
  if (bounds.isEmpty()) throw new Error('Sample traces unavailable.');
  const pivot = bounds.getCenter(new THREE.Vector3());
  const span = Math.max(30, bounds.getSize(new THREE.Vector3()).length() / 2 + 10);
  const traceMaterial = new THREE.LineDashedMaterial({ color: '#9eaead', transparent: true, opacity: .65, dashSize: 2, gapSize: 1.7 });
  const ringMaterial = new THREE.LineBasicMaterial({ color: '#88dfca', transparent: true, opacity: .9 });
  const patchMaterial = new THREE.MeshStandardMaterial({ color: '#438f7e', roughness: .76, side: THREE.DoubleSide });
  const probeMaterial = new THREE.LineBasicMaterial({ color: '#ffd693' });
  const probe = new THREE.Group();
  const probeSurface = new THREE.MeshStandardMaterial({ color: '#dce7e3', roughness: .75 });
  const probeFace = new THREE.MeshStandardMaterial({ color: '#1d3d3f', roughness: .72 });
  const lens = new THREE.Mesh(new THREE.BoxGeometry(30, 8, 2), probeFace);
  lens.position.z = 1;
  const head = new THREE.Mesh(new THREE.BoxGeometry(32, 12, 13), probeSurface);
  head.position.z = 8;
  const grip = new THREE.Mesh(new THREE.CylinderGeometry(5, 8, 22, 20), probeSurface);
  grip.rotation.x = Math.PI / 2;
  grip.position.z = 25;
  probe.add(lens, head, grip);
  probe.visible = false;
  scene.add(probe);
  let selectedSide = 'right';
  let preset = 'oblique';
  let lastPreset = 'oblique';
  let yaw = .82;
  let pitch = .34;
  let zoom = 1;
  let pointer;
  let lastCapture = null;
  let skin;
  let skinDepth;
  function render() {
    const box = canvas.getBoundingClientRect();
    if (!box.width || !box.height) return;
    renderer.setSize(box.width, box.height, false);
    const aspect = box.width / box.height;
    const height = Math.max(span, span / aspect) / zoom;
    Object.assign(camera, { left: -height * aspect, right: height * aspect, top: height, bottom: -height });
    camera.updateProjectionMatrix();
    camera.up.set(0, preset === 'axial' ? 1 : 0, preset === 'axial' ? 0 : 1);
    camera.position.set(Math.sin(yaw) * Math.cos(pitch), Math.cos(yaw) * Math.cos(pitch), Math.sin(pitch));
    camera.position.multiplyScalar(span * 9).add(pivot);
    camera.lookAt(pivot);
    renderer.render(scene, camera);
  }
  function line(group, xyz, material, closed = false) {
    if (xyz.length < 2) return;
    const geometry = new THREE.BufferGeometry().setFromPoints(xyz.map(point));
    const object = closed ? new THREE.LineLoop(geometry, material) : new THREE.Line(geometry, material);
    if (material.isLineDashedMaterial) object.computeLineDistances();
    group.add(object);
  }
  function clear(group) {
    for (const child of [...group.children]) {
      if (!child.userData.cached) child.geometry.dispose();
      group.remove(child);
    }
  }
  function connect(id, first, second) {
    if (!first.length || !second.length || first.length !== second.length) return;
    if (patchCache.has(id)) {
      observed.add(...patchCache.get(id));
      return;
    }
    const sample = (points, i) => points[Math.floor(i * points.length / 32)];
    const distance = (a, b) => a.reduce((sum, value, axis) => sum + (value - b[axis]) ** 2, 0);
    const mean = (points) => points.reduce((out, xyz) => out.map((value, i) => value + xyz[i] / points.length), [0, 0, 0]);
    const available = [...second];
    const patches = [];
    for (const ring of first) {
      const center = mean(ring);
      available.sort((a, b) => distance(center, mean(a)) - distance(center, mean(b)));
      const neighbor = available.shift();
      let best = { offset: 0, sign: 1, cost: Infinity };
      for (const sign of [1, -1]) {
        for (let offset = 0; offset < 32; offset += 1) {
          const cost = Array.from({ length: 32 }, (_, i) => distance(sample(ring, i), sample(neighbor, (i * sign + offset + 32) % 32)))
            .reduce((total, value) => total + value, 0);
          if (cost < best.cost) best = { offset, sign, cost };
        }
      }
      const vertices = [];
      for (let i = 0; i < 32; i += 1) {
        const j = (i + 1) % 32;
        const a = sample(ring, i), b = sample(ring, j);
        const c = sample(neighbor, (i * best.sign + best.offset + 32) % 32);
        const d = sample(neighbor, (j * best.sign + best.offset + 32) % 32);
        vertices.push(...a, ...b, ...c, ...c, ...b, ...d);
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geometry.computeVertexNormals();
      const patch = new THREE.Mesh(geometry, patchMaterial);
      patch.userData.cached = true;
      patches.push(patch);
    }
    patchCache.set(id, patches);
    observed.add(...patches);
  }
  function update(captured, active, side) {
    if (side && side !== selectedSide) {
      selectedSide = side;
      setPreset(lastPreset, false);
    }
    const signature = [...captured].join('|');
    if (signature !== lastCapture) {
      clear(observed);
      clear(remaining);
      lastCapture = signature;
      for (const [side, frames] of traces) {
        const canonical = canonicalMeshes.get(side);
        const completed = frames.every((frame) => captured.has(side + '/' + frame.id));
        if (canonical) canonical.visible = completed;
        if (completed && canonical) continue;
        frames.forEach((frame, index) => {
          const has = captured.has(side + '/' + frame.id);
          const next = frames[index + 1];
          if (has) {
            for (const ring of frame.contours ?? []) line(observed, ring, ringMaterial, true);
          }
          if (!next) return;
          if (has && captured.has(side + '/' + next.id)) connect(side + '/' + frame.id, frame.contours ?? [], next.contours ?? []);
          else line(remaining, [centerOf(frame), centerOf(next)], traceMaterial);
        });
      }
    }
    clear(plane);
    probe.visible = false;
    if (active?.contact && active.width && active.beam) {
      const base = point(active.contact);
      const across = point(active.width);
      const depth = point(active.beam);
      const [centerX, centerY] = active.centerPx;
      const corners = [[0, 0], [active.widthPx, 0], [active.widthPx, active.heightPx], [0, active.heightPx]];
      line(plane, corners.map(([x, y]) => base.clone()
        .addScaledVector(across, (x - centerX) * active.mmPerPx)
        .addScaledVector(depth, (y - centerY) * active.mmPerPx).toArray()), probeMaterial, true);
      const outward = depth.clone().negate();
      const elevation = outward.clone().cross(across);
      const basis = new THREE.Matrix4().makeBasis(across, elevation, outward);
      probe.position.copy(base);
      probe.quaternion.setFromRotationMatrix(basis);
      probe.scale.x = (active.faceWidthMm ?? active.widthPx * active.mmPerPx) / 30;
      probe.visible = true;
    }
    render();
  }
  function exportMesh() {
    const points = [];
    const triangles = [];
    const visible = [...observed.children, ...[...canonicalMeshes.values()].filter((mesh) => mesh.visible)];
    for (const child of visible) {
      const positions = child.geometry.getAttribute('position');
      const offset = points.length;
      for (let i = 0; i < positions.count; i += 1) {
        points.push([positions.getX(i), positions.getY(i), positions.getZ(i)].map((value) => value.toFixed(5)).join(' '));
      }
      if (child.isMesh) {
        const indices = child.geometry.getIndex();
        const index = (i) => (indices ? indices.getX(i) : i) + offset;
        for (let i = 0; i < (indices?.count ?? positions.count); i += 3) {
          triangles.push(`3 ${index(i)} ${index(i + 1)} ${index(i + 2)}`);
        }
      }
    }
    if (!points.length) return '';
    const source = protocol.anatomySource;
    const credits = [source?.title ?? source?.label, source && 'BodyParts3D, Database Center for Life Science',
      source?.url, source?.license, source?.licenseUrl]
      .filter(Boolean).map((value) => 'comment ' + value.replace(/[^\x20-\x7e]/g, ' '));
    return ['ply', 'format ascii 1.0', 'comment Native RAS millimetres',
      'comment Captured transverse carotid reconstruction', ...credits,
      'element vertex ' + points.length, 'property float x', 'property float y', 'property float z',
      'element face ' + triangles.length, 'property list uchar int vertex_indices', 'end_header',
      ...points, ...triangles, ''].join('\n');
  }
  function setPreset(name, draw = true) {
    const sign = selectedSide === 'right' ? 1 : -1;
    const settings = {
      oblique: [.82 * sign, .34], axial: [0, Math.PI / 2], coronal: [0, 0], sagittal: [Math.PI / 2 * sign, 0],
    }[name];
    if (!settings) return;
    [yaw, pitch] = settings;
    preset = lastPreset = name;
    zoom = 1;
    onPreset(name);
    if (draw) render();
  }
  function setOpacity(value) {
    if (!skin || !skinDepth) return;
    const opacity = Math.max(0, Math.min(1, value));
    skin.visible = opacity > 0;
    skin.material.opacity = opacity;
    skin.material.depthWrite = opacity === 1;
    skin.material.transparent = opacity < 1;
    skinDepth.visible = opacity > 0 && opacity < 1;
    render();
  }
  canvas.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) return;
    pointer = [event.clientX, event.clientY];
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener('pointermove', (event) => {
    if (!pointer || !canvas.hasPointerCapture(event.pointerId)) return;
    yaw -= (event.clientX - pointer[0]) * .009;
    pitch = Math.max(-1.35, Math.min(1.35, pitch + (event.clientY - pointer[1]) * .009));
    pointer = [event.clientX, event.clientY];
    preset = null;
    onPreset(null);
    render();
  });
  canvas.addEventListener('lostpointercapture', () => { pointer = null; });
  canvas.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', '+', '=', '-'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'Home') { setPreset(lastPreset); return; }
    if (event.key.startsWith('Arrow')) {
      preset = null;
      pitch = Math.max(-1.35, Math.min(1.35, pitch));
      onPreset(null);
    }
    if (event.key === 'ArrowLeft') yaw -= .12;
    if (event.key === 'ArrowRight') yaw += .12;
    if (event.key === 'ArrowUp') pitch = Math.min(1.35, pitch + .12);
    if (event.key === 'ArrowDown') pitch = Math.max(-1.35, pitch - .12);
    if (event.key === '-' || event.key === '+' || event.key === '=') {
      zoom = Math.max(.6, Math.min(3, zoom * (event.key === '-' ? .88 : 1.14)));
    }
    render();
  });
  new ResizeObserver(render).observe(canvas);
  async function meshGeometry(path) {
      const response = await fetch(new URL(path, new URL('./data/', document.baseURI)));
      if (!response.ok) throw new Error('Mesh unavailable: ' + path);
      const buffer = await response.arrayBuffer();
      const header = new DataView(buffer);
      const vertices = header.getUint32(0, true);
      const faces = header.getUint32(4, true);
      if (!vertices || !faces || buffer.byteLength !== 8 + 12 * (vertices + faces)) throw new Error('Invalid packed mesh: ' + path);
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buffer, 8, 3 * vertices), 3));
      geometry.setIndex(new THREE.BufferAttribute(new Uint32Array(buffer, 8 + 12 * vertices, 3 * faces), 1));
      geometry.computeVertexNormals();
      return geometry;
  }
  const completeAssets = Object.entries(protocol.reconstructions ?? {}).map(async ([side, reconstruction]) => {
    const geometry = await meshGeometry(reconstruction.reconstructionPath);
    const mesh = new THREE.Mesh(geometry, patchMaterial);
    mesh.visible = false;
    canonicalMeshes.set(side, mesh);
    scene.add(mesh);
  });
  if (protocol.context?.skinPath) {
    completeAssets.push(meshGeometry(protocol.context.skinPath).then((geometry) => {
      skinDepth = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
        transparent: true, colorWrite: false, depthWrite: true,
        polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
      }));
      skinDepth.renderOrder = 3;
      skin = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: '#be9885',
        transparent: true, opacity: .32, depthWrite: false, roughness: .95 }));
      skin.renderOrder = 4;
      scene.add(skinDepth, skin);
      render();
    }));
  }
  for (const result of await Promise.allSettled(completeAssets)) {
    if (result.status === 'rejected') console.warn('Carotid context unavailable.', result.reason);
  }
  return { update, setPreset, setOpacity, exportMesh };
}
