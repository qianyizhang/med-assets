import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';

import { sectionMask } from './volume-contours.js';

// An asymmetric box distinguishes axis swaps and image flips. The independently
// calculated inside test uses voxel coordinates and never calls the renderer.
const grid = {size:[11,15,19], spacingMm:[.4,.7,1.3], originMm:[-11,5,24]};
const low = [2.3,3.2,4.45], high = [8.6,10.3,12.61];
const vertices = [];
for (let n=0; n<8; n++) {
  for (let axis=0; axis<3; axis++) {
    const index = (n & (1 << axis)) ? high[axis] : low[axis];
    vertices.push(grid.originMm[axis] + grid.spacingMm[axis] * index);
  }
}
const faces = [0,1,3,0,3,2,4,7,5,4,6,7,0,5,1,0,4,5,2,3,7,2,7,6,0,2,6,0,6,4,1,5,7,1,7,3];
for (const axes of [[0,1,2],[0,2,1],[1,2,0]]) {
  const [u,v,d] = axes;
  for (const slice of [0,6]) {
    const mask = sectionMask([{vertices,faces}],grid,axes,slice,1);
    for (let j=0; j<grid.size[v]; j++) {
      for (let i=0; i<grid.size[u]; i++) {
        const pos = []; pos[u]=grid.size[u]-i-1; pos[v]=grid.size[v]-j-1; pos[d]=slice;
        assert.equal(mask[j*grid.size[u]+i], Number(pos.every((c,axis) => low[axis]<c && c<high[axis])));
      }
    }
  }
}
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
    const compare = page.getByRole('button', {name:'Compare lumen'});
    const plain = await pixels();
    await compare.click();
    await page.locator('#comparisonKey').waitFor();
    assert.notEqual(await pixels(), plain, 'The registered overlay should change the actual axial image');
    await compare.click();
    assert.equal(await pixels(), plain, 'Turning off contours must restore the same grayscale image');
    await axial.focus(); await axial.press('End');
    await compare.click();
    await page.waitForFunction(() => document.querySelector('#visibility').textContent.includes('58%'));
    if (directory) {
      await mkdir(directory,{recursive:true});
      await page.screenshot({path:join(directory, 'upper-limit-'+side+'.png')});
    }
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
  await page.route('**/scenes/right-stitched.mesh', route => route.fulfill({status:503,body:''}));
  await page.goto(new URL('carotid-survey/volume.html', root).href);
  await page.getByRole('button',{name:'Compare lumen'}).click();
  await page.locator('#compareStatus').waitFor();
  assert.ok(await page.locator('#planes').isVisible());
  await page.unroute('**/scenes/right-stitched.mesh');
  await page.getByRole('button',{name:'Compare lumen'}).click();
  await page.locator('#comparisonKey').waitFor();
  await page.route('**/volumes/right-bmode.nrrd', r => r.fulfill({status:503,body:''}));
  await page.goto(new URL('carotid-survey/volume.html', root).href);
  await page.getByRole('button',{name:'Retry'}).waitFor();
  assert.ok(await page.locator('#viewer').isHidden());
  await page.unroute('**/volumes/right-bmode.nrrd');
  await page.getByRole('button',{name:'Retry'}).click();
  await page.locator('#viewer').waitFor();
  console.log('Both volume exports, linked slices, registered contour comparisons and independent mesh/volume recovery passed.');
} finally {
  await browser.close();
}
