import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

const repo = new URL('../../../', import.meta.url);
const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
const heart = 'heart/synthetic-imaging/beating-heart/imaging/start_here_same_slice.png';
const breath = 'lessons/one-breath/review/offline-storyboard.png';
const shot = 'lessons/dental-animation/';

export async function checkSpecialistStills(page, base, dir) {
  const place = (route) => base + '/#/' + route;
  const heading = (name) => page.getByRole('heading', { name, level: 1, exact: true });
  const images = page.locator('.ga-source-evidence img');
  const lessons = [
    ['use-cases/systems/cardiovascular', 'use-cases/heart-slice',
      'Read the same heart slice three ways', 'Cardiovascular', [heart]],
    ['use-cases/systems/respiratory', 'use-cases/one-breath',
      'One Breath · 一次呼吸', 'Respiratory', [breath]],
    ['use-cases', 'use-cases/dental-layers',
      'Reveal the layers of a prepared incisor', 'Use Cases',
      ['lessons/dental-layer-controls/media/control-review-sheet.jpg']],
    ['archive', 'archive/dental-shot-studies',
      'Dental shot studies', 'Experiments & Archive',
      ['fdi31-layer-reveal/source-pose.jpg', 'fdi31-layer-reveal/editorial-reveal.jpg',
        'caries-restoration/poster.svg', 'periodontal-cleaning/poster.svg'].map((file) => shot + file)],
  ];
  const linkTo = (route) => page.locator('.ga-content').locator('a[href="#/' + route + '"]').first();
  const catalogue = await (await page.request.get(base + '/api/gallery/v1/studies')).json();
  for (const [, route] of lessons.slice(0, 3)) {
    assert.deepEqual(catalogue.lessons.find(({ id }) => route === 'use-cases/' + id)?.stops, []);
  }
  await page.setViewportSize({ width: 1024, height: 768 });
  for (const [parent, lesson, title, returnTitle, paths] of lessons) {
    await page.goto(place(parent));
    await heading(returnTitle).waitFor();
    await linkTo(lesson).press('Enter');
    await heading(title).waitFor();
    await page.goto(place(lesson));
    await page.reload();
    await heading(title).waitFor();
    if (paths.includes(breath)) {
      await page.getByText('Trachea → left and right main bronchi', { exact: false }).waitFor();
      assert.equal(await page.getByText('气管 → 左右主支气管', { exact: true }).getAttribute('lang'), 'zh');
    }
    await page.waitForFunction((count) => {
      const elements = [...document.querySelectorAll('.ga-source-evidence img')];
      return elements.length === count && elements.every((image) => image.complete && image.naturalWidth > 0);
    }, paths.length);
    for (const [i, path] of paths.entries()) {
      const src = await images.nth(i).getAttribute('src');
      const payload = src.startsWith('data:')
        ? Buffer.from(await images.nth(i).evaluate(async (image) =>
          Array.from(new Uint8Array(await (await fetch(image.src)).arrayBuffer()))))
        : await (await page.request.get(new URL(src, base).href)).body();
      assert.equal(digest(payload), digest(await readFile(new URL(path, repo))), path);
    }
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.screenshot({ path: dir + lesson.split('/').at(-1) + '.png', fullPage: true });
    await linkTo(parent).press('Enter');
    await heading(returnTitle).waitFor();
  }

  await page.goto(place('use-cases'));
  for (const route of ['use-cases/heart-slice', 'use-cases/one-breath']) {
    await linkTo(route).waitFor();
    await linkTo(route).press('Enter');
    const src = await images.first().getAttribute('src');
    const asset = '**' + src;
    await page.route(asset, (request) => request.fulfill({ status: 404 }));
    await page.reload();
    await page.getByRole('status').filter({ hasText: 'unavailable' }).waitFor();
    await page.getByRole('link', { name: 'Open the original in the source repository' }).waitFor();
    await page.unroute(asset);
    await page.reload();
    await page.waitForFunction(() => document.querySelector('.ga-source-evidence img')?.naturalWidth > 0);
    await page.goto(place('use-cases'));
  }
  await linkTo('use-cases/dental-layers').click();
  await page.getByRole('link', { name: /Balanced specimen download/ }).click();
  await page.getByRole('button', { name: /Balanced/ }).waitFor();
  for (const id of ['02-cavity-filling', '04-gum-disease']) {
    await page.goto(place('archive/dental-shot-studies'));
    await linkTo('archive/dental-image26/' + id).click();
    await heading('Dental Image 2.6 stories').waitFor();
    assert.equal(new URL(page.url()).hash, '#/archive/dental-image26/' + id);
  }
  await page.setViewportSize({ width: 1280, height: 900 });
  console.log('PASS specialist still discovery, exact source bytes, deep links, return paths, and missing-image recovery.');
}
