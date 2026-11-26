// Chapter targets point to exact packaged anatomy or to explicitly scoped
// retained geometry. A missing acquisition state remains a separate requirement.
const flatten = (items) => items.flat(Infinity);
const sweep = (key, ...parts) => parts.map((part) => ({ source: 'sweep', key, part }));
const gallery = (slug, ...parts) => parts.map((part) => ({ source: 'gallery', part, asset: ['library/' + slug, slug.replaceAll('_', ' ')] }));
const retained = (parts, referenceScope) => ({ source: 'retained', parts, referenceScope });
const gap = (id, part, label, missingReason, rebuild = false) => ({
  assetId: 'required:' + id, assetLabel: label, part, label, missingReason,
  status: rebuild ? 'rebuild' : 'missing',
});
const state = (category, id, label) => ({ source: 'acquisition-note', category, id, label });
const missingPart = (assetId, assetLabel, part, label, missingReason) => ({
  assetId, assetLabel, part, label, missingReason, status: 'missing',
});
const lymph = gallery('lymph_node', 'lymph-node-capsule', 'lymph-node-paracortex', 'lymph-node-medulla')
  .map((row) => ({ ...row, referenceScope: 'Generic lymph node tissue layers from an independent source. It supplies neither a regional placement nor the finding.' }));

function neck(entry, id) {
  if (entry.family === 'thyroid') {
    const side = id.includes('left') ? 'left' : 'right';
    if (/^thyroid-node(?:-left|-central)?$/.test(id)) {
      return [lymph, sweep('thyroid-' + side, 'thyroid_gland', 'trachea'),
        missingPart('library/lymph_node', 'Lymph node · HRA', id, 'Cervical node location', 'The normal gland and generic lymph node references have no registered cervical nodal levels.')];
    }
    if (!/^thyroid-(?:axial(?:-superior)?|right-long(?:-nodule)?|left-long|nodule-(?:trans|long)|long-limited|left-lower-retry)$/.test(id)) return;
    const nodule = entry.id === 'thyroid-nodule' && (id.includes('nodule') || id === 'thyroid-axial-superior');
    return [sweep('thyroid-' + side, 'thyroid_gland', 'trachea', 'common_carotid_artery_' + side),
      nodule ? gap('thyroid-suspicious-nodule', 'suspicious-margin-and-foci', 'Suspicious thyroid nodule',
        'The tour uses a modeled lesion. There is no independently inspectable nodule with the taught margin and echogenic foci.', true) : [],
      /limited|retry/.test(id) ? state('thyroid', id, 'Lower-pole coverage and repeat') : []];
  }
  const match = /^(right|left)-(transverse|cca-gray|bifurcation-gray|ica-gray|color|proximal-cca|distal-cca|proximal-ica|distal-ica|eca|vertebral|distal-ica-retry|distal-lumen|before|jet|beyond)$/.exec(id);
  if (!match) return;
  const [, side, view] = match;
  const upper = side[0].toUpperCase() + side.slice(1);
  const branch = view === 'eca' ? 'ECA' : view === 'vertebral' ? 'VA'
    : /ica|bifurcation|distal-lumen|before|jet|beyond|color/.test(view) ? 'ICA' : 'CCA';
  const plaque = entry.id === 'carotid-plaque' && side === 'right' && /ica|transverse|bifurcation|color|distal-lumen|before|jet|beyond/.test(view);
  return [
    sweep('carotid-' + side, 'common_carotid_artery_' + side),
    view === 'transverse' && side === 'right' ? sweep('carotid-right', 'internal_jugular_vein_right') : [],
    retained([upper + ' ' + branch, upper + ' ' + branch + ' lumen', ...(plaque ? ['Carotid plaque'] : [])],
      'Named vessel wall/lumen and plaque surfaces from the case model. Flow and stenosis measurements remain tied to the acquisition.'),
    branch !== 'CCA' ? missingPart('case:cervical-vessels', 'Cervical vessel model', side + '-' + branch.toLowerCase() + '-path',
      upper + ' ' + branch + ' reference path', 'The native CCA sweep does not independently segment this branch and its full course.') : [],
    !/transverse|gray|distal-lumen/.test(view) ? state('carotid', id, 'Flow or Doppler sample and angle') : [],
    view.includes('retry') ? state('carotid', 'distal-ica-visibility', 'Distal ICA coverage and repeat') : [],
  ];
}

