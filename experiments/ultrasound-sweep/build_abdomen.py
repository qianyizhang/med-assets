"""Build the local abdominal sweep extensions from pinned s1233 volumes."""

import argparse
import json
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial.transform import Rotation, Slerp
from skimage.measure import label, marching_cubes

from build_study import (
    CT_SHA, H, LAST, LONG, W, WORKSHOP, body_surface, fine_scatter, material_at, unit, volume,
)
from delivery import read_poses, sha256, sweep_files, verify_inventory, write_manifest
from display_body import BONES_SHA, SKIN_SHA, registered_atlas
from fit_abdomen import CONTACT_TOLERANCE_MM, fit_window, max_outer_error, open_flanks
from geometry import KEYFRAMES, LENS_RADIUS_MM, SECTOR_HALF_ANGLE_DEG, VOXEL_MM
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
LUMENS = {'gallbladder', 'portal_vein_and_splenic_vein', 'aorta', 'inferior_vena_cava'}
PINS = {
    **WORKSHOP['maskSha256'],
    'pancreas': '9f11083652d059e85514d419c90124911953dbbce2018ccc549eaa2c73b0968b',
    'spleen': '760eb489a2f6821ce25e7565e4d73709cab5a1ef0af6537d193b2ce036213573',
    'kidney_right': '8ca7e6696b90cb1e7e39b14e5c8f7e92c59b9344bff8fd368009751335abc8b5',
    'kidney_left': 'e0c7e53f00a20cedbe3e13d687ffc6d5e03a33824d4e4c7124f25335179b794e',
    'aorta': 'c2751ba8bb12ed2091db7e0446f3f333acf47db5d35e8f75c96fab4c6564ab2e',
    'inferior_vena_cava': '44504ba513ec6292a4a030c097948f546054ea36fdfbca7b6896103cf1b488e0',
    'portal_vein_and_splenic_vein': 'b1437b7058628669a6bc9e3b2e142dd019f1a2eeee88307e141f8f7d37e17e60',
    **json.loads((HERE / 'research/rib-pins.json').read_text()),
    'rib_left_7': 'd9b0bf9b9d42918d1fd205fe07feff83884c76dcc0d042279ec8f70534d5747b',
    'rib_left_8': 'de19e43bb40e4cdf0a671b7934587641eedc0f65cde5b54c4922b66b06000058',
    'rib_left_9': 'bc45f931883dfd985f4572ce06ab16e904c2d5c27c7507f7596f7ed8ce8565f0',
    'rib_left_10': 'e64fe3453900bc1d466f9da3abaab5f53e78d4d653b8ce267081cb90ea875a1f',
    'rib_left_11': 'a934f2874e775da510d46ab0ef9f4dcc4536fab43cfaabbd0c26f9149f88a829',
    'rib_left_12': '172ab7dfdfa6daabc27a1691b835a2b8fdd7292155e6c4971ff0e6377b1af411',
    'rib_right_11': '78dc5b82c439b359983329e5247dbc629d8b8e8630dd68d5e398e5800c76a5a3',
    'rib_right_12': '9f7ae329e40c2cf483c19a191572cbee68ad0ae8606946e5a12ac86115221edb',
}
FIT_RIBS = tuple(f'rib_right_{number}' for number in range(6, 11))
RIB_REGIONS = {
    'spleen': ('left', range(7, 13)),
    'kidney-left': ('left', range(9, 13)),
    'kidney-right': ('right', range(9, 13)),
}

