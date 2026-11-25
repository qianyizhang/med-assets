"""Check delivered mid- and late-trimester images and meshes at the named probe poses."""
import argparse
from functools import partial
import json
from pathlib import Path

import numpy as np

from build_gestational import Gestation, delivery_files, read_tracks, sample_section
from delivery import read_poses, verify_inventory
from verify_pregnancy import verify_rasters


def verify(sweeps):
    for track in read_tracks():
        root = sweeps / track['id']
        verify_inventory(root, delivery_files(track))
        poses = read_poses(root / 'sweep.js')
        receipt = json.loads((root / 'verification.json').read_text())
        sampler = partial(sample_section, Gestation(track['pregnancyStage']), track)
        windows = {window['frame']: window for window in track['windows']}
        for stop in track['stops']:
            frame = stop['frame']
            pose = poses[frame]
            observed = receipt['frames'][str(frame)]
            contacts_mm = np.asarray(pose['contact']) * track['voxelMm']
            if not np.allclose(contacts_mm, observed['contactRasMm'], atol=.001):
                raise ValueError(f'{root.name} frame {frame}: pose and receipt disagree on skin contact')
            landmarks = windows[frame]['minimums']
            if not set(landmarks).issubset(observed['landmarks']):
                raise ValueError(f'{root.name} frame {frame}: landmark list differs from the track')
            scores = verify_rasters(root, track, frame, pose, landmarks, sampler)
            if roi := receipt['detailRois'].get(str(frame)):
                detail = verify_rasters(root, track, frame, pose, landmarks, sampler, roi)
                scores.update({f'detail {name}': value for name, value in detail.items()})
            print(f'{root.name} {frame} · {stop["label"]} · lowest mesh/section Dice {min(scores.values()):.4f}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sweeps', type=Path, help='Staging directory containing the mid- and late-trimester sweeps')
    verify(parser.parse_args().sweeps)
