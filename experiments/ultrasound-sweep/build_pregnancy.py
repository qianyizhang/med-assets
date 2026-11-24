"""Replay two transabdominal sweeps of an authored pregnancy at about 12 weeks."""

import argparse
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation, Slerp

from build_abdomen import ImagingGrid, axes, measure_landmark, overlay, section_palette, section_palette_sha256
from build_study import fine_scatter
from delivery import sha256, sweep_files, write_manifest
from fit_abdomen import outer_contact_offsets
from geometry import FRAME_COUNT, KEYFRAMES, LENS_RADIUS_MM, SECTOR_HALF_ANGLE_DEG, VOXEL_MM
import pregnancy_anatomy as anatomy
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
TRACK_PATH = HERE / 'pregnancy-tracks.json'
STATIONS = (0, *KEYFRAMES)
FETAL_INTERNAL = ('spinal_echoes', 'fetal_bladder', 'calvarium', 'falx', 'choroid_plexus')


def read_pregnancy_tracks():
    data = json.loads(TRACK_PATH.read_text())
    return [{**data['shared'], **sweep} for sweep in data['sweeps']]


def pose_recipe_sha256(sweep_id):
    track = next(track for track in read_pregnancy_tracks() if track['id'] == sweep_id)
    return sha256(json.dumps([STATIONS, track['windows'], track['landmarkMinimums']],
                             separators=(',', ':')).encode())


def pregnancy_recipe_sha256():
    return sha256(Path(__file__).read_bytes() + Path(anatomy.__file__).read_bytes())


def poses(track, exterior):
    windows = track['windows']
    stations = np.asarray([window['skinSiteMm'] for window in windows])
    rotations = Rotation.from_matrix([axes(window['outward'], window['marker']) for window in windows])
    turn = Slerp(STATIONS, rotations)
    out = []
    for i in range(FRAME_COUNT):
        x, z = [np.interp(i, STATIONS, sites) for sites in stations.T]
        y = brentq(lambda y: anatomy.torso((x, y, z)), 0, 120)
        pose = turn(i)
        width, _, beam = pose.as_matrix().T
        out.append({
            'contact': (np.array([x, y, z]) / VOXEL_MM).tolist(),
            'width': width.tolist(), 'beam': beam.tolist(),
            'degrees': round(np.rad2deg((pose * rotations[0].inv()).magnitude()), 1),
        })

    contacts, beams = (np.array([frame[key] for frame in out]) for key in ('contact', 'beam'))
    # Measure first incoming hits against the exported triangular skin, in
    # addition to finding the corresponding analytic central contact.
    residuals = outer_contact_offsets(*exterior, contacts, beams)
    max_contact = float(np.max(np.abs(residuals)))
    if max_contact > .2:
        raise ValueError(f'Pregnancy central contact differs from the exterior mesh by {max_contact:.2f} mm')
    movement = np.linalg.norm(np.diff(contacts, axis=0), axis=1) * VOXEL_MM
    if movement.min() < .2 or movement.max() > 3:
        raise ValueError(f'Skin contact fails to slide continuously: {movement.min():.2f}–{movement.max():.2f} mm/frame')
    return out, {
        'surfaceMaxOuterContactErrorMm': round(max_contact, 3),
        'skinTravelMm': round(float(movement.sum()), 2),
    }


