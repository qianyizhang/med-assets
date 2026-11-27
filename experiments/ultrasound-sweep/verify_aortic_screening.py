"""Check the staged transverse sweep against pinned native case inputs."""

import argparse
import json
from pathlib import Path
import struct

import numpy as np

import build_aortic_screening as aortic
from build_abdomen import ImagingGrid, measure_landmark, section_palette_sha256
from build_study import material_at, volume
from delivery import read_poses, sweep_files, validate_mesh, verify_inventory
from display_body import expected_source_digests
from fit_abdomen import CONTACT_TOLERANCE_MM, max_outer_error
from geometry import RASTER_SIZE, VOXEL_MM


def verify(case, root):
    track, = aortic.read_tracks()
    names = ['torso', *(part['id'] for part in track['parts'])]
    if not (root / 'delivery.json').is_file():
        raise ValueError('Missing aortic screening inventory')
    verify_inventory(root, sweep_files(names))
    for name in names:
        path = root / 'scenes' / f'{name}.mesh'
        validate_mesh(path.read_bytes(), path)
    receipt = json.loads((root / 'verification.json').read_text())
    if (receipt['exterior'] != track['exterior']
            or any(receipt.get(key) != value for key, value in expected_source_digests().items())
            or receipt['registrationMaskSha256'] != {name: aortic.abdomen.PINS[name] for name in aortic.abdomen.FIT_RIBS}
            or receipt['modelRecipeSha256'] != aortic.model_recipe_sha256()
            or receipt['poseRecipeSha256'] != aortic.pose_recipe_sha256(track['id'])
            or receipt['sectionPaletteSha256'] != section_palette_sha256(track)
            or receipt['maskSha256'] != aortic.PINS or receipt['ctSha256'] != aortic.CT_SHA):
        raise ValueError('Rebuild the stale aortic screening stage')

    frames = read_poses(root / 'sweep.js')
    grid = ImagingGrid(track['sectorDepthMm'])
    pitch = grid.x[0, 1] - grid.x[0, 0]
    assert np.isclose(receipt['rasterPitchMm'], pitch)
    mask = volume(case / 'segmentations/aorta.nii.gz', aortic.PINS['aorta'], 'u1')
    record = []
    for number, frame in enumerate(frames):
        span = frame['apSpan']
        endpoints = np.asarray(span['endpointsPx'])
        assert endpoints.shape == (2, 2) and np.isfinite(endpoints).all()
        assert ((endpoints >= 0) & (endpoints < np.asarray(RASTER_SIZE))).all(), number
        assert abs(np.linalg.norm(endpoints[0] - endpoints[1]) * pitch - span['millimetres']) < .002, number
        position = grid.coordinates(frame, grid.x[0, 0] + endpoints[:, 0] * pitch,
                                   grid.y[0, 0] + endpoints[:, 1] * pitch)[:, 0, :]
        endpoints_values = material_at(mask, position)
        assert np.max(abs(endpoints_values - .5)) < .005, number
        chord = position[:, :1] + np.linspace(0, 1, 81)[None, :] * (position[:, 1:] - position[:, :1])
        assert np.min(material_at(mask, chord)[1:-1]) > .49, number
        normal = np.cross(frame['width'], frame['beam'])
        ap = aortic.AP - normal * (aortic.AP @ normal)
        assert np.linalg.norm(np.cross((position[:, 0] - position[:, 1]), ap)) < .003, number
        if key := receipt['frames'].get(str(number)):
            assert key['apSpan'] == span
            assert np.allclose(aortic.ras_mm(position.T), key['apSpanEndpointsRasMm'], atol=.002)
            xyz = grid.coordinates(frame, grid.x, grid.y)
            labels = (material_at(mask, xyz) >= .5) & grid.field
            observed = measure_landmark(labels, np.zeros_like(labels, dtype='u1'))
            for field in ('largestSectionPixels', 'imageBounds'):
                assert observed[field] == key['aorta'][field]
            record.append((number, span['millimetres'], key['targetDepthMm']))

    mesh = (root / 'scenes/torso.mesh').read_bytes()
    vertices_n, triangles_n = struct.unpack_from('<2I', mesh)
    vertices = np.frombuffer(mesh, '<f4', count=3 * vertices_n, offset=8).reshape(-1, 3)
    triangles = np.frombuffer(mesh, '<u4', count=3 * triangles_n, offset=8 + 12 * vertices_n).reshape(-1, 3)
    contacts = np.asarray([frame['contact'] for frame in frames])
    assert np.max(np.linalg.norm(np.diff(contacts, axis=0), axis=1)) * VOXEL_MM < 17
    error = max_outer_error(vertices, triangles, contacts, np.array([frame['beam'] for frame in frames]))
    assert error <= CONTACT_TOLERANCE_MM
    assert np.isclose(error, receipt['surfaceMaxOuterContactErrorMm'], atol=.001)
    assert [number for number, _, _ in record] == [stop['frame'] for stop in track['stops']]
    print(f'49 registered transverse sections, packed torso contact ≤{error:.3f} mm.')
    for frame, span, depth in record:
        print(f'Frame {frame}: {span:.2f} mm AP mask chord at {depth:.1f} mm target depth.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('sweep', type=Path)
    args = parser.parse_args()
    verify(args.case, args.sweep)


if __name__ == '__main__':
    main()
