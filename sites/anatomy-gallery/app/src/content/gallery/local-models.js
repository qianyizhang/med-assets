import localDelivery from '../assets/local-delivery.json' with { type: 'json' };
import { assetUrl, byPath } from './catalog.js';
import { oneBreathPath, tracheaReviewPath } from './airway-data.js';

const assets = new Map(localDelivery.assets.map((file) => [file.path, file]));
const heartPoster = 'reviews/heart_exterior/2026-10-30-native-visibility-r01/images/updated-static-whole-front.png';
const bronchialReview = 'reviews/bronchial_tree/2026-11-21-distal-simplification-trial/';
const thyroidReview = 'reviews/teaching-assessments/refinement-form/';
const thyroidPoster = thyroidReview + 'plates/thyroid-r02.webp';
const lymphNodeReview = 'reviews/teaching-assessments/2026-11-22-lymph-node-tissue-layers/';
const lymphNodePoster = lymphNodeReview + 'plates/tissue-layers.webp';
export const firstForkPath = 'use-cases/airway/first-fork';

export const cardiacExterior = {
  family: 'cardiac-exterior',
  revision: 'static-opaque-exterior-r02',
  library: 'library/cardiac-exterior/static-opaque-exterior-r02',
  title: 'Static opaque exterior · r02',
  finding: 'Compact Workshop derivative with 124 selectable exterior objects. The repack preserves their geometry, materials and placement.',
  limit: 'Exterior reference. Vessel joins and visible gaps remain.',
  status: 'Recommended static export · Local preview',
  record: 'https://github.com/qianyizhang/med-assets/blob/9d70d2646ec2642f0312ab7ca6d17dc9e7dbd4ef/heart/exterior-presentation-r01/README.md#attribution-and-limits',
  verification: {
    href: '/reviews/heart_exterior/2026-11-21-static-repack/checks.json',
    label: 'Repack verification (JSON)',
  },
  exports: [assets.get('heart/exterior-presentation-r02/exports/static-opaque-exterior-repacked.glb')],
  preview: assetUrl(byPath.get(heartPoster)),
  scene: {
    version: 'cardiac-exterior-v1',
    posterAlt: 'Front view of the original static opaque heart',
    posterCaption: 'Blender reference · Original static r01 exterior',
  },
};

const distalSampling = {
  family: 'bronchial_tree',
  revision: 'distal-sampling-r14',
  library: 'library/bronchial_tree/distal-sampling-r14',
  title: 'Bronchial tree · distal sampling r14',
  finding: 'Lighter bronchial exterior for tracing the first fork. The central Y, both lobar neighborhoods and all 16 terminal neighborhoods retain their r13 geometry.',
  limit: 'Branch routes are schematic and terminal ends are closed. The lower fork remains angular and asymmetric, with a collar and pocket on the right. The largest outline shift measured at teaching zoom is 1.41 pixels at a distal crossing.',
  status: 'Earlier first-fork teaching edition · Local preview',
  record: 'https://github.com/qianyizhang/med-assets/blob/122eca318be6bc35c500499768f3f47ebf2a149d/models/bronchial_tree/exports/authored-central-fairing-r13/ATTRIBUTION.md',
  verification: { href: '/' + bronchialReview + 'geometry.json', label: 'Geometry verification (JSON)' },
  exports: [assets.get('models/bronchial_tree/exports/distal-sampling-r14/bronchial_distal_sampling.glb')],
  preview: assetUrl(assets.get(bronchialReview + 'evidence/close.webp')),
  lesson: firstForkPath,
  useCase: 'Trace the first bronchial fork',
  compare: 'compare/bronchial-r13',
  compareLabel: 'Compare the original r13',
  scene: {
    version: 'bronchial-first-fork-v1',
    singleMesh: true,
    posterAlt: 'Matched neutral close-ups of the first fork in original r13 and distal sampling r14',
    posterCaption: 'Blender reference · r13 and r14 at the same scale',
    material: 'Neutral',
    // Neutral close view from the trial, converted from Blender Z-up to glTF Y-up.
    camera: { position: [0, 0.166275, 0.835252], target: [0, 0.082, -0.0075], height: 0.045 },
  },
};

