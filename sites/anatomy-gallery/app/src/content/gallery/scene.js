import { identifyPoster } from './poster.js';
import * as T from './vendor/build/three.module.js';
import { OrbitControls } from './vendor/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from './vendor/examples/jsm/loaders/GLTFLoader.js';

export async function loadScene(container, buffer, view, signal, recipe) {
  const manager = new T.LoadingManager();
  manager.setURLModifier((url) => {
    if (url.startsWith('blob:') || url.startsWith('data:')) return url;
    throw Error('Use a self-contained GLB with embedded resources.');
  });
  const gltf = await new GLTFLoader(manager).parseAsync(buffer, '');
  const root = gltf.scene;
  const meshes = [];
  root.traverse((mesh) => {
    if (!mesh.isMesh) return;
    let node = mesh;
    while (node && gltf.parser.associations.get(node)?.nodes === undefined) node = node.parent;
    const index = node && gltf.parser.associations.get(node)?.nodes;
    meshes.push({
      mesh,
      name: gltf.parser.json.nodes?.[index]?.name || mesh.name || 'Mesh',
      original: mesh.material,
    });
  });
  const neutral = new T.MeshStandardMaterial({ color: 0xc7beb0, roughness: 0.78 });
  let renderer, controls, observer, mixer;
  function dispose() {
    mixer?.stopAllAction();
    mixer?.uncacheRoot(root);
    observer?.disconnect();
    controls?.dispose();
    const resources = new Set([neutral]);
    for (const { mesh, original } of meshes) {
      resources.add(mesh.geometry);
      for (const material of [original].flat()) {
        resources.add(material);
        for (const value of Object.values(material)) if (value?.isTexture) resources.add(value);
      }
    }
    for (const res of resources) res.dispose();
    renderer?.domElement.remove();
    renderer?.dispose();
    renderer?.forceContextLoss();
  }
  try {
    signal.throwIfAborted();
    renderer = new T.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    const scene = new T.Scene();
    scene.background = new T.Color('#e8ede5');
    scene.add(root, new T.HemisphereLight(0xffffff, 0x746859, 2));
    const key = new T.DirectionalLight(0xffefd6, 2.2);
    key.position.set(2, 3, 3);
    scene.add(key);
    const camera = new T.OrthographicCamera(-1, 1, 1, -1, 0.00001, 10000);
    container.append(renderer.domElement);
    controls = new OrbitControls(camera, renderer.domElement);
    controls.minZoom = 0.1;
    controls.maxZoom = 20;
    let height = 1;
    function draw() {
      renderer.render(scene, camera);
    }
    function resize() {
      const w = container.clientWidth,
        h = container.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      Object.assign(camera, {
        left: (-height * w) / h / 2,
        right: (height * w) / h / 2,
        top: height / 2,
        bottom: -height / 2,
      });
      camera.updateProjectionMatrix();
      draw();
    }
    const clip = recipe?.clip && gltf.animations.find((animation) => animation.name === recipe.clip);
    if (recipe?.clip && !clip) throw Error('The authored animation is unavailable.');
    const action = clip && (mixer = new T.AnimationMixer(root)).clipAction(clip);
    if (action) {
      action.setLoop(T.LoopOnce, 1);
      action.clampWhenFinished = true;
      action.play();
    }
    const nodeNames = new Set(meshes.map((part) => part.name));
    for (const group of Object.values(recipe?.groups ?? {})) {
      if (group?.some((name) => !nodeNames.has(name))) throw Error('The teaching selection differs from the pinned export.');
    }
    function apply(v) {
      if (action) {
        action.paused = false;
        action.enabled = true;
        mixer.setTime(v.phase * clip.duration);
        root.updateMatrixWorld(true);
      }
      const group = recipe?.groups?.[v.part];
      const bounds = new T.Box3();
      for (const { mesh, name, original } of meshes) {
        mesh.visible = recipe?.groups ? !group || group.includes(name) : v.part === 'All structures' || name === v.part;
        mesh.material = v.material === 'Neutral' ? neutral : original;
        if (mesh.visible) bounds.union(new T.Box3().setFromObject(mesh));
      }
      if (bounds.isEmpty()) throw Error('The selected part is unavailable in this export.');
      key.intensity = 2.2 * v.light;
      const center = bounds.getCenter(new T.Vector3()),
        size = bounds.getSize(new T.Vector3());
      height = Math.max(size.length() * 1.15, 0.0001);
      controls.target.copy(center);
      camera.position
        .copy(center)
        .addScaledVector(new T.Vector3(0.296, 0.5, -0.814).normalize(), height * 2);
      camera.zoom = 1;
      if (v.camera) {
        height = v.camera.height;
        camera.position.fromArray(v.camera.position);
        controls.target.fromArray(v.camera.target);
      }
      controls.update();
      resize();
    }
    controls.addEventListener('change', draw);
    observer = new ResizeObserver(resize);
    observer.observe(container);
    apply(view);
    return {
      apply,
      dispose,
      names: [...new Set(meshes.map((m) => m.name))],
      camera: () => ({
        position: camera.position.toArray(),
        target: controls.target.toArray(),
        height: height / camera.zoom,
      }),
      export: async (source) => {
        const width = 1200,
          outputHeight = 960;
        const originalRatio = renderer.getPixelRatio();
        let encoded;
        try {
          renderer.setPixelRatio(1);
          renderer.setSize(width, outputHeight, false);
          camera.right = (height * width) / outputHeight / 2;
          camera.left = -camera.right;
          camera.updateProjectionMatrix();
          draw();
          encoded = new Promise((resolve, reject) =>
            renderer.domElement.toBlob(
              (blob) =>
                blob?.type === 'image/webp'
                  ? resolve(blob)
                  : reject(Error('WebP export is unavailable.')),
              'image/webp',
              0.92,
            ),
          );
        } finally {
          renderer.setPixelRatio(originalRatio);
          resize();
        }
        return identifyPoster(
          await encoded,
          width,
          outputHeight,
          source,
          'Three.js r' + T.REVISION + ' · ' + view.version,
        );
      },
    };
  } catch (error) {
    dispose();
    throw error;
  }
}