def sample_section(grid, frame):
    xyz = grid.coordinates(frame, grid.x, grid.y)
    mm = xyz * VOXEL_MM
    fields = {name: fn(mm) for name, (fn, _, _, _) in anatomy.FIELDS.items()}
    labels = {name: (field <= 0) & grid.field for name, field in fields.items()}

    # Make the major section fill masks disjoint where volumes represent
    # boundaries and their contents. Use exact analytic masks for evidence.
    regions = {name: mask & labels['torso'] for name, mask in labels.items()}
    fetal_organs = np.logical_or.reduce([labels[name] for name in FETAL_INTERNAL])
    regions['fetus'] &= ~fetal_organs
    regions['amniotic_fluid'] &= ~(
        labels['fetus'] | labels['placenta'] | labels['umbilical_cord'])
    regions['umbilical_cord'] &= ~(labels['fetus'] | labels['placenta'])
    skin_distance = -fields['torso']
    fine = fine_scatter(xyz)
    coarse_noise = fine_scatter(xyz * .31)
    speckle = 99 * fine + 25 * coarse_noise
    tissue = 44 + speckle
    superficial_fat = np.exp(-((skin_distance - 7 - 2 * coarse_noise) / 5.8)**2)
    tissue -= superficial_fat * (12 + .28 * speckle)
    tissue += 16 * np.exp(-((skin_distance - 17 - 2 * coarse_noise) / 4)**2)
    tissue += 34 * np.exp(-((skin_distance - 14 - 2 * coarse_noise) / 1.3)**2)
    # A face-on midsagittal slice grazes the thin falx. Its axial crossing
    # returns a brighter line while the grazing midline signal stays weak.
    plane_normal = np.cross(frame['width'], frame['beam'])
    falx_strength = 1 - abs(plane_normal[0])
    ventricle = np.clip((1.3 - fields['choroid_plexus']) / 1.4, 0, 1)
    ventricle *= np.clip((-anatomy.cranium(mm) - 1.9) / 1.5, 0, 1)
    fetal_stroma = 47 + .83 * speckle + 24 * nd.gaussian_filter(coarse_noise, (.8, 1.9))
    fetal_stroma *= 1 - .61 * ventricle
    profile = (
        ('uterus', 61 + .98 * speckle),
        ('amniotic_fluid', 4 + .12 * speckle),
        ('maternal_bladder', 3 + .095 * speckle),
        ('placenta', 78 + 1.05 * speckle + 13 * coarse_noise),
        ('umbilical_cord', 72 + .96 * speckle),
        ('fetus', fetal_stroma),
        ('fetal_bladder', 5 + .10 * speckle),
        ('spinal_echoes', 192 + .41 * speckle),
        ('calvarium', 190 + .39 * speckle),
        ('falx', 62 + 119 * falx_strength + .4 * speckle),
        ('choroid_plexus', 126 + .86 * speckle),
    )
    for tissue_id, return_level in profile:
        tissue = np.where(regions[tissue_id], return_level, tissue)

    # Interfaces that face the beam are stronger than tangential interfaces.
    soft = nd.gaussian_filter(tissue, (.7, 1))
    dy, dx = np.gradient(soft)
    edge = np.abs(dy * np.cos(grid.angle) + dx * np.sin(grid.angle))
    skin = np.exp(-((skin_distance - .7) / .85)**2)
    gray = (soft + 1.25 * edge + 83 * skin) * np.exp(-np.maximum(grid.depth, 0) / 275)
    gray = np.where(grid.field & labels['torso'], np.clip(gray, 0, 243), 0).astype(np.uint8)
    return gray, labels, regions


def check_anatomy(meshes):
    # Evaluate exported boundaries against the analytic spatial relationships.
    millimetres = {name: vertices.T * VOXEL_MM for name, (vertices, _) in meshes.items()}
    margins = {name: -float(anatomy.torso(points).max())
               for name, points in millimetres.items() if name != 'torso'}
    if min(margins.values()) < 0:
        raise ValueError(f'Anatomy extends beyond the maternal exterior: {margins}')
    fetal_margin = -float(anatomy.cavity(millimetres['fetus']).max())
    if fetal_margin < 0 or np.min(anatomy.placenta(millimetres['fetus'])) <= 0:
        raise ValueError('The fetus must fit within the sac and clear the placental surface')
    end_fetus = float(anatomy.fetus(tuple(anatomy.CORD_POINTS[0])))
    end_placenta = float(anatomy.placenta(tuple(anatomy.CORD_POINTS[-1])))
    if max(end_fetus, end_placenta) >= 0:
        raise ValueError('The cord does not join both the fetus and the placenta')
    return {
        'minMaternalSkinClearanceMm': round(min(margins.values()), 2),
        'minFetalCavityClearanceFieldMm': round(fetal_margin, 2),
        'cordInsertionSignedFieldMm': [round(end_fetus, 2), round(end_placenta, 2)],
    }


