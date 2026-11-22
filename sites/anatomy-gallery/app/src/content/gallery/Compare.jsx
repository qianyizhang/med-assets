import React, { useState } from 'react';
import {
  portrait,
  portraitAsset,
  adrenalReview,
  rated,
  ratingProfile,
  ratingAxes,
  route,
  lessonPath,
  comparePath,
  libraryPath,
  assetUrl,
  bodyPartsAdrenal,
  bodyPartsReviewPath,
  salivary,
} from './catalog.js';
import { adrenalComparison, adrenalLesson } from './adrenal-study.js';
import { Evidence } from './Evidence.jsx';
import { StaticReviewIndex } from './StaticReviews.jsx';
import { AirwayCards } from './Airway.jsx';
import { baseView, stagePath } from './presets.js';
import { Link, Label, Heading, Missing } from './GalleryUI.jsx';


export function Compare({ detail, query, refinements }) {
  const [revealed, reveal] = useState(false);
  const [initialReverse] = useState(() => Math.random() < 0.5);
  const params = new URLSearchParams(query);
  const reverse = params.has('order') ? params.get('order') === 'ba' : initialReverse;
  const [share, setShare] = useState('');
  function pairPath(finish) {
    return comparePath + '?finish=' + finish + '&order=' + (reverse ? 'ba' : 'ab');
  }
  const mode = params.get('finish') || 'tissue';
  const pair = reverse ? [...adrenalComparison.pair].reverse() : adrenalComparison.pair;
  const { sections } = adrenalComparison;
  if (
    !['neutral', 'tissue'].includes(mode) ||
    (params.has('order') && !['ab', 'ba'].includes(params.get('order')))
  )
    return <Missing />;
  if (!detail)
    return (
      <>
        <Heading title="Compare">
          Inspect matched views and the evidence behind a revision decision.
        </Heading>
        {refinements && <p><Link to="compare/teaching-target?round=reopened">Review reopened exemptions →</Link></p>}
        {refinements && <p><Link to="compare/teaching-target">Review current teaching targets →</Link></p>}
        {refinements && <p><Link to="compare/teaching-refinements">Review the below-target teaching assets →</Link></p>}
        <Link className="ga-feature" to={comparePath}>
          <img src={portrait('updated-tissue-ortho')} alt="Right adrenal fold" />
          <div>
            <Label>Saved review · s1233 r04 / r05</Label>
            <h2>{adrenalComparison.title}</h2>
            <p>Two revisions, one reference section.</p>
          </div>
        </Link>
        <Link className="ga-feature" to={salivary.compare}>
          <img src={assetUrl(salivary.witness('rejection-closeup'))} alt="" />
          <div>
            <Label>Source review · Z-Anatomy r02</Label>
            <h2>The rejected submandibular duct crossing</h2>
            <p>See why the source duct course was withheld from the teaching export.</p>
          </div>
        </Link>
        <Link className="ga-feature" to={bodyPartsReviewPath}>
          <img src={assetUrl(bodyPartsAdrenal.evidence[0].asset)} alt="BodyParts3D adrenal pair" />
          <div>
            <Label>Saved source review · BodyParts3D</Label>
            <h2>Adrenal pair</h2>
            <p>Exterior silhouettes and kidney localization in the atlas source frame.</p>
          </div>
        </Link>
        <AirwayCards />
        <StaticReviewIndex />
      </>
    );
  return (
    <>
      <Link to="compare">← Compare</Link>
      <Heading title={adrenalComparison.title}>
        s1233 · Blind surface comparison · 20 November 2026
      </Heading>
      <div className="ga-actions">
        {['tissue', 'neutral'].map((f) => (
          <Link aria-current={f === mode ? 'page' : undefined} key={f} to={pairPath(f)}>
            {f === 'tissue' ? 'Tissue finish' : 'Neutral material'}
          </Link>
        ))}
        <button onClick={() => setShare(new URL(route(pairPath(mode)), location.origin + '/').href)}>
          Share comparison
        </button>
        <button onClick={() => reveal(!revealed)}>
          {revealed ? 'Hide revisions' : 'Reveal revisions and scores'}
        </button>
      </div>
      {share && (
        <label className="ga-share">
          Comparison link
          <input readOnly value={share} onFocus={(e) => e.target.select()} />
        </label>
      )}
      <div className="ga-pair">
        {pair.map(({ revision, [mode]: witness }, i) => (
          <figure key={revision}>
            <img
              src={portrait(witness)}
              alt={'Matched Blender view ' + (i ? 'B' : 'A')}
            />
            <figcaption>
              View {i ? 'B' : 'A'}{' '}
              {revealed && (
                <>
                  {' '}
                  · <Link to={libraryPath(revision)}>{revision}</Link> · {ratingProfile(rated[revision]).ratingLabel}
                </>
              )}
            </figcaption>
          </figure>
        ))}
      </div>
      {revealed && (
        <section>
          <h2>Regional localization assessment</h2>
          <p>
            The r05 surface recovers the right inferior cleft visible across adjacent CT label sections.
            The finish is illustrative. The review assesses gross placement and exterior shape.
          </p>
          <table>
            <thead>
              <tr>
                <th>Axis</th>
                {adrenalComparison.pair.map(({ revision }) => <th key={revision}>{revision}</th>)}
              </tr>
            </thead>
            <tbody>
              {ratingAxes.map((h, i) => (
                <tr key={h}>
                  <th>{h}</th>
                  {adrenalComparison.pair.map(({ revision }) => <td key={revision}>{rated[revision][i] ?? 'Unrated'}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
          <Link to="rubric">Rating rubric</Link>
        </section>
      )}
      <details>
        <summary>Inspect the source sections</summary>
        <div className="ga-source-evidence">
          <Evidence witness={{ ...sections, asset: portraitAsset(sections.display) }} />
        </div>
        <p>{sections.finding}</p>
      </details>
      <div className="ga-related">
        <a href={adrenalReview}>Original review and render provenance ↗</a>
        {revealed &&
          adrenalComparison.pair.map(({ revision }) => (
            <Link key={revision} to={stagePath(baseView(revision, adrenalComparison.part), pairPath(mode))}>
              Inspect {revision} in 3D Stage →
            </Link>
          ))}
        <Link to={lessonPath + '/' + adrenalLesson.stops.at(-1).id}>Return to the teaching view →</Link>
        <Link to={'library/' + bodyPartsAdrenal.family}>← Browse BodyParts3D adrenal family</Link>
      </div>
    </>
  );
}
