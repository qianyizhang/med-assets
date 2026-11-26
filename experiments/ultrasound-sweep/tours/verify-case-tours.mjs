// Verify canonical non-AAA exam tours, their per-section standalone players, and
// old exam addresses. Arguments: STUDY_URL [CAPTURE_DIR] [CASE_ID ...].
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import {
  absoluteFrame, checkTimeline, installTourClock, seekTour, waitForTourFrame,
} from '../composed-tour/verify-timeline.mjs';

const base = new URL(process.argv[2] || 'http://127.0.0.1:8874/');
const captures = process.argv[3];
if (captures) await mkdir(captures, { recursive: true });
const selected = process.argv.slice(4);
const expected = new Map();
for (const packageName of ['vascular', 'organs', 'pregnancy', 'echo']) {
  const folder = new URL('../cases/' + packageName + '/', import.meta.url);
  const records = JSON.parse(await readFile(new URL('cases.json', folder), 'utf8'));
  const { chapters } = await import(new URL('playable.js', folder));
  for (const record of records) {
    if (record.family === 'aaa') continue;
    expected.set(record.id, { record, chapters: chapters(record) });
  }
}
for (const id of selected) assert.ok(expected.has(id), 'Unknown non-AAA case ' + id);

const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true });
const url = (path) => new URL(path, base);
const tourPath = ({ family, id }) => 'tours/' + family + '/' + id + '.html';
const sweepPath = ({ family, id }) => 'tours/' + family + '/' + id + '-sweep.html';

function linkedFrame(path, chapter, frame, hash = '') {
  const destination = url(path);
  destination.searchParams.set('chapter', chapter);
  destination.searchParams.set('frame', frame);
  destination.hash = hash;
  return destination;
}

function locationKey(address) {
  const link = new URL(address);
  return [link.pathname, link.searchParams.get('chapter'), link.searchParams.get('frame'), link.hash];
}

async function setup({ timed = true } = {}) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 920 }, reducedMotion: 'reduce' });
  page.setDefaultTimeout(15000);
  page.setDefaultNavigationTimeout(15000);
  await page.addInitScript(() => {
    const context = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (type, options) {
      return context.call(this, type, type === '2d' ? { ...options, willReadFrequently: true } : options);
    };
  });
  if (timed) await installTourClock(page);
  return page;
}

async function pixels(surface, selector) {
  const data = await surface.locator(selector).evaluate((canvas) => {
    const { width, height } = canvas;
    const pixels = canvas.getContext('2d').getImageData(0, 0, width, height).data;
    return new Uint8Array(pixels.buffer).toBase64();
  });
  return Buffer.from(data, 'base64');
}

function equivalent(left, right) {
  if (left.length !== right.length) return false;
  let sum = 0;
  for (let i = 0; i < left.length; i++) sum += Math.abs(left[i] - right[i]);
  return sum / left.length < 0.02;
}

async function expectSource(surface, frame) {
  assert.equal(await surface.locator('#position').inputValue(), String(frame));
}

async function checkChapter(page, child, segments, chapter) {
  const { id, evidenceFrame, frames, measurement } = chapter;
  const at = (frame) => absoluteFrame(segments, id, frame);
  const go = async (frame) => {
    await seekTour(page, at(frame));
    await expectSource(child, frame);
  };

  const saved = page.locator('.chapter[id="' + id + '"] .evidence a');
  await saved.click();
  await waitForTourFrame(page, at(evidenceFrame));
  await expectSource(child, evidenceFrame);
  assert.equal(await saved.getAttribute('aria-current'), 'true');
  assert.equal((await child.locator('#value').textContent()).trim(), measurement || 'Saved evidence frame');

  const scan = await pixels(child, '#scan');
  const pose = await pixels(child, '#pose');
  let varying = false;
  for (const sample of new Set([(evidenceFrame + frames - 1) % frames, 0, frames - 1, Math.floor(frames / 3)])) {
    await go(sample);
    if (!equivalent(await pixels(child, '#scan'), scan)) {
      varying = true;
      break;
    }
  }
  assert.ok(varying, 'Static acquisition ' + id);
  await go(evidenceFrame);
  assert.ok(equivalent(await pixels(child, '#scan'), scan), 'Scan did not return to evidence ' + id);
  assert.ok(equivalent(await pixels(child, '#pose'), pose), 'Pose did not return to evidence ' + id);
  await child.locator('#orbit').fill('57');
  assert.ok(equivalent(await pixels(child, '#scan'), scan), 'Orbit changed the scan ' + id);
  assert.ok(!equivalent(await pixels(child, '#pose'), pose), 'Orbit did not change the pose ' + id);
  await child.locator('#resetView').dispatchEvent('click');
  assert.ok(equivalent(await pixels(child, '#pose'), pose), 'Reset did not restore the pose ' + id);
  const overlay = child.locator('#overlay');
  await overlay.dispatchEvent('click');
  assert.equal(await overlay.getAttribute('aria-pressed'), 'true');
  assert.ok(await child.locator('#legend').isVisible(), 'Missing tissue legend ' + id);
  await overlay.dispatchEvent('click');
  assert.ok(equivalent(await pixels(child, '#scan'), scan), 'B-mode did not return after overlay ' + id);
  return { scan, pose };
}

