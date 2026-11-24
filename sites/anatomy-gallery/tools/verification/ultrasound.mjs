import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import path from 'node:path';

const tour = '/#/use-cases/ultrasound-abdomen/gallbladder';
const assets = '/#/use-cases/ultrasound-assets';

export async function checkUltrasound({ browser, base, capture }) {
  const page = await browser.newPage({ viewport: { width: 1024, height: 768 } });
  const waitForRoute = (route) => page.waitForURL((url) => url.hash === route.slice(1), { waitUntil: 'domcontentloaded' });
  await page.goto(base + '/#/use-cases');
  await page.getByRole('link', { name: 'Ultrasound Anatomy →', exact: true }).click();
  await page.getByRole('heading', { name: 'Planned tours' }).waitFor();
  await page.getByRole('link', { name: 'Open Abdomen tour →' }).click();
  await waitForRoute(tour);
  const first = page.getByRole('button', { name: 'Select marker A' });
  const other = page.getByRole('button', { name: 'Select marker B' });
  await other.click();
  assert.match(await page.locator('.ga-ultrasound-answer').textContent(), /in the liver/);
  await first.focus();
  await first.press('Enter');
  assert.match(await page.locator('.ga-ultrasound-answer').textContent(), /^Correct/);
  assert.equal(await first.getAttribute('aria-pressed'), 'true');
  await page.screenshot({ path: path.join(capture, 'abdominal-ultrasound.png'), fullPage: true });

  const scan = await page.locator('.ga-ultrasound-image img').getAttribute('src');
  const scanRead = await page.request.get(new URL(scan, base).href);
  assert.equal(scanRead.status(), 200);
  assert.equal(scanRead.headers()['content-type'], 'image/webp');
  assert.equal(createHash('sha256').update(await scanRead.body()).digest('hex'), scan.split('/')[2]);
  await page.getByRole('button', { name: 'Matching anatomical section' }).click();
  await page.getByRole('img', { name: /gallbladder in green/ }).waitFor();
  await first.waitFor();
  assert.equal(await first.getAttribute('aria-pressed'), 'true');
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));

  await page.getByRole('link', { name: 'Inspect assets used at this stop →' }).click();
  await waitForRoute(assets + '/gallbladder?from=gallbladder');
  await page.getByRole('link', { name: 'Open related Library revision →' }).waitFor();
  await page.getByRole('link', { name: 'Liver and surrounding anatomy', exact: true }).click();
  await page.getByRole('img', { name: 'Anterior s1233 digestive assembly' }).waitFor();
  await page.locator('.ga-ultrasound-review img').evaluateAll((images) => Promise.all(images.map((image) => image.decode())));
  await page.screenshot({ path: path.join(capture, 'ultrasound-asset-review.png'), fullPage: true });
  await page.getByRole('link', { name: /Return to .*gallbladder/ }).click();
  await waitForRoute(tour);

  await page.route('**/assets/*/gallbladder-grayscale.webp', (route) => route.fulfill({ status: 503 }));
  await page.reload();
  await page.getByRole('status').filter({ hasText: 'Synthetic ultrasound unavailable' }).waitFor();
  assert.equal(await first.count(), 0);
  await page.getByRole('button', { name: 'Matching anatomical section' }).click();
  await first.waitFor();
  await page.getByRole('link', { name: 'Inspect assets used at this stop →' }).click();
  await page.getByRole('heading', { name: 'Ultrasound asset review' }).waitFor();

  const catalogue = await page.request.get(base + '/api/gallery/v1/studies');
  const { lessons } = await catalogue.json();
  assert.deepEqual(lessons.find(({ id }) => id === 'ultrasound-abdomen')?.stops, ['gallbladder']);
  await page.goto(base + assets + '/unknown');
  await page.getByRole('heading', { name: 'View unavailable' }).waitFor();
}
