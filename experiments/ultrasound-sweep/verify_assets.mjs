// Exercise the regional asset hierarchy against a complete local study.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const study = new URL(process.argv[2] || 'http://127.0.0.1:8874/');
const output = process.argv[3];
const url = new URL('development/assets.html', study);
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true, args: ['--enable-unsafe-swiftshader'],
});
const viewport = { width: 1360, height: 960 };

const ready = (page, key) => page.waitForFunction((expected) => {
  const shown = document.querySelector('#mesh').dataset.ready;
  return expected ? shown === expected : Boolean(shown);
}, key);
const indexed = (page) => page.waitForFunction(() => {
  const status = document.querySelector('#inventory-status').textContent;
  return !/loading inventory|indexing/i.test(status);
});

function useURL(key) {
  const result = new URL(url);
  result.hash = key;
  return result.href;
}

function assetCard(page, asset) {
  return page.locator('#rows a[data-asset=' + JSON.stringify(asset) + ']');
}

function variant(page, key) {
  return page.locator('#asset-parts a[data-variant][href=' + JSON.stringify('#' + key) + ']');
}

async function openVariant(page, key) {
  const link = variant(page, key);
  await link.evaluate((element) => { element.closest('details').open = true; });
  await link.click();
  await ready(page, key);
}

async function capture(page, name) {
  if (output) await page.screenshot({ path: join(output, name + '.png') });
}

async function selectionCheckbox(page, selection) {
  const input = page.locator('#tours input[name=tour][value=' + JSON.stringify(selection) + ']');
  await input.waitFor();
  return input;
}

function directTeachingSelection(row) {
  const direct = row.teachingSelections.find(({ url }) => new URL(url, study).searchParams.get('sweep') === row.case);
  assert.ok(direct, 'No direct teaching selection for ' + row.case);
  return direct.id;
}

async function meshBytes(request, path) {
  const response = await request.get(new URL(path, study).href);
  assert.ok(response.ok(), path);
  return response.body();
}

const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');

function shapeDigest(bytes, scale) {
  const vertices = bytes.readUInt32LE(0), indices = bytes.readUInt32LE(4) * 3;
  const start = 8 + vertices * 12;
  assert.equal(bytes.length, start + indices * 4);
  const normalized = Buffer.alloc(12 + vertices * 12 + indices * 4);
  normalized.writeUInt32LE(1, 0);
  normalized.writeUInt32LE(vertices, 4);
  normalized.writeUInt32LE(indices, 8);
  const physical = (i) => Math.fround(bytes.readFloatLE(8 + i * 4) * scale);
  for (let i = 0; i < vertices * 3; i++) {
    normalized.writeInt32LE(Math.round((physical(i) - physical(i % 3)) * 1000), 12 + i * 4);
  }
  bytes.copy(normalized, 12 + vertices * 12, start);
  return sha(normalized);
}