function breast(entry, id) {
  const right = sweep('breast', 'mammary_lobes', 'breast_fat', 'retromammary_fat', 'pectoralis', 'chest_wall');
  const left = gallery('breasts_hra', 'breast-left-lobes', 'breast-left-fat', 'breast-left-ducts', 'breast-left-nipple', 'breast-left-areola');
  if (/^breast-screen-(?:map|(?:right|left)-[0-2])$/.test(id)) return [
    ...(id.includes('left') ? [left] : id === 'breast-screen-map' ? [right, left] : [right]),
    retained(['Fibroglandular tissue', 'Retromammary fat', 'Pectoral fascia', 'Chest wall'],
      'Named modeled tissue layers for depth comparison. This teaching geometry does not establish equivalent coverage in both breasts.')];
  if (/^breast-cyst-(radial|anti)$/.test(id)) return [left.filter(({ part }) => /ducts|nipple|areola/.test(part)),
    retained(['Anechoic simple cyst'], 'Assessed cyst geometry in the exact worked acquisition. Anechoic signal and enhancement are properties of the scan.'),
    state('breast', 'simple-cyst-characterization', 'Anechoic signal and posterior enhancement')];
  if (/^axillary-(?:node-(?:long|short|opposite)|tail-diagnostic)$/.test(id)) {
    const side = id.endsWith('opposite') ? 'Left' : 'Right';
    return [sweep('axilla', 'axillary_node', 'fatty_hilum'), lymph,
      retained([side + ' axillary cortex', side + ' fatty hilum',
        'Fibroglandular tail', 'Pectoral fascia'], 'Named worked-case surfaces. Cortical characterization still depends on the target plane.'),
      state('breast', id, id.includes('tail') ? 'Axillary-tail coverage' : 'Cortical thickness and hilar relationship')];
  }
  if (/^breast-(?:limited-adjacent|retro-limited(?:-repeat)?)$/.test(id)) return [left,
    state('breast', id, 'Retroareolar visualization and repeat')];
}

