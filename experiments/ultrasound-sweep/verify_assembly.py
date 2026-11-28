"""Exercise compact assembly and reject corrupt staged study inputs."""

import argparse
import json
from pathlib import Path
import shutil
import struct
import tempfile

from assetkit import AssetKitError, AssetRegistry
from assetkit.ultrasound import GALLERY_REFERENCE_CONFIG, read_gallery_references
from med_assets.ultrasound_review import chapter_mesh_bindings

import assemble_tours
from gallery_reference_sources import write_gallery_donors
from delivery import read_poses, sha256, validate_mesh
from asset_qualification import validate_reviews


def javascript_value(path, variable):
    return json.loads(path.read_text().strip().removeprefix(f'const {variable} = ').removesuffix(';'))


def reject(source, target, expected):
    try:
        assemble_tours.assemble(source, target)
    except (ValueError, FileNotFoundError) as exc:
        if expected not in str(exc):
            raise
    else:
        raise AssertionError(f'Assembly accepted {expected}')
    assert not target.exists(), f'Assembly published an incomplete delivery: {target}'


def verify_review_failures(work):
    package = work / 'development/asset-reviews/test'
    package.mkdir(parents=True)
    image = package / 'paired.webp'
    image.write_bytes(b'illustrative fixture')
    record = dict(case='test', part='rim', revision='sample', task='Trace the opening', rubric='fixture',
                  reviewer='test', reviewedOn='test', scores={'form': 3}, scoreEvidence={'form': 'Visible rim'},
                  comparison={'candidate': 'asset-reviews/test/paired.webp'})
    data = dict(version=1, records=[record], evidenceSha256={image.name: sha256(image.read_bytes())})
    path = package / 'reviews.json'
    path.write_text(json.dumps(data))
    validate_reviews(path)

    def must_fail(reason):
        path.write_text(json.dumps(data))
        try:
            validate_reviews(path)
        except ValueError as error:
            assert reason in str(error), error
        else:
            raise AssertionError('Accepted invalid review: ' + reason)

    record['scores']['form'] = 5
    must_fail('score')
    record['scores']['form'] = 3
    image.write_bytes(b'changed witness')
    must_fail('identity mismatch')
    record['comparison']['candidate'] = 'asset-reviews/test/missing.webp'
    must_fail('Missing or unbound')


def verify_chapter_mesh_bindings(work):
    mesh = work / 'parts'
    mesh.mkdir()
    reviewed = mesh / 'rim.mesh'
    sibling = mesh / 'wall.mesh'
    pose = mesh / 'pose.json'

    def triangle(x):
        return struct.pack('<2I9f3I', 3, 1, x, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 2)

    reviewed.write_bytes(triangle(1))
    sibling.write_bytes(triangle(1))
    pose.write_text('[1, 0, 0]')
    placement = {'millimetresPerUnit': 1.5}
    chapter = dict(id='saved', evidenceFrame=12, observation='Trace the rim',
                   reviewMeshes={
                       'rim': dict(path='parts/rim.mesh', placement=placement, inputs=['parts/pose.json']),
                       'wall': dict(path='parts/wall.mesh', placement=placement, inputs=[]),
                   })

    def bindings():
        return chapter_mesh_bindings(work, {'worked': [chapter]}, validate_mesh=validate_mesh)['worked']['saved']

    original = bindings()
    sibling.write_bytes(triangle(2))
    assert bindings()['rim'] == original['rim']
    assert bindings()['wall']['meshSha256'] != original['wall']['meshSha256']
    reviewed.write_bytes(triangle(2))
    assert bindings()['rim']['meshSha256'] != original['rim']['meshSha256']
    reviewed.write_bytes(triangle(1))
    placement['millimetresPerUnit'] = 1
    assert bindings()['rim']['chapterSha256'] != original['rim']['chapterSha256']
    placement['millimetresPerUnit'] = 1.5
    pose.write_text('[0, 1, 0]')
    assert bindings()['rim']['chapterSha256'] != original['rim']['chapterSha256']
    pose.write_text('[1, 0, 0]')
    assert bindings()['rim'] == original['rim']

    for bad_bytes, message in ((None, 'Missing artifact file'), (b'corrupt', 'Invalid packed mesh')):
        reviewed.unlink()
        if bad_bytes is not None:
            reviewed.write_bytes(bad_bytes)
        try:
            bindings()
        except ValueError as error:
            assert message in str(error), error
        else:
            raise AssertionError(f'Chapter mesh accepted {message}')
        if not reviewed.exists():
            reviewed.write_bytes(triangle(1))
    print('Chapter mesh binding: sibling edit preserved currency; mesh, placement and pose edits invalidated it; missing and corrupt payloads rejected.')


