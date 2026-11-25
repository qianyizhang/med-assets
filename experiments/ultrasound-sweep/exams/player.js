const byId = (id) => document.getElementById(id);
const record = JSON.parse(byId('record').textContent);
const owner = document.querySelector('main').dataset.owner;
const scan = byId('scan').getContext('2d');
const locator = byId('pose').getContext('2d');
const chapterPicker = byId('chapter');
const seek = byId('seek');
const play = byId('play');
const status = byId('status');
const report = byId('evidence');
let chapters, module, offsets, length;
let stopAt;
const overlayButton = byId('overlay');
const orbit = byId('orbit');
let overlay = false,
  yaw = 0,
  previousLegend = '';
function updateLegend(entries) {
  const list = byId('legend');
  list.hidden = !overlay;
  if (overlay && !entries?.length)
    entries = [{ label: 'No identifiable tissue in this frame', color: 'transparent' }];
  const key = JSON.stringify(entries || []);
  if (key === previousLegend) return;
  previousLegend = key;
  list.replaceChildren(
    ...(entries || []).map(({ label, color }) => {
      const li = document.createElement('li'),
        dot = document.createElement('i');
      dot.style.backgroundColor = color;
      dot.setAttribute('aria-hidden', 'true');
      li.append(dot, document.createTextNode(label));
      return li;
    }),
  );
}
let current = 0,
  lastChapter = -1,
  animation = 0,
  lastTime = 0;

// Ten sampled frames per second keeps acquisitions readable and makes the
// linked observation land on exactly the same frame after seeking.
const frameMs = 100;
function stop() {
  cancelAnimationFrame(animation);
  animation = 0;
  play.textContent = current === length - 1 ? 'Play exam again' : 'Play full exam';
}
function show(index) {
  current = Math.max(0, Math.min(length - 1, index));
  const chapterIndex = offsets.findLastIndex((start) => start <= current);
  const c = chapters[chapterIndex];
  const frame = current - offsets[chapterIndex];
  for (const [ctx, render] of [
    [scan, module.render],
    [locator, module.pose],
  ]) {
    ctx.save();
    try {
      ctx.fillStyle = '#101c22';
      ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
      const entries = render(ctx, c, frame, record, { overlay, yaw });
      if (ctx === scan) updateLegend(entries);
    } finally {
      ctx.restore();
    }
  }
  if (lastChapter !== chapterIndex) {
    chapterPicker.value = String(chapterIndex);
    byId('view').textContent = c.title;

    lastChapter = chapterIndex;
  }
  const saved = frame === c.evidenceFrame;
  byId('observationCue').textContent = saved
    ? 'At this frame'
    : 'Saved observation · frame ' + (c.evidenceFrame + 1);
  const observation = byId('observationLink');
  observation.textContent = c.observation;
  observation.href = report.querySelectorAll('a')[chapterIndex].href;
  observation.onclick = (event) => {
    if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      event.preventDefault();
      jump(chapterIndex, c.evidenceFrame);
    }
  };
  byId('finished').hidden = current !== length - 1;
  seek.value = current;
  byId('position').textContent =
    `Chapter ${chapterIndex + 1} / ${chapters.length} · Frame ${frame + 1} / ${c.frames}`;
  seek.setAttribute('aria-valuetext', c.title + ', frame ' + (frame + 1) + ' of ' + c.frames);
  byId('value').textContent = frame === c.evidenceFrame ? c.measurement || 'Recorded view' : '';
}
function failed(error) {
  stop();
  byId('exam').hidden = true;
  status.hidden = false;
  status.textContent = 'This acquisition could not be displayed. The worked views and report remain available.';
  console.error(error);
}
function tick(time) {
  if (time - lastTime >= frameMs) {
    try {
      show(current + 1);
    } catch (error) {
      failed(error);
      return;
    }
    lastTime = time;
    if (current >= stopAt) {
      stop();
      return;
    }
  }
  animation = requestAnimationFrame(tick);
}
function start(end = length - 1) {
  stopAt = end;
  stop();
  lastTime = performance.now();
  play.textContent = 'Pause exam';
  animation = requestAnimationFrame(tick);
}
function jump(index, frame) {
  stop();
  show(offsets[index] + frame);
  const url = new URL(location.href);
  url.searchParams.set('chapter', chapters[index].id);
  url.searchParams.set('frame', frame);
  history.replaceState(null, '', url);
}
try {
  module = await import('../cases/' + owner + '/playable.js');
  chapters = module.chapters(record);
  if (!chapters.length || new Set(chapters.map((c) => c.id)).size !== chapters.length)
    throw new Error('Invalid chapter IDs');
  const bindings = new Set(record.views.map((v) => v.image));
  let offset = 0;
  offsets = chapters.map((c, i) => {
    if (
      !bindings.has(c.viewImage) ||
      !Number.isInteger(c.frames) ||
      c.frames < 3 ||
      !Number.isInteger(c.evidenceFrame) ||
      c.evidenceFrame < 0 ||
      c.evidenceFrame >= c.frames
    )
      throw new Error('Invalid chapter ' + c.id);
    chapterPicker.add(new Option(c.title, i));
    const a = report.querySelectorAll('a')[i];
    if (!a || new URL(a.href).searchParams.get('chapter') !== c.id) throw new Error('Unbound report link ' + c.id);
    a.onclick = (e) => {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      jump(i, c.evidenceFrame);
      byId('exam').scrollIntoView();
      byId('keyframe').focus({ preventScroll: true });
    };
    const start = offset;
    offset += c.frames;
    return start;
  });
  if (record.views.some((v) => !chapters.some((c) => c.viewImage === v.image)))
    throw new Error('Unmapped worked view');
  length = offset;
  seek.max = length - 1;
  overlayButton.onclick = () => {
    overlay = !overlay;
    overlayButton.setAttribute('aria-pressed', String(overlay));
    show(current);
  };
  orbit.oninput = () => {
    yaw = (Number(orbit.value) * Math.PI) / 180;
    byId('yaw').value = orbit.value + '°';
    show(current);
  };
  byId('resetView').onclick = () => {
    orbit.value = 0;
    orbit.oninput();
  };
  chapterPicker.onchange = () => jump(Number(chapterPicker.value), 0);
  byId('keyframe').onclick = () => jump(lastChapter, chapters[lastChapter].evidenceFrame);
  byId('replay').onclick = () => {
    jump(lastChapter, 0);
    start(offsets[lastChapter] + chapters[lastChapter].frames - 1);
  };
  play.onclick = () => {
    if (animation) {
      stop();
      return;
    }
    if (current === length - 1) show(0);
    start();
  };
  seek.oninput = () => {
    stop();
    show(Number(seek.value));
  };
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
  });
  const params = new URLSearchParams(location.search);
  const initial = Math.max(
    0,
    chapters.findIndex((c) =>
      params.has('chapter') ? c.id === params.get('chapter') : c.viewImage === params.get('view'),
    ),
  );
  const frame = Math.min(
    Math.max(
      0,
      Number.parseInt(params.get('frame'), 10) ||
        (params.has('view') && !params.has('chapter') ? chapters[initial].evidenceFrame : 0),
    ),
    chapters[initial].frames - 1,
  );
  show(offsets[initial] + frame);
  byId('exam').hidden = false;
  status.hidden = true;
} catch (error) {
  failed(error);
}
