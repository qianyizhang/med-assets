import assert from 'node:assert/strict';
import { sha256 as assetHash } from './assertions.mjs';
import { readFile } from 'node:fs/promises';
import { ovaryLocator, ovaryPickupDetail, regionalPath, teachingDisplayPath } from '../../app/src/content/gallery/teaching-data.js';

const repo = new URL('../../../../', import.meta.url);
const load = async (file) => JSON.parse(await readFile(new URL(file, repo), 'utf8'));

export async function checkOvaryLesson(page, dest, dir, delivery) {
  const lesson = await load('lessons/ovary-tubal-context/lesson.json');
  const review = await load(lesson.localization.review);
  const view = review.assessments.find(({ export: file }) => file.path === lesson.localization.export)
    .views.find(({ path }) => path === lesson.localization.plate.path);
  const regional = regionalPath + '/' + ovaryLocator.id;
  const reproductive = 'use-cases/systems/reproductive';
  const pickup = reproductive + '?detail=' + ovaryPickupDetail;
  const next = reproductive + '?detail=reproductive-female-uterine-entry';
  const go = (fragment) => page.goto(dest + '/#/' + fragment);
  const where = () => new URL(page.url()).hash;
  const asset = (path) => delivery.assets.find((entry) => entry.path === path);
  const url = (entry) => '/assets/' + entry.sha256 + '/' + entry.name;
  const decode = (image) => image.evaluate((node) => node.decode());
  const question = page.getByRole('heading', { level: 1, name: lesson.question, exact: true });
  const pelvis = page.getByRole('img', { name: lesson.orientation.plate.alt });
  const closeups = page.getByRole('img', { name: lesson.localization.plate.alt });
  const source = page.getByRole('img', { name: lesson.source.plate.alt });
  const compare = page.locator('summary').filter({ hasText: lesson.source.heading });
  const locatorReturn = page.getByRole('link', { name: '← Regional locators', exact: true });
  const reproductiveReturn = page.getByRole('link', { name: '← Reproductive', exact: true });
  const picker = page.getByRole('combobox', { name: 'Detail view' });
  const pelvisAsset = asset(lesson.orientation.plate.path);
  const sourceOriginal = asset(lesson.source.plate.original);
  const sourceDisplay = asset(teachingDisplayPath(lesson.source.plate.original));
  const verifyAsset = async (entry, expectedType) => {
    const response = await page.request.get(dest + url(entry));
    assert.equal(response.status(), 200, entry.path);
    assert.equal(response.headers()['content-type'], expectedType);
    assert.equal(assetHash(await response.body()), entry.sha256);
  };

  async function checkSequence() {
    await question.waitFor();
    await page.locator('[lang=zh]').getByText(lesson.questionZh, { exact: true }).waitFor();
    await decode(pelvis);
    await decode(closeups);
    assert.equal(await pelvis.getAttribute('src'), url(pelvisAsset));
    const src = await closeups.getAttribute('src');
    const inline = src.startsWith('data:image/webp;base64,');
    if (inline) assert.equal(await closeups.evaluate((image) => image.closest('a') === null), true);
    const raw = inline
      ? Buffer.from(src.split(',')[1], 'base64')
      : await (await page.request.get(new URL(src, dest).href)).body();
    assert.equal(raw.length, view.bytes);
    assert.equal(assetHash(raw), view.sha256);
    assert.deepEqual(await closeups.evaluate((image) => [image.naturalWidth, image.naturalHeight]), [view.width, view.height]);
    const transition = page.getByText(lesson.localization.transition, { exact: true });
    await transition.waitFor();
    await page.locator('[lang=zh]').getByText(lesson.localization.transitionZh, { exact: true }).waitFor();
    const getTop = (node) => node.evaluate((element) => element.getBoundingClientRect().top);
    assert.ok(await getTop(pelvis) < await getTop(transition));
    assert.ok(await getTop(transition) < await getTop(closeups));
    assert.ok(await source.isHidden(), 'native comparison starts closed');
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  }

  const sourceRequests = [];
  const trackSource = (request) => {
    if (new URL(request.url()).pathname === url(sourceDisplay)) sourceRequests.push(request.url());
  };
  page.on('request', trackSource);
  await go('use-cases/lessons');
  await page.getByRole('link', { name: 'Regional locators →', exact: true }).press('Enter');
  await page.getByRole('link', { name: ovaryLocator.name + ' →', exact: true }).press('Enter');
  assert.equal(where(), '#/' + regional);
  await checkSequence();
  await verifyAsset(pelvisAsset, 'image/webp');
  assert.deepEqual(sourceRequests, []);
  await page.screenshot({ path: dir + 'ovary-regional.png', fullPage: true });
  await compare.press('Enter');
  await decode(source);
  assert.equal(sourceRequests.length, 1);
  page.off('request', trackSource);
  assert.equal(await source.getAttribute('src'), url(sourceDisplay));
  const sourceModel = asset(lesson.source.model);
  assert.equal(await page.getByRole('link', { name: /Exact HRA r01 GLB/ }).getAttribute('href'), url(sourceModel));
  await verifyAsset(sourceModel, 'model/gltf-binary');
  await verifyAsset(sourceDisplay, 'image/webp');
  await page.screenshot({ path: dir + 'ovary-source-comparison.png', fullPage: true });
  await locatorReturn.click();
  await page.getByRole('heading', { level: 1, name: 'Regional locators' }).waitFor();
  assert.equal(where(), '#/' + regionalPath);

  await go('use-cases/systems');
  await page.getByRole('link', { name: /Reproductive/ }).click();
  assert.equal(where(), '#/' + reproductive);
  await page.getByRole('link', { name: /Asset detail/ }).press('Enter');
  await picker.selectOption(ovaryPickupDetail);
  await question.waitFor();
  assert.equal(where(), '#/' + pickup);
  assert.equal(await picker.inputValue(), ovaryPickupDetail);
  await page.getByRole('link', { name: 'Development', exact: true }).press('Enter');
  assert.equal(where(), '#/' + pickup + '&view=development');
  await page.getByRole('link', { name: 'Teaching', exact: true }).press('Enter');
  await question.waitFor();
  assert.equal(await picker.inputValue(), ovaryPickupDetail);
  await checkSequence();
  await page.screenshot({ path: dir + 'ovary-reproductive.png', fullPage: true });
  await page.getByRole('link', { name: 'Continue to uterine entry →', exact: true }).click();
  assert.equal(where(), '#/' + next);
  await page.getByRole('heading', { name: 'Female · uterine entry' }).waitFor();
  await page.waitForFunction(() => document.activeElement?.classList.contains('ga-content') && scrollY === 0);
  await decode(page.getByRole('img', { name: 'Female · uterine entry · Isometric' }));
  await picker.selectOption(ovaryPickupDetail);
  await question.waitFor();
  await reproductiveReturn.click();
  await page.getByRole('heading', { level: 1, name: 'Reproductive', exact: true }).waitFor();
  assert.equal(where(), '#/' + reproductive);
  await page.getByRole('link', { name: ovaryLocator.name + ' →', exact: true }).click();
  assert.equal(where(), '#/' + pickup);
  await question.waitFor();

  await page.setViewportSize({ width: 1024, height: 768 });
  for (const fragment of [regional, pickup]) {
    await go(fragment);
    await page.reload();
    await checkSequence();
    assert.equal(where(), '#/' + fragment);
  }
  await page.screenshot({ path: dir + 'ovary-reproductive-1024.png', fullPage: true });
  const withhold = (entry) => page.route('**' + url(entry), (route) => route.fulfill({ status: 503 }));
  await withhold(pelvisAsset);
  await withhold(sourceDisplay);
  await page.reload();
  await page.getByRole('status').filter({ hasText: lesson.orientation.plate.title + ' unavailable' }).waitFor();
  await decode(closeups);
  await page.getByText(lesson.orientation.cue, { exact: true }).waitFor();
  await compare.press('Enter');
  await decode(source.and(page.locator('img[src="' + url(sourceOriginal) + '"]')));
  await withhold(sourceOriginal);
  await page.reload();
  await compare.press('Enter');
  await page.getByRole('status').filter({ hasText: lesson.source.plate.title + ' unavailable' }).waitFor();
  await page.getByText(lesson.source.cue, { exact: true }).waitFor();
  await page.screenshot({ path: dir + 'ovary-missing-media.png', fullPage: true });
  for (const entry of [pelvisAsset, sourceDisplay, sourceOriginal]) {
    await page.unroute('**' + url(entry));
  }
  await page.reload();
  await checkSequence();
  await reproductiveReturn.click();
  assert.equal(where(), '#/' + reproductive);
  await page.setViewportSize({ width: 1280, height: 900 });
  console.log('PASS shared ovary sequence, exact r02 and HRA r01 evidence, entry/return routes, neighboring detail, old bookmarks, scale cue and missing-media recovery.');
}