# Each pose is (center beam target in case voxels, approximate outward direction,
# image-left direction). +X is patient right, +Y is anterior, +Z is superior.
# These are authored teaching planes through the case, with no respiratory deformation.
POSES = {
    'liver': (
        ((175, 155, 219), (.37, .92, -.21), (.78, 0, -.40)),
        ((162, 139, 209), (.26, .96, -.09), (0, -.08, 1)),
    ),
    'portal-vein': (
        # Follow the main trunk toward the liver, then rotate at the same target.
        ((157, 150, 206), (.26, .96, -.12), (1, 0, .21)),
        ((157, 150, 206), (.26, .96, -.12), (.202, -.175, -.964)),
    ),
    'pancreas': (
        ((137, 160, 211), (.03, .98, -.18), (1, 0, -.53)),
        ((153, 160, 188), (.08, .995, -.06), (.28, 0, .96)),
    ),
    'spleen': (
        # A posterior window separates splenic length from thickness on rotation.
        ((80, 103, 226), (-.342, -.915, -.215), (.928, -.365, .078)),
        ((80, 103, 226), (-.342, -.915, -.215), (-.150, -.173, .974)),
    ),
    'kidney-right': (
        ((193, 132, 166), (.98, .13, -.12), (-.08, -.74, .67)),
        ((193, 132, 166), (.98, .13, -.12), (.03, .67, .74)),
    ),
    'kidney-left': (
        ((83, 137, 184), (-.98, .13, -.10), (.04, -.60, .80)),
        ((83, 137, 185), (-.98, .13, -.10), (.04, .80, .60)),
    ),
    'aorta': (
        ((134, 139, 170), (.045, .998, -.05), (0, -.14, 1)),
        ((136, 139, 177), (.025, .998, -.11), (1, 0, 0)),
    ),
    'ivc': (
        ((156, 139, 205), (.17, .98, -.12), (.18, 0, 1)),
        ((154, 138, 196), (.14, .99, -.06), (1, 0, 0)),
    ),
}

# Required inset landmarks at each named frame. The track's primary target must
# also be present at every other frame.
LANDMARKS = {
    'liver': ('portal_vein_and_splenic_vein', 'inferior_vena_cava'),
    'portal-vein': ('liver', 'liver'),
    'pancreas': ('portal_vein_and_splenic_vein', None),
    'spleen': (None, None),
    'kidney-right': (None, None),
    'kidney-left': (None, None),
    'aorta': (None, 'inferior_vena_cava'),
    'ivc': ('liver', None),
}


def read_tracks():
    catalogue = json.loads((HERE / 'abdomen-tracks.json').read_text())
    structures = catalogue['structures']
    return [{**track, 'parts': [{'id': key, **structures[key]} for key in track['parts']]}
            for track in catalogue['sweeps']]


def pose_recipe_sha256(sweep_id):
    return sha256(json.dumps(POSES[sweep_id], separators=(',', ':')).encode())


def axes(outward, marker):
    beam = -unit(np.asarray(outward))
    marker = np.asarray(marker)
    width = -unit(marker - (marker @ beam) * beam)
    return np.column_stack([width, np.cross(beam, width), beam])


def contact_point(target, beam, shell):
    steps = np.linspace(0, 215, 431)
    ray = target[:, None] - beam[:, None] * steps
    inside = material_at(shell, ray / 2)
    exits = np.flatnonzero(inside <= .5)
    if not exits.size or exits[0] == 0:
        raise ValueError('Target ray has no interior-to-surface crossing')
    i = exits[0]
    shift = steps[i - 1] + .5 * (inside[i - 1] - .5) / (inside[i - 1] - inside[i])
    return target - beam * shift


def poses(sweep_id, shell):
    first, last = POSES[sweep_id]
    target_a, target_b = (np.array(pose[0], dtype=float) for pose in (first, last))
    start = axes(*first[1:])
    end = axes(*last[1:])
    path = Slerp([0, 1], Rotation.from_matrix([start, end]))
    for frame in range(LAST + 1):
        fraction = max(0, (frame - LONG) / (LAST - LONG))
        width, cross, beam = path(fraction).as_matrix().T
        # Slide a short distance from an adjacent plane into the named first view.
        target = (1 - fraction) * target_a + fraction * target_b
        target += max(0, 1 - frame / LONG) * 5 * cross
        contact = contact_point(target, beam, shell)
        rotation = Rotation.from_matrix(path(fraction).as_matrix() @ start.T).magnitude()
        yield dict(contact=contact.tolist(), width=width.tolist(), beam=beam.tolist(),
                   degrees=round(np.rad2deg(rotation), 1))


def mesh_from_mask(mask, z_bounds=None):
    nonzero = np.column_stack(np.nonzero(mask))
    lower = np.maximum(nonzero.min(0) - 4, 0)
    upper = np.minimum(nonzero.max(0) + 5, mask.shape)
    if z_bounds is not None:
        lower[2] = max(lower[2], z_bounds[0])
        upper[2] = min(upper[2], z_bounds[1])
    cropped = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    values = nd.gaussian_filter(np.pad(cropped, 1).astype('f'), .85)
    vertices, faces, _, _ = marching_cubes(values, .5, step_size=1)
    return mesh_bytes(vertices + lower - 1, faces[:, ::-1])