def verify_companions(destination, tours):
    from copy import deepcopy
    from survey_exemplars import CASES, bind_consumer

    by_id = {tour['id']: tour for tour in tours}
    for path in sorted(CASES.glob('*/consumer.json')):
        for consumer in json.loads(path.read_text())['consumers']:
            if consumer.get('presentation') != 'companion' or consumer['sweep'] not in by_id:
                continue
            case, chapter = consumer['case'], consumer['chapter']
            def bind(row):
                worked = dict(id=chapter, evidenceFrame=consumer['workedFrame'],
                              observation='Original worked task', measurement='Original measurement')
                bind_consumer(destination, by_id, {case: [worked]}, row)
                assert worked['observation'] == 'Original worked task' and worked['measurement'] == 'Original measurement'
                return worked

            original = bind(consumer)
            assert original['exemplar']['frame'] == consumer['frame'] and 'sourceSweep' not in original
            for field in ('part', 'poseSha256', 'workedFrame', 'subject', 'sha256', 'revision'):
                changed = deepcopy(consumer)
                if field == 'subject':
                    changed['requirements'][0]['subject'] = 'wrong-case'
                elif field in ('sha256', 'revision'):
                    changed['pins'][0][field] = '0' * 64
                else:
                    changed[field] = -1 if field == 'workedFrame' else 'wrong-input'
                try:
                    bind(changed)
                except ValueError:
                    continue
                raise AssertionError(f'{case}/{chapter}: accepted a changed {field}')


def verify_subset(staging, destination, expected):
    """A removed study may change which surviving tour owns a shared mesh."""
    actual = javascript_value(destination / 'abdomen-tours.js', 'abdomenTours')
    def metadata(tours):
        return [{key: val for key, val in tour.items() if key != 'meshPaths'} for tour in tours]
    assert metadata(actual) == metadata(expected)
    for tour in actual:
        for part in ['torso', *(part['id'] for part in tour['parts'])]:
            raw = Path(tour['assetRoot']) / 'scenes' / (part + '.mesh')
            packed = tour.get('meshPaths', {}).get(part, raw)
            assert (staging / raw).read_bytes() == (destination / packed).read_bytes()


