// Exercise the assembled AAA tours and their shared standalone sweep renderer.
// Usage: node verify-tours.mjs http://127.0.0.1:PORT/ [CAPTURE_DIR]
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const root = new URL(process.argv[2] || 'http://127.0.0.1:8874/');
const captures = process.argv[3];
if (captures) await mkdir(captures, { recursive: true });

const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
const expected = {
  'aaa-negative': [
    'proximal-aorta', 'mid-aorta', 'distal-aorta', 'iliac-bifurcation',
    'right-iliac-short', 'left-iliac-short',
  ],
  'aaa-positive': [
    'proximal-aorta', 'mid-aorta', 'sac-maximum', 'distal-aorta', 'iliac-bifurcation',
    'sac-long-axis', 'right-iliac-short', 'right-iliac-long', 'left-iliac-short', 'left-iliac-long',
  ],
  'aaa-indeterminate': [
    'proximal-aorta', 'mid-aorta', 'anterior-distal-attempt', 'lateral-distal-repeat',
  ],
};
const frameCount = 29;
const evidenceFrame = 14;
const errors = [];
const target = (path) => new URL(path, root);
const locationKey = (url) => [url.pathname, url.searchParams.get('chapter'), url.searchParams.get('frame'), url.hash];

async function setup() {
  const page = await browser.newPage({ viewport: { width: 1280, height: 940 } });
  page.setDefaultTimeout(12000);
  page.setDefaultNavigationTimeout(12000);
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('response', (response) => {
    if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) {
      errors.push(response.status() + ' ' + response.url());
    }
  });
  await page.addInitScript(() => {
    // Give the readback comparison a consistent 2D canvas backend.
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (type, options) {
      if (type === '2d') return original.call(this, type, { ...options, willReadFrequently: true });
      if (type === 'webgl2') return original.call(this, type, { ...options, preserveDrawingBuffer: true });
      return original.call(this, type, options);
    };
    const requests = new Map();
    let id = 0;
    let time = performance.now();
    window.requestAnimationFrame = (render) => {
      requests.set(++id, render);
      return id;
    };
    window.cancelAnimationFrame = (id) => requests.delete(id);
    window.stepSweep = () => {
      time = Math.max(performance.now(), time) + 201;
      const callbacks = [...requests.values()];
      requests.clear();
      for (const render of callbacks) render(time);
    };
  });
  return page;
}

async function embedded(page, id, chapter) {
  await page.waitForFunction(({ id, chapter }) => {
    const child = document.querySelector('#player iframe')?.contentWindow;
    if (!child?.location.href.startsWith(location.origin)) return false;
    const url = new URL(child.location.href);
    return url.pathname.endsWith('/tours/aaa/sweep.html') && url.searchParams.get('embed') === '1' &&
      url.searchParams.get('case') === id && url.searchParams.get('chapter') === chapter &&
      child.document.querySelector('#exam')?.hidden === false;
  }, { id, chapter }, { polling: 25 });
  const frame = await (await page.locator('#player iframe').elementHandle()).contentFrame();
  assert.ok(frame, 'Missing embedded sweep ' + id + '/' + chapter);
  await sceneReady(frame);
  return frame;
}

async function seek(surface, frame) {
  await surface.locator('#position').evaluate((slider, value) => {
    slider.valueAsNumber = value;
    slider.dispatchEvent(new Event('input', { bubbles: true }));
  }, frame);
  await expectFrame(surface, frame);
}

async function sceneReady(surface) {
  await surface.waitForFunction(() =>
    document.querySelector('#position')?.disabled === false &&
    document.querySelector('#cameraPresets')?.disabled === false &&
    document.querySelector('#sceneStatus')?.hidden === true, null, { polling: 25 });
}

