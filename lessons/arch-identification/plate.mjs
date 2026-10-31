// Editorial crown locators in the unchanged 1100 × 1000 source images.
// The coverage receipt owns identity; these points own only this 2D presentation.
export const MEDIA = '../../reviews/teeth_gums/2026-10-26-set-contact-checkpoint/media/';
export const COVERAGE = '../../docs/dental-atlas/set-coverage.json';
export const PLACEMENTS = {
  upper: {
    '11': [480, 165, 470, 68], '12': [350, 210, 325, 110],
    '13': [250, 290, 175, 185], '14': [210, 420, 385, 410],
    '15': [160, 530, 355, 545], '16': [140, 670, 345, 690],
    '17': [140, 830, 335, 850], '21': [620, 165, 630, 68],
    '22': [750, 210, 775, 110], '23': [850, 290, 925, 185],
    '24': [890, 420, 715, 410], '25': [940, 530, 745, 545],
    '26': [960, 670, 755, 690], '27': [960, 830, 765, 850],
  },
  lower: {
    '31': [500, 155, 470, 68], '32': [415, 180, 325, 110],
    '33': [345, 255, 175, 185], '34': [285, 335, 420, 420],
    '35': [240, 440, 385, 560], '36': [200, 570, 365, 700],
    '37': [155, 740, 345, 850], '41': [600, 155, 630, 68],
    '42': [685, 180, 775, 110], '43': [755, 255, 925, 185],
    '44': [815, 335, 680, 420], '45': [860, 440, 715, 560],
    '46': [900, 570, 735, 700], '47': [945, 740, 755, 850],
  },
};
export const COPY = {
  en: {
    title: 'Name the tooth', eyebrow: 'DENTAL ATLAS · 28 SOURCE LABELS',
    intro: 'Choose an arch, then a numbered crown locator.',
    upper: 'Upper arch', lower: 'Lower arch', arch: 'Arch',
    right: 'Patient right', left: 'Patient left', side: 'Patient side',
    front: 'Front', class: 'Tooth class', selected: 'Selected tooth',
    help: 'Tab to the plate · Arrow keys move along the arch · Home / End',
    coverage: 'Third-molar source coverage unavailable',
    absence: 'This does not mean these teeth are absent in a patient.',
    scope: 'Source-labelled exterior identification; contacts and bite are not validated.',
    details: 'Source & scope', source: 'BodyParts3D / DBCLS · CC BY 4.0',
    limits: 'Existing reduced-resolution atlas images, unchanged. Leaders locate visible crowns; they do not outline a tooth or measure anatomy. No new anatomy or clinical approval.',
    attribution: 'Attribution', receipt: 'Source review',
    unavailable: 'Arch image unavailable', retry: 'Retry image',
    fallback: 'FDI selection remains available below.',
    loading: 'Loading source labels…', dataError: 'Source labels unavailable. Reload to try again.',
    classes: ['Central incisor', 'Lateral incisor', 'Canine', 'First premolar', 'Second premolar', 'First molar', 'Second molar'],
  },
  zh: {
    title: '认识每一颗牙', eyebrow: '牙列图谱 · 28 个来源标签',
    intro: '选择上、下牙弓，再选择牙冠定位编号。',
    upper: '上牙弓', lower: '下牙弓', arch: '牙弓',
    right: '患者右侧', left: '患者左侧', side: '患者侧别',
    front: '前方', class: '牙齿类型', selected: '当前牙齿',
    help: 'Tab 进入图板 · 方向键沿牙弓选择 · Home / End 跳至两端',
    coverage: '第三磨牙来源覆盖尚缺',
    absence: '这不表示患者在临床上缺少这些牙齿。',
    scope: '用于辨认来源标注的牙外形；邻牙接触与咬合尚未验证。',
    details: '来源与范围', source: 'BodyParts3D / DBCLS · CC BY 4.0',
    limits: '沿用低分辨率图谱原图。引线定位可见牙冠，不描绘牙齿边界、不测量解剖结构。未新增解剖结构，未获临床认可。',
    attribution: '来源署名', receipt: '来源审阅',
    unavailable: '牙弓图像暂不可用', retry: '重试图像',
    fallback: '仍可在下方选择 FDI 编号。',
    loading: '正在读取来源标签…', dataError: '来源标签暂不可用，请刷新重试。',
    classes: ['中切牙', '侧切牙', '尖牙', '第一前磨牙', '第二前磨牙', '第一磨牙', '第二磨牙'],
  },
};
export const escapeXML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
export function initialState() {
  return {arch: 'upper', lang: 'en', selected: {upper: '11', lower: '31'}, image: {upper: true, lower: true}};
}
export function validateCoverage(coverage) {
  const teeth = coverage.teeth.filter(t => t.bp3d);
  const ids = Object.values(PLACEMENTS).flatMap(Object.keys).sort();
  if (teeth.length !== 28 || teeth.map(t => t.fdi).sort().join() !== ids.join()
      || new Set(teeth.map(t => t.bp3d.source_object)).size !== 28) throw Error('Unexpected source coverage');
  return new Map(teeth.map(t => [t.fdi, t]));
}
// Screen-left posterior → anterior → screen-right posterior in both images.
export function order(arch) {
  const [left, right] = arch === 'upper' ? ['1', '2'] : ['3', '4'];
  return [7, 6, 5, 4, 3, 2, 1].map(n => left + n).concat([1, 2, 3, 4, 5, 6, 7].map(n => right + n));
}
export function describe(fdi, lang) {
  const c = COPY[lang], q = Number(fdi[0]);
  return {arch: c[q < 3 ? 'upper' : 'lower'], side: c[q === 1 || q === 4 ? 'right' : 'left'], class: c.classes[Number(fdi[1]) - 1]};
}
export function accessibleName(fdi, lang) {
  const t = describe(fdi, lang);
  return `FDI ${fdi} · ${t.arch} · ${t.side} · ${t.class}`;
}
export function step(state, action) {
  const next = structuredClone(state);
  if (action.type === 'arch' && PLACEMENTS[action.value]) next.arch = action.value;
  if (action.type === 'language' && COPY[action.value]) next.lang = action.value;
  if (action.type === 'select' && PLACEMENTS[next.arch][action.value]) next.selected[next.arch] = action.value;
  if (action.type === 'image' && action.arch === next.arch) next.image[next.arch] = action.available;
  if (action.type === 'key') {
    const ids = order(next.arch), i = ids.indexOf(next.selected[next.arch]);
    if (action.key === 'Home') next.selected[next.arch] = ids[0];
    else if (action.key === 'End') next.selected[next.arch] = ids.at(-1);
    else if (['ArrowRight', 'ArrowDown'].includes(action.key)) next.selected[next.arch] = ids[(i + 1) % ids.length];
    else if (['ArrowLeft', 'ArrowUp'].includes(action.key)) next.selected[next.arch] = ids[(i + ids.length - 1) % ids.length];
  }
  return next;
}
export function geometry(state, width) {
  const available = state.image[state.arch], unit = 1100 / Math.max(240, width);
  const size = (width < 500 ? 28 : 36) * unit;
  return Object.entries(PLACEMENTS[state.arch]).map(([fdi, [x, y, lx, ly]]) => ({
    fdi, x, y, lx: available ? lx : (Number(fdi[0]) % 2 ? 330 : 770),
    ly: available ? ly : size / 2 + 12 * unit + (Number(fdi[1]) - 1) * (size + 8 * unit), size, font: 14 * unit,
  }));
}
export function plateHeight(state, width) {
  return state.image[state.arch] ? 1000 : (7 * (width < 500 ? 36 : 44) + 16) * 1100 / Math.max(240, width);
}
// Shared by the live page and offline render review. No embedded raster copies.
export function plateSVG(state, width = 640, {media = MEDIA, original = false} = {}) {
  const available = state.image[state.arch], height = plateHeight(state, width);
  const c = COPY[state.lang], selected = state.selected[state.arch], unit = 1100 / Math.max(240, width);
  const marks = geometry(state, width);
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1100 ${height}" width="${width}" height="${width * height / 1100}" role="radiogroup" aria-label="${c[state.arch]} · FDI" aria-describedby="keyboard-help">
    <style>.tooth{cursor:pointer;outline:none}.tooth:focus .tag{stroke:#fff;stroke-width:3px}.hit{cursor:pointer}</style>
    <rect width="1100" height="${height}" fill="#232729"/>
    ${available ? `<image href="${escapeXML(media + state.arch + '-occlusal-teeth.png')}" xlink:href="${escapeXML(media + state.arch + '-occlusal-teeth.png')}" width="1100" height="1000"/>` : ''}
    ${original ? '' : marks.map(p => {
      const active = p.fdi === selected, color = active ? '#a8f0df' : '#b3c2c5';
      return `${available ? `<g aria-hidden="true" fill="none" stroke="${color}" stroke-width="${active ? 2 : 1}" vector-effect="non-scaling-stroke">
        <path d="M${p.lx},${p.ly} L${p.x},${p.y}" vector-effect="non-scaling-stroke"/>
        <circle cx="${p.x}" cy="${p.y}" r="${(active ? 5 : 2.5) * unit}" fill="#232729" vector-effect="non-scaling-stroke"/>
        </g><circle class="hit" data-fdi="${p.fdi}" aria-hidden="true" cx="${p.x}" cy="${p.y}" r="28" fill="#000" fill-opacity="0"/>` : ''}
      <g class="tooth" data-fdi="${p.fdi}" role="radio" tabindex="${active ? 0 : -1}" aria-checked="${active}" aria-label="${escapeXML(accessibleName(p.fdi, state.lang))}">
        <rect class="tag" x="${p.lx - p.size / 2}" y="${p.ly - p.size / 2}" width="${p.size}" height="${p.size}" rx="${5 * unit}" fill="${active ? '#a8f0df' : '#182326'}" stroke="${color}" stroke-width="1" vector-effect="non-scaling-stroke"/>
        <text x="${p.lx}" y="${p.ly}" dy=".35em" text-anchor="middle" fill="${active ? '#122826' : '#f1f5f5'}" font-family="sans-serif" font-size="${p.font}" font-weight="600">${p.fdi}</text>
      </g>`;
    }).join('')}
  </svg>`;
}
