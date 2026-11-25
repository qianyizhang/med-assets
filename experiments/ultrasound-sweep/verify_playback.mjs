// Exercise the actual playback controls at the viewport where the readout shifted.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
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
  const sceneWarnings = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'warning') sceneWarnings.push(message.text());
  });
  await page.goto(url);
  const ready = async () => {
    try {
      await page.waitForFunction(() =>
        document.querySelector('#cameraPresets')?.disabled === false && document.querySelector('#play')?.disabled === false);
    } catch (cause) {
      const status = await page.locator('#tourStatus, #sceneStatus, #play').evaluateAll((nodes) =>
        nodes.map((node) => [node.textContent.trim(), node.hidden, node.disabled]));
      throw new Error('Viewer did not become ready at ' + page.url() + '. ' + JSON.stringify(status)
        + ' Warnings ' + sceneWarnings.slice(-5).join(' | '), { cause });
    }
  };
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
    region: tour.bodyRegion ?? 'Abdomen',
    stage: tour.pregnancyStage,
    probeType: tour.probeType,
    fieldShape: tour.fieldShape,
    additionalSources: (tour.additionalAnatomySources ?? []).map((source) => source.url),
    referenceContext: tour.referenceContext ?? 'Different case',
    depth: tour.sectorDepthMm ?? 133,
    showRoute: tour.showRoute ?? false,
    steering: tour.steering,
    compressionMm: tour.compressionMm,
    initialFrame: tour.initialFrame ?? tour.keyframes[0].frame,
    anatomySource: tour.anatomySource ?? {
      label: 'TotalSegmentator ' + (tour.case ?? 's1233') + ', Jakob Wasserthal and colleagues',
      url: 'https://zenodo.org/records/10047263',
    },
    usesAtlas: tour.exterior ? tour.exterior === 'fitted-atlas' : tour.id === 'gallbladder',
    parts: tour.parts.map((part) => part.label),
    landmarks: (tour.landmarks ?? []).map((id) => ({ id, ...abdomenReferences[id] })),
    keys: tour.keyframes.map((key) => {
      const reference = abdomenReferences[key.referenceId];
      return { frame: key.frame, detail: key.detail, label: key.label, referenceId: key.referenceId, path: reference.path, url: reference.url,
        referenceLabel: key.referenceLabel ?? reference.label ?? key.label, depthLabel: reference.depthLabel };
    }),
  })));
  assert.ok(catalogue.length > 1, 'The tour picker should include the abdomen sweeps.');
  const thyroidTours = catalogue.filter((tour) => tour.region === 'Neck' && tour.keys.length === 3);
  if (thyroidTours.length > 1) {
    assert.equal(new Set(thyroidTours.map((tour) => tour.keys[0].referenceId)).size, 1,
      'Both thyroid tours should share the acquired midline reference.');
  }
  const sweepPicker = page.getByRole('combobox', { name: 'Sweep' });
  const expectedRegions = new Map();
  for (const tour of catalogue) {
    const label = tour.stage ? 'Pregnancy · ' + tour.stage.age : tour.region;
    if (!expectedRegions.has(label)) expectedRegions.set(label, []);
    expectedRegions.get(label).push(tour.id);
  }
  assert.deepEqual(await sweepPicker.locator('optgroup').evaluateAll((groups) =>
    groups.map((group) => [group.label, [...group.children].map((option) => option.value)])), [...expectedRegions]);

  async function assertSeparatedTicks() {
    const bounds = await page.locator('#ticks button').evaluateAll(nodes => nodes.map(node => {
      const rect = node.getBoundingClientRect();
      return [rect.left, rect.right];
    }));
    assert.ok(bounds.every(([left], i) => !i || bounds[i-1][1] <= left + 1), 'Reference buttons overlap');
  }

  for (const tour of catalogue) {
    await sweepPicker.selectOption(tour.id);
    await page.waitForURL((value) => value.searchParams.get('sweep') === tour.id);
    await ready();
    assert.equal(await page.locator('#tourTitle').textContent(), tour.title);
    assert.equal(await page.locator('#position').inputValue(), String(tour.initialFrame));
    if (tour.region === 'Breast') {
      assert.ok(await page.evaluate(() => sweep.every(({ contactRig }) =>
        contactRig && contactRig.surfaceMm.length === contactRig.elevationMm.length
        && contactRig.surfaceMm.every((row) => row.length === contactRig.lateralMm.length)
        && contactRig.lateralMm.length >= 17 && contactRig.elevationMm.length >= 9)),
      tour.id + ' must register the contact field at every pose.');
    }
    const routeNav = page.getByRole('navigation', { name: 'Breast scan routes' });
    const regional = catalogue.filter((candidate) => candidate.region === 'Breast');
    assert.equal(await routeNav.isVisible(), tour.region === 'Breast' && regional.length > 1);
    if (await routeNav.isVisible()) {
      assert.deepEqual(await routeNav.getByRole('link').evaluateAll((links) =>
        links.map((link) => new URL(link.href).searchParams.get('sweep'))), regional.map((candidate) => candidate.id));
      assert.equal(await routeNav.locator('a[aria-current="page"]').count(), 1);
      assert.equal(new URL(await routeNav.locator('a[aria-current="page"]').getAttribute('href')).searchParams.get('sweep'), tour.id);
    }
    const pathControl = page.getByRole('button', { name: 'Scan path' });
    assert.equal(await pathControl.isVisible(), tour.showRoute);
    if (tour.showRoute) {
      assert.equal(await pathControl.getAttribute('aria-pressed'), 'true');
      const visible = await screenshot();
      await pathControl.click();
      assert.equal(await pathControl.getAttribute('aria-pressed'), 'false');
      assert.notDeepEqual(await screenshot(), visible, 'Toggling the scan path should change the rendered canvas.');
      await pathControl.click();
      assert.deepEqual(await screenshot(), visible);
      if (tour.region === 'Breast') await capture(tour.id + '-scan-path-1021', true);
    }
    assert.equal(await page.locator('#pregnancyNavigation').isVisible(), Boolean(tour.stage));
    if (tour.stage) {
      await assertSeparatedTicks();
      await page.setViewportSize({width: 390, height: 844});
      await assertSeparatedTicks();
      await page.setViewportSize({width: 1021, height: 1197});
      const ages = [...new Set(catalogue.filter(item => item.stage).map(item => item.stage.age))];
      assert.deepEqual(await page.locator('#pregnancyStages strong').allTextContents(), ages);
      assert.equal(await page.locator('#pregnancyStages [aria-current] strong').textContent(), tour.stage.age);
      const siblings = catalogue.filter(item => item.stage?.age === tour.stage.age);
      if (siblings.length > 1) {
        assert.equal(await page.locator('#pregnancyRoutes [aria-current]').getAttribute('href'), page.url());
        assert.deepEqual(await page.locator('#pregnancyRoutes a').evaluateAll(links =>
          links.map(link => new URL(link.href).searchParams.get('sweep'))), siblings.map(item => item.id));
      }
    }
    if (captureFolder && tour.id === 'kidney-left') {
      await preset('coronal').click();
      await capture('left-kidney-coronal-1021x1197');
    }
    assert.equal(await page.locator('#atlasSource').evaluate((node) => node.hidden), !tour.usesAtlas);
    assert.ok((await page.locator('#anatomySource').textContent()).includes(tour.anatomySource.label));
    const field = tour.fieldShape === 'rectangle' ? 'Imaging field' : 'Imaging sector';
    assert.deepEqual(await page.locator('#sceneLegend li').allTextContents(), [field, ...tour.parts]);
    const probeLabel = tour.probeType === 'linear' ? 'High-frequency linear array' : 'Curved array';
    const poseDepths = await page.evaluate(() => sweep.map(({ imagingDepthMm }) => imagingDepthMm ?? null));
    const depthText = (frame) => probeLabel + ' · ' + Number(((poseDepths[frame] ?? tour.depth) / 10).toFixed(2)) + ' cm depth';
    assert.equal(await page.locator('#scanDetail').textContent(), depthText(tour.initialFrame));
    if (tour.id === 'axilla') {
      assert.ok(poseDepths.every(Number.isFinite) && poseDepths[12] < poseDepths[48]);
      assert.notEqual(depthText(12), depthText(48));
    }
    if (tour.probeType === 'linear') {
      const skinOpacity = page.getByRole('slider', { name: 'Skin opacity' });
      assert.equal(await skinOpacity.inputValue(), '32');
      assert.match(await canvas.getAttribute('aria-label'), /rectangular imaging field.*patient orientation/);
      const defaultView = await screenshot();
      await preset('coronal').click();
      assert.notDeepEqual(await screenshot(), defaultView, 'Coronal and oblique views should have distinct projections.');
      await preset('oblique').click();
      assert.deepEqual(await screenshot(), defaultView, 'Reapplying the oblique preset should restore the default projection.');
      if (captureFolder && (tour.id === 'thyroid-right' || tour.region === 'Breast')) {
        await skinOpacity.fill('100');
        await page.locator('#scenePanel figcaption > span').click();
        await capture(tour.id + '-skin-100-1021', tour.region === 'Breast');
        await skinOpacity.fill('32');
      }
    }
    for (let i = 0; i < tour.keys.length; i += 1) {
      const key = tour.keys[i];
      await page.locator('#ticks button').nth(i).click();
      const expectedScan = new URL(tour.assetRoot + 'media/scan-' + String(key.frame).padStart(2, '0') + '.webp', page.url()).href;
      const expectedReference = new URL(key.path, page.url()).href;
      await page.waitForFunction(({ scan, reference }) => document.querySelector('#scan')?.src === scan
        && document.querySelector('#ref')?.src === reference, { scan: expectedScan, reference: expectedReference })
        .catch(async (cause) => {
          const actual = await page.locator('#scanArea, #referenceArea').evaluateAll((areas) =>
            areas.map((area) => area.querySelector('img')?.src ?? area.textContent.trim()));
          throw new Error(tour.id + ' frame ' + key.frame + ' did not load the expected scan and reference. ' + actual.join(' | '), { cause });
        });
      assert.equal(await page.locator('#readout').textContent(), key.label);
      assert.equal(await page.locator('#scanDetail').textContent(), depthText(key.frame));
      assert.ok((await page.locator('#referenceNote').textContent()).includes(key.referenceLabel));
      assert.equal(await page.locator('#referenceDepth').textContent(), [tour.referenceContext, key.depthLabel].filter(Boolean).join(' · '));
      if (tour.region === 'Breast') await capture(tour.id + '-frame-' + key.frame + '-1021', true);
      if (tour.region === 'Pregnancy') {
        await capture(tour.id + '-' + key.frame);
        await page.locator('#section').click();
        await page.waitForFunction(() => document.querySelector('#scan')?.src.includes('/section-'));
        await capture(tour.id + '-' + key.frame + '-section');
        if (key.detail) {
          const fullField = await screenshot();
          await page.locator('#scanZoom').click();
          await page.waitForFunction(() => document.querySelector('#scan')?.src.includes('/detail-section-'));
          assert.notDeepEqual(await screenshot(), fullField, 'Magnification should outline its physical bounds in the 3D field.');
          await capture(tour.id + '-' + key.frame + '-magnified');
          assert.equal(await page.locator('#position').inputValue(), String(key.frame));
          assert.equal(await page.locator('#ref').evaluate(img => img.src), new URL(key.path, page.url()).href);
          await page.locator('#section').click();
          await page.waitForFunction(() => document.querySelector('#scan')?.src.includes('/detail-scan-'));
          await page.locator('#scanZoom').click();
          await page.waitForFunction(() => document.querySelector('#scan')?.src.includes('/media/scan-'));
          assert.deepEqual(await screenshot(), fullField, 'Returning to the full field should remove the magnification outline.');
          await page.locator('#section').click();
        }
        await page.locator('#section').click();
      }
      if (tour.region === 'Neck' && tour.keys.length === 3) {
        if (key.frame === 0 && tour.id === 'thyroid-right') await capture('thyroid-midline-1021x1197');
        if (key.frame === 12) await capture(tour.id + '-transverse-1021x1197');
        if (key.frame === 48) await capture(tour.id + '-longitudinal-1021x1197');
      }
    }
    const position = page.getByRole('slider', { name: 'Sweep position' });
    for (let i = 1; !tour.steering && i < tour.keys.length; i += 1) {
      const first = tour.keys[i - 1];
      const last = tour.keys[i];
      if (last.frame - first.frame <= 2) continue;
      for (const [frame, key] of [[first.frame + 1, first], [last.frame - 1, last]]) {
        await position.fill(String(frame));
        await page.waitForFunction(({ frame, label }) => document.querySelector('#scan')?.src.endsWith('scan-' + String(frame).padStart(2, '0') + '.webp')
          && document.querySelector('#referenceNote').textContent === 'Nearest reference · ' + label,
        { frame, label: key.referenceLabel });
      }
    }
    if (tour.region === 'Neck' && tour.keys.length === 3) {
      assert.deepEqual(tour.keys.map((key) => key.frame), [0, 12, 48]);
      assert.equal(tour.initialFrame, 12);
      const ticks = page.locator('#ticks button');
      const assertTickLayout = async () => {
        const bounds = await ticks.evaluateAll((nodes) => nodes.map((node) => {
          const { left, right, width, bottom } = node.getBoundingClientRect();
          return { left, right, width, bottom, rowBottom: node.parentElement.getBoundingClientRect().bottom };
        }));
        assert.ok(bounds.every((rect, i) => !i || rect.left >= bounds[i - 1].right));
        assert.ok(bounds.every(({ width, bottom, rowBottom }) => width >= 36 && bottom <= rowBottom),
          'Each tick label should remain inside its own readable button.');
      };
      await assertTickLayout();
      await page.setViewportSize({ width: 390, height: 844 });
      await assertTickLayout();
      for (let i = 0; i < tour.keys.length; i += 1) {
        await ticks.nth(i).click();
        assert.equal(await position.inputValue(), String(tour.keys[i].frame));
      }
      await page.setViewportSize({ width: 1021, height: 1197 });
    }
    await page.locator('#ticks button').last().click();
    await page.locator('#section').click();
    await page.waitForFunction(() => document.querySelector('#scan')?.src.includes('/section-'));
    await page.locator('#assetTab').click();
    assert.deepEqual(await page.locator('#assetControls button').allTextContents(),
      ['3D anatomy', 'Simulated scan', 'Acquired ultrasound']);
    assert.equal(await page.locator('#assetEvidence canvas').count(), 1);
    const sources = () => page.locator('#assetSources a').evaluateAll((links) => links.map((link) => link.href));
    assert.deepEqual(await sources(), [
      ...(tour.usesAtlas ? ['https://dbarchive.biosciencedbc.jp/en/bodyparts3d/desc.html'] : []),
      tour.anatomySource.url, ...tour.additionalSources,
    ]);
    await page.locator('[data-asset="simulation"]').click();
    await page.waitForFunction(() => document.querySelector('#assetEvidence img')?.src.includes('/scan-'));
    assert.deepEqual(await sources(), [tour.anatomySource.url, ...tour.additionalSources]);
    if (tour.id === 'breast' || tour.region === 'Pregnancy') {
      assert.doesNotMatch(await page.locator('#assetFinding').innerText(), /CT-derived|from the CT/i);
      assert.doesNotMatch(await page.locator('#anatomySource').textContent(), /TotalSegmentator|CT-derived/i);
    }
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
    let returnFrame = tour.keys.at(-1).frame;
    if (tour.region === 'Neck' && tour.keys.length === 3) {
      const midline = tour.keys[0];
      returnFrame = midline.frame;
      await page.locator('#assetFrame').selectOption(String(returnFrame));
      await page.waitForFunction((src) => document.querySelector('#assetEvidence img')?.src === src,
        new URL(midline.path, page.url()).href);
      if (await related.isVisible()) {
        const extras = await related.locator('figure img').evaluateAll((images) => images.map((image) => image.src));
        assert.ok(!extras.includes(new URL(midline.path, page.url()).href), 'A primary midline reference should not repeat in Related anatomy.');
      }
    }
    await page.locator('#return').click();
    assert.equal(await page.locator('#position').inputValue(), String(returnFrame));
  }

  await page.goBack();
  await ready();
  assert.equal(await sweepPicker.inputValue(), catalogue.at(-2).id);
  await page.goForward();
  await ready();
  assert.equal(await sweepPicker.inputValue(), catalogue.at(-1).id);

  const axilla = catalogue.find((tour) => tour.id === 'axilla');
  if (axilla) {
    const axillaUrl = new URL(url);
    axillaUrl.searchParams.set('sweep', axilla.id);
    await page.goto(axillaUrl.href);
    await ready();
    assert.equal(await page.locator('#position').inputValue(), '12');
    const shallow = await screenshot();
    const poseScript = new URL(axilla.assetRoot + 'sweep.js', page.url()).href;
    await page.route(poseScript, async (route) => {
      const response = await route.fetch();
      const source = (await response.text()).trim();
      const frames = JSON.parse(source.slice('const sweep = '.length, -1));
      frames[12].imagingDepthMm = frames[48].imagingDepthMm;
      await route.fulfill({ response, body: 'const sweep = ' + JSON.stringify(frames) + ';' });
    });
    await page.reload();
    await ready();
    assert.equal(await page.locator('#position').inputValue(), '12');
    assert.notDeepEqual(await screenshot(), shallow, 'Changing only the modeled depth must change the rendered field.');
    await page.unroute(poseScript);
  }

  const screening = catalogue.find((tour) => tour.id === 'aortic-screening');
  if (screening) {
    const screeningUrl = new URL(url);
    screeningUrl.searchParams.set('sweep', screening.id);
    await page.goto(screeningUrl.href);
    await ready();
    assert.deepEqual(screening.keys.map(({ frame }) => frame), [12, 30, 48]);
    assert.equal(screening.initialFrame, 12);
    const spans = await page.evaluate(() => sweep.map(({ apSpan }) => apSpan));
    assert.ok(spans.every((span) => span?.millimetres > 0 && span.endpointsPx.length === 2));
    const ap = page.getByRole('button', { name: 'AP span' });
    const marks = page.locator('#apMarks');
    const readout = page.locator('#apReadout');
    const position = page.locator('#position');
    const section = page.locator('#section');
    const media = (frame, kind = 'scan') => new URL(
      screening.assetRoot + 'media/' + kind + '-' + String(frame).padStart(2, '0') + '.webp', screeningUrl,
    ).href;
    const waitFrame = (frame, kind) => page.waitForFunction((src) => document.querySelector('#scan')?.src === src, media(frame, kind));
    async function assertMarks(frame) {
      const { endpointsPx: [[x1, y1], [x2, y2]], millimetres } = spans[frame];
      assert.equal(await ap.getAttribute('aria-pressed'), 'true');
      assert.ok(await marks.isVisible());
      assert.ok(await readout.isVisible());
      assert.equal(await readout.textContent(), 'Modeled AP span · ' + millimetres.toFixed(1) + ' mm');
      assert.equal(await page.locator('#apChord').getAttribute('d'), `M ${x1} ${y1} L ${x2} ${y2}`);
      const caps = (await page.locator('#apEnds').getAttribute('d')).match(/-?\d+(?:\.\d+)?/g).map(Number);
      assert.equal(caps.length, 8);
      for (const [index, [x, y]] of spans[frame].endpointsPx.entries()) {
        const [a, b, c, d] = caps.slice(index * 4, index * 4 + 4);
        assert.ok(Math.abs((a + c) / 2 - x) < .001 && Math.abs((b + d) / 2 - y) < .001);
        assert.ok(Math.abs(Math.hypot(a - c, b - d) - 10) < .001);
      }
      assert.ok(await marks.evaluate((wrapper) => {
        const svg = wrapper.querySelector('svg');
        const image = document.querySelector('#scan');
        const rect = image.getBoundingClientRect();
        const scale = Math.min(rect.width / image.naturalWidth, rect.height / image.naturalHeight);
        const matrix = svg.getScreenCTM();
        return image.naturalWidth === 500 && image.naturalHeight === 350
          && Math.abs(matrix.a - scale) < .001 && Math.abs(matrix.d - scale) < .001
          && Math.abs(matrix.e - rect.left - (rect.width - 500 * scale) / 2) < 1
          && Math.abs(matrix.f - rect.top - (rect.height - 350 * scale) / 2) < 1;
      }), 'Calipers should share the displayed image coordinates, including letterboxing.');
    }
    assert.equal(await ap.getAttribute('aria-pressed'), 'false');
    assert.equal(await marks.isVisible(), false);
    assert.equal(await readout.isVisible(), false);
    await capture('aortic-screening-unmarked-1021x1197', true);
    await ap.click();
    await assertMarks(screening.initialFrame);
    for (const [index, { frame }] of screening.keys.entries()) {
      await page.locator('#ticks button').nth(index).click();
      await waitFrame(frame);
      await assertMarks(frame);
    }
    await position.fill('29');
    await waitFrame(29);
    await assertMarks(29);
    await page.setViewportSize({ width: 390, height: 844 });
    await assertMarks(29);
    await page.setViewportSize({ width: 1021, height: 1197 });
    await page.locator('#ticks button').nth(1).click();
    await section.click();
    await waitFrame(30, 'section');
    await assertMarks(30);
    await capture('aortic-screening-marked-section-1021x1197', true);
    await page.locator('#assetTab').click();
    await page.locator('#return').click();
    await waitFrame(30, 'section');
    await assertMarks(30);

    let releaseInitial;
    const heldInitial = new Promise((resolve) => { releaseInitial = resolve; });
    let release;
    const held = new Promise((resolve) => { release = resolve; });
    await page.route(media(screening.initialFrame), async (route) => {
      await heldInitial;
      await route.continue();
    });
    await page.route(media(30), async (route) => {
      await held;
      await route.continue();
    });
    await page.route(media(48), (route) => route.abort());
    try {
      await page.reload({ waitUntil: 'domcontentloaded' });
      await ap.click();
      assert.equal(await marks.isVisible(), false);
      assert.equal(await readout.isVisible(), false);
      releaseInitial();
      await waitFrame(screening.initialFrame);
      await assertMarks(screening.initialFrame);
      await page.locator('#ticks button').nth(1).click();
      await page.waitForFunction(() => document.querySelector('#scanArea').getAttribute('aria-busy') === 'true');
      await assertMarks(screening.initialFrame);
      release();
      await waitFrame(30);
      await assertMarks(30);
      await page.locator('#ticks button').last().click();
      await page.getByText('Scan unavailable for this frame.').waitFor();
      assert.equal(await marks.isVisible(), false);
      assert.equal(await readout.isVisible(), false);
      assert.equal(await ap.getAttribute('aria-pressed'), 'true');
      await page.locator('#ticks button').nth(1).click();
      await waitFrame(30);
      await assertMarks(30);
    } finally {
      releaseInitial();
      release();
      await page.unroute(media(screening.initialFrame));
      await page.unroute(media(30));
      await page.unroute(media(48));
    }
    const aortaNav = page.getByRole('navigation', { name: 'Abdominal aorta scan routes' });
    const aortaLinks = aortaNav.getByRole('link');
    const destinations = await aortaLinks.evaluateAll((nodes) => nodes.map((link) => new URL(link.href).searchParams.get('sweep')));
    assert.deepEqual(new Set(destinations), new Set(['aorta', screening.id]));
    await aortaLinks.nth(destinations.indexOf('aorta')).click();
    await page.waitForURL((location) => location.searchParams.get('sweep') === 'aorta');
    await ready();
    assert.equal(await ap.isVisible(), false);
    await page.goBack();
    await ready();
    assert.equal(await sweepPicker.inputValue(), screening.id);
    assert.ok(await ap.isVisible());
  }

  const steered = catalogue.find((tour) => tour.steering);
  if (steered) {
    const startURL = new URL(url);
    startURL.searchParams.set('sweep', steered.id);
    await page.goto(startURL.href);
    await ready();
    const { axes, cells } = steered.steering;
    const range = axes.map(({ label }) => page.getByRole('slider', { name: label, exact: true }));
    const expectedCount = axes.reduce((count, axis) => count * axis.values.length, 1);
    assert.deepEqual(axes.map((axis) => axis.values.length), [3, 5, 3]);
    assert.equal(cells.length, expectedCount);
    assert.equal(new Set(cells.map((cell) => cell.indices.join('/'))).size, expectedCount);
    assert.equal(new Set(cells.map((cell) => cell.frame)).size, expectedCount);
    const position = page.getByRole('slider', { name: 'Sweep position' });
    const scanFor = (frame, prefix = 'scan') => new URL(
      steered.assetRoot + 'media/' + prefix + '-' + String(frame).padStart(2, '0') + '.webp', page.url(),
    ).href;
    const waitScan = (src) => page.waitForFunction((path) => document.querySelector('#scan')?.src === path, src);
    const registered = await page.evaluate(() => Boolean(sweep[0].contactRig));
    const currentIndices = async () => Promise.all(range.map(async (slider) => Number(await slider.inputValue())));
    const panelPositions = () => page.locator('#steering, #scanArea, #referenceArea').evaluateAll((nodes) =>
      nodes.map((node) => node.getBoundingClientRect().top + scrollY));
    const fixedPositions = await panelPositions();
    const renderedCells = new Set();
    for (const cell of cells) {
      const previous = await currentIndices();
      for (let axis = 0; axis < range.length; axis += 1) {
        if (previous[axis] !== cell.indices[axis]) await range[axis].fill(String(cell.indices[axis]));
      }
      await waitScan(scanFor(cell.frame));
      assert.equal(await position.inputValue(), String(cell.frame));
      assert.deepEqual(await currentIndices(), cell.indices);
      (await panelPositions()).forEach((top, i) => {
        assert.ok(Math.abs(top - fixedPositions[i]) < 1, 'Steering values should not shift the scan panels.');
      });
      const digest = createHash('sha256').update(await screenshot()).digest('hex');
      assert.ok(!renderedCells.has(digest), 'Distinct steering poses should render distinct geometry.');
      renderedCells.add(digest);
      for (let axis = 0; axis < range.length; axis += 1) {
        const value = Number(axes[axis].values[cell.indices[axis]].toFixed(1));
        const unit = axes[axis].unit;
        assert.equal(await range[axis].getAttribute('aria-valuetext'), value + (unit === '°' ? unit : ' ' + unit));
      }
    }

    await preset('oblique').click();
    const rendered = await screenshot();
    const candidatePixels = await page.evaluate(async (png) => {
      const input = new Image();
      input.src = 'data:image/png;base64,' + png;
      await input.decode();
      const copy = document.createElement('canvas');
      copy.width = input.naturalWidth;
      copy.height = input.naturalHeight;
      const ctx = copy.getContext('2d');
      ctx.drawImage(input, 0, 0);
      const { width, height } = copy;
      const { data } = ctx.getImageData(0, 0, width, height);
      const candidates = [];
      for (let y = Math.round(height * .22); y < height * .78; y += 8) {
        for (let x = Math.round(width * .21); x < width * .79; x += 8) {
          const i = (y * width + x) * 4;
          const [r, g, b] = data.slice(i, i + 3);
          if (r > 148 && g > 155 && b > 150 && Math.max(r, g, b) - Math.min(r, g, b) < 36) {
            candidates.push({ x: x / width, y: y / height, brightness: r + g + b });
          }
        }
      }
      return candidates.sort((a, b) => b.brightness - a.brightness).slice(0, 40);
    }, rendered.toString('base64'));
    const canvasRect = await canvas.boundingBox();
    let hit;
    for (const pixel of candidatePixels) {
      const x = canvasRect.x + pixel.x * canvasRect.width;
      const y = canvasRect.y + pixel.y * canvasRect.height;
      await page.mouse.move(x, y);
      if ((await canvas.evaluate(node => getComputedStyle(node).cursor)) === 'move') {
        hit = { x, y };
        break;
      }
    }
    assert.ok(hit, 'The visible probe should expose a direct-drag affordance.');
    const beforeDrag = await currentIndices();
    const lateralDirection = beforeDrag[0] === 0 ? 1 : -1;
    const verticalDirection = beforeDrag[2] === 0 ? -1 : 1;
    await page.mouse.down();
    await page.mouse.move(hit.x + 35 * lateralDirection, hit.y + 28 * verticalDirection, { steps: 4 });
    await page.mouse.up();
    const destination = cells.find((cell) => cell.indices[0] === beforeDrag[0] + lateralDirection
      && cell.indices[1] === beforeDrag[1] && cell.indices[2] === beforeDrag[2] - verticalDirection);
    await waitScan(scanFor(destination.frame));
    assert.equal(await preset('oblique').getAttribute('aria-pressed'), 'true', 'Probe drag should not orbit the camera.');

    if (steered.compressionMm) {
      const pressure = page.getByRole('button', { name: 'Firmer pressure' });
      const key = steered.keys.at(-1);
      await page.locator('#ticks button').last().click();
      await waitScan(scanFor(key.frame));
      const comparison = new URL(key.path, page.url()).href;
      const unpressedView = await screenshot();
      await pressure.click();
      await waitScan(scanFor(key.frame, 'press-scan'));
      assert.notDeepEqual(await screenshot(), unpressedView, 'Firmer pressure should change the 3D geometry.');
      await capture(steered.id + '-firmer-pressure-1021', true);
      assert.equal(await pressure.getAttribute('aria-pressed'), 'true');
      assert.equal(await position.inputValue(), String(key.frame));
      assert.equal(await page.locator('#ref').evaluate((img) => img.src), comparison);
      assert.ok((await page.locator('#scanDetail').textContent()).includes(
        Number(((steered.depth - steered.compressionMm) / 10).toFixed(2)) + ' cm depth',
      ));
      await page.locator('#section').click();
      await waitScan(scanFor(key.frame, 'press-section'));
      await page.locator('#section').click();
      await waitScan(scanFor(key.frame, 'press-scan'));
      await page.locator('#assetTab').click();
      await page.locator('[data-asset="simulation"]').click();
      await page.waitForFunction((path) => document.querySelector('#assetEvidence img')?.src === path,
        scanFor(key.frame, 'press-scan'));
      await page.locator('#return').click();
      assert.equal(await pressure.getAttribute('aria-pressed'), 'true');
      assert.equal(await position.inputValue(), String(key.frame));
      await waitScan(scanFor(key.frame, 'press-scan'));

      if (registered) {
        for (const pressed of [true, false]) {
          const prefix = pressed ? 'press-scan' : 'scan';
          const minimumSample = key.frame - 12;
          await position.fill(String(minimumSample - 3));
          await waitScan(scanFor(minimumSample - 3, prefix));
          const sample = await page.evaluate((minimumFrame) => new Promise((resolve, reject) => {
            const range = document.querySelector('#position');
            const playback = document.querySelector('#play');
            const scanArea = document.querySelector('#scanArea');
            const observer = new MutationObserver(() => {
              const frame = range.valueAsNumber;
              if (frame < minimumFrame) return;
              observer.disconnect();
              clearTimeout(timeout);
              if (playback.textContent === 'Pause') playback.click();
              resolve({ frame, src: scanArea.querySelector('img')?.src });
            });
            const timeout = setTimeout(() => {
              observer.disconnect();
              reject(new Error('Playback did not reach the sampled contact frame.'));
            }, 7000);
            observer.observe(scanArea, { childList: true, subtree: true, attributes: true });
            playback.click();
          }), minimumSample);
          assert.ok(sample.frame < key.frame, 'Playback should show an intermediate contact pose.');
          assert.equal(sample.src, scanFor(sample.frame, prefix));
          const played = await screenshot();
          await position.fill(String(sample.frame - 1));
          await waitScan(scanFor(sample.frame - 1, prefix));
          await position.fill(String(sample.frame));
          await waitScan(sample.src);
          assert.deepEqual(await screenshot(), played, 'Playback must render the same registered geometry as scrubbing to the baked frame.');
          if (pressed) {
            await pressure.click();
            await waitScan(scanFor(sample.frame));
          }
        }
        await position.fill(String(key.frame));
        await waitScan(scanFor(key.frame));
        assert.deepEqual(await screenshot(), unpressedView, 'Releasing registered pressure should restore the seated pose.');

        const skin = page.getByRole('slider', { name: 'Skin opacity' });
        await skin.fill('100');
        const seatedSkin = await screenshot();
        await capture(steered.id + '-seated-skin-100-1021', true);
        await pressure.click();
        await waitScan(scanFor(key.frame, 'press-scan'));
        assert.notDeepEqual(await screenshot(), seatedSkin, 'Pressure must also alter the opaque skin.');
        await capture(steered.id + '-pressed-skin-100-1021', true);
        await pressure.click();
        await waitScan(scanFor(key.frame));
        assert.deepEqual(await screenshot(), seatedSkin, 'The opaque skin should return to the seated pose.');
        await skin.fill('32');
      } else {
        await pressure.click();
        await waitScan(scanFor(key.frame));
        assert.deepEqual(await screenshot(), unpressedView, 'Releasing pressure should restore the original 3D pose.');
      }

      const missingPress = scanFor(key.frame, 'press-scan');
      await page.route(missingPress, (route) => route.abort());
      await page.reload();
      await ready();
      await page.locator('#ticks button').last().click();
      await waitScan(scanFor(key.frame));
      await pressure.click();
      await page.getByText('Scan unavailable for this frame.').waitFor();
      assert.equal(await page.locator('#ref').evaluate((img) => img.src), comparison);
      await pressure.click();
      await waitScan(scanFor(key.frame));
      await page.unroute(missingPress);
    }
    const nextRoute = catalogue.find((tour) => tour.region === 'Breast' && tour.id !== steered.id);
    if (nextRoute) {
      const links = page.getByRole('navigation', { name: 'Breast scan routes' }).getByRole('link');
      const hrefs = await links.evaluateAll((nodes) => nodes.map((node) => node.href));
      await links.nth(hrefs.findIndex((href) => new URL(href).searchParams.get('sweep') === nextRoute.id)).click();
      await page.waitForURL((location) => location.searchParams.get('sweep') === nextRoute.id);
      await ready();
      assert.equal(await sweepPicker.inputValue(), nextRoute.id);
    }
  }

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

  const torsoPath = await page.evaluate(() => {
    const tour = abdomenTours.find(({ id }) => id === 'gallbladder');
    return new URL(tour.meshPaths?.torso ?? tour.assetRoot + 'scenes/torso.mesh', location.href).href;
  });
  for (const failure of [null, 503, 404]) {
    let attempts = 0;
    await page.route(torsoPath, (route) => {
      attempts += 1;
      if (failure !== 404 && attempts > 1) return route.continue();
      return failure === null ? route.abort('connectionreset') : route.fulfill({ status: failure });
    });
    await page.reload();
    if (failure === 404) {
      await page.getByText('3D probe and scan plane unavailable.').waitFor();
      assert.equal(await canvas.isVisible(), false);
      assert.equal(attempts, 1, 'Permanent missing geometry should reach the fallback without retrying.');
    } else {
      await ready();
      assert.equal(attempts, 2, 'A transient geometry request should recover with one retry.');
    }
    await page.unroute(torsoPath);
  }
  await page.reload();
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
