// Exercise the actual playback controls at the viewport where the readout shifted.
import assert from 'node:assert/strict';

const url = process.argv[2] ?? 'http://127.0.0.1:8874';
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});

try {
  const page = await browser.newPage({ viewport: { width: 1021, height: 1197 } });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(url);
  await page.waitForFunction(() => !document.querySelector('#resetPose').disabled);
  await page.getByRole('button', { name: 'Short axis reference keyframe' }).click();
  await page.waitForFunction(() => document.querySelector('#ref')?.src.endsWith('acquired-short.webp'));
  const replay = page.getByRole('button', { name: 'Replay sweep' });
  await replay.waitFor();
  await page.waitForFunction(() => !document.querySelector('#play').disabled);

  const result = await page.evaluate(async () => {
    const elements = ['play', 'position', 'readout', 'angle', 'poseCanvas', 'planeCanvas', 'scan', 'ref'];
    const bounds = () => elements.flatMap((id) => {
      const { x, y, width, height } = document.getElementById(id).getBoundingClientRect();
      return [x, y, width, height];
    });
    const reference = bounds();
    let maxShift = 0;
    const frames = new Set();
    const deadline = performance.now() + 15000;
    document.getElementById('play').click();
    do {
      await new Promise(requestAnimationFrame);
      frames.add(Number(document.getElementById('position').value));
      maxShift = Math.max(maxShift, ...bounds().map((value, i) => Math.abs(value - reference[i])));
    } while (performance.now() < deadline && document.getElementById('play').textContent !== 'Replay sweep');
    return { maxShift, intermediate: [...frames].some((frame) => frame > 0 && frame < 48),
      end: document.getElementById('position').value };
  });
  assert.ok(result.intermediate, 'Replay should pass through intermediate poses.');
  assert.equal(result.end, '48');
  assert.ok(result.maxShift < 1, 'Playback shifted the layout by ' + result.maxShift + ' pixels.');

  await page.route('**/scan-12.webp', (route) => route.abort());
  await page.reload();
  await page.getByText('Scan unavailable for this frame.').waitFor();
  await page.getByRole('button', { name: 'Short axis reference keyframe' }).click();
  await page.waitForFunction(() => document.querySelector('#scan')?.src.endsWith('scan-48.webp'));
  assert.deepEqual(errors, []);
  console.log('Playback layout and single-frame recovery passed. Maximum shift: ' + result.maxShift + ' px.');
} finally {
  await browser.close();
}
