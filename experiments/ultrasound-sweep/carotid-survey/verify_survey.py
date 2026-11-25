"""Verify asset hashes, anatomical stack evidence and scan-only reconstruction."""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

from build_survey import (
    as_kernel, closed_tube, file_identity, footprint_hits, gate_is_supported, load_line, load_mesh,
    local_axes, mask_at, mesh_bytes, scan_pose, section_observation, VOXEL_MM,
)
from reconstruction import raster_grid, read_mask, reconstruct, world_to_pixel
from survey_delivery import acquisition_recipe_sha256
from branch_geometry import separate_daughters


def validate_view(root, view, skin=None):
    axes = np.array([view['width'], view['beam']])
    contact = np.asarray(view['contact'])
    assert np.isfinite(contact).all() and np.allclose(axes @ axes.T, np.eye(2), atol=1e-5)
    assert 0 < view['mmPerPx'] < 1
    assert np.isclose(view['widthPx'] * view['mmPerPx'], view['faceWidthMm'])
    assert 38 <= view['faceWidthMm'] <= 45
    for key in ('path', 'lumenMaskPath'):
        with Image.open(root / view[key]) as image:
            assert image.size == (view['widthPx'], view['heightPx'])
    if skin is not None:
        frame = {'contact': contact / VOXEL_MM, 'width': axes[0], 'beam': axes[1]}
        hit = footprint_hits(skin, frame, np.array([0.]), np.array([0.]))[0, 0]
        assert abs(hit) < .02


def verify_branch_continuity(side, fields, axes, intervals, named, bifurcation, distal):
    """Against independent source branch cuts, check the saved ICA interval."""
    x, y, z = axes
    width, beam = local_axes(None, False)
    i, j = np.indices((len(x), len(y)))
    reports = {'ica': [], 'eca': []}
    for height in intervals:
        if height < bifurcation + 6:
            continue
        k = np.full(i.shape, (height-z[0])/(z[1]-z[0]))
        recovered = nd.map_coordinates(fields, [i, j, k], order=1) > 0
        for key, mesh in named.items():
            ref = mask_at(mesh, [0, 0, height], width, beam, x, -y[::-1])[::-1].T
            if ref.sum() < 4:
                continue
            overlap = int((ref & recovered).sum()) / int(ref.sum())
            reports[key].append((height, overlap))
    assert intervals[-1] >= distal[2] - 1
    for key, observed in reports.items():
        relevant = [value for z, value in observed if key != 'eca' or z < bifurcation + 24]
        assert relevant and min(relevant) > 0, (side, key, min(observed, key=lambda row: row[1]))
        print(f"  {key.upper()} matched in all {len(relevant)} held-out {'proximal ' if key == 'eca' else ''}checks; "
              f"minimum source mask overlap {min(relevant):.0%}.")


