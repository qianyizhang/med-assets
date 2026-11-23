import assert from 'node:assert/strict';
import { sha256 } from './assertions.mjs';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

export async function checkLessonPlates({ browser, base: dest, published, capture: captures }) {
  const decisions = (await Promise.all(['reopen-paired', 'target-risk'].map(async (batch) =>
    JSON.parse(await readFile(new URL('../../../../reviews/teaching-assessments/' + batch + '/decisions.json', import.meta.url)))
  ))).flat();
  const cases = [
    {
      slug: 'one-breath-mechanics',
      route: 'use-cases/one-breath',
      exportPath: 'body/breathing/Breathing_Assembly.blend',
      title: 'Compare expiration and peak inspiration',
      original: /Three panels show the diaphragm/,
      disclosure: 'Original bilingual storyboard',
    },
    {
      slug: 'lymphatic-node-transit',
      route: 'use-cases/systems/lymphatic?detail=lymphatic-node-transit',
      exportPath: 'models/lymph_node/exports/hra-tissue-layers-r01/lymph-node-tissue-layers.glb',
      title: 'Look inside the source lymph node',
      original: /Node transit · Isometric/,
    },
  ];
  const page = await browser.newPage();
  for (const item of cases) {
    const decision = decisions.find((row) => row.baseline === item.exportPath);
    const view = decision.teaching ?? decision.after;
    const address = dest + '/#/' + item.route;
    const region = page.locator('section').filter({ has: page.getByRole('heading', { name: item.title, exact: true }) });
    const img = region.getByRole('img');
    const original = page.getByRole('img', { name: item.original });
    const showOriginal = async () => {
      const disclosure = page.locator('details:not([open]) > summary').filter({ hasText: item.disclosure });
      if (item.disclosure && await disclosure.count()) await disclosure.click();
      await original.waitFor();
    };
    for (const width of [1280, 1024]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(address);
      await img.waitFor();
      await showOriginal();
      assert.ok(await img.evaluate((element, item) =>
        element.naturalWidth === item.width && element.naturalHeight === item.height &&
        element.getBoundingClientRect().width >= 700 && document.documentElement.scrollWidth <= innerWidth + 1,
      { width: view.width, height: view.height }));
      const url = await img.getAttribute('src');
      assert.equal(url, '/review-evidence/' + view.sha256 + '/' + encodeURIComponent(path.basename(view.path)));
      assert.equal(sha256(await (await page.request.get(dest + url)).body()), view.sha256);
      await region.getByRole('link', { name: 'Open full teaching image · ' + item.title }).focus();
      await region.screenshot({ path: path.join(captures, item.slug + '-' + width + '.png') });
    }

    const rejectEvidence = (route) => route.fulfill({ status: 503 });
    await page.route('**/review-evidence/**', rejectEvidence);
    const blocked = page.waitForResponse((response) => response.url().includes('/review-evidence/') && response.status() === 503);
    await page.reload();
    await blocked;
    await showOriginal();
    await page.waitForFunction((title) => ![...document.querySelectorAll('h2')].some((h) => h.textContent === title), item.title);
    await page.unroute('**/review-evidence/**', rejectEvidence);

    const hosted = 'https://gallery-hosted-check.invalid';
    const proxy = async (route) => {
      const local = new URL(route.request().url());
      const response = await page.request.get(published + local.pathname + local.search);
      await route.fulfill({ response });
    };
    const hostedReviewRequests = [];
    const audit = (request) => {
      if (request.url().startsWith(hosted + '/review-evidence/')) hostedReviewRequests.push(request.url());
    };
    await page.route(hosted + '/**', proxy);
    page.on('request', audit);
    await page.goto(hosted + '/#/' + item.route);
    await showOriginal();
    assert.equal(await page.getByRole('heading', { name: item.title, exact: true }).count(), 0);
    assert.deepEqual(hostedReviewRequests, []);
    page.off('request', audit);
    await page.unroute(hosted + '/**', proxy);
  }

  await page.goto(dest + '/#/use-cases/systems/lymphatic?detail=lymphatic-nodal-entry');
  await page.getByRole('img', { name: /Nodal entry · Isometric/ }).waitFor();
  assert.equal(await page.getByRole('heading', { name: 'Look inside the source lymph node' }).count(), 0);
  console.log('Two exact teaching plates, two display widths, and unavailable, hosted and neighboring lesson states verified.');
}
