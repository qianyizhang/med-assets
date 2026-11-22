import React from 'react';
import systems from './body-systems.json';
import { byPath } from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { Heading, Link, Missing } from './GalleryUI.jsx';
import {
  skeletalCredit, skeletalLibraryPath, skeletalLicense, skeletalPackage, skeletalPath, skeletalPlatePath,
  skeletalReview, skeletalSource, skeletalStops,
} from './skeletal-data.js';

const systemPath = 'use-cases/systems/skeletal';
const views = [
  ['Front', '前视'],
  ['Side', '侧视'],
  ['Neutral gray', '中性灰材质检查'],
  ['Oblique · diagnostic materials', '斜视 · 示意材质'],
];

export function SkeletalLessonLink({ detail }) {
  return (
    <Link to={skeletalPath + (detail ? '?from=' + detail : '')}>Skeletal relationships →</Link>
  );
}

function SkeletalPlate({ stop, index }) {
  const path = skeletalPlatePath(stop.sourceId, index + 1);
  const [view, zh] = views[index];
  return (
    <Evidence witness={{
      asset: byPath.get(path),
      sourceUrl: skeletalSource + path,
      title: view + ' · ' + zh,
      alt: stop.captions[index],
      caption: stop.captions[index],
      width: 800,
      height: 800,
    }} />
  );
}

export function skeletalDetail(query) {
  const from = new URLSearchParams(query).get('from');
  const system = systems.find((entry) => entry.id === 'skeletal');
  return system.plates.some((plate) => plate.kind === 'detail' && plate.id === from) ? from : '';
}

export function SkeletalLesson({ id = 'second-costal', query }) {
  const stop = skeletalStops.find((entry) => entry.id === id);
  if (!stop) return <Missing />;
  const detail = skeletalDetail(query);
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title={stop.title}><span lang="zh">{stop.zh}</span></Heading>
      <nav className="ga-tabs" aria-label="Skeletal relationships">
        {skeletalStops.map(({ id, title }) => (
          <Link key={id} to={skeletalPath + '/' + id + (detail ? '?from=' + detail : '')}
            aria-current={id === stop.id ? 'page' : undefined}>{title}</Link>
        ))}
      </nav>
      <p>{stop.cue}</p>
      <div className="ga-pair ga-source-evidence ga-skeletal-plates">
        <SkeletalPlate key={stop.id + '-front'} stop={stop} index={0} />
        <SkeletalPlate key={stop.id + '-side'} stop={stop} index={1} />
      </div>
      <details>
        <summary>Oblique and neutral-gray views</summary>
        <div className="ga-pair ga-source-evidence ga-skeletal-plates">
          <SkeletalPlate key={stop.id + '-oblique'} stop={stop} index={3} />
          <SkeletalPlate key={stop.id + '-neutral'} stop={stop} index={2} />
        </div>
      </details>
      <h2>Scale and limits</h2>
      <p>The GLB preserves source coordinates with millimetre-to-metre conversion and an export-axis conversion. The plates use view-specific framing without a measurement scale. Blue is a diagnostic display color.</p>
      <p>{stop.limit} Coarse source seams remain. The review covered static teaching readability. Anatomy and 3D runtime remain unreviewed for these studies. The original cartilage model still needs revision.</p>
      <h2>Source and attribution</h2>
      <p>{skeletalCredit} licensed under CC Attribution 4.0 International. The original OBJ headers retain CC BY-SA 2.1 Japan.</p>
      <div className="ga-related">
        <Link to={skeletalLibraryPath(stop.id) + (detail ? '?from=' + detail : '')}>Open the exact Library revision →</Link>
        <a href={skeletalSource + skeletalReview}>Original static review ↗</a>
        <a href={skeletalSource + skeletalPackage}>Assembly and source dependencies ↗</a>
        <a href={skeletalLicense}>BodyParts3D license ↗</a>
        <Link to={systemPath + (detail ? '?detail=' + detail : '')}>Return to Body Systems · Skeletal →</Link>
      </div>
    </>
  );
}
