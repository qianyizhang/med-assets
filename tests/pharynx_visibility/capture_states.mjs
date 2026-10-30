// Record visibility selected by the actual controller on the exact GLB.
import {readFileSync, writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import {createInspection, fitVisibleParts, SOURCE_SHA256} from '../../gallery/pharynx_larynx/visibility-r01/pharynx-inspection.mjs';
const require = createRequire(pathToFileURL(resolve(process.env.PHARYNX_TEST_DEPS, 'package.json')));
const {GLTFLoader} = await import(pathToFileURL(require.resolve('three/examples/jsm/loaders/GLTFLoader.js')));
const THREE = require('three');
const raw = readFileSync(new URL('../../models/pharynx_larynx/exports/r03/pharynx_larynx.glb', import.meta.url));
const sha = value => createHash('sha256').update(value).digest('hex');
assert.equal(sha(raw), SOURCE_SHA256);
const record = JSON.parse(readFileSync(new URL('./fixtures/record-excerpt.json', import.meta.url)));
const {scene} = await new GLTFLoader().parseAsync(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength), '');
const controller = createInspection(record, scene), states = {};
for (const [label, mode] of [['baseline', 'all'], ['cartilage', 'cartilage'], ['muscles', 'muscles'], ['reset', 'all']]) {
  controller.select(mode);
  states[label] = controller.items().filter(item => item.visible).map(item => item.id).sort();
}
const bounds = new THREE.Box3().setFromObject(scene), center = bounds.getCenter(new THREE.Vector3()), size = bounds.getSize(new THREE.Vector3());
const camera = new THREE.PerspectiveCamera(38, 1, .001, 1000);
const controls = {target: center.clone(), update() {}};
const direction = new THREE.Vector3(.6, .25, -1).normalize();
camera.position.copy(center).addScaledVector(direction, Math.max(size.x, size.y, size.z) * 2);
const cameras = [];
const capture = (label, state) => cameras.push({label, state, fovVerticalDegrees: camera.fov,
  aspect: camera.aspect, positionThree: camera.position.toArray(), targetThree: controls.target.toArray(),
  upThree: camera.up.toArray(), near: camera.near, far: camera.far});
controller.select('cartilage'); capture('cartilage-before-fit', 'cartilage');
fitVisibleParts(scene, camera, controls, THREE); capture('cartilage-after-fit', 'cartilage');
controller.select('all'); fitVisibleParts(scene, camera, controls, THREE); capture('all-fitted', 'baseline');
controller.select('cartilage'); fitVisibleParts(scene, camera, controls, THREE);
controller.select('all'); fitVisibleParts(scene, camera, controls, THREE); capture('reset-fitted', 'reset');
writeFileSync(process.argv[2], JSON.stringify({sourceSha256: SOURCE_SHA256, controllerSha256: sha(readFileSync(new URL('../../gallery/pharynx_larynx/visibility-r01/pharynx-inspection.mjs', import.meta.url))), threeVersion: require('three').REVISION, states, cameras}, null, 2) + '\n');
