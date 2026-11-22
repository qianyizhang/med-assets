import React, { useEffect, useState } from 'react';
import {
  assetUrl,
  byPath,
  sourceRoot,
  revisions,
  rated,
  ratingAxes,
  ratingProfile,
  route,
  lessonPath,
  comparePath,
  libraryPath,
  salivary,
} from './catalog.js';
import { adrenalLibrary } from './adrenal-study.js';
import { exactExportPath, exportRole, librarySearchText, selectLibraryRow } from './library-data.js';
import { baseView, localView } from './presets.js';
import { Scene } from './Scene.jsx';
import { BalancedDownload } from './BalancedDownload.jsx';
import { AdrenalReviewLinks } from './BodyPartsReview.jsx';
import { refinementPath } from './Refinements.jsx';
import { Evidence } from './Evidence.jsx';
import { Link, Label, Heading, Missing } from './GalleryUI.jsx';

function previewUrl(url) {
  const origin = 'https://med-assets-model-survey.landy123007.chatgpt.site';
  return url?.startsWith(origin + '/assets/') ? url.slice(origin.length) : url;
}

const fields = [
  ['system', 'System'],
  ['purpose', 'Purpose'],
  ['kind', 'Entry type'],
  ['state', 'Review status'],
];

function matches(row, params, search) {
  const rating = params.get('rating');
  const hasRating = row.axes?.some(value => value !== null);
  if ((rating === 'rated' && !hasRating) || (rating === 'unrated' && hasRating))
    return false;
  if (fields.some(([key]) => params.get(key) && row[key] !== params.get(key))) return false;
  return librarySearchText(row).includes(search);
}

function compareRows(a, b, sort) {
  if (sort === 'most-files' && a.fileCount !== b.fileCount) return b.fileCount - a.fileCount;
  if (sort === 'fewest-files' && a.fileCount !== b.fileCount) return a.fileCount - b.fileCount;
  if (sort === 'name-desc') return b.label.localeCompare(a.label);
  if (sort === 'rating-high' || sort === 'rating-low') {
    if (a.score === null && b.score !== null) return 1;
    if (b.score === null && a.score !== null) return -1;
    if (a.score !== b.score) return sort === 'rating-high' ? b.score - a.score : a.score - b.score;
  }
  return a.label.localeCompare(b.label);
}

function AssetItem({ row, remember, layout }) {
  return (
    <Link className={'ga-asset ga-asset-' + layout} to={row.path} onClick={remember}>
      <div className="ga-asset-image">
        {row.image ? <img src={row.image} alt="" loading="lazy" /> : <span>No preview</span>}
      </div>
      <div className="ga-asset-name">
        <span className="ga-classification">
          {row.system} · {row.kind}
        </span>
        <h3>{row.label}</h3>
        <span>
          {row.purpose}{row.selectedRevision && ' · ' + row.selectedRevision} · {row.fileCount} indexed {row.fileCount === 1 ? 'file' : 'files'}
        </span>
      </div>
      <div className="ga-asset-status">{row.state}</div>
      <span className={'ga-rating' + (row.score === null ? '' : ' ga-scored')}>
        {row.ratingLabel ?? 'Unrated'}
      </span>
    </Link>
  );
}

