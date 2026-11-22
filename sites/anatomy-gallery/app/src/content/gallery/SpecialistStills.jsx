import React from 'react';
import { byPath, dentalLayerSheet, heartSlice, oneBreathStoryboard } from './catalog.js';
import { Evidence } from './Evidence.jsx';
import { Heading, Link } from './GalleryUI.jsx';
import controlSheet from './teaching-inputs/control-review-sheet.jpg';
import sourcePose from './teaching-inputs/source-pose.jpg';
import editorialReveal from './teaching-inputs/editorial-reveal.jpg';
import cariesPoster from './teaching-inputs/caries-poster.svg';
import periodontalPoster from './teaching-inputs/periodontal-poster.svg';

export const heartSlicePath = 'use-cases/' + heartSlice.id;
export const oneBreathPath = 'use-cases/' + oneBreathStoryboard.id;
export const dentalLayersPath = 'use-cases/' + dentalLayerSheet.id;
export const dentalShotsPath = 'archive/dental-shot-studies';

const source = 'https://github.com/qianyizhang/med-assets/blob/9d70d2646ec2642f0312ab7ca6d17dc9e7dbd4ef/';
const heart = 'heart/synthetic-imaging/beating-heart/imaging/';
const breath = 'lessons/one-breath/';
const controls = 'lessons/dental-layer-controls/';
const shots = 'lessons/dental-animation/';

function Plate({ path, displayUrl, title, alt, width, height }) {
  const sourceUrl = source + path;
  return <Evidence witness={{ title, alt, width, height, displayUrl, sourceUrl,
    original: byPath.get(path), fullUrl: displayUrl ? sourceUrl : undefined }} />;
}

export function HeartSlice() {
  return (
    <>
      <Link to="use-cases/systems/cardiovascular">← Cardiovascular</Link>
      <Heading title={heartSlice.title}>Synthetic imaging · Reference frame 1</Heading>
      <p>Locate the left and right ventricles in the color guide, then find the same two chambers and their walls in each grayscale view.</p>
      <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
        <Plate path={heart + 'start_here_same_slice.png'} title="One plane through an idealized heart"
          alt="The same two ventricular chambers shown in CT-like grayscale, labeled color and MRI-like grayscale"
          width={2100} height={840} />
      </div>
      <p>The three slice displays share the idealized heart geometry at frame 1. Intensities are arbitrary teaching presets. The plate contains no patient scan or phase-varying cine data.</p>
      <a href={source + heart + 'README.md'}>Imaging package and other planes ↗</a>
    </>
  );
}

export function OneBreath() {
  return (
    <>
      <Link to="use-cases/systems/respiratory">← Respiratory</Link>
      <Heading title={<>{oneBreathStoryboard.title} · <span lang="zh">一次呼吸</span></>}>Mechanics → airway route → gas exchange</Heading>
      <p lang="zh">呼吸力学 → 气道路径 → 气体交换</p>
      <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
        <Plate path={breath + 'review/offline-storyboard.png'} title="Original bilingual offline storyboard"
          alt="Three panels show the diaphragm and lungs, the trachea dividing into the two main bronchi, and gas exchange in a separate schematic"
          width={1800} height={930} />
      </div>
      <ol>
        <li>Diaphragm down → lungs expand · <span lang="zh">膈肌下降 → 肺随之扩张</span></li>
        <li>Trachea → left and right main bronchi · <span lang="zh">气管 → 左右主支气管</span></li>
        <li>O₂: air → blood · CO₂: blood → air · <span lang="zh">氧气进入血液 · 二氧化碳进入肺泡</span></li>
      </ol>
      <p>The airway cutaway omits smaller branches. The exchange panel is a separate schematic drawn at a different scale. The storyboard supplies no measured physiology or clinical validation.</p>
      <p lang="zh">气道剖切图省略细小分支。气体交换图为独立示意图，非等比例。非定量生理模拟，不代表临床认可。</p>
      <a href={source + breath + 'README.md'}>Original lesson and replay ↗</a>
    </>
  );
}

