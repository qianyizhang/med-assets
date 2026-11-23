import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.MODEL_SURVEY_PREVIEW_URL;
const capture = process.env.MODEL_SURVEY_CAPTURE_DIR;
assert.ok(base && capture, 'Set a local Gallery URL and a capture directory.');
await mkdir(capture, { recursive: true });
const routes = {
  elbow: 'use-cases/right-arm/elbow',
  shoulder: 'use-cases/right-arm/shoulder',
  location: 'use-cases/head-and-neck/location',
  duct: 'use-cases/head-and-neck/duct-course',
  bladder: 'use-cases/systems/urinary?detail=urinary-left-vesical',
  cervix: 'use-cases/systems/reproductive?detail=reproductive-female-context',
};
const browser = await chromium.launch({ executablePath: process.env.MODEL_SURVEY_BROWSER,
  headless: true, chromiumSandbox: true, args: ['--enable-unsafe-swiftshader'] });
const checks = [];
try {
  for (const [id, route] of Object.entries(routes)) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const errors = [];
    page.on('pageerror', (error) => errors.push(String(error)));
    const lesson = page.locator('.ga-part-lesson');
    const frame = lesson.locator('.ga-part-frame');
    const still = frame.locator('img');
    const canvas = frame.locator('canvas');
    const layers = lesson.getByRole('radio');
    const answer = lesson.locator('.ga-part-answer');
    const decode = (locator) => locator.evaluate((image) => image.decode());
    const showAnswer = () => lesson.getByRole('button', { name: 'Reveal answer' }).click();
    const hideAnswer = () => lesson.getByRole('button', { name: 'Hide answer' }).click();
    const readFrame = () => canvas.evaluate((c) => c.toDataURL());
    const differentFrame = (old) => page.waitForFunction((prior) =>
      document.querySelector('.ga-part-frame canvas')?.toDataURL() !== prior, old);
    try {
      if (route.includes('?detail=')) {
        const [system, detail] = route.split('?detail=');
        await page.goto(base + '/#/' + system);
        await page.getByRole('navigation', { name: 'Teaching scale' }).locator('a[href*="?detail="]').click();
        await page.getByRole('combobox', { name: 'Detail view' }).selectOption(detail);
      } else {
        const entrance = id === 'duct' ? routes.location : id === 'shoulder' ? 'use-cases/systems/muscular' : 'use-cases';
        await page.goto(base + '/#/' + entrance);
        await page.locator('a[href="#/' + route + '"]:visible').first().click();
      }
      await page.waitForURL((url) => url.hash === '#/' + route);
      await decode(still);
      assert.equal(await answer.isVisible(), false);
      const labels = await layers.evaluateAll((radio) => radio.map((r) => r.labels[0].textContent.trim()));
      assert.ok(labels.length >= 2);
      const initialImage = await still.getAttribute('src');
      await frame.focus();
      await frame.press('ArrowRight');
      const marker = lesson.locator('.ga-part-point');
      const pointPosition = await marker.getAttribute('style');
      await layers.nth(1).check();
      await decode(still);
      assert.notEqual(await still.getAttribute('src'), initialImage);
      assert.equal(await marker.getAttribute('style'), pointPosition, 'The reference point stays fixed across matched layers.');
      await layers.first().check();
      await decode(still);
      await lesson.screenshot({ path: path.join(capture, id + '-question.png') });

      // Keep all study controls and the answer available through a failed load and a bad digest.
      await page.route('**/assets/**/*.glb', (r) => r.fulfill({ status: 503 }), { times: 1 });
      await lesson.getByRole('button', { name: 'Inspect in 3D' }).click();
      await lesson.getByText(/pinned export is unavailable/).waitFor();
      await showAnswer();
      await decode(answer.locator('img'));
      await hideAnswer();
      await page.route('**/assets/**/*.glb', async (r) => {
        const bytes = Buffer.from(await (await r.fetch()).body());
        bytes[bytes.length - 1] ^= 1;
        await r.fulfill({ status: 200, body: bytes });
      }, { times: 1 });
      await lesson.getByRole('button', { name: 'Retry 3D' }).click();
      await lesson.getByText(/differs from the pinned revision/).waitFor();
      const response = page.waitForResponse((r) => r.url().endsWith('.glb') && r.ok());
      await lesson.getByRole('button', { name: 'Retry 3D' }).click();
      const file = await response;
      const sha = createHash('sha256').update(await file.body()).digest('hex');
      assert.ok(file.url().includes('/assets/' + sha + '/'));
      await lesson.getByRole('button', { name: 'Use reference image' }).waitFor();
      await page.waitForFunction(() => {
        const c = document.querySelector('.ga-part-frame canvas');
        return c && c.width > 300 && c.height > 200;
      });
      const original = await readFrame();
      assert.ok(original.length > 5000);
      await canvas.screenshot({ path: path.join(capture, id + '-first.png') });
      const box = await canvas.boundingBox();
      const x = box.x + box.width * 0.5, y = box.y + box.height * 0.5;
      await page.mouse.move(x, y);
      await page.mouse.down();
      await page.mouse.move(x + 35, y + 5, { steps: 8 });
      await page.mouse.up();
      await differentFrame(original);
      const rotated = await readFrame();
      await layers.nth(1).check();
      await lesson.getByRole('button', { name: 'Use reference image' }).waitFor();
      await differentFrame(rotated);
      await layers.first().check();
      await lesson.getByRole('button', { name: 'Use reference image' }).waitFor();
      await page.waitForFunction((prior) => document.querySelector('.ga-part-frame canvas')?.toDataURL() === prior, rotated);
      await lesson.getByRole('button', { name: 'Reset view' }).click();
      await page.waitForFunction((prior) => document.querySelector('.ga-part-frame canvas')?.toDataURL() === prior, original);
      // Record each tissue at exactly the original camera and scale.
      for (let i = 1; i < labels.length; i++) {
        await layers.nth(i).check();
        await lesson.getByRole('button', { name: 'Use reference image' }).waitFor();
        await differentFrame(original);
        await canvas.screenshot({ path: path.join(capture, id + '-layer-' + i + '.png') });
      }
      await lesson.getByRole('button', { name: 'Use reference image' }).click();
      await showAnswer();
      await decode(answer.locator('img'));
      await answer.screenshot({ path: path.join(capture, id + '-answer.png') });
      await page.reload();
      await decode(still);
      assert.equal(await answer.isVisible(), false);
      assert.equal(await layers.first().isChecked(), true);
      await page.setViewportSize({ width: 1024, height: 768 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      assert.deepEqual(errors, []);
      checks.push({ id, route, question: await lesson.getByRole('heading').innerText(), layers: labels, firstExport: sha });
      console.log('PASS', id, labels.join(' / '));
    } finally { await page.close(); }
  }
  // The candidate's reference images and controls must also work without WebGL on another origin.
  const page = await browser.newPage();
  const publicOrigin = 'https://gallery.invalid';
  await page.route(publicOrigin + '/**', async (route) => {
    const url = new URL(route.request().url());
    await route.fulfill({ response: await page.request.get(base + url.pathname + url.search) });
  });
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, ...options) {
      if (type.includes('webgl')) return null;
      return original.call(this, type, ...options);
    };
  });
  for (const [id, route] of Object.entries(routes)) {
    await page.goto(publicOrigin + '/#/' + route);
    const lesson = page.locator('.ga-part-lesson');
    await lesson.locator('.ga-part-frame img').evaluate((image) => image.decode());
    if (id === 'location') {
      await lesson.getByRole('button', { name: 'Inspect in 3D' }).click();
      await lesson.getByRole('button', { name: 'Retry 3D' }).waitFor();
    }
    await lesson.getByRole('radio').nth(1).check();
    await lesson.getByRole('button', { name: 'Reveal answer' }).click();
    await lesson.locator('.ga-part-answer img').evaluate((image) => image.decode());
    await lesson.getByRole('region', { name: 'Labelled answer' }).press('Escape');
    await lesson.getByRole('button', { name: 'Reveal answer' }).waitFor();
  }
  await page.goto(publicOrigin + '/#/use-cases/right-arm/unknown');
  await page.getByRole('heading', { name: 'View unavailable' }).waitFor();
  await page.close();
  console.log('PASS all six tasks without WebGL, source-index fallback and invalid stop recovery.');
  await writeFile(path.join(capture, 'checks.json'), JSON.stringify(checks, null, 2) + '\n');
} finally { await browser.close(); }
