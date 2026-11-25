import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const root = new URL(process.argv[2] ?? 'http://127.0.0.1:8874/');
const directory = process.argv[3];
const browser = await chromium.launch({executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true});
try {
  const page = await browser.newPage({ viewport: {width:1180, height:890}, acceptDownloads:true });
  for (const side of ['right', 'left']) {
    const url = new URL('carotid-survey/volume.html?side=' + side, root);
    await page.goto(url.href);
    await page.locator('#viewer').waitFor();
    assert.equal(await page.locator('canvas').count(), 3);
    const axial = page.getByRole('slider', {name:'Transverse slice'});
    const pixels = () => page.locator('canvas').first().evaluate((c) => c.toDataURL());
    const before = await pixels();
    await axial.focus(); await axial.press('ArrowRight');
    assert.notEqual(await pixels(), before);
    const sagittal = page.getByRole('slider', {name:'Sagittal slice'});
    const old = await sagittal.inputValue();
    const box = await page.locator('canvas').first().boundingBox();
    await page.mouse.click(box.x + box.width * .62, box.y + box.height * .56);
    assert.notEqual(await sagittal.inputValue(), old);
    const downloading = page.waitForEvent('download');
    await page.locator('#download').click();
    const file = await downloading;
    assert.equal(file.suggestedFilename(), side + '-bmode.nrrd');
    assert.equal(await file.failure(),null);
    if (directory) {
      await mkdir(directory,{recursive:true});
      await page.goto(url.href);
      await page.locator('canvas').last().waitFor();
      await page.screenshot({path:join(directory,'volume-'+side+'.png')});
    }
    assert.equal(await page.locator('#returnExam').getAttribute('href'), './?side='+side);
  }
  await page.route('**/volumes/right-bmode.nrrd', r => r.fulfill({status:503,body:''}));
  await page.goto(new URL('carotid-survey/volume.html', root).href);
  await page.getByRole('button',{name:'Retry'}).waitFor();
  assert.ok(await page.locator('#viewer').isHidden());
  await page.unroute('**/volumes/right-bmode.nrrd');
  await page.getByRole('button',{name:'Retry'}).click();
  await page.locator('#viewer').waitFor();
  console.log('Both NRRD downloads, linked orthogonal slices, keyboard controls and failed-volume recovery passed.');
} finally {
  await browser.close();
}
