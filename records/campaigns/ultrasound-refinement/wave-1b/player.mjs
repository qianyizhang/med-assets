import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const [studyUrl, baselineUrl, output] = process.argv.slice(2);
const study = new URL(studyUrl);
const baseline = new URL(baselineUrl);
await mkdir(output, { recursive: true });
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
const locator = (base, id = 'abdomen-survey', chapter = 'abd-right-kidney') =>
  new URL(`tours/abdomen/${id}.html?chapter=${chapter}&frame=12#exam`, base).href;
const child = (page) => page.frameLocator('#player iframe');
const hex = (bytes) => createHash('sha256').update(bytes).digest('hex');
const binding = JSON.parse(await readFile(new URL(
  '../../../../experiments/ultrasound-sweep/cases/organs/consumer.json', import.meta.url,
))).consumers[0];
const meshPath = '/sweeps/kidney-right/scenes/kidney_right.mesh';
const pixelPath = '/sweeps/kidney-right/media/scan-12.webp';
const overlayPath = '/sweeps/kidney-right/media/section-12.webp';
async function capture(surface, element, name) {
  await surface.locator(element).screenshot({ path: join(output, name + '.png') });
}

try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1090 }, reducedMotion: 'reduce' });
  await context.route('**/*', (route) => [study.origin, baseline.origin].includes(new URL(route.request().url()).origin)
    ? route.continue() : route.abort());
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  await page.goto(locator(baseline));
  await child(page).locator('#pose[data-scene-ready]').waitFor();
  assert.match(await child(page).locator('#value').innerText(), /107 mm/);
  await capture(child(page), '#pose', 'before-contact');
  await capture(child(page), '#scan', 'before-scan');
  await child(page).locator('#overlay').click();
  await capture(child(page), '#scan', 'before-overlay');

  const served = {};
  const wait = (path) => page.waitForResponse(response => response.ok() && new URL(response.url()).pathname === path);
  const waiting = [meshPath, pixelPath, overlayPath].map(wait);
  await page.goto(locator(study));
  await child(page).locator('#sceneCanvas:not([hidden])').waitFor();
  await child(page).locator('#sceneHelp:not([hidden])').waitFor();
  await child(page).locator('#scan[src$="scan-12.webp"]').waitFor();
  assert.match(await child(page).locator('#apReadout').innerText(), /hilar recess.*103\.3 mm/);
  assert.match(await page.locator('#abd-right-kidney:not([hidden])').innerText(), /separate subject/);
  await capture(child(page), '#sceneCanvas', 'after-contact');
  await capture(child(page), '#scanPanel', 'after-scan');
  await child(page).getByRole('button', { name: 'Anatomy overlay' }).click();
  await child(page).locator('#scan[src$="section-12.webp"]').waitFor();
  await capture(child(page), '#scanPanel', 'after-overlay');
  for (const response of await Promise.all(waiting)) {
    const bytes = await response.body();
    served[new URL(response.url()).pathname] = { sha256: hex(bytes), bytes: bytes.length };
  }
  assert.equal(served[meshPath].sha256, binding.pins[0].sha256);
  assert.match(await page.locator('#openSweep').getAttribute('href'), /index.html\?sweep=kidney-right&frame=12$/);
  const seek = page.locator('#tourPosition');
  await seek.press('ArrowLeft');
  await child(page).locator('#scan[src$="section-11.webp"]').waitFor();
  assert.equal(await child(page).locator('#apMarks').isVisible(), false);
  await seek.press('ArrowRight');
  await child(page).locator('#scan[src$="section-12.webp"]').waitFor();
  assert.equal(await child(page).locator('#apMarks').isVisible(), true);

  await page.locator('#tourSection').selectOption('abd-right-kidney-trans');
  await child(page).locator('#pose[data-scene-ready]').waitFor();
  await page.locator('#tourSection').selectOption('abd-right-kidney');
  await child(page).locator('#scan[src$="scan-00.webp"]').waitFor();
  for (const [caseId, chapterId] of [
    ['abdomen-limited-pancreas', 'abd-right-kidney'],
    ['abdomen-survey', 'abd-right-kidney-trans'],
    ['abdomen-renal-obstruction', 'renal-right-hydro'],
  ]) {
    await page.goto(locator(study, caseId, chapterId));
    await child(page).locator('#pose[data-scene-ready]').waitFor();
    assert.equal(await child(page).locator('#position').inputValue(), '12');
    assert.equal(await page.locator('[data-source-sweep]:not([hidden])').count(), 0);
    if (caseId === 'abdomen-limited-pancreas') assert.match(await child(page).locator('#value').innerText(), /107 mm/);
  }

  const payloadResponse = await context.request.get(new URL(meshPath, study).href);
  const altered = await payloadResponse.body();
  altered[12] ^= 1;
  for (const [status, body] of [[404, ''], [200, altered]]) {
    const test = await context.newPage();
    await test.route('**' + meshPath, route => route.fulfill({ status, body }));
    await test.goto(locator(study));
    await child(test).getByText('3D probe and scan plane unavailable.').waitFor();
    await child(test).locator('#scan[src$="scan-12.webp"]').waitFor();
    assert.match(await child(test).locator('#apReadout').innerText(), /103\.3 mm/);
    await test.close();
  }

  await page.goto(new URL('development/index.html', study).href);
  const currency = await page.evaluate(async () => {
    const { chapterMeshReviewPrior } = await import('./assets-data.js');
    const manifest = await fetch('./asset-inventory.json').then(response => response.json());
    const { records: [record], rubricHash } = await fetch('./asset-reviews/kidney-wave-1b/reviews.json')
      .then(response => response.json());
    const part = manifest.chapterMeshBindings[record.case][record.chapter];
    const binding = part[record.part];
    const prior = () => chapterMeshReviewPrior(manifest, record, rubricHash, new Map());
    const current = await prior();
    manifest.recipeHashes.organs = 'unrelated edited sibling';
    part.sibling = { meshSha256: 'modified' };
    const sibling = await prior();
    binding.chapterSha256 = 'changed placement';
    return { current, sibling, placement: await prior() };
  });
  assert.deepEqual(currency, { current: false, sibling: false, placement: true });
  assert.deepEqual(errors, []);
  await writeFile(join(output, '..', 'live-identity.json'), JSON.stringify({ served, currency }, null, 2) + '\n');
  console.log('Frame 12, exact mesh and saved scans, branch isolation, valid-size corrupt and missing mesh, and review currency passed.');
} finally {
  await browser.close();
}
