import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import publication from '../snapshot-reference.json' with { type: 'json' };
import airway from '../../../lessons/one-breath/assets.json' with { type: 'json' };

const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const address = ({ sha256, name }) => `/assets/${sha256}/${name}`;
const candidateFile = { name: 'bronchial-first-fork.glb', bytes: 7401468,
  sha256: 'dec2886f07745086e56a31676b96005e0741d4475782fd879f47faf15769a42e' };
const publishedFile = { name: 'bronchial_central_fairing.glb', bytes: 10655808,
  sha256: 'c9e2eb595d677203b52aa870a9f0203f059a8f686a65056983fcc59ccd607587' };
const retiredElbow = { name: 'native-elbow.glb', bytes: 186792,
  sha256: '206915ffa0b6b625ca17e32f35b893e1d1a103f25bce59f41e02d657ab9e7fd5' };
const firstFork = 'library/bronchial_tree/first-fork-fairing-r15';
const sourceFork = 'library/bronchial_tree/authored-central-fairing-r13';
const origins = ['http://127.0.0.1:19852', 'https://gallery-release.invalid'];
const [candidateURL, publishedURL, candidateProject, publishedProject] = process.argv.slice(2);
const capture = process.env.MODEL_SURVEY_CAPTURE_DIR;
const workerOnly = process.argv.includes('--worker-only');
assert.ok(candidateURL && publishedURL && candidateProject && publishedProject && capture,
  'Pass CANDIDATE_URL PUBLISHED_URL CANDIDATE_PROJECT PUBLISHED_PROJECT and set MODEL_SURVEY_CAPTURE_DIR.');

async function checkCompiledCatalog(project, candidate) {
  const gallery = resolve(project, 'src/content/gallery');
  const { libraryRows } = await import(pathToFileURL(join(gallery, candidate ? 'library-compiler.js' : 'library-data.js')));
  const compiled = await import(pathToFileURL(join(gallery, 'selected-library.js')));
  const read = async (name) => JSON.parse(await readFile(join(gallery, name), 'utf8'));
  const rawReview = await read('teaching-inputs/teaching-assessments.json');
  const expected = candidate ? libraryRows(rawReview)
    : libraryRows(await read('../../data.json'), rawReview, { localPreview: false });
  const projection = rows => rows.map(({ id, path, history, recommended, lessons }) => ({
    id, path, recommended: recommended?.library, lessons: lessons?.map(record => record.library),
    history: history.map(({ library, exports, assessment, fileAssessments }) => ({
      library, exports: exports.map(file => [file.path, file.sha256, file.bytes, file.license]),
      assessment: assessment?.export.sha256, assessments: [...(fileAssessments ?? [])]
        .map(([path, row]) => [path, row.export.sha256, row.axes.map(axis => axis.score)]),
    })),
  }));
  assert.equal(compiled.candidate, candidate);
  assert.deepEqual(projection(compiled.rows), projection(expected), 'Compiled catalog lost a selected record or assessment');
  if (candidate) {
    const fork = compiled.rows.find(row => row.id === 'bronchial_tree').recommended.exports[0];
    assert.equal(fork.license, 'CC BY 4.0');
    assert.match(fork.credit, /Jakob Wasserthal/);
  }
  return expected.length;
}

function assertBytes(bytes, expected) {
  assert.equal(bytes.length, expected.bytes);
  assert.equal(digest(bytes), expected.sha256);
}

function browseAsset(page, name) {
  return page.evaluate(async (name) => {
    const response = await fetch(name);
    const bytes = await response.arrayBuffer();
    const hash = await crypto.subtle.digest('SHA-256', bytes);
    const sha256 = Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('');
    return { status: response.status, bytes: bytes.byteLength, sha256 };
  }, name);
}

