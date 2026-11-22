import React from 'react';
import { staticReviews } from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { Heading, Link, Missing } from './GalleryUI.jsx';

export function StaticReviewIndex() {
  return [...new Set(staticReviews.map(({ collection }) => collection))].map((collection) => (
    <section className="ga-static-index" key={collection}>
      <h2>{collection}</h2>
      <ul>
        {staticReviews.filter((study) => study.collection === collection).map((study) => (
          <li key={study.id}>
            <Link to={study.compare}>{study.title}</Link>
            <span>{study.status}</span>
          </li>
        ))}
      </ul>
    </section>
  ));
}

function ReviewSection({ section }) {
  const { title, views, paired, collapsed } = section;
  const figures = (
    <div className={'ga-pair ga-source-evidence ga-static-evidence' + (paired ? '' : ' ga-source-evidence-stacked')}>
      {views.map((witness) => <Evidence key={witness.path} witness={witness} />)}
    </div>
  );
  if (collapsed) return <details><summary>{title}</summary>{figures}</details>;
  return (
    <section>
      {title && <h2>{title}</h2>}
      {figures}
    </section>
  );
}

function ReviewFinding({ study, subsection }) {
  return (
    <section>
      {subsection && <h2><Link to={study.compare}>{study.title}</Link></h2>}
      {subsection && <p>{study.status}</p>}
      <p>{study.finding}</p>
      {study.inspector && <p><a href={study.inspector.href}>{study.inspector.label} ↗</a></p>}
      {study.sections.map((section) => <ReviewSection key={section.views[0].path} section={section} />)}
      <p><strong>Scope and limits.</strong> {study.limit}</p>
      <p>{study.credit}</p>
      <div className="ga-related">
        {study.library && <Link to={study.library}>Open the exact Library revision →</Link>}
        {study.related?.map(({ to, label }) => <Link key={to} to={to}>{label} →</Link>)}
        {study.record && <a href={study.record}>Owning evidence and attribution ↗</a>}
        {study.sources?.map(({ href, label }) => <a key={href} href={href}>{label} ↗</a>)}
      </div>
    </section>
  );
}

export function StaticReview({ study, chapter }) {
  const selected = chapter && study.chapters?.find(({ id }) => id === chapter);
  if (chapter && !selected) return <Missing />;
  return (
    <>
      <Link to={selected ? study.compare : 'compare'}>← {selected ? study.title : 'Compare'}</Link>
      <Heading title={selected?.title ?? study.title}>
        {study.collection} · {(selected ?? study).status}
      </Heading>
      {study.chapters && !selected ? (
        <>
          <ul>
            {study.chapters.map((entry) => <li key={entry.id}><Link to={entry.compare}>{entry.title}</Link></li>)}
          </ul>
          {study.chapters.map((entry) => <ReviewFinding key={entry.id} study={entry} subsection />)}
        </>
      ) : <ReviewFinding study={selected ?? study} />}
    </>
  );
}