def scene_assets(track, scene_directory=None):
    """Read exact governed meshes, or verify their staged copies before assembly."""
    references = track.get('sceneAssets', {})
    if not references:
        return {}

    from assetkit.blobs import read_verified
    from assetkit.registry import AssetRegistry, ExportRef, VoxelGrid

    repo = HERE.parents[1]
    registry = AssetRegistry.load(repo, include_legacy_adapters=False)
    grid = VoxelGrid.model_validate({key: WORKSHOP[key] for key in ('case', 'shape', 'rasMmFromVoxel')})
    slots = {entry['id'] for entry in track['parts']}
    meshes = {}
    for part, raw_ref in references.items():
        if part not in slots:
            raise ValueError(f'{track["id"]}: Unknown scene asset slot {part!r}')
        export = registry.require_voxel_export(ExportRef.model_validate(raw_ref), grid)
        if export.format != 'mesh' or export.sha256 is None or export.bytes is None:
            raise ValueError(f'{track["id"]}: Expected an identity-pinned packed mesh for {part}')
        if scene_directory is None:
            meshes[part] = read_verified(repo, export.path, export.sha256, export.bytes)
        else:
            meshes[part] = read_verified(scene_directory, f'{part}.mesh', export.sha256, export.bytes)
    return meshes


class ImagingGrid:
    """Map the same convex sector to a raster and to radial propagation paths."""

    def __init__(self, depth_mm, roi=None):
        pitch = max(.41, depth_mm / (H - 21))
        row, col = np.mgrid[:H, :W]
        origin_x, origin_y = W / 2, 12
        if roi is not None:
            left, top, right, bottom = roi
            scale = (right - left) / W
            if (not 0 <= left < right <= W or not 0 <= top < bottom <= H
                    or not np.isclose(scale, (bottom - top) / H)):
                raise ValueError(f'Detail crop must fit the field with equal pixel spacing: {roi}')
            # Map pixel centers through the crop; bounds are full-raster pixel edges.
            origin_x = (origin_x + .5 - left) / scale - .5
            origin_y = (origin_y + .5 - top) / scale - .5
            pitch *= scale
        self.x = (col - origin_x) * pitch
        self.y = (row - origin_y) * pitch
        self.depth = np.hypot(self.x, self.y + LENS_RADIUS_MM) - LENS_RADIUS_MM
        self.angle = np.arctan2(self.x, self.y + LENS_RADIUS_MM)
        half_angle = np.deg2rad(SECTOR_HALF_ANGLE_DEG)
        self.field = (self.depth >= 0) & (self.depth <= depth_mm) & (np.abs(self.angle) < half_angle)

        theta = np.linspace(-half_angle, half_angle, 301)[None, :]
        radius = LENS_RADIUS_MM + np.arange(0, depth_mm + .5, .5)[:, None]
        self.polar_x = radius * np.sin(theta)
        self.polar_y = radius * np.cos(theta) - LENS_RADIUS_MM
        self.to_polar = np.stack((self.polar_y / pitch + origin_y, self.polar_x / pitch + origin_x))
        self.to_image = np.stack((self.depth / .5, (self.angle + half_angle) / (2 * half_angle) * 300))

    @staticmethod
    def coordinates(frame, x, y):
        contact, width, beam = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
        return contact[:, None, None] + (
            width[:, None, None] * x + beam[:, None, None] * y
        ) / VOXEL_MM

    def sample(self, frame, ct, masks):
        xyz = self.coordinates(frame, self.x, self.y)
        hu = nd.gaussian_filter(material_at(ct, xyz), .84)
        labels = {name: (material_at(mask, xyz) >= .5) & self.field for name, mask in masks.items()}

        space = self.coordinates(frame, self.polar_x, self.polar_y)
        polar_hu = material_at(ct, space)
        # Coarse attenuation cues remain illustrative. Begin below the contact layer.
        blockers = np.clip((polar_hu - 230) / 430, 0, 1) + .65 * np.clip((-polar_hu - 490) / 400, 0, 1)
        blockers[:9] = 0
        transmission = material_at(np.exp(-nd.gaussian_filter(np.cumsum(blockers, axis=0), (1.4, 2.4)) * .052),
                                   self.to_image)

        dy, dx = np.gradient(hu)
        edge = nd.gaussian_filter(np.abs(dy * np.cos(self.angle) + dx * np.sin(self.angle)), (.65, 1.35))
        tissue = 44 + np.clip((hu + 70) * .23, -28, 46)
        fluid = np.zeros_like(hu)
        for name, region in labels.items():
            soft = nd.gaussian_filter(region.astype('f'), .9)
            if name in LUMENS:
                np.maximum(fluid, soft, out=fluid)
            elif name in {'liver', 'spleen', 'pancreas'}:
                tissue += soft * (13 if name == 'pancreas' else 9)
        speckle = fine_scatter(xyz) * 109
        for offset, weight in ((np.array([.39, .15, .61]), .26), (np.array([.05, .51, .8]), .19)):
            speckle += fine_scatter(xyz + offset[:, None, None]) * (82 * weight)
        wall = np.clip(np.abs(np.gradient(fluid, axis=0)) * 142, 0, 38)
        gray = (tissue + np.clip(edge * 3.25, 0, 100) + speckle) * (1 - .88 * fluid) + wall
        gray *= transmission * np.exp(-np.maximum(self.depth, 0) / 330)
        gray = np.where(self.field, np.clip(gray, 1, 245), 0).astype('u1')
        return gray, labels


