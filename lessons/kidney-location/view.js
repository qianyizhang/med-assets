import { outlinePath, source } from './source.js';

const copy = {
  en: {
    eyebrow: 'Left kidney · HRA female v1.3', language: 'Language',
    title: 'Place the internal shapes',
    intro: 'Compare the isolated pyramids and tip surfaces with the exterior in the same recorded view.',
    view: 'View', exterior: 'Exterior', internal: 'Internal shapes', paired: 'Side by side',
    locator: 'Show 2D exterior outline', exteriorCaption: 'Exterior',
    internalCaption: 'Isolated pyramids + source-labeled tip surfaces',
    scope: 'The dashed line is a 2D editorial locator copied from the exterior silhouette. It shows projected position only: no cutaway, depth or tissue boundary is measured.',
    tips: 'Pale patches are source-labeled tip surfaces. No pelvis, calyces, ureter, vessels or collecting route is shown.',
    axis: '“Front” is the recorded review axis, not a new anatomical registration. Source colors are illustrative.',
    credit: 'Source: Kristen Browne and Heidi Schlehlein (2024), HRA / HuBMAP, female left kidney v1.3.',
    changes: 'Unchanged retained r02 image; presentation changes: matched crops, view switching and optional 2D outline.',
    original: 'Original contact image', attribution: 'Attribution',
    loading: 'Loading the retained image…', error: 'The source image could not be verified. Reload after restoring the retained contact image.',
    exteriorAlt: 'Retained exterior, recorded front review axis',
    internalAlt: 'Retained isolated pyramids and source-labeled tip surfaces, recorded front review axis',
    outlineAlt: ', with a dashed 2D editorial exterior locator',
    same: 'Same camera, scale and position when switching views.',
    pairNote: 'Same camera and scale in both panels.',
    locatorNote: 'Dashed line: 2D exterior locator.', controls: 'View controls', region: 'Recorded front review view',
  },
  zh: {
    eyebrow: '左肾 · HRA 女性参考模型 v1.3', language: '语言',
    title: '对照外形，定位内部结构',
    intro: '在同一记录视角下，将单独显示的肾锥体和尖端表面与肾脏外形对照。',
    view: '视图', exterior: '外形', internal: '内部结构', paired: '并排对照',
    locator: '显示二维外形轮廓', exteriorCaption: '肾脏外形',
    internalCaption: '单独显示：肾锥体及源标注的尖端表面',
    scope: '虚线是依据外形剪影绘制的二维编辑定位线，仅提示投影位置；不表示剖切面、测量深度或组织边界。',
    tips: '浅色斑块是源模型标注的尖端表面。图中未展示肾盂、肾盏、输尿管、血管或集合系统通路。',
    axis: '“正面”仅指记录中的审阅视轴，不构成新的解剖配准。源模型颜色为示意。',
    credit: '来源：Kristen Browne、Heidi Schlehlein（2024），HRA / HuBMAP，女性左肾 v1.3。',
    changes: '保留的 r02 图像未改动；本页仅增加同尺度裁切显示、视图切换及可选二维轮廓。',
    original: '原始审阅拼图', attribution: '来源署名',
    loading: '正在加载保留图像…', error: '源图像校验失败。请恢复保留的原始图像后重新加载。',
    exteriorAlt: '保留的肾脏外形，记录中的正面审阅视轴',
    internalAlt: '保留的独立肾锥体及源标注尖端表面，记录中的正面审阅视轴',
    outlineAlt: '，叠加虚线二维外形定位线',
    same: '切换时保持相同视角、比例和画面位置。',
    pairNote: '两幅图保持相同视角与比例。',
    locatorNote: '虚线：二维外形定位线。', controls: '视图控制', region: '记录中的正面审阅视图',
  },
};
const $ = selector => document.querySelector(selector);
const params = new URLSearchParams(location.search);
const validViews = ['exterior', 'internal', 'paired'];
let view = validViews.includes(params.get('view')) ? params.get('view') : 'internal';
let language = params.get('lang') === 'zh' ? 'zh' : 'en';
let loadState = 'loading';
$('#locator').checked = params.get('outline') !== '0';
$('#outline').setAttribute('d', outlinePath);

function update() {
  const t = copy[language];
  document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
  document.title = t.eyebrow + ' · ' + t.title;
  $('[name="view"][value="' + view + '"]').checked = true;
  $('#language').value = language;
  document.querySelectorAll('[data-copy]').forEach(el => { el.textContent = t[el.dataset.copy]; });
  $('form').setAttribute('aria-label', t.controls);
  $('#views').setAttribute('aria-label', t.region);
  $('#status').hidden = loadState === 'ready';
  $('#status').textContent = t[loadState === 'error' ? 'error' : 'loading'];
  $('#views').hidden = loadState !== 'ready';
  $('#exterior-panel').hidden = view === 'internal';
  $('#internal-panel').hidden = view === 'exterior';
  $('#locator').disabled = view === 'exterior' || loadState !== 'ready';
  const showOutline = $('#locator').checked && view !== 'exterior';
  $('#outline').hidden = !showOutline;
  // SVG elements do not implement HTMLElement.hidden consistently.
  $('#outline').style.display = showOutline ? '' : 'none';
  $('#exterior-title').textContent = t.exteriorAlt;
  $('#internal-title').textContent = t.internalAlt + (showOutline ? t.outlineAlt : '');
  $('#view-note').textContent = loadState === 'ready'
    ? (view === 'paired' ? t.pairNote : t.same) + (showOutline ? ' ' + t.locatorNote : '') : '';
}
$('form').addEventListener('change', event => {
  if (event.target.name === 'view') view = event.target.value;
  update();
});
$('#language').addEventListener('change', event => { language = event.target.value; update(); });
update();

try {
  const response = await fetch(source.url);
  if (!response.ok) throw new Error('Missing retained image');
  const bytes = await response.arrayBuffer();
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
    .map(x => x.toString(16).padStart(2, '0')).join('');
  if (digest !== source.sha256) throw new Error('Source identity mismatch');
  const blob = new Blob([bytes], { type: 'image/webp' });
  const bitmap = await createImageBitmap(blob);
  if (bitmap.width !== 1260 || bitmap.height !== 1436) throw new Error('Unexpected image dimensions');
  bitmap.close();
  const url = URL.createObjectURL(blob);
  document.querySelectorAll('svg image').forEach(el => el.setAttribute('href', url));
  loadState = 'ready';
} catch {
  loadState = 'error';
}
update();