try {
  if (output) await mkdir(output, { recursive: true });
  const page = await browser.newPage({ viewport });
  page.setDefaultTimeout(45000);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(url.href);
  const manifest = await (await page.request.get(new URL('asset-inventory.json', url).href)).json();
  await page.locator('#rows a[data-asset]').first().waitFor();
  await indexed(page);
  assert.equal(await page.locator('#issues li').count(), 0, await page.locator('#issues').textContent());

  console.log(await page.locator('#inventory-status').textContent());
  const sharedSpine = await page.evaluate(async () => {
    const { sweepRows, aaaRows } = await import('./assets-data.js');
    const normal = (await sweepRows()).find((row) => row.case === 'aortic-screening' && row.part === 'vertebrae');
    const curve = (await aaaRows()).rows.filter((row) => row.part === 'vertebrae');
    return { variant: normal.variantId, cases: [...new Set(curve.map((row) => row.case))],
      fits: [...new Set(curve.map((row) => row.variantId))] };
  });
  assert.equal(sharedSpine.cases.length, 3);
  assert.deepEqual(sharedSpine.fits, [sharedSpine.variant]);

  // These byte identities come from the delivered paths, independently of browser grouping.
  const files = {
    thyroid: 'sweeps/thyroid-right/scenes/torso.mesh',
    carotid: 'sweeps/carotid-right/scenes/torso.mesh',
    gallbladder: 'scenes/gallbladder.mesh',
    liverGallbladder: 'sweeps/liver/scenes/gallbladder.mesh',
  };
  const meshes = Object.fromEntries(await Promise.all(Object.entries(files).map(async ([name, path]) =>
    [name, await meshBytes(page.request, path)])));
  const hashes = Object.fromEntries(Object.entries(meshes).map(([name, bytes]) => [name, sha(bytes)]));
  assert.notEqual(hashes.thyroid, hashes.carotid);
  assert.notEqual(hashes.gallbladder, hashes.liverGallbladder);
  const neck = await page.evaluate(async () => {
    const { sweepRows, rowID } = await import('./assets-data.js');
    return Object.fromEntries((await sweepRows()).filter((row) => row.part === 'torso' &&
      ['thyroid-right', 'thyroid-left', 'carotid-right', 'carotid-left'].includes(row.case))
      .map((row) => [row.case, { ...row, key: rowID(row) }]));
  });
  const right = neck['thyroid-right'], left = neck['thyroid-left'];
  const carotid = neck['carotid-right'], otherCarotid = neck['carotid-left'];
  assert.equal(right.assetId, 'library/skin');
  assert.equal(right.assetId, carotid.assetId);
  assert.equal(right.partId, carotid.partId);
  assert.equal(right.meshDigest, shapeDigest(meshes.thyroid, 1.5));
  assert.equal(carotid.meshDigest, shapeDigest(meshes.carotid, 1.5));
  assert.equal(right.variantId, left.variantId);
  assert.equal(carotid.variantId, otherCarotid.variantId);
  assert.notEqual(right.variantId, carotid.variantId);
  await page.locator('#region').selectOption(right.region);
  const all = page.locator('#all-tours');
  await all.uncheck();
  const first = await selectionCheckbox(page, directTeachingSelection(right));
  const second = await selectionCheckbox(page, directTeachingSelection(left));
  const third = await selectionCheckbox(page, directTeachingSelection(carotid));
  const composed = await selectionCheckbox(page, 'thyroid-orientation');
  await composed.check();
  await assetCard(page, right.assetId).click();
  assert.equal(await page.locator('#asset-parts a[data-variant]').count(), 1);
  assert.match(await page.locator('#asset-summary').innerText(), /2 acquisition uses/);
  await page.locator('#back-to-assets').click();
  await composed.uncheck();
  await first.check();
  assert.equal(await page.locator('#tours input[name=tour]:checked').count(), 1);
  await assetCard(page, right.assetId).click();
  await page.locator('#asset-detail').waitFor();
  assert.equal(await page.locator('#asset-parts a[data-variant]').count(), 1);
  await openVariant(page, right.key);
  assert.match(await page.locator('#mesh-status').innerText(), /Bounds.*mm/);
  assert.match(await page.locator('#geometry-buffers').innerText(), /triangles.*geometry buffer bytes/);
  assert.match(await page.locator('#mesh-file').getAttribute('href'), /thyroid-right\/scenes\/torso\.mesh$/);
  const side = page.getByRole('button', { name: 'Side', exact: true });
  await side.click();
  assert.equal(await side.getAttribute('aria-pressed'), 'true');

  await second.check();
  assert.equal(await page.locator('#tours input[name=tour]:checked').count(), 2);
  assert.equal(await page.locator('#asset-parts a[data-variant]').count(), 1,
    'Two thyroid sweeps should still use a single exterior variant.');
  await page.locator('#part-uses summary').click();
  await page.locator('#part-uses a[href=' + JSON.stringify('#' + left.key) + ']').click();
  await ready(page, left.key);
  const selectedURL = page.url();
  await page.reload();
  await ready(page, left.key);
  assert.equal(page.url(), selectedURL);
  assert.ok(await first.isChecked() && await second.isChecked());
  await indexed(page);
  await page.goBack();
  await ready(page, right.key);
  await third.check();
  assert.equal(await page.locator('#asset-parts a[data-variant]').count(), 2,
    'A separately fitted carotid exterior must remain its own variant.');
  await openVariant(page, carotid.key);
  assert.match(await page.locator('#mesh-file').getAttribute('href'), /carotid-right\/scenes\/torso\.mesh$/);
  await capture(page, 'asset-fitted-variants');
  await all.check();
  assert.equal(await all.isChecked(), true);
  assert.ok(await page.locator('#tours input[name=tour]:checked').count() > 3);
  await page.locator('#back-to-assets').click();
  await assetCard(page, right.assetId).waitFor();
  assert.equal(await page.locator('#region').inputValue(), right.region);
  assert.ok(await all.isChecked(), 'Returning to the hierarchy lost the all-tours scope.');
  await page.waitForFunction(() => [...document.querySelectorAll('#rows .specimen img')]
    .filter((image) => image.complete && image.naturalWidth > 0).length >= 3);
  await capture(page, 'asset-hierarchy');
  await page.locator('#query').fill('missing specimen 0000');
  await page.locator('#empty').waitFor();

  // Synthetic scores provide exact expectations and check that a use cannot
  // inherit another use's assessment merely by sharing the same physical shape.
  const fixture = await browser.newPage({ viewport });
  fixture.setDefaultTimeout(45000);
  const fixturePath = 'asset-reviews/browser-fixture.json';
  const brokenImage = 'asset-reviews/browser-fixture-broken.webp';
  const review = {
    source: 'sweep', case: right.case, part: 'torso', task: 'Verify assessment rendering',
    reviewer: 'Browser test fixture', reviewedOn: '2026-11-26', rubric: 'asset-quality',
    revision: 'Synthetic browser fixture', baseline: 'Synthetic baseline fixture',
    meshSha256: hashes.thyroid,
    scores: { fidelity: 0, form: 4, readability: 4, economy: 4 },
    scoreEvidence: { fidelity: 'Fixture observation', form: 'Fixture', readability: 'Fixture', economy: 'Fixture' },
    comparison: { candidate: brokenImage },
  };
  const modelCase = manifest.cases.find(({ id }) => id === 'carotid-normal');
  const chapter = modelCase.chapters.find(({ id }) => id === 'right-cca-gray');
  assert.ok(chapter);
  const caseKey = ['case', modelCase.id, chapter.id, 'Right CCA', '1'].map(encodeURIComponent).join('/');
  const caseReview = { ...review, source: 'case', case: modelCase.id, chapter: chapter.id, part: 'Right CCA' };
  const qualified = { ...review, case: 'gallbladder', part: 'gallbladder', meshSha256: hashes.gallbladder,
    scores: { ...review.scores, fidelity: 4 } };
  let currentRecipe = 'fixture-recipe';
  await fixture.route('**/asset-inventory.json', (route) => route.fulfill({
    json: { ...manifest, cases: [modelCase], reviews: [fixturePath],
      recipeHashes: { ...manifest.recipeHashes, vascular: currentRecipe } },
  }));
  await fixture.route('**/browser-fixture.json', (route) => route.fulfill({
    json: { version: 1, recipeHash: 'fixture-recipe', rubricHash: manifest.rubricHash, records: [review, caseReview, qualified] },
  }));
  await fixture.route('**/browser-fixture-broken.webp', (route) => route.fulfill({ status: 404 }));
  await fixture.goto(useURL(right.key));
  await ready(fixture, right.key);
  await fixture.locator('#evidence').getByText('12/16', { exact: true }).waitFor();
  assert.ok(await fixture.locator('#evidence').getByText('0/4', { exact: false }).count());
  await fixture.getByText('Evidence image unavailable.', { exact: true }).waitFor();
  await fixture.goto(useURL(left.key));
  await ready(fixture, left.key);
  await fixture.locator('#evidence').getByText('Unrated', { exact: true }).first().waitFor();
  assert.equal(await fixture.locator('#evidence').getByText('12/16', { exact: true }).count(), 0);

  await fixture.goto(useURL(caseKey));
  await ready(fixture, caseKey);
  await fixture.locator('#evidence').getByText('12/16', { exact: true }).waitFor();
  currentRecipe = 'stale-recipe-fixture';
  await fixture.reload();
  await fixture.locator('#evidence').getByText('Unrated · prior review', { exact: true }).waitFor();
  assert.equal(await fixture.locator('#evidence').getByText('12/16', { exact: true }).count(), 0);

  const gallbladder = 'sweep/gallbladder//gallbladder/1';
  await fixture.goto(useURL(gallbladder));
  await ready(fixture, gallbladder);
  await fixture.locator('#evidence').getByText('16/16', { exact: true }).first().waitFor();
  await fixture.locator('#back-to-assets').click();
  await fixture.locator('#assessment').selectOption('qualified');
  await indexed(fixture);
  assert.equal(await fixture.locator('#rows a[data-asset]').count(), 1);
  await fixture.locator('#assessment').selectOption('exemplar');
  await fixture.locator('#empty').waitFor();
  await fixture.route('**/scenes/gallbladder.mesh', (route) => route.fulfill({ status: 404 }));
  await fixture.goto(useURL(gallbladder));
  await fixture.reload();
  await fixture.getByText('Isolated mesh unavailable.', { exact: false }).waitFor();
  assert.ok(await fixture.locator('#route').isVisible());

  const topology = await browser.newPage({ viewport });
  for (const [key, label, closed] of [
    ['case/echo-aortic-stenosis/psax-av-section/Aortic%20valve%20cusp%201/1', 'Aortic valve cusp 1', false],
    ['case/pregnancy-mid-normal/mid-overview/Fetal%20surface/1', 'Fetal surface', true],
  ]) {
    await topology.goto(useURL(key));
    await ready(topology, key);
    assert.equal(await topology.locator('#selection').innerText(), label);
    await topology.getByRole('button', { name: 'Check topology', exact: true }).click();
    const result = topology.locator('#geometry-topology');
    await result.getByText(/Exact coincident vertices welded/).waitFor();
    const text = await result.innerText();
    assert.match(text, /1 component · [\d,]+ open edges · 0 nonmanifold edges/);
    assert.equal(text.includes('· 0 open edges'), closed, label + ': ' + text);
  }
  assert.deepEqual(errors, []);
  console.log('Regions, one/multiple/all tours, asset variants, exact-use deep links, 3D, ratings, topology and errors passed.');
} finally {
  await browser.close();
}
