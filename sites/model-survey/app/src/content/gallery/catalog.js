import delivery from '../assets/r2-trial.json' with { type: 'json' };

export function assetUrl(file) {
  return '/assets/' + file.sha256 + '/' + file.name;
}
export const byPath = new Map(
  delivery.assets.flatMap((file) =>
    (file.paths ?? [file.path]).filter(Boolean).map((path) => [path, file]),
  ),
);
const folder = 'assemblies/endocrine-locator/adrenal-study-';
const gallery = 'reviews/endocrine-locator/adrenal-study-r05/display/';
export const portrait = (name) => assetUrl(byPath.get(gallery + name + '.webp'));
export const sourceRoot = 'https://github.com/qianyizhang/med-assets/blob/dea3ed2/';
export const adrenalReview = sourceRoot + 'reviews/endocrine-locator/adrenal-study-r05/README.md';
export const revisions = Object.fromEntries(
  Object.entries({
    r05: 'regional',
    r04: 'illustrative',
    r03: 'teaching',
  }).map(([revision, suffix]) => [
    revision,
    byPath.get(folder + revision + '/s1233-adrenals-' + suffix + '.glb'),
  ]),
);
export const parts = [
  'Left adrenal gland',
  'Right adrenal gland',
  'Left kidney context',
  'Right kidney context',
  'Pancreas context',
];
export const rated = { r05: [4, 4, 4, 4], r04: [3, 3, 3, 3], r03: [3, 3, 3, 4] };
export const route = (path) => '#/' + path;
export const libraryId = 's1233-adrenal';
export const studyId = 'adrenal-localization';
export const reviewId = 'adrenal-r04-r05';
export const lessonPath = 'use-cases/' + studyId;
export const comparePath = 'compare/' + reviewId;
export const libraryPath = (revision) => 'library/' + libraryId + '/' + revision;
export const studies = Object.freeze({
  version: 1,
  lessons: [{ id: studyId, title: 'Locate the adrenal glands', stops: ['region', 'right-gland'] }],
  reviews: [
    {
      id: reviewId,
      title: 'The inferior adrenal fold',
      revisions: [revisions.r04.sha256, revisions.r05.sha256],
    },
  ],
});
