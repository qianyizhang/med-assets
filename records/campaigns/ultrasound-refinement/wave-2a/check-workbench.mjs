// Verify both the score shown to a learner and the actual bytes the chapter reader uses.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const base = new URL(process.argv[2]);
const root = new URL('../../../../experiments/ultrasound-sweep/development/asset-reviews/', import.meta.url);
const {chromium} = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true});
try {
  const page = await browser.newPage({viewport: {width: 1360, height: 960}});
  for (const organ of ['kidney-left', 'spleen', 'pancreas', 'liver', 'gallbladder']) {
    const owner = new URL(organ + '-wave-2a/', root);
    const {records: [review], rubricHash} = JSON.parse(await readFile(new URL('reviews.json', owner)));
    const card = JSON.parse(await readFile(new URL('gallery-card.json', owner)));
    const row = [review.source, review.case, review.chapter, review.part, review.occurrence].join('/');
    await page.goto(new URL('development/assets.html#' + row, base).href);
    const evidence = page.locator('#evidence');
    if (card.adopted) {
      await evidence.getByText(review.task, {exact: true}).waitFor();
      assert.deepEqual(await evidence.locator('dl.scores dd').evaluateAll(nodes => nodes.map(n => n.firstChild.textContent)),
        ['fidelity', 'form', 'readability', 'economy'].map(key => review.scores[key] + '/4'));
    } else {
      await evidence.getByText(/No review is recorded for this part and teaching use/).waitFor();
      assert.equal(await evidence.getByText(review.task, {exact: true}).count(), 0);
    }
    const prior = await page.evaluate(async ({review, rubricHash}) => {
      const {chapterMeshReviewPrior} = await import('./assets-data.js');
      const manifest = await fetch('./asset-inventory.json').then(response => response.json());
      return chapterMeshReviewPrior(manifest, review, rubricHash, new Map());
    }, {review, rubricHash});
    assert.equal(prior, !card.adopted, row);
    console.log(organ, card.adopted ? 'current chapter scores and mesh verified' : 'trial held outside the active chapter');
  }
} finally {
  await browser.close();
}
