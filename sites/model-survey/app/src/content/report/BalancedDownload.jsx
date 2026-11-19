import React, { useEffect, useRef, useState } from 'react';
import { FDI31_ID, fetchBalancedGlb, findBalancedExport } from '../shared/fdi31-download.js';

export function BalancedDownload({ media }) {
  const file = findBalancedExport(media);
  const active = useRef(null);
  const [status, setStatus] = useState('');

  useEffect(() => () => active.current?.abort(), []);

  async function download() {
    if (active.current) return;
    const controller = new AbortController();
    active.current = controller;
    setStatus('Preparing download…');
    try {
      const { blob, name } = await fetchBalancedGlb(file, controller.signal);
      if (controller.signal.aborted) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = name;
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
      setStatus('Download started.');
    } catch {
      if (!controller.signal.aborted) setStatus('Download unavailable. Try again or use the GitHub export.');
    } finally {
      active.current = null;
    }
  }

  if (!file) return <p className="sv-note">Balanced GLB download unavailable for this survey entry.</p>;

  return (
    <section className="sv-balanced-download" aria-label="FDI31 Balanced export" data-reviewed-rows>
      <div className="sv-balanced-actions">
        <button type="button" onClick={download} aria-disabled={status === 'Preparing download…'}>
          Download Balanced GLB
        </button>
        <a href={file.url}>GitHub export</a>
        <a href={`#${FDI31_ID}`}>Link to FDI31</a>
      </div>
      <div>{file.bytes.toLocaleString('en-US')} bytes · SHA-256 <code>{file.sha256}</code></div>
      <div>Benz, Heck &amp; Walter · <a href="https://doi.org/10.5282/ubm/data.477">CC BY-SA 4.0 source</a></div>
      <div role="status">{status}</div>
    </section>
  );
}
