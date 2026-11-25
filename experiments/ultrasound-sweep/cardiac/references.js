// One media request is active per selection. Late loads cannot replace another window.
const el = id => document.getElementById(id);
const sourceLink = (text, url) => Object.assign(document.createElement('a'), {textContent: text, href: url});

export function createReferences() {
  const select = el('ref-select'), still = el('ref-still'), video = el('ref-video'), canvas = el('reference');
  let view, active = false, modelPhase = 0, generation = 0, bundle, atlas, current, lastFrame = -1;
  let manifest;
  async function records() {
    const get = async path => {
      const r = await fetch(path);
      if (!r.ok) throw new Error('Acquisition catalogue unavailable');
      return r.json();
    };
    manifest ??= Promise.all([get('reference/sources.json'), get('acquisition.json')]).then(([group, a4c]) => {
      group.cine.a4c = {...a4c, file: '../' + a4c.file};
      return group;
    }).catch(e => { manifest = null; throw e; });
    return manifest;
  }
  function clear() {
    ++generation;
    atlas = current = null;
    lastFrame = -1;
    video.pause();
    if (video.hasAttribute('src')) { video.removeAttribute('src'); video.load(); }
    still.removeAttribute('src');
    for (const node of [canvas, still, video]) node.hidden = true;
    delete canvas.dataset.frame;
    el('credit').replaceChildren();
    el('ref-status').hidden = false;
    el('ref-status').textContent = 'Loading acquired example…';
  }
  function draw(phase) {
    modelPhase = phase;
    if (!active || !atlas) return;
    const {landmarks, columns, frameCount, tileWidth:w, tileHeight:h} = current;
    const j = landmarks.findIndex(([p], i) => i && p >= phase);
    const [pa,fa] = landmarks[j-1], [pb,fb] = landmarks[j];
    const f = Math.round(fa + (fb-fa)*(phase-pa)/(pb-pa)) % frameCount;
    if (f === lastFrame) return;
    canvas.getContext('2d').drawImage(atlas, f%columns*w, Math.floor(f/columns)*h,w,h,0,0,w,h);
    canvas.dataset.frame = f;
    lastFrame = f;
  }
  async function load(viewId, choice) {
    clear();
    const token = generation;
    try {
      bundle = await records();
      if (token !== generation) return;
      const cine = bundle.cine[viewId];
      select.replaceChildren();
      if (cine) select.add(new Option(cine.landmarks ? 'Phase-matched cine' : 'Original cine', 'cine'));
      for (const {number,label} of bundle.panels[viewId]) select.add(new Option(label, String(number)));
      if (choice) select.value = choice;
      const useCine = select.value === 'cine';
      const record = useCine ? cine : bundle.bse;
      el('credit').replaceChildren(sourceLink(record.credit, record.url), ' · ', sourceLink(record.license, record.licenseUrl));
      const note = useCine ? (cine.landmarks ? 'Different case · matched by cardiac phase' : 'Different case · recorded timing') : 'Published still · original markings and measurements';
      el('ref-description').textContent = note;
      if (useCine && !cine.landmarks) {
        video.src = 'reference/' + cine.file;
        video.hidden = false;
        video.onerror = () => { if (generation === token && video.getAttribute('src')) fail(); };
      } else {
        const image = new Image();
        const path = useCine ? 'reference/' + cine.file : 'reference/bse/ERP-20-0026inf' + select.value + '.jpg';
        image.src = path;
        await image.decode();
        if (token !== generation) return;
        if (useCine) {
          if (image.width !== cine.columns*cine.tileWidth ||
              image.height !== Math.ceil(cine.frameCount/cine.columns)*cine.tileHeight) throw new Error('Cine dimensions');
          current = cine;
          atlas = image;
          canvas.width = cine.tileWidth; canvas.height = cine.tileHeight;
          canvas.hidden = false;
          draw(modelPhase);
        } else {
          still.alt = select.selectedOptions[0].textContent + ', published echocardiographic example';
          still.src = path;
          still.hidden = false;
        }
      }
      el('ref-status').hidden = true;
    } catch { if (generation === token) fail(); }
  }
  function fail() {
    el('ref-status').hidden = false;
    el('ref-status').textContent = 'Acquired example unavailable. Reopen References to retry.';
  }
  select.onchange = () => load(view, select.value);
  return {draw, show(viewId, visible) {
    if (view === viewId && active === visible) return;
    view = viewId; active = visible;
    if (active) load(viewId); else clear();
  }};
}
