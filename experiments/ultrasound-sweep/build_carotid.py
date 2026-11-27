"""Build matched transverse and longitudinal common carotid scans on s1127."""

import argparse
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial.transform import Rotation, Slerp
from skimage.measure import marching_cubes

from breast_anatomy import select_faces
from breast_compression import contact_rows, refine_contact_skin, sample_contact_plate
from carotid_surface import conform_neck
from carotid_vein import right_jugular
from build_abdomen import axes, contact_point, measure_landmark, mesh_from_mask, overlay, section_palette, section_palette_sha256
from build_breast import footprint_hits
from build_study import body_surface, fine_scatter, material_at, unit, volume
from build_thyroid import AFFINE, CASE, CT_SHA, OBSTRUCTION_PINS, PINS, SHAPE, neck_surface, read_thyroid_tracks, section_grid
from delivery import sha256, sweep_files, write_manifest
from display_neck import fitted_neck
from geometry import FRAME_COUNT, RASTER_SIZE, VOXEL_MM
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
STATIONS = {
    'carotid-right': ((390, .1, -.2), (394, .30, 0), (389, .65, -.12)),
    'carotid-left': ((398, -.4, -.2), (400, -.5, -.2), (398, -.4, -.22)),
}
KEYFRAMES = (12, 48)


def read_tracks():
    data = json.loads((HERE / 'carotid-tracks.json').read_text())
    structures = {part['id']: part for part in read_thyroid_tracks()[0]['parts']}
    tracks = []
    for item in data['sweeps']:
        side = item['id'].removeprefix('carotid-')
        target = f'common_carotid_artery_{side}'
        names = ['thyroid_gland', 'trachea', target]
        parts = [structures[name].copy() for name in names]
        if side == 'right':
            names.append('internal_jugular_vein_right')
            parts.append({'id': names[-1], 'label': 'Right internal jugular vein',
                          'color': '#6c9fc0', 'opacity': .72})
        tracks.append({**copy.deepcopy(data['common']), **item, 'organ': target,
                       'overlayParts': [name for name in names if name != 'trachea'], 'parts': parts})
    return tracks


def pose_recipe_sha256(slug):
    return sha256(json.dumps(STATIONS[slug]).encode())


def model_recipe_sha256():
    names = ('build_carotid.py', 'build_thyroid.py', 'build_breast.py', 'breast_compression.py',
             'display_body.py', 'display_neck.py', 'exterior-atlas.json', 'fit_abdomen.py', 'build_study.py',
             'build_abdomen.py', 'carotid_vein.py', 'carotid_surface.py')
    return sha256(json.dumps({name: sha256((HERE / name).read_bytes()) for name in names}, sort_keys=True).encode())


def load_inputs(case):
    ct = volume(case / 'ct.nii.gz', CT_SHA, '<i2', SHAPE, AFFINE)
    masks = {name: volume(case / f'segmentations/{name}.nii.gz', pin, 'u1', SHAPE, AFFINE)
             for name, pin in PINS.items()}
    masks['internal_jugular_vein_right'] = right_jugular(ct, masks['common_carotid_artery_right'])
    obstruction = np.zeros(SHAPE, dtype='u1')
    for name, pin in OBSTRUCTION_PINS.items():
        obstruction |= volume(case / f'segmentations/{name}.nii.gz', pin, 'u1', SHAPE, AFFINE)
    return ct, masks, obstruction


def centerline(mask):
    z = np.arange(378, 407)
    xy = []
    for height in z:
        labels, _ = nd.label(mask[:, :, height])
        sizes = np.bincount(labels.ravel())
        sizes[0] = 0
        if not sizes.max():
            raise ValueError(f'Missing carotid trunk at {height}')
        xy.append(np.column_stack(np.nonzero(labels == sizes.argmax())).mean(0))
    return np.column_stack((nd.gaussian_filter1d(np.asarray(xy), 2, axis=0), z))


def location(line, z):
    return np.array([np.interp(z, line[:, 2], values) for values in line.T])


