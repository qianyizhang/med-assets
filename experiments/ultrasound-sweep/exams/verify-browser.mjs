// Supply a full study URL, an optional capture directory, and optional case IDs.
// Timers advance one displayed sample at a time. The actual Play, Seek, chapter
// picker, renderer and report handlers run in a disposable browser.
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const root = new URL(process.argv[2] || 'http://127.0.0.1:8874/');
const captures = process.argv[3];
if (captures) await mkdir(captures, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 920 }, reducedMotion: 'reduce' });
  const errors = [];
  page.on('response', (response) => {
    if (response.status() >= 400 && !response.url().endsWith('/favicon.ico'))
      errors.push(response.status() + ' ' + response.url());
  });
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error' && !msg.location().url.endsWith('/favicon.ico'))
      errors.push(msg.location().url + ' ' + msg.text());
  });
  await page.addInitScript(() => {
    // Select one raster backend for this readback-based pixel comparison.
    const getContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (type, options) {
      return getContext.call(this, type, type === '2d' ? { ...options, willReadFrequently: true } : options);
    };
    const queue = new Map();
    let id = 0,
      time = 0;
    window.requestAnimationFrame = (fn) => {
      queue.set(++id, fn);
      return id;
    };
    window.cancelAnimationFrame = (id) => queue.delete(id);
    window.advanceSample = () => {
      time = Math.max(performance.now(), time) + 101;
      const pending = [...queue.values()];
      queue.clear();
      pending.forEach((fn) => fn(time));
    };
  });
  let ids = process.argv.slice(4);
  if (!ids.length) {
    await page.goto(new URL('index.html', root).href);
    await page.getByRole('link', { name: 'Full exams', exact: true }).click({ force: true });
    ids = await page
      .locator('.family a')
      .evaluateAll((nodes) => nodes.map((n) => n.getAttribute('href').replace('.html', '')));
  }
  let chapters = 0,
    frames = 0;
  for (const id of ids) {
    await page.goto(new URL('exams/' + id + '.html', root).href);
    await page.waitForFunction(
      () =>
        !document.querySelector('#exam').hidden ||
        !document.querySelector('#status').textContent.includes('Loading'),
      null,
      { polling: 30 },
    );
    const result = await page.evaluate(async () => {
      const el = (id) => document.getElementById(id),
        select = el('chapter'),
        seek = el('seek');
      if (el('exam').hidden) throw Error(el('status').textContent);
      const mod = await import('../cases/' + document.querySelector('main').dataset.owner + '/playable.js');
      const record = JSON.parse(el('record').textContent),
        ch = mod.chapters(record);
      const pick = (i) => {
        select.value = i;
        select.dispatchEvent(new Event('change'));
      };
      const scrub = (i) => {
        seek.value = i;
        seek.dispatchEvent(new Event('input'));
      };
      const pixels = (id) => {
        const canvas = el(id),
          data = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
        return data;
      };
      const equivalent = (a, b) => {
        // Some Chrome graphics backends switch antialiasing after readback.
        // A decoded mean channel difference below 0.02/255 allows this only.
        let sum = 0;
        for (let i = 0; i < a.length; i++) sum += Math.abs(a[i] - b[i]);
        return sum / a.length < 0.02;
      };
      const checks = [];
      let start = 0;
      for (let i = 0; i < ch.length; i++) {
        const c = ch[i];
        pick(i);
        el('keyframe').click();
        if (Number(seek.value) !== start + c.evidenceFrame) throw Error('Wrong evidence frame: ' + c.id);
        const expected = pixels('scan'),
          second = pixels('pose');
        if (!el('value').textContent.trim()) throw Error('Missing saved view: ' + c.id);
        scrub(start + ((c.evidenceFrame + c.frames - 1) % c.frames));
        const adjacent = pixels('scan');
        scrub(start + c.evidenceFrame);
        if (!equivalent(pixels('scan'), expected) || !equivalent(pixels('pose'), second))
          throw Error('Non-repeatable frame: ' + c.id);
        let varying = !equivalent(adjacent, expected);
        if (!varying) {
          scrub(start);
          varying = !equivalent(pixels('scan'), expected);
        }
        if (!varying) {
          scrub(start + c.frames - 1);
          varying = !equivalent(pixels('scan'), expected);
        }
        if (!varying) {
          scrub(start + Math.floor(c.frames / 3));
          varying = !equivalent(pixels('scan'), expected);
        }
        if (!varying) throw Error('Static acquisition: ' + c.id);
        // The observer can rotate the primary model independent of acquisition.
        const orbit = el('orbit');
        orbit.value = 57;
        orbit.dispatchEvent(new Event('input'));
        if (!equivalent(pixels('scan'), expected)) {
          // Previous varying-frame probe may have left this chapter off evidence.
          el('keyframe').click();
          if (!equivalent(pixels('scan'), expected)) throw Error('Orbit changed scan: ' + c.id);
        }
        if (equivalent(pixels('pose'), second)) throw Error('Static 3D orbit: ' + c.id);
        el('resetView').click();
        el('keyframe').click();
        el('overlay').click();
        if (el('overlay').getAttribute('aria-pressed') !== 'true' || el('legend').hidden)
          throw Error('Missing tissue legend: ' + c.id);
        if (record.id === 'aaa-positive' && c.id === 'sac-maximum') {
          const legend = el('legend').textContent.toLowerCase();
          for (const tissue of ['wall', 'thrombus', 'lumen'])
            if (!legend.includes(tissue)) throw Error('Incomplete AAA overlay: ' + legend);
          if (equivalent(pixels('scan'), expected)) throw Error('AAA tissue overlay produced no change');
          const marked = pixels('scan');
          scrub(start + c.evidenceFrame - 1);
          el('observationLink').click();
          if (!equivalent(pixels('scan'), marked) || Number(seek.value) !== start + c.evidenceFrame)
            throw Error('Observation lost AAA registered calipers');
        }
        el('overlay').click();
        if (!equivalent(pixels('scan'), expected)) throw Error('B-mode not restored: ' + c.id);
        const evidence = el('evidence').querySelectorAll('a')[i];
        evidence.click();
        if (new URL(location.href).searchParams.get('chapter') !== c.id)
          throw Error('Report link mismatch: ' + c.id);
        checks.push(c.id);
        start += c.frames;
      }
      pick(0);
      el('play').click();
      let shown = 1;
      for (let i = 1; i < start; i++) {
        window.advanceSample();
        if (Number(seek.value) !== i)
          throw Error('Full playback stalled at ' + i + ': ' + el('status').textContent);
        shown++;
        if (i % 48 === 0) await new Promise((resolve) => setTimeout(resolve, 0));
      }
      if (el('play').textContent !== 'Play exam again') throw Error('Playback did not reach the impression');
      if (ch.length > 1) {
        pick(0);
        el('replay').click();
        for (let j = 0; j < ch[0].frames + 2; j++) window.advanceSample();
        if (Number(seek.value) !== ch[0].frames - 1 || el('play').textContent === 'Pause exam')
          throw Error('Chapter replay crossed into next acquisition');
      }
      return { checks, shown };
    });
    chapters += result.checks.length;
    frames += result.shown;
    console.log(id, result.checks.length + ' chapters, ' + result.shown + ' frames');
    if (captures) {
      const form = page.locator('#chapter');
      const options = await form.locator('option').allTextContents();
      const preferred = options.findIndex((s) =>
        /sweep the aneurysm in transverse|maximum sac|jet at|right parasternal|nodule.*transverse|opening.*sac|mural thrombus|absent.*diastol|omphalocele|ectopic|renal pelvis|cyst.*radial/i.test(
          s,
        ),
      );
      await form.selectOption(String(preferred < 0 ? Math.floor(options.length / 2) : preferred));
      await page.locator('#keyframe').dispatchEvent('click');
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: join(captures, id + '.jpg') });
      if (['aaa-positive', 'thyroid-nodule', 'pregnancy-early-abnormal', 'echo-aortic-stenosis'].includes(id)) {
        await page.locator('#overlay').dispatchEvent('click');
        await page.locator('#orbit').fill('35');
        await page.screenshot({
          path: join(captures, id + '-overlay.png'),
          clip: await page.locator('.monitors').boundingBox(),
        });
      }
    }
  }
  assert.deepEqual(errors, []);
  const real = await browser.newPage({ viewport: { width: 1024, height: 768 } });
  await real.goto(new URL('exams/aaa-positive.html', root).href);
  await real.locator('#play').click();
  await real.waitForFunction(() => document.querySelector('#seek').valueAsNumber > 1);
  await real.locator('#play').click();
  const paused = await real.locator('#seek').inputValue();
  await new Promise((resolve) => setTimeout(resolve, 250));
  assert.equal(await real.locator('#seek').inputValue(), paused);
  assert(await real.evaluate(() => document.documentElement.scrollWidth === innerWidth));
  await real.route('**/cases/echo/playable.js', (route) => route.fulfill({ status: 404, body: 'Missing module' }));
  await real.goto(new URL('exams/echo-normal.html', root).href);
  await real.waitForFunction(() =>
    document.querySelector('#status').textContent.includes('could not be displayed'),
  );
  assert(await real.getByRole('heading', { name: 'Impression', exact: true }).isVisible());
  await real.getByRole('link', { name: 'Worked views and acquired comparisons' }).click();
  await real.waitForSelector('section.report');
  await real.close();
  console.log(
    `Full playback and evidence replay passed for ${ids.length} visits, ${chapters} chapters, ${frames} displayed frames.`,
  );
} finally {
  await browser.close();
}