async function playCaseToEnd(page, segments) {
  await waitForTourFrame(page, 0);
  await page.locator('#playTour').click();
  const shown = await page.evaluate(async (sections) => {
    const viewer = document.querySelector('#player iframe');
    const position = document.querySelector('#tourPosition');
    const source = viewer.contentDocument.querySelector('#position');
    let absolute = 0;
    for (const [chapter, , first, last] of sections) {
      for (let frame = first; frame <= last; frame++) {
        if (absolute > 0) {
          await new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
              window.removeEventListener('message', accept);
              reject(Error('Case playback did not commit absolute frame ' + absolute));
            }, 15000);
            function accept({ data, source: sender, origin }) {
              if (sender !== viewer.contentWindow || origin !== location.origin || data?.type !== 'sweep-status' ||
                  data.status !== 'frame' || !Number.isInteger(data.request)) return;
              clearTimeout(timer);
              window.removeEventListener('message', accept);
              resolve();
            }
            window.addEventListener('message', accept);
            window.stepSweep();
          });
        }
        if (position.dataset.displayed !== String(absolute) || position.valueAsNumber !== absolute ||
            source.valueAsNumber !== frame ||
            document.querySelector('.chapters [aria-current="step"]').dataset.chapter !== chapter) {
          throw Error('Wrong acquisition frame at ' + chapter + '/' + frame + ' (absolute ' + absolute + ')');
        }
        absolute++;
      }
    }
    return absolute;
  }, segments);
  await page.getByRole('button', { name: 'Replay tour', exact: true }).waitFor();
  await page.locator('#playTour').click();
  await waitForTourFrame(page, 0);
  await page.getByRole('button', { name: 'Pause tour', exact: true }).click();
  await page.evaluate(() => window.stepSweep());
  await waitForTourFrame(page, 0);
  return shown;
}

async function checkAcquisitionSwitch(page, child, segments, chapters) {
  const [first, second] = chapters;
  assert.ok(second, 'A case tour requires more than one acquisition');
  const select = page.locator('#tourSection');
  await select.selectOption(first.id);
  await waitForTourFrame(page, absoluteFrame(segments, first.id, 0));
  const viewer = page.locator('#player iframe');
  await viewer.evaluate((node) => { node.dataset.acquisitionWitness = 'retained'; });
  await child.locator('#orbit').fill('35');
  const overlay = child.locator('#overlay');
  await overlay.dispatchEvent('click');
  await select.selectOption(second.id);
  await waitForTourFrame(page, absoluteFrame(segments, second.id, 0));
  assert.equal(await viewer.getAttribute('data-acquisition-witness'), 'retained', 'Case player remounted across acquisitions');
  assert.equal(await child.locator('#view').textContent(), second.title);
  assert.equal(await child.locator('#orbit').inputValue(), '35', 'Orbit reset when changing acquisition');
  assert.equal(await overlay.getAttribute('aria-pressed'), 'true', 'Overlay reset when changing acquisition');
  await overlay.dispatchEvent('click');
  await child.locator('#resetView').dispatchEvent('click');
}

