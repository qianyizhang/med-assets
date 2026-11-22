import { adrenalComparison, adrenalLesson, adrenalLibrary } from './adrenal-study.js';
import retainedReviews from './static-reviews.json' with { type: 'json' };
import { pathways } from './pathway-data.js';
import { airwayStudies } from './airway-data.js';
import { oralSpaces, oralSpacesPath, regionalLessons, regionalPath } from './teaching-data.js';
import {
  skeletalCredit, skeletalExportPath, skeletalLibraryPath, skeletalLicense, skeletalPackage, skeletalPath,
  skeletalPlatePath, skeletalSource, skeletalStops,
} from './skeletal-data.js';
import delivery from '../assets/delivery-index.json' with { type: 'json' };
import legacyDental from '../assets/legacy-dental-assets.json' with { type: 'json' };

export function assetUrl(file) {
  return '/assets/' + file.sha256 + '/' + file.name;
}
export const byPath = new Map(
  [...delivery.assets, ...legacyDental.assets].flatMap((file) =>
    (file.paths ?? [file.path]).filter(Boolean).map((path) => [path, file]),
  ),
);
const folder = 'assemblies/endocrine-locator/adrenal-study-';
const gallery = 'reviews/endocrine-locator/adrenal-study-r05/display/';
export const portraitAsset = (name) => byPath.get(gallery + name + '.webp');
export const portrait = (name) => assetUrl(portraitAsset(name));
export const sourceRoot = 'https://github.com/qianyizhang/med-assets/blob/dea3ed2/';
export const adrenalReview = sourceRoot + adrenalComparison.record;
export const revisions = Object.fromEntries(
  Object.entries(adrenalLibrary.revisions).map(([revision, { suffix }]) => [
    revision,
    byPath.get(folder + revision + '/s1233-adrenals-' + suffix + '.glb'),
  ]),
);
export const ratingAxes = ['Fidelity to evidence', 'Form and surface', 'Teaching readability', 'Mesh economy'];

export function ratingProfile(values = []) {
  const axes = ratingAxes.map((_, i) => {
    const value = values[i];
    return Number.isInteger(value) && value >= 0 && value <= 4 ? value : null;
  });
  const score = axes.includes(null) ? null : axes.reduce((sum, value) => sum + value, 0);
  let ratingLabel = 'Unrated';
  if (score !== null) ratingLabel = score + '/16';
  else if (axes.some(value => value !== null)) ratingLabel = 'Partially rated';
  return { axes, score, ratingLabel };
}

export const rated = Object.fromEntries(
  Object.entries(adrenalLibrary.revisions).map(([revision, { axes }]) => [revision, axes]),
);
export const route = (path) => '#/' + path;
export const libraryId = adrenalLibrary.id;
export const studyId = adrenalLesson.id;
export const reviewId = adrenalComparison.id;
export const lessonPath = 'use-cases/' + studyId;
export const comparePath = 'compare/' + reviewId;
export const libraryPath = (revision) => 'library/' + libraryId + '/' + revision;
export const bodyPartsAdrenal = {
  family: 'adrenals',
  id: 'adrenals__source-candidate-01',
  artifact: byPath.get('models/adrenals/exports/source-candidate-01/adrenals_source_frame.glb'),
  evidence: [
    {
      asset: byPath.get('reviews/adrenals/2026-10-23-bp3d-bounded-migration/display/candidate-409ef01a7e81.webp'),
      title: 'Oblique view',
      alt: 'Separate folded and arched adrenal gland silhouettes',
      caption: 'The two gland surfaces in the source-frame export.',
    },
    {
      asset: byPath.get('reviews/adrenals/2026-10-23-bp3d-bounded-migration/display/candidate-a524ea65d5eb.webp'),
      title: 'Contact sheet',
      alt: 'Isolated adrenal glands and their positions beside the superior poles of the kidneys',
      caption: 'The kidneys provide localization context. The gland GLB contains only the adrenal pair.',
    },
  ],
  record: 'https://github.com/qianyizhang/med-assets/blob/503c33f1dadf403faaec373c1a11a8b40dc523d6/reviews/adrenals/2026-10-23-bp3d-bounded-migration/bounded-record.json',
};
export const bodyPartsReviewPath = 'compare/' + bodyPartsAdrenal.id;
export const adrenalCandidateBookmark = '#candidate-' + bodyPartsAdrenal.id;
export const adrenalStudyBookmark = '#refinement-surface-adrenal';