const pelvic = (...parts) => gallery('vagina_hra', ...parts);
const adnexa = (side) => gallery('ovaries', 'ovary-' + side, 'uterine-tube-' + side);
const abdomenBiometry = sweep('pregnancy-mid-abdomen', 'fetus', 'stomach', 'umbilical_vein', 'spine');
const headBiometry = sweep('pregnancy-mid-brain', 'fetus', 'calvarium', 'falx', 'cavum', 'thalami');
const midBrain = (...parts) => sweep('pregnancy-mid-brain', ...parts);
const midHeart = (...parts) => sweep('pregnancy-mid-heart', ...parts);
const midAbdomen = (...parts) => sweep('pregnancy-mid-abdomen', ...parts);
const limbs = (...parts) => sweep('pregnancy-mid-spine-limbs', ...parts);
const early = (...parts) => sweep('pregnancy-early', ...parts);
const first = (...parts) => sweep('pregnancy-fetus', ...parts);
const placenta = (...parts) => sweep('pregnancy-mid-placenta', ...parts);
const pregnancyTargets = {
  'ta-orientation': early('uterus', 'maternal_bladder'),
  'tv-location': early('uterus', 'gestational_rim', 'gestational_sac', 'yolk_sac'),
  'tv-crl': early('embryo', 'amnion'), 'embryonic-mmode': early('embryo', 'cardiac_region'),
  'left-adnexa': adnexa('left'), 'right-adnexa': adnexa('right'), 'right-adnexal-repeat': adnexa('right'),
  'tubal-measure': adnexa('right'), 'posterior-pelvis': pelvic('uterus-body', 'cervix', 'vagina', 'rectum'),
  plurality: first('uterus', 'fetus', 'amniotic_fluid'), crl: first('fetus'),
  nt: first('fetus', 'nuchal_space', 'nasal_bone'), 'first-mmode': first('fetus'),
  'axial-head': first('calvarium', 'falx', 'choroid_plexus'), 'first-abdomen': first('fetus'),
  'first-bladder': first('fetal_bladder'), 'first-cord': first('umbilical_cord'),
  'first-profile': first('fetus', 'nasal_bone'), 'first-spine': first('fetus', 'spinal_echoes'),
  'first-placenta': first('placenta', 'uterus'),
  'mid-overview': midBrain('uterus', 'fetus', 'amniotic_cavity'), 'mid-mmode': midHeart('heart', 'fetus'),
  'biometry-head': headBiometry, 'biometry-abdomen': abdomenBiometry, 'biometry-femur': limbs('femur'),
  transventricular: midBrain('calvarium', 'falx', 'ventricles', 'choroid', 'cavum', 'thalami'),
  'posterior-fossa': midBrain('cerebellum', 'cisterna_magna'),
  orbits: midBrain('orbits'), 'upper-lip': midBrain('upper_lip', 'nares'), profile: midBrain('fetus', 'nasal_bone'),
  'chest-diaphragm': midHeart('lungs', 'diaphragm', 'heart'),
  'four-chamber': midHeart('heart', 'left_atrium', 'right_atrium', 'left_ventricle', 'right_ventricle'),
  lvot: midHeart('left_ventricle', 'aortic_outflow'), rvot: midHeart('right_ventricle', 'pulmonary_outflow'),
  '3vv': midHeart('aortic_outflow', 'pulmonary_outflow', 'superior_vena_cava'),
  '3vt': midHeart('aortic_outflow', 'pulmonary_outflow', 'superior_vena_cava', 'trachea'),
  kidneys: midAbdomen('kidneys', 'renal_pelves'), bladder: midAbdomen('fetal_bladder', 'umbilical_arteries'),
  insertion: midAbdomen('fetus', 'cord', 'umbilical_vein'), 'omphalocele-sagittal': midAbdomen('cord'),
  'long-spine': limbs('spine'), 'axial-spine': limbs('spine'),
  'right-hand': limbs('hands'), 'left-hand': limbs('hands'), 'right-foot': limbs('feet'), 'left-foot': limbs('feet'),
  'mid-placenta': placenta('placenta', 'uterus'), 'mid-cervix': placenta('cervical_canal', 'maternal_bladder'),
  'placental-insertion': placenta('placenta', 'cord'),
  presentation: sweep('pregnancy-late-presentation', 'fetus', 'placenta', 'cervical_canal'),
  'late-placenta': [sweep('pregnancy-late-presentation', 'placenta', 'cervical_canal'),
    gallery('placenta', 'basal-plate', 'chorionic-plate')],
  'interval-growth': sweep('pregnancy-late-biometry', 'fetus', 'calvarium', 'femur'),
  ua: [sweep('pregnancy-late-cord', 'cord', 'umbilical_vein'),
    gallery('placenta', 'umbilical-artery-1', 'umbilical-artery-2', 'term-umbilical-vein', 'term-cord')],
};

