import assert from 'node:assert/strict';
import { sha256 as hash } from './assertions.mjs';
import { readFile } from 'node:fs/promises';
import { readCaptions } from '../../app/src/content/gallery/archive-captions.js';

const repo = new URL('../../../../', import.meta.url);

async function checkKidney(page, dest, dir, delivery) {
  const kidneyPath = dest + '/#/archive/kidney-outline-trial';
  const exterior = page.locator('#exterior-panel');
  const internal = page.locator('#internal-panel');
  const outline = page.locator('#outline');
  const locator = page.locator('#locator');
  const ready = () => internal.locator('image[href^="blob:"]').waitFor({ state: 'attached' });
  await page.goto(dest + '/#/use-cases');
  await page.getByRole('link', { name: 'Experiments & Archive →' }).click();
  await page.getByRole('link', { name: 'Left kidney outline trial →' }).press('Enter');
  await ready();
  assert.ok(await outline.isVisible());
  await page.screenshot({ path: dir + 'kidney-outlined.png', fullPage: true });
  await locator.press('Space');
  assert.ok(await outline.isHidden());
  await page.screenshot({ path: dir + 'kidney-original.png', fullPage: true });
  await page.getByRole('radio', { name: 'Internal shapes', exact: true }).press('ArrowRight');
  assert.ok(await page.getByRole('radio', { name: 'Side by side', exact: true }).isChecked());
  const bounds = async () => {
    const a = await exterior.locator('svg').boundingBox();
    const b = await internal.locator('svg').boundingBox();
    assert.ok(a.x < b.x && a.y === b.y);
    assert.equal(a.width, b.width);
    assert.equal(a.height, b.height);
  };
  await bounds();
  await page.screenshot({ path: dir + 'kidney-paired.png', fullPage: true });
  await page.getByLabel('Language').selectOption('zh');
  assert.ok(await page.getByRole('radio', { name: '并排对照', exact: true }).isChecked());
  assert.ok(await outline.isHidden());
  await page.setViewportSize({ width: 1024, height: 768 });
  await bounds();
  await page.screenshot({ path: dir + 'kidney-paired-zh.png', fullPage: true });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(kidneyPath + '?view=exterior&outline=0');
  await ready();
  assert.ok(await page.getByRole('radio', { name: 'Exterior', exact: true }).isChecked());
  assert.ok(await locator.isDisabled());

  const asset = delivery.assets.find(({ path }) => path ===
    'reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/display/contact.webp');
  const url = '/assets/' + asset.sha256 + '/' + asset.name;
  assert.equal(hash(await (await page.request.get(dest + url)).body()), asset.sha256);
  const route = '**' + url;
  for (const data of [{ status: 503 }, { status: 200, body: 'wrong image bytes' }]) {
    await page.route(route, (request) => request.fulfill(data));
    await page.reload();
    await page.getByText(/source image could not be verified/).waitFor();
    assert.ok(await page.getByRole('heading', { name: 'Provisional finding' }).isVisible());
    assert.ok(await page.getByRole('link', { name: /Trial record/ }).isVisible());
    await page.unroute(route);
  }
  await page.reload();
  await ready();
  await page.getByRole('link', { name: '← Experiments & Archive' }).click();
  await page.getByRole('heading', { level: 1, name: 'Experiments & Archive' }).waitFor();
  console.log('PASS kidney controls, paired equal scale, language and direct states, exact bytes, corrupt/missing rejection and recovery.');
}

