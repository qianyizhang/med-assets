// Exercise the actual playback controls at the viewport where the readout shifted.
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const url = process.argv[2] ?? 'http://127.0.0.1:8874';
const captureFolder = process.env.ABDOMEN_TOUR_QA_DIR;
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});

try {
  const page = await browser.newPage({ viewport: { width: 1021, height: 1197 } });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(url);
  const ready = () => page.waitForFunction(() =>
    document.querySelector('#cameraPresets')?.disabled === false && document.querySelector('#play')?.disabled === false);
  await ready();
  const canvas = page.locator('#sceneCanvas');
  const screenshot = async () => {
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    return canvas.screenshot();
  };
  const preset = (id) => page.locator('#cameraPreset-' + id);
  const capture = async (name, fullPage = false) => {
    if (!captureFolder) return;
    await mkdir(captureFolder, { recursive: true });
    await page.evaluate(() => {
      scrollTo(0, 0);
      return new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });
    await page.screenshot({ path: join(captureFolder, name + '.png'), fullPage });
  };
  assert.equal(await preset('oblique').getAttribute('aria-pressed'), 'true');
  await preset('oblique').click();
  await capture('gallbladder-oblique-1021x1197');
  const oblique = await screenshot();
  const rect = await canvas.boundingBox();
  const x = rect.x + rect.width / 2;
  const y = rect.y + rect.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + 74, y + 26, { steps: 6 });
  await page.mouse.up();
  assert.notDeepEqual(await screenshot(), oblique, 'Orbit should change the 3D view.');
  assert.equal(await page.locator('#cameraPresets [aria-pressed="true"]').count(), 0);
  await preset('oblique').click();
  assert.deepEqual(await screenshot(), oblique, 'A camera preset should be reapplicable after orbit.');
  const projections = [oblique];
  for (const id of ['axial', 'coronal', 'sagittal']) {
    await preset(id).click();
    assert.equal(await preset(id).getAttribute('aria-pressed'), 'true');
    assert.equal(await page.locator('#cameraPresets [aria-pressed="true"]').count(), 1);
    const view = await screenshot();
    for (const previous of projections) assert.notDeepEqual(view, previous, id + ' camera duplicated another preset.');
    projections.push(view);
  }
  await canvas.press('ArrowRight');
  assert.equal(await page.locator('#cameraPresets [aria-pressed="true"]').count(), 0);
  await canvas.press('Home');
  assert.equal(await preset('sagittal').getAttribute('aria-pressed'), 'true');
  await canvas.press('+');
  assert.equal(await preset('sagittal').getAttribute('aria-pressed'), 'true');
  await page.locator('#shortTick').click();
  await page.waitForFunction(() => document.querySelector('#scan')?.src.endsWith('scan-48.webp'));
  const opacity = page.getByRole('slider', { name: 'Torso opacity' });
  for (const value of ['0', '100', '32']) {
    await opacity.fill(value);
    assert.equal(await opacity.getAttribute('aria-valuetext'), value + '%');
    assert.equal(await page.locator('#position').inputValue(), '48');
  }
  await opacity.press('ArrowRight');
  assert.equal(await opacity.inputValue(), '33');
  await page.click('#assetTab');
  await page.click('#return');
  await preset('oblique').click();
  assert.equal(await opacity.inputValue(), '33');
  const replay = page.getByRole('button', { name: 'Replay sweep' });
  await replay.waitFor();
  await page.waitForFunction(() => !document.querySelector('#play').disabled);

  const result = await page.evaluate(async () => {
    const elements = ['play', 'position', 'readout', 'angle', 'sceneCanvas', 'torsoOpacity', 'torsoOpacityValue', 'scan', 'ref'];
    const bounds = () => elements.flatMap((id) => {
      const element = document.getElementById(id);
      if (!element) throw new Error(id + ' unavailable during replay at frame ' + document.getElementById('position').value);
      const { x, y, width, height } = element.getBoundingClientRect();
      return [x, y, width, height];
    });
    const reference = bounds();
    let maxShift = 0;
    const frames = new Set();
    const deadline = performance.now() + 15000;
    document.getElementById('play').click();
    do {
      await new Promise(requestAnimationFrame);
      frames.add(Number(document.getElementById('position').value));
      maxShift = Math.max(maxShift, ...bounds().map((value, i) => Math.abs(value - reference[i])));
    } while (performance.now() < deadline && document.getElementById('play').textContent !== 'Replay sweep');
    return { maxShift, intermediate: [...frames].some((frame) => frame > 0 && frame < 48),
      end: document.getElementById('position').value };
  });
  assert.ok(result.intermediate, 'Replay should pass through intermediate poses.');
  assert.equal(result.end, '48');
  assert.ok(result.maxShift < 1, 'Playback shifted the layout by ' + result.maxShift + ' pixels.');

  const catalogue = await page.evaluate(() => abdomenTours.map((tour) => ({
    id: tour.id,
    title: tour.title,
    assetRoot: tour.assetRoot,
    usesAtlas: tour.exterior ? tour.exterior === 'fitted-atlas' : tour.id === 'gallbladder',
    parts: tour.parts.map((part) => part.label),
    landmarks: (tour.landmarks ?? []).map((id) => ({ id, ...abdomenReferences[id] })),
    keys: tour.keyframes.map((key) => {
      const reference = abdomenReferences[key.referenceId];
      return { frame: key.frame, label: key.label, referenceId: key.referenceId, path: reference.path, url: reference.url,
        referenceLabel: key.referenceLabel ?? reference.label ?? key.label };
    }),
  })));
  assert.ok(catalogue.length > 1, 'The tour picker should include the abdomen sweeps.');
  const sweepPicker = page.getByRole('combobox', { name: 'Sweep' });
  assert.deepEqual(await sweepPicker.locator('option').evaluateAll((nodes) => nodes.map(node => node.value)),
    catalogue.map((tour) => tour.id));

  for (const tour of catalogue) {
    await sweepPicker.selectOption(tour.id);
    await page.waitForURL((value) => value.searchParams.get('sweep') === tour.id);
    await ready();
    assert.equal(await page.locator('#tourTitle').textContent(), tour.title);
    if (captureFolder && tour.id === 'kidney-left') {
      await preset('coronal').click();
      await capture('left-kidney-coronal-1021x1197');
    }
    assert.equal(await page.locator('#atlasSource').evaluate((node) => node.hidden), !tour.usesAtlas);
    assert.deepEqual(await page.locator('#sceneLegend li').allTextContents(), ['Imaging sector', ...tour.parts]);
    for (let i = 0; i < tour.keys.length; i += 1) {
      const key = tour.keys[i];
      await page.locator('#ticks button').nth(i).click();
      const expectedScan = new URL(tour.assetRoot + 'media/scan-' + String(key.frame).padStart(2, '0') + '.webp', page.url()).href;
      const expectedReference = new URL(key.path, page.url()).href;
      await page.waitForFunction(({ scan, reference }) => document.querySelector('#scan')?.src === scan
        && document.querySelector('#ref')?.src === reference, { scan: expectedScan, reference: expectedReference });
      assert.equal(await page.locator('#readout').textContent(), key.label);
      assert.ok((await page.locator('#referenceNote').textContent()).includes(key.referenceLabel));
    }
    if (tour.keys.length === 2 && tour.keys[1].frame - tour.keys[0].frame > 1) {
      const [first, last] = tour.keys;
      const position = page.getByRole('slider', { name: 'Sweep position' });
      for (const [frame, key] of [[first.frame + 1, first], [last.frame - 1, last]]) {
        await position.fill(String(frame));
        await page.waitForFunction(({ frame, label }) => document.querySelector('#scan')?.src.endsWith('scan-' + String(frame).padStart(2, '0') + '.webp')
          && document.querySelector('#referenceNote').textContent === 'Nearest reference · ' + label,
        { frame, label: key.referenceLabel });
      }
      await page.locator('#shortTick').click();
    }
    await page.locator('#section').click();
    await page.waitForFunction(() => document.querySelector('#scan')?.src.includes('/section-'));
    await page.locator('#assetTab').click();
    assert.deepEqual(await page.locator('#assetControls button').allTextContents(),
      ['3D anatomy', 'Simulated scan', 'Acquired ultrasound']);
    assert.equal(await page.locator('#assetEvidence canvas').count(), 1);
    const sources = () => page.locator('#assetSources a').evaluateAll((links) => links.map((link) => link.href));
    assert.deepEqual(await sources(), [
      ...(tour.usesAtlas ? ['https://dbarchive.biosciencedbc.jp/en/bodyparts3d/desc.html'] : []),
      'https://zenodo.org/records/10047263',
    ]);
    await page.locator('[data-asset="simulation"]').click();
    await page.waitForFunction(() => document.querySelector('#assetEvidence img')?.src.includes('/scan-'));
    assert.deepEqual(await sources(), ['https://zenodo.org/records/10047263']);
    await page.locator('[data-asset="acquired"]').click();
    const selected = tour.keys.at(-1);
    await page.waitForFunction((src) => document.querySelector('#assetEvidence img')?.src === src,
      new URL(selected.path, page.url()).href);
    assert.ok((await sources()).includes(new URL(selected.url, page.url()).href));
    const related = page.locator('#relatedAnatomy');
    const primaryPaths = new Set(tour.keys.map((key) => new URL(key.path, page.url()).href));
    const landmarkPaths = new Set(tour.landmarks.filter((landmark) => landmark.path).map((landmark) => new URL(landmark.path, page.url()).href));
    for (const path of primaryPaths) landmarkPaths.delete(path);
    assert.equal(await related.isVisible(), landmarkPaths.size > 0);
    if (landmarkPaths.size) {
      assert.equal(await related.locator('figure').count(), 0);
      await related.locator('summary').click();
      await page.waitForFunction(() => document.querySelector('#relatedPlates').getAttribute('aria-busy') === 'false'
        && document.querySelector('#relatedPlates figure img'));
      assert.deepEqual(await related.locator('figure img').evaluateAll((images) => images.map((image) => image.src)), [...landmarkPaths]);
      assert.ok(await related.locator('figcaption a').count() >= landmarkPaths.size);
      for (const landmark of tour.landmarks.filter((item) => item.path && item.reason)) {
        assert.ok((await related.locator('figcaption').allTextContents()).some((caption) => caption.includes(landmark.reason)));
        if (landmark.note) assert.ok((await page.locator('#referenceSources').textContent()).includes(landmark.note));
      }
      if (tour.id === 'liver') {
        const widths = await related.locator('figure img').evaluateAll((images) =>
          images.map((image) => image.getBoundingClientRect().width));
        assert.ok(widths.every((width) => width >= 280 && width <= 400), 'Related images should remain readable near source resolution.');
        await capture('liver-related-anatomy-1021', true);
      }
    }
    await page.locator('#return').click();
    assert.equal(await page.locator('#position').inputValue(), String(tour.keys.at(-1).frame));
  }

  await page.goBack();
  await ready();
  assert.equal(await sweepPicker.inputValue(), catalogue.at(-2).id);
  await page.goForward();
  await ready();
  assert.equal(await sweepPicker.inputValue(), catalogue.at(-1).id);

  const gallbladder = catalogue.find((tour) => tour.id === 'gallbladder');
  await page.goto(new URL('#guided', url).href);
  await ready();
  assert.equal(await sweepPicker.inputValue(), 'gallbladder');
  assert.equal(await page.locator('#position').inputValue(), '0');
  await page.goto(new URL('#probe', url).href);
  await ready();
  assert.equal(await page.locator('#position').inputValue(), String(gallbladder.keys[0].frame));
  const invalid = new URL(url);
  invalid.searchParams.set('sweep', 'missing-tour');
  await page.goto(invalid.href);
  await ready();
  assert.equal(await sweepPicker.inputValue(), 'gallbladder');

  await page.route('**/scan-12.webp', (route) => route.abort());
  await page.reload();
  await page.getByText('Scan unavailable for this frame.').waitFor();
  await page.locator('#shortTick').click();
  await page.waitForFunction(() => document.querySelector('#scan')?.src.endsWith('scan-48.webp'));
  await page.unroute('**/scan-12.webp');
  const missingReference = new URL(gallbladder.keys[0].path, page.url()).href;
  await page.route(missingReference, (route) => route.abort());
  await page.reload();
  await page.getByText('Clinical reference unavailable.').waitFor();
  await page.waitForFunction(() => document.querySelector('#scan')?.src.endsWith('scan-12.webp'));
  await page.unroute(missingReference);

  const delayedReference = new URL(gallbladder.keys.at(-1).path, page.url()).href;
  let releaseReference;
  const waitingReference = new Promise((resolve) => { releaseReference = resolve; });
  await page.route(delayedReference, async (route) => {
    await waitingReference;
    await route.continue();
  });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.click('#assetTab');
  await page.locator('[data-asset="acquired"]').click();
  const selection = page.locator('#assetFrame');
  await selection.selectOption(String(gallbladder.keys.at(-1).frame));
  await page.getByText('Loading image…').waitFor();
  await selection.selectOption(String(gallbladder.keys[0].frame));
  const settledReference = new URL(gallbladder.keys[0].path, page.url()).href;
  await page.waitForFunction((src) => document.querySelector('#assetEvidence img')?.src === src, settledReference);
  releaseReference();
  await page.waitForFunction(() => !document.querySelector('#play').disabled);
  assert.equal(await page.locator('#assetEvidence img').evaluate((image) => image.src), settledReference);
  await page.unroute(delayedReference);

  const withLandmarks = catalogue.find((tour) => tour.landmarks.some((landmark) => landmark.path));
  if (withLandmarks) {
    const landmark = withLandmarks.landmarks.find((item) => item.path);
    const here = new URL(url);
    here.searchParams.set('sweep', withLandmarks.id);
    const path = new URL(landmark.path, here).href;
    const cataloguePath = new URL('abdomen-tours.js', here).href;
    await page.route(cataloguePath, async (route) => {
      const response = await route.fetch();
      const text = await response.text();
      const duplicateData = JSON.stringify([landmark.id, landmark.id, withLandmarks.keys[0].referenceId, 'missing-reference']);
      await route.fulfill({
        response,
        body: text + '\nabdomenTours.find(tour => tour.id === ' + JSON.stringify(withLandmarks.id)
          + ').landmarks.push(...' + duplicateData + ');',
      });
    });
    let release;
    const delayed = new Promise((resolve) => { release = resolve; });
    await page.route(path, async (route) => {
      await delayed;
      await route.continue();
    });
    await page.goto(here.href);
    await ready();
    const related = page.locator('#relatedAnatomy');
    await page.click('#assetTab');
    const fetching = page.waitForRequest(path);
    await related.locator('summary').click();
    await fetching;
    await page.click('#return');
    const response = page.waitForResponse(path);
    release();
    await response;
    await page.evaluate(async (path) => {
      await prepare(path).pending;
      await new Promise(requestAnimationFrame);
    }, landmark.path);
    assert.equal(await related.locator('figure').count(), 0, 'A hidden review should not receive stale images.');
    await page.click('#assetTab');
    await page.waitForFunction(() => document.querySelector('#relatedPlates').getAttribute('aria-busy') === 'false');
    const shownPaths = await related.locator('figure img').evaluateAll((images) => images.map((image) => image.src));
    assert.equal(shownPaths.filter((src) => src === path).length, 1, 'Repeated plate IDs should render once.');
    assert.ok(!shownPaths.includes(new URL(withLandmarks.keys[0].path, here).href), 'A keyframe comparison should not repeat as a related plate.');
    await page.unroute(path);
    await page.unroute(cataloguePath);

    await page.route(path, (route) => route.abort());
    await page.reload();
    await ready();
    await page.click('#assetTab');
    await related.locator('summary').click();
    await related.getByText('Image unavailable.').waitFor();
    assert.ok(await related.locator('figcaption a').count() > 0, 'An unavailable plate should retain its source credit.');
    await page.unroute(path);
  }
  const other = catalogue.find((tour) => tour.id !== 'gallbladder');
  const missingScript = new URL(other.assetRoot + 'sweep.js', page.url()).href;
  await page.route(missingScript, (route) => route.abort());
  await sweepPicker.selectOption(other.id);
  await page.getByText('This sweep is unavailable.').waitFor();
  await sweepPicker.selectOption('gallbladder');
  await ready();
  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    'The sweep should reflow without horizontal scrolling.');
  assert.ok(await preset('sagittal').isVisible());
  assert.deepEqual(errors, []);
  console.log('Camera presets, playback layout, ' + catalogue.length + ' sweep routes, and asset recovery passed. Maximum shift: ' + result.maxShift + ' px.');
} finally {
  await browser.close();
}
