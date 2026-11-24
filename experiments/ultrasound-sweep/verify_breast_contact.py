"""Raycast the packed, posed skin against the physical probe face."""

import argparse
import json
from pathlib import Path
from struct import unpack_from

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from build_axilla import read_axilla_tracks
from breast_anatomy import concatenate
from breast_compression import smoothstep
from build_breast import footprint_hits, read_breast_tracks
from delivery import read_poses, validate_mesh
from geometry import VOXEL_MM


# A tolerance above the packed replay's measured residuals, and below
# the millimeter-scale rim penetrations that coarse triangles introduced.
MAX_RESIDUAL_MM = {'breast': .4, 'axilla': .2, 'breast-subareolar': .65}


def load_packed_mesh(path):
    raw = path.read_bytes()
    validate_mesh(raw, path)
    points, triangles = unpack_from('<2I', raw)
    vertices = np.frombuffer(raw, '<f4', count=3 * points, offset=8)
    faces = np.frombuffer(raw, '<u4', count=3 * triangles, offset=8 + 12 * points)
    return vertices.reshape(-1, 3), faces.reshape(-1, 3)


def deform_skin(mesh, frame, pressure):
    """Reproduce scene.js displacement at the delivered triangle vertices."""
    vertices, faces = mesh
    rig = frame['contactRig']
    contact, width, beam = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
    axes = np.stack((width, np.cross(beam, width), beam))
    local = np.einsum('ij,kj->ik', vertices - contact, axes) * VOXEL_MM
    lateral, elevation, depth = local.T
    half_width, half_elevation = rig['faceWidthMm'] / 2, rig['faceElevationMm'] / 2
    feather = rig['featherMm']
    lateral_weight = 1 - smoothstep((abs(lateral) - half_width) / feather)
    elevation_weight = 1 - smoothstep((abs(elevation) - half_elevation) / feather)
    active = (lateral_weight > 0) & (elevation_weight > 0)
    sample = RegularGridInterpolator(
        (rig['elevationMm'], rig['lateralMm']), np.asarray(rig['surfaceMm'], dtype=np.float32),
    )
    surface = sample(np.column_stack((
        np.clip(elevation[active], -half_elevation, half_elevation),
        np.clip(lateral[active], -half_width, half_width),
    )))
    weight = lateral_weight[active] * elevation_weight[active]
    settle = 1 - smoothstep((depth[active] - surface) / rig['settleDepthMm'])
    displacement = np.maximum(pressure - surface, 0) * weight * settle
    deformed = vertices.astype(float)
    deformed[active] += displacement[:, None] * beam / VOXEL_MM
    return deformed, faces


def verify_route(root, tour, limit):
    route = root / tour['assetRoot']
    frames = read_poses(route / 'sweep.js')
    exterior = ['torso', *tour.get('surfaceParts', ())]
    paths = tour.get('meshPaths', {})
    mesh_paths = [root / paths[name] if name in paths else route / 'scenes' / f'{name}.mesh'
                  for name in exterior]
    mesh = concatenate([load_packed_mesh(path) for path in mesh_paths])
    pressures = [0]
    if tour.get('compressionMm'):
        pressures.append(tour['compressionMm'])
    failures = []
    for pressure in pressures:
        frame_hits = []
        for index, frame in enumerate(frames):
            rig = frame['contactRig']
            # Include the rim and center. Probe depth is measured against
            # the advanced face, after deforming the displayed triangles.
            lateral = np.linspace(-rig['faceWidthMm'] / 2, rig['faceWidthMm'] / 2, 33)
            elevation = np.linspace(-rig['faceElevationMm'] / 2, rig['faceElevationMm'] / 2, 13)
            try:
                surface = footprint_hits(deform_skin(mesh, frame, pressure), frame, lateral, elevation)
            except ValueError as exc:
                raise ValueError(f'{tour["id"]} frame {index} +{pressure:g} mm: {exc}') from exc
            frame_hits.append(surface - pressure)
        hits = np.asarray(frame_hits)
        if not np.isfinite(hits).all():
            failures.append(f'{tour["id"]} +{pressure:g} mm has missing aperture hits')
            continue
        residual = abs(hits)
        frame, j, i = np.unravel_index(np.argmax(residual), residual.shape)
        maximum = residual[frame, j, i]
        print(f'{tour["id"]} +{pressure:g} mm: max {maximum:.3f} mm '
              f'(frame {frame}, lateral {lateral[i]:+.2f}, elevation {elevation[j]:+.2f}, '
              f'signed {hits[frame, j, i]:+.3f} mm), '
              f'p95 {np.quantile(residual, .95):.3f} mm, limit {limit:g} mm')
        if maximum > limit:
            failures.append(f'{tour["id"]} +{pressure:g} mm exceeds its {limit:g} mm limit')
    return failures


def load_routes(root):
    catalogue = root / 'abdomen-tours.js'
    if catalogue.exists():
        raw = catalogue.read_text().strip()
        tours = json.loads(raw.removeprefix('const abdomenTours = ').removesuffix(';'))
        if set(MAX_RESIDUAL_MM) <= {tour['id'] for tour in tours}:
            return tours
    tracks = [*read_breast_tracks(), *read_axilla_tracks()]
    return [{**track, 'assetRoot': f'sweeps/{track["id"]}/'} for track in tracks]


def verify(root):
    routes = {tour['id']: tour for tour in load_routes(root)}
    failures = []
    for name, limit in MAX_RESIDUAL_MM.items():
        failures.extend(verify_route(root, routes[name], limit))
    if failures:
        raise ValueError('\n'.join(failures))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tour_root', type=Path, help='Staged or assembled tour root containing sweeps/')
    verify(parser.parse_args().tour_root)
