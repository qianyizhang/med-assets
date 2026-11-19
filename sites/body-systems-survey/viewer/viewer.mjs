import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const stage = document.querySelector("#stage");
const loading = document.querySelector("#loading");
const fallback = document.querySelector("#fallback");
const fallbackImage = document.querySelector("#fallback-image");
const sceneName = document.querySelector("#scene-name");
const heading = document.querySelector("#inspector-heading");
const description = document.querySelector("#description");
const partsPanel = document.querySelector("#parts");
const comparison = document.querySelector("#comparison");
const compare = document.querySelector("#compare");
const status = document.querySelector("#status");
const showAll = document.querySelector("#show-all");
const retry = document.querySelector("#retry");
const back = document.querySelector("#back");
const angleButtons = [...document.querySelectorAll("[data-angle]")];

const scene = new THREE.Scene();
scene.background = new THREE.Color("#eae8dd");
scene.add(new THREE.HemisphereLight(0xffffff, 0x767066, 2.15));
const key = new THREE.DirectionalLight(0xfff3db, 2);
key.position.set(2, 3, 3);
scene.add(key);
const fill = new THREE.DirectionalLight(0xdbe9ff, 1.45);
fill.position.set(-2, 1.5, -2);
scene.add(fill);
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.001, 30);
const models = new THREE.Group();
scene.add(models);

const loader = new GLTFLoader();
const cache = new Map();
const materials = new Map();
const state = {
  inComparison: false, variant: "raw", parts: new Map(), pair: [], task: 0,
  bounds: null, height: 1, aspect: 1,
};
let renderer;
let controls;
let current;
let catalog;

function inventory(gltf) {
  const nodes = [];
  gltf.scene.traverse(mesh => {
    if (!mesh.isMesh) return;
    // glTF names survive in the parser even when Three.js sanitizes mesh names.
    for (let node = mesh; node; node = node.parent) {
      const index = gltf.parser.associations.get(node)?.nodes;
      if (index === undefined) continue;
      const source = gltf.parser.json.nodes[index];
      const materialName = [mesh.material].flat().map(material => material.name).join(" ");
      nodes.push({ mesh, name: source.name, extras: source.extras ?? {}, materialName });
      return;
    }
  });
  return { root: gltf.scene, nodes };
}

function asset(input) {
  if (!cache.has(input.url)) {
    const request = loader.loadAsync(input.url).then(inventory).catch(error => {
      cache.delete(input.url);
      throw error;
    });
    cache.set(input.url, request);
  }
  return cache.get(input.url);
}

function material(style) {
  const id = `${style.color}/${style.alpha}`;
  if (!materials.has(id)) {
    materials.set(id, new THREE.MeshStandardMaterial({
      color: style.color, roughness: 0.78, opacity: style.alpha,
      transparent: style.alpha < 1, depthWrite: style.alpha === 1,
    }));
  }
  return materials.get(id);
}

function draw() {
  if (!renderer || renderer.domElement.hidden) return;
  renderer.render(scene, camera);
  renderer.domElement.dataset.triangles = renderer.info.render.triangles;
}

function frustum() {
  camera.top = state.height / 2;
  camera.bottom = -camera.top;
  camera.right = camera.top * state.aspect;
  camera.left = -camera.right;
  camera.updateProjectionMatrix();
}

function resize() {
  const width = stage.clientWidth;
  const height = stage.clientHeight;
  if (!width || !height) return;
  state.aspect = width / height;
  renderer.setSize(width, height, false);
  frustum();
  draw();
}

function setAngle(name) {
  if (!state.bounds) return;
  const center = state.bounds.getCenter(new THREE.Vector3());
  const size = state.bounds.getSize(new THREE.Vector3());
  const straight = state.inComparison ? [0, 0, 1] : current.direction;
  const direction = new THREE.Vector3(...straight);
  if (name === "reverse") direction.negate();
  if (name === "iso") {
    const side = new THREE.Vector3(direction.z, 0, -direction.x).normalize();
    direction.add(side).add(new THREE.Vector3(0, 1, 0)).normalize();
  }
  camera.position.copy(center).addScaledVector(direction, Math.max(size.length() * 3, 0.5));
  camera.lookAt(center);
  controls.target.copy(center);
  const inverse = camera.quaternion.clone().invert();
  const projected = new THREE.Box3();
  for (const x of [state.bounds.min.x, state.bounds.max.x]) {
    for (const y of [state.bounds.min.y, state.bounds.max.y]) {
      for (const z of [state.bounds.min.z, state.bounds.max.z]) {
        projected.expandByPoint(new THREE.Vector3(x, y, z).sub(center).applyQuaternion(inverse));
      }
    }
  }
  const dimensions = projected.getSize(new THREE.Vector3());
  state.height = Math.max(dimensions.y, dimensions.x / state.aspect) * 1.17;
  camera.zoom = 1;
  frustum();
  controls.update();
  draw();
}