export function Library({ rows, query }) {
  const params = new URLSearchParams(query);
  const text = params.get('q') || '';
  const layout = ['cards', 'tree'].includes(params.get('layout')) ? params.get('layout') : 'list';
  const sort = params.get('sort') || 'name';
  const [search, setSearch] = useState(text);
  const [count, setCount] = useState(() => history.state?.libraryReturn?.count || 18);
  useEffect(() => {
    setSearch(text);
    setCount(history.state?.libraryReturn?.count || 18);
  }, [query]);
  const searchTerm = text.toLowerCase().trim();
  const selected = rows.map((row) => selectLibraryRow(row, searchTerm));
  const filtered = selected.filter((row) => matches(row, params, searchTerm)).sort((a, b) => compareRows(a, b, sort));
  const groups = [...new Set(filtered.map((r) => r.system))].sort();
  function apply(key, value) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    location.hash = route('library' + (next.size ? '?' + next : ''));
  }
  const clearParams = new URLSearchParams(params);
  for (const key of ['q', 'rating', ...fields.map(([key]) => key)]) clearParams.delete(key);
  function remember(event) {
    const group = event.currentTarget.closest('details')?.dataset.system;
    history.replaceState(
      {
        ...history.state,
        libraryReturn: {
          count,
          group,
          href: event.currentTarget.getAttribute('href'),
          y: window.scrollY,
        },
      },
      '',
    );
  }
  const item = (row) => <AssetItem key={row.id} row={row} layout={layout} remember={remember} />;
  return (
    <>
      <Heading title="Asset Library">
        Browse models by anatomy, teaching purpose and review evidence.
      </Heading>
      <section aria-label="Browse assets">
        <form
          className="ga-search"
          onSubmit={(event) => {
            event.preventDefault();
            apply('q', search.trim());
          }}
        >
          <input
            type="search"
            aria-label="Search assets"
            placeholder="Search names, tags or file paths"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <button>Search</button>
        </form>
        <div className="ga-facets">
          {fields.map(([key, label]) => (
            <label key={key}>
              {label}
              <select
                aria-label={label}
                value={params.get(key) || ''}
                onChange={(e) => apply(key, e.target.value)}
              >
                <option value="">All</option>
                {[...new Set(selected.map((r) => r[key]))].sort().map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </label>
          ))}
          <label>
            Rating
            <select
              aria-label="Rating"
              value={params.get('rating') || ''}
              onChange={(e) => apply('rating', e.target.value)}
            >
              <option value="">All</option>
              <option value="rated">Rated</option>
              <option value="unrated">Unrated</option>
            </select>
          </label>
        </div>
        <div className="ga-browse-tools">
          <div>
            <strong aria-live="polite">{filtered.length} entries</strong>
            {' · '}
            <Link to="rubric">Rating rubric</Link>
            {(text || params.has('rating') || fields.some(([k]) => params.has(k))) && (
              <>
                {' '}
                · <Link to={'library' + (clearParams.size ? '?' + clearParams : '')}>Clear filters</Link>
              </>
            )}
          </div>
          <div className="ga-view-tools">
            <label>
              Sort{' '}
              <select aria-label="Sort" value={sort} onChange={(e) => apply('sort', e.target.value)}>
                <option value="name">Name A–Z</option>
                <option value="name-desc">Name Z–A</option>
                <option value="rating-high">Highest rating</option>
                <option value="rating-low">Lowest rating</option>
                <option value="most-files">Most files</option>
                <option value="fewest-files">Fewest files</option>
              </select>
            </label>
            <div className="ga-switch" role="group" aria-label="Library layout">
              {['list', 'tree', 'cards'].map((v) => (
                <button key={v} aria-pressed={layout === v} onClick={() => apply('layout', v)}>
                  {v[0].toUpperCase() + v.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
        {layout === 'tree' ? (
          groups.map((system) => {
            const children = filtered.filter((r) => r.system === system);
            return (
              <details
                className="ga-branch"
                key={system}
                data-system={system}
                open={groups.length === 1 || history.state?.libraryReturn?.group === system || undefined}
              >
                <summary>
                  {system} <span>{children.length}</span>
                </summary>
                {children.map(item)}
              </details>
            );
          })
        ) : (
          <div className={layout === 'cards' ? 'ga-grid' : 'ga-rows'}>
            {filtered.slice(0, count).map(item)}
          </div>
        )}
        {!filtered.length && <p>No entries match these filters.</p>}
        {layout !== 'tree' && filtered.length > count && (
          <button className="ga-more" onClick={() => setCount(count + 24)}>
            Show more entries
          </button>
        )}
      </section>
    </>
  );
}

function AxisRatings({ axes }) {
  return ratingAxes.map((label, i) => (
    <React.Fragment key={label}><dt>{label}</dt><dd>{axes[i] ?? 'Unrated'}</dd></React.Fragment>
  ));
}

export function Revision({ revision, assessment }) {
  if (!Object.hasOwn(revisions, revision)) return <Missing />;
  const file = revisions[revision];
  const profile = ratingProfile(assessment?.axes.map((axis) => axis.score) ?? rated[revision]);
  return (
    <>
      <Link to="library">← Asset Library</Link>
      <Heading title={adrenalLibrary.title}>s1233 · CT-derived regional assembly</Heading>
      <nav className="ga-tabs" aria-label="Asset revision">
        {Object.keys(revisions).map((r) => (
          <Link key={r} aria-current={r === revision ? 'page' : undefined} to={libraryPath(r)}>
            {r}
          </Link>
        ))}
      </nav>
      <div className="ga-detail">
        <Scene key={revision} initial={baseView(revision)} origin={libraryPath(revision)} />
        <section>
          <Label>Selected revision · {revision}</Label>
          <h2>Regional exterior</h2>
          <p>{adrenalLibrary.scope}</p>
          <dl className="ga-facts">
            <dt>Export</dt>
            <dd>GLB · {(file.bytes / 1000).toFixed(1)} kB</dd>
            <dt>Teaching purpose</dt>
            <dd>Regional localization</dd>
            <dt>Revision</dt>
            <dd>{revision}</dd>
            <dt>Source</dt>
            <dd>{adrenalLibrary.source}</dd>
            <dt>Assessment</dt>
            <dd>
              {profile.ratingLabel} · {assessment?.task ?? 'regional localization'}
            </dd>
            <AxisRatings axes={profile.axes} />
          </dl>
          <Link to="rubric">Rating rubric</Link>
          {assessment?.target && <p><Link to={'compare/teaching-target?asset=' + assessment.export.sha256}>Review the current teaching target →</Link></p>}
          {assessment?.refinement && <p><Link to={refinementPath(assessment.export.sha256)}>Compare the teaching refinement →</Link></p>}
          {assessment && <TeachingAssessment assessment={assessment} />}
          <p>
            Agent review · 20 Nov 2026 ·{' '}
            <a href={sourceRoot + adrenalLibrary.revisions[revision].review}>
              Assessment and evidence
            </a>
          </p>
          <div className="ga-related">
            <Link to={lessonPath + '/region'}>Regional localization lesson →</Link>
            <Link to="use-cases/systems/endocrine">Explore the endocrine system →</Link>
            {rated[revision] && <Link to={comparePath}>Compare r04 and r05 →</Link>}
            <a href={assetUrl(file)} download>
              Download exact GLB ↓
            </a>
            <a href={file.source}>Package and attribution ↗</a>
          </div>
        </section>
      </div>
    </>
  );
}

function TeachingAssessment({ assessment, previous = false }) {
  const file = assessment.export;
  return (
    <details>
      <summary>{previous ? 'Earlier assessment and reviewed views' : 'Assessment and reviewed views'}</summary>
      <p>{assessment.task}</p>
      <p>{assessment.evaluator} · {assessment.date} · Rubric {assessment.rubric.revision.slice(0, 8)}</p>
      <p>Assessed export · {file.path.split('/').at(-1)} · SHA-256 <code className="ga-digest">{file.sha256}</code></p>
      <dl className="ga-facts">
        {assessment.axes.map((axis, i) => (
          <React.Fragment key={ratingAxes[i]}>
            <dt>{ratingAxes[i]} · {axis.score ?? 'Unrated'}</dt>
            <dd>{axis.observation}</dd>
          </React.Fragment>
        ))}
      </dl>
      {assessment.target && <>
        <h3>Teaching task · {assessment.target.status}</h3><p>{assessment.target.taskCheck}</p>
        {Object.entries(assessment.target.exemptions).map(([index, exemption]) => <section key={index}>
          <h4>{ratingAxes[index]} · target exemption</h4>
          <p>{exemption.reason}</p><p>Permitted use · {exemption.permittedUse}</p><p>Reopen when · {exemption.reopen}</p>
        </section>)}
      </>}
      {assessment.decision && <p>{assessment.decision}</p>}
      <h3>Sources and checks</h3>
      <ul>
        {assessment.sources.map((source) => (
          <li key={source.url}><a href={source.url}>{source.label} ↗</a></li>
        ))}
      </ul>
      <h3>Reviewed views</h3>
      <ul>
        {assessment.views.map((view) => (
          <li key={view.path}><a href={view.url ?? assetUrl(byPath.get(view.path))}>{view.label} ↗</a></li>
        ))}
      </ul>
    </details>
  );
}

export function CollectionEntry({ row, snapshot, exact, lessonQuery = '' }) {
  const file = exact?.selectedFile ?? exact?.exports.find((entry) => entry.path === exact.assessment?.export.path) ?? exact?.exports[0] ?? byPath.get(row.media?.[0]?.path);
  const salivaryStop = exact?.family === salivary.family && Object.keys(salivary.lessonFiles)
    .find((stop) => salivary.lessonFiles[stop] === file?.name);
  const lesson = salivaryStop ? salivary.lesson + '/' + salivaryStop : exact?.lesson;
  const priorAssessment = !exact && row.exportPath;
  const profile = exact ? ratingProfile(exact.axes) : priorAssessment ? row : ratingProfile();
  const assessment = exact?.assessment ?? (priorAssessment ? row.assessment : undefined);
  const teachingView = assessment?.views.find((view) => view.path === assessment.teachingView);
  const exactPreview = exact?.portrait;
  const preview = snapshot.previewGallery?.[row.previewIds?.[0]];
  const image = exact ? exact.preview : previewUrl(preview?.image) || row.image;
  const files = exact?.exports ?? row.media;
  const formats = [...new Set(files?.map((asset) => asset.path.split('.').at(-1).toUpperCase()))];
  const status = exact ? exact.status : row.state;
  const lessons = row.lessons ?? (exact?.assessment?.maintained?.sharedOwner && exact.sharedLessons);
  return (
    <>
      <Link to="library">← Asset Library</Link>
      <Heading title={exact?.title ?? row.label}>
        {row.system} · {row.purpose}
      </Heading>
      {lessons && <nav className="ga-related" aria-label="Lessons from this model">
        {lessons.map((study) => <Link key={study.library} to={study.library}
          aria-current={study.library === exact?.library ? 'page' : undefined}>{study.title}</Link>)}
      </nav>}
      <div className="ga-detail">
        {exact?.scene ? (
          <Scene key={exact.revision} initial={localView(exact)} origin={exact.library} />
        ) : teachingView ? (
          <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
            <Evidence key={teachingView.url} witness={{
              title: row.label, displayUrl: teachingView.url, alt: teachingView.label, caption: teachingView.label,
            }} />
          </div>
        ) : exactPreview?.sourceUrl ? (
          <div className="ga-pair ga-source-evidence-stacked">
            <Evidence key={row.id + '/' + exact.revision} witness={exactPreview} />
          </div>
        ) : exactPreview || image ? (
          <img
            className="ga-study-plate"
            src={exactPreview ? assetUrl(exactPreview.asset) : image}
            alt={exactPreview?.alt ?? row.label + ' retained preview'}
          />
        ) : (
          <p>Preview unavailable.</p>
        )}
        <section>
          {exact ? exact.finding && <p>{exact.finding}</p> : <h2>{row.use}</h2>}
          {(exact ? exact.limit : row.limit) && <p>{exact ? exact.limit : row.limit}</p>}
          <dl className="ga-facts">
            <dt>Catalogue ID</dt>
            <dd>{row.id}</dd>
            <dt>Entry type</dt>
            <dd>{row.kind}</dd>
            {status && <><dt>Review status</dt><dd>{status}</dd></>}
            <dt>Indexed files</dt>
            <dd>
              {(exact ? exact.exports.filter((asset) => !asset.unavailable).length : row.fileCount) + ' ' + formats.join(' · ')}
            </dd>
            {exact ? (
              <>
                <dt>Exact revision</dt><dd>{exact.revision}</dd>
              </>
            ) : priorAssessment ? (
              <>
                <dt>Reviewed revision</dt>
                <dd>{row.revision} · {row.reviewDate}</dd>
              </>
            ) : (
              <>
                <dt>Survey date</dt>
                <dd>{snapshot.generatedAt.slice(0, 10)}</dd>
              </>
            )}
            {(exact || priorAssessment) && <AxisRatings axes={profile.axes} />}
            {file?.license && (
              <>
                <dt>Export rights</dt>
                <dd>{file.license}</dd>
              </>
            )}
          </dl>
          <p>
            Rating · {profile.ratingLabel}
            {assessment ? ' · ' + assessment.task : profile.score != null && ' · teaching task above'}
            {assessment && exact?.exports.length > 1 && ' · ' + assessment.export.path.split('/').at(-1)}
            {' · '}
            <Link to="rubric">Rating rubric</Link>
          </p>
          {assessment?.target && <p><Link to={'compare/teaching-target?asset=' + assessment.export.sha256}>Review the current teaching target →</Link></p>}
          {assessment?.refinement && <p><Link to={refinementPath(assessment.export.sha256)}>Compare the teaching refinement →</Link></p>}
          {assessment && <TeachingAssessment assessment={assessment} />}
          {exact?.previousAssessment && <TeachingAssessment assessment={exact.previousAssessment} previous />}
          {exact && (
            <>
              {exact.credit && <p>{exact.credit}{exact.license && <> <a href={exact.license}>Source license and credits ↗</a></>}</p>}
              <div className="ga-related">
                {exact.verification && <a href={exact.verification.href}>{exact.verification.label}</a>}
                {exact.inspector && <a href={exact.inspector.href}>{exact.inspector.label} ↗</a>}
                {lesson && <Link to={lesson + lessonQuery}>{salivaryStop ? 'Open this Head & Neck lesson' : exact.useCase} →</Link>}
                {exact.compare && (
                  <Link to={exact.compare}>{exact.compareLabel ?? (exact.library === salivary.library ? 'Review the excluded duct course' : 'Open the saved source review')} →</Link>
                )}
              </div>
            </>
          )}
          <AdrenalReviewLinks row={row} />
          <a href={exact?.record ?? row.evidence?.url}>{priorAssessment ? 'Assessment and evidence ↗' : 'Source evidence and attribution ↗'}</a>
          {priorAssessment && (
            <div className="ga-related">
              <a href={file.source}>Package and attribution ↗</a>
              <Link to={'use-cases/systems/' + row.teachingSystem}>Explore the teaching system →</Link>
            </div>
          )}
          {row.id === 'swirendo_fdi31' && (!exact || exact.revision === 'balanced-20261028') && <BalancedDownload media={row.media} />}
          {file && !exact && (
            <p>
              <a href={assetUrl(file)}>Download {file.name}</a>
            </p>
          )}
        </section>
      </div>
      {!!row.history.length && (
        <nav aria-label="Revision history">
          <h2>Revision history</h2>
          {exact && !row.recommended && !row.exactLibrary && exact.library !== salivary.library && <Link to={'library/' + row.id}>Overview · {row.label}</Link>}
          <ul>
            {row.history.map((study) => (
              <li key={study.library}>
                <Link to={study.library + lessonQuery} aria-current={study.library === exact?.library ? 'page' : undefined}>
                  {study.title}
                </Link>
                {study.status && ' · ' + study.status}
              </li>
            ))}
          </ul>
        </nav>
      )}
      {exact && (
        <section>
          <h2>Exact exports</h2>
          <dl className="ga-facts">
            {exact.exports.map((exported) => (
              <React.Fragment key={exported.path}>
                <dt>
                  {exported.unavailable
                    ? exported.name
                    : <a href={assetUrl(exported)} download>{exported.name} ↓</a>}
                </dt>
                <dd>
                  {exportRole(exported) && <>{exportRole(exported)} · </>}{exported.bytes.toLocaleString('en-US')} bytes · SHA-256 <code className="ga-digest">{exported.sha256}</code>
                  {exact.fileAssessments?.size > 1 && <p><Link to={exactExportPath(exact, exported)}>Review {exported.name}</Link></p>}
                  {exported.unavailable && <p>{exported.unavailable}</p>}
                </dd>
              </React.Fragment>
            ))}
          </dl>
        </section>
      )}
      {!exact && !!row.media?.length && (
        <details>
          <summary>All indexed files ({row.media.length})</summary>
          {row.media.map((m) => (
            <p key={m.path}>
              <a href={byPath.has(m.path) ? assetUrl(byPath.get(m.path)) : m.url}>{m.path}</a>
            </p>
          ))}
        </details>
      )}
    </>
  );
}
