import assert from 'node:assert/strict';
import { sha256 as hash } from './assertions.mjs';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

export async function checkRefinementPlates({ browser, base, capture: directory }) {
  const batches = new URL('../../../../reviews/teaching-assessments/', import.meta.url);
  const rows = [];
  for (const name of ['risk', 'form', 'economy']) {
    const batch = JSON.parse(await readFile(new URL('refinement-' + name + '/accepted.json', batches)));
    rows.push(...batch.outcomes);
  }
  assert.equal(new Set(rows.map((row) => row.sha256)).size, 46);
  const page = await browser.newPage();
  await page.goto(base + '/#/compare');
  await page.getByRole('link', { name: 'Review the below-target teaching assets →' }).click();
  const select = page.getByRole('combobox', { name: 'Asset', exact: true });
  await select.waitFor();
  assert.equal(await select.locator('option').count(), rows.length);
  const toggle = page.getByRole('checkbox', { name: 'Compare side by side' });
  await toggle.check();
  let downloads = 0;
  const testedMissing = new Set();
  for (const row of rows) {
    if (await select.inputValue() === row.sha256 && !page.url().endsWith(row.sha256)) {
      await page.goto(base + '/#/compare/teaching-refinements?asset=' + row.sha256);
    } else await select.selectOption(row.sha256);
    await page.waitForURL((url) => url.hash.endsWith('asset=' + row.sha256));
    await page.getByRole('heading', { name: row.family, exact: true }).waitFor();
    await page.getByText(row.decision, { exact: true }).waitFor();
    if (!(await toggle.isChecked())) await toggle.check();
    for (const [title, view] of [['Original reviewed view', row.before], ['Refinement evidence', row.after]]) {
      const link = page.getByRole('link', { name: 'Open full evidence image · ' + title, exact: true });
      const href = await link.getAttribute('href');
      const response = await page.request.get(base + href);
      assert.equal(response.status(), 200, view.path);
      assert.equal(hash(await response.body()), view.sha256, view.path);
      const size = await link.locator('img').evaluate(async (img) => {
        await img.decode();
        return [img.naturalWidth, img.naturalHeight];
      });
      assert.deepEqual(size, [view.width, view.height]);
    }
    if (row.candidate?.scores) {
      assert.deepEqual(await page.locator('table tbody tr td:last-child').allTextContents(),
        row.candidate.scores.map((score) => String(score ?? 'Unrated')), row.family);
    }
    if (row.candidate?.download) {
      const download = page.getByRole('link', { name: /Download reviewed candidate/ });
      await download.waitFor();
      const href = await download.getAttribute('href');
      const response = await page.request.get(base + href);
      const bytes = await response.body();
      assert.equal(response.status(), 200);
      assert.equal(hash(bytes), row.candidate.sha256, row.candidate.name);
      assert.equal(bytes.length, row.candidate.bytes);
      const recipe = await page.getByRole('link', { name: 'Rebuild the exact candidate' }).getAttribute('href');
      assert.equal((await page.request.get(base + recipe)).status(), 200);
      downloads++;
      if (!testedMissing.size) {
        await page.route('**' + href, (request) => request.fulfill({ status: 503 }));
        await page.reload();
        await page.getByText(/Candidate unavailable in this checkout/).waitFor();
        await page.getByRole('link', { name: 'Rebuild the exact candidate' }).waitFor();
        await page.unroute('**' + href);
        await page.reload();
        await download.waitFor();
        testedMissing.add(href);
      }
    }
    if (row.family === 'Single lymph node' || row.family === 'Thyroid · s0189' || row.family === 'Left kidney') {
      if (!(await toggle.isChecked())) await toggle.check();
      await page.screenshot({ path: path.join(directory, row.sha256.slice(0, 8) + '.png'), fullPage: true });
    }
  }
  await page.goto(base + '/#/compare/teaching-refinements?asset=missing');
  await page.getByRole('heading', { name: 'View unavailable' }).waitFor();
  console.log('PASS ' + rows.length + ' exact before/after pairs, ' + downloads +
    ' candidate downloads, replay links, missing-candidate recovery and invalid deep link.');
}
