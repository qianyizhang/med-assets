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
const consumers = (await Promise.all(['organs', 'vascular'].map(async family => {
  const path = new URL('../cases/' + family + '/consumer.json', import.meta.url);
  return JSON.parse(await readFile(path, 'utf8')).consumers;
}))).flat();
const key = entry => entry.case + '/' + entry.chapter;
const exemplars = new Map(consumers.filter(entry => entry.presentation !== 'companion').map(entry => [key(entry), entry]));
const companions = new Map(consumers.filter(entry => entry.presentation === 'companion').map(entry => [key(entry), entry]));
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
const browser = await chromium.launch({ executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true, args: ['--enable-unsafe-swiftshader'] });
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
      if (type === '2d') return context.call(this, type, { ...options, willReadFrequently: true });
      if (type === 'webgl2' || type === 'webgl') return context.call(this, type, { ...options, preserveDrawingBuffer: true });
      return context.call(this, type, options);
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

function meanChannelDifference(left, right) {
  if (left.length !== right.length) return Infinity;
  let sum = 0;
  for (let i = 0; i < left.length; i++) sum += Math.abs(left[i] - right[i]);
  return sum / left.length;
}

function equivalent(left, right) {
  return meanChannelDifference(left, right) < 0.02;
}

const preset = (surface, camera) => surface.locator('#posePresets [data-camera="' + camera + '"]');

async function poseViewport(surface, fixed) {
  const pose = surface.locator('canvas#pose[data-scene-ready]');
  await pose.waitFor();
  await pose.evaluate((canvas, sized) => {
    if (sized) {
      canvas.style.width = '440px';
      canvas.style.height = '300px';
    } else {
      canvas.style.removeProperty('width');
      canvas.style.removeProperty('height');
    }
  }, fixed);
  const deadline = Date.now() + 10000;
  do {
    const sized = await pose.evaluate((canvas) => {
      canvas.ownerDocument.defaultView.stepSweep();
      const gl = canvas.getContext('webgl2');
      return gl && gl.drawingBufferWidth === canvas.clientWidth && gl.drawingBufferHeight === canvas.clientHeight;
    });
    if (sized) return;
    await new Promise((resolve) => setTimeout(resolve, 25));
  } while (Date.now() < deadline);
  throw Error('WebGL did not draw at the current case viewport size');
}

async function posePixels(surface) {
  const result = await surface.locator('canvas#pose[data-scene-ready]').evaluate((canvas) => {
    canvas.ownerDocument.defaultView.stepSweep();
    const gl = canvas.getContext('webgl2');
    if (!gl || gl.isContextLost() || gl.drawingBufferWidth !== 440 || gl.drawingBufferHeight !== 300) {
      throw Error('Expected a live 440 × 300 case pose renderer');
    }
    const pixels = new Uint8Array(440 * 300 * 4);
    gl.readPixels(0, 0, 440, 300, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    const sample = [];
    for (let y = 0; y < 300; y += 3) {
      for (let x = 0; x < 440; x += 3) {
        const i = 4 * (y * 440 + x);
        sample.push(pixels[i], pixels[i + 1], pixels[i + 2]);
      }
    }
    if (new Set(sample).size < 12) throw Error('Pose renderer drew no visible anatomy');
    return Uint8Array.from(sample).toBase64();
  });
  return Buffer.from(result, 'base64');
}

async function checkPoseControls(surface, scan) {
  await poseViewport(surface, true);
  await preset(surface, 'oblique').click();
  const initial = await posePixels(surface);
  const views = [initial];
  for (const camera of ['axial', 'coronal', 'sagittal']) {
    await preset(surface, camera).click();
    assert.equal(await preset(surface, camera).getAttribute('aria-pressed'), 'true');
    const view = await posePixels(surface);
    assert.ok(views.every((previous) => !equivalent(view, previous)), camera + ' did not change the view');
    views.push(view);
  }
  await preset(surface, 'oblique').click();
  await surface.locator('#pose').press('ArrowLeft');
  assert.ok(!equivalent(await posePixels(surface), initial), 'Keyboard orbit did not change the pose');
  await preset(surface, 'oblique').click();
  assert.ok(equivalent(await posePixels(surface), initial), 'Oblique did not reset the orbit');

  const opacity = surface.locator('#skinOpacity');
  const original = await opacity.inputValue();
  await opacity.fill(original === '100' ? '0' : '100');
  assert.ok(!equivalent(await posePixels(surface), initial), 'Skin opacity did not change the pose image');
  await opacity.fill(original);
  assert.ok(equivalent(await posePixels(surface), initial), 'Restoring skin opacity did not restore the pose');
  assert.ok(equivalent(await pixels(surface, '#scan'), scan), 'Pose controls changed the scan');
  return initial;
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
  const overlay = child.locator('#overlay');
  await overlay.dispatchEvent('click');
  assert.equal(await overlay.getAttribute('aria-pressed'), 'true');
  assert.ok(await child.locator('#legend').isVisible(), 'Missing tissue legend ' + id);
  await overlay.dispatchEvent('click');
  assert.ok(equivalent(await pixels(child, '#scan'), scan), 'B-mode did not return after overlay ' + id);
  return scan;
}

async function playCaseToEnd(page, segments) {
  await waitForTourFrame(page, 0);
  await page.locator('#playTour').click();
  const shown = await page.evaluate(async (sections) => {
    const position = document.querySelector('#tourPosition');
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
              if (sender !== document.querySelector('#player iframe')?.contentWindow ||
                  origin !== location.origin || data?.type !== 'sweep-status' ||
                  data.status !== 'frame' || !Number.isInteger(data.request)) return;
              clearTimeout(timer);
              window.removeEventListener('message', accept);
              resolve();
            }
            window.addEventListener('message', accept);
            window.stepSweep();
          });
        }
        const source = document.querySelector('#player iframe').contentDocument.querySelector('#position');
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

