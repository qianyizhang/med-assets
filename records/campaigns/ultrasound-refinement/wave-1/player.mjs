import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const [url, output, stage] = process.argv.slice(2);
const base = new URL(url);
const receipt = JSON.parse(await readFile(resolve(output, 'reference.json')));
const staged = JSON.parse(await readFile(resolve(stage, 'sweeps/kidney-right/delivery.json')));
const captures = resolve(output, 'captures');
await mkdir(captures, { recursive: true });
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
const saved = (caseId, chapter) =>
  new URL(`tours/abdomen/${caseId}.html?chapter=${chapter}&frame=12#exam`, base);
const source = new URL('index.html?sweep=kidney-right', base);
const scan = (page, frame, mode = 'scan') => page.waitForFunction(
  ({ frame, mode }) => {
    const img = document.querySelector('#scan');
    return document.querySelector('#position').value === String(frame) &&
      img?.src.endsWith(`/${mode}-${String(frame).padStart(2, '0')}.webp`) &&
      img.complete && img.naturalWidth === 500;
  }, { frame, mode },
);
const survey = saved('abdomen-survey', 'abd-right-kidney');
async function mountPreview(casePage) {
  // The candidate exists only in this disposable browser session at this exact stop.
  const mounted = await casePage.evaluate(({ target, source }) => {
    const current = new URL(location.href);
    if (current.pathname !== target || current.searchParams.get('chapter') !== 'abd-right-kidney' ||
        current.searchParams.get('frame') !== '12') return false;
    const card = document.createElement('section');
    card.id = 'kidneyTrial';
    card.setAttribute('aria-label', 'Separate s1233 teaching exemplar');
    const title = document.createElement('h3');
    title.textContent = 'Separate s1233 teaching exemplar · held trial';
    const status = document.createElement('p');
    status.id = 'kidneyTrialStatus';
    status.textContent = 'Checking the source acquisition…';
    const iframe = document.createElement('iframe');
    iframe.name = 'kidney-trial';
    iframe.title = 's1233 right kidney at frame 12';
    iframe.style.cssText = 'width:100%;height:1000px;border:0;visibility:hidden';
    iframe.src = source;
    card.append(title, status, iframe);
    document.querySelector('#player').after(card);
    return true;
  }, { target: survey.pathname, source: source.href });
  if (!mounted) return null;
  await casePage.frameLocator('#kidneyTrial iframe').locator('#position').waitFor({ state: 'attached' });
  return casePage.frame({ name: 'kidney-trial' });
}

async function setPreviewState(casePage, available) {
  await casePage.evaluate((available) => {
    const frame = document.querySelector('#kidneyTrial iframe');
    frame.style.visibility = available ? 'visible' : 'hidden';
    frame.hidden = !available;
    document.querySelector('#player').hidden = available;
    document.querySelector('#kidneyTrialStatus').textContent = available
      ? 'Frame 12 of the s1233 sweep. This is a different subject from the worked case.'
      : 's1233 exemplar unavailable. Showing the procedural survey with its 107 mm schematic chord.';
  }, available);
}
const meshPath = 'sweeps/kidney-right/scenes/kidney_right.mesh';
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');

