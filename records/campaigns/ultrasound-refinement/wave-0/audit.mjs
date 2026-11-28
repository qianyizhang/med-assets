import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const [delivery, stage, output, summaryOutput] = process.argv.slice(2);
assert(delivery && stage && output, 'Pass the full delivery, its input staging tree, the full audit path, and an optional summary path.');
const root = pathToFileURL(resolve(delivery) + sep);
const repo = fileURLToPath(new URL('../../../../', import.meta.url));
const study = 'experiments/ultrasound-sweep/';
const git = (...args) => execFileSync('git', ['-C', repo, ...args], { encoding: 'utf8' }).trim();
const sha = raw => createHash('sha256').update(raw).digest('hex');
const read = path => readFileSync(new URL(path, root));
const json = path => JSON.parse(read(path));
const staged = path => readFileSync(resolve(stage, path));
const source = path => readFileSync(resolve(repo, path));
const sourceJSON = path => JSON.parse(source(path));
const load = path => import(new URL(path, root));
const packed = (path, name) => {
  const script = read(path).toString().trim();
  const prefix = 'const ' + name + ' = ';
  assert(script.startsWith(prefix) && script.endsWith(';'), path);
  return JSON.parse(script.slice(prefix.length, -1));
};
const fileIDs = new Map();
const fetched = [];
function file(path) {
  const key = relative(fileURLToPath(root), fileURLToPath(new URL(path, root)));
  assert(key && !key.startsWith('..'), path);
  if (!fileIDs.has(key)) {
    const raw = read(key);
    const identity = { path: key, sha256: sha(raw), bytes: raw.byteLength };
    if (/\.(mesh|raw)$/.test(key)) {
      const vertices = raw.readUInt32LE(0);
      const triangles = raw.readUInt32LE(4);
      assert(vertices && triangles && 8 + 12 * (vertices + triangles) === raw.byteLength, key);
      Object.assign(identity, { vertices, triangles });
    }
    fileIDs.set(key, identity);
  }
  return key;
}
globalThis.fetch = async url => {
  const path = file(new URL(url, root));
  fetched.push(path);
  return new Response(read(path));
};
globalThis.location = new URL('development/assets.html', root);
globalThis.abdomenTours = packed('abdomen-tours.js', 'abdomenTours');
const [{ abdomenRequirements }, { examRequirements, selectsRetained }, { meshParts }] = await Promise.all([
  load('development/assets-abdomen.js'),
  load('development/assets-exams.js'),
  load('development/assets-data.js'),
]);
const inventory = json('development/asset-inventory.json');
const assembly = sourceJSON('records/campaigns/ultrasound-refinement/wave-0/assembly.json');
git('diff', '--quiet', assembly.sourceRevision, '--', study, 'assemblies/workshop-s1233/inputs.json',
  'models/**/asset.record.json', 'lib/med_assets/ultrasound_review.py', 'docs/guides/asset-quality.md',
  ':(exclude,glob)experiments/ultrasound-sweep/**/*.md');
assert.equal(assembly.delivery.inventorySha256, sha(read('development/asset-inventory.json')));
assert.equal(assembly.delivery.sweepCatalogueSha256, sha(read('abdomen-tours.js')));
const references = packed('references.js', 'abdomenReferences');
const aaaReceiptPath = 'aaa-acquisitions/verification.json';
const aaaReceiptRaw = staged(aaaReceiptPath);
const aaaReceipt = JSON.parse(aaaReceiptRaw);
assert.equal(sha(aaaReceiptRaw), assembly.stage.registeredAaa.stageVerificationSha256);
assert.equal(aaaReceipt.recipeSha256, assembly.stage.registeredAaa.acquisitionRecipeSha256);
const aaaAcquisition = {
  stageReceipt: aaaReceiptPath, stageReceiptSha256: sha(aaaReceiptRaw),
  recipeSha256: aaaReceipt.recipeSha256, ctSha256: aaaReceipt.ctSha256,
  placements: aaaReceipt.placements, modelMmToSceneVoxels: aaaReceipt.modelMmToSceneVoxels,
};
function aaaFile(path) {
  const key = file('tours/aaa/' + path);
  assert.equal(fileIDs.get(key).sha256, aaaReceipt.files[path], key);
  return key;
}
const rubric = file('development/asset-rubric.md');
assert.equal(fileIDs.get(rubric).sha256, inventory.rubricHash);
assert.equal(inventory.rubricHash, sha(source('docs/guides/asset-quality.md')));
assert.equal(abdomenTours.length, 28);
assert.equal(inventory.cases.length, 32);
assert.equal(inventory.cases.reduce((n, c) => n + c.chapters.length, 0), 410);

const dispositions = {
  current: ['keep', 'Ultrasound workbench', 'Current task evidence supports the existing scope and rating.'],
  prior: ['hold', 'Ultrasound workbench', 'Repeat the named observation against the emitted identity before carrying the score forward.'],
  incomplete: ['hold', 'Ultrasound workbench', 'Supply the missing axis observation or bound witness for the exact task.'],
  model: ['keep-as-context-pending-task-review', 'Owning acquisition recipe', 'A task-specific review remains open. Establish fit, fidelity and readability before drawing teaching conclusions.'],
  'case-review': ['hold', 'Ultrasound workbench', 'The cited review covers the case part. Establish relevance and current evidence for this particular chapter.'],
  source: ['source/rebuild', 'Owning asset package and lesson', 'Supply a reference and show the decisive anatomy in the saved acquisition and its placed surface.'],
  reference: ['hold', 'Lesson placement owner', 'The donor is available in its own frame. Reuse in the scene requires an evidenced transform and a reader that consumes it.'],
  state: ['hold', 'Owning acquisition recipe', 'Verify the saved plane, signal, endpoints or movement for this task through the acquisition reader.'],
  gap: ['hold', 'Lesson and asset workbench', 'Resolve the stated gap in the owning reader and supply a task-specific witness.'],
};

