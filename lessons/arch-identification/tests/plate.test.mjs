import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
import {COPY, PLACEMENTS, initialState, validateCoverage, order, step, geometry, plateHeight, plateSVG} from '../plate.mjs';
import {mount} from '../ui.mjs';

// jsdom exercises actual handlers/DOM, not browser rendering. No runtime dependency.
const {JSDOM} = createRequire(import.meta.url)('jsdom');
const coverage = JSON.parse(fs.readFileSync(new URL('../../../docs/dental-atlas/set-coverage.json', import.meta.url)));
const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
function fixture(width = 640) {
  const dom = new JSDOM(html, {url: 'http://localhost/lessons/arch-identification/'});
  const root = dom.window.document.querySelector('#lesson');
  root.querySelector('#plate').getBoundingClientRect = () => ({width});
  const app = mount(root, coverage);
  const click = selector => root.querySelector(selector).dispatchEvent(new dom.window.MouseEvent('click', {bubbles: true}));
  const key = value => root.querySelector('[role="radio"][tabindex="0"]').dispatchEvent(new dom.window.KeyboardEvent('keydown', {key: value, bubbles: true, cancelable: true}));
  return {dom, root, app, click, key, close() {app.destroy(); dom.window.close();}};
}

test('exactly 28 source-supported IDs; four third-molar slots are unavailable', () => {
  assert.equal(validateCoverage(coverage).size, 28);
  for (const fdi of ['18','28','38','48']) assert.equal(coverage.teeth.find(t => t.fdi === fdi).bp3d, null);
  const invalid = structuredClone(coverage); invalid.teeth.find(t => t.fdi === '11').bp3d = null;
  assert.throws(() => validateCoverage(invalid), /Unexpected source/);
  invalid.teeth.push(coverage.teeth.find(t => t.fdi === '12'));
  assert.throws(() => validateCoverage(invalid), /Unexpected source/);
});

for (const lang of ['en','zh']) test(`all 28 UI selections stay source-bound in ${lang}`, () => {
  const f = fixture();
  f.click(`[data-lang="${lang}"]`);
  for (const arch of ['upper','lower']) {
    f.click(`[data-arch="${arch}"]`);
    assert.equal(f.root.querySelectorAll('[role="radio"]').length, 14);
    for (const t of coverage.teeth.filter(t => t.bp3d && PLACEMENTS[arch][t.fdi])) {
      f.click(`[role="radio"][data-fdi="${t.fdi}"] text`);
      assert.equal(f.root.querySelector('#fdi').textContent, `FDI ${t.fdi}`);
      assert.equal(f.root.querySelector('#fdi').dataset.source, t.bp3d.source_object);
      const selected = f.root.querySelector('[aria-checked="true"]');
      assert.equal(selected.dataset.fdi, t.fdi);
      assert.equal(f.root.querySelectorAll('[role="radio"][tabindex="0"]').length, 1);
      assert.equal(f.dom.window.document.activeElement, selected);
      if (lang === 'en') {
        const actual = [...f.root.querySelectorAll('#identity dd')].map(x => x.textContent.toLowerCase());
        const [,sourceArch,side,...toothClass] = t.name.split(' ');
        assert.deepEqual(actual, [sourceArch === 'maxillary' ? 'upper arch' : 'lower arch', 'patient ' + side, toothClass.join(' ')]);
      } else {
        assert.match(selected.getAttribute('aria-label'), /牙弓 · 患者[左右]侧/);
      }
    }
  }
  f.close();
});

test('patient-side cues and coverage reverse with the recorded lower camera', () => {
  const f = fixture();
  assert.equal(f.root.querySelector('#screen-left').textContent, 'Patient right');
  assert.equal(f.root.querySelector('#screen-right').textContent, 'Patient left');
  assert.equal(f.root.querySelector('#missing').textContent, '18 · 28');
  f.click('[data-arch="lower"]');
  assert.equal(f.root.querySelector('#screen-left').textContent, 'Patient left');
  assert.equal(f.root.querySelector('#screen-right').textContent, 'Patient right');
  assert.equal(f.root.querySelector('#missing').textContent, '38 · 48');
  f.click('[data-lang="zh"]');
  assert.equal(f.root.querySelector('#screen-left').textContent, '患者左侧');
  assert.match(f.root.querySelector('.coverage').textContent, /不表示患者在临床上缺少/);
  f.close();
});

