import { adrenalLibrary } from './adrenal-study.js';
import assessments from './reviewed-entries.json' with { type: 'json' };
import { localModels, teachingScenes } from './local-models.js';
import {
  additionalLibraryRows, assetUrl, byPath, exactLibraryRecords, libraryId, libraryPath,
  portrait, rated, ratingProfile, revisions, salivary,
} from './catalog.js';

const ownerRoot = 'https://github.com/qianyizhang/med-assets/blob/503c33f1dadf403faaec373c1a11a8b40dc523d6/';
export const libraryAliases = { dental_specimens: 'uff_tomo1b' };

const cardiacAtlasStls = [...byPath.keys()].filter(
  (path) => path.startsWith('heart/Cardiac_Atlas/exports/STL_RAS_mm/') && path.endsWith('.stl'),
);
const nativeDeliveries = {
  'body-atlas': ['body/anatomy-workshop-r1/Anatomy_Workshop.blend'],
  breathing: ['body/breathing/Breathing_Assembly.blend'],
  'cardiac-static': ['heart/Cardiac_Atlas/Cardiac_Atlas.blend', ...cardiacAtlasStls],
  'cardiac-animated': ['heart/Cardiac_Atlas_Animated/Cardiac_Atlas_Animated_Source.blend'],
  blood_cell_study: ['models/blood_cell_study/source/blood-cell-authored-study-r05-public.blend'],
};

const parentExports = {
  'body-atlas': ['workshop-r1', 'Workshop r1 · original delivery',
    'Original independently viewable Workshop components and the shared editable scene. The components keep their imported attribution and coordinates.'],
  breathing: ['breathing-assembly', 'Breathing · original delivery',
    'Eleven independently delivered clips and their shared editable assembly. The four-second movement is illustrative.'],
  'cardiac-static': ['static-ed', 'Cardiac Atlas · end diastole',
    'The static clinical full view, cutaway and baked walls share the native scene. The individual STL surfaces use the documented ED RAS-mm frame.'],
  'cardiac-animated': ['repository-source', 'Cardiac Atlas · original authored animation',
    'The clinical, tissue and cutaway views share the editable animated source and its authored loop.'],
};

const fittedHeart = {
  family: 'cardiac-animated',
  revision: 'fitted-canonical',
  library: 'library/cardiac-animated/fitted-canonical',
  title: 'Cardiac Atlas · fitted Site animation',
  finding: 'Historical animation fitted for the heart imaging Site. The retained motion samples agree with the repository-source animation, which has a different digest and node count.',
  limit: 'The exact bytes and fitting transforms are unavailable to the Library. The sample comparison does not establish replacement applicability.',
  record: ownerRoot + 'reviews/heart_exterior/2026-10-30-native-visibility-r01/provenance-and-applicability.md',
  status: 'Historical export unavailable',
  exports: [{
    path: 'body/3d/assets/motion/heart_animated_clinical.glb',
    name: 'heart_animated_clinical.glb',
    bytes: 8180452,
    sha256: '17b26d1459c0fbbbc71d051452c4074d1237683ffe02c1a8021d7ac83583857a',
    unavailable: 'Exact fitted GLB unavailable in the Library. No tracked repository export was identified.',
  }],
};

