import React from 'react';
import { Heading, Link } from './GalleryUI.jsx';
import { ultrasoundCollection, ultrasoundDevelopment } from './ultrasound-data.js';
import index from './ultrasound-progress/index.json';

const records = import.meta.glob('./ultrasound-progress/*/record.json', { eager: true, import: 'default' });
const assets = import.meta.glob('./ultrasound-progress/*/*.{mesh,webp}', {
  eager: true, import: 'default', query: '?url',
});
const cards = new Map(index.cards.map(slug => [slug, records[`./ultrasound-progress/${slug}/record.json`]]));
const assetUrl = (slug, name) => assets[`./ultrasound-progress/${slug}/${name}`];
const number = new Intl.NumberFormat('en-US');
const axes = {
  fidelity: 'Fidelity',
  form: 'Form',
  readability: 'Teaching readability',
  economy: 'Mesh economy',
};

export const hasUltrasoundProgressRevision = slug => cards.has(slug);

function CampaignProgress({ campaign }) {
  const metrics = [
    ['Governed chapters', `${number.format(campaign.governedChapters)} / ${number.format(campaign.chapters)}`],
    ['Adopted', number.format(campaign.adopted)],
    ['Reviewed', number.format(campaign.reviewed)],
    ['Qualified', number.format(campaign.qualified)],
    ['Triangles saved', number.format(campaign.trianglesSaved)],
    ['Bytes saved', number.format(campaign.bytesSaved)],
  ];
  return (
    <dl className="ga-progress-metrics ga-campaign-progress" aria-label="Campaign progress">
      {metrics.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
    </dl>
  );
}

function ProgressFigure({ slug, figure }) {
  return (
    <figure>
      <img src={assetUrl(slug, figure.file)} width={figure.width} height={figure.height} loading="lazy" alt={figure.alt} />
      <figcaption>{figure.caption}</figcaption>
    </figure>
  );
}

function ProgressCard({ slug, record }) {
  const delta = Math.round(100 * (1 - record.export.bytes / record.previous.bytes));
  const [leadFigure, ...details] = record.figures;
  const titleId = `ultrasound-progress-${slug}`;
  return (
    <article className="ga-collection-link ga-ultrasound-progress" aria-labelledby={titleId}>
      <h2 id={titleId}>{record.cardTitle}</h2>
      <p>{record.subtitle} · {record.disposition}</p>
      <ProgressFigure slug={slug} figure={leadFigure} />
      <dl className="ga-progress-metrics">
        <div><dt>Sweep mesh triangles</dt><dd>{number.format(record.previous.triangles)} → {number.format(record.export.triangles)}</dd></div>
        <div><dt>Sweep mesh bytes</dt><dd>{number.format(record.previous.bytes)} → {number.format(record.export.bytes)}{delta > 0 && ` · ${delta}% smaller`}</dd></div>
        {record.savedChord && (
          <div><dt>Saved frame {record.savedChord.frame}</dt><dd>{record.savedChord.millimetres.toFixed(1)} mm {record.savedChord.context}</dd></div>
        )}
      </dl>
      <p><Link to={`${ultrasoundDevelopment}/${slug}`}>Open exact AssetKit revision · {record.revisionLinkLabel} →</Link></p>
      <details>
        <summary>{record.detailsLabel}</summary>
        {details.map(figure => <ProgressFigure key={figure.file} slug={slug} figure={figure} />)}
        <p>{record.scope}</p>
        <dl className="ga-progress-scores">
          {Object.entries(axes).map(([key, label]) => (
            <div key={key}>
              <dt>{label}{record.scores[key] == null ? ' · Unscored' : ` · ${record.scores[key]}/4`}</dt>
              {record.observations[key] && <dd>{record.observations[key]}</dd>}
            </div>
          ))}
        </dl>
      </details>
    </article>
  );
}

function ProgressRevision({ slug, record }) {
  return (
    <>
      <Heading title={record.revisionTitle}>{record.disposition}</Heading>
      <section className="ga-collection-link">
        <p><code>{record.ref}</code></p>
        <dl>
          <dt>Coordinate frame</dt><dd>{record.coordinateFrame}</dd>
          <dt>Export</dt><dd>{number.format(record.export.triangles)} triangles · {number.format(record.export.bytes)} bytes</dd>
          <dt>SHA-256</dt><dd><code className="ga-progress-hash">{record.export.sha256}</code></dd>
        </dl>
        <div className="ga-related">
          <a href={assetUrl(slug, record.mesh)} download={`${slug}.mesh`}>Download the exact packed mesh</a>
          <a href={record.sourceUrl}>{record.sourceLabel}</a>
        </div>
      </section>
    </>
  );
}

export function UltrasoundDevelopment({ revision }) {
  return (
    <>
      <Link to={revision ? ultrasoundDevelopment : ultrasoundCollection}>
        {revision ? '← Ultrasound Development' : '← Ultrasound Anatomy'}
      </Link>
      {revision ? (
        <ProgressRevision slug={revision} record={cards.get(revision)} />
      ) : (
        <>
          <Heading title="Ultrasound Development" />
          <CampaignProgress campaign={index.campaign} />
          {[...cards].map(([slug, record]) => <ProgressCard key={slug} slug={slug} record={record} />)}
        </>
      )}
    </>
  );
}