test('keyboard traverses every ID in both orientations, wraps, and focuses selection', () => {
  const f = fixture();
  for (const arch of ['upper','lower']) {
    f.click(`[data-arch="${arch}"]`);
    f.key('Home');
    const seen = [];
    for (let i = 0; i < 14; i++) {
      seen.push(f.dom.window.document.activeElement.dataset.fdi);
      f.key('ArrowRight');
    }
    assert.deepEqual(seen, order(arch));
    assert.equal(f.dom.window.document.activeElement.dataset.fdi, seen[0]);
    f.key('ArrowLeft'); assert.equal(f.dom.window.document.activeElement.dataset.fdi, seen.at(-1));
    f.key('Home'); f.key('ArrowDown'); assert.equal(f.dom.window.document.activeElement.dataset.fdi, seen[1]);
    f.key('ArrowUp'); assert.equal(f.dom.window.document.activeElement.dataset.fdi, seen[0]);
    f.key('End'); assert.equal(f.dom.window.document.activeElement.dataset.fdi, seen.at(-1));
    f.key('Enter'); f.key(' '); assert.equal(f.dom.window.document.activeElement.dataset.fdi, seen.at(-1));
  }
  f.close();
});

test('arch and language changes preserve selections; crown targets select the same IDs', () => {
  const f = fixture();
  f.click('.hit[data-fdi="16"]');
  f.click('[data-lang="zh"]');
  assert.equal(f.root.querySelector('#fdi').textContent, 'FDI 16');
  f.click('[data-arch="lower"]'); f.click('.hit[data-fdi="46"]');
  f.click('[data-arch="upper"]'); assert.equal(f.root.querySelector('#fdi').textContent, 'FDI 16');
  f.click('[data-arch="lower"]'); assert.equal(f.root.querySelector('#fdi').textContent, 'FDI 46');
  f.close();
});

test('image failure removes floating leaders, keeps selection/keyboard/language, and retries', () => {
  const f = fixture(292);
  const oldImage = f.root.querySelector('image');
  f.click('[data-arch="lower"]');
  oldImage.dispatchEvent(new f.dom.window.Event('error'));
  assert.equal(f.root.querySelector('#image-error').hidden, true, 'late upper error must not affect lower');
  f.root.querySelector('image').dispatchEvent(new f.dom.window.Event('error'));
  assert.equal(f.root.querySelector('#image-error').hidden, false);
  assert.equal(f.root.querySelector('image'), null);
  assert.equal(f.root.querySelectorAll('.hit, #plate path').length, 0);
  assert.equal(f.root.querySelectorAll('[role="radio"]').length, 14);
  f.key('End'); f.click('[data-lang="zh"]');
  assert.equal(f.root.querySelector('#fdi').textContent, 'FDI 47');
  assert.match(f.root.querySelector('#image-error').textContent, /牙弓图像暂不可用/);
  f.click('#retry'); assert.ok(f.root.querySelector('image'));
  assert.equal(f.root.querySelector('#image-error').hidden, true);
  assert.equal(f.root.querySelector('#fdi').textContent, 'FDI 47');
  f.close();
});

test('responsive SVG labels stay legible, in bounds and separated at 240–1000 px', () => {
  for (const width of [240, 292, 360, 499, 500, 640, 1000]) {
    for (const arch of ['upper','lower']) for (const available of [true, false]) {
      const state = initialState(); state.arch = arch; state.image[arch] = available;
      const marks = geometry(state, width), height = plateHeight(state, width);
      for (const p of marks) {
        assert.ok(p.font * width / 1100 >= 13.99);
        assert.ok(p.size * width / 1100 >= 27.99);
        assert.ok(p.lx - p.size / 2 >= 0 && p.lx + p.size / 2 <= 1100, `horizontal ${width}/${arch}/${p.fdi}`);
        assert.ok(p.ly - p.size / 2 >= 0 && p.ly + p.size / 2 <= height, `vertical ${width}/${arch}/${p.fdi}`);
      }
      for (let i = 0; i < marks.length; i++) for (let j = i + 1; j < marks.length; j++) {
        const a = marks[i], b = marks[j], size = (a.size + b.size) / 2;
        assert.ok(Math.abs(a.lx - b.lx) >= size || Math.abs(a.ly - b.ly) >= size, `overlap ${width}/${arch}/${a.fdi}/${b.fdi}`);
      }
    }
  }
});

test('standalone plate references original media and contains no embedded payloads or network scripts', () => {
  const svg = plateSVG(initialState());
  assert.match(svg, /\.\.\/\.\.\/reviews\/teeth_gums\//);
  assert.doesNotMatch(svg, /data:|base64|(?:href|src)="https?:|<script/);
  // Namespace URLs are XML vocabulary, not fetches.
});

test('invalid state actions cannot select an unavailable or wrong-arch FDI', () => {
  for (const value of ['18','31','garbage']) assert.deepEqual(step(initialState(), {type:'select', value}), initialState());
  assert.equal(Object.keys(COPY.en).join(), Object.keys(COPY.zh).join());
});
