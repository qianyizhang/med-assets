import React from 'react';
import systems from './body-systems.json';
import { assetUrl, byPath, lessonPath, sourceRoot } from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { LessonReviewPlate } from './LessonReviewPlate.jsx';
import { Heading, Link, Missing } from './GalleryUI.jsx';
import { PathwayLinks } from './Pathways.jsx';
import { RegionalLinks } from './Teaching.jsx';
import { SkeletalLessonLink } from './SkeletalLesson.jsx';
import { heartSlicePath, oneBreathPath } from './SpecialistStills.jsx';

const root = 'use-cases/systems';
const frameUrl = (frame) => assetUrl(byPath.get(frame.path));
const anatomy = {
  skeletal: 'Musculoskeletal',
  muscular: 'Musculoskeletal',
  nervous: 'Nervous & senses',
  integumentary: 'Body & support',
  lymphatic: 'Lymphatic & tissue',
};

function Plate({ plate }) {
  return (
    <section className="ga-system-plate">
      <h3>{plate.title}</h3>
      <div className="ga-pair">
        {plate.frames.map((frame) => (
          <Evidence key={frame.path} witness={{
            asset: byPath.get(frame.path),
            title: frame.angle,
            alt: plate.title + ' · ' + frame.angle,
          }} />
        ))}
      </div>
      {plate.scale && <p>{plate.scale}</p>}
      <ul className="ga-legend" aria-label="Parts and display colors">
        {plate.legend.map(([name, color]) => (
          <li key={name}>
            <i style={{ background: color }} />
            {name}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function Systems({ id, query }) {
  if (!id)
    return (
      <>
        <Link to="use-cases">← Use Cases</Link>
        <Heading title="Body Systems">
          Explore the assembly, then inspect the structures that explain its function.
        </Heading>
        <div className="ga-systems">
          {systems.map((s) => (
            <Link className="ga-system-card" key={s.id} to={root + '/' + s.id}>
              <img src={frameUrl(s.plates[0].frames[0])} alt="" loading="lazy" />
              <div>
                <span className="ga-classification">{s.status}</span>
                <h2>{s.name}</h2>
                <p>{s.function}</p>
              </div>
            </Link>
          ))}
        </div>
      </>
    );
  const system = systems.find((s) => s.id === id);
  if (!system) return <Missing />;
  const address = root + '/' + id;
  const details = system.plates.filter((p) => p.kind === 'detail');
  const selected = new URLSearchParams(query).get('detail');
  const plate = selected && details.find((p) => p.id === selected);
  if (selected && !plate) return <Missing />;
  return (
    <>
      <Link to={root}>← Body Systems</Link>
      <Heading title={system.name}>{system.function}</Heading>
      <nav className="ga-tabs" aria-label="Teaching scale">
        <Link to={address} aria-current={!plate ? 'page' : undefined}>
          System assembly
        </Link>
        <Link to={address + '?detail=' + details[0].id} aria-current={plate ? 'page' : undefined}>
          Asset detail ({details.length})
        </Link>
      </nav>
      <p>{plate ? system.detail : system.overview}</p>
      {plate ? (
        <>
          <label>
            Detail view{' '}
            <select
              aria-label="Detail view"
              value={selected}
              onChange={(e) => {
                location.hash = '/' + address + '?detail=' + e.target.value;
              }}
            >
              {details.map((p) => (
                <option key={p.title} value={p.id}>
                  {p.title}
                </option>
              ))}
            </select>
          </label>
          <Plate plate={plate} />
          {selected === 'lymphatic-node-transit' && (
            <LessonReviewPlate
              exportPath="models/lymph_node/exports/hra-v1.2/NIH_M_Lymph_Node.glb"
              title="Look inside the source lymph node"
              alt="The same node with its outer capsule visible at left and hidden at right, where leaders identify the medulla, follicles and paracortex"
              width={1322}
              height={786}
            >
              <p>This separate HRA view shows tissue layers. The enlarged route above shows the lesson’s authored passage.</p>
            </LessonReviewPlate>
          )}
        </>
      ) : (
        system.plates.filter((p) => p.kind === 'assembly').map((p) => <Plate key={p.title} plate={p} />)
      )}
      <h2>Scope and limits</h2>
      <p>{system.limit}</p>
      <div className="ga-related">
        <PathwayLinks system={id} detail={selected} />
        {id === 'integumentary' && (
          <Link to="library/seated-nail-r02">Inspect the reviewed nail revision →</Link>
        )}
        {id === 'respiratory' && (
          <>
            <Link to={oneBreathPath}>One Breath storyboard · <span lang="zh">一次呼吸</span> →</Link>
            <Link to="use-cases/airway">Explore Airway Review →</Link>
            <Link to="library/terminal-airspaces-r02">Inspect the reviewed airspace revision →</Link>
          </>
        )}
        {id === 'cardiovascular' && <Link to={heartSlicePath}>Read the same heart slice three ways →</Link>}
        {id === 'endocrine' && <Link to={lessonPath + '/region'}>Locate the adrenal glands →</Link>}
        <RegionalLinks system={id} />
        {id === 'skeletal' && <SkeletalLessonLink detail={selected} />}
        <Link to={'library?system=' + encodeURIComponent(anatomy[id] || system.name)}>
          Browse related assets →
        </Link>
      </div>
      <details>
        <summary>Sources and attribution</summary>
        <ul>
          {system.sources.map(([title, path, pinnedPath = path]) => (
            <li key={path}>
              <a href={sourceRoot + pinnedPath}>{title}</a>
            </li>
          ))}
        </ul>
      </details>
    </>
  );
}
