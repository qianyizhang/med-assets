// Capture the IVC sweep at its saved pose and check the actual mesh and scan responses.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const [before, after, output, report] = process.argv.slice(2);
const { frozen, exports } = JSON.parse(await readFile(report, 'utf8'));
const newest = 'sweeps/ivc/scenes/inferior_vena_cava.mesh';
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
await mkdir(output, { recursive: true });
const verified = {};
try {
  for (const [index, base, meshPath, mesh] of [
    [0, before, frozen.compactMeshPath, frozen.previousSweep],
    [1, after, newest, exports.abdominal.export],
  ]) {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1090 },
      reducedMotion: 'reduce',
    });
    await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin
      ? route.continue() : route.abort());
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const targets = Object.fromEntries(Object.entries(frozen.savedFrameInputs)
      .filter(([path]) => !path.includes('-48.'))
      .map(([path, digest]) => ['/sweeps/ivc/' + path, digest]));
    targets['/' + meshPath] = mesh;
    const awaited = Object.keys(targets).map(path =>
      page.waitForResponse(response => response.ok() && new URL(response.url()).pathname === path));
    await page.goto(new URL('index.html?sweep=ivc&frame=12', base).href);
    await page.locator('#sceneHelp:not([hidden])').waitFor();
    await page.waitForFunction(() => {
      const scan = document.querySelector('#scan');
      return document.querySelector('#position').value === '12' && scan.src.endsWith('/scan-12.webp')
        && scan.complete && scan.naturalWidth > 0 && document.querySelector('#sceneStatus').hidden;
    });
    await page.locator('#sceneCanvas').screenshot({ path: join(output, 'player-' + index + '.png') });
    await page.locator('#scan').screenshot({ path: join(output, 'scan-' + index + '.png') });
    await page.getByRole('button', { name: 'Anatomy overlay' }).click();
    await page.waitForFunction(() => {
      const scan = document.querySelector('#scan');
      return scan.src.endsWith('/section-12.webp') && scan.complete && scan.naturalWidth > 0;
    });
    await page.locator('#scan').screenshot({ path: join(output, 'overlay-' + index + '.png') });
    await page.getByRole('button', { name: 'Axial', exact: true }).click();
    await page.locator('#sceneCanvas').screenshot({ path: join(output, 'axial-' + index + '.png') });
    const served = {};
    for (const response of await Promise.all(awaited)) {
      const bytes = await response.body();
      const path = new URL(response.url()).pathname;
      const actual = { sha256: createHash('sha256').update(bytes).digest('hex'), bytes: bytes.length };
      assert.equal(actual.sha256, targets[path].sha256, path);
      assert.equal(actual.bytes, targets[path].bytes, path);
      served[path] = actual;
    }
    assert.deepEqual(errors, []);
    verified[index ? 'candidate' : 'previous'] = { frame: 12, served, cameraPresets: ['oblique', 'axial'] };
    await context.close();
  }
  await writeFile(join(output, 'live-identity.json'), JSON.stringify(verified, null, 2) + '\n');
} finally {
  await browser.close();
}
