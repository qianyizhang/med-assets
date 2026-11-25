import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import {
  checkTimeline, installTourClock, playTourToEnd, seekTour, waitForTourFrame,
} from './verify-timeline.mjs';

const base = new URL(process.argv[2] ?? 'http://127.0.0.1:8874/');
const captures = process.argv[3];
if (captures) await mkdir(captures, { recursive: true });
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});

const abdomen = [
  ['locate', 'liver', 12, 19],
  ['follow', 'liver', 20, 30],
  ['confirm', 'liver', 31, 48],
];
const thyroid = [
  ['right-transverse', 'thyroid-right', 0, 12],
  ['right-longitudinal', 'thyroid-right', 13, 48],
  ['left-transverse', 'thyroid-left', 0, 12],
  ['left-longitudinal', 'thyroid-left', 13, 48],
];
const scanSelector = (frame) => 'img#scan[src$="scan-' + String(frame).padStart(2, '0') + '.webp"]';
const hash = (pixels) => createHash('sha256').update(pixels).digest('hex');
const errors = [];

async function waitForScan(surface, frame) {
  await surface.locator(scanSelector(frame)).waitFor();
  assert.equal(await surface.locator('#position').inputValue(), String(frame));
  await surface.locator('#cameraPresets:not([disabled])').waitFor();
}

async function checkPanelBounds(surface) {
  const overflow = await surface.locator('#stage .view').evaluateAll((views) => views.filter((view) => {
    const panel = view.parentElement.getBoundingClientRect();
    const screen = view.getBoundingClientRect();
    return screen.left < panel.left || screen.right > panel.right;
  }).length);
  assert.equal(overflow, 0, 'Every view must stay inside its panel.');
}

async function poseHash(canvas) {
  await canvas.evaluate((element) => element.ownerDocument.defaultView.stepSweep());
  return hash(await canvas.screenshot());
}

async function captureTimeline(page, name) {
  if (!captures) return;
  await page.frameLocator('#player iframe').locator('#sceneCanvas:not([hidden])')
    .evaluate((canvas) => canvas.ownerDocument.defaultView.stepSweep());
  await page.locator('#tourPosition').evaluate((slider) => slider.scrollIntoView({ block: 'center' }));
  await page.screenshot({ path: join(captures, name + '.png') });
}

async function checkAbdomen(page, standalone) {
  const route = new URL('composed-tour/', base);
  await page.goto(new URL('tours/index.html', base).href);
  await page.getByRole('link', { name: 'Three landmarks in the liver window' }).click();
  const total = await checkTimeline(page, abdomen);
  const player = page.frameLocator('#player iframe');
  await waitForScan(player, 12);
  assert.ok(await player.locator('#refPanel').isHidden());
  assert.ok(await player.locator('#assetTab').isHidden());
  const pinned = await page.locator('.pinImage img').evaluate((img) => img.currentSrc);
  assert.equal(pinned, await player.locator('#scan').evaluate((img) => img.currentSrc));
  const openingPose = await poseHash(player.locator('#sceneCanvas'));
  await page.locator('#player iframe').evaluate((iframe) => { iframe.dataset.witness = 'starting window'; });

  for (const [letter, sweep] of [['A', 'gallbladder'], ['B', 'portal-vein'], ['C', 'ivc']]) {
    const pin = page.getByRole('button', { name: 'Identify landmark ' + letter });
    await pin.focus();
    await pin.press('Enter');
    assert.equal(await pin.getAttribute('aria-pressed'), 'true');
    const answer = page.locator('.answer:visible');
    assert.equal(await answer.getAttribute('id'), 'answer-' + letter);
    for (const [i, frame] of [12, 48].entries()) {
      const link = answer.locator('a').nth(i);
      const url = new URL(await link.getAttribute('href'), page.url());
      assert.equal(url.searchParams.get('sweep'), sweep);
      await standalone.goto(url.href);
      await waitForScan(standalone, frame);
      assert.equal(await link.locator('img').evaluate((img) => img.currentSrc),
        await standalone.locator('#scan').evaluate((img) => img.currentSrc));
      assert.ok(await standalone.locator('#refPanel').isVisible());
    }
  }

  await page.bringToFront();
  assert.equal(await playTourToEnd(page, abdomen), total);
  await page.getByRole('link', { name: 'Check the final plane' }).click();
  await page.getByRole('link', { name: 'Final plane', exact: true }).click();
  await waitForTourFrame(page, total - 1);
  await waitForScan(player, 48);
  assert.equal(await page.locator('#player iframe').getAttribute('data-witness'), 'starting window');
  assert.equal(await page.locator('.pinImage img').evaluate((img) => img.currentSrc), pinned);
  assert.notEqual(await poseHash(player.locator('#sceneCanvas')), openingPose);
  assert.equal(await page.locator('.answer:visible').getAttribute('id'), 'answer-C');
  const finalSource = new URL(await page.locator('#openSweep').getAttribute('href'));
  assert.equal(finalSource.searchParams.get('sweep'), 'liver');
  assert.equal(finalSource.searchParams.get('frame'), '48');
  await captureTimeline(page, 'abdominal-liver-window');

  await page.setViewportSize({ width: 1021, height: 980 });
  await checkPanelBounds(player);
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.goto(new URL('?chapter=gallbladder&frame=48', route).href);
  await waitForScan(player, 12);
  await page.locator('#previousView a').click();
  await waitForScan(page, 48);
  assert.equal(new URL(page.url()).searchParams.get('sweep'), 'gallbladder');
  await page.goto(new URL('?chapter=liver&frame=48', route).href);
  await waitForTourFrame(page, total - 1);
  await waitForScan(player, 48);
  await page.route('**/sweeps/liver/media/scan-12.webp', (request) => request.abort());
  await page.goto(new URL('?chapter=confirm&frame=48', route).href);
  await page.locator('.missingPlane').waitFor();
  await waitForScan(player, 48);
  await page.getByRole('button', { name: 'Identify landmark B' }).click();
  await page.locator('#answer-B').waitFor();
  await page.unroute('**/sweeps/liver/media/scan-12.webp');

  await standalone.goto(new URL('index.html?sweep=portal-vein&frame=48&view=assets', base).href);
  await standalone.locator('#assets').waitFor();
  assert.equal(await standalone.locator('#assetFrame').inputValue(), '48');
  await standalone.locator('#return').click();
  await waitForScan(standalone, 48);
  await standalone.goto(new URL('index.html?sweep=portal-vein&frame=999', base).href);
  await waitForScan(standalone, 12);
  console.log('Liver window · continuous motion, pinned plane, three landmark identifications and six targeted evidence links passed.');
}

