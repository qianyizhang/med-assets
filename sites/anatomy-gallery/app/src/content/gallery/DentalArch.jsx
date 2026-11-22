import React, { useCallback } from 'react';
import html from './teaching-inputs/arch-identification/index.html?raw';
import css from './teaching-inputs/arch-identification/style.css.txt?raw';
import coverage from './teaching-inputs/arch-identification/set-coverage.json';
import { COPY, MEDIA } from './teaching-inputs/arch-identification/plate.mjs';
import { mount } from './teaching-inputs/arch-identification/ui.mjs';
import { assetUrl, byPath } from './catalog.js';
import { Link } from './GalleryUI.jsx';
import { RetainedLesson } from './RetainedLesson.jsx';

const sourceMedia = MEDIA.replace('../../', '');

function connect(root, arch) {
  try {
    return mount(root, coverage, {
      imageSources: (arch) => [
        sourceMedia.replace('/media/', '/display/') + arch + '-occlusal-teeth.webp',
        sourceMedia + arch + '-occlusal-teeth.png',
      ].map((path) => byPath.get(path)).filter(Boolean).map(assetUrl),
      standalone: false,
      initialArch: arch,
    }).destroy;
  } catch {
    root.querySelector('#boot').textContent = COPY.en.dataError + ' / ' + COPY.zh.dataError;
  }
}

export function DentalArch({ arch }) {
  const mountLesson = useCallback((root) => connect(root, arch), [arch]);
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <RetainedLesson name="arch-identification" html={html} css={css} connect={mountLesson} />
    </>
  );
}
