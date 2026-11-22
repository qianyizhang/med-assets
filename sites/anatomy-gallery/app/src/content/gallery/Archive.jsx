import React, { useRef, useState } from 'react';
import image26Stories from './teaching-inputs/image26-stories.json';
import image26Media from './teaching-inputs/image26-media.json';
import image26Srt from './teaching-inputs/image26-narration.srt?raw';
import treatmentsSrt from './teaching-inputs/treatments-narration.srt?raw';
import { localizeCaptions, readCaptions, vtt } from './archive-captions.js';
import { assetUrl, byPath } from './catalog.js';
import { Heading, Link, Missing } from './GalleryUI.jsx';
import { dentalShotsPath } from './SpecialistStills.jsx';

const source = 'https://github.com/qianyizhang/med-assets/blob/9d70d26/experiments/';
const treatmentsPath = 'dental-video-treatments';
const image26Path = 'dental-image26';
const treatmentsCues = readCaptions(treatmentsSrt);
const image26Cues = readCaptions(image26Srt);
const treatments = [
  { id: 'hyperframes', title: 'Before the hole', engine: 'HyperFrames', cue: 'Follow the contrast between the opening tooth, the plaque factory and the mineral exchange.' },
  { id: 'remotion', title: 'The Decay File', engine: 'Remotion', cue: 'Watch the captions and editorial dioramas explain the chain from cause to assessment.' },
  { id: 'manimgl', title: 'The Mineral Ledger', engine: 'ManimGL', cue: 'Watch the repeated tiles and particles show mineral loss, repair and surface breakdown.' },
  { id: 'comparison', title: 'Synchronized comparison', cue: 'Compare shots and pacing against a single soundtrack. Use the individual films to read small labels at full size.' },
].map((study) => ({
  ...study, cues: treatmentsCues,
  asset: byPath.get('experiments/' + treatmentsPath + '/results/' + study.id + '.mp4'),
}));

const image26Films = [{
  id: 'combined',
  title: 'From condition to treatment',
  cue: 'Watch all five stories in their original sequence.',
  cues: image26Cues,
  file: 'dental-condition-to-treatment.mp4',
}];
let firstCue = 1;
for (const { id, title, condition, procedure, shots, takeaway } of image26Stories.stories) {
  const cueCount = shots.length + 2;
  image26Films.push({
    id, title, cue: condition + ' → ' + procedure, takeaway,
    cues: localizeCaptions(image26Cues, firstCue, cueCount), file: id + '.mp4',
  });
  firstCue += cueCount;
}
for (const film of image26Films) {
  film.asset = image26Media.find((media) => media.name === film.file);
}

function ArchiveLink({ to, title, children }) {
  return (
    <section className="ga-collection-link">
      <Link to={to}>{title} →</Link>
      <p>{children}</p>
    </section>
  );
}

export function Archive() {
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title="Experiments &amp; Archive">Retained studies and planning records.</Heading>
      <ArchiveLink to="archive/kidney-outline-trial" title="Left kidney outline trial">
        Compare a dashed exterior outline with the equal-scale side-by-side control.
      </ArchiveLink>
      <ArchiveLink to={'archive/' + treatmentsPath} title="One script, three dental video treatments">
        Watch three approaches to the same narration and compare their shot choices in sync.
      </ArchiveLink>
      <ArchiveLink to={'archive/' + image26Path} title="Dental Image 2.6 stories">
        Watch five original generative-media studies and the combined film.
      </ArchiveLink>
      <ArchiveLink to={dentalShotsPath} title="Dental shot studies">
        Compare the original specimen poses with the separately authored caries and gum pocket storyboards.
      </ArchiveLink>
      <Link to="archive/planning">Model Survey · Overlaps and Gaps →</Link>
    </>
  );
}

function FilmPlayer({ film }) {
  const [failed, setFailed] = useState(!film.asset);
  const focusOnRetry = useRef(false);
  const captions = 'data:text/vtt;charset=utf-8,' + encodeURIComponent(vtt(film.cues));
  return (
    <>
      {failed ? (
        <div>
          <p role="status">The retained video is unavailable. The narration and study record are still available.</p>
          {film.asset && <button type="button" onClick={() => {
            focusOnRetry.current = true;
            setFailed(false);
          }}>Retry video</button>}
        </div>
      ) : (
        <video ref={(player) => {
          if (player && focusOnRetry.current) {
            player.focus();
            focusOnRetry.current = false;
          }
        }} className="ga-archive-video" controls
          playsInline preload="metadata" aria-label={film.title} src={assetUrl(film.asset)}
          onError={() => setFailed(true)}>
          <track kind="captions" srcLang="en" label="English narration" src={captions} />
        </video>
      )}
      <details className="ga-film-transcript">
        <summary>Narration transcript</summary>
        {film.cues.map(({ start, text }) => <p key={start}>{text}</p>)}
      </details>
    </>
  );
}

export function DentalFilms({ collection, id }) {
  const generated = collection === image26Path;
  const films = generated ? image26Films : treatments;
  const film = id ? films.find((candidate) => candidate.id === id) : films[0];
  if (!film) return <Missing />;
  const title = generated ? 'Dental Image 2.6 stories' : 'One script, three dental video treatments';
  const storyboard = byPath.get('experiments/' + treatmentsPath + '/results/storyboard.jpg');
  return (
    <>
      <Link to="archive">← Experiments &amp; Archive</Link>
      <Heading title={title}>
        {generated
          ? '2026-11-06 · Five illustrated studies made from 16 native Image 2.6 GIFs and frozen narration.'
          : '2026-11-03 · Three 48-second films with the same six beats, voice and score.'}
      </Heading>
      <nav className="ga-tabs" aria-label="Films">
        {films.map((option) => (
          <Link key={option.id} to={'archive/' + collection + '/' + option.id}
            aria-current={option === film ? 'page' : undefined}>
            {option.engine ?? option.title}
          </Link>
        ))}
      </nav>
      <h2>{film.title}</h2>
      <p>{film.cue}</p>
      <FilmPlayer key={film.id} film={film} />
      {film.takeaway && <p>{film.takeaway}</p>}
      <h2>Study scope</h2>
      {generated ? (
        <>
          <p>The original GIFs play once in the edit. Separate shots can vary in tooth and gum geometry. Cuts illustrate changes over time. Anatomical identity and measured healing remain unverified.</p>
          <p>Assessment and many clinical substeps are omitted. These generative-media studies have no clinical or anatomy approval. The six films are available through the local preview with the verified teaching backup restored.</p>
        </>
      ) : (
        <>
          <p>The treatments use different shot design, graphics, transitions and captions. The comparison shows how these authored versions tell the story.</p>
          <p>The films use original schematics, synthetic Kokoro narration and an original procedural score. Direct listening and clinical review remain open. The teaching scope covers mechanisms and assessment.</p>
        </>
      )}
      <div className="ga-related">
        <a href={source + collection + '/README.md'}>Experiment, playback evidence and provenance ↗</a>
        {generated ? (
          <a href={source + collection + '/SCRIPTS.md'}>Original scripts and prompts ↗</a>
        ) : (
          <>
            <a href={source + collection + '/COMPARISON.md'}>Comparison findings ↗</a>
            <a href={source + collection + '/results/manifest.json'}>Reviewed result identities ↗</a>
            {storyboard && <a href={assetUrl(storyboard)}>Original matched storyboard ↗</a>}
          </>
        )}
      </div>
    </>
  );
}
