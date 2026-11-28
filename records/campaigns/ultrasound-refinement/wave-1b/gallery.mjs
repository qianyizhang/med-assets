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
  await page.getByRole('heading', { name: 'Right kidney · Before → After' }).waitFor();
  await page.getByText(/23,156 → 4,800/).waitFor();
  await page.getByText(/416,840 → 86,432/).waitFor();
  const details = page.getByText('CT sections, live frame and proposed scores', { exact: true });
  await details.focus();
  await details.press('Enter');
  assert.equal(await details.locator('..').getAttribute('open'), '');
  const figures = page.locator('article figure img');
  assert.equal(await figures.count(), Object.keys(evidenceSha256).length);
  for (const [i, digest] of Object.values(evidenceSha256).entries()) {
    const figure = figures.nth(i);
    await figure.scrollIntoViewIfNeeded();
    const data = await figure.evaluate(async (image) => {
      await image.decode();
      const bytes = new Uint8Array(await fetch(image.src).then(response => response.arrayBuffer()));
      return bytes.toBase64();
    });
    assert.equal(hash(Buffer.from(data, 'base64')), digest);
  }
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
  await page.getByRole('link', { name: /Open exact AssetKit revision/ }).click();
  await page.getByRole('heading', { name: 's1233 right kidney · r01' }).waitFor();
  await page.getByText(pin.sha256, { exact: true }).waitFor();
  await page.reload();
  const download = page.getByRole('link', { name: 'Download the exact packed mesh' });
  const pending = page.waitForEvent('download');
  await download.click();
  assert.equal(hash(await readFile(await (await pending).path())), pin.sha256);
  assert.deepEqual(denied, []);
  console.log('Offline development route, three witness digests, keyboard disclosure, revision reload and exact mesh download passed.');
} finally {
  await browser.close();
}