async function verifyStandalone(page, expectedURL, chapter, reference) {
  await page.goto(expectedURL.href);
  await page.locator('#exam').waitFor();
  const position = page.locator('#position');
  assert.equal(await position.getAttribute('max'), String(chapter.frames - 1));
  await expectSource(page, chapter.evidenceFrame);
  assert.ok(equivalent(await pixels(page, '#scan'), reference.scan), 'Standalone scan differs from embedded');
  assert.ok(equivalent(await pixels(page, '#pose'), reference.pose), 'Standalone pose differs from embedded');
  await position.fill('0');
  await page.locator('#keyframe').click();
  await expectSource(page, chapter.evidenceFrame);

  const play = page.locator('#play');
  await position.fill('0');
  await play.click();
  await page.evaluate(() => window.stepSweep());
  await expectSource(page, 1);
  await play.click();
  await page.evaluate(() => window.stepSweep());
  await expectSource(page, 1);
  await play.click();
  await page.evaluate((frames) => {
    for (let i = 2; i < frames; i++) window.stepSweep();
  }, chapter.frames);
  await expectSource(page, chapter.frames - 1);
  assert.equal(new URL(page.url()).searchParams.get('chapter'), chapter.id, 'Standalone playback left its section');
}

try {
  const page = await setup();
  const standalone = await setup();
  const errors = [];
  for (const tab of [page, standalone]) {
    tab.on('pageerror', (error) => errors.push(error.message));
    tab.on('response', (response) => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) errors.push(response.status() + ' ' + response.url());
    });
    tab.on('console', (message) => {
      if (message.type() === 'error' && !message.location().url.endsWith('/favicon.ico')) errors.push(message.text());
    });
  }

  await page.goto(url('index.html').href);
  await page.getByRole('link', { name: 'Tours', exact: true }).click({ force: true });
  const listed = await page.locator('.family a').evaluateAll((links) =>
    links.map((link) => new URL(link.href).pathname));
  const canonical = [...expected.values()].map(({ record }) => url(tourPath(record)).pathname);
  assert.deepEqual(listed.filter((path) => canonical.includes(path)).sort(), canonical.sort());
  assert.ok(listed.every((path) => !path.includes('/exams/')), 'Tours still lists a legacy exam URL');

  let chaptersChecked = 0;
  let framesChecked = 0;
  const ids = selected.length ? selected : [...expected.keys()];
  for (const id of ids) {
    const { record, chapters } = expected.get(id);
    const segments = chapters.map(({ id, frames }) => [id, id, 0, frames - 1]);
    const sample = chapters.at(-1);
    const legacy = linkedFrame('exams/' + id + '.html', sample.id, sample.evidenceFrame, '#exam');
    const destination = linkedFrame(tourPath(record), sample.id, sample.evidenceFrame, '#exam');
    try {
      await page.goto(legacy.href);
      await page.waitForURL(destination.href);
      const child = page.frameLocator('#player iframe');
      await waitForTourFrame(page, absoluteFrame(segments, sample.id, sample.evidenceFrame));
      await expectSource(child, sample.evidenceFrame);
      const total = await checkTimeline(page, segments);
      await checkAcquisitionSwitch(page, child, segments, chapters);
      const report = page.locator('#reportEvidence a');
      assert.equal(await report.count(), chapters.length);
      for (const [index, chapter] of chapters.entries()) {
        const selector = page.locator('#tourSection');
        await selector.selectOption(chapter.id);
        await waitForTourFrame(page, absoluteFrame(segments, chapter.id, 0));
        await expectSource(child, 0);
        assert.equal(await page.locator('.chapters [aria-current="step"]').getAttribute('data-chapter'), chapter.id);
        assert.equal(await child.locator('#view').textContent(), chapter.title);
        const reference = await checkChapter(page, child, segments, chapter);

        const link = report.nth(index);
        const saved = linkedFrame(tourPath(record), chapter.id, chapter.evidenceFrame, '#exam');
        assert.deepEqual(locationKey(new URL(await link.getAttribute('href'), page.url())), locationKey(saved));
        assert.equal((await link.textContent()).trim(), chapter.title);
        assert.ok((await link.locator('..').textContent()).includes(chapter.measurement || chapter.observation),
          'Report lost the saved evidence for ' + chapter.id);
        await seekTour(page, absoluteFrame(segments, chapter.id, 0));
        await link.click();
        await waitForTourFrame(page, absoluteFrame(segments, chapter.id, chapter.evidenceFrame));
        assert.deepEqual(locationKey(page.url()), locationKey(saved));
        assert.ok(equivalent(await pixels(child, '#scan'), reference.scan), 'Report link changed the saved scan ' + chapter.id);

        if (chapter === sample) {
          const sweep = linkedFrame(sweepPath(record), chapter.id, chapter.evidenceFrame);
          assert.deepEqual(locationKey(await page.locator('#openSweep').getAttribute('href')), locationKey(sweep));
          await verifyStandalone(standalone, sweep, chapter, reference);
          if (captures) {
            await page.bringToFront();
            await page.locator('#tourPosition').evaluate((slider) => slider.scrollIntoView({ block: 'center' }));
            await page.screenshot({ path: join(captures, id + '.jpg') });
          }
        }
      }
      await page.bringToFront();
      await seekTour(page, 0);
      assert.equal(await playCaseToEnd(page, segments), total);
      chaptersChecked += chapters.length;
      framesChecked += total;
      console.log(id + ' · ' + chapters.length + ' sections · ' + total + ' frames');
    } catch (cause) {
      throw new Error('Failed ' + id + ' at ' + page.url(), { cause });
    }
  }

  assert.deepEqual(errors, []);
  const real = await setup({ timed: false });
  await real.setViewportSize({ width: 1024, height: 768 });
  const echo = expected.get('echo-normal').record;
  const echoChapters = expected.get(echo.id).chapters;
  const oldView = new URL('exams/' + echo.id + '.html', base);
  oldView.searchParams.set('view', echoChapters.at(-1).viewImage);
  oldView.hash = '#exam';
  const oldChapter = echoChapters.find(({ viewImage }) => viewImage === oldView.searchParams.get('view'));
  const echoSegments = echoChapters.map(({ id, frames }) => [id, id, 0, frames - 1]);
  await real.goto(oldView.href);
  await real.waitForURL((current) => current.pathname === url(tourPath(echo)).pathname);
  const echoPlayer = real.frameLocator('#player iframe');
  await waitForTourFrame(real, absoluteFrame(echoSegments, oldChapter.id, oldChapter.evidenceFrame));
  await expectSource(echoPlayer, oldChapter.evidenceFrame);
  oldView.searchParams.set('frame', '0');
  await real.goto(oldView.href);
  await real.waitForURL((current) => current.pathname === url(tourPath(echo)).pathname);
  await waitForTourFrame(real, absoluteFrame(echoSegments, oldChapter.id, 0));
  await expectSource(echoPlayer, 0);

  await seekTour(real, 0);
  await real.locator('#playTour').click();
  await real.waitForFunction(() => Number(document.querySelector('#tourPosition').dataset.displayed) > 1);
  await real.locator('#playTour').click();
  const paused = await real.locator('#tourPosition').inputValue();
  await new Promise((resolve) => setTimeout(resolve, 250));
  assert.equal(await real.locator('#tourPosition').inputValue(), paused);
  assert.ok(await real.evaluate(() => document.documentElement.scrollWidth === innerWidth));

  await real.route('**/cases/echo/playable.js', (route) => route.fulfill({ status: 404, body: 'Missing renderer fixture' }));
  await real.reload();
  await real.frameLocator('#player iframe').getByText(/could not be displayed/i).waitFor();
  assert.ok(await real.locator('#playTour').isDisabled());
  assert.ok(await real.getByRole('heading', { name: 'Impression', exact: true }).isVisible());
  await real.getByRole('link', { name: 'Worked views and acquired comparisons', exact: true }).click();
  await real.waitForSelector('section.report');
  console.log(ids.length + ' canonical exam tours, ' + chaptersChecked + ' sections, ' + framesChecked + ' committed frames passed.');
} finally {
  await browser.close();
}
