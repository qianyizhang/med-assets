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
const annotatedViewport = { width: 1239, height: 741 };

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

async function reveal(locator) {
  await locator.waitFor({ state: 'attached' });
  await locator.evaluate((element) => {
    for (let group = element.closest('details'); group; group = group.parentElement.closest('details')) {
      group.open = true;
    }
  });
}

async function openVariant(page, key) {
  const link = variant(page, key);
  await reveal(link);
  await link.click();
  await ready(page, key);
}

async function capture(page, name) {
  if (output) await page.screenshot({ path: join(output, name + '.png') });
}

async function selectionCheckbox(page, selection) {
  const input = page.locator('#tours input[name=tour][value=' + JSON.stringify(selection) + ']');
  await reveal(input);
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

async function assertChooserBreadth(page) {
  const counts = await page.locator('#tour-choices, #tour-choices .tour-group-children')
    .evaluateAll((groups) => groups.map((group) => group.children.length));
  assert.ok(counts.length > 1 && counts.every((count) => count <= 7), JSON.stringify(counts));
}

async function repaint(page) {
  await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))));
}

async function verifyWorkspace(context) {
  const page = await context.newPage({ viewport: annotatedViewport });
  page.setDefaultTimeout(45000);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const asset = 'case:breast-tissue';
  const use = 'case/breast-retroareolar-cyst/breast-cyst-anti/Anechoic%20simple%20cyst/1';
  const checkboxes = () => page.locator('#visibility-list input[type=checkbox]');
  const mode = (value) => page.locator('#workspace-mode button[data-mode=' + value + ']');
  const pixels = () => page.locator('#mesh').screenshot({ animations: 'disabled' });
  await page.goto(url.href);
  await indexed(page);
  await assertChooserBreadth(page);
  await page.locator('#region').selectOption('abdomen');
  await assertChooserBreadth(page);
  const branches = page.locator('#tour-choices > .tour-group > details > summary');
  assert.deepEqual((await branches.allTextContents()).map((label) => label.trim()), [
    'AAA screening 3', 'Abdominal tours 4', 'Orientation tours 1', 'Standalone sweeps 10',
  ]);
  assert.equal(await page.locator('#tour-choices input[name=tour]').count(), 18);
  assert.equal(await page.locator('#tour-count').innerText(), '18 of 18 selected');
  await capture(page, 'abdomen-tour-chooser-1239');
  const aaaGroup = page.getByRole('checkbox', { name: 'Select all in AAA screening', exact: true });
  const aaaLeaves = page.locator('#tours input[name=tour][value^=aaa-]');
  await aaaGroup.uncheck();
  assert.equal(await aaaLeaves.and(page.locator(':checked')).count(), 0);
  assert.equal(await page.locator('#tour-count').innerText(), '15 of 18 selected');
  await aaaGroup.check();
  assert.equal(await aaaLeaves.and(page.locator(':checked')).count(), 3);
  const negative = await selectionCheckbox(page, 'aaa-negative');
  await negative.uncheck();
  assert.equal(await aaaGroup.evaluate((input) => input.indeterminate), true);
  assert.equal(await aaaLeaves.and(page.locator(':checked')).count(), 2);
  await negative.check();
  assert.equal(await aaaGroup.evaluate((input) => input.indeterminate), false);
  assert.equal(await page.locator('#tour-count').innerText(), '18 of 18 selected');
  await page.locator('#region').selectOption('breast');
  await page.locator('#all-tours').uncheck();
  await (await selectionCheckbox(page, 'breast-retroareolar-cyst')).check();
  await assetCard(page, asset).click();
  await ready(page);
  assert.ok(await page.locator('#asset-shelf').isVisible(), 'Selecting an asset hid the shelf.');
  assert.match(await page.locator('#asset-title').innerText(), /Breast tissue model/);
  assert.equal(await mode('asset').getAttribute('aria-pressed'), 'true');
  assert.match(await page.locator('#acquisition').inputValue(), /^case\/breast-retroareolar-cyst\//);
  assert.equal(await page.locator('#geometry-checks').isHidden(), true);
  assert.equal(await page.locator('#mesh-file').isHidden(), true);
  assert.ok(await checkboxes().count() > 3);
  const parts = page.locator('#visibility-list');
  for (const name of ['Fibroglandular tissue', 'Retromammary fat', 'Anechoic simple cyst']) {
    assert.ok(await parts.getByRole('checkbox', { name, exact: false }).isChecked(), name + ' was missing from the assembled asset');
  }
  const side = page.getByRole('button', { name: 'Side', exact: true });
  await side.click();
  await repaint(page);
  const withParts = await pixels();
  const gland = parts.getByRole('checkbox', { name: /^Fibroglandular tissue$/ });
  await gland.uncheck();
  await repaint(page);
  assert.notDeepEqual(await pixels(), withParts, 'Part visibility did not change the rendered geometry.');
  assert.equal(await side.getAttribute('aria-pressed'), 'true', 'Toggling a part changed the asset camera.');
  await gland.check();
  await repaint(page);
  assert.deepEqual(await pixels(), withParts, 'Restoring the part did not restore the same assembled preview.');
  await page.getByRole('button', { name: 'Oblique', exact: true }).click();
  await page.locator('.workspace').evaluate((workspace) => workspace.scrollIntoView({ block: 'start' }));
  await repaint(page);
  await capture(page, 'retained-multipart-asset-1239');
  await mode('scene').click();
  await ready(page);
  assert.equal(await mode('scene').getAttribute('aria-pressed'), 'true');
  assert.ok(await page.locator('#asset-shelf').isVisible());
  assert.equal(await page.locator('#mesh').count(), 1);
  assert.ok(await checkboxes().count() > 1, 'Scene mode did not expose adjacent assets.');
  const breast = parts.getByRole('checkbox', { name: /Breast tissue model/ });
  assert.ok(await breast.isChecked());
  const sceneSide = page.getByRole('button', { name: 'Side', exact: true });
  await sceneSide.click();
  await repaint(page);
  const withAsset = await pixels();
  assert.notDeepEqual(withAsset, withParts, 'Asset and Scene mode displayed the same geometry.');
  await breast.uncheck();
  await repaint(page);
  assert.notDeepEqual(await pixels(), withAsset, 'Scene visibility did not change the rendered geometry.');
  assert.equal(await sceneSide.getAttribute('aria-pressed'), 'true', 'Toggling an asset changed the scene camera.');
  await breast.check();
  await repaint(page);
  assert.deepEqual(await pixels(), withAsset);
  await page.getByRole('button', { name: 'Oblique', exact: true }).click();
  await page.locator('.workspace').evaluate((workspace) => workspace.scrollIntoView({ block: 'start' }));
  await repaint(page);
  await capture(page, 'retained-multipart-scene-1239');
  await mode('asset').click();
  assert.equal(await mode('asset').getAttribute('aria-pressed'), 'true');
  const antiradial = 'case/breast-retroareolar-cyst/breast-cyst-anti';
  await page.locator('#acquisition').selectOption(antiradial);
  await ready(page, antiradial);
  assert.equal(new URL(await page.locator('#route').getAttribute('href')).searchParams.get('chapter'), 'breast-cyst-anti');
  await page.goto(useURL(use));
  await ready(page, use);
  assert.match(await page.locator('#route').getAttribute('href'), /breast-retroareolar-cyst\.html.*chapter=breast-cyst-anti/);
  assert.ok(await page.locator('#asset-shelf').isVisible());
  assert.ok(await page.locator('#geometry-checks').isVisible(), 'Exact use did not restore isolated geometry checks.');
  await page.locator('#evidence').getByRole('heading', { name: 'Assessment', exact: true }).waitFor();

  for (const [row, acquisition, route] of [
    ['sweep/gallbladder//gallbladder/1', 'sweep/gallbladder', { sweep: 'gallbladder' }],
    ['aaa/aaa-negative/proximal-aorta/wall/1', 'aaa/aaa-negative/proximal-aorta', { chapter: 'proximal-aorta', frame: '14' }],
  ]) {
    await page.goto(useURL(row));
    await ready(page, row);
    await mode('scene').click();
    await ready(page, acquisition);
    assert.ok(await checkboxes().count() > 1, acquisition + ' did not load scene assets.');
    const href = new URL(await page.locator('#route').getAttribute('href'));
    for (const [name, value] of Object.entries(route)) assert.equal(href.searchParams.get(name), value);
    assert.equal(await page.locator('#geometry-checks').isHidden(), true);
  }
  assert.deepEqual(errors, []);
  await page.close();
}

async function assertNoProxy(page) {
  assert.ok(await page.locator('#mesh').isHidden(), 'A missing requirement unexpectedly rendered geometry.');
  assert.equal(await page.locator('#mesh').getAttribute('data-ready'), null);
  assert.equal(await page.locator('#visibility-list input[type=checkbox]:visible').count(), 0);
  assert.ok(await page.locator('#mesh-file').isHidden(), 'A missing requirement exposed a geometry source.');
  assert.ok(await page.locator('#evidence').isHidden(), 'A missing requirement exposed an anatomy rating.');
}

async function verifyAbdominalWorkspace(context, entries) {
  const page = await context.newPage({ viewport: annotatedViewport });
  page.setDefaultTimeout(45000);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(url.href);
  await indexed(page);
  const sources = await page.evaluate(async (cases) => {
    const { sweepRows, caseRows, rowID } = await import('./assets-data.js');
    const rows = await Promise.all(cases.map(caseRows));
    return {
      cases: rows.flat().map((row) => ({ ...row, key: rowID(row) })),
      sweeps: (await sweepRows()).map((row) => ({ ...row, key: rowID(row) })),
    };
  }, entries.filter(({ family }) => family === 'abdomen'));
  const available = sources.cases.filter((row) => row.source !== 'requirement');
  const requirements = sources.cases.filter((row) => row.source === 'requirement');
  assert.ok(available.length && requirements.length);
  assert.ok(available.every((row) => row.donor && row.mesh && row.meshDigest), 'An abdominal geometry row lacks an exact donor.');
  assert.ok(requirements.every((row) => !row.mesh && !row.meshDigest), 'Requirement was assigned surrogate geometry.');

  assert.ok(available.some((row) => row.donor.source === 'gallery' && row.chapter === 'bladder-uvj'));

  const standalone = sources.sweeps.find((row) => row.case === 'gallbladder' && row.part === 'gallbladder');
  assert.ok(standalone, 'Standalone gallbladder donor is unavailable.');
  const biliary = available.find((row) => row.case === 'abdomen-biliary-stone' &&
    row.chapter === 'biliary-stone-supine' && row.mesh === standalone.mesh);
  assert.ok(biliary, 'Supine biliary tour did not reuse the standalone gallbladder.');
  assert.equal(biliary.meshDigest, standalone.meshDigest);
  assert.equal(biliary.variantId, standalone.variantId);
  assert.equal(biliary.assetId, standalone.assetId);
  assert.equal(sha(await meshBytes(page.request, biliary.mesh)),
    '6509c00826a818036d690192e98cb2f8e14aeb8786f9c699b2c8d5fb95ea1de9');

  const calculus = requirements.find((row) => row.case === biliary.case && row.chapter === biliary.chapter &&
    /calculus/i.test(row.partLabel ?? row.label));
  assert.equal(calculus?.status, 'rebuild');
  const wall = requirements.find((row) => row.case === biliary.case && row.chapter === biliary.chapter &&
    /gallbladder wall/i.test(row.partLabel ?? row.label));
  const lumen = requirements.find((row) => row.case === biliary.case && row.chapter === biliary.chapter &&
    /gallbladder lumen/i.test(row.partLabel ?? row.label));
  assert.equal(wall?.status, 'missing');
  assert.equal(lumen?.status, 'missing');
  assert.ok(requirements.every((row) => !/calculus/i.test(row.partLabel ?? row.label) || row.case === biliary.case),
    'The calculus requirement leaked into a different tour.');

  await page.locator('#region').selectOption('abdomen');
  await page.locator('#all-tours').uncheck();
  const tour = await selectionCheckbox(page, biliary.case);
  await tour.check();
  assert.equal(await page.locator('#tour-count').innerText(), '1 of 18 selected');
  const mode = (value) => page.locator('#workspace-mode button[data-mode=' + value + ']');
  const gapCard = assetCard(page, calculus.assetId);
  const donorCard = assetCard(page, biliary.assetId);
  await donorCard.click();
  await ready(page);
  const expected = [biliary.source, biliary.case, biliary.chapter].join('/') + '@' + biliary.sourceSpace;
  await page.locator('#acquisition').selectOption(expected);
  await ready(page, expected);
  assert.match(await page.locator('#selection-context').innerText(), /registration.*unavailable/i);
  const donor = page.locator('#donor-source a');
  assert.equal(new URL(await donor.getAttribute('href'), url).searchParams.get('sweep'), 'gallbladder');
  const checkboxes = page.locator('#visibility-list input[type=checkbox]');
  assert.equal(await checkboxes.count(), 1);
  for (const label of ['Gallbladder wall', 'Gallbladder lumen']) {
    assert.match(await page.locator('#requirements').innerText(), new RegExp('Missing part · ' + label));
  }
  assert.equal(await donorCard.getAttribute('data-requirement'), 'missing');
  await page.locator('.workspace').evaluate((element) => element.scrollIntoView({ block: 'start' }));
  await repaint(page);
  await capture(page, 'biliary-donor-1239');

  await mode('scene').click();
  await ready(page, expected);
  assert.match(await page.locator('#selection-context').innerText(), /source geometry.*registration.*unavailable/i);
  assert.doesNotMatch(await page.locator('#visibility-list').innerText(), /calculus|gallbladder wall|gallbladder lumen/i);
  await repaint(page);
  await capture(page, 'biliary-source-scene-1239');

  await page.goto(useURL(biliary.key));
  await ready(page, biliary.key);
  await indexed(page);
  assert.equal(new URL(await page.locator('#mesh-file').getAttribute('href'), url).pathname,
    new URL(standalone.mesh, url).pathname);
  assert.equal(new URL(await donor.getAttribute('href'), url).searchParams.get('sweep'), 'gallbladder');

  await page.locator('#region').selectOption('abdomen');
  await page.locator('#all-tours').uncheck();
  await (await selectionCheckbox(page, biliary.case)).check();
  await page.locator('#availability').selectOption('gaps');
  const unavailable = calculus;
  assert.ok(!available.some((item) => item.assetId === unavailable.assetId), 'The calculus requirement has substitute geometry.');
  const unavailableCard = assetCard(page, unavailable.assetId);
  assert.ok(await unavailableCard.locator('.requirement-placeholder').isVisible());
  assert.equal(await unavailableCard.locator('img').count(), 0);
  await unavailableCard.click();
  await assertNoProxy(page);
  await mode('scene').click();
  await assertNoProxy(page);
  assert.match(await page.locator('#requirements').innerText(), /Rebuild required|Missing part/);
  assert.ok(await page.locator('#requirements a[href*="abdomen-biliary-stone"]').first().isVisible());
  assert.match(await gapCard.innerText(), /Rebuild required/);
  await page.locator('.workspace').evaluate((element) => element.scrollIntoView({ block: 'start' }));
  await capture(page, 'biliary-missing-1239');

  const part = page.locator('#asset-parts details[data-part="mobile-calculus"] a[data-variant]').first();
  await reveal(part);
  await part.click();
  await assertNoProxy(page);
  await page.reload();
  await indexed(page);
  assert.ok(await page.locator('#requirements').isVisible());
  await assertNoProxy(page);

  await page.goto(useURL('case/abdomen-biliary-stone/biliary-stone-supine/Mobile%20calculus/1'));
  await indexed(page);
  await assertNoProxy(page);
  assert.match(await page.locator('#selection-context').innerText(), /Rebuild required/i);
  await capture(page, 'biliary-old-bookmark-1239');

  await page.locator('#region').selectOption('abdomen');
  await page.locator('#all-tours').uncheck();
  const other = requirements.find((row) => row.part === 'bowel-gas-and-shadow');
  await (await selectionCheckbox(page, other.case)).check();
  await page.locator('#availability').selectOption('gaps');
  assert.equal(await gapCard.count(), 0, 'The calculus appeared with the biliary tour excluded.');
  assert.match(await assetCard(page, other.assetId).innerText(), /Rebuild required/);
  await (await selectionCheckbox(page, biliary.case)).check();
  await gapCard.waitFor();
  assert.equal(await page.locator('#tour-count').innerText(), '2 of 18 selected');
  await page.locator('#all-tours').check();
  assert.equal(await page.locator('#tour-count').innerText(), '18 of 18 selected');
  await gapCard.waitFor();
  await page.locator('#availability').selectOption('geometry');
  assert.equal(await gapCard.count(), 0, 'Geometry-only shelf exposed a calculus requirement.');
  const diaphragm = available.find((row) => row.part === 'diaphragm' && row.chapter === 'abd-liver');
  const bladder = available.find((row) => row.part === 'left-ureteral-orifice' && row.chapter === 'bladder-uvj');
  const duct = available.find((row) => row.part === 'common-bile-duct' && row.chapter === 'abd-cbd');
  const ductLiver = available.find((row) => row.part === 'liver' && row.case === duct?.case && row.chapter === 'abd-cbd');
  const liver = available.find((row) => row.part === 'liver' && row.case === diaphragm?.case && row.chapter === diaphragm?.chapter);
  assert.ok(diaphragm && bladder && liver && duct && ductLiver);
  for (const [row, space, credit, excluded] of [
    [diaphragm, 'z-anatomy-diaphragm', /Z-Anatomy/, /Hepatobiliary anatomy|Body envelope/i],
    [bladder, 'hra-female-pelvic-base', /Human Reference Atlas/, /renal anatomy|body envelope/i],
    [liver, 'ct-s1233', null, /diaphragm|bladder base/i],
    [duct, duct.sourceSpace, /Human Reference Atlas/, /hepatobiliary anatomy · s1233|body envelope/i],
    [ductLiver, 'ct-s1233', null, /hepatobiliary tree|bile duct · hra/i],
  ]) {
    assert.equal(row.sourceSpace, space);
    if (credit) assert.notEqual(space, 'ct-s1233');
    await page.goto(useURL(row.key));
    await ready(page, row.key);
    if (credit) {
      assert.match(await page.locator('#donor-source').innerText(), credit);
      assert.match(await page.locator('#donor-source a').last().getAttribute('href'), /ATTRIBUTION\.md$/);
      assert.equal(row.meshDigest, shapeDigest(await meshBytes(page.request, row.mesh), 1));
    }
    await mode('scene').click();
    const key = [row.source, row.case, row.chapter].join('/') + '@' + space;
    await ready(page, key);
    assert.doesNotMatch(await page.locator('#visibility-list').innerText(), excluded,
      'The source inspector combined incompatible coordinate spaces.');
    if (row === bladder || row === diaphragm) {
      await indexed(page);
      await page.locator('.workspace').evaluate((element) => element.scrollIntoView({ block: 'start' }));
      await repaint(page);
      await capture(page, row.part === 'diaphragm' ? 'diaphragm-gallery-source-1239' : 'bladder-hra-source-1239');
    }
  }
  await page.route(new URL(standalone.mesh, url).href, (route) => route.fulfill({ status: 404 }));
  const missingDonor = ['requirement', biliary.case, biliary.chapter, 'gallbladder', '1'].join('/');
  await page.goto(useURL(missingDonor));
  await indexed(page);
  await assertNoProxy(page);
  assert.match(await page.locator('#requirements').innerText(), /Missing part · gallbladder/i);
  await page.close();
  assert.deepEqual(errors, []);
}

try {
  if (output) await mkdir(output, { recursive: true });
  const page = await browser.newPage({ viewport });
  page.setDefaultTimeout(45000);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const failedRequests = [];
  page.on('requestfailed', (request) => failedRequests.push(request.failure()?.errorText + ' ' + request.url()));
  await page.goto(url.href);
  const manifest = await (await page.request.get(new URL('asset-inventory.json', url).href)).json();
  await page.locator('#rows a[data-asset]').first().waitFor();
  await indexed(page);
  assert.equal(await page.locator('#issues li').count(), 0,
    [await page.locator('#issues').textContent(), ...failedRequests.slice(-10)].join('\n'));

  console.log(await page.locator('#inventory-status').textContent());
  await verifyWorkspace(browser);
  await verifyAbdominalWorkspace(browser, manifest.cases);
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
  const sweeps = page.getByRole('checkbox', { name: 'Select all in Standalone sweeps', exact: true });
  await all.uncheck();
  const first = await selectionCheckbox(page, directTeachingSelection(right));
  const second = await selectionCheckbox(page, directTeachingSelection(left));
  const third = await selectionCheckbox(page, directTeachingSelection(carotid));
  const composed = await selectionCheckbox(page, 'thyroid-orientation');
  await composed.check();
  await assetCard(page, right.assetId).click();
  assert.equal(await page.locator('#asset-parts a[data-variant]').count(), 1);
  assert.match(await page.locator('#asset-summary').innerText(), /1 part across 2 acquisitions/);
  assert.ok(await page.locator('#asset-shelf').isVisible());
  await reveal(composed);
  await composed.uncheck();
  await reveal(first);
  await first.check();
  assert.equal(await page.locator('#tours input[name=tour]:checked').count(), 1);
  assert.equal(await sweeps.evaluate((control) => control.indeterminate), true);
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

  await reveal(second);
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
  await reveal(third);
  await third.check();
  assert.equal(await page.locator('#asset-parts a[data-variant]').count(), 2,
    'A separately fitted carotid exterior must remain its own variant.');
  await openVariant(page, carotid.key);
  assert.match(await page.locator('#mesh-file').getAttribute('href'), /carotid-right\/scenes\/torso\.mesh$/);
  await capture(page, 'asset-fitted-variants');
  await all.check();
  assert.equal(await all.isChecked(), true);
  assert.ok(await sweeps.isChecked());
  assert.ok(await page.locator('#tours input[name=tour]:checked').count() > 3);
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
  await fixture.locator('#workspace-mode [data-mode=scene]').click();
  await ready(fixture, 'sweep/gallbladder');
  assert.match(await fixture.locator('#mesh-status').innerText(), /Some components are unavailable.*Gallbladder/s);
  assert.ok(await fixture.locator('#visibility-list input[type=checkbox]').count() > 0);
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
