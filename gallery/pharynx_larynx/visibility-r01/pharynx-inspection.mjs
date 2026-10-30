// Visibility recipe for one reviewed export, not an anatomy/model registry.
export const SOURCE_SHA256 = 'd691a60f12d448b9b36d362270429c672c01c7fae0f10a8789ef188dd4c08530';
export const GROUPS = Object.freeze({
  cartilage: Object.freeze(['FJ2769', 'FJ2770', 'FJ2775', 'FJ2792', 'FJ2808']),
  muscles: Object.freeze(['FJ2740', 'FJ2742', 'FJ2743', 'FJ2745', 'FJ2746', 'FJ2747',
    'FJ2752', 'FJ2754', 'FJ2755', 'FJ2757', 'FJ2758', 'FJ2759', 'FJ2778', 'FJ2780',
    'FJ2782', 'FJ2784', 'FJ2785', 'FJ2788', 'FJ2796', 'FJ2798', 'FJ2800', 'FJ2802',
    'FJ2803', 'FJ2806', 'FJ2809']),
  supporting: Object.freeze(['FJ2749', 'FJ2771', 'FJ2807']),
});
const DISPUTED = Object.freeze({
  FJ2742: 'Middle pharyngeal constrictor — source laterality disputed (source: Right)',
  FJ2754: 'Middle pharyngeal constrictor — source laterality disputed (source: Left)',
});
const MODES = ['cartilage', 'muscles', 'all'];

export function createInspection(record, scene) {
  if (record.id !== 'pharynx_larynx__r03' || record.assetId !== 'draft_pharynx_larynx') return null;
  if (record.source?.sha256 !== SOURCE_SHA256) throw Error('Pharynx inspection source hash mismatch');
  if (record.cameraContract?.sourceViews) throw Error('Pharynx inspection conflicts with source visibility views');
  for (const [id, label] of Object.entries(DISPUTED)) {
    if (record.displayLabelOverrides?.[id] !== label) throw Error('Missing neutral source label: ' + id);
  }
  const expected = new Set(Object.values(GROUPS).flat()), parts = new Map(), original = new Map();
  scene.traverse(object => {
    original.set(object, object.visible);
    if (!object.isMesh) return;
    const id = object.userData?.source_file_id;
    if (!expected.has(id) || parts.has(id)) throw Error('Unexpected or duplicate pharynx part: ' + id);
    if (typeof object.userData.source_name !== 'string' || !object.userData.source_name.trim()) {
      throw Error('Missing pharynx source name: ' + id);
    }
    parts.set(id, object);
  });
  if (parts.size !== expected.size) throw Error('Missing pharynx source parts');
  let mode = 'all';
  const effectivelyVisible = object => {
    for (let current = object; current; current = current.parent) if (!current.visible) return false;
    return true;
  };
  return {
    get mode() { return mode; },
    select(next) {
      if (!MODES.includes(next)) throw Error('Unknown pharynx inspection mode');
      // Always restore the captured base visibility first, including ancestors.
      for (const [object, visible] of original) object.visible = visible;
      const show = new Set(next === 'cartilage' ? GROUPS.cartilage : [...GROUPS.cartilage, ...GROUPS.muscles]);
      if (next !== 'all') for (const [id, object] of parts) object.visible = original.get(object) && show.has(id);
      mode = next;
    },
    items() {
      return [...parts].map(([id, object]) => ({
        id,
        label: record.displayLabelOverrides?.[id] || object.userData.source_name,
        visible: effectivelyVisible(object),
      }));
    },
  };
}

const COPY = {
  en: {
    title: 'Inspect source layers', cartilage: 'Cartilage', muscles: 'Muscles + cartilage', all: 'Reset all parts',
    labels: 'Visible source labels',
    cartilageNote: 'Muscles, ligaments and the pharyngeal raphe are hidden for inspection.',
    musclesNote: 'Only the two ligaments and the pharyngeal raphe are hidden for inspection.',
    allNote: 'Original source visibility restored.',
    count: (shown, total) => `${shown} / ${total} source parts shown.`,
    positions: 'Positions and camera stay unchanged when switching layers. Drag to rotate; scroll to zoom.',
    limits: 'Dissected surfaces only; source epiglottic openings are retained. No continuous mucosal airway.',
    sides: 'FJ2742 / FJ2754: middle pharyngeal constrictors with disputed source sides; raw Left/Right names are not verified anatomical sides.',
  },
  zh: {
    title: '查看来源层次', cartilage: '软骨', muscles: '肌肉与软骨', all: '恢复全部结构',
    labels: '当前可见的来源标注',
    cartilageNote: '为便于观察，已隐藏肌肉、韧带与咽缝。',
    musclesNote: '为便于观察，仅隐藏两条韧带与咽缝。',
    allNote: '已恢复来源的初始可见状态。',
    count: (shown, total) => `显示 ${shown} / ${total} 个来源结构。`,
    positions: '切换层次时保留结构位置与相机。拖动旋转，滚动缩放。',
    limits: '仅展示解剖分离后的表面；保留来源会厌孔洞，不表示连续黏膜气道。',
    sides: 'FJ2742 / FJ2754 为来源侧别存在争议的咽中缩肌；原始 Left/Right 名称不视为已验证的解剖侧别。',
  },
};

export function mountInspection(record, scene, viewport) {
  const controller = createInspection(record, scene);
  if (!controller) return null;
  const doc = viewport.ownerDocument;
  const style = doc.createElement('link');
  style.rel = 'stylesheet';
  style.href = new URL('./pharynx-inspection.css', import.meta.url).href;
  doc.head.append(style);
  const panel = doc.createElement('div');
  panel.className = 'pharynx-inspection';
  panel.setAttribute('role', 'group');
  const title = doc.createElement('h2');
  title.id = 'pharynx-inspection-title';
  panel.setAttribute('aria-labelledby', title.id);
  const buttons = doc.createElement('div');
  buttons.className = 'pharynx-layer-buttons';
  const status = doc.createElement('p');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  const positions = doc.createElement('p'), limits = doc.createElement('p'), sides = doc.createElement('p');
  positions.className = limits.className = sides.className = 'pharynx-layer-note';
  const labels = doc.createElement('details'), summary = doc.createElement('summary'), list = doc.createElement('ul');
  labels.append(summary, list);
  panel.append(title, buttons, status, positions, limits, sides, labels);
  viewport.before(panel);
  let language = 'en';
  for (const mode of MODES) {
    const button = doc.createElement('button');
    button.type = 'button';
    button.dataset.layer = mode;
    button.onclick = () => { controller.select(mode); paint(language); };
    buttons.append(button);
  }
  function paint(lang = 'en') {
    language = lang === 'zh' ? 'zh' : 'en';
    const text = COPY[language], items = controller.items(), visible = items.filter(item => item.visible);
    title.textContent = text.title;
    for (const button of buttons.children) {
      button.textContent = text[button.dataset.layer];
      button.setAttribute('aria-pressed', String(button.dataset.layer === controller.mode));
    }
    status.textContent = `${text.count(visible.length, items.length)} ${text[controller.mode + 'Note']}`;
    positions.textContent = text.positions;
    limits.textContent = text.limits;
    sides.textContent = text.sides;
    summary.textContent = `${text.labels} (${visible.length})`;
    list.replaceChildren(...visible.map(item => {
      const row = doc.createElement('li');
      row.textContent = `${item.id} · ${item.label}`;
      return row;
    }));
  }
  paint();
  return {paint};
}
