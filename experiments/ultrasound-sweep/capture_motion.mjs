// Capture the built standalone study with its own timeline, pose renderer and scans.
// Usage: node capture_motion.mjs http://127.0.0.1:PORT/index.html OUTPUT_DIR [SWEEP_ID ...]
// Requires Playwright, an installed Chromium browser and ffmpeg.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdir, mkdtemp, rename, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const [studyURL, outputDir, ...requestedIds] = process.argv.slice(2);
assert.ok(studyURL && outputDir, 'Usage: node capture_motion.mjs STUDY_URL OUTPUT_DIR [SWEEP_ID ...]');
execFileSync('ffmpeg', ['-version'], { stdio: 'ignore' });
const url = new URL(studyURL);
assert.ok(['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname), 'Serve the built study on loopback.');

const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});

const sampleCount = 25;
const posterIndex = Math.floor(sampleCount / 2);
const layout = `
  html, body { overflow: hidden !important; }
  #stage { position: fixed !important; inset: 0 !important; z-index: 2147483647 !important;
    display: grid !important; grid-template: 416px / 560px 400px !important; gap: 0 !important;
    background: #080a0a !important; margin: 0 !important; }
  #stage > .panel { display: none !important; }
  #stage > :is(#scenePanel, #scanPanel) { display: block !important; margin: 0 !important;
    border: 0 !important; border-radius: 0 !important; min-width: 0 !important; }
  #stage #scenePanel { grid-area: 1 / 1 !important; }
  #stage #scanPanel { grid-area: 1 / 2 !important; }
  #stage :is(#scenePanel, #scanPanel) > :not(.view), #sceneHelp { display: none !important; }
  #stage .view { width: 100% !important; height: 100% !important; aspect-ratio: auto !important;
    min-block-size: 0 !important; max-block-size: none !important; }
`;

function encodeVideo(pattern, output) {
  execFileSync('ffmpeg', ['-nostdin', '-loglevel', 'error', '-y', '-framerate', '5',
    '-i', pattern, '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-preset', 'veryfast', '-crf', '19', '-movflags', '+faststart', output + '.mp4']);
}

async function encodePoster(page, screenshot) {
  const result = await page.evaluate(async (jpeg) => {
    const image = new Image();
    image.src = 'data:image/jpeg;base64,' + jpeg;
    await image.decode();
    const canvas = document.createElement('canvas');
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    canvas.getContext('2d').drawImage(image, 0, 0);
    return canvas.toDataURL('image/webp', 0.9);
  }, screenshot.toString('base64'));
  const header = 'data:image/webp;base64,';
  assert.ok(result.startsWith(header), 'Chrome did not encode the WebP poster');
  return Buffer.from(result.slice(header.length), 'base64');
}

function selectScan(frame) {
  const position = document.querySelector('#position');
  position.valueAsNumber = frame;
  position.dispatchEvent(new Event('input', { bubbles: true }));
}

try {
  await mkdir(outputDir, { recursive: true });
  const page = await browser.newPage({ viewport: { width: 960, height: 416 }, deviceScaleFactor: 1 });
  await page.route('**/*', (route) => new URL(route.request().url()).origin === url.origin
    ? route.continue() : route.abort());
  await page.goto(url.href);
  const catalogue = await page.evaluate(() => abdomenTours.map(({ id }) => id));
  assert.ok(catalogue.length, 'The assembled sweep catalogue is empty.');
  const ids = requestedIds.length ? requestedIds : catalogue;
  for (const id of ids) {
    assert.ok(catalogue.includes(id) && /^[a-z0-9-]+$/.test(id), 'Unknown sweep ' + id);
  }
  for (const id of ids) {
    const scratch = await mkdtemp(join(outputDir, '.sweep-motion-'));
    const output = join(scratch, id);
    const framePath = (index) => join(scratch, String(index).padStart(2, '0') + '.jpg');
    try {
      url.searchParams.set('sweep', id);
      await page.goto(url.href);
      await page.waitForFunction(() => document.querySelector('#cameraPresets')?.disabled === false &&
        document.querySelector('#play')?.disabled === false && !document.querySelector('#sceneCanvas')?.hidden);
      assert.equal(await page.evaluate(() => selectedTour.id), id, 'Wrong route');
      const last = Number(await page.locator('#position').getAttribute('max'));
      assert.ok(Number.isInteger(last) && last > 0, 'Sweep has no timeline');
      assert.equal(await page.locator('#cameraPreset-oblique').getAttribute('aria-pressed'), 'true');
      await page.addStyleTag({ content: layout });
      const boxes = await page.locator('#sceneCanvas, #scanArea').evaluateAll((elements) =>
        elements.map((element) => {
          const { x, y, width, height } = element.getBoundingClientRect();
          return [x, y, width, height];
        }));
      assert.deepEqual(boxes, [[0, 0, 560, 416], [560, 0, 400, 416]], 'Capture panels did not fill the viewport');
      for (let i = 0; i < sampleCount; i++) {
        const frame = Math.round(i * last / (sampleCount - 1));
        const basename = 'scan-' + String(frame).padStart(2, '0') + '.webp';
        await page.evaluate(selectScan, frame);
        await page.waitForFunction(({ frame, basename }) => {
          const scan = document.querySelector('#scanArea img');
          const expected = new URL(selectedTour.assetRoot + 'media/' + basename, location.href).href;
          return state.shownFrame === frame && scan?.currentSrc === expected &&
            scan.complete && scan.naturalWidth > 0;
        }, { frame, basename });
        // The scene invalidates on frame changes and draws on the next animation frame.
        await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        const screenshot = await page.screenshot({ type: 'jpeg', quality: 94 });
        await writeFile(framePath(i), screenshot);
        if (i === posterIndex) await writeFile(output + '.webp', await encodePoster(page, screenshot));
      }
      encodeVideo(join(scratch, '%02d.jpg'), output);
      for (const ext of ['mp4', 'webp']) {
        await rename(output + '.' + ext, join(outputDir, id + '.' + ext));
      }
      console.log(id + ' · frames 0–' + last + ' · poster frame ' + Math.round(last / 2));
    } catch (cause) {
      throw new Error('Motion capture failed for ' + id + ' at ' + url.href, { cause });
    } finally {
      await rm(scratch, { recursive: true, force: true });
    }
  }
} finally {
  await browser.close();
}