export function DentalLayers() {
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title={dentalLayerSheet.title}>FDI 31 · Dental layer controls</Heading>
      <p>Compare the source pose with enamel, dentin and bone isolated in a fixed view.</p>
      <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
        <Plate path={controls + 'media/control-review-sheet.jpg'} displayUrl={controlSheet}
          title="Original control review sheet"
          alt="Four panels show the prepared FDI 31 specimen in source pose, then with only enamel, only dentin and only bone visible"
          width={1000} height={650} />
      </div>
      <p>Enamel, dentin, pulp and bone are source labels on the SWIRendo prepared T2 specimen. The colors and offsets are editorial. Buccolingual orientation remains unresolved.</p>
      <div className="ga-related">
        <a href={source + controls + 'README.md'}>Original controls, credits and replay ↗</a>
        <Link to="library/swirendo_fdi31">Find the Balanced specimen download →</Link>
        <Link to={dentalShotsPath}>Compare the authored shot studies →</Link>
      </div>
    </>
  );
}

export function DentalShotStudies() {
  return (
    <>
      <Link to="archive">← Experiments &amp; Archive</Link>
      <Heading title="Dental shot studies">Original specimen stills and schematic posters from three authored prototypes.</Heading>
      <section>
        <h2>One specimen, four source-labelled layers</h2>
        <div className="ga-pair ga-source-evidence">
          <Plate path={shots + 'fdi31-layer-reveal/source-pose.jpg'} displayUrl={sourcePose}
            title="Source pose" alt="Prepared FDI 31 incisor with its labelled layers in source position"
            width={960} height={540} />
          <Plate path={shots + 'fdi31-layer-reveal/editorial-reveal.jpg'} displayUrl={editorialReveal}
            title="Editorial reveal" alt="The specimen's enamel and bone displaced to expose the interior layers"
            width={960} height={540} />
        </div>
        <p>The two states show editorial transforms and illustrative colors on the prepared SWIRendo specimen. They preserve the source geometry. Buccolingual orientation remains unresolved.</p>
        <div className="ga-related">
          <a href={source + shots + 'fdi31-layer-reveal/README.md'}>Original shot and geometry check ↗</a>
          <Link to={dentalLayersPath}>See the separate layer controls review →</Link>
        </div>
      </section>
      <section>
        <h2>A cavity changes tooth structure</h2>
        <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
          <Plate path={shots + 'caries-restoration/poster.svg'} displayUrl={cariesPoster}
            title="Original caries storyboard poster"
            alt="Authored molar cross-section with a brown lesion at the chewing surface"
            width={960} height={540} />
        </div>
        <p>The opening poster shows localized decay. The source storyboard uses later shots for assessment, preparation and restoration. Its tooth geometry and preparation design remain clinically unvalidated.</p>
        <div className="ga-related">
          <a href={source + shots + 'caries-restoration/README.md'}>Original storyboard and scope ↗</a>
          <Link to="archive/dental-image26/02-cavity-filling">Related Image 2.6 cavity filling film →</Link>
        </div>
      </section>
      <section>
        <h2>Why professional cleaning reaches deeper</h2>
        <div className="ga-pair ga-source-evidence ga-source-evidence-stacked">
          <Plate path={shots + 'periodontal-cleaning/poster.svg'} displayUrl={periodontalPoster}
            title="Original periodontal cleaning poster"
            alt="Authored cross-section showing a conceptual gum pocket and deposits alongside the tooth root"
            width={960} height={540} />
        </div>
        <p>The poster shows the conceptual pocket and deposits. The source shot plan uses a marker to illustrate a cleaning region along the root. Instrument technique remains outside the study.</p>
        <div className="ga-related">
          <a href={source + shots + 'periodontal-cleaning/README.md'}>Original shot and scope ↗</a>
          <Link to="archive/dental-image26/04-gum-disease">Related Image 2.6 gum disease film →</Link>
        </div>
      </section>
    </>
  );
}
