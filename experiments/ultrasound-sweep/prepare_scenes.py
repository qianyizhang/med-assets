"""Stage the registered 3D view in an existing gallbladder sweep build."""

import argparse
import hashlib
import json
import shutil
import struct
import urllib.request
from pathlib import Path

import numpy as np

from delivery import read_poses, sweep_files, write_manifest
from display_body import fitted_surface, check_contacts
from geometry import (
    LENS_RADIUS_MM,
    PIP_POSITION,
    PIP_SCALE,
    PROBE_RINGS,
    SECTOR_DEPTH_MM,
    SECTOR_HALF_ANGLE_DEG,
    VOXEL_MM,
    probe_geometry,
)

HERE = Path(__file__).resolve().parent
VENDOR_FIXTURE = HERE.parents[1] / 'tests/runtime/glb-runtime-fixture.json'
VENDOR_PATHS = {'vendor/LICENSE', 'vendor/build/three.core.js', 'vendor/build/three.module.js'}


def mesh_bytes(vertices, triangles):
    """Write counts followed by XYZ positions and triangle indices, all little endian."""
    positions = np.ascontiguousarray(vertices, dtype='<f4')
    indices = np.ascontiguousarray(triangles, dtype='<u4')
    if (not len(positions) or positions.ndim != 2 or positions.shape[1] != 3
            or not np.isfinite(positions).all() or indices.ndim != 2 or indices.shape[1] != 3
            or not len(indices) or np.max(indices) >= len(positions)):
        raise ValueError('Invalid scene mesh positions or triangle indices')
    return struct.pack('<2I', len(positions), len(indices)) + positions.tobytes() + indices.tobytes()


def read_vendor(vendor_dir):
    fixture = json.loads(VENDOR_FIXTURE.read_text())
    files = {}
    for item in fixture['resources']:
        path = item['path']
        if path not in VENDOR_PATHS:
            continue
        if vendor_dir is None:
            with urllib.request.urlopen(item['url'], timeout=45) as response:
                raw = response.read()
        else:
            raw = (vendor_dir / path.removeprefix('vendor/')).read_bytes()
        if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError(f'Three.js dependency identity mismatch: {path}')
        files[path] = raw
    if files.keys() != VENDOR_PATHS:
        raise ValueError('Incomplete Three.js fixture')
    return files


def shared_geometry():
    files = {}
    for name, rings in PROBE_RINGS.items():
        positions, faces = probe_geometry(rings)
        triangles = [(face[0], face[i], face[i + 1]) for face in faces for i in range(1, len(face) - 1)]
        files[f'scenes/{name}.mesh'] = mesh_bytes(positions, triangles)
    files['scenes/geometry.json'] = json.dumps({
        'voxelMm': VOXEL_MM,
        'lensRadiusMm': LENS_RADIUS_MM,
        'sectorDepthMm': SECTOR_DEPTH_MM,
        'sectorHalfAngleDeg': SECTOR_HALF_ANGLE_DEG,
        'pipPosition': PIP_POSITION,
        'pipScale': PIP_SCALE,
    }).encode()
    return files


def stage(output, vendor_dir=None):
    poses = read_poses(output / 'sweep.js')
    contacts = np.array([frame['contact'] for frame in poses])
    files = {}
    for name in ('liver', 'ribs', 'gallbladder'):
        with np.load(output / f'{name}.npz') as mesh:
            # Marching cubes and the GLB atlas use opposite windings.
            files[f'scenes/{name}.mesh'] = mesh_bytes(mesh['vertices'], mesh['faces'][:, ::-1])
    with np.load(output / 'torso.npz') as torso, np.load(output / 'ribs.npz') as ribs:
        vertices, faces = fitted_surface(torso['vertices'], ribs['vertices'], contacts)
    check_contacts(vertices, faces, contacts, np.array([frame['beam'] for frame in poses]))
    files['scenes/torso.mesh'] = mesh_bytes(vertices, faces)
    files.update(shared_geometry())
    files.update(read_vendor(vendor_dir))
    for relative, raw in files.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    write_manifest(output, sweep_files(('torso', 'liver', 'ribs', 'gallbladder')) +
                   ['media/acquired-long.webp', 'media/acquired-short.webp'])
    shutil.copyfile(HERE / 'scene.js', output / 'scene.js')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Existing study output containing the four NPZ meshes')
    parser.add_argument('--vendor-dir', type=Path, help='Reuse a locally staged, hash-checked Three.js vendor directory')
    args = parser.parse_args()
    stage(args.output, args.vendor_dir)


if __name__ == '__main__':
    main()
