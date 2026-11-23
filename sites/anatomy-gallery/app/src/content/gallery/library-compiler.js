import { adrenalLibrary } from './adrenal-study.js';
import assessments from './reviewed-entries.json' with { type: 'json' };
import { localModels, teachingScenes } from './local-models.js';
import {
  additionalLibraryRows, assetUrl, byPath, exactLibraryRecords, libraryId, libraryPath,
  portrait, rated, ratingProfile, revisions, salivary,
} from './catalog.js';

import editionsByPath from './library-editions.json' with { type: 'json' };
import declarations from './library-packages.json' with { type: 'json' };
import recommendations from './library-recommendations.json' with { type: 'json' };

const ownerRoot = 'https://github.com/qianyizhang/med-assets/blob/503c33f1dadf403faaec373c1a11a8b40dc523d6/';
const fittedHeart = {
  family: 'cardiac-animated',
  revision: 'fitted-canonical',
  library: 'library/cardiac-animated/fitted-canonical',
  title: 'Cardiac Atlas · fitted Site animation',
  finding: 'Historical animation fitted for the heart imaging Site. The retained motion samples agree with the repository-source animation, which has a different digest and node count.',
  limit: 'The exact bytes and fitting transforms are unavailable to the Library. The sample comparison does not establish replacement applicability.',
  record: ownerRoot + 'reviews/heart_exterior/2026-10-30-native-visibility-r01/provenance-and-applicability.md',
  status: 'Historical export unavailable',
  exports: [{
    path: 'body/3d/assets/motion/heart_animated_clinical.glb',
    name: 'heart_animated_clinical.glb',
    bytes: 8180452,
    sha256: '17b26d1459c0fbbbc71d051452c4074d1237683ffe02c1a8021d7ac83583857a',
    unavailable: 'Exact fitted GLB unavailable in the Library. No tracked repository export was identified.',
  }],
};


function declaredAsset(path) {
  const asset = byPath.get(path);
  if (!asset) throw Error('Missing Library delivery: ' + path);
  return asset;
}

function assessmentForFile(campaign, file) {
  const entry = campaign.get(file.path);
  return entry && entry.export.sha256 === file.sha256 && entry.export.bytes === file.bytes ? entry : undefined;
}

