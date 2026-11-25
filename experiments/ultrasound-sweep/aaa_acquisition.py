"""Build registered modeled AAA acquisitions using the pinned s1233 context and packed probe scene."""

import argparse
from copy import copy
import json
from pathlib import Path
import struct
import subprocess
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image
from scipy import ndimage as nd

from build_abdomen import ImagingGrid, overlay
from build_aortic_screening import load_masks, read_tracks
from build_study import CT_SHA, material_at, unit, volume
from delivery import sha256, validate_mesh
from fit_abdomen import outer_contact_offsets
from geometry import LENS_RADIUS_MM, SECTOR_HALF_ANGLE_DEG, VOXEL_MM
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
RECIPE_FILES = (
    'aaa_acquisition.py', 'aaa_model.mjs', 'aortic-screening-track.json', 'build_abdomen.py',
    'build_aortic_screening.py', 'build_study.py', 'fit_abdomen.py', 'geometry.py', 'prepare_scenes.py',
    'cases/vascular/cases.json', 'cases/vascular/playable.js', 'cases/vascular/playable-model.js',
    'cases/vascular/playable-aorta.js',
)
PARTS = [
    {'id': 'wall', 'label': 'Aorta and proximal iliacs', 'color': '#c96351', 'opacity': .68},
    {'id': 'lumen', 'label': 'Arterial lumen', 'color': '#dd916d', 'opacity': .82},
    {'id': 'vein', 'label': 'Inferior vena cava', 'color': '#789dc4', 'opacity': .63},
    {'id': 'vertebrae', 'label': 'Thoracolumbar vertebrae', 'color': '#c5b58d', 'opacity': .42},
]
MURAL = {'id': 'mural', 'label': 'Mural thrombus', 'color': '#dbae65', 'opacity': .78}


def native_tour(study):
    catalogue_path = study / 'abdomen-tours.js'
    if catalogue_path.is_file():
        catalogue = catalogue_path.read_text().strip()
        if not catalogue.startswith('const abdomenTours = ') or not catalogue.endswith(';'):
            raise ValueError(f'Invalid tour catalogue at {study}')
        tours = json.loads(catalogue.removeprefix('const abdomenTours = ').removesuffix(';'))
        normal = next((tour for tour in tours if tour['id'] == 'aortic-screening'), None)
        if normal is not None:
            return normal
    track, = read_tracks()
    return track | {'assetRoot': 'sweeps/aortic-screening/'}


def input_mesh(study, tour, name):
    path = tour.get('meshPaths', {}).get(name, f"{tour['assetRoot']}scenes/{name}.mesh")
    disk = study / path
    raw = disk.read_bytes()
    validate_mesh(raw, disk)
    n_vertices, n_faces = struct.unpack_from('<II', raw)
    vertices = np.frombuffer(raw, '<f4', 3 * n_vertices, 8).reshape(-1, 3).astype('d')
    faces = np.frombuffer(raw, '<u4', 3 * n_faces, 8 + 12 * n_vertices).reshape(-1, 3)
    return Path(path).as_posix(), vertices, faces


class Registration:
    """Fit the authored trunk axis to the native artery while preserving cross-sectional millimetres."""

    def __init__(self, vertices, bifurcation_mm):
        distal, proximal = np.min(vertices[:, 2]), np.max(vertices[:, 2])
        heights = np.linspace(distal + 4, proximal - 4, 21)
        centers = np.array([vertices[np.abs(vertices[:, 2] - z) < 2, :2].mean(axis=0) for z in heights])
        slope, intercept = np.polyfit(heights, centers, 1)
        axial = proximal - 1
        center = np.r_[slope * axial + intercept, axial]
        caudal = unit(np.r_[-slope, -1])
        anterior_to_posterior = np.array([0., -1., 0.])
        posterior = unit(anterior_to_posterior - (anterior_to_posterior @ caudal) * caudal)
        left = -unit(np.cross(posterior, caudal))
        axial_scale = (axial - distal) * VOXEL_MM / (-caudal[2] * bifurcation_mm)
        self.matrix = np.column_stack((left, posterior, caudal * axial_scale)) / VOXEL_MM
        self.origin = center - self.matrix @ [0., 47., 0.]
        self.inverse = np.linalg.inv(self.matrix)

    def points(self, values):
        return np.einsum('...j,ij->...i', values, self.matrix) + self.origin

    def coordinates(self, grid):
        return np.einsum('ij,jkl->ikl', self.inverse, grid - self.origin[:, None, None])


