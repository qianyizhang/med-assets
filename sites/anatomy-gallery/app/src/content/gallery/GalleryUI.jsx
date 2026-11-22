import React from 'react';
import { route } from './catalog.js';

export function Link({ to, children, ...props }) {
  const href = to === 'rubric' ? '/rubric' : (location.pathname === '/' ? '' : '/') + route(to);
  return (
    <a href={href} {...props}>
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
