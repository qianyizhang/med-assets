import React from 'react';
import { assetUrl, byPath, salivary } from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { Heading, Link, Missing } from './GalleryUI.jsx';
import ovaryLesson from './teaching-inputs/ovary-tubal-context/lesson.json';
import ovaryCloseups from './teaching-inputs/ovary-tubal-context/ovary-teaching.webp';
import {
  oralFolder, oralSpaces, oralSpacesPath, ovaryLocator, regionalLessons, regionalPath, teachingDisplayPath,
} from './teaching-data.js';

const source = 'https://github.com/qianyizhang/med-assets/blob/e63006dca598031d58bdf66485fed24a24194558/';
const systems = {
  cardiovascular: 'Cardiovascular',
  nervous: 'Nervous and senses',
  reproductive: 'Reproductive',
};
const systemPath = (system) => 'use-cases/systems/' + system;

function TeachingPlate({ plate }) {
  const asset = byPath.get(teachingDisplayPath(plate.original));
  return (
    <Evidence witness={{
      ...plate,
      asset,
      original: byPath.get(plate.original),
      width: asset?.width,
      height: asset?.height,
      sourceUrl: source + plate.original,
    }} />
  );
}

export function OralSpacesLesson({ lang = 'en', query }) {
  if (!Object.hasOwn(oralSpaces, lang)) return <Missing />;
  const lesson = oralSpaces[lang];
  const fromDuct = new URLSearchParams(query).get('from') === 'duct-course';
  const origin = fromDuct ? '?from=duct-course' : '';
  const headNeck = salivary.lesson + (fromDuct ? '/duct-course' : '/location') + (lang === 'zh' ? '?oral=zh' : '');
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <div lang={lang}>
        <Heading title={lesson.question}>{lesson.cue}</Heading>
        <nav className="ga-tabs" aria-label={lang === 'zh' ? '示意图语言' : 'Cutaway language'}>
          <Link to={oralSpacesPath + '/en' + origin} lang="en" aria-current={lang === 'en' ? 'page' : undefined}>English</Link>
          <Link to={oralSpacesPath + '/zh' + origin} lang="zh" aria-current={lang === 'zh' ? 'page' : undefined}>中文</Link>
        </nav>
        <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
          <TeachingPlate key={lang} plate={{ ...lesson, lang, original: oralFolder + 'oral-spaces-' + lang + '.png' }} />
        </div>
        <h2>{lang === 'zh' ? '比例与适用范围' : 'Scale and limits'}</h2>
        <p>{lesson.limit}</p>
        <p>{lesson.review}</p>
        <div className="ga-related">
          <a href={source + oralFolder + 'oral-spaces-' + lang + '.svg'}>{lang === 'zh' ? 'r01 矢量原图' : 'Original r01 vector'}</a>
          <a href={source + oralFolder + 'README.md'}>{lang === 'zh' ? '图包与来源' : 'Diagram package and provenance'}</a>
          <a href={source + 'reviews/oral_spaces/2026-10-26-r01/INDEPENDENT-REVIEW.md'}>{lang === 'zh' ? '独立二维评审与三维结论' : 'Independent 2D review and 3D findings'}</a>
        </div>
      </div>
      <div className="ga-related">
        <Link to={headNeck} lang={lang}>
          {fromDuct
            ? (lang === 'zh' ? '返回腮腺管走行 →' : 'Return to the parotid duct course →')
            : (lang === 'zh' ? '查看头颈部主要唾液腺的位置 →' : 'Find the major salivary glands in Head & Neck →')}
        </Link>
      </div>
    </>
  );
}

export function RegionalLinks({ system, ovaryHref }) {
  return regionalLessons.filter((lesson) => lesson.system === system).map((lesson) => (
    <Link to={(lesson === ovaryLocator && ovaryHref) || regionalPath + '/' + lesson.id} key={lesson.id}>
      {lesson.name} →
    </Link>
  ));
}

function BilingualText({ en, zh }) {
  return <><p>{en}</p><p lang="zh">{zh}</p></>;
}

