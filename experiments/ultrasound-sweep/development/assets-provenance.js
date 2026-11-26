// A teaching binding and the original construction of its source answer different questions.
const labels = {
  exact: 'Exact source reused', adapted: 'Existing asset adapted',
  'same-source': 'Separately derived from source data', authored: 'Independently authored',
  unresolved: 'Unresolved provenance',
};
const repo = 'https://github.com/qianyizhang/med-assets/blob/main/';
const recipes = repo + 'experiments/ultrasound-sweep/';
const ctAbdomen = new Set(['gallbladder', 'liver', 'portal-vein', 'pancreas', 'spleen', 'kidney-left', 'kidney-right', 'aorta', 'ivc', 'aortic-screening']);
const hraMammary = new Set(['mammary_lobes', 'lactiferous_ducts', 'breast_fat', 'areola', 'nipple', 'suspensory_ligaments']);
let sweepFiles = {};
let recipeHashes = {};
let caseOwners = new Map();

export function setProvenanceInventory(manifest) {
  sweepFiles = manifest?.sweepHashes ?? {};
  recipeHashes = manifest?.recipeHashes ?? {};
  caseOwners = new Map((manifest?.cases ?? []).map(c => [c.id, c.owner]));
}

function fact(kind, source, revision, evidence, url) {
  return { kind, label: labels[kind], source, revision: revision || 'Revision unresolved', evidence, url };
}

function sweepOrigin(row) {
  const id = row.case;
  const part = row.part;
  const file = sweepFiles[id]?.[part];
  const version = file && 'Delivered file SHA-256 · ' + file;
  if (part === 'torso' && (row.assetId === 'library/skin' || ctAbdomen.has(id) || /^(thyroid|carotid)-/.test(id))) {
    return fact('adapted', 'BodyParts3D body envelope', 'bp3d-envelope-r01',
      'The sweep fits the atlas exterior to its subject and probe window.',
      recipes + (ctAbdomen.has(id) ? 'display_body.py' : 'display_neck.py'));
  }
  if (/^(breast|axilla)/.test(id)) {
    if (part === 'torso') return fact('adapted', 'HRA female skin', 'v1.3',
      'The recipe selects the regional skin; the axilla recipe also poses the upper arm.',
      recipes + (id === 'axilla' ? 'axilla_anatomy.py' : 'breast_anatomy.py'));
    if (hraMammary.has(part)) return fact('adapted', 'Gallery mammary anatomy · HRA', 'teaching-economy-r01',
      'The sweep packs named bilateral surfaces together. The duct binding includes locally capped tips.',
      recipes + 'breast_anatomy.py');
    return fact('authored', id === 'axilla' ? 'Axillary teaching model' : 'Breast teaching layers', version,
      'The recipe constructs this teaching surface in the mammary or axillary reference frame.',
      recipes + (id === 'axilla' ? 'axilla_anatomy.py' : 'build_breast.py'));
  }
  if (ctAbdomen.has(id) || /^(thyroid|carotid)-/.test(id)) {
    const neck = !ctAbdomen.has(id);
    const recipe = neck ? (id.startsWith('thyroid') ? 'build_thyroid.py' : 'build_carotid.py')
      : id === 'aortic-screening' ? 'build_aortic_screening.py' : id === 'gallbladder' ? 'prepare_scenes.py' : 'build_abdomen.py';
    return fact('same-source', 'TotalSegmentator · ' + (neck ? 's1127' : 's1233'), version,
      part === 'internal_jugular_vein_right' ? 'The right jugular was traced separately in the s1127 contrast CT.'
        : 'The sweep derives this surface from CT labels. Other meshes based on these data may have different contours and topology.', recipes + recipe);
  }
  if (id.startsWith('pregnancy-')) return fact('authored', 'Stage-specific pregnancy sweep anatomy', version,
    'The original sweep generates the anatomy at its named gestational stage.',
    recipes + (id === 'pregnancy-early' ? 'build_early_pregnancy.py' : /pregnancy-(mid|late)/.test(id) ? 'build_gestational.py' : 'build_pregnancy.py'));
  return fact('unresolved', row.title || row.label || id, version, 'A traceable source recipe is still needed.', row.url);
}

