// Bounded viewer integration, not a repeated mesh-fidelity or clinical audit.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {registerHooks} from 'node:module';
import {MODELS, DEFAULT_QUALITY, getModel, loadExactModel, bindLayers, LAYERS} from '../../dist/fdi31/model-contract.mjs';

const vendor = new URL('../../dist/review/uff-tomo1b/payload/viewer/vendor/', import.meta.url);
registerHooks({resolve(specifier, context, next) {
  if (specifier === 'three') return {url: new URL('three.module.js', vendor).href, shortCircuit: true};
  return next(specifier, context);
}});
const {GLTFLoader} = await import(new URL('GLTFLoader.js', vendor));

for (const quality of Object.keys(MODELS)) {
  test(`${quality}: exact selected bytes/hash and four labelled nodes through the actual vendor loader`, async () => {
    const model = getModel(quality);
    const gzip = await readFile(new URL('../../dist' + model.url, import.meta.url));
    let requests = 0;
    const bytes = await loadExactModel('http://localhost:8000', undefined, quality, async (url, options) => {
      requests++;
      assert.equal(url.href, 'http://localhost:8000' + model.url);
      assert.equal(options.credentials, 'omit'); assert.equal(options.redirect, 'error');
      return new Response(gzip);
    });
    assert.equal(requests, 1); assert.equal(bytes.length, model.bytes);
    const asset = await new GLTFLoader().parseAsync(bytes.buffer, '');
    assert.deepEqual(Object.keys(bindLayers(asset)), LAYERS);
  });
}

test('unknown quality and tampered selected-model bytes fail closed', async () => {
  let requests = 0;
  await assert.rejects(loadExactModel('http://localhost:8000', undefined, '__proto__', async () => { requests++; }), /Unknown model quality/);
  assert.equal(requests, 0);
  const gzip = await readFile(new URL('../../dist' + MODELS.balanced.url, import.meta.url));
  gzip[400] ^= 1;
  await assert.rejects(loadExactModel('http://localhost:8000', undefined, 'balanced', async () => new Response(gzip)), /SHA-256 mismatch/);
  await assert.rejects(loadExactModel('http://localhost:8000', undefined, 'detailed', async () => new Response(gzip)), /byte count mismatch/);
});

test('published manifest and visible selector agree on the exact two choices and Balanced default', async () => {
  const manifest = JSON.parse(await readFile(new URL('../../dist/fdi31/model-manifest.json', import.meta.url), 'utf8'));
  assert.equal(DEFAULT_QUALITY, 'balanced');
  assert.equal(manifest.defaultQuality, DEFAULT_QUALITY);
  assert.deepEqual(manifest.models, MODELS);
  const html = await readFile(new URL('../../dist/fdi31/index.html', import.meta.url), 'utf8');
  assert.match(html, /value="balanced" selected/);
  assert.match(html, /value="detailed"/);
  assert.equal((html.match(/data-mode=/g) ?? []).length, 6);
  assert.match(html, /Quality changes keep your layer selection and camera/);
  assert.match(html, /Detailed reference, not the Balanced draft/);
  assert.match(html, /id="changelog"/);
});
