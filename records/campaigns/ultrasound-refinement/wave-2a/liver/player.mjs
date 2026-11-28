import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, resolve, sep } from 'node:path';

const [baseline, candidate, output, candidateSha] = process.argv.slice(2);
const directories = { baseline: resolve(baseline), candidate: resolve(candidate) };
const frozen = JSON.parse(await readFile(new URL('./frozen.json', import.meta.url)));
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const hash = buffer => createHash('sha256').update(buffer).digest('hex');
const mime = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.json': 'application/json',
};
const server = createServer(async (request, response) => {
  try {
    const { pathname } = new URL(request.url, 'http://127.0.0.1');
    const [, name, ...parts] = decodeURIComponent(pathname).split('/');
    const root = directories[name];
    const path = resolve(root, ...parts);
    if (!path.startsWith(root + sep)) throw new Error('Invalid path');
    const body = await readFile(path);
    response.writeHead(200, { 'Content-Type': mime[extname(path)] || 'application/octet-stream' }).end(body);
  } catch {
    response.writeHead(404).end();
  }
});
await mkdir(output);
await new Promise((done, fail) => {
  server.once('error', fail);
  server.listen(0, '127.0.0.1', done);
});

let browser;
try {
  browser = await chromium.launch({
    executablePath: process.env.MODEL_SURVEY_BROWSER,
    chromiumSandbox: true,
    args: ['--enable-unsafe-swiftshader'],
  });
  const origin = 'http://127.0.0.1:' + server.address().port;
  const meshPath = 'sweeps/liver/scenes/liver.mesh';
  const referencePath = 'references/liver-12.webp';
  const scanPaths = ['scan', 'section'].flatMap(kind =>
    Array.from({ length: 49 }, (_, frame) =>
      `sweeps/liver/media/${kind}-${String(frame).padStart(2, '0')}.webp`));
  await Promise.all([...scanPaths, 'sweeps/liver/sweep.js', referencePath].map(async relative => {
    const a = await readFile(resolve(directories.baseline, relative));
    const b = await readFile(resolve(directories.candidate, relative));
    assert.equal(hash(a), hash(b), relative);
  }));
  const receipt = { browser: browser.version(), frozenScansAndOverlays: scanPaths.length, matchingPoseCount: 49 };
  for (const name of ['baseline', 'candidate']) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 1050 }, reducedMotion: 'reduce' });
    await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
    const page = await context.newPage();
    const errors = [];
    const meshes = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => {
      if (new URL(request.url()).pathname.endsWith('/' + meshPath)) meshes.push(request.url());
    });
    const respond = path => page.waitForResponse(response => response.ok()
      && new URL(response.url()).pathname.endsWith('/' + path));
    const responses = [meshPath, 'sweeps/liver/sweep.js', scanPaths[12], scanPaths[61], referencePath].map(respond);
    await page.goto(`${origin}/${name}/index.html?sweep=liver&frame=12`);
    await page.getByRole('button', { name: 'Oblique portal view reference keyframe', exact: true }).click();
    await page.waitForFunction(() => {
      const scan = document.querySelector('#scan');
      const canvas = document.querySelector('#sceneCanvas');
      return document.querySelector('#position').value === '12'
        && scan.src.endsWith('scan-12.webp') && scan.complete && scan.naturalWidth > 0
        && document.querySelector('#ref').naturalWidth > 0
        && !canvas.hidden && canvas.width > 0 && canvas.height > 0
        && document.querySelector('#sceneStatus').hidden;
    });
    await page.locator('#sceneCanvas').screenshot({ path: resolve(output, name + '-scene.png') });
    await page.locator('#scan').screenshot({ path: resolve(output, name + '-scan.png') });
    await page.getByRole('button', { name: 'Anatomy overlay' }).click();
    await page.waitForFunction(() => {
      const scan = document.querySelector('#scan');
      return scan.src.endsWith('section-12.webp') && scan.complete && scan.naturalWidth > 0;
    });
    await page.locator('#scan').screenshot({ path: resolve(output, name + '-overlay.png') });
    const served = {};
    for (const response of await Promise.all(responses)) {
      const payload = await response.body();
      const key = new URL(response.url()).pathname.split('/').slice(2).join('/');
      served[key] = { sha256: hash(payload), bytes: payload.length };
      const expected = frozen.baseline[key];
      if (key !== meshPath || name === 'baseline') assert.deepEqual(served[key], expected);
      else assert.equal(served[key].sha256, candidateSha);
    }
    assert.equal(meshes.length, 1);
    assert.deepEqual(errors, []);
    receipt[name] = { served, frame: 12, errors: [], meshRequests: meshes.length };
    await context.close();
  }
  assert.notEqual(
    hash(await readFile(resolve(output, 'baseline-scene.png'))),
    hash(await readFile(resolve(output, 'candidate-scene.png'))),
  );
  await writeFile(resolve(output, 'live-identity.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log('Both liver frame-12 scenes rendered. Exact mesh bytes and all 98 scan/overlay images verified.');
} finally {
  await browser?.close();
  server.close();
}
