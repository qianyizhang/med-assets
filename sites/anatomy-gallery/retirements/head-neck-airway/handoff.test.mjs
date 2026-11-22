import assert from 'node:assert/strict';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';
import { legacyHandoff } from './handoff.mjs';

const head = 'anatomy-head-neck-review.landy123007.chatgpt.site';
const airway = 'anatomy-airway-review.landy123007.chatgpt.site';
const gallery = 'https://med-assets-model-survey.landy123007.chatgpt.site/#/';
const original = '<!doctype html><html lang="en"><title>Legacy</title><main><h1>Retained review</h1></main>';

test('the salivary link uses the fragment and keeps the original review available', () => {
  const html = legacyHandoff(head, '/review/salivary-native-r02/', original);
  assert.ok(html.endsWith('<h1>Retained review</h1></main>'));
  assert.match(html, /<main><nav aria-label="Anatomy Gallery">/);
  const link = { href: html.match(/id="anatomy-gallery-handoff" href="([^"]+)"/u)[1] };
  assert.equal(link.href, gallery + 'use-cases/head-and-neck/location');

  const document = { getElementById: () => link };
  const window = {
    location: { hash: '#negative-image' },
    addEventListener(event, update) {
      assert.equal(event, 'hashchange');
      this.update = update;
    },
  };
  runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/u)[1], { URL, document, window });
  assert.equal(link.href, gallery + 'compare/salivary-native-r02');
  for (const [hash, target] of [
    ['#%76iews', 'use-cases/head-and-neck/duct-course'],
    ['#downloads', 'library/salivary_glands/z-native-scoped-r02'],
    ['#changelog', 'use-cases/head-and-neck/location'],
    ['#%ZZ', 'use-cases/head-and-neck/location'],
  ]) {
    window.location.hash = hash;
    window.update();
    assert.equal(link.href, gallery + target);
  }
});

test('the exact bronchial bookmark gets an r13 notice and file requests stay outside the handoff', () => {
  const path = '/review/bronchial-r13/';
  assert.ok(legacyHandoff(airway, path).includes(gallery + 'compare/bronchial-r13'));
  assert.equal(legacyHandoff(airway, path + 'payload/model.glb'), null);
  assert.equal(legacyHandoff(airway, '/review/trachea-r06/models/trachea-open.glb'), null);
  assert.equal(legacyHandoff(head, '/CHANGELOG.md'), null);
  assert.equal(legacyHandoff('anatomy-verification.landy123007.chatgpt.site', '/review/trachea-polish-r05/'), null);
  assert.throws(() => legacyHandoff(head, '/', '<h1>Missing source review</h1>'), /original legacy HTML/);
});

test('repeated preparation preserves the page and a restored bronchial review', () => {
  const path = '/review/bronchial-r13/';
  for (const [host, url, source] of [[head, '/', original], [airway, path, original], [airway, path, '']]) {
    const prepared = legacyHandoff(host, url, source);
    assert.equal(legacyHandoff(host, url, prepared), prepared);
    assert.equal(prepared.match(/id="anatomy-gallery-handoff"/gu).length, 1);
    if (source) assert.ok(prepared.includes('<h1>Retained review</h1>'));
  }
});
