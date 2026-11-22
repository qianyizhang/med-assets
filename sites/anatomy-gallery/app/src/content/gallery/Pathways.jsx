import React, { useState } from 'react';
import systems from './body-systems.json';
import testisEn from './teaching-inputs/testis-pathway-en.svg?raw';
import testisZh from './teaching-inputs/testis-pathway-zh.svg?raw';
import { byPath } from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { Heading, Link, Missing } from './GalleryUI.jsx';
import { teachingDisplayPath } from './teaching-data.js';
import { pathways, pathwayPath } from './pathway-data.js';
import { LymphPlate, LymphSources } from './LymphPlate.jsx';

const source = 'https://github.com/qianyizhang/med-assets/blob/9d70d26/';
const testisVectors = { en: testisEn, zh: testisZh };

export function PathwayLinks({ system, detail }) {
  return Object.entries(pathways)
    .filter(([, lesson]) => !system || lesson.system === system)
    .map(([id, lesson]) => (
      <Link key={id} to={pathwayPath(id) + (detail ? '?from=' + detail : '')}>
        {lesson.en.title} · <span lang="zh">{lesson.zh.title}</span> →
      </Link>
    ));
}

export function PathwayLesson({ id, lang = 'en', query }) {
  const [showDirection, setShowDirection] = useState(false);
  if (!['en', 'zh'].includes(lang)) return <Missing />;
  const lesson = pathways[id];
  const copy = lesson[lang];
  const zh = lang === 'zh';
  const from = new URLSearchParams(query).get('from');
  const assembly = systems.find((system) => system.id === lesson.system);
  const detail = assembly.plates.some((plate) => plate.kind === 'detail' && plate.id === from)
    ? from : '';
  const base = lesson.folder + '/' + lesson.file + '-' + lang;
  const lymph = id === 'lymph-collecting-routes';
  const vector = source + base + '.svg';
  const inline = id === 'testis-pathway' ? 'data:image/svg+xml,' + encodeURIComponent(testisVectors[lang]) : undefined;
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <div lang={lang}>
        <Heading title={copy.title}>{copy.cue}</Heading>
        <nav className="ga-tabs" aria-label={zh ? '示意图语言' : 'Diagram language'}>
          {Object.entries({ en: 'English', zh: '中文' }).map(([code, label]) => (
            <Link key={code} lang={code} aria-current={code === lang ? 'page' : undefined}
              to={pathwayPath(id, code) + (detail ? '?from=' + detail : '')}>{label}</Link>
          ))}
        </nav>
        {lymph ? (
          <LymphPlate key={lang} lang={lang} file={byPath.get(base + '.png')} alt={copy.alt}
            showDirection={showDirection} setShowDirection={setShowDirection} />
        ) : <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
          <Evidence key={id + '-' + lang} witness={{
            lang, title: copy.title, alt: copy.alt, width: 1400, height: 1060,
            asset: byPath.get(teachingDisplayPath(base + '.png')),
            original: byPath.get(base + '.png'), displayUrl: inline,
            fullUrl: inline ? vector : undefined, sourceUrl: vector,
          }} />
        </div>}
        <h2>{zh ? '比例与适用范围' : 'Scale and limits'}</h2>
        <p>{copy.limits}</p>
        <h2>{zh ? '来源与署名' : 'Source and attribution'}</h2>
        <p>{copy.credit}</p>
        {lymph ? <LymphSources lang={lang} folder={lesson.folder} /> : <div className="ga-related">
          <a href={vector}>{zh ? '矢量原图' : 'Original vector'}</a>
          <a href={source + lesson.folder + '/README.md'}>{zh ? '图包、来源和参考' : 'Diagram package and references'}</a>
          <a href={source + lesson.review}>{zh ? '图像审阅' : 'Diagram review'}</a>
        </div>}
        <div className="ga-related">
          <Link to={'use-cases/systems/' + lesson.system + (detail ? '?detail=' + detail : '')}>
            {zh ? '返回人体系统 · ' : 'Return to Body Systems · '}{lesson.systemName[lang]} →
          </Link>
        </div>
      </div>
    </>
  );
}