def section_palette(track):
    return sorted((part for part in track['parts'] if part['id'] in track['overlayParts']),
                  key=lambda part: (part['id'] == track['organ'], part['id'] in LUMENS))


def section_palette_sha256(track):
    palette = [[part[key] for key in ('id', 'color', 'opacity')] for part in section_palette(track)]
    return sha256(json.dumps(palette, separators=(',', ':')).encode())


def overlay(gray, labels, parts):
    rgb = np.repeat(gray[..., None], 3, axis=2).astype('f')
    for part in parts:
        region = labels[part['id']]
        hex_color = part['color'].removeprefix('#')
        color = np.array([int(hex_color[i:i + 2], 16) for i in (0, 2, 4)])
        opacity = part['opacity']
        fill = (region * opacity)[..., None]
        rgb = rgb * (1 - fill) + color * fill
        rim = (region & ~nd.binary_erosion(region))[..., None] * .43
        rgb = rgb * (1 - rim) + np.minimum(color * 1.35, 255) * rim
    return rgb.astype('u1')


def measure_landmark(mask, gray):
    pieces = label(mask)
    size = np.bincount(pieces.ravel())
    size[0] = 0
    major = pieces == size.argmax() if size.max() else np.zeros_like(mask)
    rows, cols = np.nonzero(major)
    return {
        'largestSectionPixels': len(rows),
        'imageBounds': [int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max())] if len(rows) else None,
        'meanGray': round(float(gray[major].mean()), 1) if len(rows) else None,
    }


def exterior_inputs(case, tracks):
    if not any(track['exterior'] == 'fitted-atlas' for track in tracks):
        return None
    points = []
    for name in FIT_RIBS:
        rib = volume(case / f'segmentations/{name}.nii.gz', PINS[name], 'u1')
        points.append(np.column_stack(np.nonzero(rib)))
    vertices, faces = registered_atlas(np.concatenate(points))
    flank = None
    if any(track['id'] in RIB_REGIONS for track in tracks):
        flank = open_flanks(vertices, faces)
    return vertices, faces, flank


