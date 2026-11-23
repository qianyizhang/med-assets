// Build the Library, study API, and selected resource routes together.
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { compileResources } from '../app/src/content/shared/release-resources.js';
import { checkMembership, compileLibrary } from '../app/src/content/gallery/library-model.js';
import { assetRoute, assetsByPath } from '../app/src/content/shared/asset-index.mjs';

async function build(project, selection, previewSnapshotSha256) {
  if (!['candidate', 'published'].includes(selection)) throw Error('Select candidate or published.');
  const candidate = selection === 'candidate';
  const gallery = resolve(project, 'src/content/gallery');
  const read = async (file) => JSON.parse(await readFile(join(gallery, file), 'utf8'));
  const { libraryRows } = await import(pathToFileURL(join(gallery, candidate ? 'library-compiler.js' : 'library-data.js')));
  const { studies } = await import(pathToFileURL(join(gallery, 'catalog.js')));
  const rawReview = await read('teaching-inputs/teaching-assessments.json');
  const publicIndex = await read('../assets/delivery-index.json');
  const byPath = assetsByPath(publicIndex);
  const review = candidate ? { ...rawReview, assessments: rawReview.assessments.map(assessment => ({
    ...assessment,
    views: assessment.views.map(view => {
      const asset = byPath.get(view.path);
      if (!asset) throw Error('Missing assessed view delivery: ' + view.path);
      return { ...view, url: assetRoute(asset) };
    }),
  })) } : rawReview;
  const frozenSurvey = candidate ? undefined : await read('../../data.json');
  const rows = candidate
    ? libraryRows(review)
    : libraryRows(frozenSurvey, review, { localPreview: false });
  const resources = compileResources({
    selection, publicIndex, reviews: review,
    ...(candidate && { localDelivery: await read('../assets/local-delivery.json'),
      legacyDental: await read('../assets/legacy-dental-assets.json'),
      archive: await read('teaching-inputs/image26-media.json') }),
  });
  const selected = compileLibrary(rows, candidate ? review : undefined);
  if (candidate) checkMembership(selected, publicIndex, resources);
  // Planning describes the historical Survey, using the corresponding family links.
  const planning = (candidate ? libraryRows(undefined, { localPreview: false }) : libraryRows(frozenSurvey))
    .map(({ id, label, path }) => ({ id, label, path }));
  await writeFile(join(gallery, 'selected-library.json'), JSON.stringify({ candidate, ...selected, planning }));
  await writeFile(join(gallery, '../assets/gallery-release.json'),
    JSON.stringify({ selection, studies, previewSnapshotSha256, resources }));
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  await build(...process.argv.slice(2));
}
