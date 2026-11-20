import React, { useEffect, useState } from 'react';
import {
  assetUrl,
  byPath,
  portrait,
  sourceRoot,
  adrenalReview,
  revisions,
  rated,
  route,
  libraryId,
  lessonPath,
  comparePath,
  libraryPath,
} from './catalog.js';
import { baseView } from './presets.js';
import { Scene } from './Scene.jsx';
import { BalancedDownload } from '../report/BalancedDownload.jsx';
import { Link, Label, Heading, Hero, Missing } from './GalleryUI.jsx';

function previewUrl(url) {
  const origin = 'https://med-assets-model-survey.landy123007.chatgpt.site';
  return url?.startsWith(origin + '/assets/') ? url.slice(origin.length) : url;
}

export function libraryRows(snapshot) {
  const curated = {
    id: libraryId,
    label: 'Adrenal glands · s1233',
    system: 'Endocrine',
    purpose: 'Regional localization',
    use: 'CT-derived regional assembly',
    path: libraryPath('r05'),
    image: portrait('updated-iso'),
  };
  return [
    curated,
    ...[...snapshot.queries.model_survey.rows, ...snapshot.queries.products.rows].map((row) => ({
      ...row,
      label: row.id === 'adrenals' ? 'Adrenal pair · BodyParts3D' : row.label,
      path: 'library/' + encodeURIComponent(row.id),
      image: previewUrl(snapshot.previewGallery?.[row.previewIds?.[0]]?.thumb),
    })),
  ];
}

