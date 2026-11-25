import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const base = new URL(process.argv[2] ?? 'http://127.0.0.1:8874/');
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});

const chapters = ['liver', 'portal-vein', 'gallbladder'];
const scanSelector = (frame) => 'img#scan[src$="scan-' + String(frame).padStart(2, '0') + '.webp"]';
const hash = (pixels) => createHash('sha256').update(pixels).digest('hex');

async function waitForScan(surface, frame) {
  await surface.locator(scanSelector(frame)).waitFor();
  assert.equal(await surface.locator('#position').inputValue(), String(frame));
}

async function waitForPlayback(surface, frame) {
  const expected = frame === 48 ? 'Replay sweep' : 'Play sweep';
  await surface.getByRole('button', { name: expected, exact: true }).and(surface.locator('#play:not([disabled])')).waitFor();
  await waitForScan(surface, frame);
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

const errors = [];
try {
  const page = await browser.newPage({ viewport: { width: 1320, height: 1040 } });
  const standalone = await browser.newPage({ viewport: { width: 1320, height: 1040 } });
  for (const tab of [page, standalone]) tab.on('pageerror', (error) => errors.push(error.message));
  const tour = new URL('composed-tour/index.html', base);
  await page.goto(tour.href);
  const player = page.frameLocator('#player iframe');
  const canvas = player.locator('#sceneCanvas');

  for (const chapter of chapters) {
    const section = page.locator('#' + chapter);
    assert.equal(await page.locator('.chapters [aria-current="step"]').getAttribute('data-chapter'), chapter);
    await section.waitFor();
    await waitForPlayback(player, 0);

    const startPose = hash(await canvas.screenshot());
    await player.getByRole('button', { name: 'Play sweep', exact: true }).click();
    await player.locator('#scan').and(player.locator('img:not([src$="scan-00.webp"]):not([src$="scan-48.webp"])')).waitFor();
    await waitForPlayback(player, 48);
    const endPose = hash(await canvas.screenshot());
    assert.notEqual(endPose, startPose, chapter + ' probe scene must move with the sweep');
    await player.getByRole('button', { name: 'Replay sweep', exact: true }).click();
    await player.locator('#scan').and(player.locator('img:not([src$="scan-48.webp"])')).waitFor();

    const evidence = section.getByRole('link', { name: /^12/ });
    await evidence.click();
    await waitForPlayback(player, 12);
    assert.equal(await evidence.getAttribute('aria-current'), 'true');
    const scan = await player.locator('#scan').getAttribute('src');
    const label = await player.locator('#readout').textContent();
    assert.equal(await player.locator('#referenceDepth').textContent(), 'Different case');
    const standaloneURL = new URL(await page.locator('#openSweep').getAttribute('href'));
    await standalone.goto(standaloneURL.href);
    await waitForPlayback(standalone, 12);
    assert.equal(await standalone.locator('#scan').getAttribute('src'), scan);
    assert.equal(await standalone.locator('#readout').textContent(), label);

    await player.locator('#assetTab').click();
    assert.equal(await player.locator('#assetFrame').inputValue(), '12');
    await player.locator('#return').click();
    await waitForScan(player, 12);
    await page.locator('#advance').click();
  }

  assert.equal(await page.locator('.chapters [aria-current="step"]').getAttribute('data-chapter'), 'liver');
  await waitForPlayback(player, 0);
  await checkPanelBounds(player);
  await page.getByRole('button', { name: 'Play tour', exact: true }).click();
  await player.locator('#scan:not([src$="scan-00.webp"])').waitFor();
  await player.locator('#position').fill('24');
  await page.getByRole('button', { name: 'Play tour', exact: true }).waitFor();
  await waitForPlayback(player, 24);
  await page.locator('#openSweep[href$="frame=24"]').waitFor();
  await standalone.goto(await page.locator('#openSweep').getAttribute('href'));
  await waitForPlayback(standalone, 24);

  await page.getByRole('button', { name: 'Play tour', exact: true }).click();
  for (const chapter of chapters.slice(1)) {
    await page.locator('.chapters [data-chapter="' + chapter + '"][aria-current="step"]').waitFor();
    await player.getByRole('button', { name: 'Pause', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Pause tour', exact: true }).waitFor();
  }
  const replayTour = page.getByRole('button', { name: 'Replay tour', exact: true });
  await replayTour.waitFor();
  await waitForPlayback(player, 48);
  await replayTour.click();
  await page.locator('.chapters [data-chapter="liver"][aria-current="step"]').waitFor();
  await player.getByRole('button', { name: 'Pause', exact: true }).waitFor();
  await page.getByRole('button', { name: 'Pause tour', exact: true }).click();
  await player.getByRole('button', { name: 'Play sweep', exact: true }).waitFor();
  await page.setViewportSize({ width: 1021, height: 980 });
  await checkPanelBounds(player);

  const assets = new URL('index.html?sweep=portal-vein&frame=48&view=assets', base);
  await standalone.goto(assets.href);
  await standalone.locator('#assets').waitFor();
  assert.equal(await standalone.locator('#assetFrame').inputValue(), '48');
  await standalone.locator('#return').click();
  await waitForPlayback(standalone, 48);

  const invalid = new URL('index.html?sweep=portal-vein&frame=999', base);
  await standalone.goto(invalid.href);
  await waitForPlayback(standalone, 12);
  assert.deepEqual(errors, []);
  console.log('Abdominal tour chapters, probe motion, playback, evidence parity and deep links passed.');
} finally {
  await browser.close();
}
