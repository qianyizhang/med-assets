// Shared browser assertions for a tour's absolute transport and its embedded source viewer.
import assert from 'node:assert/strict';

export async function installTourClock(page) {
  await page.addInitScript(() => {
    const requests = new Map();
    let nextId = 0;
    let time = performance.now();
    window.requestAnimationFrame = (callback) => {
      requests.set(++nextId, callback);
      return nextId;
    };
    window.cancelAnimationFrame = (id) => requests.delete(id);
    // Advance the parent once per committed frame. Child clocks are stepped
    // separately by tests that need an actual WebGL image before sampling.
    window.stepSweep = () => {
      time = Math.max(performance.now(), time) + 201;
      const callbacks = [...requests.values()];
      requests.clear();
      for (const callback of callbacks) callback(time);
    };
  });
}

export async function checkTimeline(page, segments) {
  await page.locator('#tourPosition:not([disabled])').waitFor();
  const marks = await page.locator('.chapters a[data-chapter]').evaluateAll((links) =>
    links.map(({ dataset, style }) => ({
      range: [dataset.chapter, dataset.sweep, Number(dataset.start), Number(dataset.end)],
      percent: Number.parseFloat(style.getPropertyValue('--marker-position')),
    })));
  assert.deepEqual(marks.map(({ range }) => range), segments, 'Authored section ranges changed');
  const totalFrames = segments.reduce((sum, [, , start, end]) => sum + end - start + 1, 0);
  let offset = 0;
  for (const { range: [chapter, , start, end], percent } of marks) {
    assert.ok(Math.abs(percent - offset / (totalFrames - 1) * 100) < 0.001, chapter + ' marker is not frame-proportional');
    offset += end - start + 1;
  }
  const position = page.locator('#tourPosition');
  assert.equal(await position.getAttribute('min'), '0');
  assert.equal(await position.getAttribute('max'), String(totalFrames - 1));
  assert.equal(await page.locator('input[type=range]:visible').count(), 1, 'Tour must expose a single transport range');
  const player = page.frameLocator('#player iframe');
  assert.ok(await player.locator('#position').isHidden(), 'Embedded scrubber is still visible');
  assert.ok(await player.locator('#play').isHidden(), 'Embedded play button is still visible');
  assert.equal(await page.locator('#restart, #advance').count(), 0, 'Old chapter navigation still present');
  return totalFrames;
}

export function absoluteFrame(segments, chapter, sourceFrame) {
  let offset = 0;
  for (const [id, , start, end] of segments) {
    if (id === chapter) {
      assert.ok(sourceFrame >= start && sourceFrame <= end, 'Source frame is outside section ' + chapter);
      return offset + sourceFrame - start;
    }
    offset += end - start + 1;
  }
  throw Error('Unknown section ' + chapter);
}

export async function waitForTourFrame(page, number) {
  await page.waitForFunction((frame) => document.querySelector('#tourPosition')?.dataset.displayed === String(frame),
    number, { polling: 20 });
  const position = page.locator('#tourPosition');
  assert.equal(await position.inputValue(), String(number));
  const total = Number(await position.getAttribute('max')) + 1;
  assert.equal(await page.locator('#tourFrameNumber').textContent(), (number + 1) + ' / ' + total);
}

export async function seekTour(page, number) {
  await page.locator('#tourPosition').fill(String(number));
  await waitForTourFrame(page, number);
}

export async function playTourToEnd(page, segments) {
  await waitForTourFrame(page, 0);
  await page.locator('#playTour').click();
  const player = page.frameLocator('#player iframe');
  let number = 0;
  for (const [chapter, , start, end] of segments) {
    for (let sourceFrame = start; sourceFrame <= end; sourceFrame++) {
      if (number > 0) {
        // A large clock step still advances exactly one sample per acknowledgement.
        await page.evaluate(() => window.stepSweep());
        await waitForTourFrame(page, number);
      }
      assert.equal(await player.locator('#position').inputValue(), String(sourceFrame),
        'Wrong source frame at absolute frame ' + number);
      if (sourceFrame === start || sourceFrame === end) {
        assert.equal(await page.locator('.chapters [aria-current="step"]').getAttribute('data-chapter'), chapter);
      }
      number++;
    }
  }
  await page.getByRole('button', { name: 'Replay tour', exact: true }).waitFor();
  await page.locator('#playTour').click();
  await waitForTourFrame(page, 0);
  await page.getByRole('button', { name: 'Pause tour', exact: true }).click();
  await page.evaluate(() => window.stepSweep());
  await waitForTourFrame(page, 0);
  return number;
}
