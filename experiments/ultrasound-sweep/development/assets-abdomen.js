// Teaching requirements of the modeled organ cases, mapped to inspectable
// references. A source mesh and the patient's missing finding are separate.
const hepatobiliary = ['ct:s1233:hepatobiliary', 'Hepatobiliary anatomy · s1233'];
const renal = ['ct:s1233:renal-model', 'Renal anatomy · s1233'];
const bladder = ['library/bladder/pelvic-base-r01', 'Bladder base and ureteral entries · HRA'];
const pancreaticRegions = ['library/pancreas/hra-female-context-r04', 'Pancreas and adjacent anatomy · HRA'];
const sweep = (key, part, legacyParts = [], referenceScope) => ({ source: 'sweep', key, part, legacyParts, referenceScope });
const gallery = (part, legacyParts = [], asset, referenceScope) => ({ source: 'gallery', part, legacyParts, asset, referenceScope });
const gap = (asset, part, label, missingReason, legacyParts = []) => ({
  status: 'missing', assetId: asset[0], assetLabel: asset[1], part, label, missingReason, legacyParts,
});
const rebuild = (...args) => ({ ...gap(...args), status: 'rebuild' });

const liver = sweep('liver', 'liver', [], 'Whole-organ reference. Separately selectable lobes are absent.');
const portal = sweep('portal-vein', 'portal_vein_and_splenic_vein', ['Main portal vein', 'Main portal vein wall'],
  'One combined portal and splenic vein segmentation. It supplies vascular locations and no separate wall, flow or spectral state.');
const ivc = sweep('ivc', 'inferior_vena_cava', ['IVC']);
const gallbladder = sweep('gallbladder', 'gallbladder', [], 'Whole gallbladder outline from a normal anatomy reference.');
const pancreas = sweep('pancreas', 'pancreas', [], 'Whole pancreatic outline supports head-to-tail location. Separately selectable regions use another source.');
const spleen = sweep('spleen', 'spleen', ['Spleen'], 'Whole splenic outline. Independent hilum uses an HRA reference.');
const kidneyScope = 'Whole kidney outline for location and outer contour. Independent HRA cortex and hilar entry anatomy are separate references.';
const rightKidney = sweep('kidney-right', 'kidney_right', ['Right kidney'], kidneyScope);
const leftKidney = sweep('kidney-left', 'kidney_left', ['Left kidney'], kidneyScope);
const aortic = ['ct:s1233:aortic-model', 'Aortic and iliac model · s1233'];
const aorta = sweep('aortic-screening', 'aorta', ['Aorta'],
  'The native segmented outer contour supplies location and orientation. It does not resolve wall thickness or a separate lumen.');
const aorticDetails = [
  gap(aortic, 'aortic-wall', 'Aortic wall', 'The native mask supplies the outer contour, without a separate wall mesh.'),
  gap(aortic, 'aortic-lumen', 'Aortic lumen', 'The outer arterial surface does not independently resolve the lumen.', ['Aortic lumen']),
];

const pancreatic = (part, aliases) => gallery('pancreas-' + part, aliases, pancreaticRegions,
  'Independently selectable static pancreatic region from the HRA source.');
const head = pancreatic('head', ['Pancreatic head']);
const body = pancreatic('body', ['Pancreatic body']);
const tail = pancreatic('tail', ['Pancreatic tail']);
const uncinate = pancreatic('uncinate', ['Uncinate process']);
const splenicHilum = gallery('splenic-hilum', ['Splenic hilum'], pancreaticRegions,
  'Hilar surface patch from the HRA source.');
const renalDetail = (side) => {
  const part = side.toLowerCase();
  const asset = ['library/kidney_' + part + '/teaching-economy-r01', side + ' renal landmarks · HRA'];
  return [
    gallery('kidney-' + part + '-cortex', [], asset, 'Static HRA cortex. It does not depict this case’s collecting system.'),
    gallery('kidney-' + part + '-hilum', [], asset, 'HRA hilar entry context. The renal sinus is a distinct requirement.'),
    gap(renal, part + '-renal-sinus', side + ' renal sinus',
      'The whole-organ CT exterior and HRA hilum supply location but no independently selectable renal sinus.', [side + ' renal sinus']),
  ];
};
const rightRenalDetail = renalDetail('Right');
const leftRenalDetail = renalDetail('Left');

