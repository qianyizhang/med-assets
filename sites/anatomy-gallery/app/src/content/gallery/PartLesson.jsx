import React, { useEffect, useId, useRef, useState } from 'react';
import { byPath } from './catalog.js';
import { isLoopbackGallery } from './local-models.js';
import { fetchModelBytes } from './model-bytes.js';
import { loadScene } from './scene.js';
import teachingReview from './teaching-inputs/teaching-assessments.json';

function lessonFile(path) {
  const published = byPath.get(path);
  if (published || !isLoopbackGallery(globalThis.location?.hostname)) return published;
  const file = teachingReview.campaign.find((row) => row.maintained && row.export.path === path)?.export;
  return file && { ...file, name: path.split('/').at(-1) };
}

function positionView(layer, camera) {
  return { part: layer.label, material: 'Tissue', light: 1, camera };
}

// The shared camera is in atlas coordinates. A layer changes visible surfaces;
// switching files preserves the camera the learner last used.
export function PartLesson({ task }) {
  const [selected, setSelected] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [active, setActive] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [sceneState, setSceneState] = useState({ status: 'idle' });
  const [missingImage, setMissingImage] = useState('');
  const [point, setPoint] = useState(null);
  const questionId = useId();
  const answerId = useId();
  const host = useRef(null);
  const answerPanel = useRef(null);
  const revealButton = useRef(null);
  const engine = useRef(null);
  const camera = useRef(task.camera);
  const chosen = useRef(task.layers[0]);
  const pointer = useRef(null);
  const layer = task.layers[selected];
  const file = lessonFile(layer.path);
  const ready = active && sceneState.status === 'ready' && sceneState.path === layer.path;
  const failed = active && sceneState.status === 'failed' && sceneState.path === layer.path;

  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    const target = host.current;
    const path = layer.path;
    let owned;
    function lost() {
      camera.current = owned?.camera() ?? camera.current;
      setPoint(null);
      setSceneState({ path, status: 'failed', message: '3D was interrupted.' });
    }
    target.addEventListener('webglcontextlost', lost, true);
    (async () => {
      const asset = lessonFile(path);
      if (!asset) throw Error('This model is unavailable here.');
      const bytes = await fetchModelBytes(asset, controller.signal);
      const groups = Object.fromEntries(task.layers.filter((item) => item.path === path)
        .map((item) => [item.label, item.nodes ?? null]));
      owned = await loadScene(target, bytes, positionView(chosen.current, camera.current), controller.signal, { groups });
      if (controller.signal.aborted) { owned.dispose(); return; }
      owned.apply(positionView(chosen.current, camera.current));
      engine.current = owned;
      setSceneState({ path, status: 'ready' });
    })().catch((error) => {
      if (!controller.signal.aborted) setSceneState({ path, status: 'failed', message: error.message });
    });
    return () => {
      controller.abort();
      target.removeEventListener('webglcontextlost', lost, true);
      if (engine.current === owned) engine.current = null;
      owned?.dispose();
    };
  }, [active, attempt, layer.path, task]);

  useEffect(() => {
    if (!revealed) return;
    answerPanel.current.focus({ preventScroll: true });
    answerPanel.current.scrollIntoView({ block: 'nearest' });
  }, [revealed]);

  function choose(index) {
    const next = task.layers[index];
    if (ready && engine.current) {
      camera.current = engine.current.camera();
      if (next.path === layer.path) engine.current.apply(positionView(next, camera.current));
    }
    if (active && next.path !== layer.path) setSceneState({ status: 'loading' });
    chosen.current = next;
    setSelected(index);
    setMissingImage('');
  }

  function toggle3D() {
    if (ready) {
      camera.current = task.camera;
      setActive(false);
    } else {
      setSceneState({ status: 'loading' });
      setActive(true);
      setAttempt((n) => n + 1);
    }
    setPoint(null);
  }

  function placePoint(event) {
    const start = pointer.current;
    pointer.current = null;
    if (!start || start.id !== event.pointerId || Math.hypot(event.clientX - start.x, event.clientY - start.y) > 5) return;
    const rect = event.currentTarget.getBoundingClientRect();
    setPoint({ x: (event.clientX - rect.left) / rect.width, y: (event.clientY - rect.top) / rect.height, live: ready });
  }
  function movePoint(event) {
    const delta = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1], ' ': [0, 0], Enter: [0, 0] }[event.key];
    if (!delta) return;
    event.preventDefault();
    const limit = (n) => Math.min(1, Math.max(0, n));
    setPoint((previous) => {
      const p = previous?.live === ready ? previous : null;
      return { x: limit((p?.x ?? 0.5) + delta[0] * 0.025), y: limit((p?.y ?? 0.5) + delta[1] * 0.025), live: ready };
    });
  }

  return <section className="ga-part-lesson" aria-labelledby={questionId}>
    <h2 id={questionId}>{task.question}</h2>
    {task.instruction && <p>{task.instruction}</p>}
    <div className="ga-part-layout">
      <div className="ga-part-frame" role="group" tabIndex={0} aria-label="Anatomy view" aria-describedby={questionId + '-point'}
        onKeyDown={movePoint} onWheel={() => setPoint(null)}
        onPointerDown={(e) => { pointer.current = { id: e.pointerId, x: e.clientX, y: e.clientY }; setPoint(null); }}
        onPointerCancel={() => { pointer.current = null; }} onPointerUp={placePoint}>
        <div ref={host} className="ga-part-canvas" style={{ visibility: ready ? 'visible' : 'hidden' }} />
        {!ready && (missingImage === layer.image.src
          ? <span className="ga-part-unavailable" role="status">Reference image unavailable. You can still reveal the answer.</span>
          : <img src={layer.image.src} alt={layer.image.alt} onError={() => setMissingImage(layer.image.src)} />)}
        {point?.live === ready && <span className="ga-part-point" aria-hidden="true" style={{ left: (100 * point.x) + '%', top: (100 * point.y) + '%' }} />}
      </div>
      <div className="ga-part-options">
        <fieldset><legend>Tissue layers</legend>
          {task.layers.map((item, index) => <label key={item.label}>
            <input type="radio" name={questionId} checked={selected === index} onChange={() => choose(index)} />
            {item.label}
          </label>)}
        </fieldset>
        {file && <button type="button" onClick={toggle3D} disabled={active && !ready && !failed}>
          {ready ? 'Use reference image' : failed ? 'Retry 3D' : active ? 'Loading 3D…' : 'Inspect in 3D'}
        </button>}
        {ready && <button type="button" onClick={() => { camera.current = task.camera; engine.current.apply(positionView(layer, task.camera)); setPoint(null); }}>Reset view</button>}
        {failed && <p role="status">{sceneState.message} You can switch layers or reveal the answer.</p>}
        <p className="ga-part-hint" id={questionId + '-point'}>Click to mark a spot across layers, or focus the view and use the arrow keys.</p>
        <button ref={revealButton} type="button" className="ga-part-reveal" aria-expanded={revealed} aria-controls={answerId}
          onClick={() => setRevealed((value) => !value)}>{revealed ? 'Hide answer' : 'Reveal answer'}</button>
      </div>
    </div>
    <div className="ga-part-answer" ref={answerPanel} id={answerId} hidden={!revealed}
      role="region" aria-label="Labelled answer" tabIndex={-1}
      onKeyDown={(event) => {
        if (event.key === 'Escape') { setRevealed(false); revealButton.current.focus(); }
      }}>
      {revealed && <><p>{task.answer}</p>{task.answerImage &&
        <a href={task.answerImage.src} aria-label="Open full labelled answer"><img src={task.answerImage.src} alt={task.answerImage.alt} /></a>}</>}
    </div>
  </section>;
}
