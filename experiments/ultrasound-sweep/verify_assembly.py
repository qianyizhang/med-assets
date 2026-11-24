"""Exercise compact assembly and reject corrupt staged study inputs."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

import assemble_tours
from delivery import read_poses, sha256


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


def verify(source):
    with tempfile.TemporaryDirectory() as work:
        work = Path(work)
        staging = work / 'staging'
        destination = work / 'delivery'
        shutil.copytree(source, staging)
        research = work / 'research'
        shutil.copytree(assemble_tours.RESEARCH, research)
        original_research = assemble_tours.RESEARCH
        assemble_tours.RESEARCH = research
        try:
            assemble_tours.assemble(staging, destination)
            tours = javascript_value(destination / 'abdomen-tours.js', 'abdomenTours')
            references = javascript_value(destination / 'references.js', 'abdomenReferences')
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
                expected = [0, 12, 48] if tour['id'].startswith('thyroid-') else [12, 48]
                assert [key['frame'] for key in tour['keyframes']] == expected
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
            right = staging / 'sweeps/thyroid-right'
            if right.exists():
                left = staging / 'sweeps/thyroid-left'
                thyroid = [tour for tour in tours if tour['id'] in ('thyroid-left', 'thyroid-right')]
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
                previous = javascript_value(abdomen / 'abdomen-tours.js', 'abdomenTours')
                assert previous == [tour for tour in tours if tour['id'] not in ('thyroid-left', 'thyroid-right')]
                (work / 'left').rename(left)
                (work / 'right').rename(right)
                receipt = right / 'verification.json'
                wrong_field = {**json.loads(receipt.read_text()), 'fieldWidthMm': -1}
                cases.extend([
                    (receipt, json.dumps(wrong_field).encode(), 'configured linear field', False),
                    (right / 'delivery.json', None, 'Missing linear sweep delivery inventory', False),
                    (research / 'acquired/thyroid-isthmus.webp', b'invalid', 'Unexpected acquired image identity', False),
                ])
            breast = staging / 'sweeps/breast'
            if breast.exists():
                tour = next(tour for tour in tours if tour['id'] == 'breast')
                assert tour['anatomySource']['url'] and tour['simulationNote']
                breast.rename(work / 'breast')
                previous_dir = work / 'without-breast'
                assemble_tours.assemble(staging, previous_dir)
                previous = javascript_value(previous_dir / 'abdomen-tours.js', 'abdomenTours')
                assert previous == [tour for tour in tours if tour['id'] != 'breast']
                (work / 'breast').rename(breast)
                receipt = breast / 'verification.json'
                wrong_source = {**json.loads(receipt.read_text()), 'femaleSkinSha256': '0' * 64}
                cases.extend([
                    (receipt, json.dumps(wrong_source).encode(), 'current breast atlas inputs', False),
                    (breast / 'delivery.json', None, 'Missing linear sweep delivery inventory', False),
                    (research / 'acquired/breast-48.webp', b'invalid', 'Unexpected acquired image identity', False),
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
    verify(parser.parse_args().source)
