// Run against the assembled gallery. Optional second argument retains browser captures.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir} from 'node:fs/promises';
import {join} from 'node:path';
const {chromium} = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const root = process.argv[2] || 'http://127.0.0.1:8887/';
const folder = process.argv[3];
if (folder) await mkdir(folder, {recursive: true});
const browser = await chromium.launch({executablePath: process.env.MODEL_SURVEY_BROWSER,
  chromiumSandbox: true, args: ['--enable-unsafe-swiftshader']});
try {
  const page = await browser.newPage({viewport: {width: 1360, height: 860}, reducedMotion: 'reduce'});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const by = id => page.locator('#' + id);
  const pixels = async id => createHash('sha256').update(await by(id).evaluate(canvas => canvas.toDataURL())).digest('hex');
  const click = name => page.getByRole('button', {name, exact: true}).click();
  const capture = async name => { if (folder) await page.screenshot({path: join(folder, name + '.png')}); };
  const fillRange = (id, value) => by(id).fill(String(value));
  await page.goto(root);
  await by('sweepPicker').selectOption('cardiac-a4c');
  await page.waitForURL('**/cardiac/?view=plax');
  await page.waitForFunction(() => document.querySelector('#torso-status').hidden);
  assert.equal(await by('pose').getAttribute('aria-pressed'), 'true');
  await by('window').selectOption('a4c');
  await page.waitForFunction(() => !document.querySelector('#play').disabled);
  assert.equal(await by('play').textContent(), 'Play beat');
  assert.equal(await by('phase').inputValue(), '0');
  await capture('apical-study');
  if (folder) {
    for (let frame = 0; frame < 25; frame++) {
      await fillRange('phase', frame * 40);
      await page.locator('.images').screenshot({path: join(folder, 'beat-' + String(frame).padStart(2, '0') + '.png')});
    }
    await click('End diastole');
  }
  await click('Heart section');
  const ed = await pixels('section'), sceneED = await pixels('scene');
  await click('End systole');
  assert.notEqual(await pixels('section'), ed);
  assert.notEqual(await pixels('scene'), sceneED);
  assert.equal(await by('tilt').inputValue(), '0');
  await click('End diastole');
  assert.equal(await pixels('section'), ed);
  const beforeOrbit = await pixels('scene');
  await by('scene').press('ArrowRight');
  assert.notEqual(await pixels('scene'), beforeOrbit);
  assert.equal(await pixels('section'), ed);
  await by('scene').press('Home');
  assert.equal(await pixels('scene'), beforeOrbit);
  await fillRange('tilt', 20);
  assert.equal(await by('phase').inputValue(), '0');
  assert.notEqual(await pixels('section'), ed);
  assert.notEqual(await pixels('scene'), sceneED);
  await click('Reset');
  assert.equal(await pixels('section'), ed);
  await click('Anatomy overlay');
  assert.notEqual(await pixels('section'), ed);
  await capture('apical-overlay');
  await click('Anatomy overlay');
  await click('Acquired examples');
  await page.waitForFunction(() => document.querySelector('#reference').dataset.frame === '2');
  const referenceED = await pixels('reference');
  for (const [label, frame, name] of [
    ['End diastole', 2, 'diastole'], ['End systole', 18, 'systole'], ['Early filling', 26, 'filling'],
  ]) {
    await click(label);
    assert.equal(await by('reference').getAttribute('data-frame'), String(frame));
    if (frame > 2) assert.notEqual(await pixels('reference'), referenceED);
    if (folder) {
      for (const id of ['reference', 'section']) await by(id).screenshot({path: join(folder, name + '-' + id + '.png')});
    }
  }
  const matched = await pixels('reference');
  await fillRange('tilt', -28);
  assert.equal(await pixels('reference'), matched);
  assert.equal(await by('phase').inputValue(), '520');
  await by('flow').check();
  assert.match(await by('flow-note').textContent(), /reopen/);
  await fillRange('phase', 200);
  assert.match(await by('flow-note').textContent(), /aortic and pulmonary/);
  await fillRange('phase', 1000);
  assert.equal(await by('reference').getAttribute('data-frame'), '2');
  await click('Play beat');
  const phases = await page.evaluate(async () => {
    const samples = [];
    const start = performance.now();
    while (performance.now() - start < 1400) {
      await new Promise(requestAnimationFrame);
      samples.push(Number(document.querySelector('#phase').value));
    }
    return samples;
  });
  await click('Pause beat');
  assert.ok(new Set(phases).size > 12 && phases.some((x, i) => i && x < phases[i - 1]));
  assert.equal(await by('tilt').inputValue(), '-28');
  const paused = await by('phase').inputValue();
  await page.waitForTimeout(100);
  assert.equal(await by('phase').inputValue(), paused);
  await by('study').selectOption('gallbladder');
  await page.waitForFunction(() => !document.querySelector('#play').disabled);
  assert.equal(await by('sweepPicker').inputValue(), 'gallbladder');
  await page.emulateMedia({reducedMotion: 'no-preference'});
  await page.goto(new URL('cardiac/', root).href);
  await page.waitForFunction(() => document.querySelector('#play').textContent === 'Pause beat');
  await click('Pause beat');
  await page.route('**/acquired-a4c.webp', route => route.abort());
  await click('Acquired examples');
  await page.getByText(/Acquired example unavailable/).waitFor();
  await click('Early filling');
  assert.equal(await by('phase').inputValue(), '520');
  await page.unroute('**/acquired-a4c.webp');
  await click('Heart section');
  await click('Acquired examples');
  await page.waitForFunction(() => document.querySelector('#reference').dataset.frame === '26');
  await page.setViewportSize({width: 640, height: 800});
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.route('**/heart-geometry.js', route => route.abort());
  await page.reload();
  await page.getByText(/Heart model unavailable/).waitFor();
  await click('Acquired examples');
  await click('End systole');
  await page.waitForFunction(() => document.querySelector('#reference').dataset.frame === '18');
  assert.equal(await by('study').isEnabled(), true);
  assert.deepEqual(errors, []);
  console.log('Gallery navigation, motion, phase, pose, orbit, overlay, reference, recovery and reflow passed.');
  console.log(new Set(phases).size + ' distinct presented phases during a 1.4 s cine comparison.');
} finally {
  await browser.close();
}