function collectionRow(row, authoredReviews, campaign, replacements, localPreview, selectedRoute) {
  const { media: entries = [], revisions = [], ...family } = row;
  const media = entries.map(file => {
    const asset = byPath.get(file.path);
    return asset?.sha256 === file.sha256 && asset.bytes === file.bytes ? { ...file, ...asset } : file;
  });
  const label = row.id === 'adrenals' ? 'Adrenal pair · BodyParts3D' : row.label;
  const local = localPreview && localModels.find((model) => model.family === row.id);
  const records = [
    ...exactLibraryRecords.filter(record => record.family === row.id),
    ...revisions.map(record => ({ ...record, exports: record.exports.map(declaredAsset) })),
    ...(row.id === fittedHeart.family ? [fittedHeart] : []),
  ];
  if (local) records.unshift(...localModels.filter((model) => model.family === row.id));

  const paths = new Set(records.flatMap((record) => record.exports.map((file) => file.path)));
  const editions = new Map();
  for (const assessment of replacements) {
    const path = assessment.export.path;
    if (paths.has(path)) continue;
    const route = assessment.route ?? editionsByPath[path];
    const [section, family, revision] = route?.split('/') ?? [];
    if (section !== 'library' || family !== row.id || !revision) continue;
    if (!editions.has(revision) && records.some(record => record.revision === revision)) {
      throw new Error('Teaching revision collides with an existing package: ' + path);
    }
    if (!editions.has(revision)) {
      const edition = { family: row.id, revision, library: 'library/' + row.id + '/' + revision,
        title: (assessment.maintained?.label ?? assessment.maintained?.family ?? label) + ' · ' + revision,
        finding: assessment.decision, status: 'Reviewed teaching export · Local preview',
        record: assessment.sources[0]?.url, exports: [] };
      if (row.id === salivary.family) Object.assign(edition, {
        credit: salivary.credit, license: salivary.license, compare: salivary.compare,
      });
      editions.set(revision, edition);
      records.unshift(edition);
    }
    const delivery = byPath.get(path) ?? localModels.flatMap(record => record.exports).find(file => file.path === path);
    editions.get(revision).exports.push({ ...delivery, ...assessment.export, name: path.split('/').at(-1),
      mediaType: delivery?.mediaType ?? 'model/gltf-binary' });
    paths.add(path);
  }
  const history = records.map((original) => {
    const study = localPreview && teachingScenes.find((model) => model.family === row.id && model.revision === original.revision
      && original.exports.some((file) => file.path === model.exports[0].path && file.sha256 === model.exports[0].sha256));
    const record = study
      ? { ...original, scene: study.scene, exports: [study.exports[0], ...original.exports.filter((f) => f.path !== study.exports[0].path)] }
      : original;
    const previous = authoredReviews.get(record.library);
    const fileAssessments = new Map();
    for (const file of record.exports) {
      const current = assessmentForFile(campaign, file)
        ?? (file.path === previous?.export.path && file.sha256 === previous.export.sha256 ? previous : undefined);
      if (current) fileAssessments.set(file.path, current);
    }
    const available = [...fileAssessments.values()];
    const assessment = available.find((entry) => entry.maintained) ?? available[0];
    if (!assessment) return record;
    const previousMatch = previous && assessment.export.path === previous.export.path
      && assessment.export.sha256 === previous.export.sha256;
    const witness = assessment.views.find((view) => view.path === assessment.teachingView) ?? assessment.views[0];
    return {
      ...record,
      record: assessment.sources?.find((source) => record.recordPath && source.path === record.recordPath)?.url ?? record.record,
      assessment, fileAssessments, defaultFile: assessment.export.path,
      previousAssessment: previousMatch && previous !== assessment ? previous : undefined,
      axes: assessment.axes.map((axis) => axis.score),
      preview: record.preview ?? witness?.url ?? (witness && assetUrl(byPath.get(witness.path))),
    };
  });
  const maintained = history.filter(record =>
    record.assessment?.maintained || [...(record.fileAssessments?.values() ?? [])].some(assessment => assessment.maintained));
  const editorial = selectedRoute && history.find(record => record.library === selectedRoute);
  if (selectedRoute && !editorial) throw Error('Missing recommended Library revision: ' + selectedRoute);
  const recommended = maintained.length === 1 ? maintained[0] : editorial || undefined;
  const assessed = history.find((record) => record.assessment);
  const files = [...new Map([...media, ...history.flatMap((record) => record.exports)].map((file) => [file.path, file])).values()];
  return {
    ...family, label, media, history, recommended,
    state: recommended?.status ?? row.state,
    aliases: row.id === 'uff_tomo1b' ? ['dental_specimens'] : [],
    kind: row.product ? 'Product or study' : 'Model family',
    fileCount: files.filter((file) => !file.unavailable).length,
    formats: [...new Set(files.map((file) => file.path.split('.').at(-1).toUpperCase()))],
    ...ratingProfile((recommended ?? assessed)?.axes),
    path: recommended?.library ?? row.exactLibrary ?? assessed?.library
      ?? (row.id === salivary.family ? salivary.library : 'library/' + encodeURIComponent(row.id)),
    selectedRevision: recommended?.revision ?? assessed?.revision,
    image: recommended?.preview ?? assessed?.preview ?? row.image,
  };
}

