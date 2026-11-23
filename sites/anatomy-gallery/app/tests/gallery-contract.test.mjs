import test from 'node:test';
import assert from 'node:assert/strict';
import { createGalleryDelivery } from '../src/content/shared/release-delivery.js';
import { baseView, localView, readView, stagePath } from '../src/content/gallery/presets.js';
import { byPath, ratingProfile, studies } from '../src/content/gallery/catalog.js';
import { bronchialExterior, cardiacExterior, firstForkPath } from '../src/content/gallery/local-models.js';
import { libraryRows } from '../src/content/gallery/library-compiler.js';
import { selectLibraryRow } from '../src/content/gallery/library-view.js';

test('rubric and study links work without a bucket or write access', async () => {
  const handle = createGalleryDelivery({ assets: [] }, () => false, { resources: [], studies });
  const request = (p, method = 'GET') => handle(new Request('https://example.test' + p, { method }), {});
  assert.equal(
    (await request('/rubric')).headers.get('location'),
    'https://example.test/#/rubric',
  );
  assert.deepEqual(await (await request('/api/gallery/v1/studies')).json(), studies);
  assert.equal(await (await request('/api/gallery/v1/studies', 'HEAD')).text(), '');
  assert.equal((await request('/api/gallery/v1/studies', 'POST')).status, 405);
  assert.equal(await request('/api/snapshot'), null);
});
test('a teaching total requires four assessed axes and preserves an assessed zero', () => {
  const partial = ratingProfile([0, 3, null, 2]);
  assert.deepEqual(partial, { axes: [0, 3, null, 2], score: null, ratingLabel: 'Partially rated' });
  assert.equal(ratingProfile().ratingLabel, 'Unrated');
  assert.equal(ratingProfile([3, 3, 4]).score, null);
  assert.equal(ratingProfile([0, 0, 0, 0]).ratingLabel, '0/16');
  assert.equal(ratingProfile([4, 3, 3, 3]).ratingLabel, '13/16');
});

test('a shared view pins the model, part, appearance and finite camera', () => {
  const v = {
    ...baseView('r04', 'Right adrenal gland'),
    material: 'Neutral',
    light: 0.75,
    camera: { position: [0.1, 0.2, 0.3], target: [0, 0, 0], height: 0.04 },
  };
  const query = stagePath(v).split('?')[1];
  assert.deepEqual(readView(query), v);
  const asQuery = (x) => 'view=' + encodeURIComponent(JSON.stringify(x));
  for (const change of [
    { revision: 'r900' },
    { revision: 'constructor' },
    { sha256: 'bad' },
    { light: -1 },
    { version: 'v2' },
    { part: 'absent' },
    { camera: { position: [1, 2, 3], target: [1, 2, 3], height: 1 } },
    { camera: { position: [1, 2, 3], target: [0, 0, 0], height: -1 } },
  ]) {
    assert.equal(readView(asQuery({ ...v, ...change })), null);
  }
  assert.equal(readView('view=bad'), null);
  assert.equal(readView('view=' + 'x'.repeat(1700)), null);
});

test('the candidate recommendation leaves the original and public catalogue routes intact', () => {
  const original = byPath.get('heart/exterior-presentation-r01/exports/static-opaque-exterior.glb');
  const packages = [{ id: 'cardiac-exterior', media: [original], revisions: [
    { family: 'cardiac-exterior', revision: 'static-opaque-exterior', library: 'library/cardiac-exterior/static-opaque-exterior', exports: [original.path] },
  ] }];
  const selected = { 'cardiac-exterior': cardiacExterior.library };
  const find = (localPreview = false) => libraryRows(undefined, { localPreview, packages, selected }).find(row => row.id === 'cardiac-exterior');
  const publicRow = find();
  const local = find(true);
  assert.equal(publicRow.path, 'library/cardiac-exterior');
  assert.equal(publicRow.history.some((record) => record.library === cardiacExterior.library), false);
  assert.equal(local.path, cardiacExterior.library);
  assert.deepEqual(local.history.slice(1), publicRow.history);
  assert.equal(selectLibraryRow(local, original.sha256).path, 'library/cardiac-exterior/static-opaque-exterior');
  const cardiacView = localView(cardiacExterior);
  assert.equal(selectLibraryRow(local, cardiacView.sha256).path, cardiacExterior.library);
  const [stage, query] = stagePath(cardiacView, cardiacExterior.library).split('?');
  assert.equal(stage, 'stage/cardiac-exterior-v1');
  assert.deepEqual(readView(query), cardiacView);
  const wrong = new URLSearchParams({ view: JSON.stringify({ ...cardiacView, sha256: original.sha256 }) });
  assert.equal(readView(wrong), null);
});

