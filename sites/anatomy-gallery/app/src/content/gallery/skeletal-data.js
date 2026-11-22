export const skeletalPath = 'use-cases/skeletal-relationships';
export const skeletalDate = '2026-10-23';
export const skeletalReview = 'reviews/skeletal_teaching/' + skeletalDate + '/record.json';
export const skeletalPackage = 'assemblies/skeletal-teaching/README.md';
export const skeletalSource = 'https://github.com/qianyizhang/med-assets/blob/503c33f1dadf403faaec373c1a11a8b40dc523d6/';
export const skeletalCredit = 'BodyParts3D © The Database Center for Life Science';
export const skeletalLicense = 'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html';

export const skeletalStops = [
  {
    id: 'second-costal',
    sourceId: 'second-costal',
    title: 'Second costal cartilage in skeletal context',
    zh: '第二肋软骨及骨架参照',
    cue: 'Find the two blue cartilage segments between the selected second ribs and the sternum. In the side view, follow one rib back toward T1 and T2.',
    finding: 'The dated static review retains both second costal cartilages with their selected ribs, sternum and T1/T2.',
    limit: 'The assembly covers the second costal cartilages and selected bones. All-rib coverage, complete cartilage anatomy and joint behavior are outside its scope.',
    captions: [
      'The two cartilage segments flank the sternum at the anterior ends of the second ribs.',
      'The sternum is anterior, with the selected thoracic vertebrae at the back of the view.',
      'The oblique view shows the silhouettes and coarse seams with a single neutral material.',
      'Diagnostic blue distinguishes the same selected cartilage segments in the oblique view.',
    ],
  },
  {
    id: 'l3-l4-disc',
    sourceId: 'L3-L4-disc',
    title: 'L3–L4 disc: gross exterior relationship',
    zh: 'L3–L4 椎间盘：大体外部关系',
    cue: 'Find the blue disc between L3 above and L4 below. Use the side view to locate the disc between the vertebral bodies, anterior to the posterior processes.',
    finding: 'The dated static review retains the exterior disc between the two source vertebrae.',
    limit: 'This exterior study covers gross placement. Annulus and nucleus anatomy, facet contact, loads and motion are outside its scope.',
    captions: [
      'The exterior disc is the band between L3 and L4.',
      'The disc sits between the vertebral bodies, anterior to the posterior processes.',
      'The oblique neutral view shows the exterior shapes and coarse interfaces.',
      'Diagnostic blue identifies the same exterior disc in the oblique view.',
    ],
  },
];

export const skeletalLibraryPath = (id) => 'library/cartilage-assembly/' + id + '-' + skeletalDate;
export const skeletalExportPath = (sourceId) => 'assemblies/skeletal-teaching/' + skeletalDate + '/' + sourceId + '.glb';
export const skeletalPlatePath = (sourceId, number) => skeletalReview.replace('record.json', sourceId + '-' + number + '.webp');