def verify(source, aaa_acquisitions=None):
    with tempfile.TemporaryDirectory() as work:
        work = Path(work)
        verify_review_failures(work)
        verify_chapter_mesh_bindings(work)
        source_root = work / 'gallery-inputs'
        repo = assemble_tours.HERE.parents[1]
        donor = next(donor for donor in read_gallery_references(repo).donors if donor.slot == 'bladder')
        _, _, export = AssetRegistry.load_records(repo, (donor.ref.record,)).require_record_export(donor.ref)
        config = source_root / GALLERY_REFERENCE_CONFIG
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({'schemaVersion': 1, 'donors': [donor.to_dict()]}))
        record = source_root / donor.ref.record
        record.parent.mkdir(parents=True)
        shutil.copyfile(repo / donor.ref.record, record)
        bladder = source_root / export.path
        bladder.parent.mkdir(parents=True)
        pointer = f'version https://git-lfs.github.com/spec/v1\noid sha256:{export.sha256}\nsize {export.bytes}\n'
        bladder.write_text(pointer)
        write_gallery_donors(work, source_root)
        assert json.loads((work / 'development/gallery-donors.json').read_text()) == []
        bladder.write_text(pointer.replace(export.sha256, 'a' * 64))
        try:
            write_gallery_donors(work, source_root)
        except AssetKitError as exc:
            assert 'Gallery donor pointer identity mismatch' in str(exc)
        else:
            raise AssertionError('Workbench skipped a pointer with an unexpected digest')
        bladder.write_bytes(b'corrupt donor')
        try:
            write_gallery_donors(work, source_root)
        except AssetKitError as exc:
            assert 'Export size or SHA-256 mismatch' in str(exc)
        else:
            raise AssertionError('Workbench accepted a donor with an unexpected digest')
        staging = work / 'staging'
        destination = work / 'delivery'
        shutil.copytree(source, staging)
        bundle = staging / 'aaa-acquisitions'
        if aaa_acquisitions is not None:
            if bundle.exists():
                shutil.rmtree(bundle)
            shutil.copytree(aaa_acquisitions, bundle)
        cardiac = work / 'cardiac-input'
        shutil.copytree(assemble_tours.HERE / 'cardiac', cardiac)
        reference = json.loads((cardiac / 'acquisition.json').read_text())
        cases = [
            (reference['file'], 'Unexpected acquired cardiac cine identity'),
            ('reference/plax.webp', 'Unexpected acquired cardiac cine identity: plax'),
            ('reference/bse-table1.zip', 'Unexpected published echo panel archive'),
            ('torso/skin.raw', 'Unexpected cardiac torso geometry: skin'),
        ]
        for name, message in cases:
            path = cardiac / name
            original = path.read_bytes()
            path.write_bytes(b'wrong input')
            try:
                assemble_tours.copy_cardiac_study(cardiac, work / 'invalid-cardiac')
            except ValueError as exc:
                assert message in str(exc)
            else:
                raise AssertionError(f'Corrupt cardiac input entered the delivery: {name}')
            assert not (work / 'invalid-cardiac').exists()
            path.write_bytes(original)
        research = work / 'research'
        shutil.copytree(assemble_tours.RESEARCH, research)
        original_research = assemble_tours.RESEARCH
        assemble_tours.RESEARCH = research
        try:
            assemble_tours.assemble(staging, destination)
            tours = javascript_value(destination / 'abdomen-tours.js', 'abdomenTours')
            verify_companions(destination, tours)
            references = javascript_value(destination / 'references.js', 'abdomenReferences')
            # All declared per-view comparison IDs resolve in the complete delivered study.
            if len(tours) == 28 and (destination / 'carotid-survey/protocol.json').is_file():
                from case_library import ROOT, load_cases
                echo = json.loads((assemble_tours.HERE / 'cardiac/reference/sources.json').read_text())
                sources = set(references) | {f'bse-{p["number"]}' for v in echo['panels'].values() for p in v}
                for family in load_cases(ROOT).values():
                    for record in family:
                        bound = {rid for v in record['views'] for rid in v.get('referenceIds', [])}
                        assert not bound - sources, (record['id'], bound - sources)
            projected = set()
            for tour in tours:
                for part in ['torso', *(part['id'] for part in tour['parts'])]:
                    raw = f'{tour["assetRoot"]}scenes/{part}.mesh'
                    packed = tour.get('meshPaths', {}).get(part, raw)
                    projected.add((destination / packed).resolve())
                    assert (destination / packed).read_bytes() == (staging / raw).read_bytes()
                for reference in [*(key['referenceId'] for key in tour['keyframes']), *tour['landmarks']]:
                    row = references[reference]
                    data = (destination / row['path']).read_bytes()
                    if 'sha256' in row:
                        assert sha256(data) == row['sha256']
                frames = [key['frame'] for key in tour['keyframes']]
                if tour.get('pregnancyStage'):
                    receipt = json.loads((staging / tour['assetRoot'] / 'verification.json').read_text())
                    assert frames == sorted(int(frame) for frame in receipt['frames'])
                    assert tour['pregnancyStage']['focus']
                    for path in assemble_tours.detail_files(tour['keyframes']):
                        assert (destination / tour['assetRoot'] / path).read_bytes() == (
                            staging / tour['assetRoot'] / path).read_bytes()
                elif tour['id'] == 'aortic-screening':
                    assert frames == [12, 30, 48]
                    assert tour['showApSpan'] and len({key['referenceId'] for key in tour['keyframes']}) == 3
                else:
                    expected = [0, 12, 48] if tour['id'].startswith('thyroid-') else [12, 48]
                    assert frames == expected
            assert len(projected) < sum(1 + len(tour['parts']) for tour in tours)
            assert not (destination / 'torso.npz').exists()
            assert not (destination / 'sweeps/aorta/delivery.json').exists()

            aorta = staging / 'sweeps/aorta'
            splenic_receipt = staging / 'sweeps/spleen/verification.json'
            stale_recipe = json.loads(splenic_receipt.read_text())
            stale_recipe['poseRecipeSha256'] = '0' * 64
            stale_palette = json.loads(splenic_receipt.read_text())
            stale_palette['sectionPaletteSha256'] = '0' * 64
            manifest = aorta / 'delivery.json'
            hashes = json.loads(manifest.read_text())
            broken = work / 'broken'
            invalid_poses = javascript_value(aorta / 'sweep.js', 'sweep')[:-1]
            cases = [
                (splenic_receipt, json.dumps(stale_recipe).encode(), 'current pose recipe', False),
                (splenic_receipt, json.dumps(stale_palette).encode(), 'current section palette', False),
                (staging / 'vendor/build/three.core.js', b'invalid vendor', 'Three.js dependency identity mismatch', False),
                (staging / 'scenes/lens.mesh', b'invalid lens', 'Stale shared probe geometry', False),
                (aorta / 'media/scan-12.webp', (aorta / 'media/scan-48.webp').read_bytes(),
                 'Sweep delivery identity mismatch', False),
                (aorta / 'media/section-48.webp', None, 'Missing sweep input', False),
                (aorta / 'sweep.js', f'const sweep = {json.dumps(invalid_poses)};'.encode(),
                 'Expected 49 poses', True),
                (aorta / 'scenes/torso.mesh', b'invalid mesh', 'Invalid packed mesh', True),
                (aorta / 'media/section-48.webp', b'invalid image', 'Cannot decode WebP', True),
                (research / 'acquired/extrahepatic-duct.webp', b'invalid acquired comparison',
                 'Unexpected acquired image identity', False),
            ]
            acquisition = staging / 'carotid-survey/data'
            if acquisition.exists():
                protocol = json.loads((destination / 'carotid-survey/protocol.json').read_text())
                assert len(protocol['stations']) == 18 and len(protocol['datasetId']) == 64
                geometry = json.loads((acquisition / 'protocol-geometry.json').read_text())
                display = destination / 'carotid-survey' / protocol['displaySkinPath']
                assert sha256(display.read_bytes()) == '9e49f67e9cfc534053181f71a65bc1b816c9158fdd568b3f4f5818ef477267f3'
                original_skin = geometry['context']['skinPath']
                assert (destination / 'carotid-survey/data' / original_skin).read_bytes() == (acquisition / original_skin).read_bytes()
                geometry_path = acquisition / 'protocol-geometry.json'
                seal = acquisition / 'delivery.json'
                good_geometry, good_seal = geometry_path.read_bytes(), seal.read_bytes()
                try:
                    stale = {**geometry, 'acquisitionRecipeSha256': '0' * 64}
                    geometry_path.write_text(json.dumps(stale))
                    seal.write_text(json.dumps({**json.loads(good_seal), 'protocol-geometry.json': sha256(geometry_path.read_bytes())}))
                    reject(staging, broken, 'Rebuild the carotid survey')
                finally:
                    geometry_path.write_bytes(good_geometry)
                    seal.write_bytes(good_seal)
                sources = json.loads((assemble_tours.HERE / 'carotid-survey/sources.json').read_text())
                for key, binding in sources.items():
                    assert references[key] == binding
                    assert sha256((destination / binding['path']).read_bytes()) == binding['sha256']
                for side in ('right', 'left'):
                    first_scan = geometry['tracking'][side][0]['path']
                    volume = geometry['volumes'][side]['path']
                    assert (destination / 'carotid-survey/data' / volume).is_file()
                    cases.append((acquisition / first_scan, None, 'Carotid survey acquisition identity mismatch', False))
                cases.append((acquisition / 'delivery.json', None, 'Incomplete carotid survey acquisition', False))
                cases.append((acquisition / volume, b'broken volume', 'Carotid survey acquisition identity mismatch', False))
            right = staging / 'sweeps/thyroid-right'
            if right.exists():
                left = staging / 'sweeps/thyroid-left'
                thyroid = [tour for tour in tours if tour['id'] in ('thyroid-left', 'thyroid-right')]
                thyroid_route = Path('tours/thyroid-orientation/index.html')
                assert (destination / thyroid_route).is_file()
                assert 'thyroid-orientation/index.html' in (destination / 'tours/index.html').read_text()
                assert len(thyroid) == 2
                assert all(tour['initialFrame'] == 12 and tour['keyframes'][0]['referenceId'] == 'thyroid-isthmus'
                           for tour in thyroid)
                assert read_poses(right / 'sweep.js')[0] == read_poses(left / 'sweep.js')[0]
                for filename in ('scan-00.webp', 'section-00.webp'):
                    assert (right / 'media' / filename).read_bytes() == (left / 'media' / filename).read_bytes()
                left.rename(work / 'left')
                reject(staging, broken, 'Incomplete thyroid study')
                right.rename(work / 'right')
                abdomen = work / 'abdomen'
                assemble_tours.assemble(staging, abdomen)
                verify_subset(staging, abdomen, [tour for tour in tours if tour['id'] not in ('thyroid-left', 'thyroid-right')])
                assert not (abdomen / thyroid_route).exists()
                assert 'thyroid-orientation/index.html' not in (abdomen / 'tours/index.html').read_text()
                (work / 'left').rename(left)
                (work / 'right').rename(right)
                receipt = right / 'verification.json'
                wrong_field = {**json.loads(receipt.read_text()), 'fieldWidthMm': -1}
                cases.extend([
                    (receipt, json.dumps(wrong_field).encode(), 'configured linear field', False),
                    (right / 'delivery.json', None, 'Missing linear sweep delivery inventory', False),
                    (research / 'acquired/thyroid-isthmus.webp', b'invalid', 'Unexpected acquired image identity', False),
                ])
            carotid = staging / 'sweeps/carotid-right'
            if carotid.exists():
                carotid.rename(work / 'carotid-right')
                reject(staging, broken, 'Incomplete carotid study')
                (work / 'carotid-right').rename(carotid)
                receipt = carotid / 'verification.json'
                original = json.loads(receipt.read_text())
                bad_roi = {**original['detailBoundsMm'], '48': [-100, 2, 20, 15]}
                cases.extend([
                    (receipt, json.dumps({**original, 'modelRecipeSha256': '0' * 64}).encode(), 'current carotid anatomy', False),
                    (receipt, json.dumps({**original, 'detailBoundsMm': bad_roi}).encode(), 'Invalid linear detail bounds', False),
                    (carotid / 'media/detail-scan-48.webp', None, 'Missing sweep input', False),
                    (research / 'acquired/carotid-transverse.webp', b'invalid comparison', 'Unexpected acquired image identity', False),
                ])
            breast = staging / 'sweeps/breast'
            if breast.exists():
                tour = next(tour for tour in tours if tour['id'] == 'breast')
                assert tour['anatomySource']['url'] and tour['simulationNote']
                focused = staging / 'sweeps/breast-subareolar'
                focused.rename(work / 'focused')
                reject(staging, broken, 'Incomplete breast study')
                breast.rename(work / 'breast')
                previous_dir = work / 'without-breast'
                assemble_tours.assemble(staging, previous_dir)
                verify_subset(staging, previous_dir, [tour for tour in tours if tour['id'] not in ('breast', 'breast-subareolar')])
                (work / 'breast').rename(breast)
                (work / 'focused').rename(focused)
                steering_receipt = focused / 'verification.json'
                wrong_pressure = {**json.loads(steering_receipt.read_text()), 'compressionMm': 0}
                receipt = breast / 'verification.json'
                wrong_source = {**json.loads(receipt.read_text()), 'femaleSkinSha256': '0' * 64}
                wrong_render = {**json.loads(receipt.read_text()), 'renderRecipeSha256': '0' * 64}
                missing_rig = read_poses(focused / 'sweep.js')
                del missing_rig[12]['contactRig']
                folded_rig = read_poses(focused / 'sweep.js')
                folded_rig[48]['contactRig']['surfaceMm'][0][0] = -100
                cases.extend([
                    (focused / 'sweep.js', f'const sweep = {json.dumps(missing_rig)};'.encode(),
                     'Invalid seated contact field at frame 12', False),
                    (focused / 'sweep.js', f'const sweep = {json.dumps(folded_rig)};'.encode(),
                     'Invalid seated contact field at frame 48', False),
                    (receipt, json.dumps(wrong_render).encode(), 'current tissue rendering recipe', False),
                    (steering_receipt, json.dumps(wrong_pressure).encode(), 'configured steering and compression', False),
                    (focused / 'media/press-scan-48.webp', None, 'Missing sweep input', False),
                    (receipt, json.dumps(wrong_source).encode(), 'current breast atlas inputs', False),
                    (breast / 'delivery.json', None, 'Missing linear sweep delivery inventory', False),
                    (research / 'acquired/breast-48.webp', b'invalid', 'Unexpected acquired image identity', False),
                ])
            if (staging / 'sweeps/axilla').exists():
                pose_file = staging / 'sweeps/axilla/sweep.js'
                wrong_depth = read_poses(pose_file)
                wrong_depth[12]['imagingDepthMm'] = -1
                cases.append((pose_file, f'const sweep = {json.dumps(wrong_depth)};'.encode(),
                              'Invalid axillary imaging depth at frame 12', False))
                receipt = staging / 'sweeps/axilla/verification.json'
                wrong_skin = {**json.loads(receipt.read_text()), 'femaleSkinSha256': '0' * 64}
                cases.append((receipt, json.dumps(wrong_skin).encode(), 'current axillary exterior', False))
                cases.append((research / 'acquired/axilla-48.webp', b'invalid', 'Unexpected acquired image identity', False))
            maternal = staging / 'sweeps/pregnancy-placenta'
            fetal = staging / 'sweeps/pregnancy-fetus'
            if maternal.exists():
                fetal.rename(work / 'fetal')
                reject(staging, broken, 'Incomplete pregnancy study')
                maternal.rename(work / 'maternal')
                legacy = work / 'without-pregnancy'
                assemble_tours.assemble(staging, legacy)
                previous = javascript_value(legacy / 'abdomen-tours.js', 'abdomenTours')
                assert previous == [tour for tour in tours if tour['id'] not in ('pregnancy-fetus', 'pregnancy-placenta')]
                (work / 'fetal').rename(fetal)
                (work / 'maternal').rename(maternal)
                receipt = maternal / 'verification.json'
                stale_anatomy = {**json.loads(receipt.read_text()), 'pregnancyRecipeSha256': '0' * 64}
                cases.extend([
                    (receipt, json.dumps(stale_anatomy).encode(), 'current pregnancy anatomy', False),
                    (fetal / 'delivery.json', None, 'Missing pregnancy sweep delivery inventory', False),
                    (research / 'acquired/pregnancy-placenta-12.webp', b'invalid',
                     'Unexpected acquired image identity', False),
                ])
            advanced = staging / 'sweeps/pregnancy-mid-heart'
            if advanced.exists():
                advanced.rename(work / 'heart')
                reject(staging, broken, 'Incomplete gestational study')
                (work / 'heart').rename(advanced)
                receipt = advanced / 'verification.json'
                stale_model = {**json.loads(receipt.read_text()), 'modelRecipeSha256': '0' * 64}
                cases.append((receipt, json.dumps(stale_model).encode(), 'current pregnancy anatomy', False))
            early = staging / 'sweeps/pregnancy-early'
            if early.exists():
                cases.extend([
                    (early / 'media/detail-scan-29.webp', None, 'Missing sweep input', False),
                    (early / 'media/detail-section-29.webp', (early / 'media/detail-section-48.webp').read_bytes(),
                     'Sweep delivery identity mismatch', False),
                ])
            survey = staging / 'sweeps/aortic-screening'
            if survey.exists():
                receipt = survey / 'verification.json'
                original = json.loads(receipt.read_text())
                bad_span = read_poses(survey / 'sweep.js')
                bad_span[30]['apSpan']['millimetres'] += 4
                cases.extend([
                    (receipt, json.dumps({**original, 'modelRecipeSha256': '0' * 64}).encode(), 'current aortic survey anatomy', False),
                    (receipt, json.dumps({**original, 'rasterPitchMm': -1}).encode(), 'Invalid aortic raster calibration', False),
                    (survey / 'sweep.js', f'const sweep = {json.dumps(bad_span)};'.encode(), 'Invalid modeled AP span', False),
                    (research / 'acquired/aortic-screening-30.webp', b'invalid comparison', 'Unexpected acquired image identity', False),
                ])
            if bundle.exists():
                seal = bundle / 'verification.json'
                data = json.loads(seal.read_text())
                wrong_torso = {**data['sharedAssets'], 'torso': '0' * 64}
                cases.extend([
                    (seal, None, 'Missing registered AAA acquisition receipt', False),
                    (seal, json.dumps({**data, 'recipeSha256': '0' * 64}).encode(), 'current case and rendering recipes', False),
                    (seal, json.dumps({**data, 'registrationSurfaceSha256': '0' * 64}).encode(), 'CT registration surface', False),
                    (seal, json.dumps({**data, 'sharedAssets': wrong_torso}).encode(), 'selected normal aortic anatomy', False),
                    (bundle / 'assets/aaa-positive/sac-maximum/scan-14.webp', b'wrong image',
                     'AAA acquisition identity mismatch', False),
                ])
            for path, bad, expected, reseal in cases:
                original = path.read_bytes()
                if bad is None:
                    path.unlink()
                else:
                    path.write_bytes(bad)
                if reseal:
                    manifest.write_text(json.dumps({**hashes, str(path.relative_to(aorta)): sha256(bad)}))
                reject(staging, broken, expected)
                path.write_bytes(original)
                if reseal:
                    manifest.write_text(json.dumps(hashes))
        finally:
            assemble_tours.RESEARCH = original_research
    print(f'Compact delivery and {len(cases)} independent assembly failure paths passed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Fully generated staging tree using current builders')
    parser.add_argument('--aaa-acquisitions', type=Path, help='Verify with a separately prepared registered AAA bundle')
    args = parser.parse_args()
    verify(args.source, args.aaa_acquisitions)
