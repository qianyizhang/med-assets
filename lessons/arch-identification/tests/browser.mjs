// Actual browser journey. Requires a working sandbox; never falls back to --no-sandbox.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {PLACEMENTS, order} from '../plate.mjs';
const {chromium} = createRequire(import.meta.url)('playwright-core');
const [url, out] = process.argv.slice(2);
if (!url || !out) throw Error('Usage: node tests/browser.mjs LOCAL_URL NEW_OUTPUT_DIRECTORY');
if (!['localhost', '127.0.0.1', '[::1]'].includes(new URL(url).hostname)) throw Error('Local review URL required');
const browser = await chromium.launch({executablePath: process.env.BROWSER_EXECUTABLE || '/usr/bin/chromium', chromiumSandbox: true, headless: true});
try {
  await fs.mkdir(out, {recursive: false});
  const page = await browser.newPage({viewport: {width: 1080, height: 900}});
  const errors = []; page.on('pageerror', error => errors.push(String(error)));
  await page.goto(url);
  await page.locator('[role="radio"]').first().waitFor();
  for (const lang of ['en','zh']) {
    await page.locator(`[data-lang="${lang}"]`).click();
    for (const arch of ['upper','lower']) {
      await page.locator(`[data-arch="${arch}"]`).click();
      for (const fdi of Object.keys(PLACEMENTS[arch])) {
        await page.locator(`[role="radio"][data-fdi="${fdi}"]`).click();
        assert.equal(await page.locator('#fdi').textContent(), `FDI ${fdi}`);
      }
      await page.locator('[role="radio"][tabindex="0"]').focus();
      await page.keyboard.press('Home');
      for (const fdi of order(arch)) {
        assert.equal(await page.locator(':focus').getAttribute('data-fdi'), fdi);
        await page.keyboard.press('ArrowRight');
      }
      const expected = lang === 'en' ? (arch === 'upper' ? 'Patient right' : 'Patient left') : (arch === 'upper' ? '患者右侧' : '患者左侧');
      assert.equal(await page.locator('#screen-left').textContent(), expected);
      await page.screenshot({path:path.join(out, `${arch}-${lang}.png`), fullPage:true});
    }
  }
  await page.setViewportSize({width:320, height:800});
  await page.waitForFunction(() => document.querySelector('#plate svg').getAttribute('width') === String(document.querySelector('#plate').getBoundingClientRect().width));
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  for (const arch of ['upper','lower']) {
    await page.locator(`[data-arch="${arch}"]`).click();
    const boxes = await page.locator('.tag').evaluateAll(els => els.map(el => { const r=el.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}; }));
    for (let i=0;i<boxes.length;i++) for (let j=i+1;j<boxes.length;j++) {
      const a=boxes[i],b=boxes[j]; assert.ok(a.right<=b.x || b.right<=a.x || a.bottom<=b.y || b.bottom<=a.y);
    }
    await page.screenshot({path:path.join(out, `narrow-${arch}-zh.png`), fullPage:true});
  }
  const imageRoute = '**/lower-occlusal-teeth.png';
  await page.route(imageRoute, route => route.abort());
  await page.reload();
  await page.locator('[data-arch="lower"]').click();
  await page.locator('#image-error').waitFor({state:'visible'});
  await page.locator('[role="radio"][data-fdi="46"]').click();
  await page.locator('[data-lang="zh"]').click();
  assert.equal(await page.locator('#fdi').textContent(), 'FDI 46');
  await page.screenshot({path:path.join(out, 'missing-lower-zh.png'), fullPage:true});
  await page.unroute(imageRoute);
  await page.locator('#retry').click();
  await page.locator('#image-error').waitFor({state:'hidden'});
  assert.equal(await page.locator('#fdi').textContent(), 'FDI 46');
  assert.deepEqual(errors, []);
  await fs.writeFile(path.join(out, 'result.json'), JSON.stringify({browser:await browser.version(), result:'passed', ids:28, languages:['en','zh'], viewportWidths:[1080,320], imageFailureAndRetry:true},null,2)+'\n');
} finally {await browser.close();}