export function matchesBodyPartsExport(row) {
  const asset = bodyPartsAdrenal.artifact;
  return row.id === bodyPartsAdrenal.family && row.media.some((file) =>
    file.path === asset.path && file.sha256 === asset.sha256 && file.bytes === asset.bytes,
  );
}

const salivaryReviewRoot = 'reviews/salivary_glands/2026-10-26-native-scoped-r02/';
const salivaryExportRoot = 'models/salivary_glands/exports/z-native-scoped-r02/';
const salivaryLessonFiles = { 'duct-course': 'glands-and-parotid-ducts.glb', location: 'same-source-context.glb' };
export const salivary = {
  family: 'salivary_glands',
  revision: 'z-native-scoped-r02',
  library: 'library/salivary_glands/z-native-scoped-r02',
  lesson: 'use-cases/head-and-neck',
  lessonFiles: salivaryLessonFiles,
  compare: 'compare/salivary-native-r02',
  record: sourceRoot + salivaryReviewRoot + 'README.md',
  title: 'Major salivary glands',
  finding: 'Three gland pairs and gross parotid duct course',
  limit: 'Both submandibular ducts excluded. The left source crossing is confirmed.',
  credit: 'Z-Anatomy and upstream contributors · CC BY-SA 4.0.',
  license: sourceRoot + 'sources/datasets/z-anatomy/salivary-region/License.txt',
  exports: Object.values(salivaryLessonFiles).map((name) => byPath.get(salivaryExportRoot + name)),
  useCase: 'Find the glands in Head & Neck',
  portrait: {
    asset: byPath.get(salivaryReviewRoot + 'glands-ducts-front-source.webp'),
    alt: 'Front view of the three gland pairs and two parotid ducts in the r02 export.',
  },
  witness: (name) => byPath.get(salivaryReviewRoot + name + '.webp'),
};

export const airway = airwayStudies.map((study) => {
  const evidence = study.views.map(([file, title, alt, original]) => ({
    file,
    asset: byPath.get(study.reviewDir + file),
    original: original && byPath.get(study.reviewDir + original),
    title,
    alt,
  }));
  return {
    ...study,
    library: 'library/' + study.family + '/' + study.revision,
    compare: 'compare/' + study.id,
    lesson: 'use-cases/airway',
    useCase: 'Explore Airway Review',
    record: sourceRoot + study.recordPath,
    exports: study.exportNames.map((name) =>
      byPath.get('models/' + study.family + '/exports/' + study.revision + '/' + name),
    ),
    evidence,
    portrait: study.portraitFile ? evidence.find((view) => view.file === study.portraitFile) : evidence[0],
  };
});

function bindReview(study, compare) {
  const sections = (study.sections ?? []).map((section) => ({
    ...section,
    views: section.views.map((view) => ({
      ...view,
      asset: byPath.get(view.display ?? view.path),
      original: view.display ? byPath.get(view.path) : undefined,
      retainOriginal: true,
      alt: view.alt ?? view.title,
    })),
  }));
  const portrait = study.portraitPath
    ? sections.flatMap((section) => section.views).find((view) => view.path === study.portraitPath)
    : sections[0]?.views[0];
  return {
    ...study,
    compare,
    sections,
    portrait: portrait?.asset ? portrait : undefined,
    chapters: study.chapters?.map((chapter) => bindReview(chapter, compare + '/' + chapter.id)),
    library: study.family && 'library/' + study.family + '/' + study.revision,
    exports: [
      ...(study.exportPaths ?? []).map((path) => byPath.get(path)),
      ...(study.unavailableExports ?? []),
    ],
  };
}