export function bindingProvenance(row) {
  if (row.source === 'requirement') return fact('unresolved', 'No mesh bound', undefined,
    row.missingReason || 'This requirement has no identified geometry.', undefined);
  if (row.donor) {
    const donor = row.donor;
    if (donor.source === 'gallery') return fact('exact', (donor.label || row.assetLabel) + ' · ' + (row.sourceNode || donor.part),
      donor.assetRevision || row.assetRevision,
      'Named GLB surface from the pinned export, transferred with its indexed triangles and physical positions.' +
        (row.sourceSha256 ? ' Source GLB SHA-256 · ' + row.sourceSha256 : ''), donor.url);
    const origin = sweepOrigin(donor);
    const digest = sweepFiles[donor.case]?.[donor.part];
    return { ...fact('exact', (donor.label || donor.case) + ' · ' + donor.part,
      digest ? 'Delivered file SHA-256 · ' + digest : donor.assetRevision,
      'The teaching binding points to the original sweep mesh at the same scale.', donor.url), origin };
  }
  if (row.source === 'sweep') return sweepOrigin(row);
  const owner = caseOwners.get(row.case);
  const recipe = recipeHashes[owner];
  const revision = recipe && 'Case recipe SHA-256 · ' + recipe;
  if (row.source === 'aaa') return fact('authored', 'AAA teaching case · ' + row.part, revision,
    'The acquisition pack places the authored vascular model against the registered native aorta.', recipes + 'aaa_acquisition.py');
  if (row.family === 'echo') {
    if (/rib cage|costal cartilage|chest exterior/i.test(row.part)) return fact('adapted', 'BodyParts3D thoracic anatomy',
      /exterior/i.test(row.part) ? 'bp3d-envelope-r01' : 'teaching-economy-r01',
      'The thoracic crop and skeletal packing recipe prepare the cardiac reference frame.', recipes + 'cardiac/torso/build_torso.py');
    return fact('authored', 'Cardiac cycle teaching model', revision, 'The authored heart geometry is sampled at the chapter’s evidence frame.', recipes + 'cardiac/heart-geometry.js');
  }
  if (row.referenceKind === 'retained' && owner) {
    if (row.family?.startsWith('pregnancy-') && row.part === 'Fetal surface') {
      if (row.family === 'pregnancy-first' && row.case.endsWith('-abnormal')) {
        return fact('same-source', 'First-trimester stage model · case volume', revision,
          'The case samples the same authored stage model as the original sweep and reconstructs the fetal exterior from its case labels.',
          recipes + 'cases/pregnancy/build_playable.py');
      }
      return fact('adapted', 'Gestational stage anatomy · fetal exterior', revision,
        'The case fits the stage anatomy to its biometry. The recipe can reconstruct the exterior from sampled stage labels when the surface file is unavailable.',
        recipes + 'cases/pregnancy/playable-scene.js');
    }
    if (row.family === 'breast' && /fibroglandular|pectoral fascia|retromammary|chest wall/i.test(row.part))
      return fact('adapted', 'Breast sweep layer profiles', revision, 'The case uses sampled profiles of the original sweep layers to construct its regional teaching surfaces.', recipes + 'cases/organs/build-breast-profiles.py');
    return fact('authored', row.title + ' · ' + row.partLabel, revision,
      'Named surface constructed by the worked case recipe at the evidence frame.', recipes + 'cases/' + owner + '/playable-scene.js');
  }
  return fact('unresolved', row.assetLabel || row.title, row.assetRevision, 'The inventory has no verified construction or reuse relationship for this part.', row.url);
}