def fit_exterior(track, frames, shell, torso, source):
    contacts = np.asarray([frame['contact'] for frame in frames])
    beams = np.asarray([frame['beam'] for frame in frames])
    ct_vertices, ct_faces = torso
    ct_error = max_outer_error(ct_vertices, ct_faces, contacts, beams)
    lateral = track['id'] in RIB_REGIONS
    result = {'exterior': track['exterior'], 'caseCtMaxOuterContactErrorMm': round(ct_error, 3)}
    if track['exterior'] == 'case-ct':
        vertices, faces, error = ct_vertices, ct_faces, ct_error
    else:
        raw, faces, flank = source
        posed, arm_weight = flank if lateral else (raw, np.zeros(len(raw)))
        # Use the left/right flank sheet even when a posterolateral beam points mostly forward.
        vertices = fit_window(posed, shell, contacts, beams, arm_weight, axis=0 if lateral else None)
        error = max_outer_error(vertices, faces, contacts, beams)
        result.update(atlasSkinSha256=SKIN_SHA, atlasBonesSha256=BONES_SHA,
                      registrationMaskSha256={name: PINS[name] for name in FIT_RIBS},
                      atlasBeforeConformanceMaxOuterContactErrorMm=round(max_outer_error(
                          raw, faces, contacts, beams), 3),
                      armPose='shoulders moved back and out' if lateral else 'source atlas')
    if error > CONTACT_TOLERANCE_MM:
        raise ValueError(f'{track["id"]}: incoming ray meets the exterior {error:.2f} mm from the contact')
    result['surfaceMaxOuterContactErrorMm'] = round(error, 3)
    return mesh_bytes(vertices, faces), result


def refresh_exteriors(tracks, sweeps_dir, shell, torso, source):
    """Replace only torso meshes and their receipts in an already authored study."""
    updated = []
    for track in tracks:
        output = sweeps_dir / track['id']
        frames = read_poses(output / 'sweep.js')
        receipt_path = output / 'verification.json'
        receipt = json.loads(receipt_path.read_text())
        if receipt['ctSha256'] != CT_SHA:
            raise ValueError(f'{track["id"]}: existing sweep has a different source CT')
        names = sweep_files(['torso', *(part['id'] for part in track['parts'])])
        verify_inventory(output, names)
        mesh, exterior = fit_exterior(track, frames, shell, torso, source)
        receipt.pop('surfaceMaxCenterlineErrorMm', None)
        updated.append((output, mesh, {**receipt, **exterior}, names))
    for output, mesh, receipt, names in updated:
        for path, data in ((output / 'scenes/torso.mesh', mesh),
                           (output / 'verification.json', (json.dumps(receipt, indent=2) + '\n').encode())):
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                stream.write(data)
            os.chmod(stream.name, path.stat().st_mode & 0o777)
            os.replace(stream.name, path)
        write_manifest(output, names)
        print(f'{output.name}: {receipt["exterior"]}, maximum incoming-ray error '
              f'{receipt["surfaceMaxOuterContactErrorMm"]:.3f} mm', flush=True)