function native(ref) {
  const record = sourceJSON(ref.record);
  assert.equal(record.assetId, ref.asset);
  const revision = record.revisions.find(r => r.revisionId === ref.revision);
  const exported = revision.exports.find(e => e.id === ref.export);
  assert(exported, JSON.stringify(ref));
  return {
    key: ref.asset + '@' + ref.revision + ':' + ref.export,
    record: ref.record,
    revisionStatus: revision.status,
    frame: revision.frame,
    sourceIds: revision.sourceIds,
    path: exported.path,
    sha256: exported.sha256,
    bytes: exported.bytes,
    ...(exported.voxelGrid && { voxelGrid: exported.voxelGrid }),
  };
}
const atlas = sourceJSON(study + 'exterior-atlas.json');
const donors = sourceJSON(study + 'gallery-reference-assets.json').donors;
const atlasSkin = native(atlas.skin);
const atlasSkeleton = native(atlas.skeleton);
const mammary = native(donors.find(d => d.slot === 'breasts_hra').ref);
const tracks = sourceJSON(study + 'abdomen-tracks.json');
const liverRef = tracks.sweeps.find(t => t.id === 'liver').sceneAssets.liver;
const liver = native({ ...liverRef, record: 'models/liver_s1233/asset.record.json' });
const sweepsById = new Map(abdomenTours.map(s => [s.id, s]));
const sides = ['aorta', 'aortic-screening', 'gallbladder', 'ivc', 'kidney-left', 'kidney-right', 'liver', 'pancreas', 'portal-vein', 'spleen'];
const mammaryParts = new Set(['mammary_lobes', 'breast_fat', 'lactiferous_ducts', 'nipple', 'areola']);
const pregnancyBuilder = id => id === 'pregnancy-early' ? 'build_early_pregnancy.py'
  : /^pregnancy-(mid|late)-/.test(id) ? 'build_gestational.py' : 'build_pregnancy.py';
const sweepPath = (config, name, base = root) => file(new URL(
  config.meshPaths?.[name] ?? new URL('scenes/' + name + '.mesh', new URL(config.assetRoot, base)), base));
const sourceModels = new Map();
const sourceID = data => {
  const key = JSON.stringify(data);
  if (!sourceModels.has(key)) sourceModels.set(key, 'source-' + (sourceModels.size + 1));
  return sourceModels.get(key);
};

function sweepSource(config, name) {
  const { id } = config;
  const owner = 'Original sweep recipe';
  const neck = /^(thyroid|carotid)-/.test(id);
  const breast = /^(breast|axilla)/.test(id);
  const pregnancy = id.startsWith('pregnancy-');
  const ct = neck || sides.includes(id);
  const caseId = config.case ?? (ct ? 's1233' : id);
  const frame = ct ? caseId + ' RAS-oriented voxel indices'
    : breast ? 'HRA-derived source, local right ' + (id === 'axilla' ? 'axilla' : 'mammary') + ' sweep voxels'
      : caseId + ' authored stage voxels';
  const scaleMm = config.voxelMm ?? 1.5;
  const builder = id === 'gallbladder' ? 'build_study.py'
    : id === 'aortic-screening' ? 'build_aortic_screening.py'
      : neck ? (id.startsWith('thyroid') ? 'build_thyroid.py' : 'build_carotid.py')
        : pregnancy ? pregnancyBuilder(id) : id === 'axilla' ? 'build_axilla.py'
          : breast ? 'build_breast.py' : 'build_abdomen.py';
  let representation = 'case-derived-mesh', input = 'TotalSegmentator ' + caseId + ' label mask';
  let recipe = builder, upstream;
  if (name === 'torso') {
    representation = 'adapted-external-mesh';
    if (breast) {
      input = 'HRA female skin v1.3 regional selection' + (id === 'axilla' ? ' and upper-arm posing' : '');
      recipe = id === 'axilla' ? 'axilla_anatomy.py' : 'breast_anatomy.py';
    } else if (pregnancy) {
      representation = 'procedural-mesh';
      input = 'Authored stage-specific maternal exterior';
    } else if (ct) {
      input = 'BodyParts3D exterior fitted to the CT probe window';
      upstream = atlasSkin.key;
      recipe = neck ? 'display_neck.py' : 'display_body.py';
    }
  } else if (breast && mammaryParts.has(name)) {
    representation = 'adapted-external-mesh';
    input = 'Bilateral HRA mammary parts in the sweep frame, with local changes as needed by the recipe';
    recipe = 'breast_anatomy.py';
    upstream = mammary.key;
  } else if (breast || pregnancy) {
    representation = 'procedural-mesh';
    input = pregnancy ? 'Authored pregnancy stage morphology' : 'Authored regional tissue and landmark model';
  } else if (name === 'internal_jugular_vein_right') {
    input = 'Right internal jugular vein independently traced from the s1127 contrast CT';
    recipe = 'carotid_vein.py';
  }
  const path = sweepPath(config, name);
  const identity = fileIDs.get(path);
  assert.equal(identity.sha256, inventory.sweepHashes[id][name], id + '/' + name);
  const directNative = id === 'liver' && name === 'liver' ? liver.key : undefined;
  if (directNative) {
    assert.equal(identity.sha256, liver.sha256);
    assert.equal(identity.bytes, liver.bytes);
  }
  return { path, representation, case: caseId, frame, mmPerSceneUnit: scaleMm,
    reader: study + 'study.js', recipe: study + recipe, input, owner,
    ...(upstream && { upstream }), ...(directNative && { directNative }) };
}

