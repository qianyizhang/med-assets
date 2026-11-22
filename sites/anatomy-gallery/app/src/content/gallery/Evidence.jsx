import React, { useState } from 'react';
import { assetUrl } from './catalog.js';

export function Evidence({ witness }) {
  const [format, setFormat] = useState((witness.asset || witness.displayUrl) ? 'display' : 'original');
  const sourceUrl = witness.sourceUrl ?? witness.original?.source;
  const file = format === 'display' ? witness.asset : format === 'original' ? witness.original : null;
  const url = (format === 'display' && witness.displayUrl) || (file && assetUrl(file));
  return (
    <figure lang={witness.lang}>
      {!url ? (
        <p className="ga-missing-evidence" role="status">
          {witness.lang === 'zh' ? '图像无法显示。' : witness.title + ' unavailable.'}
          {sourceUrl && (
            <> <a href={sourceUrl}>{witness.lang === 'zh' ? '在来源档案中打开原图' : 'Open the original in the source repository'}</a></>
          )}
        </p>
      ) : (
        <a href={witness.fullUrl ?? url} aria-label={(witness.lang === 'zh' ? '打开完整图像 · ' : 'Open full evidence image · ') + witness.title}>
          <img
            src={url}
            alt={witness.alt}
            width={witness.width}
            height={witness.height}
            onError={() => setFormat(format === 'display' && witness.original ? 'original' : 'unavailable')}
          />
        </a>
      )}
      <figcaption>
        {witness.title}{witness.caption && ' · ' + witness.caption}
        {witness.retainOriginal && witness.original && format === 'display' && (
          <> · <a href={assetUrl(witness.original)}>Original image</a></>
        )}
      </figcaption>
    </figure>
  );
}