def clear_spine(registration, model_wall, vertebrae, model):
    """Use the least anterior placement that clears the native vertebral mask."""
    vertices = np.asarray(model_wall['vertices'])
    faces = np.asarray(model_wall['faces']).reshape(-1, 3)
    triangles = vertices[faces]
    probes = np.vstack((vertices, triangles.mean(axis=1),
                        ((triangles + np.roll(triangles, 1, axis=1)) * .5).reshape(-1, 3)))
    for anterior_mm in range(21 if model == 'positive' else 1):
        placed = copy(registration)
        placed.origin = registration.origin - anterior_mm * registration.matrix[:, 1]
        overlap = float(material_at(vertebrae, placed.points(probes).T).max())
        if overlap < .02:
            return placed, {'anteriorOffsetMm': anterior_mm, 'maxVertebralMaskSample': overlap}
    raise ValueError(f'The {model} arterial model intersects the native vertebral mask.')


def load_context(case):
    ct = volume(case / 'ct.nii.gz', CT_SHA, '<i2').copy()
    structures = load_masks(case)
    vertebrae = structures.pop('vertebrae')
    replace = np.logical_or.reduce(list(structures.values()))
    # Remove the source vessels before inserting the modeled cases. Fill from the
    # neighboring tissue so the CT scan never shows a second native lumen.
    boxes = nd.find_objects(replace)
    region = boxes[0]
    bounds = tuple(slice(max(0, side.start - 6), min(n, side.stop + 6))
                   for side, n in zip(region, ct.shape, strict=True))
    mask = nd.binary_dilation(replace[bounds], iterations=2)
    indices = nd.distance_transform_edt(mask, return_distances=False, return_indices=True)
    local = ct[bounds]
    filled = local[tuple(indices)]
    blended = nd.gaussian_filter(filled.astype('f'), .8)
    local[mask] = blended[mask].round().astype(ct.dtype)
    return ct, vertebrae


