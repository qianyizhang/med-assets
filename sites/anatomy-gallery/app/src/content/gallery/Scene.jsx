import React, { useEffect, useRef, useState } from 'react';
import { adrenalScene } from './adrenal-study.js';
import { portrait, route } from './catalog.js';
import { localScene, stagePath, viewAsset } from './presets.js';
import teachingReview from './teaching-inputs/teaching-assessments.json';
import { isLoopbackGallery } from './local-models.js';
import { fetchModelBytes } from './model-bytes.js';
import { loadScene } from './scene.js';

async function modelBytes(file, initial, signal) {
  if (file) {
    if (file.size > 64_000_000) throw Error('Choose a GLB smaller than 64 MB.');
    return file.arrayBuffer();
  }
  const asset = viewAsset(initial);
  return fetchModelBytes(asset, signal);
}

export function Scene({ initial, origin, stage = false, auto = false, file = null }) {
  const model = localScene(initial);
  const [active, setActive] = useState(auto),
    [attempt, setAttempt] = useState(0);
  const [view, setView] = useState(initial),
    [status, setStatus] = useState(''),
    [ready, setReady] = useState(false);
  const [names, setNames] = useState(model ? [] : adrenalScene.parts),
    [shared, setShared] = useState('');
  const container = useRef(null),
    engine = useRef(null),
    latest = useRef(initial);
  function change(next) {
    try {
      engine.current?.apply(next);
      latest.current = next;
      setView(next);
      setShared('');
    } catch (e) {
      setStatus(e.message);
    }
  }
  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    const host = container.current;
    let owned;
    function lost(event) {
      event.preventDefault();
      setStatus('3D rendering was interrupted. The reference view is available below.');
      setReady(false);
    }
    host.addEventListener('webglcontextlost', lost, true);
    setStatus('Loading 3D scene…');
    setReady(false);
    (async () => {
      const bytes = await modelBytes(file, initial, controller.signal);
      controller.signal.throwIfAborted();
      owned = await loadScene(host, bytes, latest.current, controller.signal, model?.scene);
      if (controller.signal.aborted) {
        owned.dispose();
        return;
      }
      engine.current = owned;
      setNames(owned.names);
      setReady(true);
      setStatus('');
    })().catch((e) => {
      if (!controller.signal.aborted) setStatus(e.message);
    });
    return () => {
      controller.abort();
      host.removeEventListener('webglcontextlost', lost, true);
      owned?.dispose();
      engine.current = null;
    };
  }, [active, attempt, file, initial.version, initial.revision]);
  const state = () => ({ ...view, camera: engine.current?.camera() ?? view.camera });
  const absolute = () => new URL(route(stagePath(state(), origin)), location.origin + '/').href;
  async function share() {
    const link = absolute();
    setShared(link);
    try {
      await navigator.clipboard.writeText(link);
      setStatus('Preset link copied.');
    } catch {
      setStatus('Select and copy the preset link below.');
    }
  }
  async function saveImage() {
    try {
      const source = file ? file.name : absolute();
      const blob = await engine.current.export(source);
      const url = URL.createObjectURL(blob),
        a = document.createElement('a');
      a.href = url;
      a.download = (file ? 'local-scene' : model ? view.revision : 'adrenal-' + view.revision) + '-stage.webp';
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      if (!file) setShared(source);
      setStatus(file ? 'WebP exported.' : 'WebP exported with its preset link embedded.');
    } catch (e) {
      setStatus(e.message);
    }
  }
  const showReview = model && isLoopbackGallery(globalThis.location?.hostname)
    && (origin === model.library || model.scene.posterPath || model.lesson === origin);
  const assessment = showReview ? teachingReview.campaign.find((entry) =>
    entry.export.path === model.exports[0].path && entry.export.sha256 === model.exports[0].sha256) : undefined;
  const reviewedView = assessment?.views.find((image) =>
    image.path === (assessment.teachingView ?? model.scene.posterPath));
  const poster = reviewedView?.url ?? model?.preview ?? portrait(
    (initial.revision === 'r04' ? 'original' : 'updated') +
      (initial.part === 'Right adrenal gland' ? '-right-iso' : '-iso'),
  );
  return (
    <section className="ga-scene" aria-label="Interactive scene">
      <div className="ga-viewport">
        <div ref={container} className="ga-canvas" hidden={!ready} />
        {!ready && !file && initial.revision !== 'r03' && (
          <img src={poster} alt={reviewedView?.label ?? model?.scene.posterAlt ?? 'Reference render of the reviewed adrenal study'} />
        )}
        {!ready && (
          <button
            onClick={() => {
              setActive(true);
              setAttempt((n) => n + 1);
            }}
          >
            {active ? 'Retry 3D' : 'Inspect in 3D'}
          </button>
        )}
      </div>
      {!ready && !file && initial.revision !== 'r03' && (
        <p>{reviewedView?.label ?? model?.scene.posterCaption ??
          'Blender reference · ' + (initial.part === 'Right adrenal gland' ? 'isolated right gland' : 'regional view')}</p>
      )}
      {ready && model?.scene.groups && <p>{model.scene.posterCaption}</p>}
      {status && <p role="status">{status}</p>}
      <div className="ga-controls">
        {!model?.scene.singleMesh && <label>
          {model?.scene.groups ? 'Teaching view' : 'Structure'}
          <select
            aria-label={model?.scene.groups ? 'Teaching view' : 'Structure'}
            disabled={!ready}
            value={view.part}
            onChange={(e) => change({ ...view, part: e.target.value, camera: model?.scene.groups ? state().camera : null })}
          >
            {(model?.scene.groups ? Object.keys(model.scene.groups) : ['All structures', ...names]).map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>}
        {model?.scene.clip && <label>
          Cycle phase · {Math.round(view.phase * 100)}%
          <input type="range" aria-label="Cycle phase" min="0" max="1" step="0.001" disabled={!ready}
            value={view.phase} onChange={(e) => change({ ...state(), phase: Number(e.target.value) })} />
        </label>}
        <label>
          Material
          <select
            aria-label="Material"
            disabled={!ready}
            value={view.material}
            onChange={(e) => change({ ...state(), material: e.target.value })}
          >
            <option>Tissue</option>
            <option>Neutral</option>
          </select>
        </label>
        {stage && (
          <label>
            Key light
            <select
              aria-label="Key light"
              disabled={!ready}
              value={view.light}
              onChange={(e) => change({ ...state(), light: Number(e.target.value) })}
            >
              <option value="0.75">Soft</option>
              <option value="1">Standard</option>
              <option value="1.25">Bright</option>
            </select>
          </label>
        )}
        {ready && <button onClick={() => change(initial)}>Reset view</button>}
        {!stage && (
          <a
            href={route(stagePath(view, origin))}
            onClick={(e) => {
              e.currentTarget.href = absolute();
            }}
          >
            Open in 3D Stage ↗
          </a>
        )}
      </div>
      {stage && (
        <div className="ga-actions">
          <button disabled={!ready || !!file} onClick={share}>
            Share this view
          </button>
          <button disabled={!ready} onClick={saveImage}>
            Export WebP
          </button>
        </div>
      )}
      {file && (
        <p>A shareable preset needs a versioned gallery export. This file is open on your device.</p>
      )}
      {shared && (
        <label className="ga-share">
          Persistent preset link
          <input readOnly value={shared} onFocus={(e) => e.target.select()} />
        </label>
      )}
    </section>
  );
}