function selectVariant() {
  if (state.pair.length !== 2) return;
  state.pair[0].visible = state.variant === "raw";
  state.pair[1].visible = state.variant === "workshop";
  stage.dataset.variant = state.variant;
  draw();
}

async function loadComparison() {
  const [raw, workshop] = await Promise.all(catalog.comparison.map(asset));
  const mask = raw.nodes.find(node => node.extras.source_label === "stomach");
  const smooth = workshop.nodes.find(node => node.extras.view_role === "surface");
  if (!mask || !smooth) throw new Error("A stomach surface is missing");
  return [mask, smooth].map(({ mesh }) => {
    mesh.updateWorldMatrix(true, false);
    const copy = mesh.clone(false);
    copy.matrix.copy(mesh.matrixWorld);
    copy.matrixAutoUpdate = false;
    copy.material = material({ color: "#cf8e38", alpha: 1 });
    return copy;
  });
}

async function loadModel() {
  const groups = new Map();
  const roots = [];
  const bounds = new THREE.Box3();
  const included = current.include ? new Set(current.include) : null;
  const loaded = await Promise.all(current.inputs.map(asset));
  for (const [i, { root, nodes }] of loaded.entries()) {
    const input = current.inputs[i];
    const rules = input.groups.map(style => ({ style, expression: new RegExp(style.pattern, "im") }));
    root.updateMatrixWorld(true);
    for (const node of nodes) {
      const { mesh, name, extras, materialName } = node;
      mesh.visible = (!included || included.has(name)) && (!input.surfaceOnly || extras.view_role === "surface");
      if (!mesh.visible) continue;
      const style = rules.find(rule => rule.expression.test(`${name}\n${materialName}`))?.style ?? input;
      if (!input.sourceMaterials) mesh.material = material(style);
      const color = input.sourceMaterials && [mesh.material].flat()[0]?.color
        ? "#" + [mesh.material].flat()[0].color.getHexString()
        : style.color;
      if (!groups.has(style.label)) groups.set(style.label, { color, meshes: [] });
      groups.get(style.label).meshes.push(mesh);
      bounds.union(new THREE.Box3().setFromObject(mesh));
    }
    roots.push(root);
  }
  if (bounds.isEmpty()) throw new Error("No selected mesh was found in the local assets");
  return { roots, groups, bounds };
}

function renderParts() {
  partsPanel.replaceChildren();
  showAll.hidden = state.parts.size === 0;
  for (const [label, group] of state.parts) {
    const row = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = group.meshes.some(mesh => mesh.visible);
    input.addEventListener("change", () => {
      group.meshes.forEach(mesh => { mesh.visible = input.checked; });
      status.textContent = [...partsPanel.querySelectorAll("input")].some(input => input.checked)
        ? "" : "All structures are hidden.";
      draw();
    });
    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.setAttribute("aria-hidden", "true");
    swatch.style.setProperty("--swatch", group.color);
    row.append(input, swatch, label);
    partsPanel.append(row);
  }
}

function showFallback(message, canRetry = false) {
  loading.hidden = true;
  if (renderer) renderer.domElement.hidden = true;
  if (current) {
    fallbackImage.src = current.fallback;
    fallbackImage.alt = `${current.title} · static gallery image`;
    fallback.hidden = false;
  }
  angleButtons.forEach(button => { button.disabled = true; });
  compare.disabled = true;
  document.querySelectorAll("#comparison input").forEach(input => { input.disabled = true; });
  status.textContent = message;
  retry.hidden = !canRetry;
}

