import React, { useState } from 'react';
import {
  portrait,
  adrenalReview,
  rated,
  route,
  lessonPath,
  comparePath,
  libraryPath,
} from './catalog.js';
import { baseView, stagePath } from './presets.js';
import { Link, Label, Heading, Missing } from './GalleryUI.jsx';

const headings = ['Fidelity to evidence', 'Form and surface', 'Teaching readability', 'Mesh economy'];

export function Compare({ detail, query }) {
  const [revealed, reveal] = useState(false);
  const [initialReverse] = useState(() => Math.random() < 0.5);
  const params = new URLSearchParams(query);
  const reverse = params.has('order') ? params.get('order') === 'ba' : initialReverse;
  const [share, setShare] = useState('');
  function pairPath(finish) {
    return comparePath + '?finish=' + finish + '&order=' + (reverse ? 'ba' : 'ab');
  }
  const mode = new URLSearchParams(query).get('finish') || 'tissue';
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
        <Link className="ga-feature" to={comparePath}>
          <img src={portrait('updated-tissue-ortho')} alt="Right adrenal fold" />
          <div>
            <Label>Saved review · s1233 r04 / r05</Label>
            <h2>The inferior adrenal fold</h2>
            <p>Two revisions, one reference section.</p>
          </div>
        </Link>
      </>
    );
  return (
    <>
      <Link to="compare">← Compare</Link>
      <Heading title="The inferior adrenal fold">
        s1233 · Blind surface comparison · 20 November 2026
      </Heading>
      <div className="ga-actions">
        {['tissue', 'neutral'].map((f) => (
          <Link aria-current={f === mode ? 'page' : undefined} key={f} to={pairPath(f)}>
            {f === 'tissue' ? 'Tissue finish' : 'Neutral material'}
          </Link>
        ))}
        <button onClick={() => setShare(new URL(route(pairPath(mode)), location.href).href)}>
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
        {(reverse ? ['r05', 'r04'] : ['r04', 'r05']).map((r, i) => (
          <figure key={r}>
            <img
              src={portrait(
                (r === 'r05' ? 'updated' : 'original') +
                  '-' +
                  (mode === 'neutral' ? 'fold' : 'tissue') +
                  '-ortho',
              )}
              alt={'Matched Blender view ' + (i ? 'B' : 'A')}
            />
            <figcaption>
              View {i ? 'B' : 'A'}{' '}
              {revealed && (
                <>
                  {' '}
                  · <Link to={libraryPath(r)}>{r}</Link> · {rated[r].reduce((sum, n) => sum + n, 0)}/16
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
                <th>r04</th>
                <th>r05</th>
              </tr>
            </thead>
            <tbody>
              {headings.map((h, i) => (
                <tr key={h}>
                  <th>{h}</th>
                  <td>{rated.r04[i]}</td>
                  <td>{rated.r05[i]}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Link to="rubric">Rating rubric</Link>
        </section>
      )}
      <details>
        <summary>Inspect the source sections</summary>
        <img
          className="ga-evidence"
          src={portrait('case-sections')}
          alt="Matched case contours at the right inferior cleft"
        />
        <p>
          At −67.35 mm, the worst local contour difference fell from 5.97 mm in r04 to 0.64 mm in r05.
        </p>
      </details>
      <div className="ga-related">
        <a href={adrenalReview}>Original review and render provenance ↗</a>
        {revealed &&
          ['r04', 'r05'].map((r) => (
            <Link key={r} to={stagePath(baseView(r, 'Right adrenal gland'))}>
              Inspect {r} in 3D Stage →
            </Link>
          ))}
        <Link to={lessonPath + '/right-gland'}>Return to the teaching view →</Link>
      </div>
    </>
  );
}