export function libraryRows(teachingReview, { localPreview = true, packages = declarations, selected = recommendations } = {}) {
  const authoredReviews = new Map(teachingReview?.assessments.map((assessment) => [assessment.route, assessment]));
  const campaign = new Map((localPreview ? teachingReview?.campaign ?? [] : [])
    .map((assessment) => [assessment.export.path, assessment]));
  const replacements = [...campaign.values()].filter(entry => entry.route || editionsByPath[entry.export.path]);
  const adrenalAssessment = (revision) => assessmentForFile(campaign, revisions[revision]);
  const collections = [...packages, ...additionalLibraryRows]
    .map(row => collectionRow(row, authoredReviews, campaign, replacements, localPreview, localPreview && selected[row.id]));
  if (localPreview) {
    for (const family of Object.keys(selected)) {
      if (family !== 'cardiac-atlas' && !collections.some(row => row.id === family)) {
        throw Error('Missing recommended Library family: ' + family);
      }
    }
    const sharedLessons = new Map();
    for (const row of collections) {
      for (const record of row.history) {
        const selection = record.assessment?.maintained;
        if (!selection?.sharedOwner) continue;
        if (!sharedLessons.has(selection.sharedOwner)) sharedLessons.set(selection.sharedOwner, []);
        const lessons = sharedLessons.get(selection.sharedOwner);
        lessons.push({ library: record.library, title: selection.label });
        record.sharedLessons = lessons;
      }
    }
    const still = collections.find((row) => row.id === 'cardiac-static');
    const motion = collections.find((row) => row.id === 'cardiac-animated');
    if (still && motion) {
      const history = [...still.history, ...motion.history];
      const lessons = history.filter((record) => record.assessment?.maintained?.familyId === 'cardiac-atlas');
      if (lessons.length === 2) {
        const recommended = lessons.find(record => record.library === selected['cardiac-atlas']);
        if (!recommended) throw Error('Missing recommended shared Cardiac Atlas revision.');
        collections.splice(collections.indexOf(motion), 1);
        collections[collections.indexOf(still)] = {
          ...still, id: 'cardiac-atlas', label: lessons[0].assessment.maintained.family,
          aliases: [still.id, motion.id], history,
          lessons, path: recommended.library, recommended, selectedRevision: recommended.revision,
          state: recommended.status ?? still.state, image: recommended.preview ?? still.image,
          ...ratingProfile(recommended.axes),
          media: [...still.media, ...motion.media], fileCount: still.fileCount + motion.fileCount,
          formats: [...new Set([...still.formats, ...motion.formats])],
          use: 'Distinguish the great vessels at end diastole or scrub the ventricular wall against the fixed aorta.',
        };
      }
    }
  }
  return [
    {
      id: libraryId,
      label: adrenalLibrary.label,
      system: adrenalLibrary.system,
      purpose: adrenalLibrary.purpose,
      use: adrenalLibrary.use,
      kind: 'Revision series',
      state: 'Reviewed for regional localization',
      fileCount: Object.keys(revisions).length,
      formats: ['GLB'],
      ...ratingProfile(adrenalAssessment(adrenalLibrary.recommended)?.axes.map((axis) => axis.score) ?? rated[adrenalLibrary.recommended]),
      path: libraryPath(adrenalLibrary.recommended),
      image: portrait(adrenalLibrary.portrait),
      history: Object.entries(revisions).map(([revision, file]) => ({
        revision,
        library: libraryPath(revision),
        exports: [file],
        assessment: adrenalAssessment(revision),
        ...ratingProfile(adrenalAssessment(revision)?.axes.map((axis) => axis.score) ?? rated[revision]),
      })),
    },
    ...assessments.map((entry) => ({
      ...entry,
      assessment: assessmentForFile(campaign, byPath.get(entry.exportPath)),
      ...ratingProfile(assessmentForFile(campaign, byPath.get(entry.exportPath))?.axes.map((axis) => axis.score) ?? entry.axes),
      kind: 'Reviewed revision',
      state: 'Reviewed for teaching task',
      path: 'library/' + entry.id,
      image: assetUrl(byPath.get(entry.posterPath)),
      fileCount: 1,
      formats: ['GLB'],
      media: [byPath.get(entry.exportPath)],
      history: [],
    })),
    ...collections,
  ];
}
