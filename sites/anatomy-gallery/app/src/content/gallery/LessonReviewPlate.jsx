import React, { useState } from 'react';
import { byPath } from './catalog.js';
import { isLoopbackGallery } from './local-models.js';
import teachingReview from './teaching-inputs/teaching-assessments.json';

export function LessonReviewPlate({ exportPath, title, alt, width, height, children }) {
  const [status, setStatus] = useState('loading');
  if (!isLoopbackGallery(globalThis.location?.hostname) || status === 'failed') return null;

  const file = byPath.get(exportPath);
  const assessment = file && teachingReview.campaign?.find(({ export: reviewed }) =>
    reviewed.path === exportPath && reviewed.sha256 === file.sha256 && reviewed.bytes === file.bytes);
  const view = assessment?.views.find(({ path }) => path === assessment.teachingView);
  if (!view?.url) return null;

  return (
    <section hidden={status !== 'ready'}>
      <h2>{title}</h2>
      {children}
      <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
        <figure>
          <a href={view.url} aria-label={'Open full teaching image · ' + title}>
            <img
              src={view.url}
              alt={alt}
              width={width}
              height={height}
              onLoad={({ currentTarget: img }) =>
                setStatus(img.naturalWidth === width && img.naturalHeight === height ? 'ready' : 'failed')}
              onError={() => setStatus('failed')}
            />
          </a>
          <figcaption>{view.label}</figcaption>
        </figure>
      </div>
    </section>
  );
}