async function checkWorker(project, origin, expected, candidate) {
  const { createDataAppWorker } = await import(pathToFileURL(resolve(project, 'src/data-app-worker.js')));
  const worker = createDataAppWorker({
    deploymentAssets: { html: publication.livePublication.html, snapshot: publication.livePublication.snapshot },
  });
  const deniedBucket = new Proxy({}, { get() { assert.fail('A rejection or value route must not access storage'); } });
  const request = (path, method = 'GET') => worker.fetch(new Request(origin + path, { method }), { BUCKET: deniedBucket });
  const study = await request('/api/gallery/v1/studies');
  assert.equal(study.status, 200);
  assert.deepEqual(await study.json(), expected);
  assert.equal((await request('/api/gallery/v1/studies', 'POST')).status, 405);
  const rubric = await request('/rubric');
  assert.equal(rubric.status, 302);
  assert.equal(rubric.headers.get('location'), origin + '/#/rubric');
  assert.equal((await request('/api/deployment-assets/html')).status, 403);
  assert.equal((await request('/api/deployment-assets/snapshot')).status, 403);
  assert.equal((await request(address(candidate ? publishedFile : retiredElbow), 'PUT')).status, 403);
  const release = JSON.parse(await readFile(resolve(project, 'src/content/assets/gallery-release.json')));
  assert.equal(release.selection, candidate ? 'candidate' : 'published');
  assert.equal((await request('/assets/index.json')).status, 200);
  if (!candidate) {
    assert.equal((await request(address(candidateFile))).status, 404);
    return;
  }

  const model = release.resources.find(file => file.url === address(candidateFile));
  const evidence = release.resources.find(file =>
    file.sha256 === '25f4c42dd5bd378dc9a2fbcd90758f65d17e4d006de9aedad8eaaa202d0d9281');
  const receipt = release.resources.find(file =>
    file.path === 'reviews/bronchial_tree/2026-11-21-distal-simplification-trial/geometry.json');
  assert.equal(release.resources.filter(file => file.localOnly).length, 16);
  assert.equal(release.resources.filter(file => file.immutable === false).length, 4);
  const index = await (await request('/assets/index.json')).json();
  assert.equal(index.assets.some(file => file.sha256 === model.sha256), false);
  const publicModel = index.assets.find(file => file.sha256 === publishedFile.sha256);
  for (const entry of [model, evidence, receipt, { ...publicModel, url: address(publicModel) }]) {
    const bytes = await readFile(new URL('../../../' + entry.path, import.meta.url));
    assertBytes(bytes, entry);
    const key = 'assets/sha256/' + entry.sha256;
    let object;
    const fake = {
      head: async actual => {
        assert.equal(actual, key);
        return object?.metadata;
      },
      get: async (actual, options) => {
        assert.equal(actual, key);
        const range = options?.range;
        return object && { body: range ? bytes.subarray(range.offset, range.offset + range.length) : bytes };
      },
      put: () => assert.fail('Read-only Worker probe attempted a write'),
    };
    function read(method = 'GET', headers) {
      return worker.fetch(new Request(origin + entry.url, { method, headers }), { BUCKET: fake });
    }
    assert.equal((await read()).status, 503);
    assert.equal((await read('HEAD')).status, 503);
    object = { metadata: { size: bytes.length, customMetadata: { sha256: 'wrong' } } };
    assert.equal((await read()).status, 503);
    object.metadata.customMetadata.sha256 = entry.sha256;
    const response = await read();
    assert.equal(response.status, 200);
    assert.equal(response.headers.get('content-type'), entry.mediaType);
    assertBytes(Buffer.from(await response.arrayBuffer()), entry);
    const head = await read('HEAD');
    assert.equal(head.status, 200);
    assert.equal(head.headers.get('content-length'), String(entry.bytes));
    assert.equal(await head.text(), '');
    const partial = await read('GET', { Range: 'bytes=0-15' });
    assert.equal(partial.status, 206);
    assert.equal(partial.headers.get('content-range'), 'bytes 0-15/' + entry.bytes);
    assert.deepEqual(Buffer.from(await partial.arrayBuffer()), bytes.subarray(0, 16));
    assert.equal((await read('GET', { Range: 'bytes=' + entry.bytes + '-' })).status, 416);
    assert.equal((await request(entry.url, 'PUT')).status, entry === model || entry === evidence || entry === receipt ? 405 : 403);
  }

  assert.equal((await request(address(retiredElbow))).status, 404);
  assert.equal((await request('/review-evidence/' + evidence.sha256 + '/unselected.webp')).status, 404);
  assert.equal((await request(receipt.url + '.other')).status, 404);
}

async function checkDownload(browser, origin, path, file, html) {
  const context = await browser.newContext();
  try {
    await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
    const page = await context.newPage();
    const response = await page.goto(origin + '/#/' + path);
    assert.equal(response?.status(), 200);
    assertBytes(await response.body(), html);
    const download = page.getByRole('link', { name: file.name + ' ↓', exact: true });
    const [saved] = await Promise.all([page.waitForEvent('download'), download.click()]);
    assert.equal(saved.suggestedFilename(), file.name);
    assertBytes(await readFile(await saved.path()), file);
  } finally {
    await context.close();
  }
}

