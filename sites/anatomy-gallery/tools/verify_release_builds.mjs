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
assert.ok(candidateURL && publishedURL && candidateProject && publishedProject && capture,
  'Pass CANDIDATE_URL PUBLISHED_URL CANDIDATE_PROJECT PUBLISHED_PROJECT and set MODEL_SURVEY_CAPTURE_DIR.');

async function checkCompiledCatalog(project, candidate) {
  const gallery = resolve(project, 'src/content/gallery');
  const { libraryRows } = await import(pathToFileURL(join(gallery, 'library-data.js')));
  const compiled = await import(pathToFileURL(join(gallery, 'selected-library.js')));
  const read = async (name) => JSON.parse(await readFile(join(gallery, name), 'utf8'));
  const expected = libraryRows(await read('../../data.json'), await read('teaching-inputs/teaching-assessments.json'),
    { localPreview: candidate });
  const data = (rows) => JSON.parse(JSON.stringify(rows,
    (_, value) => value instanceof Map ? Object.fromEntries(value) : value));
  assert.equal(compiled.candidate, candidate);
  assert.deepEqual(data(compiled.rows), data(expected), 'Compiled catalog lost a selected record or assessment');
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
  const bucket = new Proxy({}, { get() { assert.fail('A read-only rejection or value route must not read private storage'); } });
  const request = (path, method = 'GET') => worker.fetch(new Request(origin + path, { method }), { BUCKET: bucket });
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
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER, headless: true, chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
try {
  const releases = {};
  for (const [name, upstream, project] of [['candidate', candidateURL, candidateProject], ['published', publishedURL, publishedProject]]) {
    const libraryRows = await checkCompiledCatalog(project, name === 'candidate');
    const html = await readFile(join(project, 'dist/index.html'));
    const htmlSha256 = digest(html);
    await checkDownload(browser, upstream, name === 'candidate' ? firstFork : sourceFork,
      name === 'candidate' ? candidateFile : publishedFile, { bytes: html.length, sha256: htmlSha256 });
    const results = [];
    for (const origin of origins) {
      const observed = await checkRelease(browser, origin, upstream, name === 'candidate', releases.candidate?.stage);
      await checkWorker(project, origin, observed.studies, name === 'candidate');
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
