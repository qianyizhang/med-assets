import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const address = new URL(process.argv[2] ?? 'http://127.0.0.1:8874/carotid-survey/');
const output = process.env.CAROTID_SURVEY_QA_DIR;
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});

try {
  const page = await browser.newPage({ viewport: { width: 1021, height: 1197 }, acceptDownloads: true });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const url = new URL(address);
  url.searchParams.set('side', 'left');
  await page.goto(url.href);
  await page.locator('#exam').waitFor();
  const protocol = await page.evaluate(async () => {
    const read = (path) => fetch(path).then((result) => result.json());
    const [manifest, geometry] = await Promise.all([read('./protocol.json'), read('./data/protocol-geometry.json')]);
    const supplement = new Map(geometry.stations.map((station) => [station.id, station]));
    return { ...manifest, ...geometry, stations: manifest.stations.map((station) => ({ ...supplement.get(station.id), ...station })) };
  });
  const initial = protocol.stations.find((station) => station.side === 'left');
  const doppler = protocol.stations.find((station) => station.side === 'left' && station.waveformProfile
    && station.gate && station.gate.steeringSupported !== false);
  const right = protocol.stations.find((station) => station.side === 'right');
  const scans = page.locator('#display');
  const waitImage = async (path) => page.waitForFunction((target) => document.querySelector('#display').getAttribute('aria-busy') === 'false'
    && document.querySelector('#scan').src === target && !document.querySelector('#scanPlane').hidden, new URL('data/' + path, address).href);
  async function capture(name, fullPage = false) {
    if (!output) return;
    await mkdir(output, { recursive: true });
    await page.evaluate(() => {
      scrollTo(0, 0);
      return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });
    await page.screenshot({ path: join(output, name + '.png'), fullPage });
  }
  const side = (label) => page.getByRole('group', { name: 'Side', exact: true }).getByRole('button', { name: label, exact: true });
  const mode = (label) => page.getByRole('group', { name: 'Imaging mode' }).getByRole('button', { name: label, exact: true });
  const station = page.getByRole('combobox', { name: 'Segment' });
  const captureImage = page.locator('#capture');
  await waitImage(initial.views.transverse.path);
  assert.equal(await side('Left').getAttribute('aria-pressed'), 'true');
  assert.equal(new URL(await page.locator('#sweepsLink').evaluate((link) => link.href)).searchParams.get('sweep'), 'carotid-left');
  await page.locator('#reconstructionStatus').waitFor({ state: 'hidden' });
  const camera = (label) => page.getByRole('group', { name: 'Reconstruction camera' }).getByRole('button', { name: label });
  await camera('Coronal').click();
  assert.equal(await camera('Coronal').getAttribute('aria-pressed'), 'true');
  await camera('Oblique').click();
  const skin = page.getByRole('slider', { name: 'Skin opacity' });
  await skin.fill('100');
  assert.equal(await skin.getAttribute('aria-valuetext'), '100%');
  await capture('left-opaque-oblique', true);
  await skin.fill('32');
  assert.equal(await page.locator('#openVolume').isVisible(), false);
  assert.ok(await page.locator('#comparison img').isVisible() || await page.locator('#comparison').isVisible());
  await capture('left-transverse-overview', true);

  await page.getByRole('button', { name: 'Calipers', exact: true }).click();
  const points = [[100, 130], [130, 145]];
  for (const [x, y] of points) {
    const [left, top] = await page.locator('#annotations').evaluate((svg, [x, y]) => {
      const point = new DOMPoint(x, y).matrixTransform(svg.getScreenCTM());
      return [point.x, point.y];
    }, [x, y]);
    await page.mouse.click(left, top);
  }
  const expectedMm = (Math.hypot(30, 15) * initial.views.transverse.mmPerPx).toFixed(1) + ' mm';
  assert.equal(await page.locator('#caliperDistance').textContent(), expectedMm);
  await page.getByRole('button', { name: 'Save distance' }).click();
  assert.match(await page.locator('#records').textContent(), new RegExp(expectedMm.replace('.', '\\.')));
  const manual = await page.evaluate(() => JSON.parse(sessionStorage.getItem('ultrasound-carotid-exam-v1')).records[0][1]);
  assert.equal(manual.frame, initial.views.transverse.path);
  assert.equal(manual.imagePath, initial.views.transverse.path);
  assert.equal(manual.type, 'Manual B-mode distance');
  await capture('left-calipers', true);
  await page.getByRole('button', { name: 'Calipers', exact: true }).click();
  await captureImage.click();
  assert.equal(await captureImage.textContent(), 'Image captured');
  assert.match(await page.locator('#progressText').textContent(), /^1 \/ /);

  await station.selectOption(doppler.id);
  await mode('Long axis').click();
  await waitImage(doppler.views.longitudinal.path);
  await mode('Color').click();
  await page.locator('#color').waitFor();
  assert.ok(await page.locator('#color').evaluate((canvas) =>
    canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data.some((value, index) => index % 4 === 3 && value > 0)));
  await capture('left-color', true);
  await captureImage.click();
  await mode('Spectral').click();
  await page.locator('#spectrum').waitFor();
  const spectralReference = await page.evaluate((ids) => ids.map((id) => abdomenReferences[id])
    .find((entry) => entry && /spectral|waveform/i.test(entry.label ?? ''))?.path, doppler.referenceIds);
  if (spectralReference) {
    await page.waitForFunction((target) => document.querySelector('#comparison img')?.src === target,
      new URL('../' + spectralReference, address).href);
    assert.equal(await page.locator('#referenceView').textContent(), 'Spectral Doppler');
  }
  const expected = await page.evaluate(async ({ id, gate }) => {
    const { duplexStations, duplexSample, registeredAcquisition } = await import('./duplex.js');
    const runtime = await fetch('./protocol.json').then((response) => response.json());
    const station = duplexStations(runtime).find((station) => station.id === id);
    return duplexSample(station, registeredAcquisition(gate, {
      prfHz: Number(document.querySelector('#scale').value),
    })).measurements;
  }, { id: doppler.id, gate: doppler.gate });
  const velocities = 'PSV ' + expected.psvCmS.toFixed(1) + ' · EDV ' + expected.edvCmS.toFixed(1) + ' cm/s';
  assert.equal(await page.locator('#velocityReadout').textContent(), velocities);
  await page.getByRole('button', { name: 'Save waveform' }).click();
  assert.ok((await page.locator('#records').textContent()).includes(velocities));
  await capture('left-spectral', true);
  const beam = () => page.locator('#annotations line').first().evaluate((line) => {
    const coordinate = (name) => Number(line.getAttribute(name));
    const dx = coordinate('x2') - coordinate('x1');
    const dy = coordinate('y2') - coordinate('y1');
    return Math.atan2(dy, dx);
  });
  const originalBeam = await beam();
  const beamOrigin = () => page.locator('#annotations line').first().getAttribute('y1').then(Number);
  assert.equal(await beamOrigin(), doppler.gate.steeredOriginPx[1]);
  await page.locator('#gate').fill('20');
  assert.ok(Math.abs(await beam() - originalBeam) < .03, 'Moving the gate should retain the beam angle.');
  assert.equal(await beamOrigin(), doppler.gate.steeredOriginPx[1], 'The parallel ray should still start at the probe face.');
  await page.locator('#gate').fill('100');
  await page.getByText('Keep the Doppler gate inside the lumen.').waitFor();
  assert.equal(await page.getByRole('button', { name: 'Save waveform' }).isDisabled(), true);
  await page.locator('#gate').fill('0');
  assert.equal(await page.locator('#velocityReadout').textContent(), velocities);

  await side('Right').click();
  await station.selectOption(right.id);
  await mode('Transverse').click();
  await waitImage(right.views.transverse.path);
  const tracked = protocol.tracking.right;
  const slider = page.getByRole('slider', { name: 'Transverse tracking' });
  const first = tracked.findIndex((frame, index) => index > 0 && frame.contours?.length === 1 && tracked[index + 1]?.contours?.length === 1);
  assert.ok(first > 0);
  await slider.fill(String(first));
  await waitImage(tracked[first].path);
  await page.getByText('Common carotid · Transverse reference · Side unreported', { exact: true }).waitFor();
  assert.match(await page.locator('#comparison img').getAttribute('src'), /carotid-transverse\.webp$/);
  await captureImage.click();
  await slider.fill(String(first + 1));
  await waitImage(tracked[first + 1].path);
  await captureImage.click();
  assert.match(await page.locator('#reconstructionSummary').textContent(), /Right 2\//);
  const branch = tracked.findIndex((frame) => frame.segment === 'branches');
  assert.ok(branch > first);
  await slider.fill(String(branch));
  await waitImage(tracked[branch].path);
  await page.getByText('Left bifurcation · Transverse reference', { exact: true }).waitFor();
  assert.match(await page.locator('#comparison img').getAttribute('src'), /carotid-bifurcation\.webp$/);
  assert.equal(await page.locator('#openVolume').isVisible(), false);
  const [download] = await Promise.all([
    page.waitForEvent('download'), page.getByRole('button', { name: 'Export PLY' }).click(),
  ]);
  assert.equal(download.suggestedFilename(), 'captured-carotid-reconstruction.ply');
  const ply = await readFile(await download.path(), 'utf8');
  assert.ok(ply.startsWith('ply\nformat ascii 1.0\ncomment Native RAS millimetres\n'));
  assert.match(ply, /element face [1-9]\d*/);
  assert.ok(ply.includes(protocol.anatomySource.url));
  const firstVertex = ply.split('end_header\n')[1].split('\n')[0].split(' ').map(Number);
  assert.ok(tracked[first].contours.flat().some((point) => point.every((value, index) => Math.abs(value - firstVertex[index]) < .001)));
  const reconstruction = page.locator('#reconstruction');
  const reconstructionDigest = async () => {
    const { x, y, width, height } = await reconstruction.boundingBox();
    const clip = { x: Math.ceil(x + 7), y: Math.ceil(y + 7), width: Math.floor(width - 14), height: Math.floor(height - 14) };
    return createHash('sha256').update(await page.screenshot({ clip })).digest('hex');
  };
  await reconstruction.focus();
  const before = await reconstructionDigest();
  await reconstruction.press('ArrowRight');
  await page.evaluate(() => new Promise(requestAnimationFrame));
  assert.notEqual(await reconstructionDigest(), before);
  await reconstruction.press('Home');
  await page.evaluate(() => new Promise(requestAnimationFrame));
  assert.equal(await reconstructionDigest(), before);
  await capture('right-partially-captured', true);
  await page.getByRole('button', { name: 'Acquire stack' }).click();
  await page.getByRole('button', { name: 'Stop acquisition' }).waitFor();
  await page.locator('#openVolume').waitFor({ timeout: 30000 });
  assert.equal(new URL(await page.locator('#openVolume').evaluate((link) => link.href)).searchParams.get('side'), 'right');
  assert.match(await page.locator('#reconstructionSummary').textContent(), new RegExp('Right ' + tracked.length + '/' + tracked.length));
  await page.getByRole('button', { name: 'Acquire stack' }).waitFor();
  await capture('right-complete-reconstruction', true);
  const [completeDownload] = await Promise.all([
    page.waitForEvent('download'), page.getByRole('button', { name: 'Export PLY' }).click(),
  ]);
  const fullMesh = await readFile(await completeDownload.path(), 'utf8');
  const sourceMesh = await page.evaluate(async (path) => {
    const packed = new DataView(await fetch('./data/' + path).then((response) => response.arrayBuffer()));
    return { vertices: packed.getUint32(0, true), faces: packed.getUint32(4, true) };
  }, protocol.reconstructions.right.reconstructionPath);
  assert.match(fullMesh, new RegExp('element vertex ' + sourceMesh.vertices + '\\n'));
  assert.match(fullMesh, new RegExp('element face ' + sourceMesh.faces + '\\n'));

  await page.reload();
  await waitImage(initial.views.transverse.path);
  assert.ok((await page.locator('#records').textContent()).includes(velocities));
  assert.equal(await page.locator('#openVolume').isVisible(), false);
  await side('Right').click();
  await station.selectOption(right.id);
  await waitImage(right.views.transverse.path);
  assert.ok(await page.locator('#openVolume').isVisible());
  const unavailable = protocol.stations.find((candidate) => candidate.side === 'right' && !candidate.views?.transverse);
  if (unavailable) {
    await station.selectOption(unavailable.id);
    await page.locator('#scanStatus').waitFor();
    assert.equal(await captureImage.isDisabled(), true);
  }
  await page.setViewportSize({ width: 760, height: 1000 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  assert.ok(await reconstruction.evaluate((canvas) => {
    const viewport = canvas.parentElement;
    const panel = viewport.closest('.reconstruction');
    return Math.abs(canvas.getBoundingClientRect().width - panel.clientWidth) <= 1
      && viewport.getBoundingClientRect().height <= 330;
  }), 'The compact reconstruction should fill its panel width without exceeding its height cap.');
  await capture('compact-reconstruction', true);
  await page.setViewportSize({ width: 1021, height: 1197 });

  const blocked = new URL('data/' + initial.views.transverse.path, address).href;
  await page.route(blocked, (route) => route.abort());
  await page.reload();
  await page.locator('#scanStatus').waitFor();
  await page.waitForFunction(() => document.querySelector('#display').getAttribute('aria-busy') === 'false');
  assert.equal(await captureImage.isDisabled(), true);
  assert.equal(await page.getByRole('button', { name: 'Calipers', exact: true }).isDisabled(), true);
  await page.unroute(blocked);
  await side('Right').click();
  await station.selectOption(right.id);
  await waitImage(right.views.transverse.path);
  await side('Left').click();
  await station.selectOption(initial.id);
  await waitImage(initial.views.transverse.path);
  assert.equal(await scans.getAttribute('aria-busy'), 'false');
  for (const item of protocol.stations) {
    await side(item.side === 'left' ? 'Left' : 'Right').click();
    await station.selectOption(item.id);
    if (!item.views?.transverse || !item.views?.longitudinal) continue;
    await mode('Transverse').click();
    await waitImage(item.views.transverse.path);
    if (item.forkEvidence?.arterialMaskPaths?.transverse) {
      assert.equal(await page.locator('#branches').isVisible(), false);
      await page.getByRole('button', { name: 'Show branches' }).click();
      await page.locator('#branches').waitFor();
      assert.ok((await page.locator('#annotations text').allTextContents()).includes('ICA'));
      assert.ok((await page.locator('#annotations text').allTextContents()).includes('ECA'));
      await capture(item.side + '-transverse-bifurcation', true);
      await page.getByRole('button', { name: 'Show branches' }).click();
      assert.equal(await page.locator('#branches').isVisible(), false);
    }
    await mode('Long axis').click();
    await waitImage(item.views.longitudinal.path);
    if (item.forkEvidence?.arterialMaskPaths?.longitudinal) {
      await page.getByRole('button', { name: 'Show branches' }).click();
      await page.locator('#branches').waitFor();
      assert.deepEqual(new Set(await page.locator('#annotations text').allTextContents()), new Set(['CCA', 'ICA', 'ECA']));
      await capture(item.side + '-longitudinal-bifurcation', true);
      await page.getByRole('button', { name: 'Show branches' }).click();
      const gate = item.colorGate ?? item.gate;
      if (gate && gate.steeringSupported !== false) {
        assert.equal(await mode('Spectral').isDisabled(), true);
        await mode('Color').click();
        await page.locator('#color').waitFor();
        assert.equal(await page.locator('#angleControl').isVisible(), false);
        const source = await page.evaluate((ids) => ids.map((id) => abdomenReferences[id])
          .find((entry) => entry && /color doppler/i.test(entry.label ?? ''))?.path, item.referenceIds);
        if (source) {
          await page.waitForFunction((target) => document.querySelector('#comparison img')?.src === target,
            new URL('../' + source, address).href);
        }
        await capture(item.side + '-bulb-color', true);
      }
    }
  }
  await page.evaluate(() => {
    const phase = document.querySelector('#examPhase');
    window.examTiming = [];
    new MutationObserver(() => {
      examTiming.push([phase.textContent, performance.now()]);
    }).observe(phase, { subtree: true, childList: true, characterData: true });
  });
  await page.getByRole('button', { name: 'Play exam', exact: true }).click();
  await page.getByText('Right · Transverse stack', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Pause exam' }).click();
  await page.getByText(/Paused · Right · Transverse stack/).waitFor();
  assert.equal(await page.getByRole('button', { name: 'Resume exam' }).getAttribute('aria-pressed'), 'false');
  await page.getByRole('button', { name: 'Resume exam' }).click();
  const review = page.locator('#reviewSpan');
  await page.getByText('Model-placed wall span · 7.8 mm', { exact: true }).waitFor({ timeout: 45000 });
  await page.getByRole('button', { name: 'Pause exam' }).click();
  const pausedScan = await page.locator('#scan').evaluate((image) => image.src);
  assert.equal(pausedScan, new URL('data/' + protocol.stations.find((station) => station.id === 'right-cca-dist').views.longitudinal.path, address).href);
  assert.ok(await review.isVisible());
  assert.equal(await page.getByRole('link', { name: 'Compare measured values' }).getAttribute('href'), './review/distal-cca-measurements.webp');
  await capture('right-paused-wall-caliper', true);
  assert.equal(await page.locator('#scan').evaluate((image) => image.src), pausedScan);
  await page.getByRole('button', { name: 'Resume exam' }).click();
  await page.getByText('Model-placed wall span · 7.7 mm', { exact: true }).waitFor({ timeout: 110000 });
  await capture('left-wall-caliper', true);
  await page.getByRole('button', { name: 'Replay exam' }).waitFor({ timeout: 110000 });
  const completed = await page.locator('#reconstructionSummary').textContent();
  assert.ok(completed.includes('Right ' + protocol.tracking.right.length + '/' + protocol.tracking.right.length));
  assert.ok(completed.includes('Left ' + protocol.tracking.left.length + '/' + protocol.tracking.left.length));
  assert.equal(new URL(await page.locator('#openVolume').evaluate((link) => link.href)).searchParams.get('side'), 'left');
  assert.equal(await page.locator('#openVolume').isVisible(), true);
  await side('Right').click();
  assert.equal(new URL(await page.locator('#openVolume').evaluate((link) => link.href)).searchParams.get('side'), 'right');
  assert.equal(await page.locator('#openVolume').isVisible(), true);
  assert.match(await page.locator('#ratios').textContent(), /Right ICA\/CCA PSV ratio \d+\.\d+ · Left ICA\/CCA PSV ratio \d+\.\d+/);
  assert.ok((await page.locator('#records').textContent()).includes(expectedMm), 'Playback should retain a manually saved caliper.');
  const saved = await page.evaluate(() => Object.fromEntries(JSON.parse(sessionStorage.getItem('ultrasound-carotid-exam-v1')).records));
  for (const side of ['right', 'left']) {
    const id = side + '-cca-dist';
    const record = saved[id + '/wall-span'];
    const view = protocol.stations.find((station) => station.id === id).views.longitudinal;
    assert.equal(record.frame, view.path);
    assert.equal(record.value, side === 'right' ? '7.8 mm' : '7.7 mm');
    const [[ax, ay], [bx, by]] = record.endpointsPx;
    assert.ok(Math.abs(Math.hypot(bx - ax, by - ay) * view.mmPerPx - record.lengthMm) < 1e-8);
    assert.ok(saved[id + '/spectral'].beamAngleDeg >= 0);
  }
  const timing = await page.evaluate(() => examTiming);
  for (const [phase, minimum] of [
    ['Right · Distal CCA · Spectral Doppler', 2600],
    ['Left · Distal CCA · Long axis', 3200],
    ['Left · Bulb and bifurcation · Long axis', 1950],
  ]) {
    const index = timing.findIndex(([name]) => name === phase);
    assert.ok(index >= 0 && timing[index + 1][1] - timing[index][1] >= minimum, phase + ' should remain readable during playback.');
  }
  if (output) await writeFile(join(output, 'playback-timing.json'), JSON.stringify(timing, null, 2) + '\n');
  await capture('completed-bilateral-exam', true);
  assert.deepEqual(errors, []);
  console.log('Calibrated calipers, waveform measurements, color, captured PLY, bilateral playback, route and media recovery passed.');
} finally {
  await browser.close();
}
