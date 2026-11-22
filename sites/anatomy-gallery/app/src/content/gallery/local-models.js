import localDelivery from '../assets/local-delivery.json' with { type: 'json' };
import { assetUrl, byPath } from './catalog.js';

const assets = new Map(localDelivery.assets.map((file) => [file.path, file]));
const heartPoster = 'reviews/heart_exterior/2026-10-30-native-visibility-r01/images/updated-static-whole-front.png';
const bronchialReview = 'reviews/bronchial_tree/2026-11-21-distal-simplification-trial/';
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

export const bronchialExterior = {
  family: 'bronchial_tree',
  revision: 'distal-sampling-r14',
  library: 'library/bronchial_tree/distal-sampling-r14',
  title: 'Bronchial tree · distal sampling r14',
  finding: 'Lighter bronchial exterior for tracing the first fork. The central Y, both lobar neighborhoods and all 16 terminal neighborhoods retain their r13 geometry.',
  limit: 'Branch routes are schematic and terminal ends are closed. The lower fork remains angular and asymmetric, with a collar and pocket on the right. The largest outline shift measured at teaching zoom is 1.41 pixels at a distal crossing.',
  status: 'Recommended for first-fork teaching · Local preview',
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

export const localModels = [cardiacExterior, bronchialExterior];

export function isLoopbackGallery(hostname) {
  return ['127.0.0.1', 'localhost', '[::1]'].includes(hostname);
}
