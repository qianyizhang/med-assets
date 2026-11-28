"""Build bilateral linear thyroid sweeps on the pinned TotalSegmentator s1127 case."""

import argparse
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial.transform import Rotation, Slerp
from skimage.measure import marching_cubes

from build_abdomen import (
    axes, contact_point, measure_landmark, mesh_from_mask, overlay, section_palette, section_palette_sha256,
)
from build_study import body_surface, fine_scatter, material_at, volume
from scene_assets import scene_assets
from delivery import sha256, sweep_files, write_manifest
from display_neck import fitted_neck
from fit_abdomen import outer_contact_offsets
from geometry import FRAME_COUNT, KEYFRAMES, RASTER_SIZE, VOXEL_MM
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
CASE = 's1127'
CT_SHA = '4367b68d8c8e339ef52edbb819b53f199cf807b7475e0693190b5427e3f1c032'
SHAPE = (275, 275, 409)
AFFINE = np.eye(4) * [VOXEL_MM, VOXEL_MM, VOXEL_MM, 1]
AFFINE[:3, 3] = [-191.59765625, -35.09765625, -311.0]
PINS = {
    'thyroid_gland': '90e46bd16d3395fab1bad27506a05211ca7e17660380e69ff90e456a61ca5fc0',
    'trachea': 'f7f88b8117b623a0b8c8eb7dba46498627da5afa115002ba879a664e02a624fe',
    'common_carotid_artery_left': '1afcd7bef5e969daa5b4f09788dfabbd05d4a8fd260a140b90370e957e70fb10',
    'common_carotid_artery_right': 'b96238f9bac2dab4a3467d5036816972dfc49529f2ba526fe8659a443c5281e2',
}
OBSTRUCTION_PINS = {
    'clavicula_left': '3430ddb4a58e7f160cf1da567f42b6d81f9104e0d6eb6eb021877e6c7d11c770',
    'clavicula_right': 'fceccff51b1e297a94c54157a7e895267c4d8054af35bb5687d966e83889d95d',
    'sternum': '51492ef613fe15778e67cc8b997e2914ae5fc3ddca25e3e65de7a472abc88e5e',
}
ROI_FLOOR = 344
# RAS X divider between the two visual teaching lobes at the sampled levels.
LOBE_DIVIDER_X = 131.5
ENTRY = ((134.6, 132, 382), (.08, 1, .25), (1, 0, 0))
TEACHING_FRAMES = (0, *KEYFRAMES)
# Coordinates on the source RAS grid, with the marker at image-left.
# Transverse: marker toward patient right. Longitudinal: marker toward the head.
POSES = {
    'thyroid-right': (
        ((135.067, 131, 382.904), (-.15965, 1, .1252), (1, 0, 0)),
        ((139.033, 135.134, 380.188), (.13836, 1, .14086), (.28656, 0, 1)),
    ),
    'thyroid-left': (
        ((121.166, 131, 381.916), (.22825, 1, -.08968), (1, 0, 0)),
        ((125.733, 133.668, 382.851), (.03411, 1, -.01726), (-.34251, 0, 1)),
    ),
}


def read_thyroid_tracks():
    recipe = json.loads((HERE / 'thyroid-tracks.json').read_text())
    common = recipe['common']
    parts = [{'id': key, **recipe['structures'][key]} for key in common['parts']]
    return [{**common, **sweep, 'parts': parts} for sweep in recipe['sweeps']]


def pose_recipe_sha256(sweep_id):
    recipe = {'keyframes': list(zip(TEACHING_FRAMES, (ENTRY, *POSES[sweep_id]), strict=True)),
              'angleOriginFrame': 0}
    return sha256(json.dumps(recipe, separators=(',', ':')).encode())


def poses(sweep_id, shell):
    authored = (ENTRY, *POSES[sweep_id])
    targets = np.array([pose[0] for pose in authored])
    orientations = Rotation.from_matrix([axes(*pose[1:]) for pose in authored])
    path = Slerp(TEACHING_FRAMES, orientations)
    for i in range(FRAME_COUNT):
        start, end = (0, 1) if i < KEYFRAMES[0] else (1, 2)
        fraction = (i - TEACHING_FRAMES[start]) / (TEACHING_FRAMES[end] - TEACHING_FRAMES[start])
        rotation = path(i)
        width, _, beam = rotation.as_matrix().T
        target = (1 - fraction) * targets[start] + fraction * targets[end]
        contact = contact_point(target, beam, shell)
        yield {'contact': contact.tolist(), 'width': width.tolist(), 'beam': beam.tolist(),
               'degrees': round(np.rad2deg((rotation * orientations[0].inv()).magnitude()), 1)}


