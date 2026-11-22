import React, { useEffect, useState } from 'react';
import { Evidence } from './Evidence.jsx';
import { Heading, Link, Missing } from './GalleryUI.jsx';
import { ratingAxes, route } from './catalog.js';

const root = 'compare/teaching-refinements';
export const refinementPath = (digest) => root + '?asset=' + digest;

function Plate({ assessment, field, label }) {
  const review = assessment.refinement;
  const image = assessment.views.find((view) => view.path === review[field]);
  return <Evidence key={image.sha256} witness={{ title: label, displayUrl: image.url, alt: image.label, caption: image.label }} />;
}

function CandidateDownload({ candidate }) {
  const [available, setAvailable] = useState(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch(candidate.url, { method: 'HEAD', signal: controller.signal, cache: 'no-store' })
      .then((response) => setAvailable(response.ok && Number(response.headers.get('content-length')) === candidate.bytes))
      .catch(() => { if (!controller.signal.aborted) setAvailable(false); });
    return () => controller.abort();
  }, [candidate.url, candidate.bytes]);
  return <p>
    {available && <><a href={candidate.url} download={candidate.name}>Download reviewed candidate · {candidate.name}</a>
      {' · '}{candidate.bytes.toLocaleString()} bytes · </>}
    {available === false && 'Candidate unavailable in this checkout. '}
    <a href={candidate.recipeUrl}>Rebuild the exact candidate</a>
  </p>;
}

export function Refinements({ assessments, query }) {
  const [sideBySide, setSideBySide] = useState(false);
  const rows = assessments.filter((row) => row.refinement);
  if (!rows.length) return <Missing />;
  const groups = [...new Set(rows.map((row) => row.refinement.group))].sort();
  const ordered = groups.flatMap((group) => rows.filter((row) => row.refinement.group === group)
    .sort((a, b) => a.refinement.beforeScores[0] - b.refinement.beforeScores[0] ||
      a.refinement.beforeScores[2] - b.refinement.beforeScores[2] ||
      a.refinement.family.localeCompare(b.refinement.family)));
  const digest = new URLSearchParams(query).get('asset');
  const current = digest ? ordered.find((row) => row.export.sha256 === digest) : ordered[0];
  if (!current) return <Missing />;
  const review = current.refinement;
  const index = ordered.indexOf(current);
  const candidate = review.candidate;
  return <>
    <Link to="compare">← Compare</Link>
    <Heading title="Teaching asset refinements">{current.task}</Heading>
    <nav className="ga-refinement-nav" aria-label="Refinement reviews">
      <label>Asset
        <select value={current.export.sha256} onChange={(e) => { location.hash = route(refinementPath(e.target.value)); }}>
          {groups.map((group) => <optgroup key={group} label={group}>
            {ordered.filter((row) => row.refinement.group === group).map((row) =>
              <option key={row.export.path} value={row.export.sha256}>{row.refinement.family}</option>)}
          </optgroup>)}
        </select>
      </label>
      <span>{index + 1} of {ordered.length}</span>
      {index > 0 && <Link to={refinementPath(ordered[index - 1].export.sha256)}>Previous</Link>}
      {index + 1 < ordered.length && <Link to={refinementPath(ordered[index + 1].export.sha256)}>Next</Link>}
    </nav>
    <h2>{review.family}</h2>
    <p>{review.finding}</p>
    <label className="ga-compare-choice"><input type="checkbox" checked={sideBySide}
      onChange={(e) => setSideBySide(e.target.checked)} /> Compare side by side</label>
    <div key={current.export.sha256} className={'ga-pair ga-source-evidence' + (sideBySide ? '' : ' ga-source-evidence-stacked')}>
      {sideBySide && <Plate assessment={current} field="before" label="Original reviewed view" />}
      <Plate assessment={current} field="after" label="Refinement evidence" />
    </div>
    <p>{review.caption}</p>
    <h2>Review decision</h2><p>{review.decision ?? current.decision}</p>
    {review.limits && <p>{review.limits}</p>}
    <table><caption>Ratings for the reviewed export</caption>
      <thead><tr><th scope="col">Axis</th><th scope="col">Before</th><th scope="col">Reviewed</th>{candidate?.scores && <th scope="col">Candidate</th>}</tr></thead>
      <tbody>{current.axes.map((axis, i) => <tr key={ratingAxes[i]}><th scope="row">{ratingAxes[i]}</th>
        <td>{review.beforeScores[i] ?? 'Unrated'}</td><td>{(review.reviewedScores ?? current.axes.map((a) => a.score))[i] ?? 'Unrated'}</td>{candidate?.scores && <td>{candidate.scores[i] ?? 'Unrated'}</td>}</tr>)}</tbody>
    </table>
    {candidate?.economyObservation && <p><strong>Candidate mesh economy.</strong> {candidate.economyObservation}</p>}
    {candidate?.library && <p><Link to={candidate.library}>Inspect the recommended teaching revision →</Link></p>}
    {candidate?.url && <CandidateDownload key={candidate.sha256} candidate={candidate} />}
    <Link to={'library?q=' + current.export.sha256}>Find this exact export in Asset Library →</Link>
  </>;
}


