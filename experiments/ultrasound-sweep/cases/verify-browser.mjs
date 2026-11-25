// Run against an assembled study. Optional directory retains review captures.
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const root = new URL(process.argv[2] || 'http://127.0.0.1:8874/');
const captures = process.argv[3];
if (captures) await mkdir(captures, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true });
try {
  const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const visit = async (path) => {
    const response = await page.goto(new URL(path, root).href, { waitUntil: 'domcontentloaded' });
    assert.equal(response.status(), 200, path);
  };
  await visit('index.html');
  await page.getByRole('link', { name: 'Worked cases', exact: true }).click();
  assert.equal(await page.locator('.family').count(), 10);
  const cases = await page.locator('.family a').evaluateAll((links) => links.map((a) => a.href));
  assert.equal(new Set(cases).size, cases.length);
  if (captures) await page.screenshot({ path: join(captures, 'catalog.png') });
  const plates = new Map();
  for (const url of cases) {
    await visit(url);
    const title = await page.locator('h1').innerText();
    assert(await page.locator('section.report').innerText());
    const images = await page.locator('figure img').evaluateAll(async (images) => {
      await Promise.all(
        images.map(async (image) => {
          image.loading = 'eager';
          try { await image.decode(); } catch(error) {
            throw new Error('Cannot decode '+image.src+' on '+location.pathname+': '+error.message);
          }
        }),
      );
      return images.map((img) => [img.src, img.naturalWidth]);
    });
    for (const [src, width] of images) {
      assert(width > 0, src);
      plates.set(src, title);
    }
    const panels = page.locator('details.paired');
    if (await panels.count()) {
      await panels.first().locator('summary').click();
      assert(await panels.first().locator('img').first().isVisible(), title);
      await panels.first().locator('summary').click();
    }
    await page.evaluate(() => window.scrollTo(0, 0));
    for (const width of [1024, 1360]) {
      await page.setViewportSize({ width, height: 900 });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), title);
    }
    await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))));
    if (captures && /aaa-positive|echo-aortic-stenosis|pregnancy-mid-abnormal|thyroid-nodule/.test(url)) {
      await page.screenshot({ path: join(captures, new URL(url).pathname.split('/').pop() + '.png') });
    }
  }
  for (const [route, fragment] of [
    ['cardiac/?view=plax', 'echo'],
    ['carotid-survey/', 'carotid'],
  ]) {
    await visit(route);
    await page.getByRole('link', { name: 'Worked cases', exact: true }).click();
    assert.equal(new URL(page.url()).hash, '#' + fragment);
  }
  const staticPage = await browser.newPage({ javaScriptEnabled: false });
  await staticPage.goto(new URL('cases/index.html', root).href);
  await staticPage.locator('.family a').first().click();
  await staticPage.getByRole('link', { name: 'Impression', exact: true }).click();
  assert.equal(new URL(staticPage.url()).hash, '#impression');
  await staticPage.close();
  assert.deepEqual(errors, []);
  if (captures) {
    const entries = [...plates.keys()].filter((url) => url.endsWith('.svg'));
    const perSheet = 12;
    for (let i = 0; i < entries.length; i += perSheet) {
      await page.setViewportSize({ width: 1400, height: 1000 });
      await page.setContent(
        '<main style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font:15px system-ui"></main>',
      );
      await page.evaluate(
        async (urls) => {
          for (const url of urls) {
            const box = document.createElement('div'),
              img = new Image();
            img.src = url;
            img.style = 'width:100%;height:205px;object-fit:contain;background:#122127';
            box.append(img, document.createTextNode(url.split('/').pop()));
            document.querySelector('main').append(box);
            await img.decode();
          }
        },
        entries.slice(i, i + perSheet),
      );
      await page.screenshot({ path: join(captures, 'plates-' + String(i / perSheet).padStart(2, '0') + '.jpg') });
    }
  }
  console.log(
    `${cases.length} worked case routes, ${plates.size} distinct images, study entry points and laptop layouts passed.`,
  );
} finally {
  await browser.close();
}
