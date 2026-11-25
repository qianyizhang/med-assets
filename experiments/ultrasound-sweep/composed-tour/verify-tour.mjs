import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import {
  absoluteFrame, checkTimeline, installTourClock, playTourToEnd, seekTour, waitForTourFrame,
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

const abdomen = [['liver', 'liver', 0, 48], ['portal-vein', 'portal-vein', 0, 48], ['gallbladder', 'gallbladder', 0, 48]];
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
  await page.goto(new URL('composed-tour/index.html', base).href);
  const total = await checkTimeline(page, abdomen);
  assert.equal(total, 147);
  const player = page.frameLocator('#player iframe');
  assert.ok(await player.locator('#assetTab').isHidden(), 'Standalone keyframe asset tab leaked into the tour');
  const canvas = player.locator('#sceneCanvas');

  for (const [chapter, sweep] of abdomen) {
    await page.locator('.chapters [data-chapter="' + chapter + '"]').click();
    await waitForTourFrame(page, absoluteFrame(abdomen, chapter, 0));
    await waitForScan(player, 0);
    await page.locator('#' + chapter).waitFor();
    const firstPose = await poseHash(canvas);
    await seekTour(page, absoluteFrame(abdomen, chapter, 48));
    await waitForScan(player, 48);
    const lastPose = await poseHash(canvas);
    assert.notEqual(firstPose, lastPose, chapter + ' probe scene did not move with the source sweep');

    const evidence = page.locator('#' + chapter + ' .evidence a').filter({ hasText: /^12/ });
    await evidence.click();
    await waitForTourFrame(page, absoluteFrame(abdomen, chapter, 12));
    assert.equal(await evidence.getAttribute('aria-current'), 'true');
    await waitForScan(player, 12);
    const scan = await player.locator('#scan').getAttribute('src');
    const label = await player.locator('#readout').textContent();
    assert.equal(await player.locator('#referenceDepth').textContent(), 'Different case');
    const standaloneURL = new URL(await page.locator('#openSweep').getAttribute('href'));
    assert.equal(standaloneURL.searchParams.get('sweep'), sweep);
    assert.equal(standaloneURL.searchParams.get('frame'), '12');
    assert.equal(standaloneURL.searchParams.has('embed'), false);
    await standalone.goto(standaloneURL.href);
    await waitForScan(standalone, 12);
    await standalone.getByRole('button', { name: 'Play sweep', exact: true }).waitFor();
    assert.equal(await standalone.locator('#scan').getAttribute('src'), scan);
    assert.equal(await standalone.locator('#readout').textContent(), label);

    await standalone.locator('#assetTab').click();
    assert.equal(await standalone.locator('#assetFrame').inputValue(), '12');
    await standalone.locator('#return').click();
    await waitForScan(standalone, 12);
  }

  await page.bringToFront();
  await seekTour(page, 0);
  assert.equal(await playTourToEnd(page, abdomen), total);
  await seekTour(page, absoluteFrame(abdomen, 'portal-vein', 12));
  await waitForScan(player, 12);
  await captureTimeline(page, 'abdominal-orientation-timeline');
  await page.setViewportSize({ width: 1021, height: 980 });
  await checkPanelBounds(player);

  await standalone.goto(new URL('index.html?sweep=portal-vein&frame=48&view=assets', base).href);
  await standalone.locator('#assets').waitFor();
  assert.equal(await standalone.locator('#assetFrame').inputValue(), '48');
  await standalone.locator('#return').click();
  await waitForScan(standalone, 48);
  await standalone.goto(new URL('index.html?sweep=portal-vein&frame=999', base).href);
  await waitForScan(standalone, 12);
  console.log('Abdominal orientation · 3 sections · 147 committed frames, probe motion and standalone evidence passed.');
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
