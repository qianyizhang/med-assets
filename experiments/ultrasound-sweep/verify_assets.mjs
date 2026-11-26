// Exercise the qualification workbench against a complete local study.
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const study = new URL(process.argv[2] || 'http://127.0.0.1:8874/');
const output = process.argv[3];
const url = new URL('development/assets.html', study);
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true, args: ['--enable-unsafe-swiftshader'],
});
const ready = (page, key) => page.waitForFunction((expected) => {
  const shown = document.querySelector('#mesh').dataset.ready;
  return expected ? shown === expected : Boolean(shown);
}, key);
const indexed = (page) => page.waitForFunction(() => {
  const status = document.querySelector('#inventory-status').textContent;
  return status.includes('isolated parts') && !status.includes('indexing');
});

try {
  const page = await browser.newPage({ viewport: { width: 1360, height: 960 } });
  page.setDefaultTimeout(45000);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(url.href);
  const records = await (await page.request.get(new URL('asset-inventory.json', url).href)).json();
  await page.locator('#rows a').first().waitFor();
  await page.waitForFunction(() => [...document.querySelectorAll('.specimen img')].filter((image) =>
    image.complete && image.naturalWidth > 0).length >= 3);
  await page.locator('#rows a').first().click();
  await ready(page);
  assert.match(await page.locator('#mesh-status').innerText(), /Bounds.*mm/);
  assert.match(await page.locator('#geometry-buffers').innerText(), /triangles.*geometry buffer bytes/);
  await page.getByRole('button', { name: 'Side', exact: true }).click();
  assert.equal(await page.getByRole('button', { name: 'Side', exact: true }).getAttribute('aria-pressed'), 'true');
  const key = await page.locator('#mesh').getAttribute('data-ready');
  await page.reload();
  await ready(page, key);
  await indexed(page);
  assert.equal(await page.locator('#rows a[aria-current="true"]').getAttribute('href'), '#' + key);
  assert.equal(await page.locator('#source').inputValue(), key.split('/')[0], 'Reload did not coordinate the source filter');
  assert.equal(await page.locator('#issues li').count(), 0, await page.locator('#issues').textContent());
  if (output) {
    await mkdir(output, { recursive: true });
    await page.screenshot({ path: join(output, 'asset-inventory.png') });
  }

  await page.locator('#clear').click();
  for (const source of ['case', 'aaa', 'sweep']) {
    await page.locator('#source').selectOption(source);
    assert.ok(await page.locator('#rows a').count(), source + ' inventory empty');
  }
  await page.locator('#source').selectOption('case');
  for (const entry of records.cases.filter(({ family }) => family !== 'aaa')) {
    await page.locator('#query').fill(entry.id);
    assert.ok(await page.locator('#rows a').count(), entry.id + ' missing from inventory');
  }
  await page.locator('#query').fill('carotid-normal right cca');
  const collapsedCount = await page.locator('#rows a').count();
  await page.locator('#expand-uses').check();
  assert.ok(await page.locator('#rows a').count() > collapsedCount, 'Repeated acquisition uses were not collapsed');
  await page.locator('#expand-uses').uncheck();
  await page.locator('#rows a').first().click();
  await ready(page);
  const earlierUse = await page.locator('#mesh').getAttribute('data-ready');
  await page.locator('#part-uses summary').click();
  assert.ok(await page.locator('#part-uses a').count() > 1);
  const use = page.locator('#part-uses a').last();
  const useKey = (await use.getAttribute('href')).slice(1);
  await use.click();
  await ready(page, useKey);
  await page.goBack();
  await ready(page, earlierUse);
  assert.equal(await page.locator('#rows a[aria-current="true"]').getAttribute('href'), '#' + earlierUse);
  await page.locator('#query').fill('missing specimen 0000');
  assert.ok(await page.locator('#empty').isVisible());

  const fixture = await browser.newPage({ viewport: { width: 1360, height: 960 } });
  fixture.setDefaultTimeout(30000);
  const fixturePath = 'asset-reviews/browser-fixture.json';
  const brokenImage = 'asset-reviews/browser-fixture-broken.webp';
  const review = {
    source: 'sweep', case: 'gallbladder', part: 'gallbladder', task: 'Verify assessment rendering',
    reviewer: 'Browser test fixture', reviewedOn: '2026-11-26', rubric: 'asset-quality',
    revision: 'Synthetic browser fixture', baseline: 'Synthetic baseline fixture',
    scores: { fidelity: 0, form: 4, readability: 4, economy: 4 },
    scoreEvidence: { fidelity: 'Fixture observation', form: 'Fixture', readability: 'Fixture', economy: 'Fixture' },
    comparison: { candidate: brokenImage },
  };
  const carotid = records.cases.find(({ id }) => id === 'carotid-normal');
  let currentRecipe = 'fixture-recipe';
  await fixture.route('**/asset-inventory.json', (route) =>
    route.fulfill({ json: { cases: [carotid], reviews: [fixturePath], recipeHashes: { vascular: currentRecipe } } }));
  const caseReview = { ...review, source: 'case', case: carotid.id, part: 'Right CCA' };
  const fullyQualified = { ...review, part: 'torso', scores: { ...review.scores, fidelity: 4 } };
  await fixture.route('**/browser-fixture.json', (route) => route.fulfill({
    json: { version: 1, recipeHash: 'fixture-recipe', records: [review, caseReview, fullyQualified] },
  }));
  await fixture.route('**/browser-fixture-broken.webp', (route) => route.fulfill({ status: 404 }));
  const specimen = new URL(url.href);
  const ratedKey = 'sweep/gallbladder//gallbladder/1';
  specimen.hash = ratedKey;
  await fixture.goto(specimen.href);
  await ready(fixture, ratedKey);
  await fixture.locator('#evidence').getByText('12/16', { exact: true }).waitFor();
  assert.equal(await fixture.locator('#assessment').inputValue(), 'assessed');
  assert.ok(await fixture.locator('#evidence').getByText('0/4', { exact: false }).count());
  await fixture.getByText('Evidence image unavailable.', { exact: true }).waitFor();
  assert.match(await fixture.locator('#geometry-buffers').innerText(), /triangles/);
  await indexed(fixture);
  await fixture.locator('#source').selectOption('sweep');
  await fixture.locator('#assessment').selectOption('qualified');
  assert.equal(await fixture.locator('#rows a').count(), 1);
  assert.match(await fixture.locator('#rows a').innerText(), /Patient exterior/);
  await fixture.locator('#assessment').selectOption('below');
  assert.equal(await fixture.locator('#rows a').count(), 1);
  assert.match(await fixture.locator('#rows a').innerText(), /Gallbladder/);
  await fixture.locator('#assessment').selectOption('exemplar');
  assert.ok(await fixture.locator('#empty').isVisible());
  await fixture.locator('#assessment').selectOption('');
  await fixture.locator('#family').selectOption('');
  await fixture.locator('#source').selectOption('case');
  await fixture.locator('#query').fill('right cca');
  await fixture.locator('#rows a').first().click();
  await fixture.locator('#evidence').getByText('12/16', { exact: true }).waitFor();
  await fixture.locator('#part-uses summary').click();
  const other = fixture.locator('#part-uses a').last();
  const otherKey = (await other.getAttribute('href')).slice(1);
  await other.click();
  await ready(fixture, otherKey);
  await fixture.locator('#evidence').getByText('12/16', { exact: true }).waitFor();
  currentRecipe = 'stale-recipe-fixture';
  await fixture.reload();
  await fixture.locator('#evidence').getByText('Unrated · prior review', { exact: true }).waitFor();
  assert.equal(await fixture.locator('#evidence').getByText('12/16', { exact: true }).count(), 0);
  await fixture.goto(specimen.href);
  await fixture.route('**/scenes/gallbladder.mesh', (route) => route.fulfill({ status: 404 }));
  await fixture.reload();
  await fixture.getByText('Isolated mesh unavailable.', { exact: false }).waitFor();
  assert.ok(await fixture.locator('#route').isVisible());
  const topology = await browser.newPage({ viewport: { width: 1360, height: 960 } });
  for (const [specimen, label, closed] of [
    ['case/echo-aortic-stenosis/psax-av-section/Aortic%20valve%20cusp%201/1', 'Aortic valve cusp 1', false],
    ['case/pregnancy-mid-normal/mid-overview/Fetal%20surface/1', 'Fetal surface', true],
  ]) {
    const link = new URL(url.href);
    link.searchParams.set('witness', label);
    link.hash = specimen;
    await topology.goto(link.href);
    await ready(topology, specimen);
    assert.equal(await topology.locator('#selection').innerText(), label);
    await topology.getByRole('button', { name: 'Check topology', exact: true }).click();
    const result = topology.locator('#geometry-topology');
    await result.getByText(/Exact coincident vertices welded/).waitFor();
    const text = await result.innerText();
    assert.match(text, /1 component · [\d,]+ open edges · 0 nonmanifold edges/);
    assert.equal(text.includes('· 0 open edges'), closed, label + ': ' + text);
  }
  assert.deepEqual(errors, []);
  console.log('Visual inventory, all case identities, isolation, navigation, scores, empty filters and missing assets passed.');
} finally {
  await browser.close();
}