const exactNotes = {
  'cardiac-exterior/static-opaque-exterior': {
    title: 'Static opaque exterior · Workshop derivative',
    status: 'Original static delivery · r01',
    record: 'heart/exterior-presentation-r01/README.md',
    finding: 'Opaque visibility correction derived from Workshop heart_detailed.glb. The source-tagged internal and cutaway nodes are excluded from the displayed scene.',
    limit: 'Presentation correction only. Vessel joins and visible gaps remain.',
  },
  'cardiac-exterior/animated-source-opaque-exterior': {
    title: 'Animated opaque exterior · repository-source derivative',
    status: 'Repository-source animation',
    record: 'heart/exterior-presentation-r01/README.md',
    finding: 'Opaque visibility correction derived from Heart_Clinical_Animated.glb. Retains the authored loop and 109 exterior channels.',
    limit: 'The separate fitted Site animation has a different identity.',
  },
  'heart/metadata-cleanup-r01': {
    record: 'models/heart/exports/metadata-cleanup-r01/README.md',
    finding: 'Metadata correction of the original Breathing heart shell. The one clip retains the source translation.',
    limit: 'Illustrative breathing motion of a surface. Cardiac contraction and internal anatomy are outside scope.',
  },
  'lymph-collecting-routes/source-context-r01': {
    record: 'models/lymph-collecting-routes/source-context-r01/README.md',
    finding: 'Seven selected routes reconstructed from the pinned source scene. The dimmed scaffold and body silhouette provide orientation.',
    limit: 'Editorial contour and source-named terminations. Physiological flow and body registration are unverified.',
  },
  'thyroid_ct_s0189/source-candidate-02': {
    finding: 'Source-frame case s0189 exterior retained as the reference for the illustrative exterior.',
    limit: 'Case-specific segmented surface with retained irregularities. No normative claim.',
  },
  'thyroid_ct_s0189/illustrative-exterior-r01': {
    finding: 'Sample-specific exterior with editorial smoothing of the superficial ridges.',
    limit: 'No healthy or normative claim. Exact same-case trachea is unavailable locally.',
  },
  'peripheral_nerves/sciatic-hip-r01': {
    record: 'reviews/peripheral_nerves/2026-10-30-sciatic-hip-r01/README.md',
  },
  'peripheral_nerves/ulnar-elbow-r01': {
    record: 'reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/README.md',
  },
};

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

function previewUrl(url) {
  const origin = 'https://med-assets-model-survey.landy123007.chatgpt.site';
  return url?.startsWith(origin + '/assets/') ? url.slice(origin.length) : url;
}

function exactRecord(row, revision, media, snapshot) {
  const folder = media[0].path.slice(0, media[0].path.lastIndexOf('/'));
  const packageRecord = row.docs?.find((doc) => doc.path === folder + '/README.md');
  const references = media.flatMap((file) => file.recordReferences ?? []);
  const matchingRecord = references.find((ref) => ref.path.includes(revision)) ?? references[0];
  const note = exactNotes[row.id + '/' + revision];
  const parent = parentExports[row.id];
  const metadata = revision === 'metadata-cleanup-r01';
  const isOnlyExport = row.media.filter((file) => file.path.endsWith('.glb')).length === media.length;
  const matchedPreview = (row.previewIds ?? []).map((id) => snapshot.previewGallery?.[id])
    .find((preview) => preview && media.some((file) => file.sha256 === preview.sourceSha256));
  return {
    family: row.id,
    revision,
    library: 'library/' + row.id + '/' + revision,
    title: note?.title ?? parent?.[1] ?? row.label + ' · ' + revision,
    finding: note?.finding ?? parent?.[2] ?? (metadata
      ? 'Metadata correction of the original package export. Geometry and animation payload are retained.'
      : isOnlyExport ? row.use : ''),
    limit: note?.limit ?? (!metadata && isOnlyExport ? row.limit : ''),
    status: note?.status ?? (metadata ? 'Metadata-only alternative' : isOnlyExport ? row.state : undefined),
    record: note?.record ? ownerRoot + note.record
      : (parent ? row.evidence?.url : row.id === 'joints' ? packageRecord?.url
        : matchingRecord?.url ?? packageRecord?.url) ?? row.evidence?.url,
    exports: media.map((file) => byPath.get(file.path)),
    preview: previewUrl(matchedPreview?.image),
  };
}

function historyFor(row, snapshot) {
  const history = exactLibraryRecords.filter((record) => record.family === row.id);
  const namedPaths = new Set(history.flatMap((record) => record.exports.map((file) => file.path)));
  const groups = new Map();
  for (const file of row.media) {
    if (namedPaths.has(file.path)) continue;
    const asset = byPath.get(file.path);
    if (!asset || asset.sha256 !== file.sha256 || asset.bytes !== file.bytes) continue;
    const parts = file.path.split('/');
    const revision = parentExports[row.id]?.[0] ?? (row.id === 'cardiac-exterior'
      ? asset.name.slice(0, -'.glb'.length)
      : row.id === 'blood_cell_study' ? 'authored-r05' : parts.at(-2));
    if (!groups.has(revision)) groups.set(revision, []);
    groups.get(revision).push(file);
  }
  return [
    ...history,
    ...Array.from(groups, ([revision, media]) => exactRecord(row, revision, media, snapshot)),
    ...(row.id === fittedHeart.family ? [fittedHeart] : []),
  ];
}

