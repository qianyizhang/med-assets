"""Build the local sweep from pinned public inputs and the two acquired references."""
import argparse
import gzip
import hashlib
import json
import shutil
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage.measure import find_contours, marching_cubes

HERE = Path(__file__).resolve().parent
WORKSHOP = json.loads((HERE.parents[1] / 'assemblies/workshop-s1233/inputs.json').read_text())
CT_SHA = '5352376d8fd9c0ab582a7fca1443f28762a66b9782d59c645b976771587c0cfc'
FIG_SHA = 'f62a0d6d988c87a8a53b304fb12f5b0152fe5a45d896de42a4a164e6f923ae43'
CINE_SHA = '5c58e3797b0e6f105353e169b05d13a4db359ac1127f2717a9c122497c8abfeb'
SHAPE = tuple(WORKSHOP['shape'])
AFFINE = np.array(WORKSHOP['rasMmFromVoxel'])
W, H = 500, 350
LONG, LAST = 12, 48


def checked(path, sha):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError(f'Unexpected input identity: {path.name}')
    return data


def volume(path, sha, dtype):
    raw = gzip.decompress(checked(path, sha))
    affine = np.array(struct.unpack_from('<12f', raw, 280)).reshape(3, 4)
    if struct.unpack_from('<3h', raw, 42) != SHAPE or not np.array_equal(affine, AFFINE[:3]):
        raise ValueError(f'Unexpected grid: {path.name}')
    return np.frombuffer(raw, dtype, offset=int(struct.unpack_from('<f', raw, 108)[0])).reshape(SHAPE, order='F')


def unit(vector):
    return vector / np.linalg.norm(vector)


def material_at(volume, coordinates):
    return nd.map_coordinates(volume, coordinates, order=1, mode='nearest', output=np.float32, prefilter=False)


def fine_scatter(coordinates):
    # Interpolate a deterministic submillimetre scatter field at each pose.
    grid = coordinates * 4.25
    cells = np.floor(grid).astype(np.int32)
    fraction = grid - cells
    values = np.zeros(grid.shape[1:], dtype=np.float32)
    for dx, dy, dz in np.ndindex(2, 2, 2):
        key = ((cells[0]+dx).astype('u4') * np.uint32(73856093)
               ^ (cells[1]+dy).astype('u4') * np.uint32(19349663)
               ^ (cells[2]+dz).astype('u4') * np.uint32(83492791))
        key ^= key >> 16
        key *= np.uint32(2246822519)
        key ^= key >> 13
        weight = ((fraction[0] if dx else 1-fraction[0]) *
                  (fraction[1] if dy else 1-fraction[1]) *
                  (fraction[2] if dz else 1-fraction[2]))
        values += ((key / 4294967295.0) * 2 - 1) * weight
    return nd.gaussian_filter(values, (.40, .92))


def body_surface(ct):
    # Isolate the external torso before smoothing, excluding the bed and the head.
    solid = ct[:, :, 84:333:2][::2, ::2] > -380
    solid = nd.binary_opening(solid, iterations=1)
    components, _ = nd.label(solid)
    counts = np.bincount(components.ravel())
    solid = components == (counts[1:].argmax() + 1)
    solid = np.stack([nd.binary_fill_holes(a) for a in solid.transpose(2, 0, 1)], axis=2)
    shell = nd.gaussian_filter(solid.astype('f'), 1.15)
    vertices, faces, _, _ = marching_cubes(shell, 0.5, step_size=1)
    vertices = vertices * 2 + [0, 0, 84]
    return shell, vertices, faces


def anatomy_surfaces(case, masks, output):
    rib_names = ['rib_right_' + str(i) for i in range(6, 11)]
    rib_pins = json.loads((HERE / 'research/rib-pins.json').read_text())
    ribs = np.zeros(SHAPE, dtype='u1')
    for name in rib_names:
        ribs |= volume(case / f'segmentations/{name}.nii.gz', rib_pins[name], 'u1')
    for name, mask in [('ribs', ribs), ('liver', masks['liver']), ('gallbladder', masks['gallbladder'])]:
        values = nd.gaussian_filter(mask.astype('f'), .85)
        vertices, faces, _, _ = marching_cubes(values, .5, step_size=2)
        np.savez(output / f'{name}.npz', vertices=vertices, faces=faces)


