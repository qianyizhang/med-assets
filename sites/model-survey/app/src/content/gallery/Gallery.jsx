import React, { useEffect, useRef, useState } from 'react';
import { route, libraryId, studyId, reviewId } from './catalog.js';
import { useDataApp } from '../../data-app-public.jsx';
import { Library, Revision, CollectionEntry } from './Library.jsx';
import { UseCases, Lesson, Planning } from './UseCases.jsx';
import { Compare } from './Compare.jsx';
import { Stage } from './Stage.jsx';
import { Rubric } from './Rubric.jsx';
import { Link, Heading, Missing } from './GalleryUI.jsx';
import './gallery.css';

function useRoute() {
  const current = () =>
    location.hash.slice(1) || (location.pathname === '/rubric' ? '/rubric' : '/library');
  const [url, setUrl] = useState(current);
  useEffect(() => {
    const follow = () => setUrl(current());
    window.addEventListener('hashchange', follow);
    return () => window.removeEventListener('hashchange', follow);
  }, []);
  return url;
}

function Header({ surface }) {
  return (
    <header className="ga-bar">
      <Link to="library" className="ga-brand">
        Anatomy Gallery
      </Link>
      <nav aria-label="Gallery">
        <Link to="library" aria-current={surface === 'library' ? 'page' : undefined}>
          Asset Library
        </Link>
        <Link
          to="use-cases"
          aria-current={['use-cases', 'archive'].includes(surface) ? 'page' : undefined}
        >
          Use Cases
        </Link>
        <details className="ga-tools" key={surface}>
          <summary>Tools</summary>
          <div>
            <Link to="compare" aria-current={surface === 'compare' ? 'page' : undefined}>
              Compare
            </Link>
            <Link to="stage" aria-current={surface === 'stage' ? 'page' : undefined}>
              3D Stage
            </Link>
          </div>
        </details>
      </nav>
    </header>
  );
}

export function Gallery({ Legacy }) {
  const { snapshot } = useDataApp(),
    raw = useRoute();
  const [path, query = ''] = raw.split('?'),
    [surface = 'library', id, revision, ...extra] = path.replace(/^\//, '').split('/');
  const titleRef = useRef(null),
    lastPath = useRef(path);
  useEffect(() => {
    if (lastPath.current !== path) {
      lastPath.current = path;
      const restore = path === '/library' && history.state?.libraryReturn;
      if (restore) {
        const frame = requestAnimationFrame(() => {
          const target = titleRef.current?.querySelector('a[href="' + CSS.escape(restore.href) + '"]');
          target?.focus({ preventScroll: true });
          window.scrollTo(0, restore.y);
        });
        return () => cancelAnimationFrame(frame);
      }
      titleRef.current?.focus({ preventScroll: true });
      window.scrollTo(0, 0);
    }
  }, [path]);
  const old = !path.startsWith('/') || !!import.meta.env.VITE_ADRENAL_PILOT;
  if (old)
    return (
      <>
        <a className="ga-legacy-return" href={route('library')}>
          ← Anatomy Gallery
        </a>
        <Legacy />
      </>
    );
  let page = <Missing />;
  if (!extra.length) {
    if (surface === 'library') {
      const row = snapshot.queries.model_survey.rows
        .concat(snapshot.queries.products.rows)
        .find((r) => r.id === id);
      if (!id) page = <Library snapshot={snapshot} query={query} />;
      else if (id === libraryId) page = <Revision revision={revision || 'r05'} />;
      else if (row && !revision) page = <CollectionEntry row={row} snapshot={snapshot} />;
    } else if (surface === 'use-cases' && (!id || id === studyId))
      page = id ? <Lesson stop={revision || 'region'} /> : <UseCases />;
    else if (surface === 'compare' && !revision && (!id || id === reviewId))
      page = <Compare detail={!!id} query={query} />;
    else if (surface === 'stage' && !revision) page = <Stage key={raw} id={id} query={query} />;
    else if (surface === 'rubric' && !id) page = <Rubric />;
    else if (surface === 'archive' && !id)
      page = (
        <>
          <Link to="use-cases">← Use Cases</Link>
          <Heading title="Experiments & Archive">Retained studies and planning records.</Heading>
          <Link to="archive/planning">Model Survey · Overlaps and Gaps →</Link>
        </>
      );
    else if (surface === 'archive' && id === 'planning')
      page = <Planning snapshot={snapshot} section={revision || 'overlaps'} />;
  }
  return (
    <article className="report-content ga-gallery">
      <Header surface={surface} />
      <div className="ga-content" ref={titleRef} tabIndex="-1">
        {page}
      </div>
    </article>
  );
}
