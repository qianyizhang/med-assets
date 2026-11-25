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
      return original.call(this, type, type === '2d' ? { ...options, willReadFrequently: true } : options);
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
  return frame;
}

async function seek(surface, frame) {
  await surface.locator('#position').evaluate((slider, value) => {
    slider.valueAsNumber = value;
    slider.dispatchEvent(new Event('input', { bubbles: true }));
  }, frame);
}

async function pixels(surface, selector) {
  const result = await surface.locator(selector).evaluate((canvas) => {
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

async function evidence(surface) {
  await surface.locator('#evidence').dispatchEvent('click');
  assert.equal(await surface.locator('#position').inputValue(), String(evidenceFrame));
}

async function advanceFrames(surface, count) {
  return surface.evaluate(async (size) => {
    const position = document.querySelector('#position');
    const shown = [position.valueAsNumber];
    for (let i = 1; i < size; i++) {
      window.stepSweep();
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

async function checkRenderedChapter(surface, id, chapter) {
  assert.equal(await surface.locator('#position').getAttribute('max'), String(frameCount - 1));
  await evidence(surface);
  const scan = await pixels(surface, '#scanCanvas');
  const pose = await pixels(surface, '#sceneCanvas');
  await seek(surface, 0);
  assert.ok(!matches(await pixels(surface, '#scanCanvas'), scan), 'Static scan ' + id + '/' + chapter);
  await seek(surface, frameCount - 1);
  assert.ok(!matches(await pixels(surface, '#sceneCanvas'), pose), 'Static probe ' + id + '/' + chapter);
  await evidence(surface);
  assert.ok(matches(await pixels(surface, '#scanCanvas'), scan), 'Scan did not return to evidence');
  assert.ok(matches(await pixels(surface, '#sceneCanvas'), pose), 'Probe did not return to evidence');

  await surface.locator('#orbit').fill('37');
  assert.ok(matches(await pixels(surface, '#scanCanvas'), scan), 'Orbit changed the scan');
  assert.ok(!matches(await pixels(surface, '#sceneCanvas'), pose), 'Orbit did not move the scene');
  await surface.locator('#resetView').dispatchEvent('click');
  assert.ok(matches(await pixels(surface, '#sceneCanvas'), pose), 'Reset did not restore the scene');

  const limited = id === 'aaa-indeterminate' && ['anterior-distal-attempt', 'lateral-distal-repeat'].includes(chapter);
  if (limited) {
    assert.match(await surface.locator('#measurement').textContent(), /measurement withheld/i);
  }
  const positiveSac = id === 'aaa-positive' && chapter === 'sac-maximum';
  if (positiveSac) {
    assert.match(await surface.locator('#measurement').textContent(), /43 mm AP\s*×\s*46 mm transverse/);
  }
  await surface.locator('#section').dispatchEvent('click');
  assert.equal(await surface.locator('#section').getAttribute('aria-pressed'), 'true');
  if (positiveSac) {
    const legend = await surface.locator('#legend').textContent();
    assert.match(legend, /wall/i);
    assert.match(legend, /thrombus/i);
    assert.match(legend, /lumen/i);
    const marked = await pixels(surface, '#scanCanvas');
    assert.ok(!matches(marked, scan), 'Tissue overlay left the sac raster unchanged');
    await seek(surface, evidenceFrame - 1);
    assert.doesNotMatch(await surface.locator('#measurement').textContent(), /43 mm AP\s*×\s*46 mm transverse/);
    await evidence(surface);
    assert.ok(matches(await pixels(surface, '#scanCanvas'), marked), 'Sac calipers did not return with evidence');
  }
  if (limited) {
    assert.doesNotMatch(await surface.locator('#legend').textContent(), /Aortic wall|Aortic lumen/);
    for (const frame of [0, evidenceFrame, frameCount - 1]) {
      await seek(surface, frame);
      assert.doesNotMatch(await surface.locator('#measurement').textContent(), /\d\s*mm/);
    }
    await evidence(surface);
  }
  await surface.locator('#section').dispatchEvent('click');
  assert.ok(matches(await pixels(surface, '#scanCanvas'), scan), 'B-mode was not restored');
  return { scan, pose };
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
  await page.getByRole('link', { name: 'AAA screening tours' }).click({ force: true });
  assert.equal(new URL(page.url()).pathname, aaaIndex.pathname);
  await page.goto(target('exams/index.html#aaa').href);
  await page.waitForURL(aaaIndex.href);

  let totalFrames = 0;
  for (const [id, chapters] of Object.entries(expected)) {
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
      const { scan, pose } = await checkRenderedChapter(child, id, chapter);
      if (chapter === 'anterior-distal-attempt' || chapter === 'lateral-distal-repeat') retryPoses.push(pose);
      const solo = target('tours/aaa/sweep.html?case=' + id + '&chapter=' + chapter + '&frame=' + evidenceFrame);
      await page.waitForFunction((href) => document.querySelector('#openSweep')?.href === href, solo.href, { polling: 25 });
      await standalone.goto(await page.locator('#openSweep').getAttribute('href'));
      await standalone.locator('#exam').waitFor({ state: 'visible' });
      assert.equal(await standalone.locator('#position').inputValue(), String(evidenceFrame));
      assert.deepEqual(locationKey(new URL(await standalone.locator('#tourLink').getAttribute('href'))),
        locationKey(direct(chapter, evidenceFrame)));
      assert.ok(matches(await pixels(standalone, '#scanCanvas'), scan), 'Standalone scan differs from embedded ' + chapter);
      assert.ok(matches(await pixels(standalone, '#sceneCanvas'), pose), 'Standalone pose differs from embedded ' + chapter);
      if (chapter === chapters[0]) await checkStandaloneTransport(standalone);

      const report = page.locator('#reportEvidence a').nth(chapters.indexOf(chapter));
      assert.deepEqual(locationKey(new URL(await report.getAttribute('href'), page.url())), locationKey(direct(chapter, evidenceFrame)));
      await report.click();
      child = await embedded(page, id, chapter);
      assert.equal(await child.locator('#position').inputValue(), String(evidenceFrame));
      if (captures && chapter === 'sac-maximum') {
        await child.locator('#section').dispatchEvent('click');
        await page.screenshot({ path: join(captures, id + '-overlay.png') });
        await child.locator('#section').dispatchEvent('click');
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
  assert.deepEqual(errors, []);
  assert.equal(totalFrames, 580);
  console.log('AAA Tours navigation, legacy routes, evidence, retry, standalone parity and playback passed.');
} finally {
  await browser.close();
}
