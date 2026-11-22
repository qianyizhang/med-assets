import React from 'react';
import { salivary } from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { Heading, Link, Missing } from './GalleryUI.jsx';
import { PartLesson } from './PartLesson.jsx';
import { salivaryLocalEdition, salivaryTask } from './salivary-tasks.js';
import teachingReview from './teaching-inputs/teaching-assessments.json';
import { oralSpacesPath } from './teaching-data.js';

const stops = {
  location: {
    title: 'Find the three gland pairs',
    views: ['annotated-context', 'context-superior-source', 'context-inferior-source'],
  },
  'duct-course': {
    title: 'Follow the parotid duct over the masseter',
    views: ['context-side-source', 'glands-ducts-front-source'],
  },
};

const evidence = {
  'annotated-context': ['Identify the three gland pairs · r02 source key', 'Labels point to the parotid beside the mandible, the submandibular below it and the sublingual in the floor of the mouth.', 'Same-source context with gland labels.'],
  'context-superior-source': ['Context from above', 'Looking down inside the jaw at the paired glands and muscles.', 'Use this angle to inspect the floor of the mouth.'],
  'context-inferior-source': ['Context from below', 'Looking up at the floor of the mouth under the mandible.', 'Use this angle to locate the submandibular glands below the jaw.'],
  'context-side-source': ['Context from the side', 'The parotid duct runs forward from the gland across the superficial masseter.', 'The side view places the retained duct against the muscle.'],
  'glands-ducts-front-source': ['Isolated glands and parotid ducts', 'Front view with three gland pairs and two forward-running parotid ducts.', 'The primary export omits the mandible and muscles.'],
  'rejection-closeup': ['Rejected left submandibular duct', 'Opaque and translucent views show the left source duct passing through the modeled mylohyoid.', 'Diagnostic transparency exposes the crossing in the original source. The course is excluded from the teaching exports.'],
  comparison: ['Draft and scoped source views', 'The original draft and source-preserved gland shapes shown in separate poses.', 'The sources and poses differ. Use this comparison to inspect the change in teaching scope.'],
};

function SalivaryEvidence({ names }) {
  return (
    <div className="ga-pair ga-source-evidence">
      {names.map((name) => {
        const [title, alt, caption] = evidence[name];
        return <Evidence key={name} witness={{ asset: salivary.witness(name), title, alt, caption }} />;
      })}
    </div>
  );
}

export function SalivaryLesson({ stop = 'location', query, localPreview }) {
  if (!Object.hasOwn(stops, stop)) return <Missing />;
  const view = stops[stop];
  const localLibrary = 'library/' + salivary.family + '/' + salivaryLocalEdition;
  const current = localPreview && teachingReview.campaign.find((row) => row.maintained &&
    row.route === localLibrary && row.export.path.endsWith('/' + salivary.lessonFiles[stop]));
  const library = current ? current.route + '?file=' + current.export.sha256 : salivary.library;
  const chinese = new URLSearchParams(query).get('oral') === 'zh';
  const language = chinese ? '?oral=zh' : '';
  const cutaway = oralSpacesPath + (chinese ? '/zh' : '/en') + (stop === 'duct-course' ? '?from=duct-course' : '');
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title="Locate the major salivary glands">Head &amp; Neck · Z-Anatomy</Heading>
      <nav className="ga-tabs" aria-label="Lesson stops">
        <Link to={salivary.lesson + '/location' + language} aria-current={stop === 'location' ? 'step' : undefined}>
          Gland locations
        </Link>
        <Link to={salivary.lesson + '/duct-course' + language} aria-current={stop === 'duct-course' ? 'step' : undefined}>
          Parotid duct course
        </Link>
      </nav>
      <h2>{view.title}</h2>
      <PartLesson key={stop} task={salivaryTask(stop, Boolean(current))} />
      {stop === 'duct-course' && (
        <section>
          <h3>The submandibular crossing remains unresolved</h3>
          <p>
            The original left submandibular duct crosses the modeled mylohyoid. The right course
            remains unaccepted. Both ducts are excluded, and the outlet locations
            and lumens remain unverified.
          </p>
          <Link to={salivary.compare}>See the rejected reconstruction in Compare →</Link>
        </section>
      )}
      <details>
        <summary>Source views from the r02 study</summary>
        <SalivaryEvidence names={view.views} />
        <a href={salivary.license}>Z-Anatomy source license and credits ↗</a>
      </details>
      <div className="ga-related">
        {stop === 'location' && <Link to={salivary.lesson + '/duct-course' + language}>Follow the parotid duct →</Link>}
        <Link to={library}>Open this lesson’s export in Asset Library →</Link>
        <Link to={cutaway}>Locate the oral vestibule in a 2D cutaway →</Link>
      </div>
    </>
  );
}

export function SalivaryReview() {
  return (
    <>
      <Link to="compare">← Compare</Link>
      <Heading title="The rejected submandibular duct crossing">
        Head &amp; Neck · Z-Anatomy r02 source review · 26 October 2026
      </Heading>
      <p>
        The original left duct crosses the modeled mylohyoid. The diagnostic exposes that
        crossing and documents why the review withheld both submandibular ducts. The right
        course has no independently confirmed defect.
      </p>
      <SalivaryEvidence names={['rejection-closeup', 'comparison']} />
      <h2>Review scope</h2>
      <p>
        The scoped export retains the gland surfaces for gross localization and the parotid
        surface course. The original whole model remains Needs revision. The accepted scope
        excludes complete duct routing, outlets, lumens and clinical use.
      </p>
      <div className="ga-related">
        <Link to={salivary.lesson + '/duct-course'}>Return to the parotid duct lesson →</Link>
        <Link to={salivary.library}>Open the exact r02 exports in Asset Library →</Link>
        <a href={salivary.record}>Source record and diagnostic replay ↗</a>
      </div>
    </>
  );
}
