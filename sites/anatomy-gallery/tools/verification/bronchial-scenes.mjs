import assert from 'node:assert/strict';
import { sha256 as digest, galleryRoute } from './assertions.mjs';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import review from '../../../../reviews/bronchial_tree/2026-11-21-distal-simplification-trial/geometry.json' with { type: 'json' };
import { assetUrl } from '../../app/src/content/gallery/catalog.js';
import { bronchialExterior, firstForkPath, localModels } from '../../app/src/content/gallery/local-models.js';
import { localView, stagePath } from '../../app/src/content/gallery/presets.js';

function identity(bytes) {
  const length = bytes.readUInt32LE(12);
  const gltf = JSON.parse(bytes.subarray(20, 20 + length));
  assert.equal(gltf.meshes.length, 1);
  const [primitive] = gltf.meshes[0].primitives;
  assert.equal(gltf.meshes[0].primitives.length, 1);
  return { bytes: bytes.length, sha256: digest(bytes), triangles: gltf.accessors[primitive.indices].count / 3 };
}

export async function checkBronchialScenes({ browser, base, capture }) {
  const url = (route) => galleryRoute(base, route);
  const original = 'library/bronchial_tree/authored-central-fairing-r13';
  const [candidate] = bronchialExterior.exports;
  const modelUrl = base + assetUrl(candidate);
  const context = await browser.newContext();
  const page = await context.newPage();
  const heading = (name) => page.getByRole('heading', { level: 1, name, exact: true });
  const canvas = page.locator('.ga-canvas canvas');
  const scene = page.getByRole('region', { name: 'Interactive scene' });
  const loaded = async () => {
    await canvas.waitFor();
    await page.waitForFunction(() => document.querySelector('.ga-canvas canvas')?.toDataURL().length > 5000);
    assert.ok(await page.getByLabel('Material', { exact: true }).isEnabled());
  };
  await page.goto(base + '/');
  await page.getByRole('link', { name: 'Use Cases', exact: true }).click();
  await page.getByRole('link', { name: 'Airway Review' }).click();
  const stop = page.getByRole('link', { name: /Trace the first bronchial fork/ });
  assert.equal(await stop.getAttribute('href'), '#/' + firstForkPath);
  await stop.press('Enter');
  await heading(bronchialExterior.useCase).waitFor();
  assert.equal(new URL(page.url()).hash, '#/' + firstForkPath);
  const poster = scene.locator('.ga-viewport img');
  await page.waitForFunction(() => document.querySelector('.ga-viewport img')?.naturalWidth > 0);

  await page.route(modelUrl, (route) => route.fulfill({ status: 503 }), { times: 1 });
  await page.getByRole('button', { name: 'Inspect in 3D' }).click();
  await scene.getByRole('status').getByText('The pinned export is unavailable.').waitFor();
  assert.ok(await poster.isVisible());
  assert.ok(await page.getByLabel('Material', { exact: true }).isDisabled());
  await page.route(modelUrl, (route) => route.fulfill({ body: Buffer.alloc(candidate.bytes) }), { times: 1 });
  await page.getByRole('button', { name: 'Retry 3D' }).click();
  await scene.getByRole('status').getByText('The export differs from the pinned revision.').waitFor();
  await page.screenshot({ path: path.join(capture, 'first-fork-corrupt.png') });
  const pending = page.waitForResponse((response) => response.url() === modelUrl && response.status() === 200);
  await page.getByRole('button', { name: 'Retry 3D' }).click();
  const delivered = identity(await (await pending).body());
  assert.deepEqual(delivered, { bytes: candidate.bytes, sha256: candidate.sha256, triangles: 308288 });
  await loaded();
  assert.equal(await page.getByLabel('Material', { exact: true }).inputValue(), 'Neutral');
  await page.screenshot({ path: path.join(capture, 'first-fork-loaded.png') });
  await page.setViewportSize({ width: 900, height: 790 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.setViewportSize({ width: 1280, height: 900 });

  await page.getByRole('link', { name: 'Open in 3D Stage' }).click();
  await page.getByRole('heading', { name: '3D Stage' }).waitFor();
  await loaded();
  const before = await canvas.evaluate((element) => element.toDataURL());
  await page.getByLabel('Material', { exact: true }).selectOption('Tissue');
  assert.notEqual(await canvas.evaluate((element) => element.toDataURL()), before);
  await page.getByRole('button', { name: 'Share this view' }).click();
  const shared = await page.getByLabel('Persistent preset link').inputValue();
  const [stage, query] = new URL(shared).hash.slice(2).split('?');
  assert.equal(stage, 'stage/' + bronchialExterior.scene.version);
  const params = new URLSearchParams(query);
  assert.equal(params.get('from'), firstForkPath);
  const view = JSON.parse(params.get('view'));
  assert.equal(view.sha256, candidate.sha256);
  assert.equal(view.revision, bronchialExterior.revision);
  assert.ok(view.camera.height > 0);
  for (const open of [() => page.goto(shared), () => page.reload()]) {
    await open();
    await loaded();
    assert.equal(await page.getByLabel('Material', { exact: true }).inputValue(), 'Tissue');
  }
  await page.getByRole('link', { name: 'Return to first-fork lesson' }).click();
  await heading(bronchialExterior.useCase).waitFor();
  await page.reload();
  await heading(bronchialExterior.useCase).waitFor();
  await page.getByRole('link', { name: 'Open the reviewed fork in Asset Library' }).click();
  await heading(bronchialExterior.title).waitFor();
  assert.equal(new URL(page.url()).hash, '#/' + bronchialExterior.library);
  await page.reload();
  await heading(bronchialExterior.title).waitFor();
  await page.getByText(/Rating · 14\/16/).waitFor();
  assert.equal(await page.getByText('11/16', { exact: true }).count(), 0);
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('link', { name: candidate.name + ' ↓', exact: true }).click(),
  ]);
  assert.equal(download.suggestedFilename(), candidate.name);
  assert.deepEqual(identity(await readFile(await download.path())), delivered);

  await page.goto(url('library'));
  const search = page.getByRole('searchbox', { name: 'Search assets' });
  await search.fill('Bronchial tree');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  const result = page.locator('.ga-asset[href="#/' + bronchialExterior.library + '"]');
  await result.getByText('14/16', { exact: true }).waitFor();
  await result.click();
  await heading(bronchialExterior.title).waitFor();
  await page.goto(url('library/bronchial_tree'));
  await heading(bronchialExterior.title).waitFor();

  await page.getByRole('link', { name: 'Compare the original r13' }).click();
  await heading('Bronchial tree · central junction r13').waitFor();
  await page.reload();
  await page.getByRole('link', { name: 'Open this exact revision in Asset Library' }).click();
  assert.equal(new URL(page.url()).hash, '#/' + original);
  await page.getByText(/Rating · 11\/16/).waitFor();
  const exact = await page.getByRole('link', { name: 'bronchial_central_fairing.glb ↓' }).getAttribute('href');
  const retained = identity(await (await page.request.get(base + exact)).body());
  assert.deepEqual(retained, { bytes: review.original.bytes, sha256: review.original.sha256, triangles: 443892 });
  assert.equal(await page.getByRole('link', { name: candidate.name + ' ↓', exact: true }).count(), 0);

  for (const [bookmark, revision, filename, sha256] of [
    ['compare/bronchial-r09', 'authored-lobar-fairing-r09', 'bronchial_lobar_fairing.glb', '8820a14b820239c0ea53a3597ad7731b7c66eb41f05b197fde2e90ee08fb47e4'],
    ['compare/polish-appendix/bronchial', 'authored-junction-repair-r07', 'bronchial_authored_junction_repair.glb', '3408ca8e8f394dd268b1dbeafdc59fdc8cc104c0976628e455dbc070ae0a7993'],
  ]) {
    await page.goto(url(bookmark));
    const library = 'library/bronchial_tree/' + revision;
    await page.locator('a[href="#/' + library + '"]').first().click();
    const link = await page.getByRole('link', { name: filename + ' ↓' }).getAttribute('href');
    assert.equal(link, '/assets/' + sha256 + '/' + filename);
    assert.equal(digest(await (await page.request.get(base + link)).body()), sha256);
  }

  await page.goto(url('library/bronchial_tree/distal-sampling-r14'));
  const r14Receipt = page.getByRole('link', { name: 'Geometry verification (JSON)' });
  assert.deepEqual(await (await page.request.get(base + await r14Receipt.getAttribute('href'))).json(), review);
  const r14Download = page.locator('a[download]').first();
  const r14 = identity(await (await page.request.get(base + await r14Download.getAttribute('href'))).body());
  assert.deepEqual(r14, { bytes: review.updated.bytes, sha256: review.updated.sha256, triangles: 308288 });
  assert.ok(await page.getByText('Earlier first-fork teaching edition · Local preview', { exact: true }).isVisible());
  const r14Model = localModels.find((model) => model.scene.version === 'bronchial-first-fork-v1');
  const legacy = url(stagePath({ ...localView(r14Model), material: 'Tissue' }, firstForkPath));
  const legacyUrl = base + assetUrl(r14Model.exports[0]);
  const legacyPayload = page.waitForResponse((response) => response.url() === legacyUrl && response.ok());
  await page.goto(legacy);
  assert.deepEqual(identity(await (await legacyPayload).body()), r14);
  await loaded();
  await page.getByRole('heading', { name: r14Model.title, exact: true }).waitFor();
  assert.equal(await page.getByLabel('Material', { exact: true }).inputValue(), 'Tissue');
  await page.reload();
  await loaded();
  await page.getByRole('link', { name: 'Return to first-fork lesson' }).click();
  await heading(bronchialExterior.useCase).waitFor();
  await page.getByRole('link', { name: 'Open the reviewed fork in Asset Library' }).click();
  await heading(bronchialExterior.title).waitFor();

  const currentPoster = await readFile(new URL('../../../../' + bronchialExterior.scene.posterPath, import.meta.url));
  await page.route(modelUrl, (route) => route.fulfill({ status: 503 }), { times: 1 });
  await page.goto(url(stagePath(localView(bronchialExterior))));
  await scene.getByRole('status').getByText('The pinned export is unavailable.').waitFor();
  assert.equal(await poster.getAttribute('src'), '/review-evidence/' + digest(currentPoster) + '/bronchial-first-fork-teaching.webp');
  await page.getByRole('button', { name: 'Retry 3D' }).click();
  await loaded();

  const manifest = await (await page.request.get(base + '/assets/index.json')).json();
  assert.ok(!manifest.assets.some((asset) => asset.sha256 === candidate.sha256));
  // verify_release_builds.mjs checks the separate published v10 project.
  const testOrigin = 'https://gallery.example.test';
  const alternate = await context.newPage();
  await alternate.route(testOrigin + '/**', async route => {
    const url = new URL(route.request().url());
    return route.fulfill({ response: await alternate.request.get(base + url.pathname + url.search) });
  });
  await alternate.goto(testOrigin + '/#/use-cases/airway');
  await alternate.locator('a[href="#/' + firstForkPath + '"]').waitFor();
  await alternate.goto(testOrigin + '/#/' + bronchialExterior.library);
  await alternate.getByRole('heading', { level: 1, name: bronchialExterior.title }).waitFor();
  await alternate.goto(testOrigin + '/' + new URL(shared).hash);
  await alternate.getByRole('heading', { level: 1, name: '3D Stage' }).waitFor();
  await alternate.locator('.ga-canvas canvas').waitFor();
  await alternate.close();

  await writeFile(path.join(capture, 'bronchial-exterior.json'), JSON.stringify({
    browser: browser.version(), lesson: url(firstForkPath), library: url(bronchialExterior.library), shared,
    candidate: delivered, original: retained, legacy: { preset: legacy, ...r14 },
    retry: '503, same-size corrupt response, successful exact-model retry',
    alternateOrigin: testOrigin,
    visibility: 'Candidate lesson, Library record and saved Stage view on both origins. Public index excludes the candidate asset.',
  }, null, 2) + '\n');
  console.log('PASS bronchial teaching, verified WebGL and downloads, both preset versions, r07/r09/r13 compatibility, exact failure poster and candidate routes on both origins');
}
