import React, { useEffect, useState } from 'react';
import { assetUrl } from './catalog.js';
import projection from './teaching-inputs/lymph-projection.json';

const width = 1520;
const height = 1960;
const views = Object.entries(projection.selected_projection);
const caps = views.flatMap(([, { panel_points }]) => [panel_points[0], panel_points.at(-1)]);
const motionQuery = '(prefers-reduced-motion: reduce)';
const source = 'https://github.com/qianyizhang/med-assets/blob/503c33f1dadf403faaec373c1a11a8b40dc523d6/';
const openStax = 'https://openstax.org/books/anatomy-and-physiology-2e/pages/';
const labels = {
  en: {
    show: 'Show direction',
    pause: 'Pause direction',
    static: 'Static plate',
    loading: 'Loading plate',
    running: 'Thoracic route only · lower cap to upper cap',
    reduced: 'Static plate · reduced motion',
    missing: 'The plate could not load. Open the retained PNG or reload to retry.',
    original: 'Open full-size PNG',
    package: 'Lesson package and projection binding',
  },
  zh: {
    show: '显示方向',
    pause: '暂停方向',
    static: '静态图',
    loading: '正在载入图像',
    running: '仅胸导管路径 · 下端封口至上端封口',
    reduced: '静态图 · 减少动态效果',
    missing: '图像无法载入。请打开存档 PNG，或重新载入页面。',
    original: '打开原尺寸 PNG',
    package: '教学图包与投影绑定',
  },
};

export function LymphPlate({ lang, file, alt, showDirection, setShowDirection }) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(!file);
  const [reduced, setReduced] = useState(() => matchMedia(motionQuery).matches);
  useEffect(() => {
    const preference = matchMedia(motionQuery);
    const update = () => {
      setReduced(preference.matches);
      if (preference.matches) setShowDirection(false);
    };
    preference.addEventListener('change', update);
    update();
    return () => preference.removeEventListener('change', update);
  }, [setShowDirection]);
  const active = loaded && showDirection && !reduced;
  const copy = labels[lang];
  const status = failed ? copy.missing : !loaded ? copy.loading : reduced ? copy.reduced : active ? copy.running : copy.static;

  return (
    <figure>
      <figcaption className="ga-controls ga-lymph-controls">
        <button type="button" disabled={!loaded || reduced} onClick={() => setShowDirection(!showDirection)}>
          {active ? copy.pause : copy.show}
        </button>
        <span role="status">{status}</span>
        {file && <a href={failed ? file.source : assetUrl(file)}>{copy.original} ↗</a>}
      </figcaption>
      {!failed && (
        <div className="ga-lymph-plate">
          <img src={assetUrl(file)} width={width} height={height} alt={alt}
            onLoad={({ currentTarget }) => {
              const matches = currentTarget.naturalWidth === width && currentTarget.naturalHeight === height;
              setLoaded(matches);
              setFailed(!matches);
            }}
            onError={() => { setLoaded(false); setFailed(true); }} />
          {active && (
            <svg viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
              <defs>
                <mask id="lymph-cap-mask">
                  <rect width={width} height={height} fill="white" />
                  {caps.map(([x, y]) => <circle key={y} cx={x} cy={y} r="9" fill="black" />)}
                </mask>
              </defs>
              {views.map(([view, { panel_points }]) => (
                <path key={view} data-view={view} mask="url(#lymph-cap-mask)"
                  d={'M ' + panel_points.map(([x, y]) => `${x.toFixed(6)} ${y.toFixed(6)}`).join(' L ')} />
              ))}
            </svg>
          )}
        </div>
      )}
    </figure>
  );
}

export function LymphSources({ lang, folder }) {
  return (
    <div className="ga-related">
      <a href={source + folder + '/README.md'}>{labels[lang].package} ↗</a>
      <a href={openStax + '1-6-anatomical-terminology'}>OpenStax §1.6 ↗</a>
      <a href={openStax + '21-1-anatomy-of-the-lymphatic-and-immune-systems'}>OpenStax §21.1 ↗</a>
    </div>
  );
}