export function TeachingTarget({ assessments, query }) {
  const params = new URLSearchParams(query);
  const reopened = params.get('round') === 'reopened';
  const rows = assessments.filter((row) => row.maintained && row.target && (!reopened || row.target.reviewedAxes))
    .sort((a, b) => a.maintained.collection.localeCompare(b.maintained.collection) || a.target.family.localeCompare(b.target.family));
  const selected = params.get('asset');
  const row = selected ? assessments.find((item) => item.target && item.export.sha256 === selected
    && (!reopened || item.target.reviewedAxes)) : rows[0];
  if (!row) return <Missing />;
  const { target } = row;
  const low = Object.entries(target.exemptions);
  return <>
    <Link to="compare">← Compare</Link>
    <Heading title="Teaching target review">{row.task}</Heading>
    <label>Reviewed asset{' '}
      <select value={row.export.sha256} onChange={(event) => {
        location.hash = route('compare/teaching-target?' + (reopened ? 'round=reopened&' : '') + 'asset=' + event.target.value);
      }}>
        {!row.maintained && <option value={row.export.sha256}>{target.family} · earlier edition</option>}
        {[...new Set(rows.map((r) => r.maintained.collection))].map((collection) => <optgroup key={collection} label={collection}>
          {rows.filter((r) => r.maintained.collection === collection).map((r) =>
            <option key={r.export.path} value={r.export.sha256}>{r.target.family}</option>)}
        </optgroup>)}
      </select>
    </label>
    <h2>{target.family}</h2>
    {!row.maintained && <p>Earlier reviewed edition</p>}<p>Teaching task · {target.status}. {target.taskCheck}</p>
    <div className="ga-pair ga-source-evidence">
      {(target.before === target.after ? ['after'] : ['before', 'after']).map((side) => {
        const image = row.views.find((v) => v.path === target[side]);
        return <Evidence key={side + image.sha256} witness={{ title: target.before === target.after ? 'Retained teaching view' : side === 'before' ? 'Starting view' : 'Trial or reviewed view',
          displayUrl: image.url, alt: image.label, caption: image.label }} />;
      })}
    </div>
    <p>{row.export.path === target.baseline ? 'Retained starting file' : 'Selected teaching edition'} · {row.export.path.split('/').at(-1)}</p>
    {target.workItem && <p><a href={row.sources.find((source) => source.path === target.workItem)?.url}>Open the owned follow-up</a></p>}
    <table><caption>Scores for the named task</caption>
      <thead><tr><th scope="col">Axis</th><th scope="col">Before</th><th scope="col">Current</th></tr></thead>
      <tbody>{row.axes.map((axis, i) => <tr key={ratingAxes[i]}><th scope="row">{ratingAxes[i]}</th>
        <td>{target.beforeScores[i] ?? 'Unrated'}</td><td>{axis.score ?? 'Unrated'}</td></tr>)}</tbody>
    </table>
    {low.map(([i, exception]) => <section key={i}><h3>{ratingAxes[i]} · target exemption</h3>
      <p>{exception.reason}</p><p>Permitted use · {exception.permittedUse}</p><p>Reopen when · {exception.reopen}</p></section>)}
    <div className="ga-related">
      <Link to={'library?q=' + target.controlSha256}>Find the original file →</Link>
      <Link to={'library?q=' + row.export.sha256}>Inspect the reviewed file →</Link>
    </div>
  </>;
}
