import {COPY, initialState, validateCoverage, describe, plateSVG, step} from './plate.mjs';

export function mount(root, coverage) {
  const teeth = validateCoverage(coverage), doc = root.ownerDocument;
  const stage = root.querySelector('#plate');
  let state = initialState();
  let renderedWidth = 0;
  function render(focusTooth = false) {
    const c = COPY[state.lang], id = state.selected[state.arch], t = describe(id, state.lang);
    const wasFocused = stage.contains(doc.activeElement);
    doc.documentElement.lang = state.lang === 'zh' ? 'zh-CN' : 'en';
    doc.title = `${c.title} · FDI ${id}`;
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
    stage.innerHTML = plateSVG(state, renderedWidth);
    const image = stage.querySelector('image'), arch = state.arch;
    image?.addEventListener('error', () => dispatch({type: 'image', arch, available: false}), {once: true});
    if (focusTooth || wasFocused) stage.querySelector(`[role="radio"][data-fdi="${id}"]`).focus();
  }
  function dispatch(action, focusTooth = false) { state = step(state, action); render(focusTooth); }
  function click(event) {
    const tooth = event.target.closest('[data-fdi]');
    if (tooth) dispatch({type: 'select', value: tooth.dataset.fdi}, true);
    const arch = event.target.closest('[data-arch]');
    if (arch) dispatch({type: 'arch', value: arch.dataset.arch});
    const language = event.target.closest('[data-lang]');
    if (language) dispatch({type: 'language', value: language.dataset.lang});
    if (event.target.closest('#retry')) dispatch({type: 'image', arch: state.arch, available: true});
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
    root.removeEventListener('click', click); stage.removeEventListener('keydown', keydown); observer?.disconnect();
  }};
}
