// Exercise a fully assembled local study with generated motion clips.
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const base = new URL(process.argv[2]);
const captures = process.argv[3];
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});

try {
  if (captures) await mkdir(captures, { recursive: true });
  const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const capture = async (name) => {
    if (captures) await page.screenshot({ path: path.join(captures, name + '.png') });
  };
  await page.goto(new URL('index.html', base).href);
  await page.getByRole('link', { name: 'Development reviews', exact: true }).click();
  await page.locator('#motion-link').click();
  const sweeps = await page.evaluate(() => abdomenTours.length);
  assert.ok(sweeps > 0);
  assert.equal(await page.locator('.motion-card').count(), sweeps);
  await page.locator('.motion-card video').first().waitFor();
  const video = page.locator('.motion-card video').first();
  await video.evaluate(async video => {
    await video.play();
    await new Promise(resolve => video.requestVideoFrameCallback(resolve));
    video.pause();
  });
  await capture('motion');
  await page.locator('#bmode-link').click();
  const expected = await page.evaluate(() => abdomenTours.flatMap(sweep =>
    sweep.keyframes.map(key => ({
      id: sweep.id, frame: key.frame,
      scan: sweep.assetRoot + 'media/scan-' + String(key.frame).padStart(2, '0') + '.webp',
      reference: abdomenReferences[key.referenceId].path,
    }))));
  const rows = page.locator('.comparison');
  assert.equal(await rows.count(), expected.length);
  const displayed = await rows.evaluateAll(items => items.map(item => ({
    images: [...item.querySelectorAll('figure img')].map(img => img.src),
    frame: item.querySelector('.open-sweep').href,
  })));
  for (const [index, key] of expected.entries()) {
    const actual = displayed[index];
    assert.deepEqual(actual.images, [key.scan, key.reference].map(file => new URL(file, base).href));
    assert.equal(new URL(actual.frame).searchParams.get('sweep'), key.id);
    assert.equal(Number(new URL(actual.frame).searchParams.get('frame')), key.frame);
  }
  await rows.first().locator('img').evaluateAll(images => Promise.all(images.map(image => image.decode())));
  await capture('bmode-collection');
  await page.locator('#region').selectOption('Abdomen');
  await page.locator('#sweep').selectOption('gallbladder');
  await rows.first().locator('img').evaluateAll(images => Promise.all(images.map(image => image.decode())));
  await capture('bmode');
  await rows.nth(1).getByRole('link', { name: 'Open keyframe' }).click();
  await page.waitForFunction(() => document.querySelector('#scan')?.src.endsWith('scan-48.webp')
    && document.querySelector('#position')?.value === '48');
  await page.goBack();
  await page.locator('#bmode-link[aria-current=page]').waitFor();
  assert.equal(await page.locator('#sweep').inputValue(), 'gallbladder');
  await page.route('**/media/acquired-short.webp', route => route.fulfill({ status: 404 }));
  await page.reload();
  await rows.nth(1).scrollIntoViewIfNeeded();
  await rows.nth(1).getByText('Acquired reference unavailable').waitFor();
  assert.ok(await rows.nth(1).locator('figure img').first().evaluate(img => img.decode().then(() => true)));
  assert.ok(await rows.nth(1).locator('.source-credit a').count());
  if (process.argv[4]) {
    const batchStudy = new URL(process.argv[4]);
    await page.goto(new URL('development/?view=bmode&renders=batch', batchStudy).href);
    await page.locator('#batch-filter').waitFor();
    const samples = await page.evaluate(() => Object.keys(ultrasoundRenderComparison.rows).length);
    assert.ok(samples > 0);
    assert.equal(await rows.filter({ hasNotText: 'Outside this batch' }).count(), samples);
    const sample = rows.filter({ hasNotText: 'Outside this batch' }).first();
    assert.equal(await sample.locator('figure').count(), 3);
    await sample.locator('img').evaluateAll(images => Promise.all(images.map(image => image.decode())));
    await capture('render-batch');
  }
  assert.deepEqual(errors, []);
  console.log('PASS Motion playback, ' + expected.length + ' exact scan/reference pairs, filters, keyframe return and missing-reference recovery.');
} finally {
  await browser.close();
}