def anterior_query_mesh(mesh):
    # Broad query bounds contain every candidate anterior probe ray. The
    # delivered full mesh is still measured independently at the final poses.
    vertices, faces = mesh
    lower = vertices[faces].min(axis=1)
    upper = vertices[faces].max(axis=1)
    keep = ((lower <= [211, 290, 435]) & (upper >= [55, 125, 348])).all(axis=1)
    return select_faces(vertices, faces, keep)


def raw_poses(track, line, shell, native, ct, artery, obstruction, exterior=None):
    settings = STATIONS[track['id']]
    locations = [location(line, z) for z, _, _ in settings]
    orientation = []
    for number, (z, yaw, rock) in enumerate(settings):
        outward = np.array([yaw, 1., 0.])
        tangent = unit(location(line, z + 4) - location(line, z - 4))
        if number < 2:
            outward -= tangent * (outward @ tangent)
            marker = np.array([1., 0., 0.])
        else:
            # Fit the long section to the actual centerline over the active aperture.
            points = line[(line[:, 2] >= z - 11) & (line[:, 2] <= z + 11)]
            _, _, basis = np.linalg.svd(points - points.mean(0))
            tangent = basis[0] * np.sign(basis[0, 2])
            outward -= tangent * (outward @ tangent)
            marker = tangent
        width, _, beam = axes(outward, marker).T
        normal = np.cross(width, beam)
        w, b = Rotation.from_rotvec(normal * rock).apply([width, beam])
        orientation.append(np.column_stack((w, np.cross(b, w), b)))
    rotations = Rotation.from_matrix(np.asarray(orientation))
    key = (0, *KEYFRAMES)
    path = Slerp(key, rotations)
    previous = None
    initial = None
    rays_lateral = np.linspace(-track['fieldWidthMm'] / 2, track['fieldWidthMm'] / 2, 17)
    depths = np.arange(0, track['sectorDepthMm'] + 7, .8)
    for i in range(FRAME_COUNT):
        target = np.array([np.interp(i, key, coordinate) for coordinate in np.asarray(locations).T])
        width, _, beam = path(i).as_matrix().T
        normal = np.cross(width, beam)
        candidates = []
        for rock in np.linspace(-.5, .5, 23):
            w, b = Rotation.from_rotvec(normal * rock).apply([width, beam])
            contact = contact_point(target, b, shell)
            frame = {'contact': contact.tolist(), 'width': w.tolist(), 'beam': b.tolist()}
            try:
                row_samples = np.linspace(-3, 3, 7)
                hit = footprint_hits(native, frame, rays_lateral, row_samples)
                display = hit if exterior is None else footprint_hits(exterior, frame, rays_lateral, row_samples)
            except ValueError:
                continue
            position = contact[:, None, None] + (w[:, None, None] * rays_lateral[None, :, None]
                       + b[:, None, None] * (depths[None, None, :] + hit[3][None, :, None])) / VOXEL_MM
            vessel = material_at(artery, position) >= .5
            opaque = ((material_at(obstruction, position) > .48) | (material_at(ct, position) < -530)) & (depths > 4)
            blocked = np.count_nonzero(vessel & np.maximum.accumulate(opaque, axis=1))
            total = max(np.count_nonzero(vessel), 1)
            travel = 0 if previous is None else np.linalg.norm(previous - contact) * VOXEL_MM
            depth_variation = max(np.ptp(hit), np.ptp(display))
            disagreement = abs(hit - display)
            cost = (190 * blocked / total + depth_variation + 3.3 * travel + 8 * abs(rock)
                    + 50 * max(0, depth_variation - 11)
                    + 32 * max(0, disagreement.max() - 3.3) + 8 * np.quantile(disagreement, .94))
            candidates.append((cost, frame, contact))
        if not candidates:
            raise ValueError(f'No viable {track["id"]} footprint at frame {i}')
        _, frame, previous = min(candidates, key=lambda row: row[0])
        w, b = (np.asarray(frame[key]) for key in ('width', 'beam'))
        orientation = Rotation.from_matrix(np.column_stack((w, np.cross(b, w), b)))
        if initial is None:
            initial = orientation
        frame['degrees'] = round(float(np.rad2deg((orientation * initial.inv()).magnitude())), 2)
        yield frame, target