async function checkAcquisitionSwitch(page, child, segments, chapters, caseId) {
  // This test exercises the state retained by the worked-case player across successive acquisitions.
  const [first, second] = chapters.filter(chapter => !exemplars.has(caseId + '/' + chapter.id));
  assert.ok(second, 'A case tour requires more than one acquisition');
  const select = page.locator('#tourSection');
  await select.selectOption(first.id);
  await waitForTourFrame(page, absoluteFrame(segments, first.id, 0));
  const viewer = page.locator('#player iframe');
  await viewer.evaluate((node) => { node.dataset.acquisitionWitness = 'retained'; });
  await child.locator('canvas#pose[data-scene-ready]').waitFor();
  const opacity = child.locator('#skinOpacity');
  const original = await opacity.inputValue();
  await opacity.fill('70');
  await preset(child, 'coronal').click();
  const overlay = child.locator('#overlay');
  await overlay.dispatchEvent('click');
  await select.selectOption(second.id);
  await waitForTourFrame(page, absoluteFrame(segments, second.id, 0));
  assert.equal(await viewer.getAttribute('data-acquisition-witness'), 'retained', 'Case player remounted across acquisitions');
  assert.equal(await child.locator('#view').textContent(), second.title);
  assert.equal(await opacity.inputValue(), '70', 'Skin opacity reset when changing acquisition');
  assert.equal(await preset(child, 'coronal').getAttribute('aria-pressed'), 'true', 'Preset reset when changing acquisition');
  assert.equal(await overlay.getAttribute('aria-pressed'), 'true', 'Overlay reset when changing acquisition');
  await overlay.dispatchEvent('click');
  await opacity.fill(original);
  await preset(child, 'oblique').click();
}