function assessmentForFile(campaign, file) {
  const entry = campaign.get(file.path);
  return entry && entry.export.sha256 === file.sha256 && entry.export.bytes === file.bytes ? entry : undefined;
}

export function exactExportPath(record, file) {
  return file && record.exports.length > 1 && record.defaultFile && file.path !== record.defaultFile
    ? record.library + '?file=' + file.sha256 : record.library;
}

export function selectExactExport(record, digest) {
  if (!digest || !record) return record;
  const file = record.exports.find((entry) => entry.sha256 === digest);
  if (!file) return undefined;
  if (!record.assessment || record.assessment.export.path === file.path) return record;
  const assessment = record.fileAssessments?.get(file.path);
  return { ...record, selectedFile: file, scene: undefined, assessment,
    previousAssessment: undefined, axes: assessment?.axes.map((axis) => axis.score),
    portrait: undefined, preview: assessment?.views[0]?.url };
}

function collectionRow(row, snapshot, authoredReviews, campaign, replacements, localPreview) {
  const listed = row.media ?? [];
  const native = (nativeDeliveries[row.id] ?? []).map((path) => byPath.get(path));
  const media = [...listed, ...native.filter((asset) => !listed.some((file) => file.path === asset.path))];
  const label = row.id === 'adrenals' ? 'Adrenal pair · BodyParts3D' : row.label;
  const local = localPreview && localModels.find((model) => model.family === row.id);
  const records = historyFor({ ...row, label, media }, snapshot);
  if (local) records.unshift(...localModels.filter((model) => model.family === row.id));

  const paths = new Set(records.flatMap((record) => record.exports.map((file) => file.path)));
  for (const assessment of replacements) {
    if ((!paths.has(assessment.target.baseline) && !paths.has(assessment.target.familyBaseline)) || paths.has(assessment.export.path)) continue;
    const file = { ...assessment.export, name: assessment.export.path.split('/').at(-1) };
    const revision = file.path.split('/').at(-2);
    if (records.some((record) => record.revision === revision)) {
      throw new Error('Teaching revision collides with an existing package: ' + file.path);
    }
    paths.add(file.path);
    records.unshift({ family: row.id, revision, library: 'library/' + row.id + '/' + revision,
      title: label + ' · ' + revision, finding: assessment.decision,
      status: 'Reviewed teaching export · Local preview', record: assessment.sources[0]?.url, exports: [file] });
  }
  const history = records.map((original) => {
    const study = localPreview && teachingScenes.find((model) => model.family === row.id && model.revision === original.revision
      && original.exports.some((file) => file.path === model.exports[0].path && file.sha256 === model.exports[0].sha256));
    const record = study
      ? { ...original, scene: study.scene, exports: [study.exports[0], ...original.exports.filter((f) => f.path !== study.exports[0].path)] }
      : original;
    const previous = authoredReviews.get(record.library);
    const fileAssessments = new Map();
    for (const file of record.exports) {
      const current = assessmentForFile(campaign, file)
        ?? (file.path === previous?.export.path && file.sha256 === previous.export.sha256 ? previous : undefined);
      if (current) fileAssessments.set(file.path, current);
    }
    const available = [...fileAssessments.values()];
    const assessment = available.find((entry) => entry.maintained) ?? available[0];
    if (!assessment) return record;
    const previousMatch = previous && assessment.export.path === previous.export.path
      && assessment.export.sha256 === previous.export.sha256;
    const witness = assessment.views[0];
    return {
      ...record,
      record: assessment.sources?.find((source) => record.recordPath && source.path === record.recordPath)?.url ?? record.record,
      assessment, fileAssessments, defaultFile: assessment.export.path,
      previousAssessment: previousMatch && previous !== assessment ? previous : undefined,
      axes: assessment.axes.map((axis) => axis.score),
      preview: record.preview ?? witness?.url ?? (witness && assetUrl(byPath.get(witness.path))),
    };
  });
  const recommended = history.find((record) => record.assessment?.target && record.assessment.maintained)
    ?? (local ? history.find((record) => record.revision === local.revision) : undefined);
  const assessed = history.find((record) => record.assessment);
  const files = [...new Map([...media, ...history.flatMap((record) => record.exports)].map((file) => [file.path, file])).values()];
  return {
    ...row, label, media, history, recommended,
    state: recommended?.status ?? row.state,
    aliases: row.id === 'uff_tomo1b' ? ['dental_specimens'] : [],
    kind: row.product ? 'Product or study' : 'Model family',
    fileCount: files.filter((file) => !file.unavailable).length,
    formats: [...new Set(files.map((file) => file.path.split('.').at(-1).toUpperCase()))],
    ...ratingProfile((recommended ?? assessed)?.axes),
    path: recommended?.library ?? row.exactLibrary ?? assessed?.library
      ?? (row.id === salivary.family ? salivary.library : 'library/' + encodeURIComponent(row.id)),
    selectedRevision: recommended?.revision ?? assessed?.revision,
    image: recommended?.preview ?? row.image ?? assessed?.preview ?? previewUrl(snapshot.previewGallery?.[row.previewIds?.[0]]?.thumb),
  };
}

