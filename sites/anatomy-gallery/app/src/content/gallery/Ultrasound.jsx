import React, { useState } from 'react';
import { assetsByPath } from '../shared/asset-index.mjs';
import localDelivery from '../assets/local-delivery.json';
import pose from './teaching-inputs/ultrasound-abdomen.json';
import locator from './teaching-inputs/ultrasound-body-locator.svg';
import { assetUrl, byPath } from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { Heading, Link, Missing } from './GalleryUI.jsx';
import {
  abdomenTour, abdomenPartPath, abdomenParts, abdomenStopPath,
  otherTopics, ultrasoundAssets, ultrasoundCollection, ultrasoundDevelopment,
} from './ultrasound-data.js';

const local = assetsByPath(localDelivery);
const delivery = (path) => byPath.get(path) ?? local.get(path);
const defaultStop = abdomenTour.stops[0];

function BodyLocator() {
  const [missing, setMissing] = useState(false);
  return (
    <figure className="ga-ultrasound-locator">
      <figcaption>Probe location</figcaption>
      <div className="ga-ultrasound-body">
        {missing ? <p role="status">Body locator unavailable. The marker represents the right upper abdomen.</p> : (
          <div className="ga-ultrasound-body-image">
            <img src={locator} width="405" height="955" alt="Anterior body locator"
              onError={() => setMissing(true)} />
            <span className="ga-ultrasound-probe" role="img" aria-label="Probe marker in the right upper abdomen"
              style={{ left: pose.locator.xPercent + '%', top: pose.locator.yPercent + '%' }} />
          </div>
        )}
      </div>
      <p>Right upper abdomen · schematic body atlas</p>
    </figure>
  );
}

function ScanPanel({ view, section, answer, onAnswer }) {
  const [imageState, setImageState] = useState('loading');
  const asset = delivery(view.path);
  const unavailable = !asset || imageState === 'missing';
  return (
    <figure className="ga-ultrasound-monitor">
      <figcaption>
        {view.title} <span>· Patient right at image left · {pose.depthMm / 10} cm field</span>
      </figcaption>
      <div className="ga-ultrasound-image" style={{ aspectRatio: pose.display.width + ' / ' + pose.display.height }}>
        {unavailable ? <p role="status">{view.title} unavailable. Switch views or inspect the asset review.</p> : (
          <>
            <img src={assetUrl(asset)} width={pose.display.width} height={pose.display.height} alt={view.alt}
              onLoad={() => setImageState('ready')} onError={() => setImageState('missing')} />
            {imageState === 'ready' && pose.targets.map((target) => (
              <button key={target.label} type="button" className="ga-ultrasound-target"
                style={{ left: target.xPercent + '%', top: target.yPercent + '%' }}
                aria-label={'Select marker ' + target.label} aria-pressed={answer?.label === target.label}
                onClick={() => onAnswer(target)}>{target.label}</button>
            ))}
          </>
        )}
      </div>
      {section && <p className="ga-ultrasound-legend">Green · gallbladder <span>Coral · liver</span></p>}
    </figure>
  );
}

export function UltrasoundCollection() {
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title="Ultrasound Anatomy">
        Connect the probe position to the anatomy in a synthetic ultrasound view.
      </Heading>
      <section className="ga-collection-link">
        <h2>Abdomen</h2>
        <p>Find the gallbladder along the liver edge in the first tour.</p>
        <div className="ga-related">
          <Link to={abdomenStopPath(defaultStop)}>Open Abdomen tour →</Link>
          <Link to={ultrasoundAssets}>Inspect tour assets →</Link>
          <Link to={ultrasoundDevelopment}>Development →</Link>
        </div>
      </section>
      <section className="ga-collection-link" aria-label="Planned tours">
        <h2>Planned tours</h2>
        <ul>{otherTopics.map(([topic, task]) => <li key={topic}><strong>{topic}</strong> · {task}</li>)}</ul>
      </section>
    </>
  );
}

export function UltrasoundTour({ stopId }) {
  const stop = stopId ? abdomenTour.stops.find(({ id }) => id === stopId) : defaultStop;
  return stop ? <AbdomenStop key={stop.id} stop={stop} /> : <Missing />;
}

function AbdomenStop({ stop }) {
  const [section, setSection] = useState(false);
  const [answer, setAnswer] = useState(null);
  const view = section ? stop.section : stop.grayscale;
  return (
    <>
      <Link to={ultrasoundCollection}>← Ultrasound Anatomy</Link>
      <Heading title={stop.title}>
        Abdomen ultrasound · Use the liver as your landmark. Which marker sits inside the gallbladder?
      </Heading>
      <div className="ga-ultrasound-controls">
        <button type="button" aria-pressed={section} onClick={() => setSection((value) => !value)}>
          Matching anatomical section
        </button>
        <Link to={abdomenPartPath(stop.part, stop)}>Inspect assets used at this stop →</Link>
      </div>
      <div className="ga-ultrasound-board">
        <BodyLocator />
        <ScanPanel key={view.path} view={view} section={section} answer={answer} onAnswer={setAnswer} />
      </div>
      <p className="ga-ultrasound-answer" role="status">
        {answer && (answer.part === stop.part
          ? 'Correct. The gallbladder is the dark elongated structure along the liver edge.'
          : 'That marker is in the liver. Look for the dark structure against its edge.')}
      </p>
      <p className="ga-ultrasound-note">
        Fixed teaching view from two s1233 anatomy labels. Brightness, texture and the outer tissue field are illustrative.
      </p>
    </>
  );
}

export function UltrasoundAssetReview({ partId, query }) {
  const part = partId ? abdomenParts.find(({ id }) => id === partId) : abdomenParts[0];
  if (!part) return <Missing />;
  const from = new URLSearchParams(query).get('from');
  const stop = abdomenTour.stops.find(({ id }) => id === from) ?? defaultStop;
  return (
    <>
      <Link to={abdomenStopPath(stop)}>← Return to gallbladder stop</Link>
      <Heading title="Ultrasound asset review">
        Abdomen · {stop.title}
      </Heading>
      <nav className="ga-tabs" aria-label="Abdomen tour assets">
        {abdomenParts.map((item) => (
          <Link key={item.id} to={abdomenPartPath(item.id, stop)} aria-current={item === part ? 'page' : undefined}>
            {item.title}
          </Link>
        ))}
      </nav>
      <section className="ga-ultrasound-review">
        <h2>{part.title}</h2>
        <p>{part.role}</p>
        <p><strong>What to review.</strong> {part.finding}</p>
        {part.locator && <div className="ga-ultrasound-evidence-locator"><BodyLocator /></div>}
        {part.views && <div className="ga-pair">
          {part.views.map((view) => (
            <Evidence key={view.path} witness={{ ...view, asset: delivery(view.path), sourceUrl: part.source }} />
          ))}
        </div>}
        {part.geometry && (
          <dl className="ga-ultrasound-geometry">
            <dt>Source and plane</dt><dd>{pose.case} · axial slice {pose.sliceIndex} · anterior to posterior</dd>
            <dt>Authored probe contact</dt><dd>RAS ({pose.contactRasMm.join(', ')}) mm</dd>
            <dt>Field</dt><dd>{pose.depthMm} mm depth · {pose.halfAngleDegrees * 2}° · {pose.display.mmPerPixel} mm/px</dd>
          </dl>
        )}
        <div className="ga-related">
          <a href={part.source}>{part.sourceLabel} ↗</a>
          {part.library && <Link to={part.library}>Open related Library revision →</Link>}
        </div>
      </section>
    </>
  );
}
