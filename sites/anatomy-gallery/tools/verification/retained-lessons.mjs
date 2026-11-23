import assert from 'node:assert/strict';
import { sha256 as hash } from './assertions.mjs';
import { readFile } from 'node:fs/promises';
import { teachingDisplayPath } from '../../app/src/content/gallery/teaching-data.js';
import { pathways, pathwayPath } from '../../app/src/content/gallery/pathway-data.js';
import {
  skeletalLibraryPath, skeletalPath, skeletalReview, skeletalStops,
} from '../../app/src/content/gallery/skeletal-data.js';

const repo = new URL('../../../../', import.meta.url);

export async function checkPathways(page, dest, dir, delivery) {
  const go = (path) => page.goto(dest + '/#/' + path);
  const figures = page.locator('.ga-source-evidence img');
  const loaded = () => page.waitForFunction(() => {
    const image = document.querySelector('.ga-source-evidence img');
    return image?.complete && image.naturalWidth === 1400 && image.naturalHeight === 1060;
  });
  const detailIds = {
    digestive: 'digestive-duodenal-entry',
    reproductive: 'reproductive-male-context',
    urinary: 'urinary-outlet',
  };
  const testis = JSON.parse(await readFile(new URL(
    'reviews/testis_pathway/2026-10-29-r02/readability.json', repo), 'utf8'));
  await go('use-cases');
  for (const [id, lesson] of Object.entries(pathways)) {
    if (id === 'lymph-collecting-routes') continue;
    const testisSvg = id === 'testis-pathway';
    const bindings = testisSvg ? null : JSON.parse(await readFile(new URL(
      lesson.review.replace('record.json', 'evidence-bindings.json'), repo), 'utf8'));
    const systemPath = 'use-cases/systems/' + lesson.system;
    const detailPath = systemPath + '?detail=' + detailIds[lesson.system];
    const linkName = lesson.en.title + ' · ' + lesson.zh.title + ' →';
    await page.getByRole('link', { name: linkName, exact: true }).press('Enter');
    await loaded();
    await page.getByRole('link', { name: /Return to Body Systems/ }).click();
    assert.equal(new URL(page.url()).hash, '#/' + systemPath);
    await go(detailPath);
    await page.getByRole('link', { name: linkName, exact: true }).click();
    for (const lang of ['en', 'zh']) {
      const zh = lang === 'zh';
      if (zh) await page.getByRole('link', { name: '中文', exact: true }).press('Enter');
      const title = page.getByRole('heading', { level: 1, name: lesson[lang].title, exact: true });
      await title.waitFor();
      await page.reload();
      await loaded();
      assert.equal(new URL(page.url()).hash, '#/' + pathwayPath(id, lang) + '?from=' + detailIds[lesson.system]);
      const pngPath = lesson.folder + '/' + lesson.file + '-' + lang + '.png';
      const original = delivery.assets.find(({ path }) => path === pngPath);
      const display = delivery.assets.find(({ path }) => path === teachingDisplayPath(pngPath));
      const expected = testisSvg
        ? testis.results.find(({ language }) => language === lang).artifacts.display.current_sha256
        : bindings.find(({ language }) => language === lang).png_sha256;
      const src = await figures.getAttribute('src');
      if (testisSvg) {
        assert.equal(hash(Buffer.from(decodeURIComponent(src.replace(/^data:image\/svg\+xml,/, '')))), expected);
      } else {
        assert.equal(display.sourceSha256, expected);
        assert.equal(src, '/assets/' + display.sha256 + '/' + display.name);
        assert.equal(hash(await (await page.request.get(dest + src)).body()), display.sha256);
      }
      assert.equal(await figures.evaluate((image) => image.closest('[lang]').lang), lang);
      await page.screenshot({ path: dir + id + '-' + lang + '.png', fullPage: true });
      await page.setViewportSize({ width: 1024, height: 768 });
      assert.ok(await figures.evaluate((image) => image.clientWidth >= 760 &&
        document.documentElement.scrollWidth <= innerWidth + 1));
      await figures.screenshot({ path: dir + id + '-' + lang + '-1024.png' });
      await page.setViewportSize({ width: 1280, height: 900 });
      if (zh && original) {
        const route = '**' + src;
        const fallback = '/assets/' + original.sha256 + '/' + original.name;
        const failed = (request) => request.fulfill({ status: 503 });
        await page.route(route, failed);
        await page.reload();
        await page.locator(`img[src="${fallback}"]`).waitFor();
        await loaded();
        assert.equal(hash(await (await page.request.get(dest + fallback)).body()), expected);
        await page.route('**' + fallback, failed);
        await page.reload();
        await page.getByRole('link', { name: '在来源档案中打开原图' }).waitFor();
        assert.ok(await page.getByText(lesson.zh.cue, { exact: true }).isVisible());
        await page.screenshot({ path: dir + id + '-fallback.png' });
        await page.unroute(route);
        await page.unroute('**' + fallback);
        await page.reload();
        await loaded();
      }
    }
    await page.getByRole('link', { name: /返回人体系统/ }).click();
    assert.equal(new URL(page.url()).hash, '#/' + detailPath);
    await go('use-cases');
  }
  await page.route('**/assets/**', (request) => request.fulfill({ status: 503 }));
  await go(pathwayPath('testis-pathway', 'en'));
  await loaded();
  await page.getByRole('link', { name: '中文', exact: true }).press('Enter');
  await loaded();
  await page.unroute('**/assets/**');
  await go('use-cases/testis-pathway/unsupported');
  await page.getByRole('heading', { name: 'View unavailable' }).waitFor();
  console.log('PASS all six pathway figures, exact identities, Body Systems detail returns, language, laptop readability, WebP to original PNG, missing media and recovery.');
}

