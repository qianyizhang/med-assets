const media = 'lessons/ultrasound-anatomy/media/';
const digestive = 'lessons/body-systems/display/digestive-s1233-assembly-';
export const ultrasoundCollection = 'use-cases/ultrasound';
export const ultrasoundDevelopment = 'use-cases/ultrasound-development';
export const ultrasoundAssets = 'use-cases/ultrasound-assets';
const source = 'https://github.com/qianyizhang/med-assets/blob/e51891b/';

export const abdomenTour = {
  id: 'ultrasound-abdomen',
  title: 'Abdomen ultrasound',
  stops: [{
    id: 'gallbladder',
    title: 'Find the gallbladder beside the liver',
    part: 'gallbladder',
    grayscale: {
      path: media + 'gallbladder-grayscale.webp',
      title: 'Synthetic ultrasound',
      alt: 'Marker A is inside the dark elongated shape. Marker B is in the brighter tissue beside it.',
    },
    section: {
      path: media + 'gallbladder-section.webp',
      title: 'Matching anatomical section',
      alt: 'Marker A is in the gallbladder in green, and marker B is in the liver in coral.',
    },
  }],
};

export const abdomenTourPath = 'use-cases/' + abdomenTour.id;

export const otherTopics = [
  ['Abdominal aortic aneurysm', 'Distinguish the abdominal aorta from nearby structures and locate its outer walls.'],
  ['Thyroid', 'Find the thyroid and trachea in a transverse section.'],
  ['Breast', 'Orient to the tissue layers between the skin and chest wall.'],
  ['Pregnancy', 'Orient to the fetus, placenta and amniotic cavity.'],
];

export const abdomenParts = [
  {
    id: 'gallbladder',
    title: 'Gallbladder',
    role: 'The dark shape in the exercise comes from the s1233 gallbladder label.',
    finding: 'The source label resolves the outline beside the liver. The grayscale wall is drawn from the label boundary and needs review against an ultrasound reference.',
    library: 'library/gallbladder/metadata-cleanup-r01',
    source: source + 'reviews/teaching-assessments/target-risk/README.md',
    sourceLabel: 'Read the separate exterior and cutaway review',
    views: [{
      path: 'reviews/teaching-assessments/target-risk/views/gallbladder.webp',
      title: 'Related model · exterior and authored teaching cut',
      alt: 'Gallbladder model shown in multiple views, including its separately authored cutaway',
      caption: 'The authored wall and duct cue belong to this model study. The lesson samples the original label.',
    }],
  },
  {
    id: 'liver',
    title: 'Liver and surrounding anatomy',
    role: 'The liver provides the landmark against which to find the gallbladder.',
    finding: 'The assembly plates show the gross relationship in the shared case. The two teaching masks leave most surrounding tissues unlabelled.',
    source: source + 'assemblies/workshop-s1233/README.md',
    sourceLabel: 'Read the same-case assembly record',
    views: [
      { path: digestive + 'iso.webp', title: 'Isometric', alt: 'Oblique s1233 digestive assembly', caption: 'Matched view width 74.6 cm · teaching materials' },
      { path: digestive + 'ortho.webp', title: 'Anterior orthographic', alt: 'Anterior s1233 digestive assembly', caption: 'Matched view width 74.6 cm · teaching materials' },
    ],
  },
  {
    id: 'probe',
    title: 'Body locator and probe',
    role: 'The anterior atlas locates the probe at the right upper abdomen.',
    finding: 'The probe is a schematic marker. Its position on the atlas gives regional orientation, while the scan field is placed separately in s1233 coordinates. A registered exterior and recognizable probe can improve correspondence.',
    source: source + 'body/2d-v4/whole-body-anatomy-v4-spatial/README.md',
    sourceLabel: 'Read the regional atlas record',
    locator: true,
  },
  {
    id: 'scan',
    title: 'Section and synthetic grayscale',
    role: 'Both views use the same tissue labels, field and orientation.',
    finding: 'The section shows two sampled labels. The grayscale adds illustrative brightness, texture and boundaries. The surrounding tissue and near field are stylized.',
    source: source + 'assemblies/workshop-s1233/inputs.json',
    sourceLabel: 'Open the pinned source-mask record',
    views: [
      abdomenTour.stops[0].section,
      abdomenTour.stops[0].grayscale,
    ],
    geometry: true,
  },
];

export function abdomenStopPath(stop) {
  return abdomenTourPath + '/' + stop.id;
}

export function abdomenPartPath(part, stop) {
  return ultrasoundAssets + '/' + part + '?from=' + stop.id;
}