export const bronchialExterior = {
  ...distalSampling, revision: 'first-fork-fairing-r15', library: 'library/bronchial_tree/first-fork-fairing-r15',
  title: 'Bronchial tree · first-fork fairing r15',
  finding: 'Follow the trunk around the central fork into each main branch. Local fairing reduces the collar at the junction.',
  limit: 'Interpreted teaching surface. The source tree and earlier editions remain available in revision history.',
  status: 'Recommended for first-fork teaching · Local preview',
  recordPath: 'models/bronchial_tree/exports/first-fork-fairing-r15/README.md',
  exports: [assets.get('models/bronchial_tree/exports/first-fork-fairing-r15/bronchial-first-fork.glb')],
  record: undefined, verification: undefined, preview: undefined,
  scene: { ...distalSampling.scene, version: 'bronchial-first-fork-v2',
    posterPath: 'reviews/teaching-assessments/target-form/plates/bronchial-first-fork-teaching.webp',
    posterAlt: 'Fairing at the first bronchial fork in r15',
    posterCaption: 'Trace the trunk into both branches of the first fork.' },
};

export const thyroidExterior = {
  family: 'thyroid_ct_s0189',
  revision: 'illustrative-exterior-r02',
  library: 'library/thyroid_ct_s0189/illustrative-exterior-r02',
  title: 'Thyroid · s0189 illustrative exterior r02',
  finding: 'Localized fairing reduces the lower rear ridges. The medial bridge, unequal lobes and source frame are preserved.',
  limit: 'Case-derived illustrative exterior. The same-case trachea, tissue detail and clinical accuracy remain unverified.',
  status: 'Recommended for bridge recognition · Local preview',
  recordPath: 'models/thyroid_ct_s0189/exports/illustrative-exterior-r02/README.md',
  verification: { href: '/' + thyroidReview + 'thyroid-integrity.json', label: 'Surface integrity verification (JSON)' },
  exports: [assets.get('models/thyroid_ct_s0189/exports/illustrative-exterior-r02/thyroid-illustrative-exterior.glb')],
  preview: assetUrl(assets.get(thyroidPoster)),
  compare: 'compare/teaching-refinements?asset=4c2dee513f713fd8d649e7d1928ba3859ce1d25e81468e707b65a5fbeeee216a',
  compareLabel: 'Compare r01 and r02',
  scene: {
    version: 'thyroid-bridge-v1',
    singleMesh: true,
    material: 'Neutral',
    posterPath: thyroidPoster,
    posterAlt: 'Matched rear thyroid views before and after local fairing, with a second r02 view of the bridge',
    posterCaption: 'Find the continuous bridge below the recess and compare the two unequal lobes.',
    // Matched whole view, converted from Blender Z-up to glTF Y-up.
    camera: { position: [0, 0.66, 0.02], target: [0, 0.625, -0.18], height: 0.078 },
  },
};

const lymphNodeFollicles = ['Yao_follicles'];
const lymphNodeParacortex = ['Yao_paracortex'];
const lymphNodeMedulla = ['Yao_medulla_of_lymph_node'];

export const lymphNodeTissues = {
  family: 'lymph_node',
  revision: 'hra-tissue-layers-r01',
  library: 'library/lymph_node/hra-tissue-layers-r01',
  title: 'Lymph node · HRA tissue layers r01',
  finding: 'Compare the capsule with the exact source follicles, paracortex and medulla. The tissue-only export omits all three source vessel and network meshes.',
  limit: 'The capsule apertures and irregular interior relief remain source features. Tissue contacts, histology and flow remain unverified.',
  status: 'Original tissue-layer teaching edition · Local preview',
  recordPath: 'models/lymph_node/exports/hra-tissue-layers-r01/README.md',
  verification: { href: '/' + lymphNodeReview + 'build.json', label: 'Decoded source comparison (JSON)' },
  exports: [assets.get('models/lymph_node/exports/hra-tissue-layers-r01/lymph-node-tissue-layers.glb')],
  preview: assetUrl(assets.get(lymphNodePoster)),
  compare: 'library/lymph_node/hra-v1.2',
  compareLabel: 'Open the original HRA export',
  scene: {
    version: 'lymph-node-tissues-v1',
    initialPart: 'Capsule',
    groups: {
      Capsule: ['Yao_capsule_of_lymph_node'],
      'Named tissue regions': [...lymphNodeFollicles, ...lymphNodeParacortex, ...lymphNodeMedulla],
      Follicles: lymphNodeFollicles,
      Paracortex: lymphNodeParacortex,
      Medulla: lymphNodeMedulla,
    },
    posterPath: lymphNodePoster,
    posterAlt: 'Two matched views compare the lymph node capsule with follicles, paracortex and medulla',
    posterCaption: 'Switch from the capsule to the named tissue regions and compare their positions at the same angle.',
    // Primary comparison camera, converted from Blender Z-up to glTF Y-up.
    camera: { position: [0.01503, 0.336791, 0.140863], target: [-0.000899, 0.32848, 0.071606], height: 0.02385 },
  },
};

