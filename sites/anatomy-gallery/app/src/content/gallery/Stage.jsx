import React, { useState } from 'react';
import { trachealLessonScenes } from './local-models.js';
import { adrenalLibrary } from './adrenal-study.js';
import { libraryPath } from './catalog.js';
import { baseView, localScene, readView, stageReturn } from './presets.js';
import { Scene } from './Scene.jsx';
import { Link, Heading, Missing } from './GalleryUI.jsx';

export function Stage({ id, query, localPreview }) {
  const [file, setFile] = useState(null),
    [seq, setSeq] = useState(0);
  const view = id ? readView(query) : baseView(adrenalLibrary.recommended);
  const model = view && localScene(view);
  if (!view || (id && id !== view.version) || (model && !localPreview && !trachealLessonScenes.includes(model))) return <Missing />;
  const record = model?.library ?? libraryPath(view.revision);
  const origin = id && stageReturn(new URLSearchParams(query).get('from'), view);
  return (
    <>
      {origin && <Link to={origin.path}>← {origin.label}</Link>}
      <Heading title="3D Stage">Frame a structure, share the exact view, or export its poster.</Heading>
      <div className="ga-list-title">
        <h2>{file?.name ?? model?.title ?? 'Adrenal glands · ' + view.revision}</h2>
        <label className="ga-file">
          Open local GLB
          <input
            type="file"
            accept=".glb"
            onChange={(e) => {
              if (e.target.files[0]) {
                setFile(e.target.files[0]);
                setSeq((n) => n + 1);
              }
            }}
          />
        </label>
      </div>
      {file && <button onClick={() => setFile(null)}>Return to gallery model</button>}
      <Scene
        key={file ? 'file' + seq : query}
        initial={file ? baseView(adrenalLibrary.recommended) : view}
        origin={origin?.path}
        file={file}
        auto
        stage
      />
      {!file && origin?.path !== record && (
        <Link to={record}>View asset record →</Link>
      )}
    </>
  );
}
