import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

const [baseUrl, screenshot] = process.argv.slice(2);
const base = new URL(baseUrl);
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
const record = JSON.parse(await readFile(new URL('../../../../models/kidney_right_s1233/asset.record.json', import.meta.url)));
const pin = record.revisions[0].exports[0];
const packageUrl = new URL('../../../../experiments/ultrasound-sweep/development/asset-reviews/kidney-wave-1b/reviews.json',
  import.meta.url);
const { evidenceSha256 } = JSON.parse(await readFile(packageUrl));
const audit = JSON.parse(await readFile(new URL('../wave-0/audit-summary.json', import.meta.url)));
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true });

try {
  assert.equal(await fetch('http://127.0.0.1:8874/').then(() => true, () => false), false,
    'Study server must be stopped for Gallery verification');
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const denied = [];
  await context.route('**/*', route => {
    if (new URL(route.request().url()).origin === base.origin) return route.continue();
    denied.push(route.request().url());
    return route.abort();
  });
  const page = await context.newPage();
  await page.goto(new URL('/#/use-cases/ultrasound', base).href);
  await page.getByRole('link', { name: 'Development →' }).click();
  const campaign = page.getByLabel('Campaign progress');
  const metrics = Object.fromEntries(await campaign.locator('div').evaluateAll(rows => rows.map(
    row => [row.querySelector('dt').textContent, row.querySelector('dd').textContent],
  )));
  const [governed, total] = metrics['Governed chapters'].split(' / ').map(value => Number(value.replaceAll(',', '')));
  assert.equal(total, audit.summary.population.chapters);
  assert.ok(governed >= 1 && governed <= total);
  for (const label of ['Adopted', 'Reviewed']) assert.ok(Number(metrics[label].replaceAll(',', '')) >= 1);
  assert.match(metrics['Qualified'], /^[\d,]+$/);
  for (const label of ['Triangles saved', 'Bytes saved']) assert.match(metrics[label], /^-?[\d,]+$/);
  const card = page.getByRole('article', { name: 'Right kidney · Before → After' });
  await card.getByText(/23,156 → 4,800/).waitFor();
  await card.getByText(/416,840 → 86,432/).waitFor();
  const details = card.getByText('CT sections, exact mesh comparison and lead review', { exact: true });
  await details.focus();
  await details.press('Enter');
  assert.equal(await details.locator('..').getAttribute('open'), '');
  await card.getByText('Teaching readability · 3/4', { exact: true }).waitFor();
  await card.getByText(/Adopt for orientation at frame 12/).waitFor();
  const figures = card.locator('figure img');
  assert.equal(await figures.count(), Object.keys(evidenceSha256).length);
  const remaining = new Set(Object.values(evidenceSha256));
  for (let i = 0; i < await figures.count(); i++) {
    const figure = figures.nth(i);
    await figure.scrollIntoViewIfNeeded();
    const data = await figure.evaluate(async (image) => {
      await image.decode();
      const bytes = new Uint8Array(await fetch(image.src).then(response => response.arrayBuffer()));
      return bytes.toBase64();
    });
    assert.ok(remaining.delete(hash(Buffer.from(data, 'base64'))), 'Unexpected or repeated witness');
  }
  assert.equal(remaining.size, 0);
  for (const width of [1280, 960]) {
    await page.setViewportSize({ width, height: 900 });
    const overflow = await page.evaluate(() => ({
      width: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      offenders: [...document.querySelectorAll('article, figure, img, main')].flatMap(element =>
        element.getBoundingClientRect().right > innerWidth ? [element.tagName + '.' + element.className] : []),
    }));
    assert.ok(overflow.scrollWidth <= overflow.width, JSON.stringify(overflow));
  }
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.getByRole('heading', { name: 'Ultrasound Development' }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: screenshot, fullPage: true });
  await card.getByRole('link', { name: /Open exact AssetKit revision/ }).click();
  await page.getByRole('heading', { name: 's1233 right kidney · r01' }).waitFor();
  await page.getByText(pin.sha256, { exact: true }).waitFor();
  await page.reload();
  const download = page.getByRole('link', { name: 'Download the exact packed mesh' });
  const pending = page.waitForEvent('download');
  await download.click();
  const file = await pending;
  assert.equal(file.suggestedFilename(), 'kidney-right-r01.mesh');
  assert.equal(hash(await readFile(await file.path())), pin.sha256);
  await page.goto(new URL('/#/use-cases/ultrasound-development/unknown-revision', base).href);
  await page.getByRole('heading', { name: 'View unavailable' }).waitFor();
  assert.deepEqual(denied, []);
  console.log('Offline campaign progress, four review witness digests, keyboard disclosure, revision reload, exact mesh download and unknown route passed.');
} finally {
  await browser.close();
}
