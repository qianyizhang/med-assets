import React from 'react';
import { portrait, route, lessonPath, libraryPath } from './catalog.js';

export function Link({ to, children, ...props }) {
  return (
    <a href={to === 'rubric' ? '/rubric' : route(to)} {...props}>
      {children}
    </a>
  );
}

export function Label({ children }) {
  return <div className="ga-meta">{children}</div>;
}

export function Heading({ title, children }) {
  return (
    <div className="ga-heading">
      <h1>{title}</h1>
      {children && <p>{children}</p>}
    </div>
  );
}

export function Hero({ lesson = false }) {
  return (
    <div className="ga-hero">
      <div className="ga-hero-copy">
        <Label>Endocrine system · s1233</Label>
        <h2>{lesson ? 'Locate the adrenal glands' : 'Adrenal glands'}</h2>
        <p>
          {lesson
            ? 'Find each gland above its kidney, then follow the curved lower rim of the right gland.'
            : 'Explore the paired glands in their regional setting, reconstructed from CT labels.'}
        </p>
        <Link className="ga-primary" to={lesson ? lessonPath + '/region' : libraryPath('r05')}>
          {lesson ? 'Begin lesson' : 'Inspect revision r05'} <span aria-hidden="true">→</span>
        </Link>
      </div>
      <div className="ga-hero-plate">
        <img
          src={portrait(lesson ? 'updated-iso' : 'updated-tissue-ortho')}
          alt={
            lesson
              ? 'Paired adrenal glands above the kidneys'
              : 'Right adrenal gland showing its curved inferior rim'
          }
        />
      </div>
    </div>
  );
}

export function Missing() {
  return (
    <>
      <Heading title="View unavailable">
        This address does not identify a gallery record or supported preset.
      </Heading>
      <Link to="library">Return to Asset Library</Link>
    </>
  );
}
