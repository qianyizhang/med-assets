import {DEFAULT_QUALITY, getModel, bindLayers, loadExactModel} from './model-contract.mjs';
import {selectMode, applyVisibility, restoreContext} from './view-state.mjs';

const $ = selector => document.querySelector(selector);
let lang = 'en';
try { if (localStorage.getItem('dental-language') === 'zh') lang = 'zh'; } catch {}
let state = selectMode('all');
let quality = DEFAULT_QUALITY;
let savedView = null;
let phase = 'idle';
let runtime = null;
let controller = null;
let pendingTimeout = null;
let generation = 0;

const labels = {
  enamel: ['Enamel label', '釉质标签'], dentin: ['Dentin label', '牙本质标签'],
  pulp: ['Pulp-space label', '牙髓空间标签'], bone: ['Bone label', '骨标签'],
};
const context = {
  all: ['Whole specimen · 4 source labels', '完整标本 · 4 个来源标签',
    'Original specimen positions. Outer labels may obscure inner ones; isolate a label to reveal it without moving any geometry.',
    '保持原始标本位置。外层可能遮挡内层；单独显示可看清标签，无需移动几何。'],
  tooth: ['Tooth-label context · bone hidden', '牙体标签关系 · 骨已隐藏',
    'Enamel, dentin and pulp-space labels in their shared source frame. Hiding bone is for visibility, not a claim that the tooth is detached or jaw-registered.',
    '釉质、牙本质与牙髓空间标签保持共同来源坐标。隐藏骨仅为看清，不表示牙齿已被拔出或已配准入颌骨。'],
  enamel: ['Enamel label · isolated', '釉质标签 · 单独显示',
    'Other labels are hidden, not removed. This prepared-specimen label is not an intact healthy enamel shell; openings and islands are not disease findings.',
    '其他标签只是隐藏，未被删除。该制备标本的标签不等同于健康完整釉质壳；开口与碎片不代表疾病。'],
  dentin: ['Dentin label · isolated', '牙本质标签 · 单独显示',
    'Inspect the source-labelled dentin body without outer-layer occlusion. Its surface and preparation features are not independently validated anatomy.',
    '排除外层遮挡，检查来源标注的牙本质主体。其表面与制备特征不代表经独立验证的解剖。'],
  pulp: ['Pulp-space label · isolated', '牙髓空间标签 · 单独显示',
    'A narrow source segmentation label, not a nerve/vessel model or a validated complete root canal. Restore context to compare its location.',
    '狭窄的来源分割标签，不是神经／血管模型，也不代表已验证的完整根管。恢复完整标本以对照位置。'],
  bone: ['Bone label · isolated', '骨标签 · 单独显示',
    'This label reaches the source-volume boundary. Its cropped extent is not the complete surrounding jaw, and it is not registered to the separate BP3D dental arch.',
    '该标签达到来源体数据边界。截断范围不是完整周围颌骨，也未与独立 BP3D 牙弓配准。'],
};
const statuses = {
  idle: ['3D is optional. Choose Open 3D layer view to begin.', '三维为可选功能。选择“打开三维分层视图”开始。'],
  loading: ['Loading the exact candidate; checking compressed and GLB hashes…', '正在加载精确候选；校验压缩文件与 GLB 哈希…'],
  ready: ['Exact candidate verified. Layer controls are ready.', '精确候选已校验，可以切换分层。'],
  failed: ['3D could not load here. Static evidence remains available below.', '此环境无法加载三维。下方静态证据仍可查看。'],
  lost: ['3D context was lost. Use static evidence or try loading again.', '三维上下文已丢失。可查看静态证据或重新加载。'],
};
const text = pair => pair[lang === 'zh' ? 1 : 0];
const qualityNames = {balanced: ['Balanced draft', '均衡草稿'], detailed: ['Detailed reference', '详细参考']};

function updateQuality() {
  const model = getModel(quality);
  $('#quality').value = quality;
  $('#quality-note').textContent = quality === 'balanced'
    ? text(['105,370 triangles · 0.89 MB download. Smaller teaching draft; smoother fine surfaces and coarser bone. Not identical detail or clinical validation.',
      '105,370 三角面 · 下载 0.89 MB。较小的教学草稿；细表面更平滑、骨表面更粗。并非细节完全一致或临床验证。'])
    : text(['1,328,980 triangles · 7.65 MB download. Unchanged retained detailed candidate, not the master or anatomical ground truth.',
      '1,328,980 三角面 · 下载 7.65 MB。未改动的保留详细候选，不是主模型或解剖真值。']);
  $('#download-size').textContent = text(['Selected download: ', '所选下载：'])
    + (model.compressedBytes / 1e6).toFixed(2) + text([' MB compressed. Only this model loads when opened.', ' MB（压缩）。打开时仅加载所选模型。']);
  $('#model-metrics').textContent = text(qualityNames[quality]) + ' · ' + model.bytes.toLocaleString('en-US')
    + text([' GLB bytes · ', ' GLB 字节 · ']) + model.triangles.toLocaleString('en-US') + text([' triangles', ' 三角面']);
  $('#model-hash').textContent = model.sha256;
  $('#model-download').setAttribute('href', model.url);
  $('#viewport').dataset.quality = quality;
}

