import React from 'react';
import { airway, assetUrl } from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { Heading, Label, Link } from './GalleryUI.jsx';
import { bronchialExterior, firstForkPath } from './local-models.js';
import { localView } from './presets.js';
import { Scene } from './Scene.jsx';

export function AirwayCards({ localPreview = false }) {
  return airway.slice(0, 3).reverse().map((study) => {
    const teaching = localPreview && study.id === 'bronchial-r13';
    return (
      <Link className="ga-feature" to={teaching ? firstForkPath : study.compare} key={study.id}>
        <img src={teaching ? bronchialExterior.preview : assetUrl(study.portrait.asset)} alt="" loading="lazy" />
        <div>
          <Label>Airway Review</Label>
          <h2>{teaching ? bronchialExterior.useCase : study.title}</h2>
          <p>{teaching ? 'Follow the trunk into both main branches on the lighter r14 exterior.' : study.finding}</p>
        </div>
      </Link>
    );
  });
}

export function AirwayLesson({ localPreview }) {
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title="Airway Review">
        Trace airway regions from the nose to the bronchial fork using three separate studies.
      </Heading>
      <AirwayCards localPreview={localPreview} />
      <div className="ga-related">
        <Link to="use-cases/systems/respiratory">See the respiratory assembly in Body Systems →</Link>
      </div>
    </>
  );
}

export function FirstForkLesson() {
  return (
    <>
      <Link to="use-cases/airway">← Airway Review</Link>
      <Heading title={bronchialExterior.useCase}>
        Follow the upper trunk to the central Y, then follow each main branch away from the split.
      </Heading>
      <div className="ga-detail">
        <Scene initial={localView(bronchialExterior)} origin={firstForkPath} />
        <section>
          <h2>{bronchialExterior.title}</h2>
          <p>{bronchialExterior.status}</p>
          <p>{bronchialExterior.limit}</p>
          <div className="ga-related">
            <Link to={bronchialExterior.library}>Open r14 in Asset Library →</Link>
            <Link to={bronchialExterior.compare}>{bronchialExterior.compareLabel} →</Link>
          </div>
        </section>
      </div>
    </>
  );
}

export function AirwayReview({ study }) {
  const relatedCast = study.family === 'trachea'
    ? airway.find((item) => item.family === 'trachea' && item.id !== study.id)
    : null;
  return (
    <>
      <Link to="compare">← Compare</Link>
      <Heading title={study.title}>Airway Review · Saved source review</Heading>
      <p>{study.reviewFinding ?? study.finding}</p>
      <div className={study.evidenceLayout === 'stacked'
        ? 'ga-pair ga-source-evidence ga-source-evidence-stacked'
        : 'ga-pair ga-source-evidence'}>
        {study.evidence.map((witness) => <Evidence key={witness.asset.sha256} witness={witness} />)}
      </div>
      <h2>Scope and limits</h2>
      <p>{study.limit}</p>
      <div className="ga-related">
        <Link to={study.library}>Open this exact revision in Asset Library →</Link>
        {relatedCast && <Link to={relatedCast.compare}>{relatedCast.title} →</Link>}
        <Link to="use-cases/airway">Return to Airway Review →</Link>
        <a href={study.record}>Owning review and attribution ↗</a>
      </div>
    </>
  );
}