export const staticReviews = retainedReviews.map((study) => bindReview(study, 'compare/' + study.id));
const staticLibrary = staticReviews.flatMap((study) => study.chapters ?? [study]).filter((study) => study.library);
const skeletalLibrary = skeletalStops.map((stop) => {
  const library = skeletalLibraryPath(stop.id);
  const portraitPath = skeletalPlatePath(stop.sourceId, 1);
  return {
    ...stop,
    family: 'cartilage-assembly',
    revision: library.split('/').at(-1),
    library,
    lesson: skeletalPath + '/' + stop.id,
    useCase: 'Return to the relationship plates',
    record: skeletalSource + skeletalPackage,
    credit: skeletalCredit + ' licensed under CC Attribution 4.0 International.',
    license: skeletalLicense,
    exports: [byPath.get(skeletalExportPath(stop.sourceId))],
    portrait: {
      asset: byPath.get(portraitPath),
      sourceUrl: skeletalSource + portraitPath,
      title: 'Front view',
      alt: stop.captions[0],
    },
  };
});
export const exactLibraryRecords = [salivary, ...airway, ...staticLibrary, ...skeletalLibrary];
export const additionalLibraryRows = staticLibrary.filter((study) => study.libraryRow).map((study) => ({
  id: study.family,
  label: study.title,
  system: 'Oral & dental',
  purpose: study.libraryRow,
  use: study.finding,
  state: study.status,
  exactLibrary: study.library,
  image: study.portrait && assetUrl(study.portrait.asset),
  evidence: { url: study.record },
  media: study.exports,
}));

export const heartSlice = { id: 'heart-slice', title: 'Read the same heart slice three ways', stops: [] };
export const oneBreathStoryboard = { id: 'one-breath', title: 'One Breath', stops: [] };
export const dentalLayerSheet = { id: 'dental-layers', title: 'Reveal the layers of a prepared incisor', stops: [] };

export const studies = Object.freeze({
  version: 1,
  lessons: [
    { id: studyId, title: adrenalLesson.title, stops: adrenalLesson.stops.map(({ id }) => id) },
    {
      id: 'head-and-neck',
      title: 'Locate the major salivary glands',
      stops: ['location', 'duct-course'],
    },
    { id: 'right-arm', title: 'Right elbow and shoulder', stops: ['elbow', 'shoulder'] },
    { id: oralSpacesPath.split('/').at(-1), title: 'Oral spaces', stops: Object.keys(oralSpaces) },
    { id: regionalPath.split('/').at(-1), title: 'Regional locators', stops: regionalLessons.map(({ id }) => id) },
    { id: skeletalPath.split('/').at(-1), title: 'Skeletal relationships', stops: skeletalStops.map(({ id }) => id) },
    { id: 'dental-arch', title: 'Dental arch identification', stops: ['upper', 'lower'] },
    ...Object.entries(pathways).map(([id, lesson]) => ({ id, title: lesson.en.title, stops: ['en', 'zh'] })),
    heartSlice,
    oneBreathStoryboard,
    dentalLayerSheet,
  ],
  reviews: [
    ...staticReviews.map((study) => ({
      id: study.id,
      title: study.title,
      revisions: (study.chapters ?? [study]).flatMap((entry) => entry.exports.map((file) => file.sha256)),
    })),
    ...airway.map((study) => ({
      id: study.id,
      title: study.title,
      revisions: study.exports.map((file) => file.sha256),
    })),
    {
      id: 'salivary-native-r02',
      title: 'The rejected submandibular duct crossing',
      revisions: salivary.exports.map((file) => file.sha256),
    },
    {
      id: reviewId,
      title: adrenalComparison.title,
      revisions: adrenalComparison.pair.map(({ revision }) => revisions[revision].sha256),
    },
    {
      id: bodyPartsAdrenal.id,
      title: 'Adrenal pair · BodyParts3D',
      revisions: [bodyPartsAdrenal.artifact.sha256],
    },
  ],
});
