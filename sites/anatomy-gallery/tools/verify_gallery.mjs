const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
import { createHash } from 'node:crypto';
import { mkdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
import { adrenalComparison, adrenalLesson, adrenalLibrary } from '../app/src/content/gallery/adrenal-study.js';
import { assetUrl, comparePath, lessonPath, libraryPath, portrait, revisions } from '../app/src/content/gallery/catalog.js';
import { balanced, checkBalancedDownload } from './verify_survey_bookmarks.mjs';
import { checkArchive } from './verify_archive.mjs';
import { checkSpecialistStills } from './verify_specialist_stills.mjs';
import { checkDentalArch, checkLymph, checkPathways, checkSkeletal } from './verify_retained_teaching.mjs';
import { checkOvaryLesson } from './verify_ovary_lesson.mjs';
import {
  oralFolder, oralSpaces, oralSpacesPath, ovaryLocator, regionalLessons, regionalPath, teachingDisplayPath,
} from '../app/src/content/gallery/teaching-data.js';

async function checkTeaching(page, dest, dir, delivery) {
  const index = new Map(delivery.assets.map((asset) => [asset.path, asset]));
  const url = (path) => dest + '/#/' + path;
  const assetPath = (asset) => '/assets/' + asset.sha256 + '/' + asset.name;
  const images = page.locator('.ga-source-evidence img');
  const heading = (name) => page.getByRole('heading', { level: 1, name, exact: true });
  const waitForPlates = (count) => page.waitForFunction((expected) => {
    const plates = [...document.querySelectorAll('.ga-source-evidence img')];
    return plates.length === expected && plates.every((image) => image.complete && image.naturalWidth > 0);
  }, count);
  const checkAsset = async (asset) => {
    const response = await page.request.get(dest + assetPath(asset));
    assert.equal(response.status(), 200, asset.path);
    assert.equal(response.headers()['content-type'], asset.mediaType);
    const raw = await response.body();
    assert.equal(raw.length, asset.bytes);
    assert.equal(createHash('sha256').update(raw).digest('hex'), asset.sha256);
  };
  const checkPlates = async (originalPaths) => {
    await waitForPlates(originalPaths.length);
    const shown = await images.evaluateAll((elements) => elements.map((image) => ({
      src: image.getAttribute('src'),
      naturalWidth: image.naturalWidth,
      naturalHeight: image.naturalHeight,
      width: image.getBoundingClientRect().width,
      available: image.closest('.ga-source-evidence').clientWidth,
    })));
    for (const [i, originalPath] of originalPaths.entries()) {
      const original = index.get(originalPath);
      const display = index.get(teachingDisplayPath(originalPath));
      assert.equal(display.sourceSha256, original.sha256);
      assert.equal(shown[i].src, assetPath(display));
      assert.equal(shown[i].naturalWidth, display.width);
      assert.equal(shown[i].naturalHeight, display.height);
      assert.ok(shown[i].width >= shown[i].available - 1, display.path);
      await checkAsset(display);
      await checkAsset(original);
    }
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  };

  await page.goto(url('use-cases'));
  await heading('Use Cases').waitFor();
  await page.screenshot({ path: dir + 'teaching-use-cases.png' });
  await page.getByRole('link', { name: /Oral spaces/ }).press('Enter');
  await heading(oralSpaces.en.question).waitFor();
  await page.getByRole('link', { name: 'English', exact: true }).click();
  await page.getByRole('link', { name: '中文', exact: true }).press('Enter');
  await heading(oralSpaces.zh.question).waitFor();
  await page.goBack();
  await heading(oralSpaces.en.question).waitFor();
  for (const [lang, lesson] of Object.entries(oralSpaces)) {
    await page.goto(url(oralSpacesPath + '/' + lang));
    await page.reload();
    await heading(lesson.question).waitFor();
    await checkPlates([oralFolder + 'oral-spaces-' + lang + '.png']);
    assert.equal(await images.first().evaluate((image) => image.closest('[lang]').lang), lang);
    await page.screenshot({ path: dir + 'oral-spaces-' + lang + '.png', fullPage: true });
    await page.setViewportSize({ width: 1024, height: 768 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await images.first().screenshot({ path: dir + 'oral-spaces-' + lang + '-1024.png' });
    await page.setViewportSize({ width: 1280, height: 900 });
  }
  const cutawayLink = page.getByRole('link', { name: /Locate the oral vestibule in a 2D cutaway/ });
  await page.getByRole('link', { name: /查看头颈部主要唾液腺的位置/ }).click();
  await page.reload();
  await page.getByRole('link', { name: 'Parotid duct course', exact: true }).click();
  await cutawayLink.click();
  await heading(oralSpaces.zh.question).waitFor();
  await page.getByRole('link', { name: 'English', exact: true }).press('Enter');
  await heading(oralSpaces.en.question).waitFor();
  await page.reload();
  await page.getByRole('link', { name: /Return to the parotid duct course/ }).click();
  assert.equal(new URL(page.url()).hash, '#/use-cases/head-and-neck/duct-course');
  await cutawayLink.click();
  await heading(oralSpaces.en.question).waitFor();
  await page.getByRole('link', { name: '← Use Cases', exact: true }).click();
  await page.getByRole('link', { name: 'Regional locators →' }).click();
  await heading('Regional locators').waitFor();
  await page.screenshot({ path: dir + 'regional-locators.png' });
  for (const lesson of regionalLessons.filter((entry) => entry !== ovaryLocator)) {
    await page.getByRole('link', { name: lesson.name + ' →', exact: true }).press('Enter');
    await heading(lesson.question).waitFor();
    assert.equal(new URL(page.url()).hash, '#/' + regionalPath + '/' + lesson.id);
    await page.reload();
    await heading(lesson.question).waitFor();
    const originals = lesson.plates.map(({ original }) => original);
    await checkPlates(originals);
    const model = index.get(lesson.model);
    const download = page.getByRole('link', { name: /Exact source GLB/ });
    assert.equal(await download.getAttribute('href'), assetPath(model));
    await checkAsset(model);
    await page.screenshot({ path: dir + lesson.id + '.png', fullPage: true });
    await page.setViewportSize({ width: 1024, height: 768 });
    await waitForPlates(originals.length);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await images.first().screenshot({ path: dir + lesson.id + '-1024.png' });
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.getByRole('link', { name: /assembly in Body Systems/ }).click();
    assert.equal(new URL(page.url()).hash, '#/use-cases/systems/' + lesson.system);
    await page.getByRole('link', { name: lesson.name + ' →', exact: true }).click();
    await heading(lesson.question).waitFor();
    await page.getByRole('link', { name: '← Regional locators', exact: true }).click();
    await heading('Regional locators').waitFor();
  }

  const aortic = regionalLessons[0];
  const original = index.get(aortic.plates[0].original);
  const display = index.get(teachingDisplayPath(original.path));
  const withhold = (asset) => page.route('**' + assetPath(asset), (route) => route.fulfill({ status: 503 }));
  await withhold(display);
  await page.goto(url(regionalPath + '/' + aortic.id));
  await waitForPlates(2);
  assert.equal(await images.first().getAttribute('src'), assetPath(original));
  await withhold(original);
  await page.reload();
  await page.getByRole('status').filter({ hasText: 'Arch region overview unavailable' }).waitFor();
  await waitForPlates(1);
  await page.getByRole('link', { name: 'Open the original in the source repository' }).waitFor();
  await page.getByRole('link', { name: /Review and source identity/ }).waitFor();
  await page.screenshot({ path: dir + 'teaching-missing-media.png' });
  await page.unroute('**' + assetPath(original));
  await page.unroute('**' + assetPath(display));
  await page.reload();
  await waitForPlates(2);
  assert.equal(await images.first().getAttribute('src'), assetPath(display));
  console.log('PASS oral spaces and three regional locators, exact model and plate responses, keyboard, reload and returns, laptop layouts, PNG fallback and missing media.');
}

async function checkAuthoring(browser, page, base, dir) {
  const stop = adrenalLesson.stops[1];
  const revision = adrenalLesson.revision;
  const file = revisions[revision];
  const library = '#/' + libraryPath(revision);
  const lesson = '#/' + lessonPath + '/' + stop.id;
  const sceneReady = (view) => view.locator('.ga-canvas:not([hidden]) canvas').waitFor();

  await page.goto(base);
  await page.getByRole('searchbox').fill('adrenal');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await page.getByRole('heading', { name: adrenalLibrary.label, exact: true }).click();
  assert.equal(new URL(page.url()).hash, library);
  const exportLink = page.getByRole('link', { name: 'Download exact GLB' });
  assert.equal(await exportLink.getAttribute('href'), assetUrl(file));
  const exportDownload = page.waitForEvent('download');
  await exportLink.click();
  const exportBytes = await readFile(await (await exportDownload).path());
  assert.equal(exportBytes.length, file.bytes);
  assert.equal(createHash('sha256').update(exportBytes).digest('hex'), file.sha256);

  await page.goBack();
  assert.equal(await page.getByRole('searchbox').inputValue(), 'adrenal');
  await page.goForward();
  await page.getByRole('link', { name: 'Open in 3D Stage' }).click();
  await page.getByRole('link', { name: 'Return to asset record' }).click();
  await page.waitForURL((url) => url.hash === library);
  await page.getByRole('link', { name: 'Regional localization lesson' }).click();
  await page.getByRole('link', { name: 'Next · ' + stop.label }).click();
  await page.waitForURL((url) => url.hash === lesson);
  await page.getByRole('heading', { name: stop.title, exact: true }).waitFor();
  await page.getByRole('button', { name: 'Inspect in 3D' }).click();
  await sceneReady(page);

  await page.getByRole('link', { name: 'Inspect the fold evidence' }).click();
  await page.waitForURL((url) => url.hash === '#/' + comparePath);
  await page.getByRole('heading', { name: adrenalComparison.title }).waitFor();
  const section = portrait(adrenalComparison.sections.display);
  await page.getByText('Inspect the source sections').click();
  await page.getByRole('img', { name: adrenalComparison.sections.alt }).waitFor();
  await page.waitForFunction((url) => [...document.images].some((img) =>
    img.getAttribute('src') === url && img.naturalWidth > 0), section);
  await page.route('**' + section, (route) => route.fulfill({ status: 503, body: 'unavailable' }));
  await page.reload();
  await page.getByText('Inspect the source sections').click();
  await page.getByRole('status').filter({ hasText: adrenalComparison.sections.title + ' unavailable' }).waitFor();
  await page.getByText(adrenalComparison.sections.finding).waitFor();
  await page.waitForFunction(() => {
    const images = [...document.querySelectorAll('.ga-pair img')];
    return images.length === 2 && images.every((image) => image.naturalWidth > 0);
  });
  await page.unroute('**' + section);
  await page.getByRole('link', { name: 'Original review and render provenance' }).waitFor();
  await page.getByRole('button', { name: 'Reveal revisions and scores' }).click();
  await page.getByRole('link', { name: 'Neutral material' }).click();
  await page.getByRole('button', { name: 'Share comparison' }).click();
  const comparison = await page.getByLabel('Comparison link').inputValue();
  assert.match(comparison, /finish=neutral&order=(ab|ba)/);
  await page.screenshot({ path: dir + 'compare.png' });
  await page.getByRole('link', { name: 'Inspect ' + revision + ' in 3D Stage' }).click();
  await sceneReady(page);
  await page.getByRole('link', { name: 'Return to comparison' }).click();
  await page.waitForURL((url) => url.hash === new URL(comparison).hash);

  await page.getByRole('link', { name: 'Return to the teaching view' }).click();
  await page.waitForURL((url) => url.hash === lesson);
  await page.getByRole('link', { name: 'Open in 3D Stage' }).click();
  await sceneReady(page);
  await page.getByLabel('Material', { exact: true }).selectOption('Neutral');
  await page.getByLabel('Key light').selectOption('0.75');
  await page.getByRole('button', { name: 'Share this view' }).click();
  const shared = await page.getByLabel('Persistent preset link').inputValue();
  const link = new URL(shared);
  const query = new URLSearchParams(link.hash.split('?')[1]);
  const preset = JSON.parse(query.get('view'));
  assert.equal(link.search, '');
  assert.equal(preset.sha256, file.sha256);
  assert.equal(preset.revision, revision);
  assert.equal(preset.part, stop.part);
  assert.ok(preset.camera.height > 0);
  const fresh = await browser.newPage();
  try {
    await fresh.goto(shared);
    await sceneReady(fresh);
    assert.equal(await fresh.getByLabel('Material', { exact: true }).inputValue(), 'Neutral');
    assert.equal(await fresh.getByLabel('Key light').inputValue(), '0.75');
    assert.equal(await fresh.getByLabel('Structure', { exact: true }).inputValue(), stop.part);
    await fresh.getByRole('button', { name: 'Share this view' }).click();
    const reopened = new URL(await fresh.getByLabel('Persistent preset link').inputValue());
    const reopenedPreset = JSON.parse(new URLSearchParams(reopened.hash.split('?')[1]).get('view'));
    for (const key of ['position', 'target']) {
      preset.camera[key].forEach((value, axis) => {
        assert.ok(Math.abs(reopenedPreset.camera[key][axis] - value) < 1e-8);
      });
    }
    assert.ok(Math.abs(reopenedPreset.camera.height - preset.camera.height) < 1e-8);
    await fresh.getByRole('link', { name: stop.returnLabel }).click();
    await fresh.waitForURL((url) => url.hash === lesson);
  } finally {
    await fresh.close();
  }

  await page.reload();
  await sceneReady(page);
  await page.getByRole('button', { name: 'Share this view' }).click();
  const exportedView = await page.getByLabel('Persistent preset link').inputValue();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export WebP' }).click();
  await (await download).saveAs(dir + 'stage.webp');
  const poster = await readFile(dir + 'stage.webp');
  assert.equal(poster.toString('ascii', 8, 12), 'WEBP');
  assert.ok(poster.includes(Buffer.from('dc:source="' + exportedView.replaceAll('&', '&amp;') + '"')));
  assert.ok(poster.includes(Buffer.from('Three.js r180')));
  await page.screenshot({ path: dir + 'stage.png' });

  await page.route('**' + assetUrl(file), (route) => route.fulfill({ status: 503, body: 'unavailable' }));
  await page.goto(shared);
  await page.getByText('The pinned export is unavailable.').waitFor();
  assert.ok(await page.getByRole('button', { name: 'Retry 3D' }).isVisible());
  await page.getByRole('link', { name: stop.returnLabel }).click();
  await page.waitForURL((url) => url.hash === lesson);
  await page.unroute('**' + assetUrl(file));
  console.log('PASS authored Library download, lesson stops, matched Compare with optional media unavailable, and exact Stage share, poster and unavailable model.');
}

async function checkCollections(p, dest, repo, dir) {
  await p.goto(dest + '/#/');
  await p.getByRole('heading', { name: 'Asset Library', exact: true }).waitFor();
  assert.equal(await p.title(), 'Anatomy Gallery');
  await p.screenshot({ path: dir + 'library.png' });
  const entryCount = p.locator('.ga-browse-tools strong[aria-live="polite"]');
  const declaredEntries = await entryCount.innerText();
  const more = p.getByRole('button', { name: 'Show more entries' });
  const entries = p.locator('.ga-asset');
  async function expandEntries() {
    const declared = Number.parseInt(await entryCount.innerText(), 10);
    while (await entries.count() < declared) {
      const before = await entries.count();
      await more.click();
      await p.waitForFunction((count) => document.querySelectorAll('.ga-asset').length > count, before);
    }
    assert.equal(await entries.count(), declared);
    const routes = await entries.evaluateAll((links) => links.map((link) => link.getAttribute('href')));
    assert.equal(new Set(routes).size, declared, 'Pagination should not repeat a route');
  }

  await p.getByLabel('Rating', { exact: true }).selectOption('rated');
  await p.waitForFunction(() => document.querySelector('.ga-asset .ga-scored') !== null);
  for (const [sort, direction] of [['rating-low', 1], ['rating-high', -1]]) {
    await p.getByLabel('Sort', { exact: true }).selectOption(sort);
    await p.waitForURL((url) => new URLSearchParams(url.hash.split('?')[1]).get('sort') === sort);
    await p.waitForFunction((order) => {
      const totals = [...document.querySelectorAll('.ga-asset .ga-rating')]
        .map((cell) => cell.textContent)
        .filter((rating) => rating.endsWith('/16'))
        .map((rating) => parseInt(rating, 10));
      return totals.length >= 4 && totals.every((total, i) => !i || (total - totals[i - 1]) * order >= 0);
    }, direction);
    await expandEntries();
    const ratings = await entries.locator('.ga-rating').allTextContents();
    const totals = ratings.filter((rating) => rating.endsWith('/16')).map((rating) => parseInt(rating, 10));
    assert.ok(totals.length >= 4);
    assert.ok(totals.every((total, i) => !i || (total - totals[i - 1]) * direction >= 0));
    assert.ok(ratings.slice(totals.length).every((rating) => rating === 'Partially rated'));
    const titles = await entries.locator('h3').allTextContents();
    for (const title of ['Esophageal wall', 'Seated nail unit', 'Terminal airspaces', 'Adrenal glands · s1233', 'Ovary + tubal ends', 'Bronchial tree']) {
      assert.ok(titles.includes(title), title);
    }
  }

  // A cataloged dental tool is outside the maintained-family assessment campaign.
  const search = p.getByRole('searchbox');
  const waitForFilter = (name, value) => p.waitForURL(
    (url) => new URLSearchParams(url.hash.split('?')[1]).get(name) === value,
  );
  await search.fill('cotton_tweezers');
  await p.getByRole('button', { name: 'Search', exact: true }).click();
  await waitForFilter('q', 'cotton_tweezers');
  await p.waitForFunction(() => !document.querySelector('.ga-asset .ga-scored'));
  await p.getByLabel('Rating', { exact: true }).selectOption('unrated');
  await waitForFilter('rating', 'unrated');
  const tweezers = entries.filter({ has: p.getByRole('heading', { name: /Cotton tweezers/ }) });
  await tweezers.getByText('Unrated', { exact: true }).waitFor();
  const [system] = (await tweezers.locator('.ga-classification').innerText()).split(' · ');
  await p.getByLabel('System', { exact: true }).selectOption(system);
  await waitForFilter('system', system);
  await p.getByRole('button', { name: 'Tree', exact: true }).click();
  await waitForFilter('layout', 'tree');
  const branch = p.locator('.ga-branch[open]').filter({ has: tweezers });
  await branch.waitFor();
  assert.equal(await p.locator('.ga-branch[open]').count(), 1);
  await p.reload();
  await branch.waitFor();
  await p.waitForFunction(() => document.querySelector('input[type="search"]')?.value === 'cotton_tweezers');
  assert.equal(await p.getByLabel('System', { exact: true }).inputValue(), system);
  assert.equal(await p.getByLabel('Rating', { exact: true }).inputValue(), 'unrated');
  assert.equal(await p.locator('.ga-scored').count(), 0);
  await p.screenshot({ path: dir + 'library-tree.png' });
  await p.getByRole('button', { name: 'Cards', exact: true }).click();
  await p.locator('.ga-asset-cards').first().waitFor();
  await search.fill('unfindable-search-record');
  await p.getByRole('button', { name: 'Search', exact: true }).click();
  await p.getByText('No entries match these filters.').waitFor();
  await p.getByRole('link', { name: 'Clear filters' }).click();
  await p.getByText(declaredEntries, { exact: true }).waitFor();
  assert.equal(await p.getByLabel('Sort', { exact: true }).inputValue(), 'rating-high');
  await expandEntries();
  for (const [family, revision] of [['uff_tomo1b', 'r01'], ['cotton_tweezers', 'r04'], ['mouth_mirror', 'r01']]) {
    await p.goto(dest + '/#/library?q=' + family);
    await p.locator('a[href="#/library/' + family + '/' + revision + '"]').waitFor();
  }
  await p.getByRole('link', { name: 'Body Systems', exact: true }).click();
  await p.locator('.ga-system-card').first().waitFor();
  assert.equal(await p.locator('.ga-system-card').count(), 11);
  await p.waitForFunction(() =>
    [...document.querySelectorAll('.ga-system-card img')].filter(i => i.getBoundingClientRect().top < innerHeight).every(i => i.naturalWidth > 0));
  await p.screenshot({ path: dir + 'body-systems.png' });
  const addresses = await p.locator('.ga-system-card').evaluateAll((cards) => cards.map((a) => a.href));
  for (const address of addresses) {
    await p.goto(address);
    await p.getByRole('heading', { name: 'Scope and limits' }).waitFor();
    await p.waitForFunction(() =>
      [...document.querySelectorAll('.ga-pair img')].every((i) => i.naturalWidth > 0),
    );
    await p.getByRole('link', { name: /Asset detail \(/ }).click();
    const detail = p.getByLabel('Detail view');
    await detail.selectOption({ index: 1 });
    await p.reload();
    await p.waitForFunction(
      () =>
        document.querySelectorAll('.ga-system-plate img').length === 2 &&
        [...document.querySelectorAll('.ga-system-plate img')].every((i) => i.naturalWidth > 0),
    );
    assert.ok((await p.locator('.ga-legend li').count()) > 0);
    await p.getByRole('link', { name: 'Browse related assets' }).click();
    await p.locator('.ga-asset').first().waitFor();
  }
  await p.getByRole('link', { name: 'Use Cases', exact: true }).click();
  await p.getByRole('link', { name: 'Head & Neck' }).click();
  await p.getByRole('heading', { name: 'Find the three gland pairs' }).waitFor();
  await p.locator('.ga-part-frame img').evaluate((image) => image.decode());
  await p.getByText('Source views from the r02 study', { exact: true }).click();
  await p.waitForFunction(() =>
    [...document.querySelectorAll('.ga-source-evidence img')].filter(i => i.naturalWidth > 0 && i.src.includes('/assets/')).length === 3,
  );
  await p.getByRole('link', { name: 'Parotid duct course', exact: true }).press('Enter');
  await p.getByRole('heading', { name: 'Follow the parotid duct over the masseter' }).waitFor();
  await p.getByRole('heading', { name: 'The submandibular crossing remains unresolved' }).waitFor();
  await p.screenshot({ path: dir + 'head-neck.png' });
  await p.getByRole('link', { name: 'See the rejected reconstruction in Compare' }).click();
  await p.waitForFunction(() =>
    [...document.querySelectorAll('.ga-source-evidence img')].filter(i => i.naturalWidth > 0).length === 2,
  );
  await p.screenshot({ path: dir + 'salivary-review.png' });
  await p.getByRole('link', { name: 'Return to the parotid duct lesson' }).click();
  assert.equal(new URL(p.url()).hash, '#/use-cases/head-and-neck/duct-course');
  await p.getByRole('link', { name: 'Open this lesson’s export in Asset Library' }).click();
  assert.match(new URL(p.url()).hash, /^#\/library\/salivary_glands\/z-native-shared-r01\?file=[0-9a-f]{64}$/);
  await p.getByRole('link', { name: 'glands-and-parotid-ducts.glb ↓', exact: true }).waitFor();
  await p.goto(dest + '/#/compare/salivary-native-r02');
  await p.getByRole('link', { name: 'Open the exact r02 exports in Asset Library' }).click();
  assert.equal(new URL(p.url()).hash, '#/library/salivary_glands/z-native-scoped-r02');
  assert.match(await p.locator('.ga-study-plate').getAttribute('src'), /\/glands-ducts-front-source\.webp$/);
  assert.match(await p.getByRole('link', { name: 'Source license and credits ↗' }).getAttribute('href'),
    /sources\/datasets\/z-anatomy\/salivary-region\/License\.txt$/);
  const salivary = JSON.parse(await readFile(path.join(repo,
    'reviews/salivary_glands/2026-10-26-native-scoped-r02/decision.json'), 'utf8'));
  for (const entry of salivary.media) {
    const name = path.basename(entry.path);
    const url = dest + '/assets/' + entry.sha256 + '/' + name;
    if (name.endsWith('.glb')) {
      const link = p.getByRole('link', { name, exact: false });
      assert.equal(await link.getAttribute('href'), new URL(url).pathname);
    }
    const response = await p.request.get(url);
    assert.equal(response.status(), 200);
    assert.match(response.headers()['content-type'], name.endsWith('.glb') ? /model\/gltf-binary/ : /image\/webp/);
    const bytes = await response.body();
    assert.equal(bytes.length, entry.bytes);
    assert.equal(createHash('sha256').update(bytes).digest('hex'), entry.sha256);
  }
  const diagnostic = '**/assets/*/rejection-closeup.webp';
  await p.route(diagnostic, (r) => r.fulfill({ status: 503, body: 'unavailable' }));
  await p.getByRole('link', { name: 'Review the excluded duct course' }).click();
  await p.getByRole('status').filter({ hasText: 'Rejected left submandibular duct unavailable' }).waitFor();
  await p.getByRole('link', { name: 'Source record and diagnostic replay' }).waitFor();
  await p.unroute(diagnostic);
  await p.setViewportSize({ width: 390, height: 844 });
  await p.goto(dest + '/#/use-cases/head-and-neck/location');
  await p.getByRole('heading', { name: 'Find the three gland pairs' }).waitFor();
  assert.equal(await p.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await p.screenshot({ path: dir + 'head-neck-mobile.png' });
  await p.setViewportSize({ width: 1280, height: 900 });
  await p.goto(dest + '/#/use-cases/systems/respiratory');
  await p.getByRole('link', { name: 'Explore Airway Review' }).click();
  const airwayLinks = p.locator('.ga-feature');
  await airwayLinks.first().waitFor();
  const airwayUrls = await airwayLinks.evaluateAll((links) => links.map((link) => link.href));
  assert.deepEqual(airwayUrls.map((address) => new URL(address).hash), [
    '#/compare/nasal-airspace-r01', '#/compare/trachea-r06', '#/use-cases/airway/first-fork',
  ]);
  await airwayLinks.last().click();
  await p.getByRole('heading', { name: 'Trace the first bronchial fork' }).waitFor();
  const originalBronchial = await p.getByRole('link', { name: 'Compare the original r13' }).getAttribute('href');
  assert.equal(originalBronchial, '#/compare/bronchial-r13');
  const reviewUrls = [...airwayUrls.slice(0, 2), dest + '/' + originalBronchial];
  const exactAirway = [
    ['nih3d-airspace-r01', ['nasal_airspace.glb']],
    ['open-airway-r06', ['trachea-open.glb', 'trachea-cutaway.glb']],
    ['authored-central-fairing-r13', ['bronchial_central_fairing.glb']],
  ];
  const delivery = JSON.parse(await readFile(path.join(repo,
    'sites/anatomy-gallery/app/src/content/assets/delivery-index.json'), 'utf8'));
  for (const [i, address] of reviewUrls.entries()) {
    await p.goto(address);
    await p.getByRole('heading', { name: 'Scope and limits' }).waitFor();
    await p.waitForFunction(() => {
      const images = [...document.querySelectorAll('.ga-source-evidence img')];
      return images.length >= 2 && images.every((image) => image.naturalWidth > 0);
    });
    if (address.endsWith('/bronchial-r13')) {
      assert.match(await p.locator('.ga-source-evidence img').first().getAttribute('src'), /\/before-close\.webp$/);
    }
    if (i === 1) {
      await p.screenshot({ path: dir + 'trachea-r06.png' });
      await p.getByRole('link', { name: 'Trachea · closed display cast r05' }).click();
      await p.getByRole('link', { name: 'Open this exact revision in Asset Library' }).click();
      await p.getByRole('link', { name: 'trachea_host_conforming_illustration.glb', exact: false }).waitFor();
      assert.equal(await p.getByRole('link', { name: 'trachea-open.glb', exact: false }).count(), 0);
      await p.getByRole('link', { name: 'Trachea · open airway and cutaway r06' }).click();
    } else {
      await p.getByRole('link', { name: 'Open this exact revision in Asset Library' }).click();
    }
    const [revision, filenames] = exactAirway[i];
    await p.getByRole('heading', { name: 'Exact exports' }).waitFor();
    assert.ok(new URL(p.url()).hash.endsWith('/' + revision));
    if (revision === 'authored-central-fairing-r13') {
      assert.match(await p.locator('.ga-study-plate').getAttribute('src'), /\/after-whole\.webp$/);
    }
    for (const name of filenames) {
      const entry = delivery.assets.find((asset) =>
        (asset.paths ?? [asset.path]).some((file) => file?.endsWith('/' + revision + '/' + name)));
      const link = p.getByRole('link', { name: name + ' ↓', exact: true });
      assert.equal(await link.getAttribute('href'), '/assets/' + entry.sha256 + '/' + name);
      const response = await p.request.get(new URL(await link.getAttribute('href'), dest).href);
      assert.equal(response.status(), 200);
      const raw = await response.body();
      assert.equal(raw.length, entry.bytes);
      assert.equal(createHash('sha256').update(raw).digest('hex'), entry.sha256);
    }
  }
  await checkTeaching(p, dest, dir, delivery);
  await checkOvaryLesson(p, dest, dir, delivery);
  await checkPathways(p, dest, dir, delivery);
  await checkLymph(p, dest, dir);
  await checkSkeletal(p, dest, dir, delivery);
  await checkDentalArch(p, dest, dir, delivery);
  await checkArchive(p, dest, dir, delivery);
  await checkSpecialistStills(p, dest, dir);
  await p.goto(dest + '/#/use-cases/systems/endocrine?detail=absent');
  await p.getByRole('heading', { name: 'View unavailable' }).waitFor();
  await p.goto(dest + '/#/use-cases/systems/endocrine');
  await p.getByRole('heading', {name: 'Head-to-pelvis gland locator'}).waitFor();
  await p.waitForFunction(() => [...document.querySelectorAll('.ga-pair img')].every(i => i.naturalWidth > 0));
  await p.screenshot({ path: dir + 'endocrine-system.png' });
  const missingPlate = await p.locator('.ga-system-plate img').first().getAttribute('src');
  await p.route('**' + missingPlate, (r) => r.fulfill({ status: 503, body: 'unavailable' }));
  await p.reload();
  await p.getByRole('status').filter({ hasText: 'unavailable' }).waitFor();
  await p.locator('.ga-system-plate img').first().waitFor();
  await p.getByText('Sources and attribution').waitFor();
  await p.unroute('**' + missingPlate);
  await p.goto(dest + '/#/library/terminal-airspaces-r02');
  await p.getByText(/Rating · 15\/16/).waitFor();
  await p.waitForFunction(() => document.querySelector('.ga-study-plate')?.naturalWidth > 0);
  await p.goto(dest + '/rubric');
  await p.getByRole('heading', { name: 'Review a teaching asset' }).waitFor();
  const family = '#family-adrenals';
  const candidate = '#candidate-adrenals__source-candidate-01';
  const related = '#refinement-surface-adrenal';
  const familyRow = p.locator('.ga-content').filter({ has: p.getByRole('link', { name: 'Review this version' }) });
  const candidateTitle = p.getByRole('heading', { name: 'Adrenal pair · BodyParts3D', exact: true });
  const familyReturn = p.getByRole('link', { name: 'Browse BodyParts3D adrenal family' });
  const review = JSON.parse(await readFile(path.join(repo,
    'reviews/adrenals/2026-10-23-bp3d-bounded-migration/bounded-record.json')));
  const witnesses = review.evidence.filter((image) => image.reviewPhase === 'candidate').reverse();
  const evidence = p.locator('.ga-pair img');
  await p.goto(dest + '/' + family);
  await familyRow.waitFor();
  await familyRow.getByRole('link', { name: 'Review this version' }).press('Enter');
  await candidateTitle.waitFor();
  assert.equal(new URL(p.url()).hash, '#/compare/adrenals__source-candidate-01');
  await p.reload();
  await candidateTitle.waitFor();
  await p.waitForFunction(() => {
    const images = [...document.querySelectorAll('.ga-pair img')];
    return images.length === 2 && images.every((image) => image.naturalWidth > 0);
  });
  await p.screenshot({ path: dir + 'bodyparts3d-review.png', fullPage: true });
  for (const [index, witness] of witnesses.entries()) {
    const url = await evidence.nth(index).getAttribute('src');
    assert.ok(url.includes(witness.sha256) && url.endsWith(path.basename(witness.file)));
    const response = await p.request.get(new URL(url, dest).href);
    assert.equal(response.headers()['content-type'], 'image/webp');
    assert.equal(createHash('sha256').update(await response.body()).digest('hex'), witness.sha256);
  }
  await p.getByText('Export identity and attribution').click();
  await p.getByText(review.artifact.sha256, { exact: true }).waitFor();
  const candidateDownload = p.waitForEvent('download');
  await p.getByRole('link', { name: 'Download this GLB' }).click();
  const candidateFile = await readFile(await (await candidateDownload).path());
  assert.equal(candidateFile.length, review.artifact.bytes);
  assert.equal(createHash('sha256').update(candidateFile).digest('hex'), review.artifact.sha256);
  await p.goBack();
  await familyRow.waitFor();
  await familyRow.getByRole('link', { name: 'Related s1233 teaching study' }).click();
  await p.getByRole('heading', { name: 'The inferior adrenal fold', exact: true }).waitFor();
  assert.equal(new URL(p.url()).hash, '#/compare/adrenal-r04-r05');
  await familyReturn.click();
  await familyRow.waitFor();
  await p.goto(dest + '/' + related);
  await p.reload();
  await p.getByRole('heading', { name: 'The inferior adrenal fold', exact: true }).waitFor();
  await familyReturn.click();
  await familyRow.waitFor();
  const missingImage = '**/assets/' + witnesses[0].sha256 + '/*';
  await p.route(missingImage, (r) => r.fulfill({ status: 503, body: 'unavailable' }));
  await p.goto(dest + '/' + candidate);
  await candidateTitle.waitFor();
  await p.getByText('Oblique view unavailable.', { exact: false }).waitFor();
  assert.equal(await p.locator('.ga-pair img').count(), 1);
  await p.getByRole('link', { name: 'Bounded review record and source identities' }).waitFor();
  await familyReturn.click();
  await familyRow.waitFor();
  await p.unroute(missingImage);
  await p.goto(dest + '/?view=1#swirendo_fdi31');
  await p.getByRole('heading', { name: 'FDI31 · prepared specimen' }).waitFor();
  await checkBalancedDownload(p);
  const balancedRoute = '**/assets/' + balanced.sha256 + '/' + balanced.name;
  for (const failure of [
    { status: 503, body: 'unavailable' },
    { status: 200, contentType: 'model/gltf-binary', body: Buffer.alloc(balanced.bytes) },
  ]) {
    await p.route(balancedRoute, (r) => r.fulfill(failure));
    await p.getByRole('button', { name: 'Download Balanced GLB' }).click();
    await p.getByRole('status').filter({ hasText: 'Download unavailable.' }).waitFor();
    await p.unroute(balancedRoute);
  }
  await p.goto(dest + '/#/archive/planning');
  await p.getByRole('heading', { name: 'Survey planning report' }).waitFor();
  await p.getByRole('link', { name: 'Overlaps', exact: true }).waitFor();
  await p.getByRole('link', { name: 'Gaps', exact: true }).click();
  await p.getByRole('heading', { name: 'Clinical/anatomical review' }).waitFor();
  await p.goto(dest + '/#/stage/adrenal-v1?view=bad');
  await p.getByRole('heading', { name: 'View unavailable' }).waitFor();
  await p.goto(dest + '/#/stage');
  await p
    .getByLabel('Open local GLB')
    .setInputFiles(
      path.join(repo, 'assemblies/endocrine-locator/adrenal-study-r05/s1233-adrenals-regional.glb'),
    );
  await p.getByRole('button', { name: 'Export WebP' }).waitFor();
  await p.waitForFunction(
    () => !!document.querySelector('.ga-canvas canvas') && !document.querySelector('.ga-canvas').hidden,
  );
  assert.ok(await p.getByRole('button', { name: 'Share this view' }).isDisabled());
  await p.goto(dest + '/#/library');
  await p.setViewportSize({ width: 390, height: 780 });
  assert.ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
}

const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  headless: true,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
try {
  const ctx = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    permissions: ['clipboard-read', 'clipboard-write'],
  });
  const p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', (e) => {
    console.log('PAGE ERROR', String(e));
    errors.push(String(e));
  });
  const dest = process.env.MODEL_SURVEY_PREVIEW_URL || 'http://127.0.0.1:8858';
  const repo = fileURLToPath(new URL('../../../', import.meta.url));
  const dir = process.env.MODEL_SURVEY_CAPTURE_DIR
    ? path.resolve(process.env.MODEL_SURVEY_CAPTURE_DIR) + path.sep
    : path.join(repo, '.artifacts/gallery-library-systems/');
  await mkdir(dir, { recursive: true });
  if (process.argv.includes('--ovary')) {
    const delivery = JSON.parse(await readFile(path.join(repo,
      'sites/anatomy-gallery/app/src/content/assets/delivery-index.json'), 'utf8'));
    await checkOvaryLesson(p, dest, dir, delivery);
  } else {
    await checkAuthoring(browser, p, dest, dir);
  }
  if (!process.argv.includes('--authoring') && !process.argv.includes('--ovary')) {
    await checkCollections(p, dest, repo, dir);
    console.log(
      'PASS all eleven systems, BodyParts3D adrenal review, Head & Neck, Airway, exact evidence, bookmarks, rubric, FDI31 exact and failed downloads, archive and invalid or local presets.',
    );
  }
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
}