async function setParitySize(surface) {
  // Match the WebGL viewport for pixel comparison independent of outer gutters.
  await surface.addStyleTag({ content: '#sceneCanvas { width: 440px !important; height: 300px !important; }' });
  await surface.waitForFunction(() => {
    window.stepSweep();
    const gl = document.querySelector('#sceneCanvas').getContext('webgl2');
    return gl?.drawingBufferWidth === 440 && gl.drawingBufferHeight === 300;
  }, null, { polling: 25 });
}

async function scenePixels(surface) {
  const result = await surface.locator('#sceneCanvas').evaluate((canvas) => {
    window.stepSweep();
    const gl = canvas.getContext('webgl2');
    if (!gl || gl.isContextLost()) throw Error('Expected a live WebGL 2 scene');
    const { drawingBufferWidth: width, drawingBufferHeight: height } = gl;
    if (width !== 440 || height !== 300) throw Error('Unexpected WebGL parity viewport: ' + width + ' × ' + height);
    const rgba = new Uint8Array(width * height * 4);
    gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, rgba);
    const samples = [];
    for (let y = 0; y < height; y += 3) {
      for (let x = 0; x < width; x += 3) {
        const offset = (y * width + x) * 4;
        samples.push(rgba[offset], rgba[offset + 1], rgba[offset + 2]);
      }
    }
    if (new Set(samples).size < 12) throw Error('WebGL scene did not draw 3D anatomy');
    return Uint8Array.from(samples).toBase64();
  });
  return Buffer.from(result, 'base64');
}

async function scanPixels(surface) {
  const result = await surface.locator('#scanCanvas').evaluate((canvas) => {
    const data = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
    return new Uint8Array(data.buffer, data.byteOffset, data.byteLength).toBase64();
  });
  return Buffer.from(result, 'base64');
}

function matches(left, right) {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let i = 0; i < left.length; i++) difference += Math.abs(left[i] - right[i]);
  return difference / left.length < 0.02;
}

async function expectFrame(surface, frame) {
  await surface.waitForFunction((value) =>
    document.querySelector('#frameNumber')?.textContent.trim() === value, frame + ' / ' + (frameCount - 1), { polling: 25 });
  assert.equal(await surface.locator('#position').inputValue(), String(frame));
}

async function evidence(surface) {
  await surface.locator('#evidence').dispatchEvent('click');
  await expectFrame(surface, evidenceFrame);
}

async function overlay(surface, enabled) {
  await surface.locator('#section').dispatchEvent('click');
  await surface.waitForFunction((value) =>
    document.querySelector('#section')?.getAttribute('aria-pressed') === value, String(enabled), { polling: 25 });
}

async function advanceFrames(surface, count) {
  return surface.evaluate(async (size) => {
    const position = document.querySelector('#position');
    const number = document.querySelector('#frameNumber');
    const shown = [position.valueAsNumber];
    for (let i = 1; i < size; i++) {
      window.stepSweep();
      if (number.textContent.trim() !== position.value + ' / ' + position.max) {
        throw Error('Playback timeline and displayed frame disagree');
      }
      shown.push(position.valueAsNumber);
      if (i % 10 === 0) await new Promise((resolve) => setTimeout(resolve, 0));
    }
    return shown;
  }, count);
}

async function checkStandaloneTransport(page) {
  const play = page.locator('#play');
  const position = page.locator('#position');
  const url = page.url();
  await play.dispatchEvent('click');
  assert.deepEqual(await advanceFrames(page, 2), [evidenceFrame, evidenceFrame + 1]);
  await play.dispatchEvent('click');
  assert.deepEqual(await advanceFrames(page, 2), [evidenceFrame + 1, evidenceFrame + 1], 'Pause moved the sweep');
  await play.dispatchEvent('click');
  const start = evidenceFrame + 1;
  assert.deepEqual(await advanceFrames(page, frameCount - start),
    Array.from({ length: frameCount - start }, (_, i) => start + i));
  assert.equal(await play.textContent(), 'Replay sweep');
  assert.equal(page.url(), url, 'Standalone playback crossed into another acquisition');
  await play.dispatchEvent('click');
  assert.equal(await position.inputValue(), '0');
  await play.dispatchEvent('click');
}