def match_aperture(frame, native, exterior, width_mm):
    x = np.linspace(-width_mm / 2, width_mm / 2, 65)
    y = np.linspace(-3, 3, 21)
    source = footprint_hits(native, frame, x, y)
    display = footprint_hits(exterior, frame, x, y)
    # Use the packed display's native surface to seat its lens. Record the CT
    # residual before this shared deformation so the fit cannot hide a mismatch.
    advance = float(display.max())
    out = {**frame, 'contact': (np.asarray(frame['contact']) + np.asarray(frame['beam']) *
                               advance / VOXEL_MM).tolist(),
           'contactRig': {'lateralMm': x.tolist(), 'elevationMm': y.tolist(),
                          'faceWidthMm': width_mm, 'faceElevationMm': 6.,
                          'settleDepthMm': 32., 'featherMm': 10.,
                          'surfaceMm': (display - advance).round(5).tolist()}}
    return out, source - display


def resolved_vessel(mask):
    """Smooth the native segmentation at a subvoxel scale for mesh and image."""
    voxels = np.column_stack(np.nonzero(mask))
    lo = np.maximum(voxels.min(0) - 4, 0)
    hi = np.minimum(voxels.max(0) + 5, mask.shape)
    bounds = tuple(slice(a, b) for a, b in zip(lo, hi, strict=True))
    candidate = nd.gaussian_filter(mask[bounds].astype('f'), .68)
    field = np.zeros(mask.shape, dtype='f4')
    field[bounds] = candidate
    return field


def vessel_mesh(field):
    # Crop the display to the neck, exact same 0.5 level-set as the sampled masks.
    z0 = 371
    cropped = np.pad(field[:, :, z0:407], 1)
    vertices, faces, _, _ = marching_cubes(cropped, .5)
    return mesh_bytes(vertices + [-1, -1, z0 - 1], faces[:, ::-1])


def native_sample(frame, ct, masks, obstruction, x, y, field, organ):
    c, w, b = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
    xyz = c[:, None, None] + (w[:, None, None] * x + b[:, None, None] * y) / VOXEL_MM
    hu = nd.gaussian_filter(material_at(ct, xyz), (.68, .74))
    sampled = {name: nd.map_coordinates(mask, xyz, order=1, mode='constant',
                                          output=np.float32, prefilter=False)
               for name, mask in masks.items()}
    labels = {name: (values >= .5) & field for name, values in sampled.items()}
    air = np.clip((-hu - 325) / 430, 0, 1)
    opaque = ((material_at(obstruction, xyz) > .48) | (hu < -530)) & (y > 4)
    thyroid = nd.gaussian_filter(labels['thyroid_gland'].astype('f'), .8)
    artery = nd.gaussian_filter(sampled[organ], (.90, .78))
    bone = np.clip((hu - 245) / 380, 0, 1)
    pitch = y[1, 0] - y[0, 0]
    attenuation = np.exp(-nd.gaussian_filter(np.cumsum((bone + air) * (y > 0), axis=0), (1, 1.6)) * .46 * pitch)
    # Echo direction follows the native interfaces that face the beam. The
    # simulated bands do not encode arterial wall thickness or flow.
    fascia = np.clip(np.abs(np.gradient(hu, axis=0)) / pitch * 1.28, 0, 105)
    xx, yy, zz = xyz
    wave = .63 * yy + (.10 if frame['contact'][0] > 130 else -.10) * xx + .16 * zz
    wave += .30 * np.sin(zz * .26) + .27 * np.cos(xx * .38)
    strands = np.exp(-(np.sin(wave) / .24) ** 2)
    muscle = np.clip((hu + 4) / 70, 0, 1) * np.clip((85 - y) / 40, 0, 1)
    fascia += (22 * strands) * muscle
    walls = 86 * np.clip(abs(np.gradient(artery, axis=0)) / pitch, 0, 1.2)
    # Single directional reflection at the sampled artery interface; no
    # separate wall layers or tissue thickness are inferred.
    dy, dx = np.gradient(sampled[organ], pitch)
    incidence = abs(dy) / np.maximum(np.hypot(dx, dy), .025)
    walls += 72 * np.exp(-((sampled[organ] - .5) / .12)**2) * incidence**1.5
    tissue = 43 + np.clip((hu + 60) * .31, -27, 28) + 20 * thyroid
    scatter = 72 * fine_scatter(xyz) + 33 * fine_scatter(xyz + np.array([.39, .15, .61])[:, None, None])
    vein = np.zeros_like(artery)
    if 'internal_jugular_vein_right' in masks:
        vein = nd.gaussian_filter(sampled['internal_jugular_vein_right'], (.90, .83))
        walls += 45 * np.clip(abs(np.gradient(vein, axis=0)) / pitch, 0, 1)
    fluid = np.maximum(artery, vein)
    gray = ((tissue + fascia + scatter) * (1 - .92 * fluid) + walls + 8 * fluid) * attenuation
    return np.where(field, np.clip(gray, 1, 245), 0).astype('u1'), labels, opaque


