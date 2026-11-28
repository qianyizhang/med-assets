// Verify both exact thyroid meshes and use the player to reach the longitudinal views.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const [before, after, output, report] = process.argv.slice(2);
const receipt = JSON.parse(await readFile(report, 'utf8'));
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true, args: ['--enable-unsafe-swiftshader'] });
const identity = {};
await mkdir(output, { recursive: true });
try {
  for (const [version, base, mesh] of [['previous', before, receipt.previousSweep], ['candidate', after, receipt.export]]) {
    identity[version] = {};
    for (const side of ['right', 'left']) {
      const context = await browser.newContext({ viewport: { width: 1440, height: 1090 }, reducedMotion: 'reduce' });
      await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin
        ? route.continue() : route.abort());
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const sweep = 'thyroid-' + side;
      const root = '/sweeps/' + sweep + '/';
      const pins = Object.fromEntries(Object.entries(receipt.frozen.savedFrameInputs[side].files)
        .filter(([path]) => !path.endsWith('-00.webp')).map(([path, value]) => [root + path, value]));
      pins['/sweeps/thyroid-right/scenes/thyroid_gland.mesh'] = mesh;
      const pending = Object.keys(pins).map(path =>
        page.waitForResponse(response => response.ok() && new URL(response.url()).pathname === path));
      await page.goto(new URL('index.html?sweep=' + sweep + '&frame=12', base).href);
      await page.locator('#sceneHelp:not([hidden])').waitFor();
      await page.locator('#torsoOpacity').evaluate(input => {
        input.value = '15';
        input.dispatchEvent(new Event('input', { bubbles: true }));
      });
      const overlay = page.getByRole('button', { name: 'Anatomy overlay' });
      for (const frame of [12, 48]) {
        if (frame === 48) await page.getByRole('button', { name: 'Longitudinal reference keyframe', exact: true }).click();
        const shot = field => join(output, [version, side, frame, field].join('-') + '.png');
        await page.waitForFunction(frame => {
          const img = document.querySelector('#scan');
          return document.querySelector('#position').value === String(frame) &&
            img.src.endsWith('/scan-' + frame + '.webp') && img.complete && img.naturalWidth > 0 &&
            document.querySelector('#sceneStatus').hidden;
        }, frame);
        await page.locator('#sceneCanvas').screenshot({ path: shot('scene') });
        await page.locator('#scan').screenshot({ path: shot('scan') });
        await overlay.click();
        await page.waitForFunction(frame => {
          const img = document.querySelector('#scan');
          return img.src.endsWith('/section-' + frame + '.webp') && img.complete && img.naturalWidth > 0;
        }, frame);
        await page.locator('#scan').screenshot({ path: shot('overlay') });
        await overlay.click();
      }
      const served = {};
      for (const response of await Promise.all(pending)) {
        const bytes = await response.body();
        const path = new URL(response.url()).pathname;
        const actual = { bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') };
        assert.equal(actual.bytes, pins[path].bytes);
        assert.equal(actual.sha256, pins[path].sha256);
        served[path] = actual;
      }
      assert.deepEqual(errors, []);
      identity[version][side] = { served, frames: [12, 48], action: 'Longitudinal reference keyframe', torsoOpacityPercent: 15 };
      await context.close();
    }
  }
  await writeFile(join(output, 'live-identity.json'), JSON.stringify(identity, null, 2) + '\n');
} finally {
  await browser.close();
}