const donorRows = new Map(json('development/gallery-donors.json').map(row => [row.part, row]));
const nativeDonors = new Map(donors.map(d => [d.slot, native(d.ref)]));
function referenceSource(row) {
  const upstream = nativeDonors.get(row.assetId.split('/')[1]);
  assert.equal(upstream.sha256, row.sourceSha256);
  return { path: file(row.mesh), representation: 'external-reference-mesh', frame: row.sourceSpace,
    mmPerSceneUnit: row.scale, sourceNode: row.sourceNode, upstream: upstream.key, credit: row.credit,
    reader: study + 'development/assets-data.js', recipe: study + 'gallery_reference_sources.py',
    registration: 'Independent workbench reference in its source coordinates' };
}

const reviewInfo = [];
const reviewByTarget = new Map();
const target = (scope, caseId, part) => [scope, caseId, part].join('/');
const families = {};
for (const path of inventory.reviews) {
  const family = path.split('/')[1];
  const canonical = study + 'development/' + path;
  const document = sourceJSON(canonical);
  const built = json('development/' + path);
    const counters = { authored: 0, additionalUses: 0, historicalFourTopScores: 0, identityMatches: 0,
    current: 0, currentFourTopScores: 0, 'earlier-identity': 0, 'missing-evidence': 0,
    missingReadability: 0, used: 0 };
  let expanded = 0;
  for (const record of document.records) {
    const { additionalUses = [], ...primary } = record;
    const bindings = [primary, ...additionalUses.map(use => ({ ...primary, ...use }))];
    for (const binding of bindings) assert.deepEqual(built.records[expanded++], binding, path);
    const witnesses = [];
    const { comparison } = record;
    if (comparison) {
      for (const view of [comparison, ...comparison.views ?? []]) {
        for (const name of ['baseline', 'candidate', 'original']) {
          if (!view[name]) continue;
          const href = file('development/' + view[name]);
          const witness = fileIDs.get(href);
          assert.equal(witness.sha256, document.evidenceSha256[relative(dirname(path), view[name])]);
          if (!witnesses.includes(href)) witnesses.push(href);
        }
      }
    }
    const axes = ['fidelity', 'form', 'readability', 'economy'];
    const missingAxes = axes.filter(axis => !Number.isInteger(record.scores[axis]) || !record.scoreEvidence?.[axis]);
    const allTop = !missingAxes.length && axes.every(axis => record.scores[axis] === 4) && witnesses.length > 0;
    const emitted = record.source === 'sweep' ? inventory.sweepHashes[record.case]?.[record.part] : inventory.recipeHashes[family];
    const authored = record.source === 'sweep' ? record.meshSha256 : document.recipeHash;
    const identityMatches = emitted === authored && document.rubricHash === inventory.rubricHash;
    const currency = !identityMatches ? 'earlier-identity'
      : missingAxes.length || !witnesses.length ? 'missing-evidence' : 'current';
    const reviewID = family + '/' + counters.authored;
    counters.authored++;
    counters.additionalUses += additionalUses.length;
    counters.historicalFourTopScores += Number(allTop);
    counters.identityMatches += Number(identityMatches);
    counters[currency]++;
    counters.currentFourTopScores += Number(allTop && currency === 'current');
    counters.missingReadability += Number(missingAxes.includes('readability'));
    const item = {
      id: reviewID, path: canonical, source: record.source, case: record.case, chapter: record.chapter,
      part: record.part, task: record.task, reviewedOn: record.reviewedOn, reviewer: record.reviewer,
      revision: record.revision, binding: record.source === 'sweep' ? 'mesh-sha256' : 'family-recipe-sha256',
      authored, emitted, identityMatches, rubric: record.rubric, rubricSha256: document.rubricHash,
      currency, allTop, scores: record.scores, observations: record.scoreEvidence, missingAxes,
      witnesses, limits: record.note, additionalUses,
    };
    reviewInfo.push(item);
    for (const binding of bindings) {
      const key = target(binding.source, binding.case, binding.part);
      if (!reviewByTarget.has(key)) reviewByTarget.set(key, []);
      reviewByTarget.get(key).push({ review: item, chapter: binding.chapter, occurrence: binding.occurrence });
    }
  }
  assert.equal(expanded, built.records.length, path);
  families[family] = counters;
}

const usedReviews = new Set();
function reviewsAt(scope, caseId, chapter, part, occurrence = 1) {
  const bindings = (reviewByTarget.get(target(scope, caseId, part)) ?? [])
    .filter(row => row.chapter === chapter && (row.occurrence ?? 1) === occurrence).map(row => row.review);
  for (const review of bindings) usedReviews.add(review.id);
  return bindings;
}
function decision(reviews, fallback) {
  if (reviews.some(r => r.currency === 'current')) return 'current';
  if (reviews.some(r => r.currency === 'missing-evidence')) return 'incomplete';
  if (reviews.length) return 'prior';
  return fallback;
}
function addReviews(row, reviews, fallback = 'model') {
  return { ...row, disposition: decision(reviews, fallback),
    ...(reviews.length ? { reviews: reviews.map(r => r.id) } : { review: 'unrated' }) };
}