def native_frame(sample, registration, torso, grid):
    target = registration.points(np.asarray(sample['target']))
    angle = np.deg2rad(-53 if sample['window'] == 'lateral' else 0)
    beam = unit(registration.matrix @ [np.sin(angle), np.cos(angle), 0])
    if sample['long']:
        width = unit(registration.matrix @ [sample['slope'], 0, 1])
    else:
        width = unit(registration.matrix @ [np.cos(angle), -np.sin(angle), 0])
    if abs(width @ beam) > 1e-9:
        raise ValueError('Probe frame axes are not perpendicular.')
    # Cast from outside the torso toward the vessel. The earliest intersection
    # determines the center of the lens in the same voxels as scene.js and CT.
    outside = target - 400 * beam
    vertices, faces = torso
    offset, = outer_contact_offsets(vertices, faces, [outside], [beam])
    contact = outside + (offset / VOXEL_MM) * beam
    target_depth = float((target - contact) @ beam * VOXEL_MM)
    if sample['window'] == 'lateral' and (registration.inverse @ (contact - target))[0] <= 0:
        raise ValueError('The repeat probe missed the modeled patient-left window.')
    contact_error, = outer_contact_offsets(vertices, faces, [contact], [beam])
    if abs(contact_error) > 1e-4:
        raise ValueError('The modeled probe lens center is detached from the reused exterior.')
    if not 1 < target_depth < grid.depth[grid.field].max() - 1:
        raise ValueError(f'Modeled target outside the probe field at depth {target_depth:.1f} mm.')
    frame = {'contact': contact.tolist(), 'width': width.tolist(), 'beam': beam.tolist(),
             'degrees': (90 if sample['long'] else round(float(np.rad2deg(angle)), 1)),
             'limited': sample['limited'], 'calipers': []}
    pixel_mm = grid.x[0, 1] - grid.x[0, 0]
    for caliper in sample['calipers']:
        native = registration.points(np.asarray(caliper['endpoints']))
        delta = (native - contact) * VOXEL_MM
        if np.max(np.abs(delta @ np.cross(width, beam))) > 1e-6:
            raise ValueError('Modeled vessel caliper left the registered probe plane.')
        x, y = delta @ width, delta @ beam
        radial = np.hypot(x, y + LENS_RADIUS_MM) - LENS_RADIUS_MM
        angle = np.arctan2(x, y + LENS_RADIUS_MM)
        if np.any(radial < 0) or np.any(radial > grid.depth[grid.field].max()) or np.any(
                np.abs(angle) > np.deg2rad(SECTOR_HALF_ANGLE_DEG)):
            raise ValueError('Modeled vessel caliper left the displayed scan sector.')
        px = np.column_stack(((x - grid.x[0, 0]) / pixel_mm, (y - grid.y[0, 0]) / pixel_mm))
        length = np.linalg.norm(native[1] - native[0]) * VOXEL_MM
        expected = np.linalg.norm(np.diff(caliper['endpoints'], axis=0))
        if abs(length - expected) > 1e-6:
            raise ValueError('Registration changed the calibrated vessel dimension.')
        frame['calipers'].append({'millimetres': round(float(length), 4), 'endpointsPx': px.round(4).tolist(),
                                  'transverse': caliper['transverse']})
    return frame, target_depth, abs(contact_error)


def tube_table(rows):
    slots = max(map(len, rows))
    table = np.zeros((len(rows), slots, 11), dtype='f')
    table[..., 2:4] = table[..., 6:8] = 1
    for i, values in enumerate(rows):
        table[i, :len(values)] = values
    return table


def vessel_labels(coords, table, step):
    x, y, z = coords
    indices = np.rint(z / step).astype('i')
    active = (indices >= 0) & (indices < len(table))
    indices = np.clip(indices, 0, len(table) - 1)
    labels = {name: np.zeros(x.shape, bool) for name in ('wall', 'lumen', 'mural', 'vein', 'venous_lumen')}
    for slot in range(table.shape[1]):
        cx, cy, rx, ry, lx, ly, lrx, lry, wall, color, mural = table[indices, slot].transpose(2, 0, 1)
        outer = ((x - cx) / rx)**2 + ((y - cy) / ry)**2
        inside = active & (outer <= 1)
        lumen = inside & (((x - lx) / lrx)**2 + ((y - ly) / lry)**2 <= 1)
        artery = inside & (color > 0)
        labels['wall'] |= artery
        labels['lumen'] |= lumen & artery
        labels['mural'] |= artery & (mural > 0) & (outer <= (1 - wall / np.maximum(rx, ry))**2)
        labels['vein'] |= inside & (color < 0)
        labels['venous_lumen'] |= lumen & (color < 0)
    labels['mural'] &= ~labels['lumen']
    return labels