async function checkRelease(browser, origin, upstream, candidate, candidateStage) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, serviceWorkers: 'block' });
  try {
    const page = await context.newPage();
    page.setDefaultTimeout(12000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await context.route('**/*', async route => {
      const request = route.request(), url = new URL(request.url());
      if (url.origin !== origin) return route.abort();
      const range = await request.headerValue('range');
      const response = await page.request.fetch(upstream + url.pathname + url.search, {
        method: request.method(), headers: range ? { range } : {}, maxRedirects: 0,
      });
      return route.fulfill({ response });
    });
    const visit = route => page.goto(origin + '/#/' + route);
    const heading = name => page.getByRole('heading', { name, exact: true, level: 1 });

    await visit('library');
    await heading('Asset Library').waitFor();
    const studies = await page.evaluate(async () => {
      const response = await fetch('/api/gallery/v1/studies');
      if (response.status !== 200) throw Error('Study API unavailable');
      return response.json();
    });
    assert.equal(studies.version, 1);
    assert.equal(studies.lessons.find(lesson => lesson.id === 'right-arm')?.stops.join(','), candidate ? 'elbow,shoulder' : undefined);

    await visit('library/bronchial_tree');
    const file = candidate ? candidateFile : publishedFile;
    if (!candidate) {
      const history = page.getByRole('navigation', { name: 'Revision history' });
      const old = history.locator('a[href="#/' + sourceFork + '"]');
      await old.waitFor();
      assert.equal(await history.locator('a[href="#/' + firstFork + '"]').count(), 0);
      await old.click();
    }
    const score = candidate ? '14/16' : '11/16';
    await page.getByText('Rating · ' + score, { exact: false }).waitFor();
    const download = page.getByRole('link', { name: file.name + ' ↓', exact: true });
    const href = await download.getAttribute('href');
    assert.equal(href, address(file));
    assert.deepEqual(await browseAsset(page, href), { status: 200, bytes: file.bytes, sha256: file.sha256 });
    await page.getByText('Assessment and reviewed views', { exact: true }).click();
    const assessment = page.locator('details[open]').filter({ hasText: 'Assessed export' }).first();
    await assessment.getByText(file.sha256, { exact: true }).waitFor();
    const witness = assessment.getByRole('link', { name: candidate ? /^Start at the trunk/ : /^Neutral r13 overview/ });
    const evidence = await witness.getAttribute('href');
    assert.equal(new URL(evidence, origin).origin, origin);
    const checked = await browseAsset(page, evidence);
    assert.equal(checked.status, 200);
    assert.equal(checked.sha256, candidate
      ? '25f4c42dd5bd378dc9a2fbcd90758f65d17e4d006de9aedad8eaaa202d0d9281'
      : 'c8d4264c82cf9f391d4a2a8110355dce8f4ffd359be3ea85dab7a2383254f6e1');

    const index = await page.evaluate(async () => (await fetch('/assets/index.json')).json());
    assert.equal(index.assets.some(asset => asset.sha256 === candidateFile.sha256), false);
    assert.equal(index.assets.some(asset => asset.sha256 === retiredElbow.sha256), !candidate);
    const elbow = await browseAsset(page, address(retiredElbow));
    assert.equal(elbow.status, candidate ? 404 : 200);
    if (!candidate) assert.deepEqual(elbow, { status: 200, bytes: retiredElbow.bytes, sha256: retiredElbow.sha256 });
    assert.equal((await browseAsset(page, address(candidateFile))).status, candidate ? 200 : 404);

    await visit(firstFork);
    if (candidate) await page.getByRole('link', { name: candidateFile.name + ' ↓', exact: true }).waitFor();
    else await heading('View unavailable').waitFor();
    await visit('use-cases/right-arm/elbow');
    if (candidate) {
      await heading('Right elbow').waitFor();
      await page.getByRole('navigation', { name: 'Right arm lessons' }).waitFor();
    } else await heading('View unavailable').waitFor();

    const cutaway = airway.assets.find(asset => asset.id === 'tracheaCutaway');
    if (candidate) {
      const open = airway.assets.find(asset => asset.id === 'tracheaOpen');
      for (const [asset, rating] of [[open, '12/16'], [cutaway, '14/16']]) {
        await visit('library/trachea/open-airway-r06?file=' + asset.sha256);
        await page.getByText('Rating · ' + rating, { exact: false }).waitFor();
        await page.getByText('Assessment and reviewed views', { exact: true }).click();
        await page.locator('details[open]').filter({ hasText: 'Assessed export' }).first()
          .getByText(asset.sha256, { exact: true }).waitFor();
      }
    }
    await visit('use-cases/one-breath');
    const scene = page.getByRole('region', { name: 'Interactive scene' });
    let stageLink = '#/stage';
    if (candidate) {
      await scene.getByRole('button', { name: 'Inspect in 3D' }).click();
      await scene.locator('canvas').waitFor();
      const stage = scene.getByRole('link', { name: /Open in 3D Stage/ });
      stageLink = await stage.getAttribute('href');
      assert.match(stageLink, /^#\/stage\/trachea-cutaway-v1/);
      await stage.click();
      await heading('3D Stage').waitFor();
      await scene.locator('canvas').waitFor();
      await page.getByRole('link', { name: 'Return to One Breath' }).waitFor();
    } else {
      await page.getByRole('heading', { level: 1, name: /One Breath/ }).waitFor();
      assert.equal(await scene.count(), 0);
      await page.goto(origin + '/' + candidateStage);
      await heading('View unavailable').waitFor();
      await visit('stage');
      await heading('3D Stage').waitFor();
      await scene.locator('canvas').waitFor();
    }
    const trachea = await browseAsset(page, address({ ...cutaway, name: cutaway.file }));
    assert.deepEqual(trachea, { status: 200, bytes: cutaway.bytes, sha256: cutaway.sha256 });

    await visit('archive/dental-image26/combined');
    const fallback = page.getByText('The retained video is unavailable. The narration and study record are still available.');
    const video = page.locator('video');
    if (candidate) {
      const playable = () => page.waitForFunction(() => document.querySelector('video')?.readyState >= 1);
      await playable();
      const videoPath = await video.getAttribute('src');
      await page.route(origin + videoPath, route => route.fulfill({ status: 503 }));
      await page.reload();
      await fallback.waitFor();
      await page.unroute(origin + videoPath);
      await page.getByRole('button', { name: 'Retry video' }).click();
      await playable();
    } else {
      await fallback.waitFor();
      assert.equal(await video.count(), 0);
    }
    await page.getByText('Narration transcript', { exact: true }).click();
    assert.ok(await page.locator('.ga-film-transcript p').count() > 0);

    await visit('library/swirendo-pilot/fdi31-prepared-r03');
    await page.getByText('Historical r03 GLB unavailable locally.', { exact: false }).waitFor();
    assert.equal(await page.getByRole('link', { name: /A_1_31_T2_SEG_na__layered.glb ↓/ }).count(), 0);
    assert.deepEqual(errors, []);
    return { studies, assets: index.assets.length, fork: candidate ? firstFork : sourceFork, score, evidence: checked,
      download: file, elbow, trachea, stage: stageLink, archive: candidate ? 'playback and retry' : 'transcript fallback' };
  } finally {
    await context.close();
  }
}

await mkdir(capture, { recursive: true });
const builds = [['candidate', candidateURL, candidateProject], ['published', publishedURL, publishedProject]];
for (const [name, , project] of builds) {
  const release = JSON.parse(await readFile(resolve(project, 'src/content/assets/gallery-release.json')));
  for (const origin of origins) await checkWorker(project, origin, release.studies, name === 'candidate');
  console.log('PASS generated Worker', name, origins.join(', '));
}
if (workerOnly) process.exit(0);
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER, headless: true, chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
try {
  const releases = {};
  for (const [name, upstream, project] of builds) {
    const libraryRows = await checkCompiledCatalog(project, name === 'candidate');
    const html = await readFile(join(project, 'dist/index.html'));
    const htmlSha256 = digest(html);
    await checkDownload(browser, upstream, name === 'candidate' ? firstFork : sourceFork,
      name === 'candidate' ? candidateFile : publishedFile, { bytes: html.length, sha256: htmlSha256 });
    const results = [];
    for (const origin of origins) {
      const observed = await checkRelease(browser, origin, upstream, name === 'candidate', releases.candidate?.stage);
      results.push(observed);
      console.log('PASS', name, origin, observed.score, observed.archive);
    }
    assert.deepEqual(results[0], results[1], name + ' release changed by browser origin');
    const { studies, ...observed } = results[0];
    releases[name] = { htmlSha256, libraryRows, studyApiSha256: digest(JSON.stringify(studies)), ...observed };
  }
  assert.notEqual(releases.candidate.download.sha256, releases.published.download.sha256);
  await writeFile(join(capture, 'release-browser.json'), JSON.stringify({
    browser: browser.version(), origins, publishedVersion: publication.livePublication.version, releases,
  }, null, 2) + '\n');
} finally {
  await browser.close();
}
