import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile } from 'node:fs/promises';
import displayImages from '../display-images.json' with { type: 'json' };
import { airway, staticReviews, assetUrl, byPath } from '../app/src/content/gallery/catalog.js';

const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.MODEL_SURVEY_PREVIEW_URL || 'http://127.0.0.1:8889';
const captures = process.env.MODEL_SURVEY_STATIC_CAPTURES;
const route = (to) => '/#/' + to;
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');

const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  headless: true,
  chromiumSandbox: true,
});
try {
  if (captures) await mkdir(captures, { recursive: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  const go = (path) => page.goto(base + route(path));
  const content = page.locator('.ga-content');
  const heading = (title) => content.getByRole('heading', { name: title, level: 1, exact: true });
  const checked = new Set();

  async function verifyAsset(file) {
    if (checked.has(file.sha256)) return;
    const response = await page.request.get(base + assetUrl(file));
    assert.equal(response.status(), 200, file.path);
    assert.match(response.headers()['content-type'], new RegExp('^' + file.mediaType));
    const bytes = await response.body();
    assert.equal(bytes.length, file.bytes, file.path);
    assert.equal(hash(bytes), file.sha256, file.path);
    checked.add(file.sha256);
  }

  async function verifyEvidence(study) {
    const figures = content.locator('.ga-static-evidence figure');
    for (const summary of await content.locator('details > summary').all()) {
      await summary.click();
    }
    const expected = study.sections.flatMap(({ views }) => views);
    assert.equal(await figures.count(), expected.length, study.id);
    for (const [index, witness] of expected.entries()) {
      const figure = figures.nth(index);
      const title = await figure.locator('figcaption').textContent();
      assert.ok(title.includes(witness.title), study.id + ' witness order');
      const image = figure.locator('img');
      await image.evaluate((element) => element.decode());
      assert.equal(await image.getAttribute('src'), assetUrl(witness.asset));
      await verifyAsset(witness.asset);
      if (witness.original) {
        assert.equal(await figure.getByRole('link', { name: 'Original image' }).getAttribute('href'), assetUrl(witness.original));
        await verifyAsset(witness.original);
      }
    }
  }

  async function verifyLayout(study) {
    for (const [i, section] of study.sections.entries()) {
      const group = content.locator('.ga-static-evidence').nth(i);
      if (!await group.isVisible()) continue;
      const [first, second] = await group.locator('figure').evaluateAll((figures) =>
        figures.slice(0, 2).map((figure) => {
          const { top, left, width } = figure.getBoundingClientRect();
          return { top, left, width };
        }));
      assert.ok(first.width > 330, study.id + ' evidence width');
      if (section.paired && second) {
        assert.ok(second.left > first.left && Math.abs(second.top - first.top) < 2, study.id);
      } else if (second) {
        assert.ok(second.top > first.top && Math.abs(second.left - first.left) < 2, study.id);
      }
    }
  }

  await go('compare');
  for (const study of staticReviews) {
    const entry = content.getByRole('link', { name: study.title, exact: true });
    await entry.press('Enter');
    await heading(study.title).waitFor();
    if (study.chapters) {
      const links = await content.locator('ul').first().getByRole('link').allTextContents();
      assert.deepEqual(links, study.chapters.map(({ title }) => title));
    }
    for (const entry of study.chapters ?? [study]) {
      await go(entry.compare);
      await heading(entry.title).waitFor();
      await page.reload();
      await heading(entry.title).waitFor();
      if (entry.inspector) assert.equal(await content.getByRole('link', { name: entry.inspector.label + ' ↗' }).getAttribute('href'), entry.inspector.href);
      await verifyEvidence(entry);
      await verifyLayout(entry);
      if (captures && ['abdomen-label-r01', 'bronchial-r09', 'spinal-relationships-r03', 'marrow-cutaway-r05',
        'penile-components-r04', 'uff-tomo1b-r01', 'fdi31-interface-locked', 'mouth-mirror-r01'].includes(entry.id)) {
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.screenshot({ path: captures + '/' + entry.id + '.png' });
      }
      if (entry.library) {
        const link = content.getByRole('link', { name: 'Open the exact Library revision →' });
        assert.equal(await link.getAttribute('href'), '#/' + entry.library);
        await link.click();
        await content.getByText(entry.revision, { exact: true }).waitFor();
        await heading(entry.title).waitFor();
        assert.equal(await content.locator('a:not([href])').count(), 0, entry.id + ' Library links need destinations');
        if (entry.inspector) assert.equal(await content.getByRole('link', { name: entry.inspector.label + ' ↗' }).getAttribute('href'), entry.inspector.href);
        for (const file of entry.exports) {
          assert.ok((await content.textContent()).includes(file.sha256));
          if (file.unavailable) {
            await content.getByText(file.unavailable, { exact: true }).waitFor();
            assert.equal(await content.locator('a[download]').count(), 0);
            continue;
          }
          const download = content.locator('a[download]').filter({ hasText: file.name });
          assert.equal(await download.getAttribute('href'), assetUrl(file));
          await verifyAsset(file);
          if (entry.id === 'mouth-mirror-r01') {
            const [received] = await Promise.all([page.waitForEvent('download'), download.click()]);
            assert.equal(hash(await readFile(await received.path())), file.sha256);
          }
        }
        await content.getByRole('link', { name: 'Open the saved source review →' }).click();
        await content.getByRole('link', { name: 'Open the exact Library revision →' }).waitFor();
        assert.equal(new URL(page.url()).hash, '#/' + entry.compare);
      }
      if (study.chapters) {
        await content.getByRole('link', { name: '← ' + study.title, exact: true }).click();
        await heading(study.title).waitFor();
      }
    }
    await content.getByRole('link', { name: '← Compare', exact: true }).click();
    await heading('Compare').waitFor();
  }

  const abdomen = staticReviews.find(({ id }) => id === 'abdomen-label-r01');
  const first = abdomen.sections[0].views[0];
  const displayRoute = '**' + assetUrl(first.asset);
  const originalRoute = '**' + assetUrl(first.original);
  const unavailable = (request) => request.fulfill({ status: 503 });
  await page.route(displayRoute, unavailable);
  await go(abdomen.compare);
  await content.locator('img[src="' + assetUrl(first.original) + '"]').evaluate((image) => image.decode());
  await page.route(originalRoute, unavailable);
  await page.reload();
  await content.getByRole('status').filter({ hasText: first.title + ' unavailable.' }).waitFor();
  await content.getByRole('link', { name: 'Open the original in the source repository' }).waitFor();
  assert.equal(await content.locator('.ga-static-evidence img').count(), 1);
  if (captures) await page.screenshot({ path: captures + '/missing-evidence.png' });
  await page.unroute(displayRoute, unavailable);
  await page.unroute(originalRoute, unavailable);
  await page.reload();
  await content.locator('img[src="' + assetUrl(first.asset) + '"]').evaluate((image) => image.decode());

  for (const bindings of Object.values(displayImages)) {
    for (const [source, display] of bindings) {
      await verifyAsset(byPath.get(display));
      await verifyAsset(byPath.get(source));
    }
  }
  for (const study of airway.filter(({ evidence }) => evidence.some((view) => view.original))) {
    await go(study.compare);
    await heading(study.title).waitFor();
    for (const witness of study.evidence.filter((view) => view.original)) {
      const webp = '**' + assetUrl(witness.asset);
      await content.locator('img[src="' + assetUrl(witness.asset) + '"]').evaluate((image) => image.decode());
      await page.route(webp, unavailable);
      await page.reload();
      await content.locator('img[src="' + assetUrl(witness.original) + '"]').evaluate((image) => image.decode());
      await page.unroute(webp, unavailable);
      await page.reload();
    }
  }

  await go('compare/polish-appendix/unknown-section');
  await content.getByRole('heading', { level: 1, name: 'View unavailable' }).waitFor();
  assert.equal(await content.locator('.ga-static-evidence').count(), 0);
  await go('use-cases/biliary-pathway/en');
  await heading('Biliary and pancreatic pathways').waitFor();
  if (staticReviews.some(({ id }) => id === 'fdi31-interface-locked')) {
    await go('library/swirendo_fdi31');
    await content.getByRole('link', { name: /FDI31.*interface/ }).waitFor();
    await content.locator('button').filter({ hasText: /Balanced/ }).waitFor();
  }
  const api = await (await page.request.get(base + '/api/gallery/v1/studies')).json();
  for (const study of staticReviews) {
    const expected = (study.chapters ?? [study]).flatMap(({ exports }) => exports.map(({ sha256 }) => sha256));
    assert.deepEqual(api.reviews.find(({id}) => id === study.id).revisions, expected);
  }
  console.log(`PASS Chrome: ${staticReviews.length} Compare entries, ${checked.size} exact display, source and export identities, direct links, reload, missing evidence and return navigation.`);
} finally {
  await browser.close();
}