const liverLobe = (side) => gap(hepatobiliary, side.toLowerCase() + '-hepatic-lobe', side + ' hepatic lobe',
  'The delivered s1233 liver is a whole-organ mesh. Its lobes are not independently selectable.', [side + ' hepatic lobe']);
const gallWall = gap(hepatobiliary, 'gallbladder-wall', 'Gallbladder wall',
  'The original sweep supplies the organ outline. The wall is not a separate registered mesh.', ['Gallbladder wall']);
const gallLumen = gap(hepatobiliary, 'gallbladder-lumen', 'Gallbladder lumen',
  'The original sweep does not include an independently selectable lumen.', ['Gallbladder lumen']);
const gallstone = rebuild(['required:mobile-calculus', 'Mobile gallbladder calculus'],
  'mobile-calculus', 'Mobile calculus',
  'The worked case demonstrates a mobile calculus. No existing 3D donor reproduces the calculus or its change of position.', ['Mobile calculus']);
const cbd = [
  gallery('common-bile-duct', [], pancreaticRegions, 'Static external common bile duct from the HRA pancreatic region source.'),
  gap(pancreaticRegions, 'extrahepatic-duct-wall', 'Extrahepatic duct wall',
    'The HRA duct supplies its external course. A wall with distinct inner and outer contours is unavailable.', ['Extrahepatic duct walls']),
  gap(pancreaticRegions, 'extrahepatic-duct-lumen', 'Extrahepatic duct lumen',
    'No separately resolved lumen supports the worked inner-edge measurement.', ['Extrahepatic duct']),
];
const hepaticVein = rebuild(['required:hepatic-vein', 'Hepatic vein'],
  'hepatic-vein', 'Hepatic vein and caval junction',
  'Liver and cava meshes are available. An independently traced hepatic vein and its junction are unavailable.', ['Hepatic vein', 'Hepatic vein wall']);
const hydro = [
  ['dilated-renal-pelvis', 'Dilated renal pelvis'],
  ['upper-calyx', 'Upper calyx'],
  ['lower-calyx', 'Lower calyx'],
].map(([part, label]) => rebuild(['required:right-hydronephrosis', 'Dilated right collecting system'], part, label,
  'The available right kidney and hilar meshes show static anatomy. There is no source mesh for this case’s collecting-system dilation.', [label]));
const postvoidRenal = gap(renal, 'postvoid-collecting-system', 'Postvoid collecting-system state',
  'The normal renal mesh supplies location only. It does not represent persistence of dilation after voiding.');
const filling = gap(bladder, 'distended-bladder', 'Distended acquisition state',
  'The HRA pelvic-base asset shows static anatomy. It does not supply this case’s distended bladder or assessment of a distal lesion.',
  ['Bladder wall', 'Bladder lumen']);
const postvoidBladder = gap(bladder, 'postvoid-bladder', 'Postvoid bladder state',
  'There is one static HRA anatomy reference. No paired geometry represents the case’s prevoid and postvoid change.',
  ['Bladder wall', 'Bladder lumen']);
const pancreaticShadow = rebuild(['required:pancreatic-limited-window', 'Bowel gas interface'],
  'bowel-gas-and-shadow', 'Bowel gas interface across positions',
  'The limited-window tour needs a gas interface for the first view and the repositioned attempt. Its downstream B-mode use is to reproduce acoustic shadow over the pancreas.',
  ['Bowel gas']);

