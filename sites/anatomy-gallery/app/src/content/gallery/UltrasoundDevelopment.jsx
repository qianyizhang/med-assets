import React from 'react';
import { Heading, Link } from './GalleryUI.jsx';
import { ultrasoundCollection, ultrasoundDevelopment } from './ultrasound-data.js';
import record from './ultrasound-progress/record.json';
import mesh from './ultrasound-progress/kidney-right.mesh?url';
import surfaces from './ultrasound-progress/matched-surfaces.webp';
import planes from './ultrasound-progress/protected-planes.webp';
import frame from './ultrasound-progress/live-frame-12.webp';

const revisionPath = ultrasoundDevelopment + '/kidney-right-r01';
const number = new Intl.NumberFormat('en-US');
const axes = {
  fidelity: 'Fidelity',
  form: 'Form',
  readability: 'Teaching readability',
  economy: 'Mesh economy',
};

export function UltrasoundDevelopment({ showRevision }) {
  const delta = Math.round(100 * (1 - record.export.bytes / record.previous.bytes));
  return (
    <>
      <Link to={showRevision ? ultrasoundDevelopment : ultrasoundCollection}>
        {showRevision ? '← Ultrasound Development' : '← Ultrasound Anatomy'}
      </Link>
      {showRevision ? (
        <>
          <Heading title="s1233 right kidney · r01">AssetKit revision · Lead review pending</Heading>
          <section className="ga-collection-link">
            <p><code>{record.ref}</code></p>
            <dl>
              <dt>Coordinate frame</dt><dd>s1233 voxel indices · RAS axes · 1.5 mm spacing</dd>
              <dt>Export</dt><dd>{number.format(record.export.triangles)} triangles · {number.format(record.export.bytes)} bytes</dd>
              <dt>SHA-256</dt><dd><code className="ga-progress-hash">{record.export.sha256}</code></dd>
            </dl>
            <div className="ga-related">
              <a href={mesh} download="kidney-right-r01.mesh">Download the exact packed mesh</a>
              <a href={record.source.url}>TotalSegmentator v2.0.1 · Jakob Wasserthal and contributors · CC BY 4.0</a>
            </div>
          </section>
        </>
      ) : (
        <>
          <Heading title="Ultrasound Development" />
          <article className="ga-collection-link ga-ultrasound-progress" aria-labelledby="right-kidney-progress">
            <h2 id="right-kidney-progress">Right kidney · Before → After</h2>
            <p>Abdominal survey long axis · s1233 teaching exemplar · Lead review pending</p>
            <figure>
              <img src={surfaces} width="1304" height="699" alt="At the same physical scale, the schematic ellipsoid becomes an asymmetric CT-derived kidney with rounded poles and a visible medial recess. The lower row shows the reverse angle." />
              <figcaption>107 mm schematic, CT half-label surface and refined r01.</figcaption>
            </figure>
            <dl className="ga-progress-metrics">
              <div><dt>Sweep mesh triangles</dt><dd>{number.format(record.previous.triangles)} → {number.format(record.export.triangles)}</dd></div>
              <div><dt>Sweep mesh bytes</dt><dd>{number.format(record.previous.bytes)} → {number.format(record.export.bytes)} · {delta}% smaller</dd></div>
              <div><dt>Saved frame 12</dt><dd>{record.savedChordMm.toFixed(1)} mm across the medial hilar recess</dd></div>
            </dl>
            <p><Link to={revisionPath}>Open exact AssetKit revision · s1233 kidney r01 →</Link></p>
            <details>
              <summary>CT sections, live frame and proposed scores</summary>
              <figure>
                <img src={planes} width="1328" height="422" loading="lazy" alt="Gold CT contours and cyan refined contours follow each other in the saved plane and both adjacent planes." />
                <figcaption>Same-case CT overlay at frame 12 and at ±1.5 mm.</figcaption>
              </figure>
              <figure>
                <img src={frame} width="1324" height="748" loading="lazy" alt="Live saved frame before and after, with 3D probe contact, grayscale B-mode and tissue overlay. Calipers span the medial hilar recess in s1233." />
                <figcaption>The worked survey uses a separate s1233 subject for this saved long-axis exemplar.</figcaption>
              </figure>
              <dl className="ga-progress-scores">
                {Object.entries(axes).map(([key, label]) => (
                  <div key={key}>
                    <dt>{label} · proposed {record.proposedScores[key]}/4</dt>
                    <dd>{record.observations[key]}</dd>
                  </div>
                ))}
              </dl>
            </details>
          </article>
        </>
      )}
    </>
  );
}
