"""Compare delivered triangles against native and teaching atlas cuts in a common slab."""

import argparse
import json
from pathlib import Path
from struct import unpack_from

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd

from branch_geometry import separate_daughters
from build_survey import (
    TRUNK, as_kernel, closed_tube, file_identity, load_line, load_mesh, local_axes, mask_at, mesh_bytes,
)
from delivery import validate_mesh

PITCH_MM = .35
CAP_MARGIN_MM = 1.0


def packed_mesh(path):
    raw = path.read_bytes()
    validate_mesh(raw, path)
    points, faces = unpack_from('<2I', raw)
    vertices = np.frombuffer(raw, '<f4', count=points * 3, offset=8).reshape(-1, 3)
    triangles = np.frombuffer(raw, '<u4', count=faces * 3, offset=8 + points * 12).reshape(-1, 3)
    return vertices, triangles


def sampled_stacks(groups, levels, x, y):
    """Rasterize the actual delivered surfaces, independently of tracking PNGs."""
    w, b = local_axes(None, False)
    grids = {}
    for kind, meshes in groups.items():
        kernels = [as_kernel(mesh) for mesh in meshes]
        volume = []
        for height in levels:
            observed = [mask_at(mesh, [0, 0, height], w, b, x, -y[::-1])[::-1] for mesh in kernels]
            volume.append(np.logical_or.reduce(observed))
        grids[kind] = np.asarray(volume)
    return grids


def similarity(result, reference):
    common = np.count_nonzero(result & reference)
    r, t = np.count_nonzero(result), np.count_nonzero(reference)
    # Distances are measured between rasterized 3D lumen boundaries at 0.35 mm.
    surface_r = result & ~nd.binary_erosion(result)
    surface_t = reference & ~nd.binary_erosion(reference)
    distances = np.r_[nd.distance_transform_edt(~surface_t)[surface_r],
                      nd.distance_transform_edt(~surface_r)[surface_t]] * PITCH_MM
    result_area = np.count_nonzero(result, axis=(1, 2)) * PITCH_MM**2
    reference_area = np.count_nonzero(reference, axis=(1, 2)) * PITCH_MM**2
    return {
        'iou': round(common / (r + t - common), 4),
        'referenceRecall': round(common / t, 4),
        'stitchedPrecision': round(common / r, 4),
        'volumeDifferencePercent': round(100 * (r - t) / t, 2),
        'medianAxialAreaAbsoluteErrorMm2': round(float(np.median(abs(result_area-reference_area))), 2),
        'symmetricSurfaceDistanceMeanMm': round(float(distances.mean()), 3),
        'symmetricSurfaceDistanceP95Mm': round(float(np.quantile(distances, .95)), 3),
    }


