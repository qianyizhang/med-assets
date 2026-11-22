import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import delivery from '../app/src/content/assets/delivery-index.json' with { type: 'json' };
import publication from '../snapshot-reference.json' with { type: 'json' };

const coverage = 'survey-coverage';
const bookmark = (id) => '/_data/components/' + id;
const publicOrigin = new URL(publication.siteUrl).origin;
// Existing shared URLs must survive a change in how new short IDs are generated.
const publishedShortId = 'Rdo55Ten';

export const balanced = delivery.assets.find((asset) => asset.name === 'FDI31-balanced.glb');

export async function checkBalancedDownload(page) {
  const pending = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download Balanced GLB' }).click();
  const download = await pending;
  assert.equal(download.suggestedFilename(), balanced.name);
  const bytes = await readFile(await download.path());
  assert.equal(bytes.length, balanced.bytes);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), balanced.sha256);
}


export async function checkSurveyBookmarks(page, origin, shortId) {
  const library = page.getByRole('heading', { name: 'Asset Library', exact: true });
  const survey = page.getByRole('navigation', { name: 'Planning sections' });
  const target = page.locator(`[data-component-id="${coverage}"][data-permalink-target="true"]`);
  const checkTarget = async () => {
    await target.getByText('Collection at a glance', { exact: true }).waitFor();
    await page.waitForFunction((element) => element === document.activeElement, await target.elementHandle());
  };
  await page.goto(origin);
  await library.waitFor();

  for (const id of [coverage, origin === publicOrigin ? publishedShortId : shortId(origin, coverage)]) {
    const url = origin + bookmark(id);
    assert.equal((await page.goto(url)).status(), 200);
    await checkTarget();
    assert.equal(new URL(page.url()).pathname, bookmark(id));
    assert.equal((await page.reload()).status(), 200);
    await checkTarget();
    await page.getByRole('link', { name: /Anatomy Gallery/ }).click();
    await library.waitFor();
    assert.equal(new URL(page.url()).pathname, '/');
    await page.goBack();
    await survey.waitFor();
    await target.waitFor();
    assert.equal(new URL(page.url()).pathname, bookmark(id));
  }

  for (const [fragment, heading, action] of [
    ['family-adrenals', 'Adrenal pair · BodyParts3D', 'Review this version'],
    ['swirendo_fdi31', 'FDI31 · prepared specimen', 'Download Balanced GLB'],
  ]) {
    const url = new URL('/?view=1#' + fragment, origin);
    const family = page.locator('.ga-content').filter({ has: page.getByText('Catalogue ID', { exact: true }) })
      .getByRole('heading', { name: heading, exact: true });
    await page.goto(url.href);
    await family.waitFor();
    await page.reload();
    await family.waitFor();
    if (fragment === 'swirendo_fdi31') {
      await checkBalancedDownload(page);
    } else {
      await page.getByRole('link', { name: action }).press('Enter');
      await page.getByRole('heading', { name: 'Adrenal pair · BodyParts3D', exact: true }).waitFor();
      await page.getByRole('link', { name: 'Browse BodyParts3D adrenal family' }).click();
      await family.waitFor();
      await page.goBack();
      await page.goBack();
      await family.waitFor();
    }
    assert.equal(new URL(page.url()).hash, url.hash);
    await page.getByRole('link', { name: 'Anatomy Gallery', exact: true }).click();
    await library.waitFor();
    await page.goBack();
    await family.waitFor();
    assert.equal(new URL(page.url()).hash, url.hash);
  }
}

// Rehearse with the packaged Worker, its immutable HTML and the public origin
// on the browser's request URL. HTML and the Balanced GLB use exact local bytes.
if (import.meta.main) {
  const project = path.resolve(process.argv[2]);
  const { default: worker } = await import(pathToFileURL(path.join(project, 'dist/server/index.js')));
  const { componentPermalinkShortId } = await import(pathToFileURL(path.join(project, 'src/chart-permalink.js')));
  const read = (name) => readFile(path.join(project, '.data-app-assets', name));
  const { assets } = JSON.parse(await read('manifest.json'));
  const html = await read('html.html');
  const snapshot = await read('snapshot.json');
  const file = await readFile(new URL('../../../' + balanced.path, import.meta.url));
  assert.equal(file.length, balanced.bytes);
  assert.equal(createHash('sha256').update(file).digest('hex'), balanced.sha256);
  const balancedKey = 'assets/sha256/' + balanced.sha256;
  const balancedMetadata = { size: file.length, customMetadata: { sha256: balanced.sha256 } };
  const storage = {
    BUCKET: {
      async head(key) {
        return key === balancedKey ? balancedMetadata : null;
      },
      async get(key) {
        if (key === balancedKey) return { ...balancedMetadata, body: new Response(file).body };
        if (key !== assets.html.key) return null;
        return {
          body: new Response(html).body, size: html.length,
          customMetadata: { sha256: assets.html.sha256 },
        };
      },
    },
  };
  const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
  const browser = await chromium.launch({
    executablePath: process.env.MODEL_SURVEY_BROWSER,
    headless: true,
    chromiumSandbox: true,
  });
  try {
    const testOrigin = 'https://gallery-bookmark-test.chatgpt.site';
    const page = await browser.newPage({ reducedMotion: 'reduce' });
    page.setDefaultTimeout(8000);
    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url());
      if (![publicOrigin, testOrigin].includes(url.origin)) return route.abort();
      if (url.pathname === '/api/snapshot') {
        return route.fulfill({ contentType: 'application/json', body: snapshot });
      }
      if (url.pathname === '/api/presentation') {
        return route.fulfill({ json: { presentation: {}, revision: 0, canEdit: false } });
      }
      const response = await worker.fetch(new Request(url, { method: route.request().method() }), storage);
      return route.fulfill({
        status: response.status,
        headers: Object.fromEntries(response.headers),
        body: Buffer.from(await response.arrayBuffer()),
      });
    });
    for (const origin of [publicOrigin, testOrigin]) {
      await checkSurveyBookmarks(page, origin, componentPermalinkShortId);
    }
    await page.goto(testOrigin + bookmark(publishedShortId));
    await page.getByRole('heading', { name: 'Asset Library', exact: true }).waitFor();
    assert.equal(await page.getByRole('navigation', { name: 'Planning sections' }).count(), 0);
    console.log('PASS authored and origin-specific Survey bookmarks, focus and reload, Back, Library homepage, family links and exact FDI31 download, and wrong-origin rejection.');
  } finally {
    await browser.close();
  }
}
