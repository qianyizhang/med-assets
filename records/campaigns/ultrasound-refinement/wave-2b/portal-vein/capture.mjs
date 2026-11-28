// Inspect the exact prior and r01 mesh in the same compact study player at frame 12.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const [before, after, output, report] = process.argv.slice(2);
const receipt = JSON.parse(await readFile(report, 'utf8'));
const sweep = 'sweeps/portal-vein';
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true, args: ['--enable-unsafe-swiftshader'] });
const identities = {};
await mkdir(output, { recursive: true });
try {
  for (const [index, base, mesh] of [[0, before, receipt.previousSweep], [1, after, receipt.export]]) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1090 }, reducedMotion: 'reduce' });
    await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin
      ? route.continue() : route.abort());
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const pins = Object.fromEntries(Object.entries(receipt.frozen.savedFrameInputs)
      .map(([path, identity]) => ['/' + sweep + '/' + path, identity]));
    pins['/' + receipt.frozen.previousCompactMesh] = mesh;
    const pending = Object.keys(pins).map(path =>
      page.waitForResponse(response => response.ok() && new URL(response.url()).pathname === path));
    await page.goto(new URL('index.html?sweep=portal-vein&frame=12', base).href);
    await page.locator('#sceneHelp:not([hidden])').waitFor();
    await page.waitForFunction(() => {
      const img = document.querySelector('#scan');
      return document.querySelector('#position').value === '12' && img.src.endsWith('/scan-12.webp')
        && img.complete && img.naturalWidth > 0 && document.querySelector('#sceneStatus').hidden;
    });
    await page.locator('#torsoOpacity').evaluate(input => {
      input.value = '15';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await page.locator('#sceneCanvas').screenshot({ path: join(output, 'player-' + index + '.png') });
    await page.locator('#scan').screenshot({ path: join(output, 'scan-' + index + '.png') });
    await page.getByRole('button', { name: 'Anatomy overlay' }).click();
    await page.waitForFunction(() => {
      const img = document.querySelector('#scan');
      return img.src.endsWith('/section-12.webp') && img.complete && img.naturalWidth > 0;
    });
    await page.locator('#scan').screenshot({ path: join(output, 'overlay-' + index + '.png') });
    await page.getByRole('button', { name: 'Axial', exact: true }).click();
    await page.locator('#sceneCanvas').screenshot({ path: join(output, 'axial-' + index + '.png') });
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
    identities[index ? 'candidate' : 'previous'] = { served, frame: 12, torsoOpacityPercent: 15, cameraPresets: ['oblique', 'axial'] };
    await context.close();
  }
  await writeFile(join(output, 'live-identity.json'), JSON.stringify(identities, null, 2) + '\n');
} finally {
  await browser.close();
}