const nativeExports = [liver, atlasSkin, atlasSkeleton, ...nativeDonors.values()];
const sweepSources = new Map();
function sweepReceipt(config) {
  const { id, assetRoot } = config;
  const entry = Object.values(assembly.stage.sweepFamilies).flat().find(item => item.id === id);
  const path = assetRoot + 'verification.json';
  const raw = staged(path);
  assert.equal(entry.stageVerificationSha256, sha(raw), id);
  return { path, sha256: sha(raw), data: JSON.parse(raw) };
}
const sweeps = abdomenTours.map(config => {
  const files = Object.keys(inventory.sweepHashes[config.id]);
  const poses = config.assetRoot + 'sweep.js';
  const frames = packed(poses, 'sweep');
  const receipt = sweepReceipt(config);
  const input = receipt.data;
  const stops = config.keyframes.map(stop => {
    assert(frames[stop.frame], config.id + '/' + stop.frame);
    const frame = String(stop.frame).padStart(2, '0');
    const acquired = references[stop.referenceId];
    assert(acquired, stop.referenceId);
    return { ...stop, pose: frames[stop.frame], scan: file(config.assetRoot + 'media/scan-' + frame + '.webp'),
      acquired: { path: file(acquired.path), credit: acquired.credit, source: acquired.url, scope: 'Independent acquired reference' },
      section: file(config.assetRoot + 'media/section-' + frame + '.webp') };
  });
  const parts = files.map(part => {
    const info = { ...sweepSource(config, part), ...(input.rasMmFromVoxel && { rasMmFromVoxel: input.rasMmFromVoxel }),
      ...(input.maskSha256?.[part] && { sourceSha256: input.maskSha256[part] }),
      ...(input.modelRecipeSha256 && { sourceRecipeSha256: input.modelRecipeSha256 }) };
    const binding = sourceID(info);
    sweepSources.set(config.id + '/' + part, binding);
    return addReviews({
      part, label: config.parts.find(p => p.id === part)?.label ?? 'Patient exterior', source: binding,
      task: part === config.organ ? config.title : 'Locate ' + (config.parts.find(p => p.id === part)?.label ?? 'the probe contact on the exterior') + ' in ' + config.title,
      savedFrames: stops.map(stop => stop.frame),
      channels: config.overlayParts?.some(p => p.id === part) ? ['3d-scene', 'named-scan-overlay'] : ['3d-scene'],
    }, reviewsAt('sweep', config.id, undefined, part));
  });
  const scanRecipe = config.id === 'gallbladder' ? 'build_study.py' : config.id === 'aortic-screening' ? 'build_aortic_screening.py'
    : config.id.startsWith('pregnancy-') ? pregnancyBuilder(config.id)
      : /^(thyroid|carotid)-/.test(config.id) ? (config.id.startsWith('thyroid') ? 'build_thyroid.py' : 'build_carotid.py')
        : /^(breast|axilla)/.test(config.id) ? (config.id === 'axilla' ? 'build_axilla.py' : 'build_breast.py') : 'build_abdomen.py';
  return {
    id: config.id, title: config.title, reader: 'index.html?sweep=' + config.id,
    frames: frames.length, poseFile: file(poses), stops, parts, receipt,
    scan: { representation: 'volume-derived-image', recipe: study + scanRecipe,
      source: config.sourceNote, ctSha256: input.ctSha256,
      displacementControls: config.compressionMm ? 'Compression states present' : undefined,
      task: 'Compare the sampled B-mode and named section at the authored acquisition stops.', disposition: 'state' },
  };
});

const stageSweeps = {
  early: 'pregnancy-early', first: 'pregnancy-fetus',
  mid: 'pregnancy-mid-brain', late: 'pregnancy-late-presentation',
};
const breastProfiles = new Set(['Fibroglandular tissue', 'Fibroglandular tail', 'Chest wall', 'Retromammary fat', 'Pectoral fascia']);
const { landmarks, volumeFor } = await load('cases/pregnancy/playable-model.js');
const probePaths = ['lens', 'housing', 'relief'].map(part => file('scenes/' + part + '.mesh'));
const modelFrames = {
  organs: 'Authored abdominal or superficial case RAS millimetres. The fit moves the original exterior to the local contact datum.',
  vascular: 'Authored bilateral cervical RAS millimetres. The fitted neck is contact context for authored vessel sections.',
  pregnancy: 'Authored maternal RAS millimetres. The stage volume axes and maternal centre drive placement.',
  echo: 'Modeled heart to thoracic atlas registration, then axes mapped into case RAS millimetres.',
  aaa: 's1233 RAS-oriented voxel indices at 1.5 mm per scene unit. Modeled paths are placed in the CT frame.',
};
const geometryCache = new WeakMap();
function meshIdentity(node) {
  const geometry = node.geometry;
  const { position } = geometry.attributes;
  const index = geometry.index;
  let cached = geometryCache.get(geometry);
  if (!cached || cached.position !== position.version || cached.index !== index?.version) {
    const hash = createHash('sha256');
    hash.update(Buffer.from(position.array.buffer, position.array.byteOffset, position.array.byteLength));
    if (index) hash.update(Buffer.from(index.array.buffer, index.array.byteOffset, index.array.byteLength));
    cached = { position: position.version, index: index?.version, digest: hash.digest('hex') };
    geometryCache.set(geometry, cached);
  }
  const matrix = node.matrixWorld.elements;
  const digest = sha(JSON.stringify([cached.digest, matrix]));
  return { meshAtEvidenceFrameSha256: digest };
}