def verify(source, root):
    manifest = json.loads((root / 'delivery.json').read_text())
    assert set(manifest) == {str(p.relative_to(root)) for p in root.rglob('*')
                             if p.is_file() and p.name != 'delivery.json'}
    for name, hash_ in manifest.items():
        file_identity(root / name, hash_)
    protocol = json.loads((root / 'protocol-geometry.json').read_text())
    assert protocol['acquisitionRecipeSha256'] == acquisition_recipe_sha256(Path(__file__).parent)
    atlas = json.loads(source.read_text())
    skin = as_kernel(load_mesh(source.parent / atlas['skin']))
    paths = {}
    sources_by_side = {}
    for side, frames in protocol['tracking'].items():
        arrays = {name: source.parent / item for name, item in atlas['sides'][side]['arteries'].items()}
        paths[side] = {name: load_line(path, name, side) for name, path in arrays.items()}
        original = {name: closed_tube(load_mesh(path)) for name, path in arrays.items()}
        corrected = {**original}
        raw_paths = paths[side].copy()
        correction = separate_daughters(corrected, paths[side])
        assert protocol['authoredBranchSeparation'][side] == correction
        for name in ('ica', 'eca'):
            delta = corrected[name][0] - original[name][0]
            assert np.max(np.linalg.norm(delta, axis=1)) <= correction['maximumCenterShiftMm'] + .01
            assert np.allclose(delta[:, 2], 0)
            assert np.allclose(paths[side][name][[0, -1]], raw_paths[name][[0, -1]], atol=.00005)
        sources_by_side[side] = {name: as_kernel(mesh) for name, mesh in corrected.items()}
        ccas = paths[side]['cca']
        for branch in ('ica', 'eca'):
            assert np.linalg.norm(ccas[-1] - paths[side][branch][0]) < .15
        assert all(read_mask(root, frame).any() for frame in frames)
        for frame in frames:
            validate_view(root, frame, skin)
        recon, field, axes = reconstruct(frames, root)
        output = protocol['reconstructions'][side]
        assert mesh_bytes(*recon) == (root / output['reconstructionPath']).read_bytes()
        metrics = output['metrics']
        assert metrics['reconstructedComponentCount'] == 1
        assert metrics['icaUnobservedFramesAboveBifurcation'] == 0
        heights = np.array([frame['contact'][2] for frame in frames])
        distal = next(station['gate']['center'] for station in protocol['stations']
                      if station['id'] == f'{side}-ica-dist')
        verify_branch_continuity(side, field, axes, (heights[:-1] + heights[1:]) / 2,
                                 {name: sources_by_side[side][name] for name in ('ica', 'eca')},
                                 ccas[-1, 2], distal)
        assert metrics['maxProbeStepMm'] <= 18
        assert metrics['medianIoU'] >= .88
        assert metrics['sourceMaskRecallWithinAcquiredSlab'] >= .87
        assert metrics['largestReconstructedComponentFraction'] >= .80
        sizes = np.bincount(nd.label(field >= 0)[0].ravel())[1:]
        assert round(float(sizes.max() / sizes.sum()), 3) == metrics['largestReconstructedComponentFraction']
        assert min(view['contact'][2] for view in frames) < ccas[-1, 2] - 30
        assert max(view['contact'][2] for view in frames) > ccas[-1, 2] + 25
        assert any(len(frame['contours']) >= 2 and frame['contact'][2] > ccas[-1, 2]
                   for frame in frames)
        print(f"{side}: {len(frames)} source-registered observed sections, "
              f"median IoU {metrics['medianIoU']:.3f}, source recall {metrics['sourceMaskRecallWithinAcquiredSlab']:.3f}, "
              f"largest reconstructed component {metrics['largestReconstructedComponentFraction']:.3f}.")

    successful = 0
    steered = 0
    for station in protocol['stations']:
        if not station.get('available'):
            continue
        successful += 1
        for view in station['views'].values():
            validate_view(root, view, skin)
        view = station['views']['longitudinal']
        gate = station['gate']
        coordinates = world_to_pixel(view, np.array(gate['wallPoints']))
        center = world_to_pixel(view, np.array(gate['center']))
        assert np.allclose(center, gate['centerPx'], atol=.001)
        assert np.linalg.norm(np.diff(coordinates, axis=0)) * view['mmPerPx'] > 0
        assert abs(np.linalg.norm(np.diff(coordinates, axis=0)) * view['mmPerPx'] - gate['diameterMm']) < .02
        mask = read_mask(root, view)
        p = center.round().astype(int)
        assert mask[p[1], p[0]]
        doppler = read_mask(root, {'lumenMaskPath': view['dopplerMaskPath']})
        assert doppler[p[1], p[0]] and not (doppler & ~mask).any()
        seg = station['segment']
        if seg.startswith('ica-') or seg == 'eca':
            other = 'eca' if seg.startswith('ica-') else 'ica'
            rival = sources_by_side[station['side']][other]
            x, y = raster_grid(view)
            other_mask = mask_at(rival, view['contact'], view['width'], view['beam'], x, y)
            assert not other_mask[p[1], p[0]], station['id']
        if seg != 'bulb':
            assert gate['steeringSupported'], station['id']
        if seg == 'bulb':
            validate_view(root, station['measurementView'], skin)
            evidence = station['forkEvidence']
            assert 9 <= evidence['transverseLevelMm'] - evidence['forkMm'][2] <= 18
            def witness(mode, artery):
                return read_mask(root, {'lumenMaskPath': evidence['arterialMaskPaths'][mode][artery]})
            transverse_ica = witness('transverse', 'ica')
            transverse_eca = witness('transverse', 'eca')
            assert min(transverse_ica.sum(), transverse_eca.sum()) >= 45
            assert not (transverse_ica & transverse_eca).any()
            assert evidence['longitudinalSplitColumns'] >= 3
            long_arteries = [witness('longitudinal', artery) for artery in ('cca', 'ica', 'eca')]
            components, _ = nd.label(np.logical_or.reduce(long_arteries))
            label = np.bincount(components[long_arteries[0]])[1:].argmax() + 1
            component = components == label
            assert all(np.count_nonzero(part & component) > 36 for part in long_arteries)
            owned_ica = long_arteries[1] & ~long_arteries[2] & component
            owned_eca = long_arteries[2] & ~long_arteries[1] & component
            separation = sum(nd.label(component[:, col])[1] >= 2 for col in np.flatnonzero(
                owned_ica.any(0) & owned_eca.any(0)))
            assert separation == evidence['longitudinalSplitColumns']
            print(f"  {station['side']} fork: nonoverlapping ICA/ECA transverse masks and "
                  f'{separation} long-axis detector columns with both open daughters.')
        direction = np.array(gate['flowDirection'])
        beam = np.array(gate['beamDirection'])
        assert np.isclose(np.linalg.norm(direction), 1)
        assert np.isclose(np.linalg.norm(beam), 1)
        assert np.isclose(abs(direction @ beam), .5)
        origin = np.asarray(gate['steeredOriginMm'])
        origin_px = world_to_pixel(view, origin)
        assert np.allclose(origin_px, gate['steeredOriginPx'], atol=.002)
        assert abs(origin_px[1] - view['centerPx'][1]) < .002
        assert np.linalg.norm(np.cross(beam, np.asarray(gate['center']) - origin)) < .001
        if gate['steeringSupported']:
            assert 1 < origin_px[0] < view['widthPx'] - 2
            assert abs(gate['steeredSkinClearanceMm']) <= 4
            steered += 1
        if color := station.get('colorGate'):
            assert seg == 'bulb' and not gate['steeringSupported']
            side = station['side']
            anchor = np.array(color['center'])
            direction = np.array(color['flowDirection'])
            beam = np.array(color['beamDirection'])
            angle = np.rad2deg(np.arccos(abs(direction @ beam)))
            assert np.isclose(angle, color['beamFlowAngleDeg'])
            assert np.isclose(np.linalg.norm(beam), 1)
            assert np.allclose(world_to_pixel(view, np.asarray(color['steeredOriginMm'])),
                               color['steeredOriginPx'], atol=.002)
            assert np.linalg.norm(np.cross(beam, anchor - np.asarray(color['steeredOriginMm']))) < .001
            keep = ('mandible', 'c3', 'c4', 'c5', 'c6', 'c7')
            contexts = {'skin': skin} | {
                name.removeprefix(side + '-'): as_kernel(load_mesh(source.parent / path))
                for name, path in atlas['context'].items() if name.startswith(side + '-') or name in keep
            }
            observation = section_observation(view, sources_by_side[side], contexts)
            skin_contact = scan_pose(skin, anchor, np.array(view['width']), beam)
            assert np.allclose(skin_contact, color['steeredSkinContactMm'], atol=.001)
            route = beam, skin_contact, np.asarray(color['steeredOriginMm']), color['steeredSkinClearanceMm']
            assert gate_is_supported(view, anchor, route, observation)
            print(f'  {side} bulb color-only beam {angle:.0f}° to flow; physically clear path.')
    print(f'{successful} paired arterial stations passed the physical gate and pose checks; {steered} supported steered paths.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_manifest', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    verify(args.source_manifest, args.output)
