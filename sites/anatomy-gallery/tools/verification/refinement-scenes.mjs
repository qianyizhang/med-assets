import assert from 'node:assert/strict';
import { sha256 } from './assertions.mjs';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { localModels, teachingScenes } from '../../app/src/content/gallery/local-models.js';
import { assetUrl } from '../../app/src/content/gallery/catalog.js';
import { readView, stagePath } from '../../app/src/content/gallery/presets.js';

async function renderedFrame(canvas) {
  await canvas.page().waitForFunction((element) => {
    const parent = element.parentElement;
    const ratio = Math.min(devicePixelRatio, 2);
    return parent.clientWidth && parent.clientHeight &&
      element.width === Math.floor(parent.clientWidth * ratio) &&
      element.height === Math.floor(parent.clientHeight * ratio);
  }, await canvas.elementHandle());
  return canvas.evaluate((element) => element.toDataURL());
}

export async function checkRefinementScenes({ browser, base, capture }) {
  // The controls can become ready one ResizeObserver delivery before the hidden
  // viewport receives its final drawing-buffer dimensions.
  const page = await browser.newPage();
  const checked = [];
  const stomachFrames = new Map();
  const lymphSelections = [];
  for (const study of [...teachingScenes, ...localModels.filter((model) => model.scene.groups)]) {
    const second = Object.keys(study.scene.groups)[1];
    const key = study.scene.version;
    await page.goto(base + '/#/' + study.library);
    const scene = page.getByRole('region', { name: 'Interactive scene' });
    const canvas = scene.locator('canvas');
    const picker = scene.getByRole('combobox', { name: 'Teaching view' });
    const address = base + assetUrl(study.exports[0]);
    await page.route(address, (request) => request.fulfill({ status: 503 }), { times: 1 });
    await scene.getByRole('button', { name: 'Inspect in 3D' }).click();
    await scene.getByText('The pinned export is unavailable.').waitFor();
    assert.ok(await picker.isDisabled());
    if (study.library.startsWith('library/cardiac-atlas/')) {
      const lessons = page.getByRole('navigation', { name: 'Lessons from this model' });
      assert.equal(await lessons.getByRole('link').count(), 2);
      const original = await (await page.request.get(address)).body();
      original[original.length - 1] ^= 1;
      await page.route(address, (route) => route.fulfill({ status: 200, body: original }), { times: 1 });
      await scene.getByRole('button', { name: 'Retry 3D' }).click();
      await scene.getByText('The export differs from the pinned revision.').waitFor();
      assert.ok(await scene.getByRole('img').evaluate(async (image) => { await image.decode(); return image.naturalWidth > 0; }));
    }
    const response = page.waitForResponse((response) => response.url() === address && response.ok());
    await scene.getByRole('button', { name: 'Retry 3D' }).click();
    const bytes = await (await response).body();
    assert.equal(bytes.length, study.exports[0].bytes);
    assert.equal(sha256(bytes), study.exports[0].sha256);
    await canvas.waitFor();
    await page.waitForFunction(() => document.querySelector('.ga-scene select')?.disabled === false);
    assert.equal(await picker.inputValue(), study.scene.initialPart);
    const before = await renderedFrame(canvas);
    assert.ok(before.length > 5000, key + ' initial drawing buffer');
    await canvas.screenshot({ path: path.join(capture, key + '-initial.png') });
    const phases = scene.getByRole('slider', { name: 'Cycle phase' });
    if (study.scene.clip) {
      await phases.fill('0.417');
    } else {
      await picker.selectOption(second);
    }
    await page.waitForFunction((first) => document.querySelector('.ga-scene canvas').toDataURL() !== first, before);
    const after = await canvas.evaluate((c) => c.toDataURL());
    await canvas.evaluate((element) => element.scrollIntoView({ block: 'center', behavior: 'instant' }));
    await canvas.screenshot({ path: path.join(capture, key + '-changed.png') });
    if (study.scene.clip) {
      await phases.fill('0');
      await page.waitForFunction((first) => document.querySelector('.ga-scene canvas').toDataURL() === first, before);
      await phases.fill('0.417');
      const phaseOnly = await canvas.evaluate((element) => element.toDataURL());
      await picker.selectOption(second);
      await page.waitForFunction((frame) => document.querySelector('.ga-scene canvas').toDataURL() !== frame, phaseOnly);
      assert.equal(await phases.inputValue(), '0.417');
      await canvas.screenshot({ path: path.join(capture, key + '-alternate-selection.png') });
    }
    if (study.family === 'stomach') {
      stomachFrames.set(study.scene.version, [before, after].map((frame) =>
        sha256(frame)));
    }
    if (study.scene.version === 'lymph-node-tissues-v2') {
      const groupFrames = new Set([before, after]);
      lymphSelections.push(study.scene.initialPart, second);
      let previousFrame = after;
      for (const part of ['Follicles', 'Paracortex', 'Medulla']) {
        await picker.selectOption(part);
        await page.waitForFunction((frame) => document.querySelector('.ga-scene canvas').toDataURL() !== frame, previousFrame);
        previousFrame = await canvas.evaluate((c) => c.toDataURL());
        groupFrames.add(previousFrame);
        lymphSelections.push(part);
      }
      assert.equal(groupFrames.size, 5);
      await picker.selectOption(second);
    }
    const link = scene.getByRole('link', { name: /Open in 3D Stage/ });
    await link.click();
    await page.waitForURL((url) => url.hash.startsWith('#/stage/' + study.scene.version));
    await page.getByRole('region', { name: 'Interactive scene' }).locator('canvas').waitFor();
    const query = new URL(page.url()).hash.split('?')[1];
    const view = readView(query);
    assert.equal(view.sha256, study.exports[0].sha256);
    assert.equal(view.part, second);
    if (study.scene.clip) assert.equal(view.phase, 0.417);
    const invalid = { ...view, part: 'Unregistered visibility mode' };
    assert.equal(readView('view=' + encodeURIComponent(JSON.stringify(invalid))), null);
    await page.reload();
    await page.getByRole('region', { name: 'Interactive scene' }).locator('canvas').waitFor();
    assert.equal(await picker.inputValue(), view.part);
    if (study.scene.clip) assert.equal(await phases.inputValue(), '0.417');
    assert.notEqual(after, before);
    await page.getByRole('link', { name: /Return to asset record/ }).click();
    await page.waitForURL((url) => url.hash === '#/' + study.library);
    if (study.family === 'parathyroids' || ['stomach-section-v2', 'lymph-node-tissues-v2'].includes(key)) {
      await page.route(address, (request) => request.fulfill({ status: 503 }), { times: 1 });
      await page.goto(base + '/#/' + stagePath(view));
      await scene.getByText('The pinned export is unavailable.').waitFor();
      const fallback = scene.getByRole('img');
      const posterPath = study.scene.posterPath;
      const poster = await readFile(new URL('../../../../' + posterPath, import.meta.url));
      const posterDigest = sha256(poster);
      assert.equal(await fallback.getAttribute('src'), '/review-evidence/' + posterDigest + '/' + path.basename(posterPath));
      assert.ok(await fallback.evaluate(async (image) => { await image.decode(); return image.naturalWidth > 0; }));
      await scene.getByRole('button', { name: 'Retry 3D' }).click();
      await canvas.waitFor();
      assert.equal(await picker.inputValue(), second);
    }
    checked.push({ version: key, model: study.exports[0].path, sha256: view.sha256,
      firstSelection: study.scene.initialPart, alternateSelection: second, phase: view.phase,
      position: view.camera?.position });
  }
  assert.ok(stomachFrames.has('stomach-section-v1') && stomachFrames.has('stomach-section-v2'));
  assert.deepEqual(stomachFrames.get('stomach-section-v1'), stomachFrames.get('stomach-section-v2'),
    'The native color and normal textures must give the same exterior and section frames.');

  // Open exactly the bytes downloaded from the ordinary Library record in the shipped Stage.
  const results = JSON.parse(await readFile(new URL(
    '../../../../reviews/teaching-assessments/reopen-economy/measurements.json', import.meta.url)));
  for (const [family, match] of Object.entries({
    liver: /bare_area/i, muscle: /pectoralis major/i, brain: /cerebellum/i,
    spinal_cord: /Representative dorsal root upper 7 side1/i, trachea: /C-band 8$/i,
  })) {
    const edition = results[family].edition;
    const filename = path.basename(edition.path);
    await page.goto(base + '/#/library/' + family + '/teaching-economy-r02');
    const downloadReady = page.waitForEvent('download');
    await page.getByRole('link', { name: filename + ' ↓', exact: true }).click();
    const download = await downloadReady;
    const bytes = await readFile(await download.path());
    assert.equal(sha256(bytes), edition.sha256);
    await page.goto(base + '/#/stage');
    await page.getByLabel('Open local GLB').setInputFiles({
      name: filename, mimeType: 'model/gltf-binary', buffer: bytes,
    });
    await page.getByRole('heading', { name: filename, exact: true }).waitFor();
    const picker = page.getByRole('combobox', { name: 'Structure' });
    await page.waitForFunction(() => document.querySelector('.ga-scene select')?.disabled === false);
    const names = await picker.locator('option').allTextContents();
    assert.equal(names.length - 1, results[family].meshCount);
    const part = names.find((name) => match.test(name));
    assert.ok(part, 'Missing protected selection in ' + filename);
    const canvas = page.locator('.ga-scene canvas');
    const all = await renderedFrame(canvas);
    assert.ok(all.length > 5000);
    await picker.selectOption(part);
    await page.waitForFunction((frame) => document.querySelector('.ga-scene canvas').toDataURL() !== frame, all);
    await canvas.screenshot({ path: path.join(capture, family + '-selected.png') });
    checked.push({ model: edition.path, sha256: edition.sha256, meshSelections: names.length - 1,
      stageSelection: part });
  }
  await writeFile(path.join(capture, 'scenes.json'), JSON.stringify({ browser: browser.version(), checked,
    stomachTexturedFrameSha256: Object.fromEntries(stomachFrames), lymphSelections }, null, 2) + '\n');
  console.log('PASS full-scene Stage selections, textured stomach equality, tissue views, sampled cardiac phase, shared presets, reload and failed-file recovery.');
}
