// Compare the scores displayed on every companion use with its exact chapter review.
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {join} from 'node:path';
const [address, output] = process.argv.slice(2);
const base = new URL(address);
const manifest = await fetch(new URL('development/asset-inventory.json', base)).then(response => response.json());
const {chromium} = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true});
await mkdir(output, {recursive: true});
try {
  const page = await browser.newPage({viewport: {width: 1360, height: 960}});
  const chapters = manifest.cases.flatMap(visit => visit.chapters.filter(chapter => chapter.exemplar)
    .map(chapter => [visit.id, chapter.id, chapter.exemplar.part].join('/')));
  const checked = [];
  for (const path of manifest.reviews) {
    const {records} = await fetch(new URL('development/' + path, base)).then(response => response.json());
    for (const record of records) {
      const key = [record.case, record.chapter, record.part].join('/');
      if (!chapters.includes(key) || record.meshSha256 !==
          manifest.chapterMeshBindings[record.case][record.chapter][record.part].meshSha256) continue;
      const row = ['case', key, 1].join('/');
      await page.goto(new URL('development/assets.html#' + row, base).href);
      const evidence = page.locator('#evidence');
      await evidence.getByText(record.task, {exact: true}).waitFor();
      const scores = await evidence.locator('dl.scores dd').evaluateAll(nodes => nodes.map(n => n.firstChild.textContent));
      assert.deepEqual(scores, ['fidelity','form','readability','economy'].map(axis => record.scores[axis] + '/4'));
      await evidence.screenshot({path: join(output, record.chapter + '.png')});
      checked.push(key);
    }
  }
  assert.deepEqual(checked.sort(), chapters.sort());
  console.log('Verified current scores on', checked.length, 'CT companion uses.');
} finally {
  await browser.close();
}
