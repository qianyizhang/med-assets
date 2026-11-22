// Render the live Gallery camera and mesh selections from exact assessed GLBs.
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import formAssessments from '../../../reviews/teaching-assessments/target-form/campaign-assessments.json' with { type: 'json' };
import riskAssessments from '../../../reviews/teaching-assessments/target-risk/campaign-assessments.json' with { type: 'json' };
import lessons from '../app/src/content/gallery/pelvic-lesson-layers.json' with { type: 'json' };
import viewer from '../viewer.lock.json' with { type: 'json' };

const [viewerInputs, output, chrome, playwright] = process.argv.slice(2);
if (!viewerInputs || !output || !chrome || !playwright) {
  throw Error('Usage: node render_pelvic_part_posters.mjs VIEWER_INPUTS FRESH_OUTPUT CHROME PLAYWRIGHT_ENTRY');
}
const { chromium } = await import(pathToFileURL(resolve(playwright)));
const gallery = new URL('../app/src/content/gallery/', import.meta.url);
const assessments = [...formAssessments.assessments, ...riskAssessments.assessments];
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const width = 840;
const height = 630;

// Anchor and label coordinates in the reviewed 4:3 frame, in source laterality.
const labels = {
  'bladder-dome-hidden': [
    ['Left ureteral entry', [222, 390], [26, 307]],
    ['Right ureteral entry', [588, 403], [590, 321]],
    ['Bladder base', [363, 470], [105, 505]],
    ['Bladder neck', [402, 573], [481, 569]],
  ],
  'cervix-pelvic-neighbors': [
    ['Bladder (anterior)', [232, 349], [32, 247]],
    ['Cervix', [432, 320], [312, 212]],
    ['Rectum (posterior)', [595, 156], [537, 38]],
    ['Vaginal exterior', [404, 476], [506, 506]],
  ],
};
const files = new Map();
for (const file of ['scene.js', 'poster.js']) {
  files.set('/' + file, { type: 'text/javascript', bytes: await readFile(new URL(file, gallery)) });
}
for (const entry of viewer.resources.filter((entry) => entry.path.endsWith('.js'))) {
  const bytes = await readFile(resolve(viewerInputs, entry.path));
  if (bytes.length !== entry.bytes || sha256(bytes) !== entry.sha256) {
    throw Error('Viewer dependency differs from its lock: ' + entry.path);
  }
  files.set('/' + entry.path, { bytes, type: 'text/javascript' });
}
for (const { path } of Object.values(lessons)) {
  const record = assessments.find((entry) => entry.export.path === path)?.export;
  const bytes = await readFile(path);
  if (!record || bytes.length !== record.bytes || sha256(bytes) !== record.sha256) {
    throw Error('Model differs from the assessed export: ' + path);
  }
  files.set('/' + path, { bytes, type: 'model/gltf-binary' });
}
files.set('/', {
  type: 'text/html',
  bytes: `<!doctype html><title>Pelvic part poster render</title>
    <script type="importmap">{"imports":{"three":"/vendor/build/three.module.js"}}</script>
    <div id="stage" style="width:${width}px;height:${height}px"></div>`,
});

await mkdir(output);
const server = createServer((req, res) => {
  const file = files.get(req.url);
  if (!file) return res.writeHead(404).end();
  res.writeHead(200, { 'Content-Type': file.type }).end(file.bytes);
});
await new Promise((resolve, reject) => server.once('error', reject).listen(0, '127.0.0.1', resolve));
let browser;
try {
  browser = await chromium.launch({
    executablePath: chrome, headless: true, chromiumSandbox: true, args: ['--enable-unsafe-swiftshader'],
  });
  const page = await browser.newPage({ viewport: { width: 880, height: 670 }, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:' + server.address().port);
  const receipts = [];
  for (const lesson of Object.values(lessons)) {
    const images = await page.evaluate(async ({ lesson, labels, width, height }) => {
      const { loadScene } = await import('/scene.js');
      const bytes = await (await fetch('/' + lesson.path)).arrayBuffer();
      const stage = document.querySelector('#stage');
      const view = { part: lesson.layers[0].id, camera: lesson.camera, light: 1 };
      const groups = Object.fromEntries(lesson.layers.map(({ id, nodes }) => [id, nodes]));
      const engine = await loadScene(stage, bytes, view, new AbortController().signal, { groups });
      const source = stage.querySelector('canvas');
      const images = [];
      for (const { id } of lesson.layers) {
        engine.apply({ ...view, part: id });
        images.push([id, source.toDataURL('image/webp', 0.93)]);
        if (id !== lesson.answerLayer) continue;
        const answer = document.createElement('canvas');
        Object.assign(answer, { width, height });
        const draw = answer.getContext('2d');
        draw.drawImage(source, 0, 0);
        draw.font = '600 25px system-ui';
        draw.textBaseline = 'middle';
        draw.lineWidth = 2.5;
        for (const [text, point, label] of labels[id]) {
          const [x, y] = point;
          const [tx, ty] = label;
          const boxWidth = Math.ceil(draw.measureText(text).width) + 22;
          draw.fillStyle = '#263140';
          draw.strokeStyle = '#263140';
          draw.beginPath();
          draw.moveTo(x, y);
          draw.lineTo(Math.max(tx, Math.min(x, tx + boxWidth)), ty);
          draw.stroke();
          draw.beginPath();
          draw.arc(x, y, 4.5, 0, 2 * Math.PI);
          draw.fillStyle = '#fff';
          draw.fill();
          draw.stroke();
          draw.fillStyle = '#263140';
          draw.beginPath();
          draw.roundRect(tx, ty - 18, boxWidth, 36, 7);
          draw.fill();
          draw.fillStyle = '#fff';
          draw.fillText(text, tx + 11, ty + 1);
        }
        images.push([id + '-answer', answer.toDataURL('image/webp', 0.93)]);
      }
      engine.dispose();
      return images;
    }, { lesson, labels, width, height });
    for (const [id, url] of images) {
      if (!url.startsWith('data:image/webp;base64,')) throw Error('WebP encoding failed: ' + id);
      const bytes = Buffer.from(url.split(',')[1], 'base64');
      const name = 'pelvic-' + id + '.webp';
      await writeFile(resolve(output, name), bytes);
      receipts.push({ name, source: lesson.path, bytes: bytes.length, sha256: sha256(bytes) });
    }
  }
  await writeFile(resolve(output, 'posters.json'), JSON.stringify({
    chromium: browser.version(), three: viewer.threeVersion, width, height, posters: receipts,
  }, null, 2) + '\n');
} finally {
  await browser?.close();
  server.close();
}