function updateContext() {
  const copy = context[state.mode];
  $('#context-title').textContent = copy[lang === 'zh' ? 1 : 0];
  $('#context-description').textContent = copy[lang === 'zh' ? 3 : 2];
  $('#visible-labels').textContent = text(phase === 'ready' ? ['Showing: ', '显示：'] : ['Preset: ', '预设：'])
    + state.visible.map(key => text(labels[key])).join(' · ');
  document.querySelectorAll('[data-mode]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.mode === state.mode));
  });
  $('#viewport').dataset.mode = state.mode;
}

function translate() {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-en]').forEach(element => { element.textContent = element.dataset[lang]; });
  $('#language').textContent = lang === 'en' ? '中文' : 'English';
  $('#status').textContent = text(qualityNames[quality]) + ' — ' + text(statuses[phase]);
  $('#integrity').textContent = phase === 'ready'
    ? text(['Compressed and decompressed bytes verified in this session.', '本次会话已核验压缩与解压后字节。'])
    : text(['No current rendered view is verified. Static evidence is separate.', '目前没有已核验的渲染视图。静态证据单独保留。']);
  runtime?.renderer.domElement.setAttribute('aria-label', text(['FDI 31 source-labelled specimen', 'FDI 31 来源分层标本']));
  updateContext();
  updateQuality();
  try { localStorage.setItem('dental-language', lang); } catch {}
}

function setPhase(next) {
  phase = next;
  $('#status').dataset.phase = next;
  if (next !== 'ready') { delete $('#status').dataset.sha256; delete $('#status').dataset.quality; }
  $('#layer-controls').disabled = next !== 'ready';
  $('#load').hidden = next !== 'idle';
  $('#retry').hidden = !['failed', 'lost'].includes(next);
  $('#placeholder').hidden = next === 'ready';
  translate();
}

function cleanup() {
  if (!runtime) return;
  runtime.observer?.disconnect();
  runtime.controls?.dispose();
  runtime.root?.traverse(object => {
    if (!object.isMesh) return;
    object.geometry.dispose();
    for (const material of [].concat(object.material)) material.dispose();
  });
  runtime.renderer.domElement.remove();
  runtime.renderer.dispose();
  runtime = null;
}

