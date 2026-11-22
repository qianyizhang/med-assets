import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import snapshotReference from '../snapshot-reference.json' with { type: 'json' };
import { assetUrl, ratingAxes } from '../app/src/content/gallery/catalog.js';
import { libraryRows } from '../app/src/content/gallery/library-data.js';

const baseline = 'e8399bd107cc6129db2d3712113e9cb5a3628664';
const repo = fileURLToPath(new URL('../../../', import.meta.url));
const git = (...args) => execFileSync('git', args, { cwd: repo, maxBuffer: 20 * 1024 * 1024 });
const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
const isGeometry = (file) => /\.(glb|stl|blend|obj)$/i.test(file);

function inputDisposition(file) {
  if (file.startsWith('sources/datasets/hra/')) return 'Original HRA input. Library lists its teaching derivative.';
  if (file === 'sources/datasets/marrow-comparison-v1/BP3D-FJ3365.obj') return 'Marrow comparison source input.';
  if (file === 'reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/v1/native-elbow.glb') return 'Pinned ulnar v1 replay input.';
  return null;
}

function baselineGeometry() {
  const paths = git('ls-tree', '-r', '--name-only', '-z', baseline).toString().split('\0').filter(isGeometry);
  return paths.map((file) => {
    const raw = git('cat-file', 'blob', baseline + ':' + file);
    const pointer = /^version https:\/\/git-lfs\.github\.com\/spec\/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n$/.exec(raw.toString());
    return {
      path: file,
      sha256: pointer ? pointer[1] : digest(raw),
      bytes: pointer ? Number(pointer[2]) : raw.length,
      disposition: inputDisposition(file),
    };
  });
}

function indexedRoutes(snapshot, tracked, review) {
  const rows = libraryRows(snapshot, review, { localPreview: true });
  const records = new Map();
  const indexed = new Map();
  for (const row of rows) {
    const history = row.history.length ? row.history : [{ library: row.path, exports: row.media ?? [] }];
    for (const record of history) {
      if (!record.exports.length) continue;
      assert.ok(!records.has(record.library), record.library);
      records.set(record.library, record);
      for (const file of record.exports) {
        assert.ok(!indexed.has(file.path), file.path + ' has multiple revision owners');
        indexed.set(file.path, { file, route: record.library });
      }
    }
  }
  const counts = { glb: 0, stl: 0, blend: 0, input: 0 };
  for (const expected of tracked) {
    const entry = indexed.get(expected.path);
    if (expected.disposition) {
      assert.equal(entry, undefined, expected.path);
      counts.input++;
      continue;
    }
    assert.ok(entry && !entry.file.unavailable, expected.path);
    assert.equal(entry.file.sha256, expected.sha256, expected.path);
    assert.equal(entry.file.bytes, expected.bytes, expected.path);
    counts[expected.path.split('.').at(-1)]++;
  }
  assert.deepEqual(counts, { glb: 135, stl: 10, blend: 5, input: 12 });
  return { rows, records, indexed, counts };
}

const capture = process.env.MODEL_SURVEY_CAPTURE_DIR;
assert.ok(capture, 'Set MODEL_SURVEY_CAPTURE_DIR to a dedicated receipt directory');
await mkdir(capture, { recursive: true });
const base = process.env.MODEL_SURVEY_PREVIEW_URL || 'http://127.0.0.1:8858';
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const seed = await readFile(path.join(repo, 'sites/anatomy-gallery/app/src/data.json'));
assert.equal(digest(seed), snapshotReference.surveySeedPublication.sourceSeedSha256, 'Frozen Survey seed');
const builtApp = process.env.MODEL_SURVEY_APP_DIR || path.join(repo, 'sites/anatomy-gallery/.local/app');
const review = JSON.parse(await readFile(path.join(builtApp,
  'src/content/gallery/teaching-inputs/teaching-assessments.json')));