def render(grid, frame, target_depth, registration, ct, vertebrae, table, step, palette, color):
    xyz = grid.coordinates(frame, grid.x, grid.y)
    coords = registration.coordinates(xyz)
    gray, background = grid.sample(frame, ct, {'vertebrae': vertebrae})
    labels = vessel_labels(coords, table, step)
    labels.update(background)
    fluid = labels['lumen'] | labels['venous_lumen']
    mural = labels['mural']
    wall = (labels['wall'] | labels['vein']) & ~(fluid | mural)
    cues = gray.astype('f')
    grain = np.clip((cues - 45) * .22, -15, 25)
    for area, value in ((fluid, 8), (mural, 66), (wall, 142)):
        soft = nd.gaussian_filter(area.astype('f'), .7)
        local = value + (.18 if value < 10 else .85) * grain
        cues = cues * (1 - soft) + local * soft
    if frame['limited']:
        # One explicit modeled obstruction per failed window. The bright
        # gas interface attenuates the relevant rays before they reach the aorta.
        polar_x, polar_y = grid.polar_x, grid.polar_y
        gas_at = target_depth * .48 + 2.6 * np.cos(polar_x * .23 + coords[2, 0, 0] * .24)
        strength = np.clip((38 - np.abs(polar_x)) / 14, 0, 1)
        hit = strength * (polar_y >= gas_at)
        shadow = material_at(nd.gaussian_filter(np.maximum.accumulate(hit, axis=0).astype('f'), (2.0, 2.6)),
                             grid.to_image)
        echo = material_at(nd.gaussian_filter((strength * (np.abs(polar_y - gas_at) < 1.15)).astype('f'), (1.3, .7)),
                           grid.to_image)
        cues = cues * (1 - .8 * shadow) + 134 * echo
        for mask in labels.values():
            mask &= shadow < .36
    for mask in labels.values():
        mask &= grid.field
    gray = np.where(grid.field, np.clip(cues, 1, 245), 0).astype('u1')
    if frame['limited'] and frame['calipers']:
        raise ValueError('A limited window must withhold calipers.')
    for caliper in frame['calipers']:
        for px, py in caliper['endpointsPx']:
            col, row = round(px), round(py)
            if not labels['wall'][row-2:row+3, col-2:col+3].any():
                raise ValueError('A caliper endpoint does not reach the rasterized outer boundary.')
    section = overlay(gray, labels, palette)
    if not color:
        return gray, section, None
    # Illustrative color presence within the patent modeled lumen. No velocities
    # or direction are assigned to this educational channel fill.
    filled = np.repeat(gray[..., None], 3, axis=2)
    signal = np.clip(145 + grain * 2, 104, 195)
    filled[labels['lumen']] = np.column_stack((signal[labels['lumen']], 40 + grain[labels['lumen']],
                                               29 + grain[labels['lumen']]))
    return gray, section, filled