async function scanMatchesDeliveredFrame(surface, id, chapter, frame) {
  const difference = await surface.evaluate(async ({ id, chapter, frame }) => {
    const response = await fetch(id + '.scene.json');
    const { mediaRoot } = (await response.json())[chapter];
    const delivered = new Image();
    delivered.src = new URL('scan-' + String(frame).padStart(2, '0') + '.webp', new URL(mediaRoot, document.baseURI));
    await delivered.decode();
    const shown = document.querySelector('#scanCanvas');
    const source = document.createElement('canvas');
    source.width = shown.width;
    source.height = shown.height;
    const context = source.getContext('2d');
    context.drawImage(delivered, 0, 0, source.width, source.height);
    const reference = context.getImageData(0, 0, source.width, source.height).data;
    const rendered = shown.getContext('2d').getImageData(0, 0, shown.width, shown.height).data;
    let total = 0;
    for (let i = 0; i < rendered.length; i += 4) {
      total += Math.abs(rendered[i] - reference[i]);
    }
    // Only the small registered caliper strokes should differ from the delivered raster.
    return total / (rendered.length / 4);
  }, { id, chapter, frame });
  assert.ok(difference < 1.5, id + '/' + chapter + ' did not display scan frame ' + frame + ' (mean delta ' + difference + ')');
}

