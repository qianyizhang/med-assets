import React, { useState } from 'react';
import { libraryPath } from './catalog.js';
import { baseView, readView, sceneVersion } from './presets.js';
import { Scene } from './Scene.jsx';
import { Link, Heading, Missing } from './GalleryUI.jsx';

export function Stage({ id, query }) {
  const [file, setFile] = useState(null),
    [seq, setSeq] = useState(0);
  const view = id ? readView(query) : baseView('r05');
  if (!view || (id && id !== sceneVersion)) return <Missing />;
  return (
    <>
      <Heading title="3D Stage">Frame a structure, share the exact view, or export its poster.</Heading>
      <div className="ga-list-title">
        <h2>{file ? file.name : 'Adrenal glands · ' + view.revision}</h2>
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
        initial={file ? baseView('r05') : view}
        file={file}
        auto
        stage
      />
      {!file && <Link to={libraryPath(view.revision)}>View asset record →</Link>}
    </>
  );
}