test('bronchial recommendation and assessment bind to their own revisions', () => {
  const source = byPath.get('models/bronchial_tree/exports/authored-central-fairing-r13/bronchial_central_fairing.glb');
  const packages = [{ id: 'bronchial_tree', label: 'Bronchial tree', media: [source] }];
  const route = 'library/bronchial_tree/authored-central-fairing-r13';
  const assessment = {
    route, export: source, axes: [3, 2, 4, 2].map((score) => ({ score })),
    views: [{ path: 'reviews/bronchial_tree/2026-10-26-authored-central-fairing-r13/evidence/after-whole.png' }],
  };
  const selected = { bronchial_tree: bronchialExterior.library };
  const find = (localPreview = false) => libraryRows({ assessments: [assessment] }, { packages, selected, localPreview })
    .find(row => row.id === 'bronchial_tree');
  const publicRow = find();
  const local = find(true);
  assert.equal(publicRow.path, route);
  assert.equal(publicRow.ratingLabel, '11/16');
  assert.deepEqual(local.history.filter((record) => !record.scene), publicRow.history);
  const earlier = local.history.find((record) => record.revision === 'distal-sampling-r14');
  const olderView = localView(earlier);
  const [olderStage, olderQuery] = stagePath(olderView, firstForkPath).split('?');
  assert.equal(olderStage, 'stage/bronchial-first-fork-v1');
  assert.deepEqual(readView(olderQuery), olderView);
  assert.equal(local.path, bronchialExterior.library);
  assert.equal(local.ratingLabel, 'Unrated');
  assert.equal(selectLibraryRow(local, source.sha256).ratingLabel, '11/16');
  const view = localView(bronchialExterior);
  const [stage, query] = stagePath(view, firstForkPath).split('?');
  assert.equal(stage, 'stage/bronchial-first-fork-v2');
  assert.deepEqual(readView(query), view);
  assert.equal(new URLSearchParams(query).get('from'), firstForkPath);
  const wrong = new URLSearchParams({ view: JSON.stringify({ ...view, sha256: source.sha256 }) });
  assert.equal(readView(wrong), null);
});

test('Library compiler binds each export and recommendation by stable identity', async () => {
  const { compileLibrary, checkMembership } = await import('../src/content/gallery/library-model.js');
  const { decodeLibrary } = await import('../src/content/gallery/decode-library.js');
  const { selectExactExport, exactExportPath, revisionStatus } = await import('../src/content/gallery/library-view.js');
  const identity = (name, char) => ({
    path: 'models/fixture/' + name, name, bytes: 12, sha256: char.repeat(64), mediaType: 'model/gltf-binary',
    license: 'CC BY 4.0',
  });
  const first = identity('surface.glb', 'f');
  const second = identity('cutaway.glb', 'e');
  const assessment = (file, score) => ({
    export: file, task: file.name, decision: file.name, axes: [score, score, score, score].map(score => ({ score })), views: [],
  });
  const a = assessment(first, 3);
  const b = assessment(second, 4);
  const multi = {
    library: 'library/fixture/r02', revision: 'r02', exports: [first, second],
    defaultFile: first.path, assessment: a, fileAssessments: new Map([[first.path, a], [second.path, b]]),
  };
  const old = { library: 'library/fixture/r01', revision: 'r01', exports: [first], status: 'Recommended for locating the wall' };
  const row = (recommended, history) => ({ id: 'fixture', history, recommended, lessons: [multi] });
  for (const ordered of [[a, b], [b, a]]) {
    const readModel = compileLibrary([row(multi, [old, multi])], { assessments: ordered });
    checkMembership(readModel, { assets: [first, second] }, []);
    assert.throws(() => checkMembership(readModel, { assets: [first] }, []), /outside the release/);
    const { rows: [resolved] } = decodeLibrary(JSON.parse(JSON.stringify(readModel)));
    assert.equal(resolved.recommended.library, multi.library);
    assert.equal(revisionStatus(resolved.recommended, resolved.recommended), 'Recommended');
    assert.equal(revisionStatus(resolved.history[0], resolved.recommended), 'Reviewed for locating the wall');
    assert.equal(resolved.lessons[0], resolved.recommended);
    assert.equal(resolved.recommended.exports[0].license, 'CC BY 4.0');
    const exact = selectExactExport(resolved.recommended, second.sha256);
    assert.equal(exact.assessment.export.path, second.path);
    assert.equal(exact.assessment.axes[0].score, 4);
    assert.equal(exactExportPath(resolved.recommended, second), multi.library + '?file=' + second.sha256);
    assert.equal(selectExactExport(resolved.recommended, 'z'.repeat(64)), undefined);
  }
  const replaced = decodeLibrary(compileLibrary([row(old, [multi, old])])).rows[0];
  assert.equal(replaced.recommended.library, old.library);
  assert.deepEqual(replaced.history.map(record => record.library), [multi.library, old.library]);
  assert.throws(() => compileLibrary([row(old, [multi])]), /outside its family history/);
});