async function checkThyroid(page, standalone) {
  await page.goto(new URL('tours/index.html', base).href);
  await page.locator('a[href="thyroid-orientation/index.html"], a[href="thyroid-orientation/"]').click();
  const tour = new URL('tours/thyroid-orientation/index.html', base);
  assert.equal(new URL('index.html', page.url()).href, tour.href);
  const total = await checkTimeline(page, thyroid);
  assert.equal(total, 98);

  const player = page.frameLocator('#player iframe');
  assert.ok(await player.locator('#assetTab').isHidden(), 'Standalone keyframe asset tab leaked into the tour');
  const step = (id) => page.locator('.chapters [data-chapter="' + id + '"][aria-current="step"]');
  const scrub = page.locator('#tourPosition');
  await seekTour(page, 12);
  await step('right-transverse').waitFor();
  await waitForScan(player, 12);
  const iframe = page.locator('#player iframe');
  await iframe.evaluate((node) => { node.dataset.frameReuseProbe = 'right'; });
  await scrub.press('ArrowRight');
  await waitForTourFrame(page, 13);
  await step('right-longitudinal').waitFor();
  await waitForScan(player, 13);
  assert.equal(await iframe.getAttribute('data-frame-reuse-probe'), 'right', 'Same right sweep was reloaded at section boundary');
  assert.equal(new URL(page.url()).searchParams.get('chapter'), 'right-longitudinal');
  assert.equal(new URL(page.url()).searchParams.get('frame'), '13');

  await page.reload();
  await waitForTourFrame(page, 13);
  await waitForScan(player, 13);
  await page.goBack();
  await waitForTourFrame(page, 12);
  await waitForScan(player, 12);

  await seekTour(page, 61);
  await step('left-transverse').waitFor();
  await waitForScan(player, 12);
  assert.equal(await iframe.getAttribute('data-frame-reuse-probe'), null, 'Previous right iframe survived a sweep switch');
  await iframe.evaluate((node) => { node.dataset.frameReuseProbe = 'left'; });
  await scrub.press('ArrowRight');
  await waitForTourFrame(page, 62);
  await step('left-longitudinal').waitFor();
  await waitForScan(player, 13);
  assert.equal(await iframe.getAttribute('data-frame-reuse-probe'), 'left', 'Same left sweep was reloaded at section boundary');

  const evidence = page.locator('#left-longitudinal .evidence a[href*="frame=48"]');
  await evidence.click();
  await waitForTourFrame(page, 97);
  await waitForScan(player, 48);
  assert.equal(await evidence.getAttribute('aria-current'), 'true');
  const witness = new URL(await page.locator('#openSweep').getAttribute('href'));
  assert.equal(witness.searchParams.get('sweep'), 'thyroid-left');
  assert.equal(witness.searchParams.get('frame'), '48');
  await standalone.goto(witness.href);
  await waitForScan(standalone, 48);
  assert.equal(await standalone.locator('#scan').getAttribute('src'), await player.locator('#scan').getAttribute('src'));

  await page.bringToFront();
  await seekTour(page, 0);
  assert.equal(await playTourToEnd(page, thyroid), total);
  await seekTour(page, 62);
  await waitForScan(player, 13);
  await captureTimeline(page, 'thyroid-orientation-timeline');
  await page.setViewportSize({ width: 1021, height: 980 });
  await checkPanelBounds(player);
  console.log('Thyroid orientation · 4 sections · 98 committed frames, keyboard, history and same-sweep reuse passed.');
}

try {
  const viewport = { width: 1320, height: 1040 };
  const page = await browser.newPage({ viewport });
  const standalone = await browser.newPage({ viewport });
  for (const tab of [page, standalone]) {
    tab.setDefaultTimeout(15000);
    tab.setDefaultNavigationTimeout(15000);
    tab.on('pageerror', (error) => errors.push(error.message));
  }
  await installTourClock(page);
  await checkAbdomen(page, standalone);
  await page.setViewportSize(viewport);
  await checkThyroid(page, standalone);
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
}
