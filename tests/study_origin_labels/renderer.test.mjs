import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {withoutAssetEntryLabels} from '../../gallery/study-origin-labels/r01/preservation.mjs';

const updated = fs.readFileSync(process.env.LABEL_RENDERER);
const baseline = fs.readFileSync(new URL('fixtures/review-v48.js', import.meta.url));
const data = JSON.parse(fs.readFileSync(new URL('fixtures/entries.json', import.meta.url)));
function harness(raw, lang) {
  const elements = new Map();
  const el = selector => {
    if (!elements.has(selector)) elements.set(selector, {innerHTML: '', textContent: '', value: ''});
    return elements.get(selector);
  };
  const esc = value => String(value ?? '').replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
  const context = {data: {...structuredClone(data), issues: []}, lang, overviewQuery: '', overviewView: 'baseline', $: el, esc,
    b: value => typeof value === 'string' ? value : value?.[lang] || value?.en || '',
    displayName: c => c.name[lang] || c.name.en, shortRemaining: () => '', t: x => x, applyStudyMode() {}};
  const source = raw.toString();
  const start = source.indexOf('function renderOverview(){');
  const end = source.indexOf('\nfunction applyStudyMode()', start);
  assert(start >= 0 && end > start);
  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  context.renderOverview();
  return {context, elements, html: () => el('#overview-rows').innerHTML};
}
function labels(html) {
  return [...html.matchAll(/<strong>.*?<\/strong><small>(.*?)<\/small>/g)].map(m => m[1]);
}
for (const lang of ['en', 'zh']) test(`actual renderer ${lang}: seven study-only rows, 62 originals and preserved destinations`, () => {
  const h = harness(updated, lang), actual = labels(h.html());
  assert.equal(data.assets.length, 69);
  assert.equal(data.candidates.length, 38);
  assert.equal(actual.length, 69);
  assert(h.elements.get('#review-overview').innerHTML.includes(lang === 'zh' ? '素材条目 · 69' : 'Asset entries · 69'));
  data.assets.forEach((asset, i) => {
    assert.equal(actual[i], asset.hasBaseline === false ? (lang === 'zh' ? '仅研究条目（无原始基线）' : 'Study-only entry (no baseline)') : (lang === 'zh' ? '原版' : 'Original'));
    assert(h.html().includes(`href="#asset-${encodeURIComponent(asset.id)}"`));
    assert(h.html().includes(`href="${asset.source.file.replace(/&/g, '&amp;')}" download`));
  });
  assert.equal(data.assets.filter(a => a.hasBaseline === false).length, 7);
  h.context.overviewView = 'current'; h.context.renderOverviewRows();
  assert.equal(labels(h.html()).length, 38);
  assert(labels(h.html()).every(x => x === (lang === 'zh' ? '更新版' : 'Updated version')));
  h.context.overviewView = 'all'; h.context.renderOverviewRows(); assert.equal(labels(h.html()).length, 107);
  h.context.overviewView = 'baseline'; h.context.overviewQuery = 'parotid_glands'; h.context.renderOverviewRows();
  assert.equal(labels(h.html()).length, 1);
  h.context.overviewQuery = 'no-matching-record-xyz'; h.context.renderOverviewRows(); assert.equal(labels(h.html()).length, 0);
});
test('original source reproduces both erroneous labels; strict reversal allows only the two reviewed edits', () => {
  for (const lang of ['en', 'zh']) {
    const old = harness(baseline, lang);
    assert(old.elements.get('#review-overview').innerHTML.includes(lang === 'zh' ? '原始素材 · 69' : 'Original assets · 69'));
    assert.equal(labels(old.html()).filter(x => x === (lang === 'zh' ? '原版' : 'Original')).length, 69);
  }
  assert.deepEqual(withoutAssetEntryLabels(updated), baseline);
  assert.throws(() => withoutAssetEntryLabels(baseline));
  assert.throws(() => withoutAssetEntryLabels(Buffer.concat([updated, Buffer.from('\n')])));
});