function pregnancyRepresentation(row, caseRow, chapter, paths) {
  const { stage, kind } = chapter;
  const exactSweep = (id, part) => {
    const path = sweepPath(sweepsById.get(id), part);
    return paths.includes(path) ? [path] : undefined;
  };
  const stageSweep = stageSweeps[stage];
  const cordSweep = { first: stageSweep, mid: 'pregnancy-mid-abdomen', late: stageSweep }[stage];
  let representation = 'coarse-voxel-surface';
  const spacing = Math.max(1.25, volumeFor(stage).spacing * 1.5);
  let input = 'Grouped case-volume labels sampled at ' + spacing + ' mm';
  let files = [file('cases/pregnancy/playable-volume-' + stage + '.js')];
  const shape = landmarks(stage, kind);
  const hasPocketGrid = shape.fluid && Number.isFinite(shape.shape.dvp);
  if (row.skin) {
    files = exactSweep(stageSweep, 'torso');
    assert(files, caseRow.id);
    representation = 'adapted-procedural-mesh';
    input = 'Stage torso locally seated against the authored contact envelope';
  } else if (row.part === 'Fetal surface') {
    const part = stage === 'early' ? 'embryo' : 'fetus';
    const adapted = exactSweep(stageSweep, part);
    if (adapted) {
      files = adapted;
      representation = 'adapted-procedural-mesh';
      input = 'Stage exterior fitted to CRL or protected biometry bands for the modeled case';
    }
  } else if (row.part === 'Placenta' && cordSweep || row.part === 'Umbilical cord' && cordSweep) {
    const part = row.part === 'Placenta' ? 'placenta' : stage === 'first' ? 'umbilical_cord' : 'cord';
    const adopted = exactSweep(row.part === 'Placenta' ? stageSweep : cordSweep, part);
    if (adopted) {
      files = adopted;
      representation = 'reused-stage-mesh';
      input = 'Packed authored stage mesh placed by the stage grid scale';
    } else if (row.part === 'Umbilical cord' && stage === 'mid' && kind === 'abnormal') {
      representation = 'procedural-tube-mesh';
      input = 'Case-authored proximal defect path blended into the stage cord path';
    }
  } else if (row.part === 'Yolk sac' && stage === 'early' && kind === 'abnormal') {
    representation = 'procedural-shell-mesh';
    input = 'Analytic ectopic yolk-sac shell';
  } else if (row.part === 'Omphalocele membrane' || row.part === 'Herniated bowel') {
    representation = row.part === 'Omphalocele membrane' ? 'procedural-shell-mesh' : 'procedural-tube-mesh';
    input = 'Case-authored abdominal wall defect landmark model';
  } else if (hasPocketGrid && row.part === 'Fluid pocket' && row.node.geometry.attributes.position.count === 610) {
    representation = 'procedural-shell-mesh';
    input = 'Analytic fluid exterior verified against case labels by verifiedFluidExterior';
  } else if (hasPocketGrid && (row.part === 'Fluid pocket' || row.part === 'Fluid pocket boundary')) {
    representation = 'localized-voxel-surface';
    input = 'Case-label pocket and boundary on the 0.9 mm local grid';
  }
  return { representation, input, files };
}

function liveSource(row, caseRow, chapter, paths) {
  const { owner } = caseRow;
  let representation, input, files, upstream, registration;
  if (owner === 'pregnancy') {
    ({ representation, input, files } = pregnancyRepresentation(row, caseRow, chapter, paths));
  } else if (owner === 'echo') {
    const part = { 'Chest exterior': 'skin', 'Rib cage': 'bones', 'Costal cartilage': 'cartilage' }[row.part];
    if (part) {
      files = paths.filter(path => path.endsWith('/' + part + '.raw'));
      assert.equal(files.length, 1, row.part);
      representation = 'adapted-external-mesh';
      upstream = part === 'skin' ? atlasSkin.key : atlasSkeleton.key;
      input = 'Packed BodyParts3D thorax and shared heart registration';
    } else {
      representation = 'procedural-cardiac-surface';
      files = ['cardiac/heart-geometry.js', 'cardiac/torso/torso-view.js'].map(file);
      input = 'Authored beating-heart rings or open leaflet patch sampled in the registered torso';
    }
    registration = study + 'cardiac/torso/registration.js';
  } else if (row.skin) {
    files = paths.filter(path => path.endsWith('/torso.mesh'));
    assert.equal(files.length, 1, caseRow.id);
    representation = 'adapted-external-mesh';
    input = 'Delivered regional exterior refitted around the chapter paths';
    upstream = caseRow.family === 'breast' ? undefined : atlasSkin.key;
    registration = study + 'cases/organs/playable-scene-skin.js';
  } else if (owner === 'vascular') {
    representation = 'procedural-loft-mesh';
    input = 'Authored vessel station rings with separate lumen and plaque where modeled';
    files = [file('cases/vascular/playable-model.js')];
  } else {
    const ramp = row.node.geometry.type === 'SphereGeometry' && row.node.scale.toArray().every(n => n === 1);
    representation = ramp ? 'procedural-profile-mesh' : 'procedural-primitive';
    const profile = ramp && breastProfiles.has(row.part);
    input = profile ? 'Authored surface fit to sampled breast-layer profiles' : ramp
      ? 'Analytic depth profile formed by modifying a primitive sphere' : 'Analytic volume shape drawn as a scaled sphere';
    const script = caseRow.family === 'abdomen' ? 'playable-abdomen.js' : 'playable-neck-breast.js';
    files = [file('cases/organs/' + script)];
    if (profile) files.push(file('cases/organs/playable-breast-profiles.js'));
  }
  return { representation, input, files, frame: modelFrames[owner], registration, upstream,
    reader: study + 'tours/case-sweep.js', recipe: study + 'cases/' + owner + '/playable-scene.js',
    recipeSha256: inventory.recipeHashes[owner], owner: 'Worked case ' + owner };
}