export function OvaryTubalLesson({ children }) {
  const { question, questionZh, orientation, localization, source: native } = ovaryLesson;
  const pelvicPlate = byPath.get(orientation.plate.path);
  const nativeModel = byPath.get(native.model);
  return (
    <>
      <Heading title={question}><span lang="zh">{questionZh}</span></Heading>
      {children}
      <section className="ga-ovary-orientation" aria-labelledby="ovary-pelvis-heading">
        <h2 id="ovary-pelvis-heading">
          {orientation.heading} · <span lang="zh">{orientation.headingZh}</span>
        </h2>
        <BilingualText en={orientation.cue} zh={orientation.cueZh} />
        <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
          <Evidence witness={{
            ...orientation.plate,
            asset: pelvicPlate,
            caption: <span lang="zh">{orientation.plate.titleZh}</span>,
            sourceUrl: 'https://github.com/qianyizhang/med-assets/blob/' +
              orientation.plate.sourceRevision + '/' + orientation.plate.path,
          }} />
        </div>
      </section>
      <section className="ga-ovary-localization" aria-labelledby="ovary-gap-heading">
        <h2 id="ovary-gap-heading">
          {localization.heading} · <span lang="zh">{localization.headingZh}</span>
        </h2>
        <BilingualText en={localization.transition} zh={localization.transitionZh} />
        <BilingualText en={localization.cue} zh={localization.cueZh} />
        <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
          <Evidence witness={{
            ...localization.plate,
            displayUrl: ovaryCloseups,
            caption: <span lang="zh">{localization.plate.titleZh}</span>,
          }} />
        </div>
        <BilingualText en={localization.limit} zh={localization.limitZh} />
      </section>
      <details>
        <summary>{native.heading} · <span lang="zh">{native.headingZh}</span></summary>
        <BilingualText en={native.cue} zh={native.cueZh} />
        <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
          <TeachingPlate plate={{
            ...native.plate,
            loading: 'lazy',
            caption: <span lang="zh">{native.plate.titleZh}</span>,
          }} />
        </div>
        <BilingualText en={native.credit} zh={native.creditZh} />
        <div className="ga-related">
          {nativeModel && (
            <a href={assetUrl(nativeModel)}>Exact HRA r01 GLB · <span lang="zh">HRA r01 源模型</span></a>
          )}
          <a href={source + native.attribution}>Source credits and license · <span lang="zh">来源署名与许可</span></a>
        </div>
      </details>
    </>
  );
}

export function RegionalLocators({ stop }) {
  if (!stop) return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title="Regional locators">
        Use an overview to find a landmark, then follow it into the detail. Each lesson identifies its source and scale.
      </Heading>
      {Object.entries(systems).map(([system, name]) => (
        <section className="ga-collection-link" key={system}>
          <h2>{name}</h2>
          <div className="ga-related"><RegionalLinks system={system} /></div>
        </section>
      ))}
    </>
  );
  const lesson = regionalLessons.find(({ id }) => id === stop);
  if (!lesson) return <Missing />;
  if (lesson === ovaryLocator) return (
    <>
      <Link to={regionalPath}>← Regional locators</Link>
      <OvaryTubalLesson />
      <div className="ga-related">
        <Link to={systemPath(lesson.system)}>See the reproductive assembly in Body Systems →</Link>
      </div>
    </>
  );
  const model = byPath.get(lesson.model);
  return (
    <>
      <Link to={regionalPath}>← Regional locators</Link>
      <Heading title={lesson.question}>
        {lesson.name} · <span lang="zh">{lesson.zh}</span>
      </Heading>
      <p>{lesson.cue}</p>
      <p lang="zh">{lesson.cueZh}</p>
      <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
        {lesson.plates.map((plate) => <TeachingPlate key={plate.original} plate={plate} />)}
      </div>
      <h2>Scale and limits</h2>
      <p>{lesson.scale}</p>
      <p>{lesson.limit}</p>
      <h2>Source and attribution</h2>
      <p>{lesson.credit}</p>
      <div className="ga-related">
        {model
          ? <a href={assetUrl(model)}>Exact source GLB · {model.name}</a>
          : <span>Source GLB unavailable.</span>}
        <a href={source + lesson.package}>Teaching package and original plates ↗</a>
        <a href={source + lesson.review}>Review and source identity ↗</a>
      </div>
      <div className="ga-related">
        <Link to={systemPath(lesson.system)}>See the {systems[lesson.system].toLowerCase()} assembly in Body Systems →</Link>
      </div>
    </>
  );
}