function pregnancy(entry, id) {
  const stage = entry.id.split('-')[1];
  const isLate = stage === 'late';
  const key = id.replace(/-(?:retry|repeat|initial)$/, '');
  const target = /^limb-[0-3]$/.test(id) ? (stage === 'first' ? first('fetus') : limbs('fetus', Number(id.at(-1)) < 2 ? 'hands' : 'feet'))
    : key === 'fluid' ? (isLate ? sweep('pregnancy-late-presentation', 'amniotic_cavity', 'fetus', 'cord') : placenta('amniotic_cavity', 'fetus', 'cord'))
    : key === 'ac' || isLate && key === 'biometry-abdomen' ? sweep('pregnancy-late-biometry', 'fetus', 'stomach', 'umbilical_vein', 'spine')
    : isLate && key === 'biometry-head' ? sweep('pregnancy-late-biometry', 'calvarium', 'falx', 'cavum', 'thalami')
    : isLate && key === 'biometry-femur' ? sweep('pregnancy-late-biometry', 'femur')
    : pregnancyTargets[id] ?? pregnancyTargets[key];
  if (!target) return;
  const abnormal = entry.id.endsWith('-abnormal');
  const ectopic = abnormal && stage === 'early' && /right-adnexa|tubal-measure/.test(id);
  const unlocated = stage === 'early' && entry.id !== 'pregnancy-early-normal' && id === 'tv-location';
  const nt = abnormal && stage === 'first' && key === 'nt';
  const omphalocele = abnormal && stage === 'mid' && /insertion$|omphalocele/.test(id) && id !== 'placental-insertion';
  return [
    unlocated ? pelvic('uterus-body', 'cervix') : target,
    unlocated ? state('pregnancy', 'uterine-cavity-observation', 'Assessment of the uterine cavity',
      'Use the saved acquisition to review the absence of a demonstrated intrauterine sac. The atlas supplies pelvic landmarks only.') : [],
    ectopic && /right|tubal/.test(id) ? retained(['Yolk sac'], 'The exact modeled yolk-sac rim supports the worked view. The extraovarian relationship is task-specific.') : [],
    ectopic ? gap('right-tubal-ectopic-complex', 'extraovarian-sac-and-ovary', 'Right tubal ectopic relationship',
      'The retained yolk-sac rim and separate normal atlas do not document a reusable extraovarian sac and separate ipsilateral ovary in one source space.', true) : [],
    nt ? [retained(['Fetal surface'], 'Worked first-trimester fetal exterior poses the posterior neck for this view.'),
      gap('increased-nuchal-translucency', 'posterior-neck-space', 'Increased nuchal translucency',
        'The normal space and fetal exterior do not depict the widened posterior space and its boundary with the amnion.', true)] : [],
    omphalocele ? retained(['Omphalocele membrane', 'Herniated bowel', 'Umbilical cord'], 'Exact modeled mid-trimester finding and cord relationship used in the worked acquisition.') : [],
    abnormal && isLate && /biometry|growth/.test(id) ? retained(['Fetal surface'], 'Worked late-trimester growth variant. A single mesh cannot represent serial measurements.') : [],
    key === 'placental-insertion' ? gallery('placenta', 'term-cord', 'chorionic-plate') : [],
    key === 'mid-cervix' ? pelvic('internal-os', 'external-os', 'cervix') : [],
    id.includes('mmode') ? state('pregnancy', id, 'Cardiac motion and rate') : [],
    /fluid/.test(id) ? state('pregnancy', id, 'Cord-free deepest vertical pocket and caliper endpoints') : [],
    /crl|^nt|^biometry|^ac-|tubal-measure/.test(id) ? state('pregnancy', id, 'Measurement plane and caliper endpoints') : [],
    /^(ua|interval-growth)/.test(id) ? state('pregnancy', id, id.startsWith('ua') ? 'Umbilical artery spectral waveform' : 'Interval comparison of serial measurements') : [],
    /repeat|initial/.test(id) ? state('pregnancy', id + '-coverage', 'Visibility limits and repeat acquisition') : [],
  ];
}