def posterior_wall_rays(grid, frame):
    xyz = grid.coordinates(frame, grid.polar_x, grid.polar_y) * VOXEL_MM
    placenta = anatomy.placenta(xyz) <= 0
    uterus = anatomy.uterus(xyz) <= 0
    steps = np.arange(len(placenta))[:, None]
    far_edge = np.where(placenta, steps, -1).max(axis=0)
    behind = (steps > far_edge) & (steps <= far_edge + 9)
    return int(np.count_nonzero((far_edge >= 0) & np.any(uterus & behind, axis=0)))


def build_track(track, output, meshes, mesh_data, anatomy_receipt):
    frames, contact_receipt = poses(track, meshes['torso'])
    palette = section_palette(track)
    grid = ImagingGrid(track['sectorDepthMm'])
    names = ['torso', *(part['id'] for part in track['parts'])]
    media, scenes = output / 'media', output / 'scenes'
    media.mkdir()
    scenes.mkdir()
    for name in names:
        (scenes / f'{name}.mesh').write_bytes(mesh_data[name])
    evidence = {}
    for i, frame in enumerate(frames):
        gray, labels, regions = sample_section(grid, frame)
        if np.count_nonzero(labels[track['organ']]) < 350:
            raise ValueError(f'{track["id"]} frame {i} misses the sweep target')
        if i in KEYFRAMES:
            measured = {name: measure_landmark(labels[name], gray) for name in names if name != 'torso'}
            minimums = track['landmarkMinimums'][KEYFRAMES.index(i)]
            for name, minimum in minimums.items():
                if measured[name]['largestSectionPixels'] < minimum:
                    raise ValueError(f'{track["id"]} frame {i} misses {name}: {measured[name]}')
            if track['organ'] == 'placenta':
                wall_rays = posterior_wall_rays(grid, frame)
                if wall_rays < 35:
                    raise ValueError(f'Frame {i} has insufficient depth to show wall beyond the placenta')
                measured['posteriorWallRays'] = wall_rays
            evidence[str(i)] = measured
        Image.fromarray(gray).save(media / f'scan-{i:02}.webp', quality=91)
        Image.fromarray(overlay(gray, regions, palette)).save(media / f'section-{i:02}.webp', quality=88)
    (output / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    (output / 'verification.json').write_text(json.dumps({
        'case': track['case'],
        'coordinateFrame': 'authored maternal RAS in 1.5 mm scene units',
        'voxelMm': VOXEL_MM,
        'exterior': track['exterior'],
        'sectorDepthMm': track['sectorDepthMm'],
        'sectorHalfAngleDeg': SECTOR_HALF_ANGLE_DEG,
        'lensRadiusMm': LENS_RADIUS_MM,
        'poseRecipeSha256': pose_recipe_sha256(track['id']),
        'pregnancyRecipeSha256': pregnancy_recipe_sha256(),
        'sectionPaletteSha256': section_palette_sha256(track),
        **contact_receipt,
        **anatomy_receipt,
        'frames': evidence,
    }, indent=2) + '\n')
    write_manifest(output, sweep_files(names))
    print(f'{track["id"]}: {len(frames)} poses, {contact_receipt["skinTravelMm"]:.1f} mm skin travel, '
          f'{contact_receipt["surfaceMaxOuterContactErrorMm"]:.3f} mm maximum central contact error', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sweeps_dir', type=Path)
    args = parser.parse_args()
    tracks = read_pregnancy_tracks()
    if any((args.sweeps_dir / track['id']).exists() for track in tracks):
        parser.error('Choose a fresh destination for the pregnancy sweeps.')
    meshes = {name: anatomy.mesh_for(name) for name in anatomy.FIELDS}
    anatomy_receipt = check_anatomy(meshes)
    mesh_data = {name: mesh_bytes(*mesh) for name, mesh in meshes.items()}
    args.sweeps_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.sweeps_dir) as stage:
        staging = Path(stage)
        for track in tracks:
            output = staging / track['id']
            output.mkdir()
            build_track(track, output, meshes, mesh_data, anatomy_receipt)
        for track in tracks:
            (staging / track['id']).rename(args.sweeps_dir / track['id'])


if __name__ == '__main__':
    main()
