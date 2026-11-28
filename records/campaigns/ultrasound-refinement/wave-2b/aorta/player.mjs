// Capture a compact sweep reader with only its reviewed surface swapped.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, resolve, sep } from 'node:path';
import { parseArgs } from 'node:util';

const { positionals, values } = parseArgs({
  allowPositionals: true,
  options: { brief: { type: 'string' }, export: { type: 'string' }, mesh: { type: 'string' }, frame: { type: 'string', multiple: true } },
});
const [baseline, replay, output] = positionals.map(path => resolve(path));
const frozen = JSON.parse(await readFile(values.brief || new URL('./frozen.json', import.meta.url)));
const frames = values.frame?.map(Number) || [12];
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const hash = bytes => ({ sha256: createHash('sha256').update(bytes).digest('hex'), bytes: bytes.length });
const same = (a, b) => {
  assert.equal(a.sha256, b.sha256);
  assert.equal(a.bytes, b.bytes);
};
const mime = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.webp': 'image/webp',
  '.svg': 'image/svg+xml', '.json': 'application/json',
};
const uses = Object.entries(frozen.exports)
  .filter(([name, value]) => 'sweep' in value && (!values.export || values.export === name));
assert(uses.length, 'No matching sweep export');
assert(!values.mesh || uses.length === 1, 'A custom mesh requires a single selected export');
const variants = new Map();
for (const [identifier, variant] of uses) {
  const mesh = await readFile(resolve(replay, values.mesh || identifier + '.mesh'));
  variants.set(variant.sweep, { path: variant.prior.compact.path, mesh });
}
const server = createServer(async (request, response) => {
  try {
    const { pathname } = new URL(request.url, 'http://localhost');
    const [, run, ...parts] = decodeURIComponent(pathname).split('/');
    const root = resolve(baseline, 'final');
    const path = resolve(root, ...parts);
    if (!path.startsWith(root + sep)) throw new Error('Invalid path');
    const candidate = variants.get(run);
    const body = parts.join('/') === candidate?.path ? candidate.mesh : await readFile(path);
    response.writeHead(200, { 'Content-Type': mime[extname(path)] || 'application/octet-stream' }).end(body);
  } catch {
    response.writeHead(404).end();
  }
});
await mkdir(output);
await new Promise((done, fail) => { server.once('error', fail); server.listen(0, '127.0.0.1', done); });

let browser;
try {
  browser = await chromium.launch({
    executablePath: process.env.MODEL_SURVEY_BROWSER,
    chromiumSandbox: true,
    args: ['--enable-unsafe-swiftshader'],
  });
  const origin = 'http://127.0.0.1:' + server.address().port;
  const receipt = { browser: browser.version(), runs: {} };
  for (const [, variant] of uses) {
    const { sweep } = variant;
    for (const side of ['previous', 'candidate']) {
      const run = side === 'candidate' ? sweep : 'original';
      const context = await browser.newContext({ viewport: { width: 1440, height: 1090 }, reducedMotion: 'reduce' });
      await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
      for (const frame of frames) {
        const stem = sweep + '-' + side + (frames.length === 1 && frame === 12 ? '' : '-' + frame);
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', e => errors.push(e.message));
        const { scan, section } = variant.savedFrames[String(frame)];
        const mesh = variant.prior.compact;
        const pins = {
          [scan.path]: scan,
          [section.path]: section,
          [variant.savedPoseScript.path]: variant.savedPoseScript,
          [mesh.path]: side === 'previous' ? mesh : hash(variants.get(sweep).mesh),
        };
        const responses = Object.keys(pins).map(path =>
          page.waitForResponse(r => r.ok() && new URL(r.url()).pathname === '/' + run + '/' + path));
        await page.goto(origin + '/' + run + '/index.html?sweep=' + sweep + '&frame=' + frame);
        await page.locator('#sceneHelp:not([hidden])').waitFor();
        await page.waitForFunction(({ frame, path }) => {
          const img = document.querySelector('#scan');
          return document.querySelector('#position').value === String(frame)
            && img.src.endsWith(path) && img.complete && img.naturalWidth > 0
            && document.querySelector('#sceneStatus').hidden;
        }, { frame, path: scan.path });
        await page.locator('#sceneCanvas').screenshot({ path: resolve(output, stem + '-scene.png') });
        await page.locator('#scan').screenshot({ path: resolve(output, stem + '-scan.png') });
        await page.getByRole('button', { name: 'Anatomy overlay' }).click();
        await page.waitForFunction((path) => {
          const img = document.querySelector('#scan');
          return img.src.endsWith(path) && img.complete && img.naturalWidth > 0;
        }, section.path);
        await page.locator('#scan').screenshot({ path: resolve(output, stem + '-overlay.png') });
        await page.getByRole('button', { name: 'Axial', exact: true }).click();
        await page.locator('#sceneCanvas').screenshot({ path: resolve(output, stem + '-axial.png') });
        const served = {};
        for (const response of await Promise.all(responses)) {
          const path = new URL(response.url()).pathname.split('/').slice(2).join('/');
          served[path] = hash(await response.body());
          same(served[path], pins[path]);
        }
        assert.deepEqual(errors, []);
        receipt.runs[stem] = { served, frame, cameraPresets: ['oblique', 'axial'] };
        await page.close();
      }
      await context.close();
    }
  }
  await writeFile(resolve(output, 'live-identity.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log('Sweep readers rendered the requested frozen frames with exact prior and candidate meshes.');
} finally {
  await browser?.close();
  server.close();
}
