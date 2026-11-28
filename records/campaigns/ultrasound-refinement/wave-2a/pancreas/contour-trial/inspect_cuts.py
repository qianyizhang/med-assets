"""Measure nearest contour components across adjacent planes and render the case evidence."""

import argparse
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from build_study import AFFINE, volume
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from trial import HERE, REPO, closest_point, sites, source_data


def helper():
    path = HERE.parents[2] / "wave-1/measure.py"
    spec = importlib.util.spec_from_file_location("wave_geometry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cut(triangles, anchor, normal):
    signed = np.einsum("tvi,i->tv", triangles - anchor, normal)
    crossed = (signed.min(1) < 0) & (signed.max(1) >= 0)
    tri, d = triangles[crossed], signed[crossed]
    t, i = np.nonzero((d < 0) != (np.roll(d, -1, axis=1) < 0))
    j = (i + 1) % 3
    s = d[t, i] / (d[t, i] - d[t, j])
    seg = (tri[t, i] + s[:, None] * (tri[t, j] - tri[t, i])).reshape(-1, 2, 3)
    return seg[np.linalg.norm(seg[:, 1] - seg[:, 0], axis=1) > 1e-8]


def at_marker(segments, marker, geo):
    _, inverse = np.unique(segments.reshape(-1, 3).round(7), axis=0, return_inverse=True)
    edges = inverse.reshape(-1, 2)
    _, labels = geo.connectivity(edges)
    group = labels[edges[:, 0]]
    length = np.linalg.norm(segments[:, 1] - segments[:, 0], axis=1)
    lengths = np.bincount(group, weights=length)
    squared = geo.squared_distance(np.broadcast_to(marker, (len(segments), 3)), segments)
    index = squared.argmin()
    return dict(
        distanceMm=float(np.sqrt(squared[index])),
        perimeterMm=float(lengths[group[index]]),
        dominant=bool(group[index] == lengths.argmax()),
    )


def draw_plate(ct, frozen, surfaces, results, destination):
    w, h = 1140, 850
    sheet = Image.new("RGB", (w, h), "#182127")
    draw = ImageDraw.Draw(sheet)

    def label(x, y, value, size=18, ink="#f0f4f6"):
        draw.text((x, y), value, font=ImageFont.load_default(size=size), fill=ink)

    label(22, 12, "The saved cut grazes the pancreatic surface", 30)
    label(
        22,
        55,
        "s1233 · two exterior contour misses · held r01 and a source-anchored trial at the same scale",
        19,
    )
    colors = ["#ffcf70", "#52dcff", "#ec85d9"]
    for x, txt, col in zip(
        [22, 240, 480],
        ["CT label exterior", "Held r01 mesh", "Source-anchored trial"],
        colors,
        strict=True,
    ):
        draw.line((x, 95, x + 24, 95), fill=col, width=3)
        label(x + 31, 82, txt, 18)
    label(789, 82, "White cross = frozen error location", 16)
    normal = np.array(frozen["normalRas"])
    scale = 8
    patch = 172
    for k, ((offset, point), result) in enumerate(zip(sites(), results, strict=True)):
        y = 119 + k * 344
        label(22, y, f"Site {k + 1}   |   {offset:+.1f} mm from the saved plane", 23)
        label(
            560,
            y,
            f"At the marker, r01 to trial: {result['r01InPlaneMm']:.2f} to {result['trialInPlaneMm']:.2f} mm in plane",
            17,
        )
        label(
            560,
            y + 22,
            f"Nearest 3D surface: {result['r01In3DMm']:.2f} to {result['trialIn3DMm']:.2f} mm",
            16,
        )
        for j in range(6):
            axial = j < 3
            rel = (j - 1) if axial else (j - 4)
            if axial:
                n = np.array([0.0, 0.0, 1.0])
                u = np.array([1.0, 0.0, 0.0])
                v = np.array([0.0, 1.0, 0.0])
                z = int(np.rint((point[2] - AFFINE[2, 3]) / 1.5)) + rel
                marker = point.copy()
                marker[2] = AFFINE[2, 3] + 1.5 * z
                title = f"Native axial z = {z}"
            else:
                n = normal
                u = np.array(frozen["pose"]["width"])
                v = -np.array(frozen["pose"]["beam"])
                marker = point + rel * 0.75 * n
                title = f"Oblique {offset + rel * 0.75:+.2f} mm"
            x = 22 + j * 184
            image_top = y + 79
            label(x, y + 48, title, 16)
            row, col = np.mgrid[:patch, :patch]
            xyz = (
                marker
                + (col[:, :, None] - (patch - 1) / 2) * u / scale
                - (row[:, :, None] - (patch - 1) / 2) * v / scale
            )
            vox = (xyz - AFFINE[:3, 3]) / 1.5
            hu = ndimage.map_coordinates(ct, vox.transpose(2, 0, 1), order=1, mode="nearest")
            img = Image.fromarray(np.uint8(np.clip((hu + 90) * 255 / 260, 0, 255))).convert("RGB")
            pen = ImageDraw.Draw(img)
            for surf, color, stroke in zip(surfaces, colors, [3, 2, 1], strict=True):
                seg = cut(surf, marker, n) - marker
                sx = np.einsum("tvi,i->tv", seg, u) * scale + (patch - 1) / 2
                sy = -np.einsum("tvi,i->tv", seg, v) * scale + (patch - 1) / 2
                for (x0, x1), (y0, y1) in zip(sx, sy, strict=True):
                    pen.line((x0, y0, x1, y1), fill=color, width=stroke)
            mid = patch // 2
            for a, b in [(-6, -2), (2, 6)]:
                pen.line((mid + a, mid, mid + b, mid), fill="white")
                pen.line((mid, mid + a, mid, mid + b), fill="white")
            pen.line((8, patch - 10, 8 + 5 * scale, patch - 10), fill="white", width=2)
            sheet.paste(img, (x, image_top))
        label(22, y + 264, "Three neighboring native slices · 1.5 mm spacing", 17)
        label(574, y + 264, "Parallel cuts · middle panel is the failed cut", 17)
    label(
        22,
        815,
        "CT in grayscale. Each scale bar spans 5 mm. The correction fits only the exterior; internal mask gaps remain in the raw reference.",
        16,
    )
    sheet.save(destination, lossless=True, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("case", "trial_mesh", "output"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    if (
        sha256(args.trial_mesh.read_bytes()).hexdigest()
        != "16919fa7975eca4d8e3b2c0de47d30490b823810daa2b8878d6baab432bc6b96"
    ):
        raise ValueError("Expected the measured source-anchored trial")
    frozen, ref = source_data(args.case)
    geo = helper()
    r01 = REPO / "models/pancreas_s1233/exports/r01/pancreas.mesh"
    surfaces = [ref]
    for mesh in [r01, args.trial_mesh]:
        verts, faces = geo.mesh(mesh)
        surfaces.append(verts[faces])
    normal = np.array(frozen["normalRas"])
    results = []
    for offset, point in sites():
        distances_3d = [
            float(np.linalg.norm(closest_point(point, tri) - point)) for tri in surfaces[1:]
        ]
        trace = []
        for shift in np.arange(-1.5, 1.501, 0.125):
            marker = point + shift * normal
            rec = {
                s: at_marker(cut(tri, marker, normal), marker, geo)
                for s, tri in zip(("source", "r01", "trial"), surfaces, strict=True)
            }
            trace.append(dict(shiftMm=shift, **rec))
        zero = next(t for t in trace if t["shiftMm"] == 0)
        results.append(
            dict(
                planeMm=offset,
                markerRasMm=point.tolist(),
                r01In3DMm=distances_3d[0],
                trialIn3DMm=distances_3d[1],
                r01InPlaneMm=zero["r01"]["distanceMm"],
                trialInPlaneMm=zero["trial"]["distanceMm"],
                parallelCuts=trace,
            )
        )
    # Interleaved positions were not used to locate or fit the two correction sites.
    origin = np.array(frozen["protectedPlanes"][1]["originRasMm"])
    controls = []
    for offset in (-2.25, -0.75, 0.75, 2.25):
        marker = origin + offset * normal
        source_cut, r01_cut, trial_cut = [cut(tri, marker, normal) for tri in surfaces]
        row = {"offsetMm": offset}
        for name, packed in (("r01", r01_cut), ("trial", trial_cut)):
            directions = [geo.compare(source_cut, packed), geo.compare(packed, source_cut)]
            row[name] = {key: max(d[key] for d in directions) for key in ("p95Mm", "maxMm")}
        controls.append(row)
    ct = volume(args.case / "ct.nii.gz", frozen["source"]["ctSha256"], "<i2").astype(np.float32)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "trace.json").write_text(
        json.dumps({"sites": results, "interleavedExteriorChecks": controls}, indent=2) + "\n"
    )
    draw_plate(ct, frozen, surfaces, results, args.output / "adjacent-contours.webp")


if __name__ == "__main__":
    main()