function echo(id) {
  const views = {
    plax: /^(LV|LA|RV|Ao\/|Aortic valve)/, 'rv-inflow': /^(RA|RV|IVC\/)/,
    'rv-outflow': /^(RV|PA\/|Pulmonary valve)/, 'psax-av': /^(Aortic valve|Ao\/|RA|RV)/,
    'psax-mv': /^(LV|LA|RV)/, 'psax-papillary': /^(LV|RV)/, 'psax-apical': /^(LV|RV)/,
    a4c: /^(LV|LA|RV|RA)$/, a2c: /^(LV|LA)$/, a3c: /^(LV|LA|Ao\/|Aortic valve)/,
    a5c: /^(LV|LA|RV|RA|Ao\/|Aortic valve)/, 'rv-focused': /^(RV|RA)$/,
    'subcostal-4c': /^(LV|LA|RV|RA)$/, 'subcostal-ivc': /^(IVC\/|RA)/,
    'subcostal-sax': /^(LV|RV)$/, 'subcostal-aorta': /^DescAo\//,
    'suprasternal-arch': /^(Arch\/|Arch branches\/|DescAo\/)/, 'right-parasternal': /^(Ao\/|Aortic valve)/,
  };
  const match = /^(.+?)-(section|diameter|color-[a-z]+|doppler-[a-z]+)$/.exec(id);
  if (!match || !views[match[1]]) return;
  const [, view, acquisition] = match;
  return [retained(views[view], 'Named chambers, vessels or semilunar leaflets from the registered cardiac model at the saved frame.'),
    /mitral|psax-mv|a2c|a3c|a4c|plax/.test(id) ? missingPart('case:adult-heart', 'Adult heart model', 'mitral-leaflets', 'Mitral leaflet detail',
      'The registered torso model supplies adjacent chamber walls; its inspectable leaflet patches are aortic and pulmonary.') : [],
    /tricuspid|inflow|rv-focused|a4c/.test(id) ? missingPart('case:adult-heart', 'Adult heart model', 'tricuspid-leaflets', 'Tricuspid leaflet detail',
      'The registered torso model supplies right-heart context rather than individually selectable tricuspid leaflets.') : [],
    acquisition !== 'section' ? state('echo', id, acquisition === 'diameter' ? 'Aortic diameter and caliper endpoints'
      : acquisition.startsWith('color') ? 'Acquisition color map' : 'Doppler gate, alignment and spectrum') : []];
}

function aaa(entry, id) {
  if (!/^(?:proximal-aorta|mid-aorta|distal-aorta|iliac-bifurcation|(?:left|right)-iliac-(?:short|long)|(?:anterior-distal-attempt|lateral-distal-repeat)|sac-(?:maximum|long-axis))$/.test(id)) return;
  const iliac = id.includes('iliac');
  return [retained(['wall', 'lumen', 'vein', 'vertebrae'],
    'Registered vascular acquisition parts in this case. Wall and lumen are independently selectable where delivered.'),
    sweep('aortic-screening', iliac ? 'iliac_artery_left' : 'aorta', ...(iliac ? ['iliac_artery_right'] : ['inferior_vena_cava', 'vertebrae'])),
    state('aaa', id, id.includes('distal-attempt') || id.includes('repeat') ? 'Limited window and repeat acquisition'
      : /long/.test(id) ? 'Long-axis span, flow and caliper endpoints' : 'Outer-wall measurement and caliper endpoints'),
    entry.id === 'aaa-positive' && /sac|iliac/.test(id) ? missingPart('aaa:aortic-model', 'Aortic and iliac model', 'mural-thrombus', 'Separate mural thrombus boundary',
      'The registered model provides selectable wall and lumen, without an inspectable separate thrombus surface.') : []];
}

export function examRequirements(entry, chapter) {
  const resolver = { thyroid: neck, carotid: neck, breast, pregnancy, echo: (_, id) => echo(id), aaa }[entry.family.split('-')[0]];
  const result = resolver?.(entry, chapter.id);
  if (!result) throw Error('No anatomy requirements authored for ' + entry.id + '/' + chapter.id);
  return flatten(result);
}

export function selectsRetained(reference, part) {
  return reference.source === 'retained' &&
    (Array.isArray(reference.parts) ? reference.parts.includes(part) : reference.parts.test(part));
}
