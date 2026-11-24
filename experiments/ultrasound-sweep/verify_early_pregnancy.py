"""Check delivered early-pregnancy images against the pose and exported mesh cuts."""

import argparse
from pathlib import Path

import numpy as np

from build_early_pregnancy import CARDIAC_CENTRE, CROWN, FIELDS, RUMP, read_tracks, sample_section
from delivery import detail_files, read_poses, sweep_files, verify_inventory
from geometry import VOXEL_MM
from verify_pregnancy import verify_rasters


def verify(sweeps):
    track, = read_tracks()
    root = sweeps / track['id']
    verify_inventory(root, sweep_files(FIELDS) + detail_files(track['stops']))
    poses = read_poses(root / 'sweep.js')
    for stop in track['stops']:
        frame = stop['frame']
        pose = poses[frame]
        landmarks = track['landmarkMinimums'][str(frame)]
        scores = verify_rasters(root, track, frame, pose, landmarks, sample_section)
        detail_scores = verify_rasters(root, track, frame, pose, landmarks, sample_section, stop['detail']['roi'],
                                       cropped_out=('maternal_bladder',))
        print(f'{track["id"]} {frame}: full Dice {min(scores.values()):.4f}, '
              f'magnified Dice {min(detail_scores.values()):.4f}')

    crl_stop = next(stop for stop in track['stops'] if stop['referenceId'] == 'pregnancy-early-crl')
    crl_pose = poses[crl_stop['frame']]
    plane_normal = np.cross(crl_pose['width'], crl_pose['beam'])
    crl_plane_gaps = np.abs((np.array((CROWN, RUMP)) - np.asarray(crl_pose['contact'])*VOXEL_MM) @ plane_normal)
    if crl_plane_gaps.max() > .6:
        raise ValueError(f'The sweep plane misses a modeled crown–rump endpoint: {crl_plane_gaps}')

    cardiac_stop = next(stop for stop in track['stops'] if stop['referenceId'] == 'pregnancy-early-cardiac')
    cardiac_pose = poses[cardiac_stop['frame']]
    focus = np.subtract(CARDIAC_CENTRE, np.asarray(cardiac_pose['contact'])*VOXEL_MM)
    heart_distance = np.linalg.norm(np.cross(focus, cardiac_pose['beam']))
    if heart_distance > .2:
        raise ValueError(f'The center beam misses the modeled cardiac region by {heart_distance:.2f} mm')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sweeps', type=Path, help='Staging directory that contains the early-pregnancy sweep')
    verify(parser.parse_args().sweeps)
