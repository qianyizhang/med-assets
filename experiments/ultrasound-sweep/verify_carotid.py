"""Verify carotid registration, packed contact and native section landmarks."""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import ndimage as nd
from scipy.spatial import cKDTree

import build_carotid as carotid
from build_abdomen import section_palette_sha256
from build_breast import footprint_hits
from delivery import read_poses, sweep_files, verify_inventory
from geometry import FRAME_COUNT, RASTER_SIZE
from verify_breast_contact import deform_skin, load_packed_mesh


BRACHIOCEPHALIC_SHA = 'fd870129e831239d6b1401529219d22321878852a8531d3e7043227830803451'


def verify_vein(case, ct, all_masks):
    vein = all_masks['internal_jugular_vein_right'].astype(bool)
    cca = all_masks['common_carotid_artery_right']
    points = np.column_stack(np.nonzero(vein))
    low = points.min(0) - 3
    high = points.max(0) + 4
    slices = tuple(slice(a, b) for a, b in zip(low, high, strict=True))
    region = vein[slices]
    shell = nd.binary_dilation(region, iterations=2) & ~region
    residual = np.median(ct[slices][region]) - np.median(ct[slices][shell])
    pin = case / 'segmentations/brachiocephalic_vein_right.nii.gz'
    confluent = carotid.volume(pin, BRACHIOCEPHALIC_SHA, 'u1', carotid.SHAPE, carotid.AFFINE)
    distance = cKDTree(np.column_stack(np.nonzero(confluent))).query(points[points[:, 2] == 375])[0].min() * 1.5
    assert nd.label(region)[1] == 1 and not np.any(vein & cca)
    assert list(np.unique(points[:, 2])) == list(range(375, 409))
    assert residual > 60 and distance <= 3
    print(f'Right vein: connected native contrast trace, +{residual:.1f} HU relative to a two-voxel shell; '
          f'{distance:.1f} mm from the source brachiocephalic mask.')


def verify_levelset(raw, levelset):
    points = np.column_stack(np.nonzero(raw))
    bounds = tuple(slice(max(0, a - 3), b + 4)
                   for a, b in zip(points.min(0), points.max(0), strict=True))
    original, smooth = raw[bounds] > 0, levelset[bounds] >= .5
    distances = (nd.distance_transform_edt(~original)[smooth], nd.distance_transform_edt(~smooth)[original])
    assert max(float(values.max()) for values in distances) <= 1