try {
  console.log('Chrome', browser.version());
  const context = await browser.newContext({ viewport: { width: 1440, height: 1090 }, reducedMotion: 'reduce' });
  await context.route('**/*', (route) => new URL(route.request().url()).origin === base.origin
    ? route.continue() : route.abort());
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const neighbors = [
    ['abdomen-survey', 'abd-right-kidney'],
    ['abdomen-limited-pancreas', 'abd-right-kidney'],
    ['abdomen-survey', 'abd-right-kidney-trans'],
    ['abdomen-renal-obstruction', 'renal-right-hydro'],
    ['abdomen-renal-obstruction', 'renal-right-postvoid'],
  ];
  for (const [caseId, chapter] of neighbors) {
    await page.goto(saved(caseId, chapter).href);
    const frame = page.frameLocator('#player iframe');
    await frame.locator('#pose[data-scene-ready]').waitFor();
    assert.equal(await frame.locator('#position').inputValue(), '12');
    const measure = await frame.locator('#value').innerText();
    console.log(caseId, chapter, 'frame 12', measure);
    if (chapter === 'abd-right-kidney') assert.match(measure, /107(?:\.0)? mm/);
    if (caseId === 'abdomen-survey' && chapter === 'abd-right-kidney') {
      await frame.locator('#pose').screenshot({ path: resolve(captures, 'baseline-contact.png') });
      await frame.locator('#scan').screenshot({ path: resolve(captures, 'baseline-scan.png') });
      await frame.locator('#overlay').click();
      await frame.locator('#scan').screenshot({ path: resolve(captures, 'baseline-overlay.png') });
    } else {
      assert.equal(await mountPreview(page), null);
    }
  }

  await page.goto(survey.href);
  await page.frameLocator('#player iframe').locator('#pose[data-scene-ready]').waitFor();
  const served = new Map();
  const files = ['scenes/kidney_right.mesh', 'sweep.js', 'media/scan-12.webp', 'media/section-12.webp'];
  const waiting = files.map((name) => page.waitForResponse((response) => response.ok() &&
    new URL(response.url()).pathname === '/sweeps/kidney-right/' + name));
  const candidate = await mountPreview(page);
  assert.ok(candidate);
  await candidate.waitForFunction(() => document.querySelector('#cameraPresets').disabled === false);
  assert.equal(hash(await (await waiting[0]).body()), staged[files[0]]);
  await setPreviewState(page, true);
  await candidate.getByRole('button', { name: 'Right renal long axis reference keyframe', exact: true }).click();
  await scan(candidate, 12);
  await candidate.locator('#sceneCanvas:not([hidden])').waitFor();
  await candidate.locator('#sceneCanvas').screenshot({ path: resolve(captures, 's1233-contact.png') });

  const registration = receipt.planeSections[1];
  const xy = registration.polesRasMm.map((point) => {
    const rel = point.map((value, index) => value - receipt.originRasMm[index]);
    const dot = (axis) => rel.reduce((sum, value, index) => sum + value * axis[index], 0);
    const pitch = 0.41; // ImagingGrid max(0.41, 133 / (350 - 21))
    return [250 + dot(receipt.widths.lateral) / pitch, 12 + dot(receipt.widths.beam) / pitch];
  });
  const roundTripMm = Math.hypot(xy[0][0] - xy[1][0], xy[0][1] - xy[1][1]) * 0.41;
  assert.ok(Math.abs(roundTripMm - registration.chordMm) < 1e-8);
  const annotate = () => candidate.evaluate(({ xy, chord }) => {
    // Show the independent label calipers in the player's existing raster overlay.
    const [[x1, y1], [x2, y2]] = xy;
    const marks = document.querySelector('#apMarks');
    marks.querySelector('#apChord').setAttribute('d', `M ${x1} ${y1} L ${x2} ${y2}`);
    marks.querySelector('#apEnds').setAttribute('d', xy.map(([x,y]) =>
      `M ${x - 5} ${y} h 10 M ${x} ${y - 5} v 10`).join(' '));
    const text = document.querySelector('#apReadout');
    text.textContent = `Half-label chord · ${chord.toFixed(1)} mm`;
    const position = document.querySelector('#position');
    const syncMarks = () => {
      marks.hidden = text.hidden = position.value !== '12';
    };
    position.addEventListener('input', syncMarks);
    syncMarks();
  }, { xy, chord: registration.chordMm });

  await annotate();
  await candidate.locator('#scanPanel').screenshot({ path: resolve(captures, 's1233-scan.png') });
  await candidate.getByRole('button', { name: 'Anatomy overlay' }).click();
  await scan(candidate, 12, 'section');
  await candidate.locator('#scanPanel').screenshot({ path: resolve(captures, 's1233-overlay.png') });
  for (const [key, frame] of [['ArrowLeft', 11], ['ArrowRight', 12], ['ArrowRight', 13]]) {
    await candidate.locator('#position').press(key);
    await scan(candidate, frame, 'section');
    assert.equal(await candidate.locator('#apMarks').isVisible(), frame === 12);
  }
  for (const [index, response] of (await Promise.all(waiting)).entries()) {
    const name = files[index], bytes = await response.body();
    assert.equal(hash(bytes), staged[name], name);
    served.set(new URL(response.url()).pathname, { sha256: hash(bytes), bytes: bytes.length });
  }
  assert.deepEqual(errors, []);
  console.log('Trial preview on the worked survey saved link, s1233 source frame 12: exact mesh, pose, B-mode and overlay; scrubbed 11→12→13; reprojection',
    roundTripMm.toFixed(6), 'mm');
  await writeFile(resolve(output, 'live-identity.json'), JSON.stringify({ paths: Object.fromEntries(served),
    endpointPixels: xy, chordMm: roundTripMm }, null, 2) + '\n');

  for (const [state, status, body] of [['missing', 404, ''], ['corrupt', 200, 'invalid']]) {
    const test = await context.newPage();
    const pattern = '**/' + meshPath;
    // Context-level interception still blocks external network requests.
    await test.route(pattern, (route) => route.fulfill({ status, body }));
    await test.goto(survey.href);
    const preview = await mountPreview(test);
    await scan(preview, 12);
    await preview.waitForFunction(() => {
      const status = document.querySelector('#sceneStatus');
      return !status.hidden && status.textContent.includes('unavailable');
    });
    await setPreviewState(test, false);
    await test.getByText(/s1233 exemplar unavailable. Showing the procedural survey/).waitFor();
    const baseline = test.frameLocator('#player iframe');
    await baseline.locator('#pose[data-scene-ready]').waitFor();
    assert.match(await baseline.locator('#value').innerText(), /107(?:\.0)? mm/);
    console.log(state, 'mesh surfaced as unavailable; s1233 B-mode and the independent schematic route still work');
    await test.close();
  }

  const fixture = await context.newPage();
  await fixture.route('**/development/mesh-review-test.html', (route) => route.fulfill({
    contentType: 'text/html', body: '<!doctype html><title>Chapter review fixture</title>',
  }));
  await fixture.goto(new URL('development/mesh-review-test.html', base).href);
  const bindingResults = await fixture.evaluate(async ({ path, meshSha256 }) => {
    const { chapterMeshReviewPrior } = await import('./assets-data.js');
    const record = { case: 'test', chapter: 'saved', part: 'kidney', meshSha256, chapterSha256: 'a'.repeat(64) };
    const binding = { path, meshSha256, chapterSha256: record.chapterSha256 };
    const rubric = 'b'.repeat(64);
    const manifest = { rubricHash: rubric, recipeHashes: { organs: 'before' }, chapterMeshBindings: {
      test: { saved: { kidney: binding, neighbor: { meshSha256: 'c'.repeat(64) } } },
    } };
    const stale = () => chapterMeshReviewPrior(manifest, record, rubric, new Map());
    const original = await stale();
    manifest.recipeHashes.organs = 'after';
    manifest.chapterMeshBindings.test.saved.neighbor.meshSha256 = 'd'.repeat(64);
    const sibling = await stale();
    binding.meshSha256 = '1'.repeat(64);
    const changedMesh = await stale();
    binding.meshSha256 = meshSha256;
    binding.chapterSha256 = '2'.repeat(64);
    const placement = await stale();
    binding.chapterSha256 = record.chapterSha256;
    binding.path = 'no-mesh-here.mesh';
    const missing = await stale();
    binding.path = 'sweeps/kidney-right/sweep.js';
    const corrupt = await stale();
    return { original, sibling, changedMesh, placement, missing, corrupt };
  }, { path: meshPath, meshSha256: receipt.candidateMeshSha256 });
  assert.deepEqual(bindingResults,
    { original: false, sibling: false, changedMesh: true, placement: true, missing: true, corrupt: true });
  console.log('Workbench review currency', JSON.stringify(bindingResults));
  await context.close();
} finally {
  await browser.close();
}
