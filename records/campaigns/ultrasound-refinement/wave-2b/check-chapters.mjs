// Exercise the worked action and its separately registered CT companion in the delivered chapter.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir, writeFile} from 'node:fs/promises';
import {join} from 'node:path';

const [address, output] = process.argv.slice(2);
const base = new URL(address);
const inventory = await fetch(new URL('development/asset-inventory.json', base)).then(response => response.json());
const {chromium} = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true, args: ['--enable-unsafe-swiftshader']});
await mkdir(output, {recursive: true});
const inspected = [];
try {
  for (const visit of inventory.cases) {
    for (const chapter of visit.chapters.filter(row => row.exemplar)) {
      const page = await browser.newPage({viewport: {width: 1380, height: 1000}, reducedMotion: 'reduce'});
      try {
        const url = new URL(visit.url, base);
        url.search = new URLSearchParams({chapter: chapter.id, frame: chapter.evidenceFrame});
        url.hash = 'exam';
        await page.goto(url.href);
        const panel = page.locator('.chapter:not([hidden])');
        assert.equal(await panel.locator('h2').innerText(), chapter.title);
        const worked = page.frameLocator('#player iframe');
        await worked.locator('#position').waitFor({state: 'attached'});
        await page.waitForFunction(frame =>
          document.querySelector('#player iframe')?.contentDocument?.querySelector('#position')?.value === String(frame),
        chapter.evidenceFrame);
        const exemplar = chapter.exemplar;
        const binding = inventory.chapterMeshBindings[visit.id][chapter.id][exemplar.part];
        const requested = page.waitForResponse(response => response.ok() &&
          response.url() === new URL(binding.path, base).href &&
          response.frame().url().includes('sweep=' + exemplar.sweep));
        await panel.locator('summary').click();
        const companion = panel.frameLocator('.ct-exemplar iframe');
        await companion.locator('#sceneHelp:not([hidden])').waitFor();
        assert.equal(await companion.locator('#position').inputValue(), String(exemplar.frame));
        const sha256 = createHash('sha256').update(await (await requested).body()).digest('hex');
        assert.equal(sha256, binding.meshSha256);
        const canvas = companion.locator('#sceneCanvas');
        await canvas.screenshot({path: join(output, chapter.id + '-oblique.png')});
        await companion.getByRole('button', {name: 'Axial', exact: true}).click();
        await canvas.screenshot({path: join(output, chapter.id + '-axial.png')});
        await companion.getByRole('button', {name: 'Anatomy overlay'}).click();
        const overlay = companion.locator('#scan[src$="section-' + String(exemplar.frame).padStart(2, '0') + '.webp"]');
        await overlay.waitFor();
        assert.ok(await overlay.evaluate(async image => { await image.decode(); return image.naturalWidth > 0; }));
        await panel.locator('summary').click();
        assert.equal(await worked.locator('#position').inputValue(), String(chapter.evidenceFrame));
        inspected.push({case: visit.id, chapter: chapter.id, workedFrame: chapter.evidenceFrame, exemplar, ...binding});
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}
assert.ok(inspected.length, 'No registered CT companions were exercised');
await writeFile(join(output, 'chapter-requests.json'), JSON.stringify(inspected, null, 2) + '\n');
console.log('Verified worked frame and exact CT companion in', inspected.length, 'chapters.');