def sample_frame(frame, track, ct, masks, obstruction, bounds=None):
    if bounds is None:
        x, y, field = section_grid(track)
        lateral, depth = x[0], y[:, 0]
    else:
        left, top, right, bottom = bounds
        width, height = RASTER_SIZE
        pitch = max((right - left) / width, (bottom - top) / height)
        lateral = (left + right) / 2 + (np.arange(width) + .5 - width / 2) * pitch
        depth = (top + bottom) / 2 + (np.arange(height) + .5 - height / 2) * pitch
        field = ((lateral[None, :] >= left) & (lateral[None, :] <= right)
                 & (depth[:, None] >= top) & (depth[:, None] <= bottom))
    pitch = depth[1] - depth[0]
    native_depth = (np.arange(int(np.floor(-16 / pitch)),
                              int(np.ceil((track['sectorDepthMm'] + 16) / pitch))) + .5) * pitch
    x_raw, y_raw = np.meshgrid(lateral, native_depth)
    field_raw = abs(x_raw) <= track['fieldWidthMm'] / 2
    gray, labels, opaque = native_sample(frame, ct, masks, obstruction, x_raw, y_raw, field_raw, track['organ'])
    rows = contact_rows(frame['contactRig'], lateral, depth)

    def warp(source, order=0):
        return sample_contact_plate(source, native_depth, rows, order=order, field=field)

    gray = warp(gray, 1)
    labels = {key: warp(mask) for key, mask in labels.items()}
    return gray, labels, warp(np.maximum.accumulate(opaque, axis=0)), pitch


def evidence(artery, gray, pitch):
    components, _ = nd.label(artery)
    sizes = np.bincount(components.ravel())
    sizes[0] = 0
    main = (components == sizes.argmax()) if sizes.max() else np.zeros_like(artery)
    y, x = np.nonzero(main)
    if len(x) < 100:
        raise ValueError('Native artery is missing or truncated')
    values = np.linalg.eigvalsh(np.cov([x, y]))
    contiguous, count = nd.label(main.sum(axis=0) * pitch >= 1.8)
    parts = np.bincount(contiguous)[1:]
    return {'nativeMajorComponentFraction': round(len(x) / artery.sum(), 4),
            'widthMm': round((np.ptp(x) + 1) * pitch, 2),
            'depthSpanMm': round((np.ptp(y) + 1) * pitch, 2),
            'longWallPairWidthMm': round(float(parts.max(initial=0) * pitch), 2),
            'elongation': round(float(np.sqrt(values[1] / max(values[0], 1e-4))), 2),
            **measure_landmark(main, gray)}


