import assert from 'node:assert/strict';
import { sha256 as digest, galleryRoute } from './assertions.mjs';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import review from '../../../../reviews/heart_exterior/2026-11-21-static-repack/checks.json' with { type: 'json' };
import { cardiacExterior } from '../../app/src/content/gallery/local-models.js';
import { assetUrl } from '../../app/src/content/gallery/catalog.js';

export async function checkCardiacScenes({ browser, base, capture }) {
  const old = 'library/cardiac-exterior/static-opaque-exterior';
  const current = cardiacExterior.library;
  const model = assetUrl(cardiacExterior.exports[0]);
  const url = (route) => galleryRoute(base, route);
  const part = 'Aorta | root, ascending, arch and descending';
  const context = await browser.newContext();
  const page = await context.newPage();
  const search = page.getByRole('searchbox', { name: 'Search assets' });
  await page.goto(base + '/');
  await search.fill('Cardiac opaque exteriors');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  const result = page.getByRole('link', { name: /Cardiac opaque exteriors/ });
  await result.waitFor();
  assert.equal(await result.getAttribute('href'), '#/' + current);
  assert.match(await result.textContent(), /Recommended static export/);
  await result.press('Enter');
  const exactHeading = (view) => view.getByRole('heading', { name: cardiacExterior.title, exact: true });
  await exactHeading(page).waitFor();
  const verificationLink = page.getByRole('link', { name: 'Repack verification (JSON)' });
  const receiptUrl = new URL(await verificationLink.getAttribute('href'), base).href;
  const receipt = await page.request.get(receiptUrl);
  assert.equal(receipt.status(), 200);
  assert.deepEqual(await receipt.json(), review);
  const head = await page.request.head(receiptUrl);
  assert.equal(head.status(), 200);
  assert.equal(head.headers()['content-length'], String((await receipt.body()).length));
  const recordLink = page.url();
  assert.equal(new URL(recordLink).hash, '#/' + current);
  await page.screenshot({ path: path.join(capture, 'static-heart-r02-record.png'), fullPage: true });

  const structures = (view) => view.getByLabel('Structure', { exact: true });
  await page.getByRole('button', { name: 'Inspect in 3D' }).click();
  const canvas = page.locator('.ga-canvas canvas');
  await canvas.waitFor();
  const names = (await structures(page).locator('option').allTextContents()).slice(1).sort();
  assert.equal(names.length, review.clean_reimport.selectable_mesh_objects_in_each_import);
  const namesSha256 = digest(names.join('\n') + '\n');
  assert.equal(namesSha256, review.clean_reimport.sorted_lf_delimited_names_sha256);
  const full = await canvas.evaluate((element) => element.toDataURL());
  assert.ok(full.length > 5_000, 'The whole model has a rendered frame');
  await structures(page).selectOption(part);
  const isolated = await canvas.evaluate((element) => element.toDataURL());
  assert.notEqual(isolated, full);
  assert.ok(isolated.length > 5_000, 'The selected structure has a rendered frame');
  await page.screenshot({ path: path.join(capture, 'static-heart-r02-aorta.png') });

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('link', { name: 'static-opaque-exterior-repacked.glb ↓', exact: true }).click(),
  ]);
  assert.equal(download.suggestedFilename(), cardiacExterior.exports[0].name);
  const bytes = await readFile(await download.path());
  assert.equal(bytes.length, review.candidate.bytes);
  assert.equal(digest(bytes), review.candidate.sha256);

  await page.getByRole('link', { name: 'Open in 3D Stage ↗' }).click();
  const share = page.getByRole('button', { name: 'Share this view' });
  await share.waitFor();
  await page.waitForFunction(() => !document.querySelector('select[aria-label="Structure"]').disabled);
  await share.click();
  const shared = await page.getByLabel('Persistent preset link').inputValue();
  const [stage, query] = new URL(shared).hash.slice(2).split('?');
  assert.equal(stage, 'stage/' + cardiacExterior.scene.version);
  const state = JSON.parse(new URLSearchParams(query).get('view'));
  assert.equal(state.sha256, review.candidate.sha256);
  assert.equal(state.part, part);
  const fresh = await context.newPage();
  await fresh.goto(shared);
  await fresh.locator('.ga-canvas canvas').waitFor();
  assert.equal(await structures(fresh).inputValue(), part);
  await fresh.reload();
  await fresh.locator('.ga-canvas canvas').waitFor();
  assert.equal(await structures(fresh).inputValue(), part);
  await fresh.getByRole('link', { name: '← Return to asset record' }).click();
  await exactHeading(fresh).waitFor();
  await fresh.reload();
  await exactHeading(fresh).waitFor();

  await page.goto(url('library/cardiac-exterior'));
  await exactHeading(page).waitFor();
  await page.getByRole('link', { name: 'Static opaque exterior · Workshop derivative' }).click();
  assert.equal(new URL(page.url()).hash, '#/' + old);
  await page.reload();
  const oldLink = page.getByRole('link', { name: 'static-opaque-exterior.glb ↓', exact: true });
  const oldResponse = await page.request.get(base + await oldLink.getAttribute('href'));
  assert.equal(oldResponse.status(), 200);
  const oldBytes = await oldResponse.body();
  assert.equal(oldBytes.length, review.baseline.bytes);
  assert.equal(digest(oldBytes), review.baseline.sha256);
  await page.goto(url('library/cardiac-exterior/animated-source-opaque-exterior'));
  const animated = page.getByRole('link', { name: 'animated-source-opaque-exterior.glb ↓' });
  assert.match(await animated.getAttribute('href'), new RegExp(review.r01_controls.animated_source_sha256));
  await page.goto(url('library/cardiac-animated/fitted-canonical'));
  await page.getByText('Exact fitted GLB unavailable in the Library.', { exact: false }).waitFor();
  assert.equal(await page.locator('a[download]').count(), 0);
  const index = await (await page.request.get(base + '/assets/index.json')).json();
  assert.ok(!index.assets.some((asset) => asset.sha256 === review.candidate.sha256));

  await fresh.route(base + model, (request) => request.fulfill({ status: 503 }), { times: 1 });
  await fresh.getByRole('button', { name: 'Inspect in 3D' }).click();
  await fresh.getByRole('status').getByText('The pinned export is unavailable.').waitFor();
  assert.ok(await structures(fresh).isDisabled());
  await fresh.getByRole('button', { name: 'Retry 3D' }).click();
  await fresh.locator('.ga-canvas canvas').waitFor();
  assert.ok(await structures(fresh).isEnabled());
  await writeFile(path.join(capture, 'heart-exterior.json'), JSON.stringify({
    browser: browser.version(), recordLink, shared, part, selectableObjects: names.length, namesSha256,
    candidate: { bytes: bytes.length, sha256: digest(bytes) },
    original: { bytes: oldBytes.length, sha256: digest(oldBytes) },
    failedFetchAndRetry: '503 then successful retry of the same exact export',
  }, null, 2) + '\n');
  console.log('PASS static heart discovery, WebGL structure selection, exact download, shared view reload, original delivery and retry');
}
