import React from 'react';
import { lessonPath, comparePath, libraryPath, salivary } from './catalog.js';
import { adrenalLesson } from './adrenal-study.js';
import { baseView } from './presets.js';
import { Scene } from './Scene.jsx';
import { Link, Label, Heading, Missing } from './GalleryUI.jsx';
import { PathwayLinks } from './Pathways.jsx';
import { oralSpacesPath, regionalPath } from './teaching-data.js';
import { SkeletalLessonLink } from './SkeletalLesson.jsx';
import { dentalLayersPath, heartSlicePath, oneBreathPath } from './SpecialistStills.jsx';
import { ultrasoundCollection } from './ultrasound-data.js';

import './use-cases.css';
import checks from './teaching-inputs/use-case-checks.json';

export function UseCases({ localPreview }) {
  return (
    <>
      <Heading title="Use Cases">
        Follow a teaching question from a regional view to the structure that answers it.
      </Heading>
      <section className="ga-collection-link">
        <Link to="use-cases/systems">Body Systems →</Link>
        <p>Orient in one of eleven system assemblies, then inspect a detail or follow a relationship.</p>
      </section>
      <section className="ga-collection-link">
        <Link to={salivary.lesson + '/location'}>Head &amp; Neck →</Link>
        <p>Find the major salivary glands and follow the supported parotid duct course.</p>
        <div className="ga-related">
          <Link className="ga-collection-related" to={oralSpacesPath}>Oral spaces · <span lang="zh">口腔空间关系</span> →</Link>
        </div>
      </section>
      <section className="ga-collection-link">
        <Link to="use-cases/airway">Airway Review →</Link>
        <p>Follow nasal airspace, the open trachea and the bronchial junction.</p>
      </section>
      {localPreview && <div className="ga-collection-link">
        <Link to={ultrasoundCollection}>Ultrasound Anatomy →</Link>
        <p>Use the probe location and matching section to identify anatomy in a synthetic scan.</p>
      </div>}
      <div className="ga-related">
        <Link to="use-cases/lessons">Lessons →</Link>
        <Link to="archive">Experiments &amp; Archive →</Link>
      </div>
      {localPreview && <details>
        <summary>Teaching checks · {checks.filter((c) => c.status === 'passed').length} passed · {checks.filter((c) => c.status === 'blocked').length} blocked</summary>
        {Array.from(new Set(checks.map((c) => c.collection)), (collection) => <section key={collection}>
          <h2>{collection}</h2>
          <ul>{checks.filter((c) => c.collection === collection).map((c) => <li key={c.route}>
            <Link to={c.route}>{c.action}</Link>{' · '}{c.status}. {c.observation}
          </li>)}</ul>
        </section>)}
        <Link to="use-cases/systems">Review the eleven Body Systems checks →</Link>
      </details>}
    </>
  );
}

export function LessonsIndex() {
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title="Lessons">Practise a single anatomy task or trace a named pathway.</Heading>
      <section>
        <h2>Locate structures</h2>
        <ul className="ga-lesson-links">
          <li><Link to={regionalPath}>Regional locators →</Link></li>
          <li><SkeletalLessonLink /></li>
          <li><Link to={lessonPath + '/' + adrenalLesson.stops[0].id}>{adrenalLesson.title} →</Link></li>
          <li><Link to="use-cases/right-arm/elbow">Practice the right elbow and shoulder →</Link></li>
          <li><Link to="use-cases/dental-arch">Dental arch identification · <span lang="zh">牙列辨认</span> →</Link></li>
          <li><Link to={oralSpacesPath}>Oral spaces · <span lang="zh">口腔空间关系</span> →</Link></li>
        </ul>
      </section>
      <section>
        <h2>Follow sequences and compare views</h2>
        <ul className="ga-lesson-links">
          <li><Link to={oneBreathPath}>One Breath · <span lang="zh">一次呼吸</span> →</Link></li>
          <li><Link to={heartSlicePath}>Read the same heart slice three ways →</Link></li>
          <li><Link to={dentalLayersPath}>Reveal the layers of a prepared incisor →</Link></li>
        </ul>
      </section>
      <section>
        <h2>Pathway diagrams</h2>
        <div className="ga-related"><PathwayLinks /></div>
      </section>
    </>
  );
}

export function Lesson({ stop }) {
  const index = adrenalLesson.stops.findIndex(({ id }) => id === stop);
  if (index === -1) return <Missing />;
  const current = adrenalLesson.stops[index];
  const next = adrenalLesson.stops[index + 1];
  return (
    <>
      <Link to="use-cases/lessons">← Lessons</Link>
      <Heading title={adrenalLesson.title}>Endocrine system · Regional localization</Heading>
      <nav className="ga-tabs" aria-label="Lesson stops">
        {adrenalLesson.stops.map(({ id, label }, i) => (
          <Link key={id} aria-current={id === stop ? 'step' : undefined} to={lessonPath + '/' + id}>
            {i + 1}. {label}
          </Link>
        ))}
      </nav>
      <div className="ga-detail">
        <Scene key={stop} initial={baseView(adrenalLesson.revision, current.part)} origin={lessonPath + '/' + stop} />
        <section>
          <Label>Stop {index + 1} of {adrenalLesson.stops.length}</Label>
          <h2>{current.title}</h2>
          <p>{current.text}</p>
          <div className="ga-related">
            {next && <Link to={lessonPath + '/' + next.id}>Next · {next.label} →</Link>}
            <Link to={libraryPath(adrenalLesson.revision)}>Open asset · s1233 {adrenalLesson.revision} →</Link>
            <Link to={comparePath}>Inspect the fold evidence →</Link>
          </div>
        </section>
      </div>
    </>
  );
}