def build_one(track, out, frames_targets, native, exterior, receipt, ct, masks, obstruction):
    frames = []
    differences = []
    evidence_rows = {}
    maximum_cover = 0
    bounds_by_frame = {}
    detail_names = []
    target = track['organ']
    media, scenes = out / 'media', out / 'scenes'
    media.mkdir()
    scenes.mkdir()
    (scenes / 'torso.mesh').write_bytes(mesh_bytes(*exterior))
    for key, mask in masks.items():
        raw = vessel_mesh(mask) if 'carotid' in key or 'jugular' in key else mesh_from_mask(mask, (369, 407))
        (scenes / f'{key}.mesh').write_bytes(raw)
    for n, (base, location_voxel) in enumerate(frames_targets):
        frame, match = match_aperture(base, native, exterior, track['fieldWidthMm'])
        frames.append(frame)
        differences.extend(match.ravel())
        indentation = -np.min(frame['contactRig']['surfaceMm'])
        if indentation > 18 or np.max(abs(match)) > 7:
            raise ValueError(f'{track["id"]} frame {n}: peak indentation {indentation:.2f} mm; '
                             f'CT–atlas aperture discrepancy {np.max(abs(match)):.2f} mm')
        gray, labels, opacity, pitch = sample_frame(frame, track, ct, masks, obstruction)
        artery = labels[target]
        details = evidence(artery, gray, pitch)
        cover = float(np.count_nonzero(artery & opacity) / np.count_nonzero(artery))
        maximum_cover = max(maximum_cover, cover)
        if cover > (.14 if n == 12 else .29):
            raise ValueError(f'{track["id"]} frame {n} has {cover:.0%} target behind bone or air')
        if n in KEYFRAMES:
            if n == 12 and not 1 <= details['elongation'] <= 1.55:
                raise ValueError(f'{track["id"]} transverse not near circular: {details}')
            if n == 48 and details['longWallPairWidthMm'] < 22:
                raise ValueError(f'{track["id"]} long axis too short: {details}')
            beam_depth = ((location_voxel - np.asarray(frame['contact'])) @ np.asarray(frame['beam'])) * VOXEL_MM
            evidence_rows[str(n)] = {**details, 'beamTargetCaseVox': location_voxel.round(5).tolist(),
                                     'beamTargetDepthMm': round(float(beam_depth), 3),
                                     'targetBehindBoneOrAirFraction': round(cover, 4),
                                     'anatomy': {key: measure_landmark(mask, gray) for key, mask in labels.items()}}
        if n in track.get('detailFrames', ()):
            right = 'internal_jugular_vein_right' in labels
            width = 28 if n == 12 else (24 if right else 26)
            x_center = 0.
            if n == 48 and right:
                # Retain the visible paired walls and keep marginal clavicular
                # shadow toward the periphery of the magnified view.
                x_cols = (np.arange(RASTER_SIZE[0]) + .5 - RASTER_SIZE[0] / 2) * pitch
                clearance = track['fieldWidthMm'] / 2 - width / 2
                x_center = min(np.linspace(-clearance, clearance, 9),
                               key=lambda center: np.count_nonzero(
                                   artery & opacity & (abs(x_cols - center) <= width / 2)))
            vertical_target = artery
            if n == 12 and right:
                vertical_target = artery | labels['internal_jugular_vein_right']
            rows = np.nonzero(vertical_target)[0]
            y_center = ((rows.min() + rows.max()) / 2 + .5 - 7) * pitch
            half_depth = max(width / RASTER_SIZE[0] * RASTER_SIZE[1] / 2,
                             (np.ptp(rows) + 1) * pitch / 2 + 1.8)
            bounds = [x_center - width / 2, float(y_center) - half_depth, x_center + width / 2, float(y_center) + half_depth]
            bounds = [round(value, 6) for value in bounds]
            if not 0 < bounds[1] < bounds[3] <= track['sectorDepthMm']:
                raise ValueError('Magnified carotid window falls outside full field')
            bounds_by_frame[str(n)] = bounds
            detail_gray, detail_labels, detail_opaque, detail_pitch = sample_frame(frame, track, ct, masks, obstruction, bounds)
            detail_target = detail_labels[target]
            detail_covered = np.count_nonzero(detail_target & detail_opaque) / np.count_nonzero(detail_target)
            evidence_rows[str(n)]['detail'] = {
                **evidence(detail_target, detail_gray, detail_pitch),
                'opaquePixelsAtTargetFraction': round(detail_covered, 4),
            }
            for kind, plate, quality in (('scan', detail_gray, 91),
                                         ('section', overlay(detail_gray, detail_labels, section_palette(track)), 88)):
                name = f'detail-{kind}-{n:02}.webp'
                Image.fromarray(plate).save(media / name, quality=quality)
                detail_names.append(f'media/{name}')
        Image.fromarray(gray).save(media / f'scan-{n:02}.webp', quality=91)
        Image.fromarray(overlay(gray, labels, section_palette(track))).save(media / f'section-{n:02}.webp', quality=88)
    (out / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    signed = np.array([frame['contactRig']['surfaceMm'] for frame in frames])
    (out / 'verification.json').write_text(json.dumps({
        **receipt, **{key: track[key] for key in ('exterior', 'probeType', 'fieldShape', 'voxelMm',
                                                  'fieldWidthMm', 'sectorDepthMm')},
        'case': CASE, 'ctSha256': CT_SHA, 'maskSha256': PINS, 'obstructionMaskSha256': OBSTRUCTION_PINS,
        'modelRecipeSha256': model_recipe_sha256(), 'poseRecipeSha256': pose_recipe_sha256(track['id']),
        'sectionPaletteSha256': section_palette_sha256(track), 'rasMmFromVoxel': AFFINE.tolist(),
        'unseatedCtVsAtlasMaxFootprintMm': round(float(np.max(np.abs(differences))), 3),
        'unseatedCtVsAtlasP95FootprintMm': round(float(np.quantile(np.abs(differences), .95)), 3),
        **({'jugularSource': 'Right internal jugular traced in the s1127 contrast CT, separate from source labels.'}
           if 'internal_jugular_vein_right' in masks else {}),
        'peakSeatingIndentationMm': round(float(-signed.min()), 3),
        'maximumTargetBehindBoneOrAirFraction': round(maximum_cover, 4),
        'vesselLevelSet': 'Native mask convolved at 0.68 source voxels sigma; the display and section use the same 0.5 isovalue.',
        'rasterPitchMm': pitch, 'frames': evidence_rows, 'detailBoundsMm': bounds_by_frame,
    }, indent=2) + '\n')
    write_manifest(out, sweep_files(['torso', *masks]) + detail_names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('sweeps_dir', type=Path)
    args = parser.parse_args()
    tracks = read_tracks()
    for track in tracks:
        if (args.sweeps_dir / track['id']).exists():
            parser.error(f'Choose a fresh destination for {track["id"]}.')
    ct, masks, obstruction = load_inputs(args.case)
    shell, _, _ = body_surface(ct)
    native = neck_surface(shell)
    native_query = anterior_query_mesh(native)
    paths = {track['id']: list(raw_poses(track, centerline(masks[track['organ']]), shell, native_query,
                                          ct, masks[track['organ']], obstruction)) for track in tracks}
    anchors = [frame for path in paths.values() for frame, _ in path]
    contacts, beams = (np.asarray([frame[key] for frame in anchors]) for key in ('contact', 'beam'))
    # Registration uses unseated native beam contacts. The screen samples then
    # invert the exact displacement shared with the 3D lens.
    vertices, faces, receipt = fitted_neck(args.case, shell, contacts, beams, shape=SHAPE, affine=AFFINE,
                                          conformer=conform_neck)
    center = contacts.mean(0)
    exterior = refine_contact_skin(vertices, faces, center, radius=41)
    # Keep triangle interpolation tight at the high right rim, where the
    # conformer crosses the steepest change in native neck contour.
    exterior = refine_contact_skin(*exterior, np.array([159, 157, 404]), radius=12)
    display_query = anterior_query_mesh(exterior)
    paths = {track['id']: list(raw_poses(track, centerline(masks[track['organ']]), shell, native_query,
                                          ct, masks[track['organ']], obstruction, display_query)) for track in tracks}
    masks = {name: resolved_vessel(mask) if 'carotid' in name or 'jugular' in name else mask
             for name, mask in masks.items()}
    args.sweeps_dir.mkdir(parents=True, exist_ok=True)
    for track in tracks:
        with TemporaryDirectory(dir=args.sweeps_dir) as temporary:
            out = Path(temporary) / track['id']
            out.mkdir()
            build_one(track, out, paths[track['id']], native, exterior, receipt, ct,
                      {part['id']: masks[part['id']] for part in track['parts']}, obstruction)
            out.rename(args.sweeps_dir / track['id'])


if __name__ == '__main__':
    main()
