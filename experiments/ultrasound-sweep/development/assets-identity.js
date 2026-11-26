// Asset identity follows the authored source or model. A mesh variant records
// exact delivered geometry separately from the case/chapter which uses it.
const atlas = { id: 'library/skin', label: 'Body envelope · BodyParts3D', revision: 'bp3d-envelope-r01' };
const skeletalAtlas = {
  id: 'atlas:skeleton', label: 'Skeletal atlas · BodyParts3D', revision: 'teaching-economy-r01',
};
const hra = { id: 'hra:3d-vh-f:skin', label: 'Female exterior · Human Reference Atlas' };
const maternal = { id: 'pregnancy:maternal-exterior', label: 'Maternal exterior models' };

export const regions = {
  abdomen: 'Abdomen', neck: 'Neck', breast: 'Breast & axilla', pregnancy: 'Pregnancy', heart: 'Heart',
};

export function regionFor(family) {
  const id = family?.toLowerCase() ?? '';
  if (/^pregnancy/.test(id)) return 'pregnancy';
  if (/^(neck|thyroid|carotid)/.test(id)) return 'neck';
  if (/^(breast|axilla)/.test(id)) return 'breast';
  if (/^(heart|echo|cardiac)/.test(id)) return 'heart';
  return 'abdomen';
}

const slug = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function exterior(row, config) {
  if (config?.exterior?.startsWith('authored-') || row.region === 'pregnancy') return maternal;
  if (config?.exterior?.startsWith('hra-') || row.region === 'breast') return hra;
  if (row.source !== 'sweep' || config?.exterior === 'fitted-atlas') return atlas;
  return { id: 'exterior:' + (config?.case ?? row.case), label: 'Case exterior' };
}

function modeledAsset(row) {
  const part = row.part.toLowerCase();
  if (row.family === 'aaa') {
    if (part === 'vein' || part.includes('cava')) return ['aaa:caval-model', 'Inferior vena cava model'];
    if (part.includes('vertebr')) return ['aaa:spinal-context', 'Spinal context'];
    return ['aaa:aortic-model', 'Aortic and iliac model'];
  }
  if (row.family === 'carotid') return ['case:cervical-vessels', 'Cervical vessel model'];
  if (row.region === 'heart') return ['case:adult-heart', 'Adult heart model'];
  if (row.region === 'pregnancy') {
    if (/placenta|cord/.test(part)) return ['pregnancy:placenta-cord', 'Placenta and cord model'];
    if (/fluid|uterus|cervix|adnexa|yolk|maternal|tubal/.test(part)) return ['pregnancy:gestational-context', 'Gestational and pelvic anatomy'];
    return ['pregnancy:fetal-anatomy', 'Fetal anatomy model'];
  }
  if (row.region === 'neck') {
    if (/carotid|jugular/.test(part)) return ['case:thyroid-neighbor-vessels', 'Thyroid neighbor vessels'];
    return ['case:thyroid', 'Thyroid and neck model'];
  }
  if (row.region === 'breast') {
    if (/axillar|lymph/.test(part)) return ['case:axillary-nodes', 'Axillary lymph node model'];
    return ['case:breast-tissue', 'Breast tissue model'];
  }
  if (/hepatic|liver/.test(part)) return ['case:hepatic-model', 'Liver model'];
  if (/kidney|renal|ureter|calyx|calice|hydroneph/.test(part)) return ['case:renal-model', 'Renal model'];
  if (/gallbladder|calculus|bile|biliary/.test(part)) return ['case:biliary-model', 'Biliary model'];
  if (/pancrea/.test(part)) return ['case:pancreas-model', 'Pancreas model'];
  return ['case:abdominal-context', 'Abdominal model'];
}