def build_track(track, output, shell, ct, masks, torso, source, governed_meshes):
    sweep_id = track['id']
    grid = ImagingGrid(track['sectorDepthMm'])
    frames = list(poses(sweep_id, shell))
    exterior_mesh, exterior_receipt = fit_exterior(track, frames, shell, torso, source)
    media, scenes = output / 'media', output / 'scenes'
    media.mkdir()
    scenes.mkdir()
    (scenes / 'torso.mesh').write_bytes(exterior_mesh)
    for name, mask in masks.items():
        # Only the abdominal portions belong in these locators. CT sampling uses full masks.
        bounds = (140, 271) if name in {'aorta', 'inferior_vena_cava'} else None
        raw = governed_meshes.get(name)
        (scenes / f'{name}.mesh').write_bytes(mesh_from_mask(mask, bounds) if raw is None else raw)
    overlay_order = section_palette(track)
    sample_masks = {part['id']: masks[part['id']] for part in overlay_order}
    receipt = {}
    for i, frame in enumerate(frames):
        gray, labels = grid.sample(frame, ct, sample_masks)
        target = measure_landmark(labels[track['organ']], gray)
        if target['largestSectionPixels'] < 55:
            raise ValueError(f'{sweep_id} frame {i} shows only {target["largestSectionPixels"]} target pixels')
        if i in KEYFRAMES:
            context = LANDMARKS[sweep_id][KEYFRAMES.index(i)]
            receipt[str(i)] = {name: measure_landmark(mask, gray) for name, mask in labels.items()}
            if context and receipt[str(i)][context]['largestSectionPixels'] < 30:
                raise ValueError(f'{sweep_id} frame {i} misses {context}: {receipt[str(i)][context]}')
        Image.fromarray(gray).save(media / f'scan-{i:02}.webp', quality=90)
        Image.fromarray(overlay(gray, labels, overlay_order)).save(media / f'section-{i:02}.webp', quality=88)
    (output / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')
    (output / 'verification.json').write_text(json.dumps({
        'case': 's1233', 'coordinateFrame': 'source voxel grid, RAS axes', 'voxelMm': VOXEL_MM,
        'sectorDepthMm': track['sectorDepthMm'],
        'sectorHalfAngleDeg': SECTOR_HALF_ANGLE_DEG, 'lensRadiusMm': LENS_RADIUS_MM,
        'ctSha256': CT_SHA, 'poseRecipeSha256': pose_recipe_sha256(sweep_id),
        'sectionPaletteSha256': section_palette_sha256(track), **exterior_receipt,
        'maskSha256': {key: PINS[key] for key in PINS if key in masks or
                       ('ribs' in masks and key in rib_names(sweep_id))},
        'frames': receipt,
    }, indent=2) + '\n')
    write_manifest(output, sweep_files(['torso', *masks]))
    print(f'{sweep_id}: {track["exterior"]}, maximum incoming-ray error '
          f'{exterior_receipt["surfaceMaxOuterContactErrorMm"]:.3f} mm', flush=True)


def rib_names(sweep_id):
    if sweep_id not in RIB_REGIONS:
        return []
    side, numbers = RIB_REGIONS[sweep_id]
    return [f'rib_{side}_{number}' for number in numbers]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('sweeps_dir', type=Path, nargs='?')
    parser.add_argument('--export-liver', type=Path, metavar='MESH',
                        help='Build only the packed liver surface from the pinned mask')
    parser.add_argument('--track', choices=POSES, action='append')
    parser.add_argument('--refresh-exteriors', action='store_true',
                        help='Replace torso meshes and update exterior receipts for an existing sweep build.')
    args = parser.parse_args()
    if args.export_liver is not None:
        if args.sweeps_dir is not None or args.track or args.refresh_exteriors:
            parser.error('--export-liver takes only the source case and output mesh')
        mask = volume(args.case / 'segmentations/liver.nii.gz', PINS['liver'], 'u1')
        raw = mesh_from_mask(mask)
        with args.export_liver.open('xb') as stream:
            stream.write(raw)
        return
    if args.sweeps_dir is None:
        parser.error('sweeps_dir is required for a sweep build')
    tracks = [track for track in read_tracks()
              if args.track is None or track['id'] in args.track]
    for track in tracks:
        if not args.refresh_exteriors and (args.sweeps_dir / track['id']).exists():
            parser.error(f'Choose a fresh destination for {track["id"]}.')
    scene_meshes = {} if args.refresh_exteriors else {track['id']: scene_assets(track) for track in tracks}
    args.sweeps_dir.mkdir(parents=True, exist_ok=True)

    ct = volume(args.case / 'ct.nii.gz', CT_SHA, '<i2')
    shell, vertices, faces = body_surface(ct)
    torso = vertices, faces[:, ::-1]
    source = exterior_inputs(args.case, tracks)
    if args.refresh_exteriors:
        refresh_exteriors(tracks, args.sweeps_dir, shell, torso, source)
        return
    masks = {}
    for track in tracks:
        sweep_id = track['id']
        names = [part['id'] for part in track['parts']]
        for name in set(names) - {'ribs'} - masks.keys():
            masks[name] = volume(args.case / f'segmentations/{name}.nii.gz', PINS[name], 'u1')
        track_masks = {name: masks[name] for name in names if name != 'ribs'}
        for name in rib_names(sweep_id):
            rib = volume(args.case / f'segmentations/{name}.nii.gz', PINS[name], 'u1')
            if 'ribs' not in track_masks:
                track_masks['ribs'] = rib.copy()
            else:
                track_masks['ribs'] |= rib
        with tempfile.TemporaryDirectory(dir=args.sweeps_dir) as staging:
            output = Path(staging) / sweep_id
            output.mkdir()
            build_track(track, output, shell, ct, track_masks, torso, source, scene_meshes[sweep_id])
            os.rename(output, args.sweeps_dir / sweep_id)


if __name__ == '__main__':
    main()