// These presets select parts of existing Library deliveries. Normalized phase is
// stored in the Stage link only for presets with a named source animation.
const exterior = 'Source exterior';
const section = 'Authored section';

function tracheaSelection(variant, lesson, returnLabel, camera) {
  const family = 'trachea';
  const revision = 'open-airway-r06';
  const description = variant === 'open' ? 'Open tracheal shell' : 'Tracheal cutaway';
  const file = byPath.get('models/trachea/exports/' + revision + '/trachea-' + variant + '.glb');
  const comparison = 'reviews/trachea/2026-10-29-open-airway-r06/display/comparison-whole.webp';
  return {
    family, revision, lesson, returnLabel, title: description,
    library: 'library/' + family + '/' + revision + '?file=' + file.sha256,
    exports: [file],
    preview: assetUrl(byPath.get(comparison)),
    scene: {
      version: 'trachea-' + variant + '-v1', camera,
      posterAlt: 'Matched projections of the source cast, open tracheal shell and cutaway',
      posterCaption: 'Matched reference projections · closed cast, open shell and cutaway',
      initialPart: description + ' and C-bands',
      groups: {
        [description + ' and C-bands']: null,
        [description + ' alone']: ['Trachea | authored ' + variant + ' teaching shell'],
      },
    },
  };
}

export const openTrachea = tracheaSelection('open', tracheaReviewPath, 'Return to the trachea review',
  { position: [0.16, 0.28, 0.47], target: [0, 0.117, -0.015], height: 0.135 });
export const cutawayTrachea = tracheaSelection('cutaway', oneBreathPath, 'Return to One Breath',
  { position: [0.11, 0.13, 0.44], target: [0.01, 0.117, -0.014], height: 0.14 });
export const trachealLessonScenes = [openTrachea, cutawayTrachea];

function sectionStudy(family, title, position, height, groups, caption, posterPath) {
  const revision = 'metadata-cleanup-r01';
  const direction = [0.23, 0.12, 1];
  const target = position.map((value, i) => value - direction[i] * height * 3 / Math.hypot(...direction));
  return {
    family, title, revision, library: 'library/' + family + '/' + revision,
    exports: [byPath.get('models/' + family + '/exports/' + revision + '/' + family + '.glb')],
    scene: { version: family + '-section-v1', groups, initialPart: exterior,
      camera: { position, target, height }, posterPath,
      posterAlt: title + ' exterior and separate authored teaching section', posterCaption: caption },
  };
}

const digestiveViews = 'reviews/teaching-assessments/2026-11-22-body-cardiovascular-digestive-endocrine/views/';
export const teachingScenes = [
  sectionStudy('gallbladder', 'Gallbladder', [-0.0265903, -0.0646819, 0.285867], 0.0863636, {
    [exterior]: ['Gallbladder | source surface'],
    [section]: ['gallbladder | anterior teaching section', 'Cystic duct · schematic'],
  }, 'Switch to the authored section to find the cut rim and separate schematic cystic duct.',
  digestiveViews + '12-isolation.webp'),
  sectionStudy('stomach', 'Stomach', [0.0904053, -0.0124194, 0.3918734], 0.128546, {
    [exterior]: ['Stomach | source surface'],
    [section]: ['stomach | authored closed-back teaching section',
      ...Array.from({ length: 11 }, (_, i) => 'Gastric mucosal fold ' + (i + 1))],
  }, 'Switch to the authored section and follow the folds across its exposed face.',
  digestiveViews + '17-isolation.webp'),
  {
    family: 'cardiac-animated', title: 'Cardiac Atlas · authored motion', revision: 'repository-source',
    library: 'library/cardiac-animated/repository-source',
    exports: [byPath.get('heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb')],
    scene: { version: 'cardiac-wall-motion-v1', clip: 'CardiacCycle_75BPM', initialPart: 'Wall and fixed aorta',
      groups: { 'Wall and fixed aorta': ['LV | complete wall', 'Aorta | root, ascending, arch and descending'], 'Whole heart': null },
      camera: { target: [0.0222792, 0.0131365, -0.00593888], position: [0.2382792, 0.0581365, -0.20693888], height: 0.1580501 },
      posterPath: digestiveViews + '06-motion.webp', posterAlt: 'Two poses of the authored heart animation',
      posterCaption: 'Scrub the authored cycle and compare the ventricular wall with the fixed aorta.' },
  },
];

const wallMotion = {
  family: 'cardiac-animated', revision: 'wall-motion-r01', library: 'library/cardiac-animated/wall-motion-r01',
  title: 'Cardiac Atlas · ventricular wall motion',
  exports: [assets.get('heart/Cardiac_Atlas_Animated/exports/wall-motion-r01/ventricular-wall-motion.glb')],
  scene: { ...teachingScenes.find((model) => model.family === 'cardiac-animated').scene, version: 'cardiac-wall-motion-v2',
    groups: { 'Wall and fixed aorta': null, 'Ventricular wall': ['LV | complete wall'] } },
};