export async function checkLymph(page, dest, dir) {
  const id = 'lymph-collecting-routes';
  const owner = 'models/lymph-collecting-routes/source-context-refined-r01/';
  const binding = JSON.parse(await readFile(new URL(owner + 'projection-binding.json', repo), 'utf8'));
  const standalone = await readFile(new URL(owner + 'index.html', repo), 'utf8');
  const lesson = pathways[id];
  const parent = 'use-cases/systems/lymphatic?detail=lymphatic-venous-angle';
  const suffix = '?from=lymphatic-venous-angle';
  const route = (lang) => '#/' + pathwayPath(id, lang) + suffix;
  const plate = page.locator('.ga-lymph-plate img');
  const svg = page.locator('.ga-lymph-plate svg');
  const paths = svg.locator('path');
  const show = page.getByRole('button', { name: 'Show direction', exact: true });
  const pause = page.getByRole('button', { name: 'Pause direction', exact: true });
  const decode = () => plate.evaluate((image) => image.decode());
  const discover = () => page.getByRole('link', { name: /Lymph collecting routes ·/ }).press('Enter');

  await page.goto(dest + '/#/use-cases');
  await discover();
  await decode();
  assert.equal(new URL(page.url()).hash, '#/' + pathwayPath(id));
  await page.goto(dest + '/#/' + parent);
  await discover();
  assert.equal(new URL(page.url()).hash, route('en'));
  await decode();
  assert.equal(await paths.count(), 0);
  await show.press('Enter');
  await paths.last().waitFor();

  const geometry = await paths.evaluateAll((elements) => elements.map((path) => ({
    view: path.dataset.view,
    d: path.getAttribute('d'),
    mask: path.getAttribute('mask'),
    dash: getComputedStyle(path).strokeDasharray,
    duration: getComputedStyle(path).animationDuration,
  })));
  assert.equal(geometry.length, 2);
  for (const { view, d, mask, dash, duration } of geometry) {
    assert.ok(standalone.includes('id="' + view + '-flow" d="' + d + '"'));
    assert.equal(mask, 'url(#lymph-cap-mask)');
    assert.equal(dash, '5px, 19px');
    assert.equal(duration, '3.2s');
    assert.equal(binding.selected_projection[view].rings, 5);
  }
  const caps = await svg.locator('mask circle').evaluateAll((circles) =>
    circles.map(({ cx, cy, r }) => [cx.baseVal.value, cy.baseVal.value, r.baseVal.value]));
  const expectedCaps = Object.values(binding.selected_projection).flatMap(({ panel_points }) => [
    [...panel_points[0], 9], [...panel_points.at(-1), 9],
  ]);
  assert.equal(caps.length, 4);
  caps.forEach((cap, i) => cap.forEach((value, j) => assert.ok(Math.abs(value - expectedCaps[i][j]) < 0.0002)));
  for (const path of await paths.all()) {
    const offsets = await path.evaluate((element) => {
      const [animation] = element.getAnimations();
      animation.pause();
      return [400, 1200].map((time) => {
        animation.currentTime = time;
        return parseFloat(getComputedStyle(element).strokeDashoffset);
      });
    });
    assert.deepEqual(offsets, [-3, -9]);
  }
  const plateCapture = { style: '.ga-lymph-controls { visibility: hidden; }' };
  await page.locator('.ga-lymph-plate').screenshot({ ...plateCapture, path: dir + 'lymph-moving-phase.png' });
  await pause.press('Enter');
  assert.equal(await paths.count(), 0);
  await page.locator('.ga-lymph-plate').screenshot({ ...plateCapture, path: dir + 'lymph-static-en.png' });
  await show.press('Enter');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.getByRole('status').filter({ hasText: 'Static plate · reduced motion' }).waitFor();
  assert.ok(await show.isDisabled());
  assert.equal(await paths.count(), 0);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await show.click();
  await pause.waitFor();
  await page.getByRole('link', { name: '中文', exact: true }).press('Enter');
  await page.getByRole('button', { name: '暂停方向' }).waitFor();
  await page.getByRole('button', { name: '暂停方向' }).press('Enter');

  await page.setViewportSize({ width: 1024, height: 768 });
  for (const lang of ['en', 'zh']) {
    await page.goto(dest + '/' + route(lang));
    await page.reload();
    await page.getByRole('heading', { name: lesson[lang].title, exact: true }).waitFor();
    await decode();
    const src = await plate.getAttribute('src');
    const response = await page.request.get(dest + src);
    assert.equal(response.status(), 200);
    assert.equal(hash(await response.body()), binding.input_plate_sha256[lang]);
    assert.ok(await plate.evaluate((image) => image.naturalWidth === 1520 &&
      image.naturalHeight === 1960 && image.clientWidth > 760 &&
      document.documentElement.scrollWidth <= innerWidth + 1));
    assert.equal(await paths.count(), 0);
    await page.screenshot({ path: dir + 'lymph-' + lang + '-1024.png', fullPage: true });
    if (lang === 'zh') {
      await page.route('**' + src, (request) => request.fulfill({ status: 503 }));
      await page.reload();
      await page.getByRole('status').filter({ hasText: '图像无法载入。' }).waitFor();
      assert.ok(await page.getByRole('button', { name: '显示方向' }).isDisabled());
      assert.equal(await paths.count(), 0);
      assert.match(await page.getByRole('link', { name: /打开原尺寸 PNG/ }).getAttribute('href'), /^https:\/\/github\.com\//);
      assert.ok(await page.getByText(lesson.zh.limits, { exact: true }).isVisible());
      await page.screenshot({ path: dir + 'lymph-missing.png' });
      await page.unroute('**' + src);
      await page.reload();
      await decode();
    }
  }
  await page.getByRole('link', { name: /返回人体系统/ }).click();
  assert.equal(new URL(page.url()).hash, '#/' + parent);
  await page.setViewportSize({ width: 1280, height: 900 });
  console.log('PASS lymph discovery, exact bilingual PNGs, authored five-ring geometry and caps, rendered dash progression, pause, reduced motion, reload, detail return and missing media.');
}

export async function checkSkeletal(page, dest, dir, delivery) {
  const source = JSON.parse(await readFile(new URL(skeletalReview, repo), 'utf8'));
  const skeletalSystem = 'use-cases/systems/skeletal';
  const detail = 'skeletal-source';
  const discover = page.getByRole('link', { name: 'Skeletal relationships →', exact: true });
  const content = page.locator('.ga-content');
  const heading = (name) => content.getByRole('heading', { level: 1, name, exact: true });
  const figures = content.locator('.ga-skeletal-plates figure');
  const images = figures.locator('img');
  const go = (path) => page.goto(dest + '/#/' + path);
  const route = (entry) => '/assets/' + entry.sha256 + '/' + entry.name;
  const asset = (path) => delivery.assets.find((entry) => entry.path === path);
  async function checkBytes(file) {
    const response = await page.request.get(dest + route(file));
    assert.equal(response.status(), 200, file.name);
    const bytes = await response.body();
    assert.equal(bytes.length, file.bytes, file.name);
    assert.equal(hash(bytes), file.sha256, file.name);
  }

  await go('use-cases');
  await discover.press('Enter');
  await heading(skeletalStops[0].title).waitFor();
  await go(skeletalSystem);
  await discover.click();
  assert.equal(new URL(page.url()).hash, '#/' + skeletalPath);
  await content.getByRole('link', { name: /Return to Body Systems · Skeletal/ }).click();
  assert.equal(new URL(page.url()).hash, '#/' + skeletalSystem);
  await go(skeletalSystem + '?detail=' + detail);
  await discover.press('Enter');
  assert.equal(new URL(page.url()).hash, '#/' + skeletalPath + '?from=' + detail);

  for (const stop of skeletalStops) {
    const study = source.studies.find((entry) => entry.id === stop.sourceId);
    const lesson = skeletalPath + '/' + stop.id + '?from=' + detail;
    const revision = skeletalLibraryPath(stop.id);
    await content.getByRole('navigation', { name: 'Skeletal relationships' })
      .getByRole('link', { name: stop.title, exact: true }).press('Enter');
    await heading(stop.title).waitFor();
    assert.equal(new URL(page.url()).hash, '#/' + lesson);
    await go(lesson);
    await page.reload();
    await heading(stop.title).waitFor();
    await page.setViewportSize({ width: 1024, height: 768 });
    for (const image of await images.all()) {
      if (await image.isVisible()) await image.evaluate((element) => element.decode());
    }
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    const boxes = await Promise.all([images.nth(0).boundingBox(), images.nth(1).boundingBox()]);
    assert.ok(boxes.every(({ width }) => width > 400));
    assert.equal(boxes[0].y, boxes[1].y);
    await page.screenshot({ path: dir + stop.id + '-1024.png' });
    await content.getByText('Oblique and neutral-gray views', { exact: true }).click();
    for (const [i, index] of [0, 1, 3, 2].entries()) {
      const evidence = study.evidence[index];
      const file = asset(evidence.file);
      assert.equal(file.sha256, evidence.sha256);
      assert.equal(evidence.sourceSha256, study.sha256);
      const image = images.nth(i);
      await image.evaluate((element) => element.decode());
      assert.equal(await image.getAttribute('src'), route(file));
      await checkBytes(file);
    }

    const library = content.getByRole('link', { name: 'Open the exact Library revision →', exact: true });
    assert.equal(await library.getAttribute('href'), '#/' + revision + '?from=' + detail);
    await library.click();
    await heading(stop.title).waitFor();
    await page.reload();
    const glb = asset(study.file);
    assert.equal(glb.sha256, study.sha256);
    assert.equal(glb.bytes, study.bytes);
    assert.equal(await content.locator('a[download]').count(), 1);
    assert.equal(await content.locator('a[download]').getAttribute('href'), route(glb));
    const exports = content.locator('section').filter({
      has: page.getByRole('heading', { name: 'Exact exports', exact: true }),
    });
    await exports.getByText(glb.sha256, { exact: true }).waitFor();
    await content.getByText(/BodyParts3D © The Database Center for Life Science/).waitFor();
    await checkBytes(glb);
    await page.goBack();
    await library.waitFor();
    assert.equal(new URL(page.url()).hash, '#/' + lesson);
    await library.click();
    await content.getByRole('link', { name: 'Return to the relationship plates →' }).click();
    assert.equal(new URL(page.url()).hash, '#/' + lesson);
    await content.getByRole('link', { name: /Return to Body Systems · Skeletal/ }).click();
    assert.equal(new URL(page.url()).hash, '#/' + skeletalSystem + '?detail=' + detail);
    await go(lesson);

    const missing = asset(study.evidence[0].file);
    await page.route('**' + route(missing), (request) => request.fulfill({ status: 503 }));
    await page.reload();
    await figures.first().getByRole('status').filter({ hasText: 'unavailable' }).waitFor();
    await figures.first().getByRole('link', { name: 'Open the original in the source repository' }).waitFor();
    await figures.nth(1).locator('img').evaluate((image) => image.decode());
    assert.ok(await content.getByText(stop.cue, { exact: true }).isVisible());
    assert.ok(await library.isVisible());
    await page.screenshot({ path: dir + stop.id + '-missing.png' });
    await library.click();
    await content.getByRole('status').filter({ hasText: 'Front view unavailable' }).waitFor();
    assert.ok(await content.locator('a[download]').isVisible());
    await page.unroute('**' + route(missing));
    await go(lesson);
    await page.reload();
    await images.first().evaluate((image) => image.decode());
    await content.getByRole('link', { name: /Return to Body Systems · Skeletal/ }).click();
    assert.equal(new URL(page.url()).hash, '#/' + skeletalSystem + '?detail=' + detail);
    await discover.press('Enter');
  }

  await go('library/cartilage-assembly');
  for (const stop of skeletalStops) {
    await content.locator('a[href="#/' + skeletalLibraryPath(stop.id) + '"]').waitFor();
  }
  await go(skeletalLibraryPath(skeletalStops[0].id) + '?from=unknown');
  assert.equal(await content.getByRole('link', { name: 'Return to the relationship plates →' }).getAttribute('href'),
    '#/' + skeletalPath + '/' + skeletalStops[0].id);
  await go(skeletalPath + '/unknown');
  await heading('View unavailable').waitFor();
  await page.setViewportSize({ width: 1280, height: 900 });
  console.log('PASS skeletal discovery, eight exact plates, two exact dated Library exports, attribution, laptop layout, direct links, reload, returns and missing-media recovery.');
}

export async function checkDentalArch(page, dest, dir, delivery) {
  const { order } = await import('../../../../lessons/arch-identification/plate.mjs');
  const packagePath = 'reviews/teeth_gums/2026-10-26-set-contact-checkpoint/';
  const routeFor = (asset) => '/assets/' + asset.sha256 + '/' + asset.name;
  const lookup = (path) => delivery.assets.find((entry) => entry.path === packagePath + path);
  const image = page.locator('#plate image');
  const radio = (fdi) => page.locator(`[role="radio"][data-fdi="${fdi}"]`);
  const readSelection = async (fdi) => {
    assert.equal(await page.locator('#fdi').textContent(), 'FDI ' + fdi);
    assert.equal(await radio(fdi).getAttribute('aria-checked'), 'true');
    assert.equal(await radio(fdi).getAttribute('tabindex'), '0');
  };
  await page.goto(dest + '/#/use-cases');
  await page.getByRole('link', { name: /Dental arch identification/ }).press('Enter');
  await page.getByRole('heading', { name: 'Name the tooth', exact: true }).waitFor();
  await radio('11').waitFor();
  for (const [arch, first, last, leftSide, missing] of [
    ['upper', '17', '27', 'Patient right', '18 · 28'],
    ['lower', '37', '47', 'Patient left', '38 · 48'],
  ]) {
    await page.locator(`[data-arch="${arch}"]`).click();
    await image.waitFor();
    const original = lookup('media/' + arch + '-occlusal-teeth.png');
    const display = lookup('display/' + arch + '-occlusal-teeth.webp');
    assert.equal(display.sourceSha256, original.sha256);
    assert.equal(await image.getAttribute('href'), routeFor(display));
    for (const asset of [original, display]) {
      assert.equal(hash(await (await page.request.get(dest + routeFor(asset))).body()), asset.sha256);
    }
    assert.equal(await page.locator('#screen-left').textContent(), leftSide);
    assert.equal(await page.locator('#missing').textContent(), missing);
    assert.equal(await page.getByRole('radio').count(), 14);
    for (const fdi of order(arch)) {
      await radio(fdi).click();
      await readSelection(fdi);
      const side = ['1', '4'].includes(fdi[0]) ? 'Patient right' : 'Patient left';
      assert.equal(await page.locator('#identity dd').nth(1).textContent(), side);
    }
    await page.keyboard.press('Home');
    assert.ok(await radio(first).evaluate((el) => el.getRootNode().activeElement === el));
    for (const fdi of order(arch)) {
      await readSelection(fdi);
      await page.keyboard.press('ArrowRight');
    }
    await page.keyboard.press('ArrowLeft');
    await readSelection(last);
    await page.keyboard.press('ArrowDown');
    await readSelection(first);
    await page.keyboard.press('ArrowUp');
    await readSelection(last);
    await page.keyboard.press('Home');
    await page.keyboard.press('End');
    await readSelection(last);
    const crown = arch === 'upper' ? '16' : '46';
    await page.locator(`.hit[data-fdi="${crown}"]`).click();
    await readSelection(crown);
    await page.screenshot({ path: dir + 'dental-arch-' + arch + '.png', fullPage: true });
  }
  await page.locator('[data-lang="zh"]').click();
  await readSelection('46');
  assert.equal(await page.locator('#identity dd').nth(1).textContent(), '患者右侧');
  await page.getByRole('button', { name: '上牙弓', exact: true }).click();
  await readSelection('16');
  await page.getByRole('button', { name: '下牙弓', exact: true }).click();
  await readSelection('46');
  await page.setViewportSize({ width: 1024, height: 768 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  await page.screenshot({ path: dir + 'dental-arch-lower-zh-1024.png', fullPage: true });
  await page.setViewportSize({ width: 1280, height: 900 });
  const lower = routeFor(lookup('display/lower-occlusal-teeth.webp'));
  const fallback = routeFor(lookup('media/lower-occlusal-teeth.png'));
  const unavailable = (request) => request.fulfill({ status: 503 });
  const openLower = async () => {
    await page.reload();
    await page.getByRole('button', { name: 'Lower arch', exact: true }).click();
  };
  await page.route('**' + lower, unavailable);
  await openLower();
  await page.locator(`#plate image[href="${fallback}"]`).waitFor();
  await page.route('**' + fallback, unavailable);
  await openLower();
  await page.getByText('Arch image unavailable', { exact: true }).waitFor();
  await radio('46').click();
  await page.keyboard.press('ArrowUp');
  await readSelection('45');
  await page.locator('[data-lang="zh"]').click();
  await readSelection('45');
  await page.screenshot({ path: dir + 'dental-arch-fallback.png', fullPage: true });
  await page.unroute('**' + lower);
  await page.unroute('**' + fallback);
  await page.getByRole('button', { name: '重试图像' }).press('Enter');
  await image.waitFor();
  await readSelection('45');
  assert.ok(await radio('45').evaluate((el) => el.getRootNode().activeElement === el));
  await page.getByText('来源与范围', { exact: true }).click();
  const attribution = await page.getByRole('link', { name: '来源署名' }).getAttribute('href');
  assert.match(attribution, /models\/teeth_gums\/exports\/r02\/ATTRIBUTION\.md$/);
  await page.getByRole('link', { name: '← Use Cases', exact: true }).click();
  await page.getByRole('heading', { level: 1, name: 'Use Cases' }).waitFor();
  await page.goto(dest + '/#/use-cases/dental-arch/lower');
  await page.reload();
  await radio('31').waitFor();
  await readSelection('31');
  console.log('PASS dental arch FDI labels and crown hotspots, patient sides, full keyboard travel, language and per-arch memory, exact media, missing-image selector and retry.');
}
