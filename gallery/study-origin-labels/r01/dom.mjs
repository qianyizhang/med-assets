// Actual gallery renderer with recorded data in happy-dom. Not browser/runtime QA.
import fs from 'node:fs';
import assert from 'node:assert/strict';
const dep = process.env.HAPPY_DOM_MODULE;
if (!dep) throw Error('Set HAPPY_DOM_MODULE to an already installed happy-dom module; no download.');
const {Window} = await import(dep);
const root = process.env.GALLERY_ROOT ? new URL('file://' + process.env.GALLERY_ROOT.replace(/\/$/, '') + '/') : new URL('../../', import.meta.url);
const w = new Window({url: 'http://fixture.invalid/review/', settings: {disableCSSFileLoading: true, disableJavaScriptFileLoading: true, disableJavaScriptEvaluation: true, enableFileSystemHttpRequests: false}});
const d = w.document;
d.write(fs.readFileSync(new URL('public/review/index.html', root), 'utf8').replace(/<script[\s\S]*?<\/script>/g, ''));
for (const [key, value] of Object.entries({window: w, document: d, location: w.location, history: w.history, scrollY: 0, scrollTo: () => {}, requestAnimationFrame: f => f()})) globalThis[key] = value;
const data = JSON.parse(fs.readFileSync(new URL('public/review/review-data.json', root)));
const calls = [];
globalThis.fetch = async url => { calls.push(url); assert.equal(url, 'review-data.json'); return {ok: true, json: async () => structuredClone(data)}; };
await import(new URL('public/review/review.js', root));
assert.equal(d.querySelector('#error').textContent, '');
assert.equal(data.assets.length, 69);
assert.equal(data.candidates.length, 38);
assert.deepEqual(data.assets.filter(a => a.hasBaseline === false).map(a => a.id).sort(), ['blood_cell_study', 'diaphragm_static_study', 'eye_anterior_segment', 'hypothalamus', 'lung_pair', 'parotid_glands', 'tongue_authored_study']);
function setView(value) { const select = d.querySelector('#overview-view'); select.value = value; select.dispatchEvent(new w.Event('change')); }
function query(value) { const input = d.querySelector('#overview-search'); input.value = value; input.dispatchEvent(new w.Event('input')); }
const rows = () => [...d.querySelectorAll('#overview-rows .overview-row')];
function verifyRows(entries, current, lang) {
  assert.equal(rows().length, entries.length);
  entries.forEach((entry, i) => {
    const row = rows()[i], links = row.querySelectorAll('.row-actions a');
    assert.equal(row.querySelector('small').textContent, current ? (lang === 'zh' ? '更新版' : 'Updated version') : entry.hasBaseline === false ? (lang === 'zh' ? '仅研究条目（无原始基线）' : 'Study-only entry (no baseline)') : (lang === 'zh' ? '原版' : 'Original'));
    assert.equal(links[0].getAttribute('href'), '#' + (current ? 'candidate-' : 'asset-') + encodeURIComponent(entry.id));
    assert.equal(links[0].getAttribute('data-study'), current ? entry.id : null);
    assert.equal(links[1].getAttribute('href'), entry.source.file);
    assert.equal(links[1].hasAttribute('download'), true);
    assert.ok(row.querySelector('.result-' + entry.gates.visual));
  });
}
for (const lang of ['en', 'zh']) {
  if (d.documentElement.lang !== lang) d.querySelector('#lang').click();
  const options = [...d.querySelector('#overview-view').options];
  assert.deepEqual(options.map(o => o.value), ['current', 'baseline', 'all']);
  assert.equal(options[1].textContent, lang === 'zh' ? '素材条目 · 69' : 'Asset entries · 69');
  setView('baseline'); verifyRows(data.assets, false, lang);
  assert.equal(d.querySelector('#overview-count').textContent, lang === 'zh' ? '69 条记录' : '69 records');
  // All seven study-only destinations remain real, openable archive entries.
  for (const asset of data.assets.filter(a => a.hasBaseline === false)) {
    w.location.hash = '#asset-' + asset.id;
    w.dispatchEvent(new w.Event('hashchange'));
    assert.equal(d.getElementById('asset-' + asset.id).open, true);
    assert.equal(d.getElementById('asset-' + asset.id).hidden, false);
  }
  query('parotid_glands'); assert.equal(rows().length, 1);
  assert.equal(rows()[0].querySelector('.row-actions a').getAttribute('href'), '#asset-parotid_glands');
  query('no-matching-record-xyz'); assert.equal(rows().length, 0); query('');
  setView('current'); verifyRows(data.candidates, true, lang);
  const first = rows()[0].querySelector('[data-study]'); first.click();
  assert.equal(w.location.hash, '#candidate-' + data.candidates[0].id);
  assert.equal(d.querySelector('#review-overview').hidden, true);
  d.querySelector('#back-overview').click();
  assert.equal(w.location.hash, '#overview');
  assert.equal(d.querySelector('#review-overview').hidden, false);
  setView('all'); assert.equal(rows().length, 107);
  assert.equal(d.querySelector('#overview-count').textContent, lang === 'zh' ? '107 条记录' : '107 records');
  setView('baseline');
}
assert.equal(d.querySelectorAll('#assets > details').length, 69);
assert.equal(d.querySelectorAll('#candidates > details').length, 38);
assert.deepEqual(calls, ['review-data.json']);
assert.equal(d.querySelectorAll('img[src]').length, 0);
console.log('PASS actual-renderer simulated DOM: 7 study-only and 62 original labels, EN/中文, 69/38/107 counts, filters, asset hash navigation, Compare/Back and exact download destinations; no media requests.');
await w.happyDOM.abort();
