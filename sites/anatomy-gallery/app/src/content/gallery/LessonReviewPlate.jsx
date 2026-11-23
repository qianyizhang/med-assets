import { candidate } from './selected-library.js';
import React, { useState } from 'react';
import teachingReview from './teaching-inputs/teaching-assessments.json';

export function LessonReviewPlate({ exportPath, title, children }) {
  const [status, setStatus] = useState('loading');
  if (!candidate || status === 'failed') return null;

  const assessment = teachingReview.campaign?.find((entry) => entry.maintained &&
    [entry.export.path, entry.target?.baseline, entry.target?.familyBaseline].includes(exportPath))
    ?? teachingReview.campaign?.find((entry) => entry.export.path === exportPath);
  const view = assessment?.views.find(({ path }) => path === assessment.teachingView);
  if (!view?.url) return null;
  const { width, height } = view;

  return (
    <section hidden={status !== 'ready'}>
      <h2>{title}</h2>
      {children}
      <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
        <figure>
          <a href={view.url} aria-label={'Open full teaching image · ' + title}>
            <img
              src={view.url}
              alt={view.label}
              width={width}
              height={height}
              onLoad={({ currentTarget: img }) =>
                setStatus((!width || img.naturalWidth === width) && (!height || img.naturalHeight === height) ? 'ready' : 'failed')}
              onError={() => setStatus('failed')}
            />
          </a>
          <figcaption>{view.label}</figcaption>
        </figure>
      </div>
    </section>
  );
}