export function libraryRows(snapshot, teachingReview, { localPreview = false } = {}) {
  const authoredReviews = new Map(teachingReview?.assessments.map((assessment) => [assessment.route, assessment]));
  const campaign = new Map((localPreview ? teachingReview?.campaign ?? [] : [])
    .map((assessment) => [assessment.export.path, assessment]));
  const replacements = [...campaign.values()].filter((entry) => entry.target && entry.target.baseline !== entry.export.path);
  const adrenalAssessment = (revision) => assessmentForFile(campaign, revisions[revision]);
  return [
    {
      id: libraryId,
      label: adrenalLibrary.label,
      system: adrenalLibrary.system,
      purpose: adrenalLibrary.purpose,
      use: adrenalLibrary.use,
      kind: 'Revision series',
      state: 'Reviewed for regional localization',
      fileCount: Object.keys(revisions).length,
      formats: ['GLB'],
      ...ratingProfile(adrenalAssessment(adrenalLibrary.recommended)?.axes.map((axis) => axis.score) ?? rated[adrenalLibrary.recommended]),
      path: libraryPath(adrenalLibrary.recommended),
      image: portrait(adrenalLibrary.portrait),
      history: Object.entries(revisions).map(([revision, file]) => ({
        revision,
        library: libraryPath(revision),
        exports: [file],
        assessment: adrenalAssessment(revision),
        ...ratingProfile(adrenalAssessment(revision)?.axes.map((axis) => axis.score) ?? rated[revision]),
      })),
    },
    ...assessments.map((entry) => ({
      ...entry,
      assessment: assessmentForFile(campaign, byPath.get(entry.exportPath)),
      ...ratingProfile(assessmentForFile(campaign, byPath.get(entry.exportPath))?.axes.map((axis) => axis.score) ?? entry.axes),
      kind: 'Reviewed revision',
      state: 'Reviewed for teaching task',
      path: 'library/' + entry.id,
      image: assetUrl(byPath.get(entry.posterPath)),
      fileCount: 1,
      formats: ['GLB'],
      media: [byPath.get(entry.exportPath)],
      history: [],
    })),
    ...[...snapshot.queries.model_survey.rows, ...snapshot.queries.products.rows, ...additionalLibraryRows]
      .filter((row) => !Object.hasOwn(libraryAliases, row.id))
      .map((row) => collectionRow(row, snapshot, authoredReviews, campaign, replacements, localPreview)),
  ];
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
  const exact = selectedFile ? selectExactExport(record, selectedFile.sha256) : record;
  return {
    ...row,
    ...ratingProfile(exact.axes),
    state: record.status ?? (exact.axes?.some((value) => value != null) ? 'Reviewed for teaching task' : 'Indexed revision'),
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