def verify(case, sweeps):
    ct, all_masks, obstruction = carotid.load_inputs(case)
    verify_vein(case, ct, all_masks)
    for track in carotid.read_tracks():
        slug = track['id']
        source = sweeps / slug
        target = track['organ']
        names = [part['id'] for part in track['parts']]
        detail_files = [f'media/detail-{kind}-{index:02}.webp'
                        for index in track['detailFrames'] for kind in ('scan', 'section')]
        if not (source / 'delivery.json').is_file():
            raise ValueError(f'Missing sealed delivery for {slug}')
        verify_inventory(source, sweep_files(['torso', *names]) + detail_files)
        receipt = json.loads((source / 'verification.json').read_text())
        assert receipt['poseRecipeSha256'] == carotid.pose_recipe_sha256(slug)
        assert receipt['modelRecipeSha256'] == carotid.model_recipe_sha256()
        assert receipt['sectionPaletteSha256'] == section_palette_sha256(track)
        assert receipt['ctSha256'] == carotid.CT_SHA and receipt['maskSha256'] == carotid.PINS
        assert set(receipt['frames']) == {str(key['frame']) for key in track['stops']}

        frames = read_poses(source / 'sweep.js')
        assert len(frames) == FRAME_COUNT
        torso = load_packed_mesh(source / 'scenes/torso.mesh')
        residual = []
        for frame in frames:
            rig = frame['contactRig']
            assert rig['faceWidthMm'] == track['fieldWidthMm']
            assert rig['faceElevationMm'] == 6
            assert 1.5 * -np.min(rig['surfaceMm']) < rig['settleDepthMm']
            x = np.linspace(-rig['faceWidthMm'] / 2, rig['faceWidthMm'] / 2, 35)
            y = np.linspace(-rig['faceElevationMm'] / 2, rig['faceElevationMm'] / 2, 15)
            residual.append(footprint_hits(deform_skin(torso, frame, 0), frame, x, y))
        values = np.asarray(residual)
        witness = np.unravel_index(abs(values).argmax(), values.shape)
        print(f'{slug}: packed contact {values.min():.3f} to {values.max():.3f} mm, '
              f'absolute p95 {np.quantile(abs(values), .95):.3f} mm, worst frame {witness[0]}', flush=True)
        assert abs(values).max() <= .8

        line = carotid.centerline(all_masks[target])
        masks = {name: carotid.resolved_vessel(all_masks[name]) if 'carotid' in name or 'jugular' in name
                 else all_masks[name] for name in names}
        for name, smooth in masks.items():
            if 'carotid' in name or 'jugular' in name:
                verify_levelset(all_masks[name], smooth)
        for key in track['stops']:
            index = key['frame']
            frame = frames[index]
            native = receipt['frames'][str(index)]
            anchor = np.asarray(native['beamTargetCaseVox'])
            height = anchor[2]
            normal = np.cross(frame['beam'], frame['width'])
            if index == 12:
                tangent = carotid.location(line, height + 4) - carotid.location(line, height - 4)
                tangent /= np.linalg.norm(tangent)
                degrees = np.rad2deg(np.arccos(np.clip(abs(normal @ tangent), 0, 1)))
                assert degrees < 18
                print(f'  Transverse normal {degrees:.1f}° from the local artery axis.')
            else:
                region = line[abs(line[:, 2] - height) <= 11]
                _, _, basis = np.linalg.svd(region - region.mean(0))
                degrees = np.rad2deg(np.arcsin(np.clip(abs(normal @ basis[0]), 0, 1)))
                active = line[abs(line[:, 2] - height) <= 9]
                residual_mm = abs((active - anchor) @ normal).max() * 1.5
                assert degrees < 4 and residual_mm <= 3.2
                print(f'  Long plane {degrees:.1f}° from the fitted axis, '
                      f'with active native centerline within {residual_mm:.2f} mm.')
            for bounds in (None, receipt['detailBoundsMm'][str(index)]):
                gray, labels, _, pitch = carotid.sample_frame(frame, track, ct, masks, obstruction, bounds)
                observed = carotid.evidence(labels[target], gray, pitch)
                expected = native if bounds is None else native['detail']
                assert observed['imageBounds'] == expected['imageBounds']
                assert observed['largestSectionPixels'] == expected['largestSectionPixels']
                if bounds:
                    x, y, x2, y2 = bounds
                    assert np.isclose(pitch, max((x2 - x) / RASTER_SIZE[0], (y2 - y) / RASTER_SIZE[1]))
                    assert -track['fieldWidthMm'] / 2 <= x < x2 <= track['fieldWidthMm'] / 2
                    assert 0 < y < y2 <= track['sectorDepthMm']
                if index == 12:
                    assert 1 <= observed['elongation'] < 1.55
                    if 'internal_jugular_vein_right' in masks:
                        assert np.count_nonzero(labels['internal_jugular_vein_right']) > 180
                else:
                    assert observed['longWallPairWidthMm'] > 22
            if index == 12 and 'internal_jugular_vein_right' in masks:
                assert native['anatomy']['internal_jugular_vein_right']['largestSectionPixels'] > 180
        print(f'{slug}: verified 49 poses, near-short/long axes and both isotropic native reslices.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('sweeps', type=Path)
    args = parser.parse_args()
    verify(args.case, args.sweeps)


if __name__ == '__main__':
    main()
