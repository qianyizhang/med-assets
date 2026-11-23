import React from 'react';
import { DataComponent, useDataApp } from '../../data-app-public.jsx';
import { planning } from './selected-library.js';
import { libraryAliases } from './library-view.js';
import { Heading, Label, Link, Missing } from './GalleryUI.jsx';

export const surveyCoverageId = 'survey-coverage';

function Coverage({ snapshot }) {
  const { appTitle, canEdit, mode, setAppTitle } = useDataApp();
  const survey = snapshot.survey;
  const families = snapshot.queries.model_survey.rows;
  const products = snapshot.queries.products.rows;
  const files = snapshot.queries.media_inventory.rows;
  const editing = canEdit && mode === 'edit';

  return (
    <DataComponent
      id={surveyCoverageId}
      title="Collection at a glance"
      kind="custom"
      queryId="model_survey"
      queryIds={['model_survey', 'products', 'media_inventory']}
      displayRows={families}
      sourceRowsByQuery={{ model_survey: families, products, media_inventory: files }}
    >
      <div data-reviewed-rows>
        <p
          data-data-app-title
          contentEditable={editing}
          suppressContentEditableWarning
          onBlur={editing ? (event) => setAppTitle(event.currentTarget.textContent.trim() || appTitle) : undefined}
        >
          {appTitle}
        </p>
        <dl className="ga-facts">
          <dt>Model families</dt><dd>{survey.familyCount}</dd>
          <dt>Related products and studies</dt><dd>{survey.productCount}</dd>
          <dt>Asset GLB paths</dt><dd>{survey.assetGlbPaths}</dd>
          <dt>Source and review GLB paths</dt><dd>{survey.glbPaths - survey.assetGlbPaths}</dd>
        </dl>
        <p>Counts describe the dated repository inventory. The Asset Library carries current export and review information.</p>
        <a href={'https://github.com/qianyizhang/med-assets/tree/' + survey.revision}>Open the surveyed revision</a>
      </div>
      <details>
        <summary>Recorded evidence limits and source disagreements</summary>
        <p>Fresh neutral previews were unreviewed. Folder and file counts describe editorial groupings. Terms and rights depend on the original source.</p>
        {survey.mismatches.map((record) => (
          <section key={record.label}>
            <h3>{record.label}</h3>
            <p><a href={record.url}>{record.evidence}</a> · <a href={record.otherUrl}>{record.other}</a></p>
            <p>{record.fix}</p>
          </section>
        ))}
      </details>
    </DataComponent>
  );
}

export function Planning({ snapshot, section }) {
  const survey = snapshot.survey;
  if (!['coverage', 'overlaps', 'gaps'].includes(section)) return <Missing />;
  return (
    <>
      <Link to="archive">← Experiments &amp; Archive</Link>
      <Heading title="Survey planning report">
        {snapshot.generatedAt.slice(0, 10)} · Model Survey snapshot {survey.revision.slice(0, 8)}
      </Heading>
      <nav className="ga-tabs" aria-label="Planning sections">
        {['coverage', 'overlaps', 'gaps'].map((key) => (
          <Link
            key={key}
            aria-current={key === section ? 'page' : undefined}
            to={'archive/planning/' + key}
          >
            {key[0].toUpperCase() + key.slice(1)}
          </Link>
        ))}
      </nav>
      {section === 'coverage' && <Coverage snapshot={snapshot} />}
      {section === 'overlaps' && survey.overlaps.map((record) => (
        <section className="ga-planning" key={record.title}>
          <Label>{record.action}</Label>
          <h2>{record.title}</h2>
          <p>{record.detail}</p>
          <div className="ga-actions">
            {record.ids.map((id) => {
              const r = planning.find((row) => row.id === (libraryAliases[id] ?? id));
              return (
                r && (
                  <Link key={id} to={r.path}>
                    {r.label}
                  </Link>
                )
              );
            })}
          </div>
        </section>
      ))}
      {section === 'gaps' && survey.gaps.map((record) => (
        <section className="ga-planning" key={record.label}>
          <Label>
            {record.group} · {record.priority} · {record.state}
          </Label>
          <h2>{record.label}</h2>
          <p>{record.scope}</p>
          <a href={record.source}>Scope evidence ↗</a>
        </section>
      ))}
    </>
  );
}