function aaaSource(config, name, base) {
  const path = sweepPath(config, name, base);
  const donor = ['torso', 'vertebrae'].includes(name) ? sweepSources.get('aortic-screening/' + name) : undefined;
  if (donor) {
    assert.equal(path, sweepPath(sweepsById.get('aortic-screening'), name));
    assert.equal(fileIDs.get(path).sha256, aaaReceipt.sharedAssets[name]);
  } else {
    assert.equal(path, aaaFile(path.slice('tours/aaa/'.length)));
  }
  return {
    representation: donor ? 'same-case-exact-mesh' : 'procedural-registered-mesh',
    input: donor ? 'Exact packed aortic-screening context' : 'Authored vascular surface registered to the CT aorta',
    path, frame: modelFrames.aaa, mmPerSceneUnit: config.voxelMm, donor,
    acquisitionReceiptSha256: aaaAcquisition.stageReceiptSha256, acquisitionRecipeSha256: aaaReceipt.recipeSha256,
    reader: study + 'tours/aaa/sweep.js',
    recipe: study + 'aaa_acquisition.py', owner: 'Registered AAA acquisition',
  };
}

function acquisition(chapter, caseRow, pose, base) {
  const { owner, family } = caseRow;
  const scenario = family === 'aaa' ? 'registered-aaa' : owner;
  const scanByOwner = {
    'registered-aaa': ['volume-derived-image', 's1233 CT background plus modeled vessel wall, lumen and tissue states', 'aaa_acquisition.py'],
    organs: ['procedural-analytic-section', 'Section through authored volumes; modeled grayscale, overlays and calipers', 'cases/organs/playable.js'],
    vascular: ['procedural-analytic-section', 'Section through modeled vessels; authored velocities and Doppler sample', 'cases/vascular/playable.js'],
    pregnancy: ['volume-derived-image', 'Stage-labeled voxels with case variants and authored acquisitions/signals', 'cases/pregnancy/playable.js'],
    echo: ['procedural-cardiac-section', 'Beating heart recipe; authored section, timing and signal', 'cases/echo/playable.js'],
  };
  const [representation, input, reader] = scanByOwner[scenario];
  const evidence = { frame: chapter.evidenceFrame, frames: chapter.frames, pose,
    viewImage: chapter.viewImage, measurement: chapter.measurement,
    marks: chapter.marks ?? chapter.measure ?? pose.calipers };
  if (base) {
    const frame = String(chapter.evidenceFrame).padStart(2, '0');
    evidence.images = ['scan', 'section', ...(base.hasColor ? ['color'] : [])]
      .map(kind => aaaFile(base.mediaRoot + kind + '-' + frame + '.webp'));
  }
  const scan = sourceID({ representation, input, recipe: study + reader,
    ...(base ? { acquisitionRecipeSha256: aaaReceipt.recipeSha256 } : { recipeSha256: inventory.recipeHashes[owner] }),
    frame: modelFrames[scenario === 'registered-aaa' ? 'aaa' : owner] });
  return { scan, evidence };
}

