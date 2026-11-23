import { assetUrl, ratingProfile } from './catalog.js';

export const libraryAliases = { dental_specimens: 'uff_tomo1b' };

const variantRoles = {
  'parathyroids_native.glb': 'Isolated source-named glands',
  'parathyroids_thyroid_context.glb': 'Glands with thyroid context',
  'diaphragm_z_native_static.glb': 'Isolated static source shell',
  'diaphragm_z_context_static.glb': 'Static source shell with context',
  'molar-support-v3.glb': 'Molar and supporting structures',
  'synthetic-pdl-v3.glb': 'Synthetic periodontal ligament',
  'glands-and-parotid-ducts.glb': 'Isolated gland and duct selection',
  'same-source-context.glb': 'Same-source localization context',
  'trachea-cutaway.glb': 'Sectioned wall and cartilages',
  'trachea-open.glb': 'Open airway exterior and lumen',
  'Cardiac_Atlas_Clinical_Cutaway_ED.glb': 'Static clinical cutaway',
  'Cardiac_Atlas_Clinical_Full_ED.glb': 'Static clinical full view',
  'Cardiac_Walls_Baked_PBR_ED.glb': 'Baked PBR wall study',
  'Heart_Clinical_Animated.glb': 'Animated clinical full view',
  'Heart_Cutaway_Animated.glb': 'Animated cutaway',
  'Heart_Tissue_Animated.glb': 'Animated tissue full view',
};

export function exportRole(file) {
  if (file.name.endsWith('.blend')) return 'Editable Blender source';
  if (file.name.endsWith('.stl')) return 'Surface export · ED RAS-mm';
  return variantRoles[file.name];
}

export function exactExportPath(record, file) {
  if (!file || file.path === (record.defaultFile ?? record.exports[0]?.path)) return record.library;
  const duplicates = record.exports.some(entry => entry.path !== file.path && entry.sha256 === file.sha256);
  return record.library + '?file=' + file.sha256 + (duplicates ? '&export=' + encodeURIComponent(file.path) : '');
}

export function selectExactExport(record, digest, path) {
  if (!digest || !record) return record;
  const matches = record.exports.filter(entry => entry.sha256 === digest);
  const file = path ? matches.find(entry => entry.path === path)
    : matches.find(entry => entry.path === record.defaultFile) ?? matches[0];
  if (!file) return undefined;
  if (record.defaultFile === file.path || record.exports.length === 1) return record;
  if (!record.defaultFile && file === record.exports[0]) return record;
  const assessment = record.fileAssessments?.get(file.path);
  return { ...record, selectedFile: file, scene: undefined, assessment, finding: assessment?.decision ?? record.finding,
    previousAssessment: undefined, axes: assessment?.axes.map((axis) => axis.score),
    portrait: undefined, preview: assessment?.views.find(view => view.path === assessment.teachingView)?.url ?? assessment?.views[0]?.url };
}

export function revisionStatus(record, recommended) {
  const status = record.status;
  if (record.library === recommended?.library) {
    if (!status) return 'Recommended';
    return status.startsWith('Recommended') ? status : 'Recommended · ' + status;
  }
  if (status?.startsWith('Recommended for ')) return 'Reviewed for ' + status.slice('Recommended for '.length);
  if (status?.startsWith('Recommended ')) {
    const former = status.slice('Recommended '.length);
    return former[0].toUpperCase() + former.slice(1);
  }
  return status;
}

export function selectLibraryRow(row, search) {
  if (!search) return row;
  const needle = search.toLowerCase();
  const shortRevision = /^r[0-9]+$/.test(needle);
  const matches = row.history.filter((record) => record.revision.toLowerCase() === needle
    || (shortRevision && record.revision.toLowerCase().endsWith('-' + needle))
    || record.exports.some((file) => file.name.toLowerCase() === needle
      || file.path.toLowerCase() === needle || file.sha256 === needle));
  if (matches.length !== 1) return row;
  const [record] = matches;
  const selectedFile = record.exports.find((file) =>
    [file.name, file.path, file.sha256].some((value) => value.toLowerCase() === needle));
  const exact = selectedFile ? selectExactExport(record, selectedFile.sha256, selectedFile.path) : record;
  return {
    ...row,
    ...ratingProfile(exact.axes),
    state: revisionStatus(record, row.recommended) ?? (exact.axes?.some((value) => value != null) ? 'Reviewed for teaching task' : 'Indexed revision'),
    path: exactExportPath(record, selectedFile),
    selectedRevision: record.revision,
    image: record.portrait ? assetUrl(record.portrait.asset) : record.preview,
  };
}

export function librarySearchText(row) {
  return [
    row.label, row.id, row.system, row.kind, row.purpose, row.state, row.use,
    ...row.formats, ...(row.aliases ?? []),
    ...(row.media ?? []).flatMap((file) => [file.path, file.sha256]),
    ...row.history.flatMap((record) => [
      record.title, record.revision,
      ...record.exports.flatMap((file) => [file.path, file.name, file.sha256]),
    ]),
  ].join(' ').toLowerCase();
}
