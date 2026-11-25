import assert from 'node:assert/strict';
import { bmodeCalibration, probePlane } from '../heart-poses.js';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const url = process.argv[2] || 'http://127.0.0.1:8887/cardiac/?view=a4c';
const folder = process.argv[3];
if (folder) await mkdir(folder, { recursive: true });
const b = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true,
  args: ['--enable-unsafe-swiftshader'],
});
try {
  const p = await b.newPage({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' }),
    errors = [];
  p.on('pageerror', (e) => errors.push(e.message));
  const capture = async (name) => {
    if (folder) {
      await p.locator('#measureWorkbench').screenshot({ path: join(folder, name + '.png') });
      await p.locator('.mw-panel canvas').screenshot({ path: join(folder, name + '-chart.png') });
    }
  };
  await p.goto(url);
  await p.getByText('Doppler & measurements', { exact: true }).click();
  const task = p.getByRole('combobox', { name: 'Measurement or Doppler check' }),
    output = p.locator('.mw-values');
  const setView = (id) => p.locator('#window').selectOption(id);
  await p.getByText('Sampling settings', { exact: true }).click();
  await p.getByLabel('Gate offset').fill('8');
  assert.match(await output.textContent(), /No sampled signal/);
  await p.getByLabel('Gate offset').fill('0');
  assert.match(await output.textContent(), /E\/A 1.46/);
  await p.getByText('Trace calipers', { exact: true }).click();
  await p.getByLabel('Trace end in milliseconds').fill('0');
  assert.match(await p.locator('.mw-interval-result').textContent(), /Choose an end/);
  await p.getByLabel('Trace end in milliseconds').fill('900');
  assert.match(await p.locator('.mw-interval-result').textContent(), /Absolute VTI/);
  await capture('spectral');
  for (const id of [
    'a4c',
    'plax',
    'psax-av',
    'psax-mv',
    'psax-papillary',
    'psax-apical',
    'a2c',
    'a3c',
    'a5c',
    'rv-focused',
    'rv-inflow',
    'rv-outflow',
    'subcostal-4c',
    'subcostal-sax',
    'subcostal-ivc',
    'subcostal-aorta',
    'suprasternal-arch',
  ]) {
    await setView(id);
    for (const option of await task.locator('option').evaluateAll((opts) => opts.map((o) => o.value))) {
      await task.selectOption(option);
      assert.ok(
        await p.locator('.mw-panel canvas').count(),
        id + '/' + option + ' missing plot: ' + (await p.locator('.mw-panel').textContent()),
      );
      assert.ok(!/NaN|Infinity/.test(await p.locator('.mw-panel').innerText()), id + '/' + option);
    }
  }
  await setView('a4c');
  await task.selectOption('lv');
  assert.match(await output.textContent(), /EDV .* mL.*ESV .* mL.*EF .*%/);
  console.log(await output.textContent());
  await capture('biplane');
  await task.selectOption('strain');
  assert.match(await output.textContent(), /End-systolic model mean −?[-\d.]+%/);
  await capture('strain');
  await task.selectOption('la');
  await p.getByLabel('Example body surface area in square meters').fill('0');
  assert.match(await output.textContent(), /Enter a body surface area/);
  await task.selectOption('color');
  await p.getByRole('button', { name: 'Early inflow' }).click();
  const px = () => p.locator('.mw-color').evaluate((c) => c.toDataURL());
  await p.getByLabel('Color Nyquist limit').fill('100');
  await capture('inflow');
  const high = await px();
  await p.getByLabel('Color Nyquist limit').fill('15');
  assert.notEqual(await px(), high);
  await capture('color');
  await setView('rv-focused');
  await task.selectOption('tapse');
  console.log(await output.textContent());
  await task.selectOption('rv');
  console.log(await output.textContent());
  await setView('subcostal-ivc');
  await task.selectOption('ivc');
  await p.getByLabel('Inspiratory diameter').fill('12');
  assert.match(await output.textContent(), /Collapse 33%/);
  // A2C uses a wider fan than A4C. A fixed screen displacement must retain its physical calibration.
  await setView('a2c');
  await task.selectOption('length');
  const wideCaliper = p.locator('.mw-calipers');
  await wideCaliper.focus();
  await wideCaliper.press('Enter');
  for (let i = 0; i < 4; i++) await wideCaliper.press('Shift+ArrowRight');
  await wideCaliper.press('Enter');
  const raster = bmodeCalibration(probePlane(0, 'a2c'));
  const wideSize = await wideCaliper.evaluate((c) => [c.width, c.height]);
  const expected = 40 / (raster.scale * Math.min(wideSize[0] / raster.width, wideSize[1] / raster.height));
  assert.ok((await output.textContent()).includes(expected.toFixed(1) + ' mm'));
  await setView('plax');
  await task.selectOption('length');
  await p.getByRole('combobox', { name: 'Structure' }).selectOption('LVOT diameter');
  await p.getByRole('button', { name: 'Freeze at mid systole' }).click();
  assert.equal(await p.locator('#phase').inputValue(), '170');
  const image = p.locator('.mw-calipers');
  await image.focus();
  await image.press('Enter');
  for (let i = 0; i < 6; i++) await image.press('Shift+ArrowRight');
  await image.press('Enter');
  console.log(await output.textContent());
  await p.getByRole('button', { name: 'Use as LVOT diameter' }).click();
  assert.match(await output.textContent(), /Saved/);
  await setView('a5c');
  await task.selectOption('lvot');
  console.log(await output.textContent());
  await p.getByText('Sampling settings', { exact: true }).click();
  assert.notEqual(await p.getByLabel('LVOT diameter', { exact: true }).inputValue(), '2.05');
  assert.deepEqual(errors, []);
  console.log(
    'All 17 protocol views, task menus, aligned color, spectral gain, trace intervals, model contours, IVC response and caliper handoff passed.',
  );
} finally {
  await b.close();
}
