import React, { useState } from 'react';
import { assetUrl } from './catalog.js';

export function Evidence({ witness }) {
  const [format, setFormat] = useState((witness.asset || witness.displayUrl) ? 'display' : 'original');
  const sourceUrl = witness.sourceUrl ?? witness.original?.source;
  const file = format === 'display' ? witness.asset : format === 'original' ? witness.original : null;
  const url = (format === 'display' && witness.displayUrl) || (file && assetUrl(file));
  const fullUrl = witness.fullUrl ?? (url?.startsWith('data:') ? undefined : url);
  const img = url && (
    <img
      src={url}
      alt={witness.alt}
      width={witness.width}
      height={witness.height}
      loading={witness.loading}
      onError={() => setFormat(format === 'display' && witness.original ? 'original' : 'unavailable')}
    />
  );
  return (
    <figure lang={witness.lang}>
      {!url ? (
        <p className="ga-missing-evidence" role="status">
          {witness.lang === 'zh' ? '图像无法显示。' : witness.title + ' unavailable.'}
          {witness.titleZh && witness.lang !== 'zh' && <> <span lang="zh">图像无法显示。</span></>}
          {sourceUrl && (
            <> <a href={sourceUrl}>{witness.lang === 'zh' ? '在来源档案中打开原图' : 'Open the original in the source repository'}</a></>
          )}
        </p>
      ) : fullUrl ? (
        <a href={fullUrl} aria-label={(witness.lang === 'zh' ? '打开完整图像 · ' : 'Open full evidence image · ') + witness.title}>
          {img}
        </a>
      ) : img}
      <figcaption>
        {witness.title}{witness.caption && <> · {witness.caption}</>}
        {witness.retainOriginal && witness.original && format === 'display' && (
          <> · <a href={assetUrl(witness.original)}>Original image</a></>
        )}
      </figcaption>
    </figure>
  );
}