async function verifyStandalone(page, expectedURL, chapter, reference) {
  await page.goto(expectedURL.href);
  await page.locator('#exam').waitFor();
  const position = page.locator('#position');
  assert.equal(await position.getAttribute('max'), String(chapter.frames - 1));
  await expectSource(page, chapter.evidenceFrame);
  assert.ok(equivalent(await pixels(page, '#scan'), reference.scan), 'Standalone scan differs from embedded');
  await poseViewport(page, true);
  const poseDelta = meanChannelDifference(await posePixels(page), reference.pose);
  assert.ok(poseDelta < 0.02, 'Standalone pose differs from embedded (mean channel delta ' + poseDelta.toFixed(4) + ')');
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

async function checkPoseUnavailable(record, webglDisabled) {
  const page = await setup({ timed: false });
  try {
    if (webglDisabled) {
      await page.addInitScript(() => {
        const context = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function (type, options) {
          return ['webgl', 'webgl2', 'experimental-webgl'].includes(type) ? null : context.call(this, type, options);
        };
      });
    } else {
      await page.route('**/cases/echo/playable-scene.js', (route) =>
        route.fulfill({ status: 404, body: 'Missing pose adapter fixture' }));
    }
    await page.goto(url(tourPath(record)).href);
    await waitForTourFrame(page, 0);
    const player = page.frameLocator('#player iframe');
    const status = player.locator('#poseStatus');
    await status.waitFor();
    assert.match(await status.textContent(), /unavailable|could not/i);
    assert.equal(await player.locator('canvas#pose[data-scene-ready]').count(), 0);
    assert.ok(await player.locator('#scan').isVisible());
    const initial = await pixels(player, '#scan');
    await seekTour(page, 3);
    await expectSource(player, 3);
    assert.ok(!equivalent(await pixels(player, '#scan'), initial), 'Scan stalled when the pose was unavailable');
    assert.ok(await page.getByRole('heading', { name: 'Impression', exact: true }).isVisible());
  } finally {
    await page.close();
  }
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
      await checkAcquisitionSwitch(page, child, segments, chapters, id);
      const report = page.locator('#reportEvidence a');
      assert.equal(await report.count(), chapters.length);
      for (const [index, chapter] of chapters.entries()) {
        const selector = page.locator('#tourSection');
        await selector.selectOption(chapter.id);
        await waitForTourFrame(page, absoluteFrame(segments, chapter.id, 0));
        await expectSource(child, 0);
        assert.equal(await page.locator('.chapters [aria-current="step"]').getAttribute('data-chapter'), chapter.id);
        const exemplar = await page.locator('.chapter:not([hidden])').getAttribute('data-source-sweep');
        const consumer = exemplars.get(id + '/' + chapter.id);
        assert.equal(exemplar, consumer?.sweep ?? null, id + '/' + chapter.id);
        const companion = companions.get(id + '/' + chapter.id);
        const extra = page.locator('.chapter:not([hidden]) .ct-exemplar iframe');
        assert.equal(await extra.count(), companion ? 1 : 0);
        if (companion) {
          const target = new URL(await extra.getAttribute('data-src'), page.url());
          assert.equal(target.searchParams.get('sweep'), companion.sweep);
          assert.equal(target.searchParams.get('frame'), String(companion.frame));
        }
        if (consumer) {
          const saved = linkedFrame(tourPath(record), chapter.id, chapter.evidenceFrame, '#exam');
          const link = report.nth(index);
          assert.deepEqual(locationKey(new URL(await link.getAttribute('href'), page.url())), locationKey(saved));
          await link.click();
          await waitForTourFrame(page, absoluteFrame(segments, chapter.id, chapter.evidenceFrame));
          await expectSource(child, chapter.evidenceFrame);
          const suffix = String(chapter.evidenceFrame).padStart(2, '0') + '.webp';
          const scan = child.locator(`#scan[src$="/scan-${suffix}"]`);
          await scan.waitFor();
          if (consumer.savedChord) {
            assert.match(await child.locator('#apReadout').textContent(), /chord across the hilar recess.*mm/);
          } else {
            assert.equal(await child.locator('#apToggle').isVisible(), false);
          }
          await child.getByRole('button', { name: 'Anatomy overlay' }).click();
          await child.locator(`#scan[src$="/section-${suffix}"]`).waitFor();
          await child.getByRole('button', { name: 'Anatomy overlay' }).click();
          await scan.waitFor();
          const standalone = new URL(await page.locator('#openSweep').getAttribute('href'), base);
          assert.equal(standalone.pathname, new URL('index.html', base).pathname);
          assert.equal(standalone.searchParams.get('sweep'), consumer.sweep);
          assert.equal(standalone.searchParams.get('frame'), String(chapter.evidenceFrame));
          continue;
        }
        assert.equal(await child.locator('#view').textContent(), chapter.title);
        const scan = await checkChapter(page, child, segments, chapter);

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
        assert.ok(equivalent(await pixels(child, '#scan'), scan), 'Report link changed the saved scan ' + chapter.id);

        if (chapter === sample) {
          const sweep = linkedFrame(sweepPath(record), chapter.id, chapter.evidenceFrame);
          assert.deepEqual(locationKey(await page.locator('#openSweep').getAttribute('href')), locationKey(sweep));
          const pose = await checkPoseControls(child, scan);
          await verifyStandalone(standalone, sweep, chapter, { scan, pose });
          await poseViewport(child, false);
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
  await checkPoseUnavailable(echo, false);
  await checkPoseUnavailable(echo, true);
  console.log(ids.length + ' canonical exam tours, ' + chaptersChecked + ' sections, ' + framesChecked + ' committed frames passed.');
} finally {
  await browser.close();
}
