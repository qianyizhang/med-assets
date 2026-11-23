import assert from 'node:assert/strict';
import { sha256 } from './assertions.mjs';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

export async function checkTeachingTargets({ browser, base, capture, builtApp: app }) {
  const input = path.join(app, 'src/content/gallery');
  const { campaign } = JSON.parse(await readFile(path.join(input, 'teaching-inputs/teaching-assessments.json')));
  const systems = JSON.parse(await readFile(path.join(input, 'body-systems.json')));
  const rows = campaign.filter((r) => r.maintained && r.target);
  // The shared cardiac selections supersede two files from the original target round.
  const cardiacControls = campaign.filter((row) => !row.maintained && row.target && [
    'heart/Cardiac_Atlas/exports/teaching-economy-r01/Cardiac_Atlas_Clinical_Full_ED.glb',
    'heart/Cardiac_Atlas_Animated/exports/wall-motion-r01/ventricular-wall-motion.glb',
  ].includes(row.export.path));
  assert.equal(cardiacControls.length, 2);
  assert.equal(rows.length + cardiacControls.length, 45);
  const page = await browser.newPage({ viewport: { width: 1220, height: 900 } });
  const go = (fragment) => page.goto(base + '/#/' + fragment);
  await go('compare');
  await page.getByRole('link', { name: 'Review current teaching targets →' }).click();
  const picker = page.getByRole('combobox', { name: 'Reviewed asset' });
  await picker.waitFor();
  assert.equal(await picker.locator('option').count(), rows.length);
  for (const row of [...rows, ...cardiacControls]) {
    await go('compare/teaching-target?asset=' + row.export.sha256);
    await page.getByRole('heading', { name: row.target.family, exact: true }).waitFor();
    assert.equal(await picker.inputValue(), row.export.sha256);
    assert.deepEqual(await page.locator('tbody tr td:last-child').allTextContents(), row.axes.map((a) => String(a.score)));
    for (const witness of new Set([row.target.before, row.target.after])) {
      const view = row.views.find((v) => v.path === witness);
      const img = page.locator('figure img[src="' + view.url + '"]');
      await img.evaluate((i) => i.decode());
      assert.ok(await img.isVisible(), row.target.family + ': ' + witness);
    }
    assert.equal(await page.getByRole('heading', { name: /target exemption/ }).count(), Object.keys(row.target.exemptions).length);
    const name = path.basename(row.export.path);
    const response = await page.request.get(base + '/assets/' + row.export.sha256 + '/' + name);
    assert.equal(response.status(), 200, name);
    const data = await response.body();
    assert.equal(sha256(data), row.export.sha256, name);
  }
  await go('compare/teaching-target?round=reopened');
  const reopenedRows = rows.filter((r) => r.target.reviewedAxes);
  assert.equal(reopenedRows.length, 20);
  assert.equal(reopenedRows.reduce((n, r) => n + r.target.reviewedAxes.length, 0), 25);
  await page.waitForFunction((n) => Array.from(document.querySelectorAll('label')).find((l) => l.firstChild?.textContent.trim() === 'Reviewed asset')?.querySelector('select')?.options.length === n, reopenedRows.length);
  assert.equal(await picker.locator('option').count(), reopenedRows.length);
  for (const reviewed of reopenedRows.filter((r) => r.target.workItem)) {
    await picker.selectOption(reviewed.export.sha256);
    await page.getByRole('heading', { name: reviewed.target.family, exact: true }).waitFor();
    const followup = page.getByRole('link', { name: 'Open the owned follow-up' });
    const href = await followup.getAttribute('href');
    const response = await page.request.get(base + href);
    assert.equal(href, reviewed.sources.find((s) => s.path === reviewed.target.workItem).url);
    assert.equal(response.status(), 200, reviewed.target.workItem);
    assert.match(await response.text(), /Next action/);
  }
  await go('compare/teaching-target?asset=missing');
  await page.getByRole('heading', { name: 'View unavailable' }).waitFor();
  for (const s of systems) {
    await go('use-cases/systems/' + s.id);
    await page.getByText('Required teaching check · ' + s.check.status, { exact: true }).click();
    await page.getByText(s.check.observation, { exact: true }).waitFor();
    await page.getByRole('link', { name: 'Open the reviewed detail' }).click();
    assert.ok(page.url().endsWith('detail=' + s.check.detail), s.id);
    await page.waitForFunction((detail) => document.querySelector('select[aria-label="Detail view"]')?.value === detail, s.check.detail);
    if (s.id === 'reproductive') {
      await page.getByRole('heading', { name: 'Where is the fimbrial end relative to the ovary?' }).waitFor();
      const images = page.locator('section[aria-labelledby^="ovary-"] img');
      assert.equal(await images.count(), 2);
      await images.evaluateAll((nodes) => Promise.all(nodes.map((node) => node.decode())));
      await page.screenshot({ path: path.join(capture, s.id + '.png'), fullPage: true });
    } else {
      await page.locator('.ga-system-plate img').evaluateAll((images) => Promise.all(images.map((i) => i.decode())));
    }
    if (s.id === 'endocrine') {
      const title = 'Locate the four atlas parathyroid glands';
      await page.getByRole('heading', { name: title }).waitFor();
      await page.getByRole('link', { name: 'Open full teaching image · ' + title }).locator('img').evaluate((i) => i.decode());
      await page.screenshot({ path: path.join(capture, s.id + '.png'), fullPage: true });
    }
  }
  const otherChecks = JSON.parse(await readFile(path.join(input, 'teaching-inputs/use-case-checks.json')));
  await go('use-cases');
  await page.locator('summary').filter({ hasText: 'Teaching checks' }).click();
  for (const check of otherChecks) {
    const link = page.getByRole('link', { name: check.action, exact: true });
    assert.equal(await link.getAttribute('href'), '#/' + check.route);
  }
  for (const check of otherChecks) {
    await go(check.route);
    await page.waitForFunction(() => document.querySelector('.ga-heading h1')?.textContent !== 'Use Cases');
    assert.equal(await page.getByRole('heading', { name: 'View unavailable' }).count(), 0, check.route);
  }
  await go('library/parathyroids/z-localization-r01?file=missing');
  await page.getByRole('heading', { name: 'View unavailable' }).waitFor();
  console.log(`PASS 45 current and historical before/after reviews and exact downloads, 11 required Body Systems stops, ${otherChecks.length} other use-case checks, invalid file and review recovery.`);
}