const thyroidContext = byPath.get('models/parathyroids/exports/z-localization-r01/parathyroids_thyroid_context.glb');
teachingScenes.push({
  family: 'parathyroids', revision: 'z-localization-r01', library: 'library/parathyroids/z-localization-r01',
  exports: [thyroidContext],
  scene: { version: 'posterior-parathyroids-v1', initialPart: 'Posterior thyroid and glands',
    groups: { 'Posterior thyroid and glands': null,
      'Glands alone': ['Superior parathyroid gland.r.001', 'Superior parathyroid gland.l.001',
        'Inferior parathyroid gland.r.001', 'Inferior parathyroid gland.l.001'] },
    camera: { target: [0, 1.472, 0.01], position: [0, 1.472, -0.14], height: 0.047 },
    posterPath: 'reviews/teaching-assessments/target-risk/views/parathyroid.webp',
    posterCaption: 'Locate both upper and both lower atlas targets on the posterior thyroid.' },
});

// Each version pins the model bytes as well as its camera and named selections.
function packedEdition(source, file, title, version, posterPath, posterCaption) {
  const revision = file.path.split('/').at(-2);
  return {
    family: source.family, title, revision,
    library: 'library/' + source.family + '/' + revision,
    exports: [file],
    scene: { ...source.scene, version, posterPath, posterCaption },
  };
}

teachingScenes.push(
  packedEdition(teachingScenes.find((model) => model.family === 'stomach'),
    assets.get('models/stomach/exports/teaching-economy-r02/stomach.glb'),
    'Stomach · exterior and section', 'stomach-section-v2',
    'reviews/teaching-assessments/reopen-economy/views/stomach-updated.webp',
    'Switch from the source exterior to the separate authored section and trace all eleven fold cues.'),
  packedEdition(lymphNodeTissues, assets.get('models/lymph_node/exports/tissue-color-pack-r02/lymph-node.glb'),
    'Lymph node · capsule and tissue regions', 'lymph-node-tissues-v2',
    'reviews/teaching-assessments/reopen-paired/plates/lymph-teaching.webp',
    'Compare the capsule outline with the follicles, paracortex and medulla. The capsule aperture and deep medullary clefts have no linked specimen annotation.'),
);

const cardiacSelections = 'heart/Cardiac_Atlas_Animated/exports/shared-source-r01/';
const cardiacReview = 'reviews/teaching-assessments/2026-11-23-cardiac-shared-source/';
const greatVesselsED = {
  family: 'cardiac-static', revision: 'great-vessels-ed-r01', library: 'library/cardiac-atlas/great-vessels-ed-r01',
  title: 'Distinguish the pulmonary trunk and aortic arch',
  status: 'Shared Cardiac Atlas · end diastole', recordPath: cardiacReview + 'README.md',
  exports: [assets.get(cardiacSelections + 'cardiac-static-ed.glb')],
  scene: { version: 'cardiac-great-vessels-v1', initialPart: 'Whole heart at end diastole',
    groups: { 'Whole heart at end diastole': null, 'Arch and pulmonary trunk': [
      'Aorta | root, ascending, arch and descending', 'Pulmonary trunk', 'Right pulmonary artery', 'Left pulmonary artery',
    ] },
    camera: { position: [0.186873, 0.060885, 0.428329], target: [0.006311, 0.017894, -0.001581], height: 0.176381 },
    posterPath: cardiacReview + 'views/great-vessels-poster.webp',
    posterCaption: 'Identify the arch behind the pulmonary trunk. Rotate the isolated vessels to check which passes in front. The joins are schematic.' },
};
const sharedWallMotion = {
  ...wallMotion, revision: 'wall-motion-shared-r01', library: 'library/cardiac-atlas/wall-motion-shared-r01',
  title: 'Compare ventricular motion with the fixed aorta',
  status: 'Shared Cardiac Atlas · authored cycle', recordPath: cardiacReview + 'README.md',
  exports: [assets.get(cardiacSelections + 'ventricular-wall-motion.glb')],
  scene: { ...wallMotion.scene, version: 'cardiac-wall-motion-v3',
    posterPath: cardiacReview + 'views/wall-motion-poster.webp' },
};

export const localModels = [greatVesselsED, sharedWallMotion, cardiacExterior, bronchialExterior, distalSampling, thyroidExterior, lymphNodeTissues, wallMotion];