async function activate(inComparison) {
  state.inComparison = inComparison;
  const task = ++state.task;
  const title = inComparison ? "Stomach comparison" : current.title;
  sceneName.textContent = title;
  heading.textContent = inComparison ? "Comparison" : "Structures";
  description.hidden = !inComparison;
  description.textContent = inComparison ? "Switch between two surfaces of the same stomach at the same camera position, zoom and color." : "";
  comparison.hidden = !inComparison;
  compare.textContent = inComparison ? "Back to assembly" : "Compare stomach";
  compare.setAttribute("aria-pressed", inComparison);
  retry.hidden = true;
  status.textContent = "";
  state.bounds = null;
  state.parts.clear();
  state.pair = [];
  stage.dataset.scene = "";
  stage.dataset.variant = "";
  renderParts();
  angleButtons.forEach(button => { button.disabled = true; });
  compare.disabled = true;
  document.querySelectorAll("#comparison input").forEach(input => { input.disabled = true; });

  if (!renderer) {
    showFallback("Interactive 3D needs WebGL2. Showing the static gallery image.");
    return;
  }
  fallback.hidden = true;
  renderer.domElement.hidden = false;
  renderer.domElement.setAttribute("aria-label", `${title} 3D viewer. Arrow keys rotate.`);
  models.clear();
  loading.hidden = false;
  draw();
  try {
    if (inComparison) {
      const pair = await loadComparison();
      if (task !== state.task) return;
      state.pair = pair;
      models.add(...pair);
      state.bounds = new THREE.Box3().setFromObject(models);
      document.querySelectorAll("#comparison input").forEach(input => { input.disabled = false; });
      selectVariant();
    } else {
      const model = await loadModel();
      if (task !== state.task) return;
      state.parts = model.groups;
      state.bounds = model.bounds;
      models.add(...model.roots);
    }
    loading.hidden = true;
    renderParts();
    angleButtons.forEach(button => { button.disabled = false; });
    compare.disabled = false;
    setAngle("straight");
    stage.dataset.scene = inComparison ? "stomach" : current.system;
  } catch (error) {
    if (task !== state.task) return;
    console.error(error);
    showFallback("The local model could not load. Showing the static gallery image.", true);
  }
}

function startRenderer() {
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  } catch (error) {
    console.error(error);
    return;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute("role", "img");
  stage.prepend(renderer.domElement);
  controls = new OrbitControls(camera, renderer.domElement);
  controls.minZoom = 0.45;
  controls.maxZoom = 12;
  controls.addEventListener("change", draw);
  renderer.domElement.addEventListener("keydown", event => {
    const arrow = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key];
    if (!arrow || !state.bounds) return;
    event.preventDefault();
    const orbit = new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
    orbit.theta += arrow[0] * 0.12;
    orbit.phi += arrow[1] * 0.12;
    camera.position.copy(new THREE.Vector3().setFromSpherical(orbit.makeSafe())).add(controls.target);
    controls.update();
    draw();
  });
  renderer.domElement.addEventListener("webglcontextlost", event => {
    event.preventDefault();
    ++state.task;
    showFallback("The 3D context stopped. Reload this page to restart.");
  });
  new ResizeObserver(resize).observe(stage);
  resize();
}

compare.addEventListener("click", () => activate(!state.inComparison));
angleButtons.forEach(button => button.addEventListener("click", () => setAngle(button.dataset.angle)));
comparison.addEventListener("change", event => {
  state.variant = event.target.value;
  selectVariant();
});
showAll.addEventListener("click", () => {
  for (const group of state.parts.values()) group.meshes.forEach(mesh => { mesh.visible = true; });
  renderParts();
  status.textContent = "";
  draw();
});
retry.addEventListener("click", () => activate(state.inComparison));

try {
  const response = await fetch("./catalog.json");
  if (!response.ok) throw new Error(`Model catalog HTTP ${response.status}`);
  catalog = await response.json();
  const selected = new URLSearchParams(location.search).get("scene");
  current = Object.hasOwn(catalog.scenes, selected) ? catalog.scenes[selected] : null;
  if (!current) {
    showFallback("Choose an assembly or model from the gallery.");
  } else {
    back.href = `${catalog.gallery}#${current.system}`;
    compare.hidden = !catalog.comparison || current.system !== "digestive";
    startRenderer();
    await activate(false);
  }
} catch (error) {
  console.error(error);
  showFallback("The local viewer catalog could not load. Reload this page or return to the gallery.");
}