export function Library({ snapshot, query }) {
  const params = new URLSearchParams(query),
    text = params.get('q') || '',
    system = params.get('system') || '';
  const [search, setSearch] = useState(text),
    [count, setCount] = useState(12);
  useEffect(() => {
    setSearch(text);
    setCount(history.state?.libraryReturn?.count || 12);
  }, [text, system]);
  const rows = libraryRows(snapshot);
  const filtered = rows.filter(
    (r) =>
      (!system || r.system === system) &&
      [r.label, r.id, r.use, r.purpose, r.system]
        .join(' ')
        .toLowerCase()
        .includes(text.trim().toLowerCase()),
  );
  function apply(q, s) {
    const p = new URLSearchParams();
    if (q.trim()) p.set('q', q.trim());
    if (s) p.set('system', s);
    location.hash = route('library' + (p.size ? '?' + p : '')).slice(1);
  }
  return (
    <>
      <Heading title="Asset Library">Find a model by anatomy, teaching purpose, or source.</Heading>
      {!text && !system && <Hero />}
      <section aria-label="Browse assets">
        <form
          className="ga-filters"
          onSubmit={(e) => {
            e.preventDefault();
            apply(search, system);
          }}
        >
          <input
            type="search"
            aria-label="Search assets"
            placeholder="Search anatomy, asset or source"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button>Search</button>
          <select
            aria-label="Filter by system"
            value={system}
            onChange={(e) => apply(search, e.target.value)}
          >
            <option value="">All systems</option>
            {[...new Set(rows.map((r) => r.system))].sort().map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </form>
        <div className="ga-list-title">
          <h2>{text || system ? 'Search results' : 'Browse the collection'}</h2>
          <span>{filtered.length} entries</span>
        </div>
        <div className="ga-grid">
          {filtered.slice(0, count).map((r) => (
            <Link
              key={r.id}
              className="ga-card"
              to={r.path}
              onClick={(event) => {
                history.replaceState(
                  {
                    ...history.state,
                    libraryReturn: {
                      count,
                      href: event.currentTarget.getAttribute('href'),
                      y: window.scrollY,
                    },
                  },
                  '',
                );
              }}
            >
              <div className="ga-thumb">
                {r.image ? (
                  <img loading="lazy" alt="" src={r.image} />
                ) : (
                  <span>Preview unavailable</span>
                )}
              </div>
              <div className="ga-card-body">
                <Label>{r.system}</Label>
                <h3>{r.label}</h3>
                <p>{r.purpose}</p>
              </div>
            </Link>
          ))}
        </div>
        {!filtered.length && (
          <p>
            No entries match. <Link to="library">Clear filters</Link>
          </p>
        )}
        {filtered.length > count && (
          <button className="ga-more" onClick={() => setCount(count + 24)}>
            Show more entries
          </button>
        )}
      </section>
    </>
  );
}

export function Revision({ revision }) {
  if (!Object.hasOwn(revisions, revision)) return <Missing />;
  const file = revisions[revision];
  return (
    <>
      <Link to="library">← Asset Library</Link>
      <Heading title="Adrenal glands">s1233 · CT-derived regional assembly</Heading>
      <nav className="ga-tabs" aria-label="Asset revision">
        {Object.keys(revisions).map((r) => (
          <Link key={r} aria-current={r === revision ? 'page' : undefined} to={libraryPath(r)}>
            {r}
          </Link>
        ))}
      </nav>
      <div className="ga-detail">
        <Scene key={revision} initial={baseView(revision)} />
        <section>
          <Label>Selected revision · {revision}</Label>
          <h2>Regional exterior</h2>
          <p>
            Left and right adrenal glands with both kidneys and the pancreas. The gland surfaces
            interpret a 1.5 mm label grid.
          </p>
          <dl className="ga-facts">
            <dt>Export</dt>
            <dd>GLB · {(file.bytes / 1000).toFixed(1)} kB</dd>
            <dt>Source</dt>
            <dd>TotalSegmentator case s1233</dd>
            <dt>Assessment</dt>
            <dd>
              {rated[revision]
                ? rated[revision].reduce((sum, n) => sum + n, 0) + '/16 · regional localization'
                : 'Unrated'}
            </dd>
          </dl>
          <Link to="rubric">Rating rubric</Link>
          <p>
            Agent review · 20 Nov 2026 ·{' '}
            <a
              href={
                revision === 'r03'
                  ? sourceRoot + 'reviews/body-systems/2026-11-20-surface-quality/README.md'
                  : adrenalReview
              }
            >
              Assessment and evidence
            </a>
          </p>
          <div className="ga-related">
            <Link to={lessonPath + '/region'}>Regional localization lesson →</Link>
            {rated[revision] && <Link to={comparePath}>Compare r04 and r05 →</Link>}
            <a href={assetUrl(file)} download>
              Download exact GLB ↓
            </a>
            <a href={file.source}>Package and attribution ↗</a>
          </div>
        </section>
      </div>
    </>
  );
}

export function CollectionEntry({ row, snapshot }) {
  const file = byPath.get(row.media?.[0]?.path);
  const source = row.id === 'adrenals' ? 'BodyParts3D' : row.system;
  const preview = snapshot.previewGallery?.[row.previewIds?.[0]];
  return (
    <>
      <Link to="library">← Asset Library</Link>
      <Heading title={row.id === 'adrenals' ? 'Adrenal pair · BodyParts3D' : row.label}>
        {source} · {row.purpose}
      </Heading>
      <div className="ga-detail">
        {preview ? (
          <img
            className="ga-study-plate"
            src={previewUrl(preview.image)}
            alt={row.label + ' retained preview'}
          />
        ) : (
          <p>Preview unavailable.</p>
        )}
        <section>
          <h2>{row.use}</h2>
          <p>{row.limit}</p>
          <p>
            Rating · Unrated &nbsp; <Link to="rubric">Rating rubric</Link>
          </p>
          {row.id === 'adrenals' && (
            <p>
              <Link to={libraryPath('r05')}>Related s1233 teaching model →</Link>
            </p>
          )}
          <a href={row.evidence?.url}>Source evidence ↗</a>
          {row.id === 'swirendo_fdi31' && <BalancedDownload media={row.media} />}
          {file && (
            <p>
              <a href={assetUrl(file)}>Download {file.name}</a>
            </p>
          )}
        </section>
      </div>
      {!!row.media?.length && (
        <details>
          <summary>All indexed files ({row.media.length})</summary>
          {row.media.map((m) => (
            <p key={m.path}>
              <a href={byPath.has(m.path) ? assetUrl(byPath.get(m.path)) : m.url}>{m.path}</a>
            </p>
          ))}
        </details>
      )}
    </>
  );
}
