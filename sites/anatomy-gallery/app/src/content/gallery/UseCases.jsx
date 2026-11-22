import React from 'react';
import { lessonPath, comparePath, libraryPath, portrait, salivary } from './catalog.js';
import { adrenalLesson } from './adrenal-study.js';
import { baseView } from './presets.js';
import { Scene } from './Scene.jsx';
import { Link, Label, Heading, Missing } from './GalleryUI.jsx';
import { PathwayLinks } from './Pathways.jsx';
import { oralSpacesPath, regionalPath } from './teaching-data.js';
import { SkeletalLessonLink } from './SkeletalLesson.jsx';
import { dentalLayersPath, heartSlicePath, oneBreathPath } from './SpecialistStills.jsx';

import checks from './teaching-inputs/use-case-checks.json';

export function UseCases({ localPreview }) {
  return (
    <>
      <Heading title="Use Cases">
        Follow a teaching question from a regional view to the structure that answers it.
      </Heading>
      {localPreview && <details>
        <summary>Teaching checks · {checks.filter((c) => c.status === 'passed').length} passed · {checks.filter((c) => c.status === 'blocked').length} blocked</summary>
        {Array.from(new Set(checks.map((c) => c.collection)), (collection) => <section key={collection}>
          <h3>{collection}</h3>
          <ul>{checks.filter((c) => c.collection === collection).map((c) => <li key={c.route}>
            <Link to={c.route}>{c.action}</Link>{' · '}{c.status}. {c.observation}
          </li>)}</ul>
        </section>)}
        <Link to="use-cases/systems">Review the eleven Body Systems checks →</Link>
      </details>}
      <div className="ga-collection-link">
        <Link to="use-cases/systems">Body Systems →</Link>
        <p>Eleven systems in paired views, from whole assemblies to named parts.</p>
      </div>
      <div className="ga-collection-link">
        <Link to={salivary.lesson + '/location'}>Head &amp; Neck →</Link>
        <p>Find the major salivary glands and follow the supported parotid duct course.</p>
      </div>
      <div className="ga-collection-link">
        <Link to={oralSpacesPath}>Oral spaces · <span lang="zh">口腔空间关系</span> →</Link>
        <p>Use the teeth and gingiva to locate the vestibule and oral cavity proper.</p>
      </div>
      <div className="ga-collection-link">
        <Link to="use-cases/airway">Airway Review →</Link>
        <p>Follow nasal airspace, the open trachea and the bronchial junction.</p>
      </div>
      <div className="ga-collection-link">
        <Link to={oneBreathPath}>One Breath · <span lang="zh">一次呼吸</span> →</Link>
        <p>Read the original storyboard from breathing mechanics to gas exchange.</p>
      </div>
      <div className="ga-collection-link">
        <Link to={heartSlicePath}>Read the same heart slice three ways →</Link>
        <p>Compare three synthetic displays of the same cardiac plane.</p>
      </div>
      <div className="ga-collection-link">
        <Link to={regionalPath}>Regional locators →</Link>
        <p>Locate aortic arch branches, the pulmonary vein, the brainstem source cut and the tubal end.</p>
      </div>
      <section className="ga-collection-link">
        <h2>Pathway diagrams</h2>
        <div className="ga-related"><PathwayLinks /></div>
      </section>
      <div className="ga-collection-link">
        <SkeletalLessonLink />
        <p>Locate the second costal cartilages and the L3–L4 disc among their neighboring bones.</p>
      </div>
      <div className="ga-collection-link">
        <Link to="use-cases/dental-arch">Dental arch identification · <span lang="zh">牙列辨认</span> →</Link>
        <p>Choose a crown or an FDI label to identify the tooth, its arch and the patient’s side.</p>
      </div>
      <div className="ga-collection-link">
        <Link to={dentalLayersPath}>Reveal the layers of a prepared incisor →</Link>
        <p>Compare the source pose with isolated layers of the prepared FDI 31 specimen.</p>
      </div>
      <div className="ga-hero">
        <div className="ga-hero-copy">
          <Label>Endocrine system · s1233</Label>
          <h2>{adrenalLesson.title}</h2>
          <p>Find each gland above its kidney, then follow the curved lower rim of the right gland.</p>
          <Link className="ga-primary" to={lessonPath + '/' + adrenalLesson.stops[0].id}>
            Begin lesson <span aria-hidden="true">→</span>
          </Link>
        </div>
        <div className="ga-hero-plate">
          <img src={portrait('updated-iso')} alt="Paired adrenal glands above the kidneys" />
        </div>
      </div>
      <div className="ga-related">
        <Link to="archive">Experiments &amp; Archive →</Link>
      </div>
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
      <Link to="use-cases">← Use Cases</Link>
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