def write_json(path, value):
    path.write_text(json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n')


def build(study, case, target):
    tour = native_tour(study)
    meshes = {name: input_mesh(study, tour, name) for name in ('aorta', 'torso', 'vertebrae')}
    torso = meshes['torso'][1:]
    ct, vertebrae = load_context(case)
    source = HERE / 'cases/vascular/cases.json'
    cases = [record for record in json.loads(source.read_text()) if record['family'] == 'aaa']
    exported = subprocess.run(['node', str(HERE / 'aaa_model.mjs')], input=json.dumps(cases),
                              text=True, capture_output=True, check=True)
    model = json.loads(exported.stdout)
    registration = Registration(meshes['aorta'][1], model['bifurcationMm'])
    grid = ImagingGrid(tour['sectorDepthMm'])
    assets = target / 'assets'
    assets.mkdir()
    paths = {name: '../../' + path for name, (path, _, _) in meshes.items() if name != 'aorta'}
    tables = {}
    registrations = {}
    placements = {}
    for name, data in model['models'].items():
        tables[name] = tube_table(data['samples'])
        placed, receipt = clear_spine(registration, data['surfaces']['wall'], vertebrae, name)
        registrations[name] = placed
        placements[name] = receipt
        mesh_dir = assets / name
        mesh_dir.mkdir()
        for part, mesh in data['surfaces'].items():
            vertices = placed.points(np.asarray(mesh['vertices']))
            # Native RAS and authored coordinates have opposite handedness.
            order = [0, 2, 1] if np.linalg.det(registration.matrix) < 0 else [0, 1, 2]
            faces = np.asarray(mesh['faces']).reshape(-1, 3)[:, order]
            (mesh_dir / f'{part}.mesh').write_bytes(mesh_bytes(vertices, faces))
    frame_total = 0
    depths = []
    contact_errors = []
    color_frames = 0
    contact_cache = {}
    for record in model['cases']:
        record_id = record['id']
        model_name = record['model']
        placed = registrations[model_name]
        palette = [PARTS[3], PARTS[2], PARTS[0], PARTS[1]] + ([MURAL] if model_name == 'positive' else [])
        config = {
            'assetRoot': './', 'organ': 'wall', 'parts': PARTS, 'voxelMm': VOXEL_MM,
            'sectorDepthMm': tour['sectorDepthMm'], 'focusRadius': 56, 'bodyRegion': 'Abdomen',
            'meshPaths': paths | {part: f'assets/{model_name}/{part}.mesh' for part in ('wall', 'lumen', 'vein')},
            'overlayParts': palette,
        }
        chapters = {}
        for chapter in record['chapters']:
            chapter_id = chapter['id']
            print(f'Building {record_id}/{chapter_id}', flush=True)
            media_root = f'assets/{record_id}/{chapter_id}/'
            media = target / media_root
            media.mkdir(parents=True)
            frames = []
            samples = chapter['frames']
            for index, sample in enumerate(samples):
                # Identical positions in different cases have the same torso contact.
                key = (model_name, json.dumps(sample, sort_keys=True))
                if key not in contact_cache:
                    contact_cache[key] = native_frame(sample, placed, torso, grid)
                frame, depth, contact_error = contact_cache[key]
                gray, section, color = render(grid, frame, depth, placed, ct, vertebrae, tables[model_name],
                                              model['sampleIntervalMm'], palette, chapter['color'])
                Image.fromarray(gray).save(media / f'scan-{index:02}.webp', quality=86, method=3)
                Image.fromarray(section).save(media / f'section-{index:02}.webp', quality=86, method=3)
                if color is not None:
                    Image.fromarray(color).save(media / f'color-{index:02}.webp', quality=86, method=3)
                    color_frames += 1
                frames.append(frame)
                depths.append(depth)
                contact_errors.append(contact_error)
                frame_total += 1
            active = samples[chapter['evidenceFrame']]
            focus = placed.points(np.asarray(active['target'])).tolist()
            chapters[chapter_id] = {
                'mediaRoot': media_root, 'frames': frames, 'hasColor': chapter['color'],
                'config': config | {'focus': focus},
            }
        write_json(target / f'{record_id}.scene.json', chapters)
    files = {path.relative_to(target).as_posix(): sha256(path.read_bytes())
             for path in sorted(target.rglob('*')) if path.is_file()}
    write_json(target / 'verification.json', {
        'version': 1,
        'frameCount': frame_total,
        'colorFrameCount': color_frames,
        'maxLensCenterContactErrorMm': max(contact_errors),
        'targetDepthMm': [round(min(depths), 3), round(max(depths), 3)],
        'sharedAssets': {name: sha256((study / path).read_bytes()) for name, (path, _, _) in meshes.items()},
        'recipeSha256': acquisition_recipe_sha256(),
        'ctSha256': CT_SHA,
        'placements': placements,
        'modelMmToSceneVoxels': np.column_stack((registration.matrix, registration.origin)).tolist(),
        'files': files,
    })


def acquisition_recipe_sha256():
    source_hashes = {name: sha256((HERE / name).read_bytes()) for name in RECIPE_FILES}
    return sha256(json.dumps(source_hashes, sort_keys=True).encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path, help='Pinned TotalSegmentator s1233 case directory.')
    parser.add_argument('study', type=Path, help='Assembled local study containing the normal aortic sweep.')
    parser.add_argument('destination', type=Path, help='Fresh evidence directory for the AAA tour media.')
    args = parser.parse_args()
    if args.destination.exists():
        parser.error('Choose a fresh destination directory.')
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.destination.parent) as scratch:
        stage = Path(scratch) / 'acquisition'
        stage.mkdir()
        build(args.study, args.case, stage)
        stage.rename(args.destination)


if __name__ == '__main__':
    main()
