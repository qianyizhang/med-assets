import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import review from '../../../reviews/bronchial_tree/2026-11-21-distal-simplification-trial/geometry.json' with { type: 'json' };
import { assetUrl } from '../app/src/content/gallery/catalog.js';
import { bronchialExterior, firstForkPath } from '../app/src/content/gallery/local-models.js';

const capture = process.env.MODEL_SURVEY_CAPTURE_DIR;
assert.ok(capture, 'Set MODEL_SURVEY_CAPTURE_DIR to a dedicated receipt directory');
await mkdir(capture, { recursive: true });
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.MODEL_SURVEY_PREVIEW_URL || 'http://127.0.0.1:8858';
const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
const url = (route) => base + '/#/' + route;
const original = 'library/bronchial_tree/authored-central-fairing-r13';
const [candidate] = bronchialExterior.exports;
const modelUrl = base + assetUrl(candidate);

function identity(bytes) {
  const length = bytes.readUInt32LE(12);
  const gltf = JSON.parse(bytes.subarray(20, 20 + length));
  assert.equal(gltf.meshes.length, 1);
  const [primitive] = gltf.meshes[0].primitives;
  assert.equal(gltf.meshes[0].primitives.length, 1);
  return { bytes: bytes.length, sha256: digest(bytes), triangles: gltf.accessors[primitive.indices].count / 3 };
}

const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  headless: true,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  context.on('page', (page) => page.on('pageerror', (error) => errors.push(String(error))));
  await context.route('**/*', (route) => route.request().url().startsWith(base + '/')
    ? route.continue() : route.abort());
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
  const poster = page.getByRole('img', { name: bronchialExterior.scene.posterAlt });
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
  assert.deepEqual(delivered, { bytes: review.updated.bytes, sha256: review.updated.sha256, triangles: 308288 });
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
  await page.getByRole('link', { name: 'Open r14 in Asset Library' }).click();
  await heading(bronchialExterior.title).waitFor();
  assert.equal(new URL(page.url()).hash, '#/' + bronchialExterior.library);
  await page.reload();
  await heading(bronchialExterior.title).waitFor();
  await page.getByText(/Rating · Unrated/).waitFor();
  assert.equal(await page.getByText('11/16', { exact: true }).count(), 0);
  const receiptLink = page.getByRole('link', { name: 'Geometry verification (JSON)' });
  const response = await page.request.get(base + await receiptLink.getAttribute('href'));
  assert.deepEqual(await response.json(), review);
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
  await result.getByText('Unrated', { exact: true }).waitFor();
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

  const manifest = await (await page.request.get(base + '/assets/index.json')).json();
  assert.ok(!manifest.assets.some((asset) => asset.sha256 === candidate.sha256));
  const publicOrigin = 'https://gallery.example.test';
  const html = await (await page.request.get(base + '/')).text();
  const publicPage = await context.newPage();
  await publicPage.route(publicOrigin + '/**', (route) => route.request().isNavigationRequest()
    ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
  await publicPage.goto(publicOrigin + '/#/use-cases/airway');
  await publicPage.locator('.ga-feature[href="#/compare/bronchial-r13"]').waitFor();
  assert.equal(await publicPage.locator('a[href="#/' + firstForkPath + '"]').count(), 0);
  await publicPage.goto(publicOrigin + '/#/' + bronchialExterior.library);
  await publicPage.getByRole('heading', { name: 'View unavailable' }).waitFor();
  await publicPage.goto(publicOrigin + '/' + new URL(shared).hash);
  await publicPage.getByRole('heading', { name: 'View unavailable' }).waitFor();

  assert.deepEqual(errors, []);
  await writeFile(path.join(capture, 'bronchial-exterior.json'), JSON.stringify({
    browser: browser.version(), lesson: url(firstForkPath), library: url(bronchialExterior.library), shared,
    candidate: delivered, original: retained,
    retry: '503, same-size corrupt response, successful exact-model retry',
    public: 'Candidate absent from the delivery index and non-loopback visitor routes',
  }, null, 2) + '\n');
  console.log('PASS bronchial teaching, verified WebGL and download, preset reload, r07/r09/r13 compatibility, retry and local-only visibility');
} finally {
  await browser.close();
}
