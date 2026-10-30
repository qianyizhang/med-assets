// Record visibility selected by the actual controller on the exact GLB.
import {readFileSync, writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import {createInspection, SOURCE_SHA256} from '../../gallery/pharynx_larynx/visibility-r01/pharynx-inspection.mjs';
const require = createRequire(pathToFileURL(resolve(process.env.PHARYNX_TEST_DEPS, 'package.json')));
const {GLTFLoader} = await import(pathToFileURL(require.resolve('three/examples/jsm/loaders/GLTFLoader.js')));
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
writeFileSync(process.argv[2], JSON.stringify({sourceSha256: SOURCE_SHA256, controllerSha256: sha(readFileSync(new URL('../../gallery/pharynx_larynx/visibility-r01/pharynx-inspection.mjs', import.meta.url))), threeVersion: require('three').REVISION, states}, null, 2) + '\n');