const chapters = [];
const runtimeNativeChapters = new Set();
const seenSearch = new Set();
for (const caseRow of inventory.cases) {
  const { id, family, owner } = caseRow;
  const prefix = 'cases/' + owner + '/';
  const isAaa = family === 'aaa';
  const reader = isAaa ? 'tours/aaa/sweep.html' : caseRow.url.replace(/\.html$/, '-sweep.html');
  const recordPath = isAaa ? file('tours/aaa/' + id + '.json') : file(reader);
  const player = read(reader).toString();
  const record = isAaa ? json(recordPath)
    : JSON.parse(player.match(/<script id="record" type="application\/json">([^]*?)<\/script>/)[1]);
  if (!isAaa) assert(player.includes('data-owner="' + owner + '"'), id);
  const { sharedSweepAvailable, ...baseRecord } = record;
  if (isAaa) assert.equal(sharedSweepAvailable, true, id);
  assert.deepEqual(baseRecord, caseRow.record, id);
  const { chapters: sampleChapters } = await load(prefix + 'playable.js');
  const sections = sampleChapters(record);
  assert.deepEqual(sections.map(({ id, title, evidenceFrame }) => ({ id, title, evidenceFrame })), caseRow.chapters);
  fetched.length = 0;
  let model, aaa;
  if (isAaa) {
    aaa = json('tours/aaa/' + id + '.scene.json');
    aaaFile(id + '.scene.json');
  } else {
    model = await (await load(prefix + 'playable-scene.js')).createCaseModel(record, sections[0]);
  }
  const paths = [...new Set(fetched)].sort();
  const requirementReader = family === 'abdomen' ? 'development/assets-abdomen.js' : 'development/assets-exams.js';
  for (const chapter of sections) {
    const key = id + '/' + chapter.id;
    assert(!seenSearch.has(key), key);
    seenSearch.add(key);
    const task = chapter.observation || chapter.title;
    const required = family === 'abdomen' ? abdomenRequirements(chapter.id) : examRequirements(caseRow, chapter);
    const packedCase = aaa?.[chapter.id];
    assert(Boolean(packedCase) === isAaa, key);
    const pose = packedCase ? packedCase.frames[chapter.evidenceFrame] : model.update(chapter, chapter.evidenceFrame);
    if (model) model.anatomy.updateMatrixWorld(true);
    const { scan, evidence } = acquisition(chapter, caseRow, pose, packedCase);
    const marks = new Set((chapter.marks ?? []).flatMap(mark => [mark.id, mark.inner]).filter(Boolean));
    const scanNames = new Set([...(chapter.labels ?? []), ...(chapter.colorIds ?? []), ...(chapter.layerLabels ?? []),
      ...marks, typeof chapter.target === 'string' ? chapter.target : undefined].filter(Boolean));
    const meshRows = packedCase ? [{ id: 'torso', label: 'Patient exterior' }, ...packedCase.config.parts]
      .map(({ id: part, label }) => ({ part, label, occurrence: 1,
        info: aaaSource(packedCase.config, part, new URL('tours/aaa/', root)) }))
      : meshParts(model).map(row => ({ part: row.part, label: row.label, occurrence: row.occurrence, path: row.path,
        info: liveSource(row, caseRow, chapter, paths), ...meshIdentity(row.node) }));
    const runtime = meshRows.map(({ info, ...row }) => {
      if (info.directNative || info.path && fileIDs.get(info.path).sha256 === liver.sha256
        || info.files?.some(path => fileIDs.get(path).sha256 === liver.sha256)) runtimeNativeChapters.add(key);
      const selected = required.some(ref => selectsRetained(ref, row.part));
      const acquisitionBinding = marks.has(row.part) ? 'measurement-mark'
        : scanNames.has(row.part) ? 'named-scan-label' : undefined;
      const bindings = reviewsAt('case', id, chapter.id, row.part, row.occurrence);
      const caseReviews = reviewsAt('case', id, undefined, row.part, row.occurrence);
      return addReviews({ ...row, source: sourceID(info), workbenchSelection: selected ? 'retained' : 'unselected',
        acquisitionBinding,
        ...(caseReviews.length > 0 && { caseReviews: caseReviews.map(review => review.id) }),
      }, bindings, selected && caseReviews.length ? 'case-review' : 'model');
    });
    const requirements = required.flatMap(ref => {
      if (ref.source === 'retained') {
        const present = meshRows.filter(row => selectsRetained(ref, row.part));
        const expected = Array.isArray(ref.parts) ? ref.parts : present.length ? [] : [chapter.title];
        const missing = expected.filter(name => !present.some(row => row.part === name));
        return missing.map(part => ({ part, representation: 'missing-structure', scope: ref.referenceScope,
          disposition: 'gap', review: 'unrated', blocker: 'No matching selectable part in the evidence-frame model.' }));
      }
      if (ref.source === 'acquisition-note') {
        return [{ part: ref.id, label: ref.label, representation: 'acquisition-state', source: scan,
          disposition: 'state', review: 'unrated' }];
      }
      const donor = ref.source === 'sweep' ? sweepSources.get(ref.key + '/' + ref.part)
        : ref.source === 'gallery' && donorRows.has(ref.part) ? sourceID(referenceSource(donorRows.get(ref.part))) : undefined;
      if (donor) {
        const donorReviews = ref.source === 'sweep' ? reviewsAt('sweep', ref.key, undefined, ref.part).map(review => review.id) : [];
        return [{ part: ref.part, source: donor, representation: 'independent-reference',
          scope: ref.referenceScope, aliases: ref.legacyParts, disposition: 'reference', review: 'unrated',
          ...(donorReviews.length && { donorReviews }),
          ...(ref.source === 'sweep' && { fromSweep: ref.key }) }];
      }
      return [{ part: ref.part, label: ref.label, representation: 'missing-structure',
        aliases: ref.legacyParts, disposition: ref.status === 'rebuild' ? 'source' : 'gap', review: 'unrated',
        blocker: ref.missingReason ?? 'The named donor is absent from this delivery.' }];
    });
    const scanUses = [...scanNames].map(part => ({
      part, source: scan, representation: 'acquisition-label', disposition: 'state', review: 'unrated',
    }));
    const probe = packedCase ? 'curved' : pose.probe;
    const probeSource = sourceID({ representation: probe === 'curved' ? 'procedural-packed-probe' : 'procedural-probe',
      input: 'Authored ' + probe + ' transducer and beam field',
      ...(probe === 'curved' && { files: [...probePaths, file('scenes/geometry.json')] }),
      reader: study + (packedCase ? 'scene.js' : 'case-scene.js') });
    chapters.push({
      case: id, chapter: chapter.id, family, owner, title: chapter.title, task, recordPath,
      reader: reader + '?' + new URLSearchParams({ ...(isAaa && { case: id }), chapter: chapter.id,
        frame: chapter.evidenceFrame }),
      coordinateFrame: modelFrames[packedCase ? 'aaa' : owner], ...evidence, probe, probeSource, scan,
      requirementReader: study + requirementReader, runtime, requirements, scanUses,
    });
  }
  if (model?.dispose) model.dispose();
  else model?.anatomy.traverse(node => { node.geometry?.dispose(); node.material?.dispose(); });
  console.error(id + ' ' + sections.length);
}