async function load(switching = false) {
  if (!switching && (phase === 'loading' || phase === 'ready')) return;
  const current = ++generation;
  controller?.abort();
  clearTimeout(pendingTimeout);
  if (runtime?.captureView) savedView = runtime.captureView();
  cleanup();
  const selectedQuality = quality;
  const model = getModel(selectedQuality);
  const attemptController = new AbortController();
  controller = attemptController;
  const timeout = setTimeout(() => {
    if (current !== generation) return;
    generation++;
    attemptController.abort();
    pendingTimeout = null;
    cleanup();
    $('#status').dataset.failure = 'Model loading timed out';
    setPhase('failed');
  }, 45000);
  pendingTimeout = timeout;
  setPhase('loading');
  try {
    const [THREE, {GLTFLoader}, {OrbitControls}] = await Promise.all([
      import('three'),
      import('/review/uff-tomo1b/payload/viewer/vendor/GLTFLoader.js'),
      import('/review/uff-tomo1b/payload/viewer/vendor/OrbitControls.js'),
    ]);
    if (current !== generation) return;
    // Establish WebGL support before transferring the large optional model.
    const renderer = new THREE.WebGLRenderer({antialias: true});
    runtime = {renderer};
    // Listen before fetch/parse: a context can disappear while the model loads.
    renderer.domElement.addEventListener('webglcontextlost', event => {
      event.preventDefault();
      if (current !== generation) return;
      generation++;
      attemptController.abort();
      clearTimeout(timeout);
      if (pendingTimeout === timeout) pendingTimeout = null;
      cleanup();
      setPhase('lost');
    });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    const bytes = await loadExactModel(location.origin, attemptController.signal, selectedQuality);
    if (current !== generation) return;
    const asset = await new GLTFLoader().parseAsync(bytes.buffer, '');
    if (current !== generation) {
      asset.scene.traverse(object => { if (object.isMesh) { object.geometry.dispose(); for (const material of [].concat(object.material)) material.dispose(); } });
      return;
    }
    runtime.root = asset.scene;
    const nodes = bindLayers(asset);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#202725');
    scene.add(asset.scene);
    // Preserve the retained vertex colors/materials and untransformed geometry.
    scene.add(new THREE.HemisphereLight(0xffffff, 0x5b5c52, 2));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.3);
    keyLight.position.set(.03, -.04, .045);
    scene.add(keyLight);
    const box = new THREE.Box3().setFromObject(asset.scene);
    // Reuse the first view's framing across quality switches, not model transforms.
    const center = savedView?.frameCenter.clone() ?? box.getCenter(new THREE.Vector3());
    const radius = savedView?.radius ?? box.getSize(new THREE.Vector3()).length() / 2;
    const camera = new THREE.OrthographicCamera(-radius, radius, radius, -radius, radius / 1000, radius * 20);
    camera.up.set(0, 0, 1);
    const controls = new OrbitControls(camera, renderer.domElement);
    runtime.controls = controls;
    runtime.nodes = nodes;
    controls.enableDamping = false;
    controls.minZoom = .4;
    controls.maxZoom = 8;
    const render = () => renderer.render(scene, camera);
    runtime.render = render;
    const resetCamera = () => {
      camera.position.copy(center).add(new THREE.Vector3(.5, -1, .45).normalize().multiplyScalar(radius * 4));
      camera.zoom = 1;
      controls.target.copy(center);
      camera.lookAt(center);
      camera.updateProjectionMatrix();
      controls.update();
    };
    runtime.resetCamera = resetCamera;
    runtime.captureView = () => ({
      position: camera.position.clone(), quaternion: camera.quaternion.clone(),
      target: controls.target.clone(), zoom: camera.zoom, frameCenter: center.clone(), radius,
    });
    const viewport = $('#viewport');
    viewport.append(renderer.domElement);
    const resize = () => {
      const width = viewport.clientWidth, height = viewport.clientHeight;
      if (!width || !height) return;
      const aspect = width / height;
      const span = radius * 1.12 * Math.max(1, 1 / aspect);
      camera.left = -span * aspect; camera.right = span * aspect;
      camera.top = span; camera.bottom = -span;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
      render();
    };
    runtime.observer = new ResizeObserver(resize);
    runtime.observer.observe(viewport);
    controls.addEventListener('change', render);
    applyVisibility(nodes, state);
    resetCamera();
    if (savedView) {
      camera.position.copy(savedView.position);
      camera.quaternion.copy(savedView.quaternion);
      camera.zoom = savedView.zoom;
      controls.target.copy(savedView.target);
      camera.updateProjectionMatrix();
      controls.update();
    }
    resize();
    savedView = null;
    $('#status').dataset.sha256 = model.sha256;
    $('#status').dataset.quality = selectedQuality;
    delete $('#status').dataset.failure;
    setPhase('ready');
  } catch (error) {
    if (current !== generation) return;
    cleanup();
    $('#status').dataset.failure = String(error);
    setPhase('failed');
  } finally {
    clearTimeout(timeout);
    if (pendingTimeout === timeout) pendingTimeout = null;
  }
}

document.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', () => {
  if (phase !== 'ready') return;
  state = selectMode(button.dataset.mode);
  applyVisibility(runtime.nodes, state);
  updateContext();
  runtime.render();
}));
$('#restore').addEventListener('click', () => {
  if (phase !== 'ready') return;
  state = restoreContext(runtime.nodes, runtime.resetCamera);
  updateContext();
  runtime.render();
});
$('#language').addEventListener('click', () => { lang = lang === 'en' ? 'zh' : 'en'; translate(); });
$('#quality').addEventListener('change', () => {
  const next = $('#quality').value;
  if (next === quality) return;
  getModel(next); // Reject unsupported selections before touching the active model.
  quality = next;
  if (phase === 'ready' || phase === 'loading') return load(true);
  // Before opening, or after a failure, selection alone never starts a download.
  translate();
});
$('#load').addEventListener('click', () => load());
$('#retry').addEventListener('click', () => load());
window.addEventListener('pagehide', () => {
  generation++;
  controller?.abort();
  clearTimeout(pendingTimeout);
  pendingTimeout = null;
  cleanup();
});
window.addEventListener('pageshow', event => {
  // Back/Forward cache can resume a disposed view: do not leave stale enabled controls.
  if (event.persisted) { state = selectMode('all'); savedView = null; setPhase('idle'); }
});
setPhase('idle');
