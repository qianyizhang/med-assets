import React from 'react';
import { lessonPath, comparePath, libraryPath, studies } from './catalog.js';
import { baseView } from './presets.js';
import { Scene } from './Scene.jsx';
import { libraryRows } from './Library.jsx';
import { Link, Label, Heading, Hero, Missing } from './GalleryUI.jsx';

export function UseCases() {
  return (
    <>
      <Heading title="Use Cases">
        Follow a teaching question from a regional view to the structure that answers it.
      </Heading>
      <Hero lesson />
      <div className="ga-related">
        <Link to="archive">Experiments &amp; Archive →</Link>
      </div>
    </>
  );
}

export function Lesson({ stop }) {
  const detail = stop === 'right-gland';
  if (!['region', 'right-gland'].includes(stop)) return <Missing />;
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title="Locate the adrenal glands">Endocrine system · Regional localization</Heading>
      <nav className="ga-tabs" aria-label="Lesson stops">
        {studies.lessons[0].stops.map((s, i) => (
          <Link key={s} aria-current={s === stop ? 'step' : undefined} to={lessonPath + '/' + s}>
            {i + 1}. {i ? 'Right inferior rim' : 'Regional view'}
          </Link>
        ))}
      </nav>
      <div className="ga-detail">
        <Scene key={stop} initial={baseView('r05', detail ? 'Right adrenal gland' : 'All structures')} />
        <section>
          <Label>Stop {detail ? '2 of 2' : '1 of 2'}</Label>
          <h2>{detail ? 'Follow the inferior rim' : 'Find the glands above the kidneys'}</h2>
          <p>
            {detail
              ? 'Isolate the right gland. Follow its recessed face to the lower rim, then rotate to see where the fold deepens. Its warm finish is illustrative.'
              : 'Use the two kidneys to orient yourself. Look above and medial to each kidney for its adrenal gland. Keep the pancreas visible as regional context.'}
          </p>
          <div className="ga-related">
            {!detail && <Link to={lessonPath + '/right-gland'}>Next · Right inferior rim →</Link>}
            <Link to={libraryPath('r05')}>Open asset · s1233 r05 →</Link>
            <Link to={comparePath}>Inspect the fold evidence →</Link>
          </div>
        </section>
      </div>
    </>
  );
}

export function Planning({ snapshot, section }) {
  const survey = snapshot.survey;
  const rows = libraryRows(snapshot);
  if (!['overlaps', 'gaps'].includes(section)) return <Missing />;
  return (
    <>
      <Link to="archive">← Experiments &amp; Archive</Link>
      <Heading title="Survey planning report">
        {snapshot.generatedAt.slice(0, 10)} · Model Survey snapshot {survey.revision.slice(0, 8)}
      </Heading>
      <nav className="ga-tabs" aria-label="Planning sections">
        {['overlaps', 'gaps'].map((key) => (
          <Link
            key={key}
            aria-current={key === section ? 'page' : undefined}
            to={'archive/planning/' + key}
          >
            {key === 'overlaps' ? 'Overlaps' : 'Gaps'}
          </Link>
        ))}
      </nav>
      {section === 'overlaps'
        ? survey.overlaps.map((record) => (
            <section className="ga-planning" key={record.title}>
              <Label>{record.action}</Label>
              <h2>{record.title}</h2>
              <p>{record.detail}</p>
              <div className="ga-actions">
                {record.ids.map((id) => {
                  const r = rows.find((row) => row.id === id);
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
          ))
        : survey.gaps.map((record) => (
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
