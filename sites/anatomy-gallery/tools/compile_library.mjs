// Build the Library, study API, and selected resource routes together.
import { execFileSync } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { compileResources } from '../app/src/content/shared/release-resources.js';
import { checkMembership, compileLibrary } from '../app/src/content/gallery/library-model.js';
import { assetRoute, assetsByPath } from '../app/src/content/shared/asset-index.mjs';

function checkCandidateAdmission(selected, offline, plan) {
  const files = [];
  const usedAssessments = new Set();
  function add(row, route, role, model) {
    const { path, sha256, bytes, unavailable } = model;
    if (!/\.(glb|blend|stl)$/i.test(path)) return;
    if (model.url?.startsWith('/assets/') && model.url !== assetRoute(model)) {
      throw Error('Gallery Library export points to a different resource route: ' + path);
    }
    files.push({ path, sha256, bytes, unavailable, reader: { family: row.id, route, role } });
  }
  function bindAssessment(record, model) {
    const id = record.fileAssessments?.[model.path] ?? record.assessment;
    if (selected.assessments[id]?.export.path === model.path) usedAssessments.add(id);
  }
  for (const row of selected.rows) {
    for (const model of row.media ?? []) {
      add(row, row.path, 'family-media', model);
      bindAssessment(row, model);
    }
    for (const record of row.history) {
      for (const model of record.exports) {
        add(row, record.library, row.recommended === record.library ? 'recommended-revision' : 'listed-revision', model);
        bindAssessment(record, model);
      }
    }
  }
  const selections = selected.teaching.campaign.flatMap(id => {
    const { export: model, maintained, taskId } = selected.assessments[id];
    if (!maintained) return [];
    if (!usedAssessments.has(id) || maintained.taskId !== taskId) {
      throw Error('Gallery Library selection has no exact reader assessment: ' + model.path);
    }
    const { path, sha256, bytes } = model;
    return [{ path, sha256, bytes, taskId, familyId: maintained.familyId, collection: maintained.collection }];
  });
  execFileSync('uv', ['run', ...(offline ? ['--offline'] : []), 'python', '-m', 'assetkit.gallery', ...(plan ? ['--plan'] : [])], {
    cwd: fileURLToPath(new URL('../../../', import.meta.url)),
    input: JSON.stringify({ files, selections }),
    stdio: ['pipe', 'inherit', 'inherit'],
  });
}

async function build(project, selection, previewSnapshotSha256, mode = '--offline', planInputs) {
  if (!['candidate', 'published'].includes(selection)) throw Error('Select candidate or published.');
  const candidate = selection === 'candidate';
  if (planInputs && !candidate) throw Error('The Gallery admission plan applies to the candidate.');
  const gallery = resolve(project, 'src/content/gallery');
  const read = async (file) => JSON.parse(await readFile(join(gallery, file), 'utf8'));
  const readTeaching = async (file) => JSON.parse(await readFile(
    join(planInputs ?? join(gallery, 'teaching-inputs'), file), 'utf8'));
  const { libraryRows } = await import(pathToFileURL(join(gallery, candidate ? 'library-compiler.js' : 'library-data.js')));
  const { studies } = await import(pathToFileURL(join(gallery, 'catalog.js')));
  const rawReview = await readTeaching('teaching-assessments.json');
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
      archive: await readTeaching('image26-media.json') }),
  });
  const selected = compileLibrary(rows, candidate ? review : undefined);
  if (candidate) {
    checkMembership(selected, publicIndex, resources);
    checkCandidateAdmission(selected, mode === '--offline', Boolean(planInputs));
  }
  if (planInputs) return;
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