def analyze_side(atlas_path, atlas, root, protocol, side):
    files = {key: atlas_path.parent / atlas['sides'][side]['arteries'][key] for key in TRUNK}
    raw = {key: closed_tube(load_mesh(path)) for key, path in files.items()}
    adjusted = raw.copy()
    lines = {key: load_line(path, key, side) for key, path in files.items()}
    fork = float(lines['cca'][-1, 2])
    correction = separate_daughters(adjusted, lines)
    if correction != protocol['authoredBranchSeparation'][side]:
        raise ValueError(f'{side}: corrected benchmark differs from delivery provenance')
    source = protocol['reconstructions'][side]
    for name, mesh in adjusted.items():
        if mesh_bytes(*mesh) != (root / source['sourcePaths'][name]).read_bytes():
            raise ValueError(f'{side} {name}: corrected benchmark differs from packed source')
    stitched = packed_mesh(root / source['reconstructionPath'])
    slab = source['metrics']['slabBoundsMm']
    cloud = np.concatenate([mesh[0] for mesh in (*raw.values(), *adjusted.values(), stitched)])
    x, y = [np.arange(a - PITCH_MM, b + PITCH_MM, PITCH_MM)
            for a, b in zip(cloud[:, :2].min(0), cloud[:, :2].max(0), strict=True)]
    levels = np.arange(slab[0] + PITCH_MM / 2, slab[1], PITCH_MM)
    groups = {'raw': list(raw.values()), 'teaching': list(adjusted.values()), 'stitch': [stitched]}
    samples = sampled_stacks(groups, levels, x, y)
    interior = (levels >= slab[0] + CAP_MARGIN_MM) & (levels <= slab[1] - CAP_MARGIN_MM)
    zone = (levels >= fork) & (levels <= correction['adjustedZRangeMm'][1])
    result = {key: {
        'fullMatchedSlab': similarity(samples['stitch'], samples[key]),
        'withoutTerminalMillimeter': similarity(samples['stitch'][interior], samples[key][interior]),
        'authoredForkZone': similarity(samples['stitch'][zone], samples[key][zone]),
        'lowerTerminalMillimeter': similarity(samples['stitch'][levels < slab[0] + CAP_MARGIN_MM],
                                              samples[key][levels < slab[0] + CAP_MARGIN_MM]),
        'upperTerminalMillimeter': similarity(samples['stitch'][levels > slab[1] - CAP_MARGIN_MM],
                                              samples[key][levels > slab[1] - CAP_MARGIN_MM]),
    } for key in ('raw', 'teaching')}
    result['rawVsTeaching'] = similarity(samples['teaching'], samples['raw'])
    result['rawVsTeachingInForkZone'] = similarity(samples['teaching'][zone], samples['raw'][zone])
    result['stitchedMeshSha256'] = file_identity(root / source['reconstructionPath'])
    result['slabBoundsMm'] = [round(z, 2) for z in slab]
    result['stitchedMeshBoundsMm'] = [round(float(z), 2) for z in
                                      (stitched[0][:, 2].min(), stitched[0][:, 2].max())]
    result['sharedForkZMm'] = round(fork, 2)
    result['nativeVesselExtentsMm'] = {key: {
        'nativeZBounds': [round(float(z), 2) for z in (mesh[0][:, 2].min(), mesh[0][:, 2].max())],
        'spanBelowAcquisition': round(max(0., slab[0] - float(mesh[0][:, 2].min())), 2),
        'spanAboveAcquisition': round(max(0., float(mesh[0][:, 2].max()) - slab[1]), 2),
    } for key, mesh in raw.items()}
    result['zones'] = {'terminalMarginMm': CAP_MARGIN_MM,
                       'authoredForkZBoundsMm': [round(fork, 2), correction['adjustedZRangeMm'][1]]}
    return result, samples, levels


def cropped_mask(mask, padding=3):
    y, x = np.nonzero(mask)
    return (slice(max(0, int(y.min())-padding), min(mask.shape[0], int(y.max())+padding+1)),
            slice(max(0, int(x.min())-padding), min(mask.shape[1], int(x.max())+padding+1)))


def overlay_panel(reference, stitched, bounds, size):
    a, b = reference[bounds], stitched[bounds]
    pixels = np.zeros((*a.shape, 3), dtype='u1')
    pixels[:] = [15, 24, 31]
    pixels[b] = [120, 177, 228]
    edge = a & ~nd.binary_erosion(a)
    pixels[edge] = [255, 187, 104]
    plot = Image.fromarray(pixels)
    scale = min(size[0] / plot.width, size[1] / plot.height)
    return plot.resize((round(plot.width*scale), round(plot.height*scale)), Image.Resampling.NEAREST)


