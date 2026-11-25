import assert from 'node:assert/strict';
import { sha256 as digest, galleryRoute } from './assertions.mjs';
import { readFile } from 'node:fs/promises';

const repo = new URL('../../../../', import.meta.url);
const heart = 'heart/synthetic-imaging/beating-heart/imaging/start_here_same_slice.png';
const breath = 'lessons/one-breath/review/offline-storyboard.png';
const shot = 'lessons/dental-animation/';

export async function checkSharedAirway(page, base, dir) {
  const manifest = JSON.parse(await readFile(new URL('lessons/one-breath/assets.json', repo)));
  const address = (route) => galleryRoute(base, route);
  const scene = page.getByRole('region', { name: 'Interactive scene' });
  for (const [route, id, variant, title, returnLabel] of [
    ['compare/trachea-r06', 'tracheaOpen', 'open', 'Open tracheal shell', 'Return to the trachea review'],
    ['use-cases/one-breath', 'tracheaCutaway', 'cutaway', 'Tracheal cutaway', 'Return to One Breath'],
  ]) {
    const asset = manifest.assets.find((item) => item.id === id);
    const url = `${base}/assets/${asset.sha256}/${asset.file}`;
    await page.goto(address(route));
    await scene.getByRole('img').evaluate((image) => image.decode());
    await page.route(url, (request) => request.fulfill({ status: 404 }), { times: 1 });
    await scene.getByRole('button', { name: 'Inspect in 3D' }).click();
    await scene.getByText('The pinned export is unavailable.', { exact: true }).waitFor();
    const altered = Buffer.from(await readFile(new URL(asset.source, repo)));
    altered[altered.length - 1] ^= 1;
    await page.route(url, (request) => request.fulfill({ body: altered }), { times: 1 });
    await scene.getByRole('button', { name: 'Retry 3D' }).click();
    await scene.getByText('The export differs from the pinned revision.', { exact: true }).waitFor();
    const delivered = page.waitForResponse((response) => response.url() === url && response.ok());
    await scene.getByRole('button', { name: 'Retry 3D' }).click();
    const payload = await (await delivered).body();
    assert.equal(payload.length, asset.bytes);
    assert.equal(digest(payload), asset.sha256);
    const canvas = scene.locator('canvas');
    const picker = scene.getByRole('combobox', { name: 'Teaching view' });
    await canvas.waitFor();
    assert.equal(await picker.inputValue(), title + ' and C-bands');
    const full = await canvas.screenshot({ path: dir + 'trachea-' + variant + '-bands.png' });
    await picker.selectOption(title + ' alone');
    const wall = await canvas.screenshot({ path: dir + 'trachea-' + variant + '-wall.png' });
    assert.ok(!wall.equals(full), 'Isolating the shell must visibly remove C-bands');
    await scene.getByRole('link', { name: 'Open in 3D Stage ↗' }).click();
    await page.waitForURL((url) => url.hash.startsWith('#/stage/trachea-' + variant + '-v1'));
    await canvas.waitFor();
    assert.equal(await picker.inputValue(), title + ' alone');
    const back = page.getByRole('link', { name: returnLabel });
    assert.equal(await back.getAttribute('href'), '#/' + route);
    await back.press('Enter');
    await page.waitForURL((url) => url.hash === '#/' + route);
  }
  const download = page.getByRole('link', { name: 'Exact cutaway GLB', exact: true });
  const cutaway = manifest.assets.find((asset) => asset.id === 'tracheaCutaway');
  const payload = await (await page.request.get(new URL(await download.getAttribute('href'), base).href)).body();
  assert.equal(digest(payload), cutaway.sha256);
  await page.getByRole('link', { name: /Follow the airway to the terminal cluster/ }).click();
  await page.waitForURL((url) => url.hash === '#/use-cases/systems/respiratory?detail=respiratory-route');
  assert.equal(await page.getByLabel('Detail view').inputValue(), 'respiratory-route');
  console.log('PASS shared airway selections, exact payloads, missing/corrupt recovery, Stage return and route lesson.');
}