const lookup = {
  'abd-liver': [liver, portal, gallery('diaphragm', ['Diaphragm']), liverLobe('Right')],
  'liver-trans': [liver, portal, gallery('diaphragm', ['Diaphragm']), liverLobe('Right')],
  'abd-left-liver': [liver, portal, liverLobe('Left')],
  'abd-portal-doppler': [portal, liver],
  'abd-hepatic-vein-doppler': [ivc, liver, hepaticVein],
  'abd-gb': [gallbladder, gallWall, gallLumen],
  'abd-gb-short': [gallbladder, gallWall, gallLumen],
  'gb-short-limited-visit': [gallbladder, gallWall, gallLumen],
  'biliary-stone-supine': [gallbladder, gallWall, gallLumen, gallstone],
  'biliary-stone-transverse': [gallbladder, gallWall, gallLumen, gallstone],
  'biliary-stone-roll': [gallbladder, gallWall, gallLumen, gallstone],
  'abd-cbd': [portal, liver, ...cbd],
  'abd-pancreas': [pancreas, portal, head, body, uncinate],
  'pancreatic-head': [pancreas, portal, head, uncinate],
  'abd-tail': [pancreas, spleen, portal, tail, splenicHilum],
  'abd-pancreas-limited': [pancreas, portal, head, body, tail, pancreaticShadow],
  'pancreas-retry': [pancreas, portal, head, body, tail, pancreaticShadow],
  'abd-spleen': [spleen, leftKidney],
  'spleen-trans': [spleen, portal, splenicHilum],
  'abd-right-kidney': [rightKidney, liver, ...rightRenalDetail],
  'abd-right-kidney-trans': [rightKidney, liver, ...rightRenalDetail],
  'right-renal-trans': [rightKidney, liver, ...rightRenalDetail],
  'abd-left-kidney': [leftKidney, spleen, ...leftRenalDetail],
  'abd-left-kidney-trans': [leftKidney, spleen, ...leftRenalDetail],
  'left-renal-trans': [leftKidney, spleen, ...leftRenalDetail],
  'renal-right-hydro': [rightKidney, ...rightRenalDetail, ...hydro],
  'renal-right-hydro-trans': [rightKidney, ...rightRenalDetail, ...hydro],
  'renal-right-postvoid': [rightKidney, ...rightRenalDetail, ...hydro, postvoidRenal],
  'renal-bladder': [gallery('dome'), gallery('base'), gallery('neck'), gallery('trigone'), filling],
  'renal-bladder-sagittal': [gallery('dome'), gallery('base'), gallery('neck'), gallery('trigone'), filling],
  'bladder-uvj': [gallery('base'), gallery('trigone'), gallery('left-ureter'), gallery('right-ureter'),
    gallery('left-ureteral-orifice', ['Left UVJ']), gallery('right-ureteral-orifice', ['Right UVJ']), filling],
  'bladder-postvoid': [gallery('dome'), gallery('base'), gallery('neck'), gallery('trigone'), postvoidBladder],
  'abd-vessels': [aorta, ivc, ...aorticDetails],
  'aorta-long': [aorta, ivc, ...aorticDetails],
  'ivc-long': [ivc, liver, hepaticVein],
};

export const abdomenReferenceNotice =
  'Reference anatomy from a separate source. These meshes remain in their original source coordinates and are not registered to the worked case or its scan.';

export function abdomenRequirements(chapter) {
  const requirements = lookup[chapter];
  if (!requirements) return [rebuild(['required:unmapped-abdomen', 'Unmapped anatomy'],
    'unmapped', 'Anatomy requirements unavailable', 'This chapter has no mapped source anatomy yet.')];
  const context = requirements.find(({ source }) => source === 'sweep');
  return context ? [...requirements, sweep(context.key, 'torso', ['Patient exterior'])] : requirements;
}

export function missingDonor(reference, reason, identity) {
  const asset = reference.part === 'diaphragm' ? ['library/diaphragm/normal-pack-r02', 'Diaphragm · Z-Anatomy']
    : reference.source === 'gallery' ? bladder : reference.part === 'torso'
    ? ['library/skin', 'Body envelope · BodyParts3D']
    : ['required:' + reference.key, reference.key[0].toUpperCase() + reference.key.slice(1).replaceAll('-', ' ')];
  const name = reference.part === 'torso' ? 'Patient exterior' : reference.part.replace(/[-_]/g, ' ');
  return gap(identity ? [identity.assetId, identity.assetLabel] : reference.asset ?? asset,
    reference.part, identity?.partLabel ?? name, reason, reference.legacyParts);
}
