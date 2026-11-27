import assert from 'node:assert/strict';
import { sha256 } from './assertions.mjs';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';

export async function checkLayerLessons({ browser, base, capture }) {
  const tasks = {
    elbow: {
      route: 'use-cases/right-arm/elbow',
      question: 'Where does the ulnar nerve pass in relation to the medial epicondyle and the olecranon?',
      labels: ['Joint capsule', 'Ulnar nerve'],
    },
    shoulder: {
      route: 'use-cases/right-arm/shoulder',
      question: 'How do the rotator cuff muscle surfaces sit around the scapular spine and the glenoid socket?',
      labels: ['Glenoid and labrum', 'Rotator cuff'],
    },
    location: {
      route: 'use-cases/head-and-neck/location',
      question: 'Can you find all three pairs of salivary glands?',
      labels: ['Jaw and oral floor', 'Glands only'],
    },
    duct: {
      route: 'use-cases/head-and-neck/duct-course',
      question: 'Can you trace the parotid duct over the masseter?',
      labels: ['Jaw and masseter', 'Gland and duct only'],
    },
    bladder: {
      route: 'use-cases/systems/urinary?detail=urinary-left-vesical',
      question: 'Where are the bladder base and neck, and where do the two ureters enter?',
      labels: ['Bladder outline', 'Dome hidden'],
    },
    cervix: {
      route: 'use-cases/systems/reproductive?detail=reproductive-female-context',
      question: 'Where are the cervix and vaginal exterior in relation to the bladder and rectum?',
      labels: ['Pelvic neighbors', 'Central structures'],
    },
  };

  async function readyLesson(page, { question, labels }) {
    const lesson = page.getByRole('region', { name: question, exact: true });
    // The hash can change while the previous lesson is still mounted.
    await lesson.waitFor();
    const layers = labels.map((name) => lesson.getByRole('radio', { name, exact: true }));
    for (const layer of layers) await layer.waitFor();
    assert.equal(await lesson.getByRole('radio').count(), labels.length, question);
    assert.equal(await layers[0].isChecked(), true, question);
    return { lesson, layers };
  }

  const checks = [];
  for (const [id, task] of Object.entries(tasks)) {
    const { route, labels } = task;
    const page = await browser.newPage();
    try {
      if (route.includes('?detail=')) {
        const [system, detail] = route.split('?detail=');
        await page.goto(base + '/#/' + system);
        await page.getByRole('navigation', { name: 'Teaching scale' }).locator('a[href*="?detail="]').click();
        await page.getByRole('combobox', { name: 'Detail view' }).selectOption(detail);
      } else {
        const entrance = { duct: tasks.location.route, shoulder: 'use-cases/systems/muscular', elbow: 'use-cases/lessons' }[id] ?? 'use-cases';
        await page.goto(base + '/#/' + entrance);
        await page.locator('a[href="#/' + route + '"]:visible').first().click();
      }
      await page.waitForURL((url) => url.hash === '#/' + route);
      const { lesson, layers } = await readyLesson(page, task);
      const frame = lesson.locator('.ga-part-frame');
      const still = frame.locator('img');
      const canvas = frame.locator('canvas');
      const answer = lesson.locator('.ga-part-answer');
      const decode = (locator) => locator.evaluate((image) => image.decode());
      const showAnswer = () => lesson.getByRole('button', { name: 'Reveal answer' }).click();
      const hideAnswer = () => lesson.getByRole('button', { name: 'Hide answer' }).click();
      const readFrame = () => canvas.evaluate((c) => c.toDataURL());
      const differentFrame = (old) => page.waitForFunction((prior) =>
        document.querySelector('.ga-part-frame canvas')?.toDataURL() !== prior, old);
      await decode(still);
      assert.equal(await answer.isVisible(), false);
      const initialImage = await still.getAttribute('src');
      await frame.focus();
      await frame.press('ArrowRight');
      const marker = lesson.locator('.ga-part-point');
      const pointPosition = await marker.getAttribute('style');
      await layers[1].check();
      await decode(still);
      assert.notEqual(await still.getAttribute('src'), initialImage);
      assert.equal(await marker.getAttribute('style'), pointPosition, 'The reference point stays fixed across matched layers.');
      await layers[0].check();
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
      const sha = sha256(await file.body());
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
      await layers[1].check();
      await lesson.getByRole('button', { name: 'Use reference image' }).waitFor();
      await differentFrame(rotated);
      await layers[0].check();
      await lesson.getByRole('button', { name: 'Use reference image' }).waitFor();
      await page.waitForFunction((prior) => document.querySelector('.ga-part-frame canvas')?.toDataURL() === prior, rotated);
      await lesson.getByRole('button', { name: 'Reset view' }).click();
      await page.waitForFunction((prior) => document.querySelector('.ga-part-frame canvas')?.toDataURL() === prior, original);
      // Record each tissue at exactly the original camera and scale.
      for (let i = 1; i < labels.length; i++) {
        await layers[i].check();
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
      assert.equal(await layers[0].isChecked(), true);
      await page.setViewportSize({ width: 1024, height: 768 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
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
  for (const [id, task] of Object.entries(tasks)) {
    await page.goto(publicOrigin + '/#/' + task.route);
    const { lesson, layers } = await readyLesson(page, task);
    await lesson.locator('.ga-part-frame img').evaluate((image) => image.decode());
    if (id === 'location') {
      await lesson.getByRole('button', { name: 'Inspect in 3D' }).click();
      await lesson.getByRole('button', { name: 'Retry 3D' }).waitFor();
    }
    await layers[1].check();
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
}