def plate(results, visuals, path):
    canvas = Image.new('RGB', (1390, 1060), (15, 24, 31))
    draw = ImageDraw.Draw(canvas)
    large, mid, tiny = [ImageFont.load_default(size=size) for size in (31, 21, 16)]
    white, muted, orange, blue = (239, 244, 249), (184, 199, 212), (255, 187, 104), (120, 177, 228)
    draw.text((38, 27), 'Stitched carotid lumen against two atlas references', font=large, fill=white)
    draw.text((38, 72), 'Each side uses one matched acquired RAS slab. Source length beyond both scan ends is excluded.', font=mid, fill=muted)
    draw.rectangle((39, 111, 55, 122), fill=blue)
    draw.text((65, 106), 'Stitched lumen', font=tiny, fill=blue)
    draw.rectangle((351, 111, 367, 122), outline=orange, width=2)
    draw.text((377, 106), 'Reference boundary', font=tiny, fill=orange)
    for side_col, side in enumerate(('right','left')):
        metrics, masks, levels = results[side], *visuals[side]
        x0 = 36 + side_col * 684
        draw.text((x0, 158), f'{side.capitalize()} carotid', font=mid, fill=white)
        low, high = metrics['slabBoundsMm']
        draw.text((x0, 190), f'Acquired axial span {low:.1f} to {high:.1f} mm', font=tiny, fill=muted)
        projections = [{key: np.any(mask, axis=axis)[::-1] for key, mask in masks.items()}
                       for axis in (1, 2)]
        for n, (axis, name) in enumerate(((1, 'Anterior view'), (2, 'Lateral view'))):
            p = projections[n]
            crop = cropped_mask(np.logical_or.reduce(list(p.values())))
            for j, key in enumerate(('raw', 'teaching')):
                x = x0 + n * 334 + j * 162
                draw.text((x+10, 226), 'Original atlas' if key=='raw' else 'Teaching atlas', font=tiny, fill=white)
                im = overlay_panel(p[key], p['stitch'], crop, (142, 392))
                canvas.paste(im, (x+(150-im.width)//2, 253))
            draw.text((x0+n*334+94, 651), name, font=tiny, fill=muted)
        for j, axial_delta in enumerate((6., 22., high - metrics['sharedForkZMm'] - .5)):
            z = metrics['sharedForkZMm'] + axial_delta
            index = int(np.argmin(abs(levels-z)))
            native, adjusted, rec = (masks[k][index] for k in ('raw','teaching','stitch'))
            crop = cropped_mask(native | adjusted | rec)
            x = x0 + j * 224
            draw.text((x, 704), (f'{axial_delta:.0f} mm above the fork' if j < 2 else 'Upper scan limit'), font=tiny, fill=white)
            for k, image in enumerate((native, adjusted)):
                draw.text((x+4+k*104, 865), 'Original' if k == 0 else 'Teaching', font=tiny, fill=muted)
                im = overlay_panel(image, rec, crop, (94, 116))
                canvas.paste(im, (x+3+k*104+(94-im.width)//2, 745+(116-im.height)//2))
        for k, ref in enumerate(('raw', 'teaching')):
            area = metrics[ref]['fullMatchedSlab']
            fork = metrics[ref]['authoredForkZone']
            label = 'Original atlas' if ref=='raw' else 'Teaching atlas'
            draw.text((x0, 909+k*34), f'{label}  ·  3D IoU {area["iou"]:.3f}  ·  Fork IoU {fork["iou"]:.3f}'
                      f'  ·  Boundary p95 {area["symmetricSurfaceDistanceP95Mm"]:.2f} mm', font=tiny, fill=white)
    draw.text((38, 1013), 'The teaching atlas separates overlapping daughter tubes. Geometry adapted from Z-Anatomy / BodyParts3D · CC BY-SA 4.0.',
              font=tiny, fill=muted)
    canvas.save(path, format='WEBP', lossless=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('atlas', type=Path)
    parser.add_argument('delivery', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    atlas = json.loads(args.atlas.read_text())
    pins = json.loads(Path(__file__).with_name('source-manifest.json').read_text())['files']
    file_identity(args.atlas, pins['atlas.json'])
    for side in atlas['sides'].values():
        for key in TRUNK:
            vessel = args.atlas.parent / side['arteries'][key]
            file_identity(vessel, pins[vessel.name])
    protocol = json.loads((args.delivery / 'protocol-geometry.json').read_text())
    results, visuals = {}, {}
    for side in ('right','left'):
        result, masks, levels = analyze_side(args.atlas, atlas, args.delivery, protocol, side)
        results[side] = result
        visuals[side] = masks, levels
        for kind in ('raw', 'teaching'):
            full = result[kind]['fullMatchedSlab']
            fork = result[kind]['authoredForkZone']
            print(f'{side} {kind}: 3D IoU {full["iou"]:.4f}, fork IoU {fork["iou"]:.4f}, '
                  f'boundary p95 {full["symmetricSurfaceDistanceP95Mm"]:.3f} mm.', flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    out = {'method': 'Independent rasterization of packed triangles and two pinned source models; native tube end rings capped without resizing.',
           'comparisonGridPitchMm': PITCH_MM, 'sides': results}
    (args.output / 'source-vs-stitch.json').write_text(json.dumps(out, indent=2) + '\n')
    plate(results, visuals, args.output / 'source-vs-stitch.webp')


if __name__ == '__main__':
    main()