assert.equal(chapters.length, 410);
for (const review of reviewInfo) {
  review.boundToRuntimeOrSweep = usedReviews.has(review.id);
  if (review.boundToRuntimeOrSweep) families[review.id.split('/')[0]].used++;
}
const representations = {};
const dispositionCounts = {};
const reverse = Object.fromEntries([...sourceModels].map(([model, key]) => [key, JSON.parse(model)]));
function count(object, key) { object[key] = (object[key] ?? 0) + 1; }
for (const row of [...sweeps.flatMap(sweep => sweep.parts), ...chapters.flatMap(chapter => [
  ...chapter.runtime, ...chapter.requirements, ...chapter.scanUses,
])]) {
  count(representations, row.representation ?? reverse[row.source].representation);
  count(dispositionCounts, row.disposition);
}
const unboundReviews = reviewInfo.filter(review => !review.boundToRuntimeOrSweep).map(review => review.id);
const summary = {
  sourceRevision: assembly.sourceRevision,
  inventory: file('development/asset-inventory.json'),
  catalogue: file('abdomen-tours.js'),
  population: {
    sweeps: sweeps.length, sweepPartUses: sweeps.reduce((n, row) => n + row.parts.length, 0),
    teachingTours: inventory.teachingTours.length, caseTours: inventory.cases.length,
    chapters: chapters.length, unauditedChapters: 0, directNativeChapterUses: runtimeNativeChapters.size,
    directNativeSweepUses: sweeps.filter(s => s.parts.some(row => reverse[row.source].directNative)).length,
    scenePartUses: chapters.reduce((n, row) => n + row.runtime.length, 0),
    workbenchRequirements: chapters.reduce((n, row) => n + row.requirements.length, 0),
    scanLabelUses: chapters.reduce((n, row) => n + row.scanUses.length, 0),
  },
  reviewFamilies: families, representations, dispositionCounts, unboundReviews,
};
const outputDocument = {
  schemaVersion: 1, summary, dispositionDefinitions: dispositions, nativeExports, aaaAcquisition, sources: reverse,
  files: Object.fromEntries(fileIDs), reviews: reviewInfo, sweeps, chapters,
};
assert.equal(runtimeNativeChapters.size, 0, 'A native chapter reader now exists; update this audit.');
const serial = '{\n' + Object.entries(outputDocument).map(([key, value]) => {
  if (Array.isArray(value)) return '  "' + key + '": [\n' +
    value.map(item => '    ' + JSON.stringify(item)).join(',\n') + '\n  ]';
  if (['sources', 'files'].includes(key)) return '  "' + key + '": {\n' +
    Object.entries(value).map(([name, item]) => '    ' + JSON.stringify(name) + ': ' + JSON.stringify(item)).join(',\n') + '\n  }';
  return '  "' + key + '": ' + JSON.stringify(value, null, 2).replaceAll('\n', '\n  ');
}).join(',\n') + '\n}\n';
writeFileSync(output, serial);
if (summaryOutput) {
  const fullBytes = Buffer.from(serial);
  const compactDocument = {
    schemaVersion: 1,
    fullAudit: { sha256: sha(fullBytes), bytes: fullBytes.byteLength },
    summary,
    dispositionDefinitions: dispositions,
    nativeExports,
    aaaAcquisition,
    reviews: reviewInfo.map(r => ({
      id: r.id, source: r.source, case: r.case, ...(r.chapter && { chapter: r.chapter }), part: r.part,
      binding: r.binding, identityMatches: r.identityMatches, currency: r.currency, allTop: r.allTop,
      scores: r.scores, ...(r.missingAxes?.length && { missingAxes: r.missingAxes }),
      additionalUses: r.additionalUses?.length ?? 0,
    })),
    sweeps: sweeps.map(s => ({
      id: s.id, title: s.title, region: s.region, parts: s.parts.length,
      directNative: s.parts.some(row => reverse[row.source].directNative),
    })),
    chapters: chapters.map(c => {
      const reps = [...new Set(c.runtime.map(row => row.representation ?? reverse[row.source].representation))].sort();
      const disps = [...new Set([...c.runtime, ...c.requirements].map(row => row.disposition))].sort();
      const gaps = c.requirements.filter(r => r.disposition === 'gap' || r.disposition === 'source').map(r => r.part);
      return {
        case: c.case, chapter: c.chapter, family: c.family, owner: c.owner, frame: c.frame,
        runtimeParts: c.runtime.length,
        hasPrimitive: reps.includes('procedural-primitive'),
        hasCoarseVoxel: reps.includes('coarse-voxel-surface'),
        directNative: c.runtime.some(row => reverse[row.source].directNative),
        representations: reps, dispositions: disps,
        ...(gaps.length && { openGaps: gaps }),
      };
    }),
  };
  const compactSerial = '{\n' + Object.entries(compactDocument).map(([key, value]) => {
    if (Array.isArray(value)) return '  "' + key + '": [\n' +
      value.map(item => '    ' + JSON.stringify(item)).join(',\n') + '\n  ]';
    return '  "' + key + '": ' + JSON.stringify(value, null, 2).replaceAll('\n', '\n  ');
  }).join(',\n') + '\n}\n';
  writeFileSync(summaryOutput, compactSerial);
}
console.log(JSON.stringify(summary, null, 2));