async function checkRenderedChapter(surface, id, chapter) {
  assert.equal(await surface.locator('#position').getAttribute('max'), String(frameCount - 1));
  await evidence(surface);
  const scan = await scanPixels(surface);
  const pose = await scenePixels(surface);
  await seek(surface, 0);
  assert.ok(!matches(await scanPixels(surface), scan), 'Static scan ' + id + '/' + chapter);
  await seek(surface, frameCount - 1);
  assert.ok(!matches(await scenePixels(surface), pose), 'Static probe ' + id + '/' + chapter);
  await evidence(surface);
  assert.ok(matches(await scanPixels(surface), scan), 'Scan did not return to evidence');
  assert.ok(matches(await scenePixels(surface), pose), 'Probe did not return to evidence');

  await surface.locator('#sceneCanvas').press('ArrowLeft');
  assert.ok(matches(await scanPixels(surface), scan), 'Orbit changed the scan');
  assert.ok(!matches(await scenePixels(surface), pose), 'Orbit did not move the WebGL scene');
  assert.equal(await surface.locator('#cameraPresets [aria-pressed="true"]').count(), 0);
  const preset = (id) => surface.locator('#cameraPreset-' + id);
  if (chapter === 'proximal-aorta') {
    const views = [pose];
    for (const name of ['axial', 'coronal', 'sagittal']) {
      await preset(name).dispatchEvent('click');
      assert.equal(await preset(name).getAttribute('aria-pressed'), 'true');
      const view = await scenePixels(surface);
      assert.ok(views.every((previous) => !matches(view, previous)), name + ' did not change the WebGL scene');
      views.push(view);
      assert.ok(matches(await scanPixels(surface), scan), name + ' changed the scan');
    }
  }
  await preset('oblique').dispatchEvent('click');
  assert.equal(await preset('oblique').getAttribute('aria-pressed'), 'true');
  assert.ok(matches(await scenePixels(surface), pose), 'Oblique preset did not restore the scene');

  if (chapter === 'proximal-aorta') {
    const opacity = surface.locator('#torsoOpacity');
    const initial = await opacity.inputValue();
    await opacity.fill('100');
    assert.equal(await opacity.getAttribute('aria-valuetext'), '100%');
    assert.ok(!matches(await scenePixels(surface), pose), 'Torso opacity did not change the WebGL scene');
    assert.ok(matches(await scanPixels(surface), scan), 'Torso opacity changed the scan');
    assert.equal(await surface.locator('#position').inputValue(), String(evidenceFrame));
    await opacity.fill(initial);
    assert.ok(matches(await scenePixels(surface), pose), 'Restoring torso opacity did not restore the scene');
  }

  if (id === 'aaa-positive' && chapter === 'sac-long-axis') {
    const color = surface.locator('#colorFlow');
    await color.click();
    assert.equal(await color.getAttribute('aria-pressed'), 'true');
    assert.ok(!matches(await scanPixels(surface), scan), 'Modeled color did not change the raster');
    assert.ok(matches(await scenePixels(surface), pose), 'Modeled color changed the probe pose');
    await color.click();
    assert.ok(matches(await scanPixels(surface), scan), 'Modeled color did not restore B-mode');
  }

  const limited = id === 'aaa-indeterminate' && ['anterior-distal-attempt', 'lateral-distal-repeat'].includes(chapter);
  if (limited) {
    assert.match(await surface.locator('#measurement').textContent(), /measurement withheld/i);
  }
  const positiveSac = id === 'aaa-positive' && chapter === 'sac-maximum';
  if (positiveSac) {
    assert.match(await surface.locator('#measurement').textContent(), /43 mm AP\s*×\s*46 mm transverse/);
  }
  await overlay(surface, true);
  if (positiveSac) {
    const legend = await surface.locator('#legend').textContent();
    assert.match(legend, /Aorta and proximal iliacs/i);
    assert.match(legend, /thrombus/i);
    assert.match(legend, /lumen/i);
    const marked = await scanPixels(surface);
    assert.ok(!matches(marked, scan), 'Tissue overlay left the sac raster unchanged');
    await seek(surface, evidenceFrame - 1);
    assert.doesNotMatch(await surface.locator('#measurement').textContent(), /43 mm AP\s*×\s*46 mm transverse/);
    await evidence(surface);
    assert.ok(matches(await scanPixels(surface), marked), 'Sac calipers did not return with evidence');
  }
  if (limited) {
    for (const frame of [0, evidenceFrame, frameCount - 1]) {
      await seek(surface, frame);
      assert.doesNotMatch(await surface.locator('#measurement').textContent(), /\d\s*mm/);
    }
    await evidence(surface);
  }
  await overlay(surface, false);
  assert.ok(matches(await scanPixels(surface), scan), 'B-mode was not restored');
  return { scan, pose };
}

async function checkUnavailableAssets() {
  const chapter = 'proximal-aorta';
  const url = target('tours/aaa/sweep.html?case=aaa-negative&chapter=' + chapter + '&frame=' + evidenceFrame);
  const failures = await browser.newPage({ viewport: { width: 1280, height: 940 } });
  failures.setDefaultTimeout(12000);
  try {
    const response = await failures.request.get(target('tours/aaa/aaa-negative.scene.json').href);
    assert.ok(response.ok(), 'No AAA scene manifest to test a missing torso');
    const { config, mediaRoot } = (await response.json())[chapter];
    const torso = config.meshPaths?.torso
      ? new URL(config.meshPaths.torso, url)
      : new URL('scenes/torso.mesh', new URL(config.assetRoot, url));
    const missingScan = new URL('scan-14.webp', new URL(mediaRoot, url));
    let torsoRequests = 0;
    await failures.route(torso.href, (route) => {
      torsoRequests++;
      return route.fulfill({ status: 404, body: 'Missing torso test fixture' });
    });
    await failures.goto(url.href);
    await checkDegradedScene(failures);
    assert.equal(torsoRequests, 1, 'Missing-torso test did not intercept the scene request');

    await failures.unroute(torso.href);
    await failures.route(missingScan.href, (route) => route.fulfill({ status: 404, body: 'Missing frame test fixture' }));
    await failures.goto(url.href);
    await sceneReady(failures);
    await expectFrame(failures, evidenceFrame);
    assert.equal(await failures.locator('#scanStatus').textContent(), 'Scan unavailable for this frame.');
    assert.ok(await failures.locator('#scanCanvas').isHidden(), 'Missing scan left stale pixels on screen');
    await seek(failures, evidenceFrame + 1);
    assert.ok(await failures.locator('#scanCanvas').isVisible(), 'Seek did not recover from a missing scan frame');
    assert.ok(await failures.locator('#sceneCanvas').isVisible(), 'Missing scan hid the available 3D scene');
  } finally {
    await failures.close();
  }

  const disabled = await browser.newPage({ viewport: { width: 1280, height: 940 } });
  disabled.setDefaultTimeout(12000);
  try {
    await disabled.addInitScript(() => {
      const original = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function (type, options) {
        return ['webgl', 'webgl2', 'experimental-webgl'].includes(type) ? null : original.call(this, type, options);
      };
    });
    await disabled.goto(url.href);
    await checkDegradedScene(disabled);
  } finally {
    await disabled.close();
  }
}

