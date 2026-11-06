const {chromium} = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const base=new URL('../.local/qa/',import.meta.url).pathname;
await fs.mkdir(base,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.MODEL_SURVEY_BROWSER,headless:true,chromiumSandbox:true});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('http://127.0.0.1:62099/',{waitUntil:'networkidle'});
 const report=page.locator('.sv-report');await report.waitFor();
 const click=async name=>page.getByRole('button',{name,exact:true}).click();
 const checks=[];
 await click('Expand');assert.equal(await page.locator('.sv-asset').count(),93);assert.equal(await page.locator('.sv-asset[open]').count(),93);checks.push('93 entries expand');
 await click('Collapse');assert.equal(await page.locator('.sv-asset').count(),0);checks.push('collapse');
 await page.getByLabel('Related products').uncheck();await click('Expand');assert.equal(await page.locator('.sv-asset').count(),62);checks.push('62 family coverage');
 for(const tab of ['Purpose','Review']){await click(tab);await click('Expand');assert.equal(await page.locator('.sv-asset').count(),62);checks.push(tab+' coverage');}
 await page.locator('.sv-baseline>summary').click();await page.locator('.recharts-bar-rectangle').first().waitFor({timeout:7000});checks.push('baseline chart rendered');
 await page.screenshot({path:base+'preview-review.png',fullPage:false});
 const search=page.getByRole('searchbox');await search.fill('thyroid');assert.ok(await page.locator('.sv-asset').count()>0);await click('Collapse');assert.equal(await page.locator('.sv-asset').count(),0);checks.push('search and collapse');
 await search.fill('not-a-real-model-zz');assert.ok(await page.getByText('No matching entries',{exact:false}).isVisible());await click('Clear search');checks.push('empty search recovery');
 await click('Overlaps');await page.getByRole('button',{name:'Cardiac Atlas · native & static ↗',exact:true}).click();assert.ok(await page.getByText('Four chambers, valves/chordae, representative vessels/coronaries; editable native rig',{exact:true}).isVisible());checks.push('overlap deep link enables related product');
 await search.fill('');await click('Gaps');await click('Expand');assert.equal(await page.locator('.sv-gap').count(),15);await page.screenshot({path:base+'preview-gaps.png',fullPage:false});checks.push('15 proposed gap nodes');
 await click('Files');await click('Expand');assert.equal(await page.locator('.sv-file').count(),141);checks.push('141 GLB paths');
 await click('Anatomy');await click('Collapse');const summary=page.locator('.sv-group>summary').first();await summary.focus();await page.keyboard.press('Enter');assert.equal(await page.locator('.sv-group[open]').count(),1);checks.push('keyboard disclosure');
 await page.waitForTimeout(250);await page.screenshot({path:base+'preview-desktop.png',fullPage:true});
 const desktopOverflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));console.log(JSON.stringify({desktopOverflow}));await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);await page.screenshot({path:base+'preview-mobile.png',fullPage:true});
 const overflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,article:document.querySelector('.sv-report').getBoundingClientRect().toJSON()}));assert.ok(overflow.scroll<=overflow.width+1,JSON.stringify(overflow));checks.push('390px reflow');
 await page.emulateMedia({colorScheme:'dark'});await page.waitForTimeout(200);await page.screenshot({path:base+'preview-dark.png',fullPage:true});const activeColors=await page.locator('.sv-tabs button[aria-pressed=true]').evaluate(e=>({color:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor}));assert.notEqual(activeColors.color,activeColors.background);checks.push('dark theme active tab contrast');
 assert.deepEqual(errors,[]);console.log(JSON.stringify({checks,errors,overflow}));await fs.writeFile(base+'verification.json',JSON.stringify({checks,errors,overflow},null,2));
}finally{await browser.close();}
