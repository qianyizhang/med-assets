import {COPY, MEDIA, initialState, validateCoverage, describe, plateSVG, step} from './plate.mjs';

export function mount(root, coverage, {
  imageSources = arch => [MEDIA + arch + '-occlusal-teeth.png'],
  standalone = true,
  initialArch = 'upper',
} = {}) {
  const teeth = validateCoverage(coverage), doc = root.ownerDocument;
  const stage = root.querySelector('#plate');
  let state = step(initialState(), {type: 'arch', value: initialArch});
  const sources = Object.fromEntries(Object.keys(state.image).map(arch => [arch, imageSources(arch)]));
  const sourceIndex = {upper: 0, lower: 0};
  for (const arch of Object.keys(state.image)) state.image[arch] = sources[arch].length > 0;
  let renderedWidth = 0;
  let destroyed = false;
  function render(focusTooth = false) {
    if (destroyed) return;
    const c = COPY[state.lang], id = state.selected[state.arch], t = describe(id, state.lang);
    const wasFocused = stage.contains(root.getRootNode().activeElement);
    const language = state.lang === 'zh' ? 'zh-CN' : 'en';
    root.lang = language;
    if (standalone) {
      doc.documentElement.lang = language;
      doc.title = `${c.title} · FDI ${id}`;
    }
    root.querySelectorAll('[data-copy]').forEach(el => { el.textContent = c[el.dataset.copy]; });
    root.querySelectorAll('[data-lang]').forEach(el => el.setAttribute('aria-pressed', String(el.dataset.lang === state.lang)));
    root.querySelectorAll('[data-arch]').forEach(el => el.setAttribute('aria-pressed', String(el.dataset.arch === state.arch)));
    root.querySelector('#screen-left').textContent = c[state.arch === 'upper' ? 'right' : 'left'];
    root.querySelector('#screen-right').textContent = c[state.arch === 'upper' ? 'left' : 'right'];
    root.querySelector('#fdi').textContent = `FDI ${id}`;
    root.querySelector('#identity').innerHTML = ['arch', 'side', 'class'].map(k => `<div><dt>${c[k]}</dt><dd>${t[k]}</dd></div>`).join('');
    root.querySelector('#fdi').dataset.source = teeth.get(id).bp3d.source_object;
    root.querySelector('#missing').textContent = state.arch === 'upper' ? '18 · 28' : '38 · 48';
    root.querySelector('#image-error').hidden = state.image[state.arch];
    renderedWidth = stage.getBoundingClientRect().width || 640;
    const imageSrc = sources[state.arch][sourceIndex[state.arch]];
    const retry = root.querySelector('#retry');
    retry.disabled = !imageSrc;
    stage.innerHTML = plateSVG(state, renderedWidth, {imageUrl: imageSrc});
    const image = stage.querySelector('image'), arch = state.arch;
    image?.addEventListener('error', () => {
      // Only this mount's current, attached image owns its availability state.
      if (image.isConnected && stage.querySelector('image') === image) {
        if (sourceIndex[arch] + 1 < sources[arch].length) {
          sourceIndex[arch]++;
          render();
        } else {
          dispatch({type: 'image', arch, available: false});
        }
      }
    }, {once: true});
    if (focusTooth || wasFocused) stage.querySelector(`[role="radio"][data-fdi="${id}"]`).focus();
  }
  function dispatch(action, focusTooth = false) {
    if (destroyed) return;
    state = step(state, action); render(focusTooth);
  }
  function click(event) {
    const tooth = event.target.closest('[data-fdi]');
    if (tooth) dispatch({type: 'select', value: tooth.dataset.fdi}, true);
    const arch = event.target.closest('[data-arch]');
    if (arch) dispatch({type: 'arch', value: arch.dataset.arch});
    const language = event.target.closest('[data-lang]');
    if (language) dispatch({type: 'language', value: language.dataset.lang});
    if (event.target.closest('#retry') && sources[state.arch].length) {
      sourceIndex[state.arch] = 0;
      dispatch({type: 'image', arch: state.arch, available: true}, true);
    }
  }
  function keydown(event) {
    if (!event.target.closest('[role="radio"]')) return;
    if (['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End',' ','Enter'].includes(event.key)) {
      event.preventDefault();
      dispatch([' ', 'Enter'].includes(event.key)
        ? {type: 'select', value: event.target.closest('[role="radio"]').dataset.fdi}
        : {type: 'key', key: event.key}, true);
    }
  }
  root.addEventListener('click', click);
  stage.addEventListener('keydown', keydown);
  root.querySelector('#boot').hidden = true;
  root.querySelector('.content').hidden = false;
  render();
  // Recalculate SVG labels in screen pixels while preserving the focused FDI.
  const Resize = doc.defaultView.ResizeObserver;
  const observer = Resize ? new Resize(() => {
    const width = stage.getBoundingClientRect().width;
    if (width && Math.abs(width - renderedWidth) > .5) render();
  }) : null;
  observer?.observe(stage);
  return {getState: () => structuredClone(state), destroy() {
    destroyed = true;
    root.removeEventListener('click', click); stage.removeEventListener('keydown', keydown); observer?.disconnect();
  }};
}
