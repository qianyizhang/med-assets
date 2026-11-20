import React, { useEffect, useRef, useState } from 'react';
import { assetUrl, parts, portrait, revisions, route } from './catalog.js';
import { stagePath } from './presets.js';
import { loadScene } from './scene.js';

async function modelBytes(file, revision, signal) {
  if (file) {
    if (file.size > 64_000_000) throw Error('Choose a GLB smaller than 64 MB.');
    return file.arrayBuffer();
  }
  const asset = revisions[revision];
  const response = await fetch(assetUrl(asset), { signal, redirect: 'error' });
  if (!response.ok) throw Error('The pinned export is unavailable.');
  const bytes = await response.arrayBuffer();
  if (bytes.byteLength !== asset.bytes) throw Error('The export has a different size.');
  const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (b) =>
    b.toString(16).padStart(2, '0'),
  ).join('');
  if (hash !== asset.sha256) throw Error('The export differs from the pinned revision.');
  return bytes;
}

export function Scene({ initial, stage = false, auto = false, file = null }) {
  const [active, setActive] = useState(auto),
    [attempt, setAttempt] = useState(0);
  const [view, setView] = useState(initial),
    [status, setStatus] = useState(''),
    [ready, setReady] = useState(false);
  const [names, setNames] = useState(parts),
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
      const bytes = await modelBytes(file, initial.revision, controller.signal);
      controller.signal.throwIfAborted();
      owned = await loadScene(host, bytes, latest.current, controller.signal);
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
  }, [active, attempt, file, initial.revision]);
  const state = () => ({ ...view, camera: engine.current?.camera() ?? view.camera });
  const absolute = () => new URL(route(stagePath(state())), location.href).href;
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
      a.download = (file ? 'local-scene' : 'adrenal-' + view.revision) + '-stage.webp';
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      if (!file) setShared(source);
      setStatus(file ? 'WebP exported.' : 'WebP exported with its preset link embedded.');
    } catch (e) {
      setStatus(e.message);
    }
  }
  const poster = portrait(
    (initial.revision === 'r04' ? 'original' : 'updated') +
      (initial.part === 'Right adrenal gland' ? '-right-iso' : '-iso'),
  );
  return (
    <section className="ga-scene" aria-label="Interactive scene">
      <div className="ga-viewport">
        <div ref={container} className="ga-canvas" hidden={!ready} />
        {!ready && !file && initial.revision !== 'r03' && (
          <img src={poster} alt="Reference render of the reviewed adrenal study" />
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
        <p>
          Blender reference ·{' '}
          {initial.part === 'Right adrenal gland' ? 'isolated right gland' : 'regional view'}
        </p>
      )}
      {status && <p role="status">{status}</p>}
      <div className="ga-controls">
        <label>
          Structure
          <select
            aria-label="Structure"
            disabled={!ready}
            value={view.part}
            onChange={(e) => change({ ...view, part: e.target.value, camera: null })}
          >
            {['All structures', ...names].map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>
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
            href={route(stagePath(view))}
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
