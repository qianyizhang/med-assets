const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
import { mkdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  headless: true,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
try {
  const ctx = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    permissions: ['clipboard-read', 'clipboard-write'],
  });
  const p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', (e) => {
    console.log('PAGE ERROR', String(e));
    errors.push(String(e));
  });
  const dest = process.env.MODEL_SURVEY_PREVIEW_URL || 'http://127.0.0.1:8858';
  const repo = fileURLToPath(new URL('../../../', import.meta.url));
  const dir = path.join(repo, '.artifacts/unified-gallery/');
  await mkdir(dir, { recursive: true });
  await p.goto(dest + '/?view=1');
  await p.getByRole('heading', { name: 'Asset Library', exact: true }).waitFor();
  await p.screenshot({ path: dir + 'library.png' });
  await p.getByRole('searchbox').fill('adrenal');
  await p.getByRole('button', { name: 'Search', exact: true }).click();
  await p.getByRole('heading', { name: 'Adrenal pair · BodyParts3D' }).waitFor();
  await p.getByRole('heading', { name: 'Adrenal glands · s1233' }).click();
  await p.goBack();
  assert.equal(await p.getByRole('searchbox').inputValue(), 'adrenal');
  await p.goForward();
  await p.getByRole('link', { name: 'Regional localization lesson' }).click();
  await p.getByRole('link', { name: 'Next · Right inferior rim' }).click();
  await p.getByRole('button', { name: 'Inspect in 3D' }).click();
  await p.waitForFunction(
    () => document.querySelector('.ga-canvas canvas') && !document.querySelector('.ga-canvas').hidden,
  );
  await p.getByRole('link', { name: 'Open in 3D Stage' }).click();
  await p.getByRole('button', { name: 'Share this view' }).waitFor();
  await p.getByLabel('Material', { exact: true }).selectOption('Neutral');
  await p.getByLabel('Key light').selectOption('0.75');
  await p.getByRole('button', { name: 'Share this view' }).click();
  const shared = await p.getByLabel('Persistent preset link').inputValue();
  assert.ok(shared.includes('adrenal-v1'));
  const fresh = await browser.newPage();
  await fresh.goto(shared);
  await fresh.waitForFunction(
    () => !!document.querySelector('.ga-canvas canvas') && !document.querySelector('.ga-canvas').hidden,
  );
  assert.equal(await fresh.getByLabel('Key light').inputValue(), '0.75');
  assert.equal(await fresh.getByLabel('Structure', { exact: true }).inputValue(), 'Right adrenal gland');
  await fresh.close();
  await p.goto(shared);
  await p.reload();
  assert.equal(await p.getByLabel('Material', { exact: true }).inputValue(), 'Neutral');
  assert.equal(await p.getByLabel('Structure', { exact: true }).inputValue(), 'Right adrenal gland');
  await p.getByRole('button', { name: 'Export WebP' }).waitFor();
  const download = p.waitForEvent('download');
  await p.getByRole('button', { name: 'Export WebP' }).click();
  const image = await download;
  await image.saveAs(dir + 'stage.webp');
  const bytes = await readFile(dir + 'stage.webp');
  assert.ok(bytes.subarray(8, 12).equals(Buffer.from('WEBP')));
  assert.ok(bytes.includes(Buffer.from('dc:source=')));
  assert.ok(bytes.includes(Buffer.from('Three.js r180')));
  await p.screenshot({ path: dir + 'stage.png' });
  await p.locator('summary').filter({ hasText: 'Tools' }).click();
  await p.getByRole('link', { name: 'Compare', exact: true }).click();
  await p.getByRole('heading', { name: 'The inferior adrenal fold' }).click();
  await p.getByRole('button', { name: 'Reveal revisions and scores' }).click();
  await p.getByText('Inspect the source sections').click();
  await p.getByRole('link', { name: 'Neutral material' }).click();
  await p.getByRole('button', { name: 'Share comparison' }).click();
  const comparison = await p.getByLabel('Comparison link').inputValue();
  assert.match(comparison, /finish=neutral&order=(ab|ba)/);
  await p.screenshot({ path: dir + 'compare.png' });
  await p.goto(dest + '/rubric');
  await p.getByRole('heading', { name: 'Review a teaching asset' }).waitFor();
  await p.goto(dest + '/?view=1#swirendo_fdi31');
  await p.locator('#swirendo_fdi31[open]').waitFor();
  await p.goto(dest + '/#/archive/planning');
  await p.getByRole('link', { name: 'Gaps', exact: true }).click();
  await p.getByRole('heading', { name: 'Clinical/anatomical review' }).waitFor();
  await p.goto(dest + '/#/stage/adrenal-v1?view=bad');
  await p.getByRole('heading', { name: 'View unavailable' }).waitFor();
  await p.goto(dest + '/#/stage');
  await p
    .getByLabel('Open local GLB')
    .setInputFiles(
      path.join(repo, 'assemblies/endocrine-locator/adrenal-study-r05/s1233-adrenals-regional.glb'),
    );
  await p.getByRole('button', { name: 'Export WebP' }).waitFor();
  await p.waitForFunction(
    () => !!document.querySelector('.ga-canvas canvas') && !document.querySelector('.ga-canvas').hidden,
  );
  assert.ok(await p.getByRole('button', { name: 'Share this view' }).isDisabled());
  await p.goto(dest + '/#/library');
  await p.setViewportSize({ width: 800, height: 700 });
  assert.ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  await p.route('**/assets/*/*.glb', (r) => r.fulfill({ status: 503, body: 'unavailable' }));
  await p.goto(dest + '/#/stage');
  await p.getByText('The pinned export is unavailable.').waitFor();
  assert.ok(await p.getByRole('button', { name: 'Retry 3D' }).isVisible());
  assert.deepEqual(errors, []);
  console.log(
    'PASS library, both adrenal lineages, two lesson stops, Stage, persistent link and WebP, blind review, sections, rubric, FDI31, archive, invalid preset and unavailable model.',
  );
} finally {
  await browser.close();
}