def neck_surface(shell):
    # Keep the measured anterior surface. Cap the regional cut through the upper
    # chest and the original superior scan boundary. There is no reconstructed head.
    neck = np.pad(shell[:, :, ROI_FLOOR // 2:], 1)
    vertices, faces, _, _ = marching_cubes(neck, .5)
    return (vertices - 1) * 2 + [0, 0, ROI_FLOOR], faces[:, ::-1]


def section_grid(track):
    width, height = RASTER_SIZE
    rows, cols = np.mgrid[:height, :width]
    pitch = track['sectorDepthMm'] / (height - 14)
    x = (cols + .5 - width / 2) * pitch
    y = (rows + .5 - 7) * pitch
    field = (np.abs(x) <= track['fieldWidthMm'] / 2) & (y >= 0) & (y <= track['sectorDepthMm'])
    return x, y, field


def sampled_mask(mask, xyz):
    return nd.map_coordinates(mask, xyz, order=0, mode='constant', prefilter=False) > 0


def center_beam_depths(contacts, beams, gland, obstructions, depth_mm):
    depth = np.arange(0, depth_mm + .25, .25)
    rays = contacts[:, None, :] + beams[:, None, :] * depth[None, :, None] / VOXEL_MM
    rays = rays.transpose(2, 0, 1)
    target = sampled_mask(gland, rays)
    bone = sampled_mask(obstructions, rays)
    hits = []
    for i, (surface, opaque) in enumerate(zip(target, bone, strict=True)):
        hit = np.flatnonzero(surface)
        if not len(hit):
            raise ValueError(f'Central beam misses thyroid at frame {i}')
        if opaque[:hit[0]].any():
            raise ValueError(f'Central beam meets a clavicle or sternum before thyroid at frame {i}')
        hits.append([float(depth[hit[0]]), float(depth[hit[-1]])])
    return hits


def sample(frame, ct, masks, grid):
    x, y, field = grid
    contact, width, beam = (np.asarray(frame[k]) for k in ('contact', 'width', 'beam'))
    xyz = contact[:, None, None] + (width[:, None, None] * x + beam[:, None, None] * y) / VOXEL_MM
    hu = nd.gaussian_filter(material_at(ct, xyz), (.65, .75))
    labels = {key: (material_at(mask, xyz) >= .5) & field for key, mask in masks.items()}
    thyroid = nd.gaussian_filter(labels['thyroid_gland'].astype('f'), 1)
    lumen = nd.gaussian_filter(np.logical_or.reduce([mask for key, mask in labels.items()
                                                   if 'carotid' in key]).astype('f'), 1)
    # Approximate echo brightness and shadow from HU and local tissue labels. The
    # reference images are separately acquired and have no pixel registration.
    baseline = 42 + np.clip((hu + 67) * .21, -24, 28) + 31 * thyroid
    interface = np.clip(np.abs(np.gradient(hu, axis=0)) * 3.2, 0, 113)
    # A weak depth-oriented return at the source label interface and a lower
    # local scatter amplitude distinguish parenchyma without tracing a contour.
    interface += np.abs(np.gradient(thyroid, axis=0)) * 21
    speckle = 76 * fine_scatter(xyz) + 35 * fine_scatter(xyz + np.array([.39, .15, .61])[:, None, None])
    speckle *= 1 - .38 * thyroid
    bone = np.clip((hu - 205) / 390, 0, 1)
    air = np.clip((-hu - 360) / 500, 0, 1)
    attenuation = np.exp(-nd.gaussian_filter(np.cumsum((bone + air) * (y > 4), axis=0), (1.1, 2.0)) * .054)
    gray = (baseline + interface + speckle) * (1 - .91 * lumen) * attenuation
    gray *= np.exp(-np.maximum(y, 0) / 215)
    return np.where(field, np.clip(gray, 1, 245), 0).astype('u1'), labels, xyz


def aperture_profile(body, contacts, beams, widths, width_mm):
    aperture = np.linspace(-width_mm / 2, width_mm / 2, 17)
    origins = contacts[:, None] + widths[:, None] * aperture[None, :, None] / VOXEL_MM
    offsets = outer_contact_offsets(*body, origins.reshape(-1, 3), np.repeat(beams, len(aperture), axis=0))
    offsets = offsets.reshape(-1, len(aperture))
    return offsets, {'lateralMm': aperture.tolist(),
                     'minSignedFirstHitMm': offsets.min(0).round(3).tolist(),
                     'maxSignedFirstHitMm': offsets.max(0).round(3).tolist()}


def build_one(track, out, ct, frames, case_body, display_body, display_receipt, masks, obstructions, meshes):
    sweep_id = track['id']
    side = sweep_id.removeprefix('thyroid-')
    names = ('torso', *masks)
    contacts, beams, widths = (np.array([frame[key] for frame in frames]) for key in ('contact', 'beam', 'width'))
    case_offsets, case_profile = aperture_profile(case_body, contacts, beams, widths, track['fieldWidthMm'])
    display_offsets, display_profile = aperture_profile(display_body, contacts, beams, widths, track['fieldWidthMm'])
    center = case_offsets.shape[1] // 2
    case_error = float(np.max(np.abs(case_offsets[:, center])))
    contact_error = float(np.max(np.abs(display_offsets[:, center])))
    if max(case_error, contact_error) > .5:
        raise ValueError(f'{sweep_id}: first incoming contact residual exceeds 0.5 mm '
                         f'(CT {case_error:.3f}, fitted display {contact_error:.3f})')
    if case_offsets.min() < -5:
        raise ValueError(f'{sweep_id}: planar aperture intersects the native CT by {-case_offsets.min():.1f} mm')

    center_depths = center_beam_depths(contacts, beams, masks['thyroid_gland'], obstructions, track['sectorDepthMm'])
    grid = section_grid(track)
    palette = section_palette(track)
    frames_evidence = {}
    media = out / 'media'
    media.mkdir()
    scenes = out / 'scenes'
    scenes.mkdir()
    for name, raw in (meshes | scene_assets(track)).items():
        (scenes / f'{name}.mesh').write_bytes(raw)
    for i, frame in enumerate(frames):
        gray, labels, xyz = sample(frame, ct, masks, grid)
        on_target_side = (xyz[0] >= LOBE_DIVIDER_X) if side == 'right' else (xyz[0] < LOBE_DIVIDER_X)
        target = measure_landmark(labels['thyroid_gland'] & on_target_side, gray)
        if target['largestSectionPixels'] < 1000:
            raise ValueError(f'{sweep_id}: lobe missing at frame {i} ({target["largestSectionPixels"]} pixels)')
        if i in TEACHING_FRAMES:
            evidence = {key: measure_landmark(mask, gray) for key, mask in labels.items()}
            evidence['target_lobe'] = target
            bones = sampled_mask(obstructions, xyz)
            behind_bone = np.maximum.accumulate(bones & grid[2], axis=0)
            target_mask = labels['thyroid_gland'] if i == 0 else labels['thyroid_gland'] & on_target_side
            fraction = np.count_nonzero(target_mask & behind_bone) / np.count_nonzero(target_mask)
            evidence['targetLobeBehindBoneFraction'] = round(fraction, 4)
            evidence['centerBeamThyroidDepthMm'] = center_depths[i]
            if fraction > .2:
                raise ValueError(f'{sweep_id}: bone precedes {fraction:.0%} of target section at frame {i}')
            if i in (0, KEYFRAMES[0]):
                trachea = evidence['trachea']
                if trachea['largestSectionPixels'] < 130:
                    raise ValueError(f'{sweep_id}: missing transverse trachea at frame {i}')
                carotid = f'common_carotid_artery_{side}'
                if i == KEYFRAMES[0] and evidence[carotid]['largestSectionPixels'] < 130:
                    raise ValueError(f'{sweep_id}: missing transverse {carotid} at frame {i}')
                bridged = labels['thyroid_gland'] & (np.abs(xyz[0] - LOBE_DIVIDER_X) < 1.25)
                evidence['thyroid_midline'] = measure_landmark(bridged, gray)
                if evidence['thyroid_midline']['largestSectionPixels'] < 80:
                    raise ValueError(f'{sweep_id}: transverse misses the gland at the midline at frame {i}')
                if i == 0:
                    bridge_before_airway = np.nonzero(bridged)[0].mean() < np.nonzero(labels['trachea'])[0].mean()
                    connected, _ = nd.label(labels['thyroid_gland'])
                    bridge_component = np.bincount(connected[bridged])[1:].argmax() + 1
                    shared = connected == bridge_component
                    for lobe, side_mask in (('right', xyz[0] >= LOBE_DIVIDER_X), ('left', xyz[0] < LOBE_DIVIDER_X)):
                        evidence[f'{lobe}_lobe'] = measure_landmark(shared & side_mask, gray)
                    if (not bridge_before_airway or any(evidence[f'{lobe}_lobe']['largestSectionPixels'] < 1200
                                                         for lobe in ('right', 'left'))):
                        raise ValueError(f'{sweep_id}: frame 0 misses the bilateral bridge anterior to the trachea')
            frames_evidence[str(i)] = evidence
        Image.fromarray(gray).save(media / f'scan-{i:02}.webp', quality=91)
        Image.fromarray(overlay(gray, labels, palette)).save(media / f'section-{i:02}.webp', quality=88)

    (out / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    (out / 'verification.json').write_text(json.dumps({
        'case': CASE, 'coordinateFrame': 's1127 voxel coordinates with RAS axes',
        'rasMmFromVoxel': AFFINE.tolist(), 'sourceGridShape': SHAPE, 'voxelMm': track['voxelMm'],
        'probeType': track['probeType'], 'fieldShape': track['fieldShape'], 'angleOriginFrame': 0,
        'fieldWidthMm': track['fieldWidthMm'], 'sectorDepthMm': track['sectorDepthMm'],
        'exterior': track['exterior'], 'ctNeckValidationZVox': [ROI_FLOOR, SHAPE[2] - 1],
        'surfaceCaseCtMaxOuterContactErrorMm': round(case_error, 3),
        'surfaceMaxOuterContactErrorMm': round(contact_error, 3),
        'caseCtApertureOffsetsMm': case_profile, 'atlasDisplayApertureOffsetsMm': display_profile,
        **display_receipt,
        'ctSha256': CT_SHA, 'maskSha256': PINS, 'obstructionMaskSha256': OBSTRUCTION_PINS,
        'centralBeamObstructionFrames': [],
        'poseRecipeSha256': pose_recipe_sha256(sweep_id), 'sectionPaletteSha256': section_palette_sha256(track),
        'glandConnectedComponents': 1, 'glandSourceVoxelBounds': [[117, 116, 372], [148, 140, 398]],
        'targetSide': side, 'lobeDividerXVox': LOBE_DIVIDER_X, 'frames': frames_evidence,
    }, indent=2) + '\n')
    write_manifest(out, sweep_files(names))
    print(f'{sweep_id}: first incoming contact error ≤ {contact_error:.3f} mm', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('sweeps_dir', type=Path)
    parser.add_argument('--track', choices=POSES, action='append')
    args = parser.parse_args()
    tracks = [track for track in read_thyroid_tracks() if args.track is None or track['id'] in args.track]
    for track in tracks:
        if (args.sweeps_dir / track['id']).exists():
            parser.error(f'Choose a fresh destination for {track["id"]}.')
    ct = volume(args.case / 'ct.nii.gz', CT_SHA, '<i2', SHAPE, AFFINE)
    masks = {key: volume(args.case / f'segmentations/{key}.nii.gz', digest, 'u1', SHAPE, AFFINE)
             for key, digest in PINS.items()}
    obstructions = np.zeros(SHAPE, dtype='u1')
    for key, digest in OBSTRUCTION_PINS.items():
        obstructions |= volume(args.case / f'segmentations/{key}.nii.gz', digest, 'u1', SHAPE, AFFINE)
    xyz = np.column_stack(np.nonzero(masks['thyroid_gland']))
    if (nd.label(masks['thyroid_gland'])[1] != 1
            or not np.array_equal([xyz.min(0), xyz.max(0)], [[117, 116, 372], [148, 140, 398]])):
        raise ValueError('Unexpected thyroid continuity or source extent')
    shell, _, _ = body_surface(ct)
    case_body = neck_surface(shell)
    sequences = {sweep_id: list(poses(sweep_id, shell)) for sweep_id in POSES}
    # Both lobes share a single body. Fit against the same bilateral union even
    # when replaying just one track, so the eventual mesh identity is stable.
    all_frames = [frame for sequence in sequences.values() for frame in sequence]
    contacts, beams = (np.array([frame[key] for frame in all_frames]) for key in ('contact', 'beam'))
    vertices, faces, display_receipt = fitted_neck(args.case, shell, contacts, beams, shape=SHAPE, affine=AFFINE)
    display_body = (vertices, faces)
    meshes = {'torso': mesh_bytes(*display_body)}
    for name, mask in masks.items():
        meshes[name] = mesh_from_mask(mask, (ROI_FLOOR, SHAPE[2]) if name != 'thyroid_gland' else None)
    args.sweeps_dir.mkdir(parents=True, exist_ok=True)
    for track in tracks:
        with tempfile.TemporaryDirectory(dir=args.sweeps_dir) as staging:
            output = Path(staging) / track['id']
            output.mkdir()
            build_one(track, output, ct, sequences[track['id']], case_body, display_body,
                      display_receipt, masks, obstructions, meshes)
            output.rename(args.sweeps_dir / track['id'])


if __name__ == '__main__':
    main()