assert.deepEqual(Object.fromEntries(review.assessments.filter(({ route }) => [
  'library/ovaries/hra-ovary-tubal-r01', 'library/bronchial_tree/authored-central-fairing-r13',
  'library/esophagus_wall/authored-cutaway-r01',
].includes(route)).map(({ route, axes }) => [route, axes.map(({ score }) => score)])), {
  'library/ovaries/hra-ovary-tubal-r01': [4, null, 3, 3],
  'library/bronchial_tree/authored-central-fairing-r13': [4, 2, 3, 2],
  'library/esophagus_wall/authored-cutaway-r01': [3, 3, 3, 3],
});
const tracked = baselineGeometry();
const { rows, records, indexed, counts } = indexedRoutes(JSON.parse(seed), tracked, review);
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  headless: true,
});
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.route('**/*', (route) => route.request().url().startsWith(base + '/') ? route.continue() : route.abort());
  const errors = [];
  page.on('pageerror', (error) => errors.push(String(error)));
  const go = (route) => page.goto(base + '/#/' + route);
  const heading = (name) => page.getByRole('heading', { name, level: 1, exact: true });
  const searchBox = page.getByRole('searchbox', { name: 'Search assets' });
  const links = page.locator('.ga-asset');

  await go('library?layout=tree');
  await heading('Asset Library').waitFor();
  const visibleRoutes = await links.evaluateAll((elements) => elements.map((link) => link.hash.slice(2)));
  assert.deepEqual(visibleRoutes.sort(), rows.map((row) => row.path).sort());

  for (const row of rows) {
    await go(row.path);
    const title = row.history.find((record) => record.library === row.path)?.title
      ?? (row.id === 's1233-adrenal' ? 'Adrenal glands' : row.label);
    await heading(title).waitFor();
    const history = await page.locator('nav[aria-label="Revision history"] a[aria-current], nav[aria-label="Revision history"] li a, nav[aria-label="Asset revision"] a')
      .evaluateAll((elements) => elements.map((link) => link.hash.slice(2)));
    assert.deepEqual(new Set(history), new Set(row.history.map((record) => record.library)), row.id);
  }

  for (const [route, record] of records) {
    await go(route);
    const first = record.exports[0];
    if (record.title) await heading(record.title).waitFor();
    else if (record.revision) {
      await page.locator('nav[aria-label="Asset revision"] a[aria-current="page"][href="#/' + route + '"]').waitFor();
    } else {
      await page.locator('a[href="' + assetUrl(first) + '"]').first().waitFor();
    }
    const exportLinks = await page.locator('a[href^="/assets/"]').evaluateAll((elements) => elements.map((link) => link.getAttribute('href')));
    assert.deepEqual(new Set(exportLinks.filter(isGeometry)),
      new Set(record.exports.filter((file) => !file.unavailable).map(assetUrl)), route);
    for (const file of record.exports.filter((file) => file.unavailable)) {
      assert.equal(await page.getByText(file.sha256, { exact: true }).isVisible(), true, route);
      assert.equal(await page.getByText(file.unavailable, { exact: true }).isVisible(), true, route);
    }
  }

  for (const expected of tracked.filter((file) => !file.disposition)) {
    await go('library?q=' + encodeURIComponent(expected.path));
    await page.waitForFunction((needle) => document.querySelector('input[type=search]')?.value === needle, expected.path);
    const match = page.locator('.ga-asset[href="#/' + indexed.get(expected.path).route + '"]');
    await match.waitFor({ timeout: 5000 });
  }

  async function search(query, expectedRoute) {
    await go('library');
    await searchBox.fill(query);
    await page.getByRole('button', { name: 'Search', exact: true }).click();
    const link = page.locator('.ga-asset[href="#/' + expectedRoute + '"]');
    await link.waitFor();
    return link;
  }
  const r13Route = 'library/bronchial_tree/authored-central-fairing-r13';
  for (const term of ['R13', 'authored-central-fairing-r13', 'bronchial_central_fairing.glb']) {
    const r13 = await search(term, r13Route);
    assert.equal(await r13.locator('.ga-asset-status').innerText(), 'Reviewed for teaching task');
    assert.equal(await r13.locator('.ga-rating').innerText(), '11/16');
  }
  const historical = 'models/bronchial_tree/exports/metadata-cleanup-r01/bronchial_tree.glb';
  const metadataRoute = indexed.get(historical).route;
  const historicalDigest = indexed.get(historical).file.sha256;
  await search(historicalDigest.toUpperCase(), metadataRoute);
  const nail = 'models/skin/nail-study-r02/nail.glb';
  await search(indexed.get(nail).file.sha256, indexed.get(nail).route);
  // The Workshop and metadata-only sibling share a filename.
  await (await search(historical, metadataRoute)).press('Enter');
  const shared = page.url();
  const fresh = await browser.newPage();
  await fresh.goto(shared);
  await fresh.getByText('Metadata-only alternative', { exact: true }).first().waitFor();
  await fresh.reload();
  await fresh.getByRole('link', { name: 'bronchial_tree.glb ↓', exact: true }).waitFor();
  await fresh.close();
  await page.getByRole('link', { name: /authored-central-fairing-r13|r13/ }).first().click();
  await page.getByRole('link', { name: 'bronchial_central_fairing.glb ↓' }).waitFor();
  assert.equal(await page.getByRole('link', { name: 'bronchial_tree.glb ↓' }).count(), 0);
  await page.goBack();
  await page.getByText('Metadata-only alternative', { exact: true }).first().waitFor();
  await page.goBack();
  await searchBox.waitFor();
  assert.equal(await searchBox.inputValue(), historical);
  await page.screenshot({ path: path.join(capture, 'metadata-search.png') });

  await (await search('dental_specimens', 'library/uff_tomo1b/r01')).click();
  const uffExport = page.getByRole('link', { name: 'uff-tomo1b-display.glb ↓' });
  await uffExport.waitFor();
  const uffTitle = await page.locator('h1').textContent();
  assert.equal(await uffExport.count(), 1);
  await go('library/dental_specimens');
  await heading(uffTitle).waitFor();
  await page.getByRole('link', { name: 'uff-tomo1b-display.glb ↓' }).waitFor();
  await go('library/fetus');
  await heading('Fetal inset study').waitFor();
  assert.equal(await page.locator('a[href$=".glb"]').count(), 0);
  await go('library/bronchial_tree/unknown');
  await heading('View unavailable').waitFor();

  const ratedRows = rows.filter((row) => row.ratingLabel !== 'Unrated');
  const totals = ratedRows.map(({ score }) => score).filter((score) => score !== null).sort((a, b) => a - b);
  const partialCount = ratedRows.length - totals.length;
  await go('library?rating=rated&sort=rating-low');
  await page.getByText(ratedRows.length + ' entries', { exact: true }).waitFor();
  assert.deepEqual(await page.locator('.ga-asset .ga-rating').allTextContents(), [
    ...totals.map((score) => score + '/16'), ...Array(partialCount).fill('Partially rated'),
  ]);
  await page.getByLabel('Sort', { exact: true }).selectOption('rating-high');
  await page.waitForFunction((value) => document.querySelector('.ga-asset .ga-rating')?.textContent === value,
    totals.at(-1) + '/16');
  assert.equal(await page.getByText('Partially rated', { exact: true }).count(), partialCount);

  for (const assessment of review.assessments) {
    const { date, evaluator, rubric } = assessment;
    assert.equal(digest(git('cat-file', 'blob', rubric.revision + ':' + rubric.path)), rubric.sha256);
    const expected = indexed.get(assessment.export.path);
    assert.equal(expected.route, assessment.route);
    const record = records.get(assessment.route);
    assert.ok(record.assessment, assessment.route);
    const scores = assessment.axes.map((axis) => axis.score);
    const rating = scores.includes(null) ? 'Partially rated' : scores.reduce((sum, score) => sum + score, 0) + '/16';
    const result = page.locator('.ga-asset[href="#/' + assessment.route + '"]');
    for (const needle of [assessment.export.sha256, assessment.export.path]) {
      await go('library?rating=rated&q=' + encodeURIComponent(needle));
      await result.getByText(rating, { exact: true }).waitFor();
    }
    await result.click();
    await heading(record.title).waitFor();
    const visibleRating = page.getByText('Rating · ' + rating, { exact: false });
    await visibleRating.waitFor();
    assert.ok((await visibleRating.textContent()).includes(assessment.task));
    await page.getByRole('link', { name: 'Rating rubric', exact: true }).waitFor();
    const displayed = await page.locator('.ga-detail dt').evaluateAll((terms, axes) =>
      terms.filter((term) => axes.includes(term.textContent)).map((term) => term.nextElementSibling.textContent),
      ratingAxes);
    assert.deepEqual(displayed, scores.map((score) => String(score ?? 'Unrated')), assessment.route);
    await page.getByText('Assessment and reviewed views', { exact: true }).press('Enter');
    const details = page.locator('details[open]').filter({ hasText: 'Assessed export' });
    await details.getByText(evaluator + ' · ' + date + ' · Rubric ' + rubric.revision.slice(0, 8)).waitFor();
    await details.getByText(assessment.export.sha256, { exact: true }).waitFor();
    for (const axis of assessment.axes) {
      await details.getByText(axis.observation, { exact: true }).waitFor();
    }
    for (const source of assessment.sources) {
      assert.equal(await details.getByRole('link', { name: source.label + ' ↗', exact: true }).getAttribute('href'),
        source.url);
      const [, revision, sourcePath] = new URL(source.url).pathname.split('/blob/')[1].match(/^([^/]+)\/(.+)$/);
      git('cat-file', '-e', revision + ':' + sourcePath);
    }
    for (const view of assessment.views) {
      const anchor = details.getByRole('link', { name: view.label + ' ↗', exact: true });
      assert.equal(await anchor.isVisible(), true);
      const href = await anchor.getAttribute('href');
      assert.ok(href.startsWith('/assets/' + view.sha256 + '/'), href);
      const response = await page.request.get(base + href);
      assert.equal(response.status(), 200, view.path);
      const bytes = await response.body();
      assert.equal(bytes.length, view.bytes, view.path);
      assert.equal(digest(bytes), view.sha256, view.path);
      const dimensions = await page.evaluate(async (url) => {
        const image = new Image();
        image.src = url;
        await image.decode();
        return [image.naturalWidth, image.naturalHeight];
      }, href);
      assert.ok(dimensions.every((dimension) => dimension > 0), view.path);
    }
    const portrait = page.locator('.ga-detail img');
    await portrait.evaluate((image) => image.decode());
    await page.setViewportSize({ width: 1024, height: 768 });
    const layout = await portrait.evaluate((image) => {
      const { width, height } = image.getBoundingClientRect();
      return { scaledHeight: width * image.naturalHeight / image.naturalWidth, height,
        pageWidth: document.documentElement.scrollWidth, windowWidth: innerWidth };
    });
    assert.ok(Math.abs(layout.height - layout.scaledHeight) < 1);
    assert.ok(layout.pageWidth <= layout.windowWidth + 1);
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.screenshot({ path: path.join(capture, assessment.route.split('/')[1] + '-rating.png'), fullPage: true });
  }

  for (const [route, file] of [
    ['library/bronchial_tree/authored-lobar-fairing-r09', 'bronchial_lobar_fairing.glb'],
    ['library/joints/z-shoulder-r01', 'shoulder_z_native.glb'],
    ['library/thyroid_ct_s0189/source-candidate-02', 'thyroid_ct_s0189_source_frame.glb'],
  ]) {
    await go('library?rating=unrated&q=' + file);
    await page.locator('.ga-asset[href="#/' + route + '"]').getByText('Unrated').waitFor();
    await go('library?rating=rated&q=' + file);
    await page.getByText('No entries match these filters.').waitFor();
    await go(route);
    await page.getByText('Rating · Unrated', { exact: false }).waitFor();
    assert.equal(await page.getByText('Assessment and reviewed views').count(), 0);
  }

  const fetched = [];
  const samples = tracked.filter(({ path: file }) =>
    /\.(blend|stl)$/.test(file) || [
      historical,
      ...review.assessments.map((assessment) => assessment.export.path),
      'models/dental_specimens/uff_tomo1b/exports/r01/uff-tomo1b-display.glb',
      'reviews/swirendo_fdi31/2026-10-27-interface-locked/media/A_1_31_T2_SEG_na__layered.glb',
      'heart/exterior-presentation-r01/exports/static-opaque-exterior.glb',
    ].includes(file));
  for (const expected of samples) {
    const { file, route } = indexed.get(expected.path);
    await go(route);
    const href = assetUrl(file);
    await page.locator('a[href="' + href + '"]').first().waitFor();
    const response = await page.request.get(base + href);
    assert.equal(response.status(), 200, expected.path);
    const bytes = await response.body();
    assert.equal(bytes.length, expected.bytes, expected.path);
    assert.equal(digest(bytes), expected.sha256, expected.path);
    fetched.push(expected.path);
  }
  await go(metadataRoute);
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('link', { name: 'bronchial_tree.glb ↓', exact: true }).click(),
  ]);
  const downloaded = await readFile(await download.path());
  assert.equal(digest(downloaded), indexed.get(historical).file.sha256);
  assert.equal(download.suggestedFilename(), 'bronchial_tree.glb');
  const wrong = await page.request.get(base + '/assets/' + '0'.repeat(64) + '/wall_LA.stl');
  assert.equal(wrong.status(), 404);

  assert.deepEqual(errors, []);
  const receipt = {
    baseline,
    rows: rows.length,
    revisionAndParentRoutes: records.size,
    counts,
    tracked: tracked.map((expected) => ({ ...expected, route: indexed.get(expected.path)?.route })),
    fetched,
    assessments: review.assessments.map(({ route, export: file, axes, evaluator, date, rubric, views }) => ({
      route, export: file, evaluator, date, rubric, axes: axes.map((axis) => axis.score), views,
    })),
  };
  await writeFile(path.join(capture, 'discovery.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log('PASS Library discovery', counts, records.size + ' routes', fetched.length + ' exact download responses');
} finally {
  await browser.close();
}