// Exercise shared airway Stage links on another origin against the same build.
async function checkAirwayAtAnotherOrigin(context, base) {
  const page = await context.newPage();
  const host = 'https://gallery.invalid';
  try {
    await page.route(host + '/**', async (route) => {
      const url = new URL(route.request().url());
      const response = await page.request.get(base + url.pathname + url.search);
      await route.fulfill({ response });
    });
    for (const [lesson, variant] of [['use-cases/one-breath', 'cutaway'], ['compare/trachea-r06', 'open']]) {
      await page.goto(host + '/#/' + lesson);
      const scene = page.getByRole('region', { name: 'Interactive scene' });
      await scene.getByRole('img').evaluate((poster) => poster.decode());
      await scene.getByRole('button', { name: 'Inspect in 3D' }).click();
      await scene.locator('canvas').waitFor();
      await scene.getByRole('link', { name: /Open in 3D Stage/ }).click();
      await page.waitForURL((url) => url.hash.startsWith('#/stage/trachea-' + variant));
      await scene.locator('canvas').waitFor();
      const record = page.getByRole('link', { name: 'View asset record →' });
      assert.match(await record.getAttribute('href'), /library\/trachea\/open-airway-r06\?file=[a-f0-9]{64}$/);
    }
  } finally {
    await page.close();
  }
}

export async function checkSpecialistStills(page, base, dir) {
  const place = (route) => galleryRoute(base, route);
  const heading = (name) => page.getByRole('heading', { name, level: 1, exact: true });
  // The local phase comparison has its own exact-byte and recovery checks.
  const originalImages = '.ga-source-evidence img:not([src^="/review-evidence/"])';
  const images = page.locator(originalImages);
  const lessons = [
    ['use-cases/systems/cardiovascular', 'use-cases/heart-slice',
      'Read the same heart slice three ways', 'Cardiovascular', [heart]],
    ['use-cases/systems/respiratory', 'use-cases/one-breath',
      'One Breath · 一次呼吸', 'Respiratory', [breath]],
    ['use-cases/lessons', 'use-cases/dental-layers',
      'Reveal the layers of a prepared incisor', 'Lessons',
      ['lessons/dental-layer-controls/media/control-review-sheet.jpg']],
    ['archive', 'archive/dental-shot-studies',
      'Dental shot studies', 'Experiments & Archive',
      ['fdi31-layer-reveal/source-pose.jpg', 'fdi31-layer-reveal/editorial-reveal.jpg',
        'caries-restoration/poster.svg', 'periodontal-cleaning/poster.svg'].map((file) => shot + file)],
  ];
  const linkTo = (route) => page.locator('.ga-content').locator('a[href="#/' + route + '"]').filter({ visible: true }).first();
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
      await page.getByRole('link', { name: /Follow the airway to the terminal cluster/ }).waitFor();
      assert.equal(await page.getByText('沿气道追踪到肺泡簇', { exact: true }).getAttribute('lang'), 'zh');
      await page.locator('summary').filter({ hasText: 'Original bilingual storyboard' }).click();
    }
    await page.waitForFunction(({ count, selector }) => {
      const elements = [...document.querySelectorAll(selector)];
      return elements.length === count && elements.every((image) => image.complete && image.naturalWidth > 0);
    }, { count: paths.length, selector: originalImages });
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

  await page.goto(place('use-cases/lessons'));
  for (const route of ['use-cases/heart-slice', 'use-cases/one-breath']) {
    await linkTo(route).waitFor();
    await linkTo(route).press('Enter');
    const storyboard = page.locator('summary').filter({ hasText: 'Original bilingual storyboard' });
    if (route.endsWith('/one-breath')) await storyboard.click();
    const src = await images.first().getAttribute('src');
    const asset = '**' + src;
    await page.route(asset, (request) => request.fulfill({ status: 404 }));
    await page.reload();
    if (route.endsWith('/one-breath')) await storyboard.click();
    await page.getByRole('status').filter({ hasText: 'unavailable' }).waitFor();
    await page.getByRole('link', { name: 'Open the original in the source repository' }).waitFor();
    await page.unroute(asset);
    await page.reload();
    if (route.endsWith('/one-breath')) await storyboard.click();
    await page.waitForFunction((selector) => document.querySelector(selector)?.naturalWidth > 0, originalImages);
    await page.goto(place('use-cases/lessons'));
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
  await checkSharedAirway(page, base, dir);
  await checkAirwayAtAnotherOrigin(page.context(), base);
  console.log('PASS specialist still discovery, exact source bytes, deep links, return paths, and missing-image recovery.');
}