async function checkFilms(page, dest, dir) {
  const treatments = 'experiments/dental-video-treatments/';
  const image26 = 'experiments/dental-image26/';
  const manifest = JSON.parse(await readFile(new URL(treatments + 'results/manifest.json', repo), 'utf8'));
  const collections = JSON.parse(await readFile(new URL('transport/collection-archives.json', repo), 'utf8'));
  const members = await readFile(new URL(collections['teaching-media'].checksumList.path, repo), 'utf8');
  const paths = new Map(members.trim().split('\n').map((entry) => entry.split('  ').reverse()));
  const treatmentIds = manifest.artifacts.filter(({ file }) => file.endsWith('.mp4')).map(({ file, sha256 }) => ({
    file, sha256, owner: treatments, id: file.split('/').at(-1).replace('.mp4', ''),
  }));
  const image26Ids = [...paths].filter(([path]) => path.startsWith(image26) && path.endsWith('.mp4')).map(([path, sha256]) => ({
    file: path.slice(image26.length), sha256, owner: image26,
    id: path.includes('/films/') ? path.split('/').at(-1).replace('.mp4', '') : 'combined',
  }));
  assert.equal(treatmentIds.length, 4);
  assert.equal(image26Ids.length, 6);
  const video = page.locator('video');
  const metadata = () => page.waitForFunction(() => {
    const player = document.querySelector('video');
    return player?.readyState >= 1 && Number.isFinite(player.duration) && player.videoWidth > 0;
  });
  for (const [link, collection] of [
    [/One script, three dental video treatments/, 'dental-video-treatments'],
    [/Dental Image 2.6 stories/, 'dental-image26'],
  ]) {
    await page.getByRole('link', { name: link }).click();
    await metadata();
    assert.equal(new URL(page.url()).hash, '#/archive/' + collection);
    await page.getByRole('link', { name: '← Experiments & Archive' }).click();
  }
  for (const { file, sha256, owner, id } of [...treatmentIds, ...image26Ids]) {
    const name = file.split('/').at(-1);
    const route = '/assets/' + sha256 + '/' + name;
    await page.goto(dest + '/#/archive/' + owner.split('/')[1] + '/' + id);
    await metadata();
    assert.equal(await video.getAttribute('src'), route);
    const range = await page.request.get(dest + route, { headers: { range: 'bytes=0-31' } });
    assert.equal(range.status(), 206);
    assert.match(range.headers()['content-range'], /^bytes 0-31\/\d+$/);
    assert.equal(hash(await (await page.request.get(dest + route)).body()), sha256);
    const seek = await video.evaluate(async (player) => {
      player.muted = true;
      await player.play();
      player.pause();
      const target = player.duration * 0.4;
      const sought = new Promise((resolve) => player.addEventListener('seeked', resolve, { once: true }));
      player.currentTime = target;
      await sought;
      player.textTracks[0].mode = 'hidden';
      return player.currentTime;
    });
    assert.ok(seek > 5, name);
    await page.waitForFunction(() => document.querySelector('video').textTracks[0].cues?.length > 0);
    const srt = owner === image26 ? owner + file.replace('.mp4', '.srt') : owner + 'audio/narration.srt';
    const expected = readCaptions(await readFile(new URL(srt, repo), 'utf8'));
    const actual = await video.evaluate((player) => [...player.textTracks[0].cues].map(({ startTime, endTime, text }) =>
      ({ start: Math.round(startTime * 1000), end: Math.round(endTime * 1000), text })));
    assert.deepEqual(actual, expected, name);
    if (['comparison', 'hyperframes', 'combined', '05-implant'].includes(id)) {
      await page.screenshot({ path: dir + 'film-' + id + '.png', fullPage: true });
    }
  }
  const url = await video.getAttribute('src');
  await page.route('**' + url, (request) => request.fulfill({ status: 503 }));
  await page.reload();
  await page.getByText(/retained video is unavailable/).waitFor();
  await page.getByText('Narration transcript', { exact: true }).press('Enter');
  assert.ok(await page.getByRole('link', { name: /Original scripts and prompts/ }).isVisible());
  await page.screenshot({ path: dir + 'film-unavailable.png', fullPage: true });
  await page.unroute('**' + url);
  await page.getByRole('button', { name: 'Retry video' }).press('Enter');
  await metadata();
  console.log('PASS ten exact archive films, native playback, seek/range, timed captions, discovery, unavailable media and retry.');
}

export async function checkArchive(page, dest, dir, delivery) {
  await checkKidney(page, dest, dir, delivery);
  await checkFilms(page, dest, dir);
}