def render(case, output):
    media = output / 'media'
    ct = volume(case / 'ct.nii.gz', CT_SHA, '<i2')
    mask_pins = {**WORKSHOP['maskSha256'], 'portal_vein_and_splenic_vein':
                 'b1437b7058628669a6bc9e3b2e142dd019f1a2eeee88307e141f8f7d37e17e60'}
    masks = {name: volume(case / f'segmentations/{name}.nii.gz', mask_pins[name], 'u1')
             for name in ('gallbladder', 'liver', 'portal_vein_and_splenic_vein')}
    anatomy_surfaces(case, masks, output)
    shell, vertices, faces = body_surface(ct)
    np.savez(output / 'torso.npz', vertices=vertices, faces=faces)
    pts = np.argwhere(masks['gallbladder'])
    center = pts.mean(axis=0)
    major = np.linalg.eigh(np.cov(pts.T))[1][:, -1]
    if major[0] > 0:
        major *= -1
    # An anterior-medial window keeps the beam nearly perpendicular to the major axis.
    outward = unit(np.array([-.55, .82, -.17]))
    beam = -outward
    width = unit(major - major.dot(beam) * beam)
    cross = unit(np.cross(beam, width))
    row, col = np.mgrid[:H, :W]
    x = (col - W / 2) * .41
    y = (row - 12) * .41
    radius = np.hypot(x, y + 38)
    depth = radius - 38
    field = (depth >= 0) & (depth <= 133) & (np.abs(np.arctan2(x, y + 38)) < np.deg2rad(36))
    rng = np.random.default_rng(931)
    # Sample one stationary scatter field so tissues retain texture as the probe moves.
    scatter = rng.standard_normal(SHAPE, dtype=np.float32)
    frames = []
    for i in range(LAST + 1):
        angle = max(0, (i - LONG) / (LAST - LONG)) * np.pi / 2
        lateral = width * np.cos(angle) + cross * np.sin(angle)
        target = center + cross * max(0, 1 - i / LONG) * 13
        steps = np.arange(0, 135, .1)
        ray = target[:, None] + outward[:, None] * steps
        inside = material_at(shell, (ray - np.array([0, 0, 84])[:, None]) / 2) > .5
        contact = ray[:, np.flatnonzero(~inside)[0]]
        xyz = contact[:, None, None] + (lateral[:, None, None] * x + beam[:, None, None] * y) / 1.5
        hu = nd.gaussian_filter(material_at(ct, xyz), 1)
        gb, liver, vessel = (nd.gaussian_filter(material_at(m, xyz), 1.5) for m in masks.values())
        grain = nd.gaussian_filter(material_at(scatter, xyz), (.65, 1.65))
        # CT supplies interfaces and relative attenuation cues, not measured acoustic properties.
        dy, dx = np.gradient(hu)
        edge = nd.gaussian_filter(np.abs(dy + dx * x / (y + 38)), (.75, 1.5))
        interface = np.clip(edge * 2.7, 0, 105)
        wall = np.clip(np.abs(np.gradient(gb, axis=0)) * 490, 0, 83)
        posterior = np.clip(np.cumsum(gb, axis=0) * .27, 0, 21)
        tissue = 45 + np.clip((hu + 85) * .20, -23, 45) + 18 * liver
        gray = (tissue + interface + grain * 27 + fine_scatter(xyz) * 110 + posterior) * (1 - .95*gb) * (1 - .70*vessel) + wall
        gray *= np.exp(-np.maximum(depth, 0) / 350)
        gray = np.where(field, np.clip(gray, 1, 245), 0).astype('u1')
        Image.fromarray(gray).save(media / f'scan-{i:02}.webp', quality=90)
        rgb = np.repeat(gray[..., None], 3, axis=2).astype(float)
        for mask, color, opacity in ((liver, [181, 115, 86], .57), (gb, [59, 191, 162], .91),
                                     (vessel, [121, 154, 196], .72)):
            alpha = (opacity * mask * field)[..., None]
            rgb = rgb * (1-alpha) + np.array(color) * alpha
        Image.fromarray(rgb.astype('u1')).save(media / f'section-{i:02}.webp', quality=86)
        outlines = find_contours((gb * field), .50)
        poly = max(outlines, key=len)[::3, ::-1].round(1).tolist() if outlines else []
        frames.append(dict(contact=contact.tolist(), width=lateral.tolist(), beam=beam.tolist(), degrees=round(np.rad2deg(angle), 1), outline=poly))
    for i in (LONG, LAST):
        if len(frames[i]['outline']) < 12:
            raise ValueError(f'Missing target at teaching frame {i}')
    (output / 'sweep.js').write_text('const sweep = ' + json.dumps(frames, separators=(',', ':')) + ';\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', type=Path)
    parser.add_argument('long_reference', type=Path)
    parser.add_argument('short_reference', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    checked(args.long_reference, FIG_SHA)
    checked(args.short_reference, CINE_SHA)
    if args.output.exists():
        parser.error('Choose a fresh output directory.')
    media = args.output / 'media'
    media.mkdir(parents=True)
    with Image.open(args.long_reference) as im:
        im.thumbnail((960, 680))
        im.convert('RGB').save(media / 'acquired-long.webp', quality=94)
    with Image.open(args.short_reference) as im:
        im.seek(12)
        im.convert('RGB').save(media / 'acquired-short.webp', quality=94)
    locator = HERE.parents[1] / 'reviews/teaching-assessments/refinement-economy/views/skin-trial.webp'
    with Image.open(locator) as im:
        im.crop((196, 67, 435, 345)).save(media / 'locator.webp', quality=90)
    render(args.case, args.output)
    for filename in ('index.html', 'study.css', 'study.js'):
        shutil.copyfile(HERE / filename, args.output / filename)


if __name__ == '__main__':
    main()
