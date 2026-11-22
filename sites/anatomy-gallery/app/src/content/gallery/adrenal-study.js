// Authored presentation of the package exports. The delivery index owns byte identity.
export const adrenalLibrary = {
  id: 's1233-adrenal',
  title: 'Adrenal glands',
  label: 'Adrenal glands · s1233',
  source: 'TotalSegmentator case s1233',
  system: 'Endocrine',
  purpose: 'Localization',
  use: 'Regional localization from TotalSegmentator CT labels',
  scope: 'Left and right adrenal glands with both kidneys and the pancreas. The gland surfaces interpret a 1.5 mm label grid.',
  recommended: 'r05',
  portrait: 'updated-iso',
  revisions: {
    r05: { suffix: 'regional', axes: [4, 4, 4, 4], review: 'reviews/endocrine-locator/adrenal-study-r05/README.md' },
    r04: { suffix: 'illustrative', axes: [3, 3, 3, 3], review: 'reviews/endocrine-locator/adrenal-study-r05/README.md' },
    r03: { suffix: 'teaching', axes: [3, 2, 3, 4], review: 'reviews/endocrine-locator/adrenal-study-r04/README.md#reassessment' },
  },
};

export const adrenalLesson = {
  id: 'adrenal-localization',
  title: 'Locate the adrenal glands',
  revision: 'r05',
  stops: [
    {
      id: 'region',
      label: 'Regional view',
      title: 'Find the glands above the kidneys',
      text: 'Use the two kidneys to orient yourself. Look above and medial to each kidney for its adrenal gland. Keep the pancreas visible as regional context.',
      part: 'All structures',
      returnLabel: 'Return to regional lesson stop',
    },
    {
      id: 'right-gland',
      label: 'Right inferior rim',
      title: 'Follow the inferior rim',
      text: 'Isolate the right gland. Follow its recessed face to the lower rim, then rotate to see where the fold deepens. Its warm finish is illustrative.',
      part: 'Right adrenal gland',
      returnLabel: 'Return to right inferior rim',
    },
  ],
};

export const adrenalComparison = {
  id: 'adrenal-r04-r05',
  title: 'The inferior adrenal fold',
  record: 'reviews/endocrine-locator/adrenal-study-r05/README.md',
  part: 'Right adrenal gland',
  pair: [
    { revision: 'r04', tissue: 'original-tissue-ortho', neutral: 'original-fold-ortho' },
    { revision: 'r05', tissue: 'updated-tissue-ortho', neutral: 'updated-fold-ortho' },
  ],
  sections: {
    display: 'case-sections',
    title: 'Matched case contours',
    alt: 'Matched case contours at the right inferior cleft',
    finding: 'At −67.35 mm, the worst local contour difference fell from 5.97 mm in r04 to 0.64 mm in r05.',
  },
};

// The version fixes the scene recipe and the part names accepted by its shared URLs.
export const adrenalScene = {
  version: 'adrenal-v1',
  parts: [
    'Left adrenal gland',
    'Right adrenal gland',
    'Left kidney context',
    'Right kidney context',
    'Pancreas context',
  ],
};