function sweepAsset(row, config) {
  if (row.region === 'pregnancy' || row.region === 'heart') return modeledAsset(row);
  if (row.region === 'breast') {
    return /axillar|lymph/.test(row.part)
      ? ['sweep:hra:axillary-anatomy', 'HRA-based axillary anatomy']
      : ['sweep:hra:breast-tissue', 'HRA-based breast tissue'];
  }
  const part = row.part.toLowerCase();
  const subject = config.case ?? 's1233';
  if (/^thyroid|isthmus/.test(part)) return ['ct:' + subject + ':thyroid', 'Thyroid · ' + subject];
  if (/carotid|jugular/.test(part)) return ['ct:' + subject + ':cervical-vessels', 'Cervical vessels · ' + subject];
  if (/aorta|iliac/.test(part)) return ['ct:' + subject + ':aortic-model', 'Aortic and iliac model · ' + subject];
  if (/liver|gallbladder|portal/.test(part)) return ['ct:' + subject + ':hepatobiliary', 'Hepatobiliary anatomy · ' + subject];
  if (/kidney|renal/.test(part)) return ['ct:' + subject + ':renal-model', 'Renal anatomy · ' + subject];
  return ['ct:' + subject + ':' + slug(row.part), row.label + ' · ' + subject];
}

export function classifyAsset(row, skin, config) {
  if (skin) {
    const asset = exterior(row, config);
    const whole = /^(torso|(?:patient|chest|maternal) exterior)$/i.test(row.part);
    return { assetId: asset.id, assetLabel: asset.label, assetRevision: asset.revision,
      partId: whole ? 'exterior' : slug(row.part), partLabel: whole ? 'Patient exterior' : row.label };
  }
  const [assetId, assetLabel] = row.region === 'heart' && /rib cage|costal cartilage/i.test(row.part)
    ? [skeletalAtlas.id, skeletalAtlas.label]
    : row.source === 'sweep' ? sweepAsset(row, config) : modeledAsset(row);
  const wall = row.family === 'carotid' && /^(left|right) (CCA|ICA|ECA|IJV|VA)$/i.test(row.part);
  const aliases = row.region === 'pregnancy'
    ? { cord: 'umbilical-cord', fetus: 'fetal-surface' } : {};
  let partId = slug(row.part);
  if (/^pregnancy-early/.test(row.family) && partId === 'fetal-surface') partId = 'embryo';
  partId = aliases[partId] ?? partId;
  return {
    assetId, assetLabel,
    assetRevision: assetId === skeletalAtlas.id ? skeletalAtlas.revision : undefined,
    partId: partId + (wall ? '-wall' : ''),
    partLabel: row.label + (wall ? ' wall' : ''),
  };
}

const linearIdentity = [1, 0, 0, 0, 1, 0, 0, 0, 1];

// Millimetres rounded to a micrometre. Remove translation by taking every
// position relative to the first vertex. Do not normalize orientation, size,
// winding, or indexing. These can distinguish real sides and deformations.
export async function geometryDigest(count, vertices, indexCount, indices, linear = linearIdentity) {
  const bytes = new ArrayBuffer((3 + count * 3 + indexCount) * 4);
  const data = new DataView(bytes);
  data.setUint32(0, 1, true);
  data.setUint32(4, count, true);
  data.setUint32(8, indexCount, true);
  const x0 = vertices(0, 0), y0 = vertices(0, 1), z0 = vertices(0, 2);
  let offset = 12;
  for (let vertex = 0; vertex < count; vertex++) {
    const x = vertices(vertex, 0) - x0;
    const y = vertices(vertex, 1) - y0;
    const z = vertices(vertex, 2) - z0;
    for (let axis = 0; axis < 3; axis++, offset += 4) {
      const j = axis * 3;
      const units = (linear[j] * x + linear[j + 1] * y + linear[j + 2] * z) * 1000;
      data.setInt32(offset, Math.round(units), true);
    }
  }
  for (let i = 0; i < indexCount; i++, offset += 4) data.setUint32(offset, indices(i), true);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
}
