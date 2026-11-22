import React from 'react';
import {
  adrenalCandidateBookmark, assetUrl,
  bodyPartsAdrenal, bodyPartsReviewPath, comparePath, matchesBodyPartsExport,
} from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { Heading, Link } from './GalleryUI.jsx';

export function AdrenalReviewLinks({ row }) {
  if (row.id !== bodyPartsAdrenal.family) return null;
  return (
    <div className="ga-related">
      {matchesBodyPartsExport(row) ? (
        <Link to={bodyPartsReviewPath}>Review this version →</Link>
      ) : (
        <p>Exact-version review unavailable for this export.</p>
      )}
      <Link to={comparePath}>Related s1233 teaching study →</Link>
    </div>
  );
}

export function BodyPartsReview() {
  const review = bodyPartsAdrenal;
  return (
    <>
      <Link to="compare">← Compare</Link>
      <Heading title="Adrenal pair · BodyParts3D">
        Saved source review · 23 October 2026
      </Heading>
      <Link to={'library/' + review.family}>← Browse BodyParts3D adrenal family</Link>
      <p>
        The left and right exterior silhouettes and their positions relative to the kidneys were
        screened against the same atlas source frame. The colors are illustrative.
      </p>
      <div className="ga-pair ga-source-evidence">
        {review.evidence.map((witness) => <Evidence key={witness.asset.sha256} witness={witness} />)}
      </div>
      <h2>Scope and limits</h2>
      <dl className="ga-facts">
        <dt>Technical</dt><dd>Passed with limitations for the recorded exact-export checks.</dd>
        <dt>Visual</dt><dd>Passed for the exterior silhouettes and same-source kidney localization.</dd>
        <dt>Anatomy</dt><dd>Reference-screened for external landmarks only.</dd>
        <dt>Runtime</dt><dd>Unverified for this BodyParts3D export.</dd>
      </dl>
      <details>
        <summary>Export identity and attribution</summary>
        <p>{review.id} · {review.artifact.bytes.toLocaleString('en-US')} bytes</p>
        <p>SHA-256 <code className="ga-digest">{review.artifact.sha256}</code></p>
        <p>BodyParts3D, © Database Center for Life Science (DBCLS) · CC BY 4.0</p>
      </details>
      <div className="ga-related">
        <a href={assetUrl(review.artifact)} download>Download this GLB ↓</a>
        <a href={review.record}>Bounded review record and source identities ↗</a>
        <a href={`https://anatomy-verification.landy123007.chatgpt.site/review/${adrenalCandidateBookmark}`}>
          Open published verification ↗
        </a>
        <Link to={comparePath}>Related s1233 teaching study →</Link>
      </div>
    </>
  );
}
