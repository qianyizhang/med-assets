import React, { useCallback } from 'react';
import html from './teaching-inputs/kidney-location/index.html?raw';
import css from './teaching-inputs/kidney-location/style.css.txt?raw';
import { source } from './teaching-inputs/kidney-location/source.js';
import { mount } from './teaching-inputs/kidney-location/view.js';
import { assetUrl, byPath } from './catalog.js';
import { Link } from './GalleryUI.jsx';
import { RetainedLesson } from './RetainedLesson.jsx';

const sourceLink = 'https://github.com/qianyizhang/med-assets/blob/9d70d26/lessons/kidney-location/README.md';
const asset = byPath.get(source.url.replace('../../', ''));
const imageUrl = asset && asset.sha256 === source.sha256 ? assetUrl(asset) : null;

export function KidneyTrial({ query }) {
  const connect = useCallback((root) => {
    if (imageUrl) root.querySelector('[data-copy="original"]').href = imageUrl;
    return mount(root, { params: new URLSearchParams(query), imageUrl, standalone: false });
  }, [query]);
  return (
    <>
      <Link to="archive">← Experiments &amp; Archive</Link>
      <RetainedLesson name="kidney-location" html={html} css={css} connect={connect} />
      <div className="ga-related">
        <a href={sourceLink}>Trial record, source checks and limits ↗</a>
        <Link to="use-cases/systems/urinary">Urinary Body Systems →</Link>
      </div>
    </>
  );
}