async function checkDegradedScene(page) {
  await page.waitForFunction(() => document.querySelector('#position')?.disabled === false, null, { polling: 25 });
  await expectFrame(page, evidenceFrame);
  assert.equal(await page.locator('#sceneStatus').textContent(), '3D probe and scan plane unavailable.');
  assert.ok(await page.locator('#sceneStatus').isVisible());
  assert.ok(await page.locator('#sceneCanvas').isHidden());
  assert.ok(await page.locator('#cameraPresets').evaluate((fieldset) => fieldset.disabled));
  assert.ok(await page.locator('#cameraPreset-oblique').isDisabled());
  assert.ok(await page.locator('#torsoOpacity').isDisabled());
  assert.ok(await page.locator('#scanCanvas').isVisible());
  const scan = await scanPixels(page);
  await seek(page, evidenceFrame + 1);
  assert.ok(await page.locator('#scanCanvas').isVisible());
  assert.ok(!matches(await scanPixels(page), scan), 'B-mode stopped updating after the scene failed');
}

try {
  const page = await setup();
  const standalone = await setup();
  await page.goto(target('index.html').href);
  await page.getByRole('link', { name: 'Tours', exact: true }).click({ force: true });
  assert.equal(new URL(page.url()).pathname, target('tours/index.html').pathname);
  const aaaIndex = target('tours/aaa/index.html');
  await page.locator('a[href="aaa/index.html"]').click();
  assert.equal(page.url(), aaaIndex.href);
  assert.deepEqual(
    (await page.locator('main a[href^="aaa-"][href$=".html"]').evaluateAll((links) =>
      [...new Set(links.map((link) => link.getAttribute('href').slice(0, -5)))])).sort(),
    Object.keys(expected).sort(),
  );

  await page.goto(target('index.html?sweep=aortic-screening').href);
  const normalTorso = await page.evaluate(() => {
    const normal = abdomenTours.find(({ id }) => id === 'aortic-screening');
    return new URL(normal.meshPaths?.torso ?? normal.assetRoot + 'scenes/torso.mesh', document.baseURI).href;
  });
  await page.getByRole('link', { name: 'AAA screening tours' }).click({ force: true });
  assert.equal(new URL(page.url()).pathname, aaaIndex.pathname);
  await page.goto(target('exams/index.html#aaa').href);
  await page.waitForURL(aaaIndex.href);

  const sharedProbe = ['lens', 'housing', 'relief'].map((part) => target('scenes/' + part + '.mesh').href);
  const probeResponses = new Set();
  page.on('response', (response) => {
    if (response.ok() && sharedProbe.includes(response.url())) probeResponses.add(response.url());
  });
  let totalFrames = 0;
  const representative = {
    'aaa-negative': 'distal-aorta',
    'aaa-positive': 'sac-maximum',
    'aaa-indeterminate': 'lateral-distal-repeat',
  };
  const caseFrames = [];
  for (const [id, chapters] of Object.entries(expected)) {
    const poseManifest = await page.request.get(target('tours/aaa/' + id + '.scene.json').href);
    assert.ok(poseManifest.ok());
    const configurations = await poseManifest.json();
    assert.deepEqual(Object.keys(configurations), chapters);
    for (const chapter of chapters) {
      const { config, frames } = configurations[chapter];
      assert.equal(new URL(config.meshPaths.torso, target('tours/aaa/sweep.html')).href, normalTorso);
      assert.equal(frames.length, frameCount);
      if (chapter === 'anterior-distal-attempt' || chapter === 'lateral-distal-repeat') {
        assert.ok(frames.every(({ limited, calipers }) => limited && calipers.length === 0),
          'The limited window must withhold distal calipers throughout the chapter');
      }
    }
    const tourPath = 'tours/aaa/' + id + '.html';
    const direct = (chapter, frame) => target(tourPath + '?chapter=' + chapter + '&frame=' + frame + '#exam');
    const old = target('exams/' + id + '.html?chapter=' + chapters[1] + '&frame=9#exam');
    await page.goto(old.href);
    await page.waitForURL((url) => url.pathname === direct(chapters[1], 9).pathname);
    assert.deepEqual(locationKey(new URL(page.url())), locationKey(direct(chapters[1], 9)), 'Legacy route lost the acquired frame');
    let child = await embedded(page, id, chapters[1]);
    assert.equal(await child.locator('#position').inputValue(), '9');
    assert.deepEqual(await page.locator('.chapters a[data-chapter]').evaluateAll((links) =>
      links.map((link) => link.dataset.chapter)), chapters);
    assert.equal(await page.locator('#reportEvidence a').count(), chapters.length);
    if (id === 'aaa-positive') {
      await page.getByRole('link', { name: 'Diagnostic continuation', exact: true }).click();
      child = await embedded(page, id, 'sac-long-axis');
      assert.equal(await child.locator('#position').inputValue(), '0');
    }

    await page.locator('.case-jumps').getByRole('link', { name: 'Worked case', exact: true }).click();
    assert.equal(new URL(page.url()).pathname, target('cases/' + id + '.html').pathname);
    const replays = page.locator('details.replays').first();
    await replays.locator('summary').click();
    const reportLink = replays.locator('a[href*="/tours/aaa/"][href*="chapter="]').first();
    const reportDestination = new URL(await reportLink.getAttribute('href'), page.url());
    assert.equal(reportDestination.pathname, target(tourPath).pathname);
    assert.ok(chapters.includes(reportDestination.searchParams.get('chapter')));
    assert.equal(reportDestination.searchParams.get('frame'), String(evidenceFrame));
    await reportLink.click();
    assert.deepEqual(locationKey(new URL(page.url())), locationKey(reportDestination));
    child = await embedded(page, id, reportDestination.searchParams.get('chapter'));
    assert.equal(await child.locator('#position').inputValue(), String(evidenceFrame));

    const retryPoses = [];
    for (const chapter of chapters) {
      await page.locator('.chapters a[data-chapter="' + chapter + '"]').click();
      child = await embedded(page, id, chapter);
      assert.equal(await child.locator('#position').inputValue(), '0');
      await setParitySize(child);
      const { scan, pose } = await checkRenderedChapter(child, id, chapter);
      if (chapter === representative[id]) {
        await scanMatchesDeliveredFrame(child, id, chapter, evidenceFrame);
        caseFrames.push({ scan, pose });
      }
      if (chapter === 'anterior-distal-attempt' || chapter === 'lateral-distal-repeat') retryPoses.push(pose);
      const solo = target('tours/aaa/sweep.html?case=' + id + '&chapter=' + chapter + '&frame=' + evidenceFrame);
      await page.waitForFunction((href) => document.querySelector('#openSweep')?.href === href, solo.href, { polling: 25 });
      await standalone.goto(await page.locator('#openSweep').getAttribute('href'));
      await sceneReady(standalone);
      await setParitySize(standalone);
      await expectFrame(standalone, evidenceFrame);
      assert.deepEqual(locationKey(new URL(await standalone.locator('#tourLink').getAttribute('href'))),
        locationKey(direct(chapter, evidenceFrame)));
      assert.ok(matches(await scanPixels(standalone), scan), 'Standalone scan differs from embedded ' + chapter);
      assert.ok(matches(await scenePixels(standalone), pose), 'Standalone pose differs from embedded ' + chapter);
      if (chapter === chapters[0]) await checkStandaloneTransport(standalone);

      const report = page.locator('#reportEvidence a').nth(chapters.indexOf(chapter));
      assert.deepEqual(locationKey(new URL(await report.getAttribute('href'), page.url())), locationKey(direct(chapter, evidenceFrame)));
      await report.click();
      child = await embedded(page, id, chapter);
      assert.equal(await child.locator('#position').inputValue(), String(evidenceFrame));
      if (captures && chapter === 'sac-long-axis') {
        await child.locator('#colorFlow').click();
        await child.locator('#sceneCanvas').evaluate(() => window.stepSweep());
        await child.locator('.sweepPanels').screenshot({ path: join(captures, id + '-modeled-color.png') });
      }
      if (captures && chapter === representative[id]) {
        await child.locator('#sceneCanvas').evaluate(() => window.stepSweep());
        const panels = child.locator('.sweepPanels');
        await panels.screenshot({ path: join(captures, id + '-shared-torso.png') });
        if (chapter === 'sac-maximum') {
          await overlay(child, true);
          await panels.screenshot({ path: join(captures, id + '-overlay.png') });
        }
      }
    }
    if (retryPoses.length) assert.ok(!matches(...retryPoses), 'Lateral retry repeated the anterior pose');

    await page.bringToFront();
    await page.locator('.chapters a[data-chapter="' + chapters[0] + '"]').click();
    await page.locator('#playTour').click();
    for (const chapter of chapters) {
      child = await embedded(page, id, chapter);
      await child.waitForFunction(() => document.querySelector('#play').textContent.trim() === 'Pause',
        null, { polling: 25 });
      const displayed = await advanceFrames(child, frameCount);
      assert.deepEqual(displayed, Array.from({ length: frameCount }, (_, i) => i), 'Tour skipped a frame in ' + chapter);
      totalFrames += displayed.length;
    }
    await page.getByRole('button', { name: 'Replay tour', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Replay tour', exact: true }).click();
    child = await embedded(page, id, chapters[0]);
    assert.equal(await child.locator('#position').inputValue(), '0');
    for (const width of [1024, 1280]) {
      await page.setViewportSize({ width, height: 940 });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Tour overflows at ' + width);
    }
    console.log(id + ' · ' + chapters.length + ' chapters · ' + chapters.length * frameCount + ' frames');
  }
  for (const [i, candidate] of caseFrames.entries()) {
    for (const previous of caseFrames.slice(0, i)) {
      assert.ok(!matches(candidate.pose, previous.pose), 'Different cases show the same WebGL acquisition');
      assert.ok(!matches(candidate.scan, previous.scan), 'Different cases show the same grayscale acquisition');
    }
  }
  assert.equal(caseFrames.length, 3);
  assert.deepEqual(probeResponses, new Set(sharedProbe), 'AAA scene did not load the shared curved probe');
  assert.deepEqual(errors, []);
  assert.equal(totalFrames, 580);
  await checkUnavailableAssets();
  console.log('AAA Tours navigation, legacy routes, evidence, retry, WebGL/scan parity, playback and degradation passed.');
} finally {
  await browser.close();
}
