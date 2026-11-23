"""Section the actual exports and compare against native, registration-checked labels or atlas parts."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage.measure import find_contours, marching_cubes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.glb import decode, buffer_view_bytes

SIZE = 520
SKY, GOLD, CORAL, MINT, INK = "#8eddf0", "#f1c873", "#fa9786", "#91d5b4", "#17272e"
FONT = ROOT / "sources/fonts/dejavu/DejaVuSans.ttf"
SCI = json.loads((ROOT / "assemblies/workshop-s1233/inputs.json").read_text())
SOURCE_MASKS = {
    **{k: SCI["maskSha256"][k] for k in ("heart", "aorta", "pulmonary_vein")},
    "lung_lower_lobe_left": "150432ae2eb7c7e664e8bd842190ad9a6e23253b3843ef32acec09c9a9b06c80",
    "lung_lower_lobe_right": "a0c40d35496bac945d78b1a39d1a1572568af41ae28aa23b2136d76d8454981a",
}


def load_mask(directory, key):
    file = directory / (key + ".nii.gz")
    if hashlib.sha256(file.read_bytes()).hexdigest() != SOURCE_MASKS[key]:
        raise ValueError(f"Wrong label identity for {key}")
    image = nib.load(file)
    if tuple(image.shape) != tuple(SCI["shape"]) or not np.allclose(
        image.affine, SCI["rasMmFromVoxel"], atol=1e-6, rtol=0
    ):
        raise ValueError("Label frame mismatch")
    return np.asarray(image.dataobj) != 0


def segments(mesh, axis, cut):
    tri = mesh["xyz"][mesh["triangles"]]
    tri = tri[(tri[:, :, axis].min(1) < cut) & (tri[:, :, axis].max(1) >= cut)]
    result = np.zeros((len(tri), 2, 3))
    counts = np.zeros(len(tri), dtype=int)
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = tri[:, i], tri[:, j]
        good = (a[:, axis] < cut) != (b[:, axis] < cut)
        t = (cut - a[good, axis]) / (b[good, axis] - a[good, axis])
        result[good, counts[good]] = a[good] + t[:, None] * (b[good] - a[good])
        counts[good] += 1
    if len(counts) and counts.min() != 2:
        raise ValueError("Incomplete section")
    return np.delete(result, axis, axis=2)


def panel(lines, bounds, labels, title, tissue=None):
    x0, y0, x1, y1 = bounds
    im = Image.new("RGB", (SIZE, SIZE), INK)
    d = ImageDraw.Draw(im)
    top, bottom = 44, SIZE - 36 - len(labels) * 26
    scale = min((SIZE - 36) / (x1 - x0), (bottom - top) / (y1 - y0))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    def screen(points):
        q = (np.asarray(points) - [cx, cy]) * [scale, -scale] + [
            SIZE / 2,
            (bottom + top) / 2,
        ]
        return [tuple(p) for p in q]

    if tissue is not None:
        array, axes = tissue
        xx = cx + (np.arange(SIZE) - SIZE / 2) / scale
        yy = cy - (np.arange(top, bottom) - (bottom + top) / 2) / scale
        affine = np.array(SCI["rasMmFromVoxel"])
        xi = np.rint((xx - affine[axes[0], 3]) / affine[axes[0], axes[0]]).astype(int)
        yi = np.rint((yy - affine[axes[1], 3]) / affine[axes[1], axes[1]]).astype(int)
        samples = array[
            np.clip(xi, 0, array.shape[0] - 1)[:, None],
            np.clip(yi, 0, array.shape[1] - 1),
        ].T
        mapped = np.clip(
            (samples.astype(float) + 900) * 130 / 1200 + 12, 12, 142
        ).astype("uint8")
        im.paste(Image.fromarray(mapped).convert("RGB"), (0, top))
    for paths, color, width in lines:
        for points in paths:
            d.line(screen(points), fill=color, width=width)
    d.rectangle((0, 0, SIZE, top - 1), fill=INK)
    d.rectangle((0, bottom, SIZE, SIZE), fill=INK)
    font = ImageFont.truetype(FONT, 18)
    d.text((13, 10), title, fill="white", font=font)
    for i, (caption, color) in enumerate(labels):
        y = SIZE - 28 * (len(labels) - i) - 8
        d.line((15, y + 11, 42, y + 11), fill=color, width=4)
        d.text((51, y), caption, fill="white", font=font)
    return im


def source_contours(mask, axis, index):
    affine = np.array(SCI["rasMmFromVoxel"])
    other = [i for i in range(3) if i != axis]
    return [
        (line * affine.diagonal()[other] + affine[other, 3])
        for line in find_contours(np.take(mask.astype(np.uint8), index, axis=axis), 0.5)
    ]


def register_case(key, names, masks, matched, out):
    arrs, meshes, distances = {}, {}, {}
    affine = np.array(SCI["rasMmFromVoxel"])
    for name, file in names.items():
        arr = load_mask(masks, name)
        xyz = np.argwhere(arr)
        lo, hi = xyz.min(0) - 1, xyz.max(0) + 2
        roi = arr[tuple(slice(l, h) for l, h in zip(lo, hi))]
        vertices, _, _, _ = marching_cubes(roi.astype(np.uint8), level=0.5)
        vertices = (vertices + lo) * affine.diagonal()[:3] + affine[:3, 3]
        ref = cKDTree(vertices)
        data = np.load(matched / key / file)
        world = data["xyz"] * [-1000, -1000, 1000] + [0, 155, 430]
        region = (
            world[:, 2] > np.quantile(world[:, 2], 0.75)
            if key == "heart"
            else world[:, 2] < np.quantile(world[:, 2], 0.25)
        )
        values = ref.query(world[region])[0]
        distances[name] = {
            "inputSha256": SOURCE_MASKS[name],
            "testedVertices": int(region.sum()),
            "nearestLabelIsosurfaceVertexMmMedianP95Max": np.quantile(
                values, [0.5, 0.95, 1]
            ).tolist(),
            "largestSampleRasMm": world[region][np.argmax(values)].tolist(),
        }
        arrs[name] = arr
        meshes[name] = {"xyz": world, "triangles": data["triangles"]}
    if key == "heart":
        arrs["aorta"] = load_mask(masks, "aorta")
        arrs["pulmonary_vein"] = load_mask(masks, "pulmonary_vein")
        settings = [(2, 319, (-96, 110, 64, 240)), (1, 146, (-100, 426, 64, 542))]
    else:
        settings = [(1, 119, (-103, 355, 51, 447)), (1, 108, (-28, 350, 123, 447))]
    ct_path = masks.parent / "ct.nii.gz"
    if (
        hashlib.sha256(ct_path.read_bytes()).hexdigest()
        != "5352376d8fd9c0ab582a7fca1443f28762a66b9782d59c645b976771587c0cfc"
    ):
        raise ValueError("Wrong registered CT")
    image = nib.load(ct_path)
    if not np.allclose(image.affine, affine, atol=1e-6, rtol=0) or tuple(
        image.shape
    ) != tuple(SCI["shape"]):
        raise ValueError("Wrong CT frame")
    ct = np.asarray(image.dataobj)
    for i, (axis, index, bounds) in enumerate(settings):
        cut = affine[axis, axis] * index + affine[axis, 3]
        lines = [
            (
                source_contours(arr, axis, index),
                GOLD if name in names else (CORAL if name == "aorta" else MINT),
                3,
            )
            for name, arr in arrs.items()
        ]
        for mesh in meshes.values():
            lines.append((segments(mesh, axis, cut), SKY, 1))
        labels = [("Source label", GOLD), ("Delivered surface", SKY)]
        if key == "heart":
            labels = [
                ("Heart label", GOLD),
                ("Delivered outline", SKY),
                ("Aorta label", CORAL),
                ("Pulmonary vein label", MINT),
            ]
        title = f"s1233    {'S' if axis == 2 else 'A'} = {cut:.1f} mm"
        panel(
            lines,
            bounds,
            labels,
            title,
            (np.take(ct, index, axis=axis), [n for n in range(3) if n != axis]),
        ).save(out / f"{key}-{i}.png")
    return distances


def diaphragm(atlas, out):
    full = {p.stem: np.load(p) for p in atlas.glob("*.npz")}
    spec = json.loads((HERE / "build.json").read_text())["diaphragm"]["edition"]
    doc, binary = decode((ROOT / spec["path"]).read_bytes())
    p = doc["meshes"][0]["primitives"][0]

    def array(index, dtype):
        a = doc["accessors"][index]
        return np.frombuffer(
            buffer_view_bytes(binary, doc["bufferViews"][a["bufferView"]]), dtype=dtype
        )

    positions = array(p["attributes"]["POSITION"], "<f4").reshape(-1, 3)
    # The isolated export stores world-space positions with no nonidentity node transform.
    if any(
        set(doc["nodes"][0]) & {k}
        for k in ("translation", "rotation", "scale", "matrix")
    ):
        raise ValueError("Unexpected isolated diaphragm matrix")
    vertices = positions[:, [0, 2, 1]] * [1, -1, 1]
    ids = array(p["indices"], "<u2").reshape(-1, 3)
    native = full["Diaphragm"]["xyz"]
    error = max(
        cKDTree(native).query(vertices)[0].max(),
        cKDTree(vertices).query(native)[0].max(),
    )
    if error > 0.000001:
        raise ValueError(f"Atlas registration exceeds 0.001 mm: {error}")
    full["Diaphragm"] = {"xyz": vertices, "triangles": ids}
    levels = [1.2337, 1.1177]
    colors = {"Diaphragm": SKY, "Vertebra L1": "#adc0c2", "Oesophagus": GOLD}
    receipt = {}
    for i, level in enumerate(levels):
        lines = []
        for n, mesh in full.items():
            section = segments(mesh, 2, level)
            receipt.setdefault(n, []).append(
                {"zMetres": level, "segments": len(section)}
            )
            if len(section):
                lines.append(
                    (section, colors.get(n, MINT if "vena cava" in n else CORAL), 3)
                )
        labels = (
            [
                ("Diaphragm", SKY),
                ("Caval surface", MINT),
                ("Esophagus", GOLD),
                ("Aorta", CORAL),
            ]
            if i == 0
            else [
                ("Descending diaphragm contours", SKY),
                ("L1 bone outline", "#adc0c2"),
                ("Aorta", CORAL),
                ("Caval surface", MINT),
            ]
        )
        panel(
            lines,
            (-0.13, -0.105, 0.13, 0.075) if i == 0 else (-0.052, -0.044, 0.052, 0.074),
            labels,
            f"Native axial plane    z = {level * 1000:.1f} mm",
        ).save(out / f"diaphragm-{i}.png")
    # Mask the projected shell. Compare the only enclosed gap to the named
    # caval cross-section at the dome; these are independent source objects.
    scale = 4000
    origin = np.array([-0.14, -0.113])
    projected = Image.new("1", (1120, 800))
    draw = ImageDraw.Draw(projected)
    xy = (vertices[:, :2] - origin) * scale
    for face in ids:
        draw.polygon([tuple(v) for v in xy[face]], fill=1)
    mask = np.asarray(projected)
    gaps = ndimage.binary_fill_holes(mask) & ~mask
    components, count = ndimage.label(gaps)
    substantial = [i for i in range(1, count + 1) if (components == i).sum() > 16]
    if len(substantial) != 1:
        raise ValueError("Expected a single enclosed projected dome aperture")
    gap = components == substantial[0]
    gap_outline = [
        c[:, ::-1] / scale + origin for c in find_contours(gap.astype("uint8"), 0.5)
    ]
    caval = segments(full["Inferior vena cava (thoracic part)"], 2, 1.254)
    caval_center = (caval.min(axis=(0, 1)) + caval.max(axis=(0, 1))) / 2
    ix, iy = np.rint((caval_center - origin) * scale).astype(int)
    if not gap[iy, ix]:
        raise ValueError("Cava cross-section centre misses the projected hole")
    yc, xc = np.where(gap)
    center = np.array([xc.mean(), yc.mean()]) / scale + origin
    panel(
        [(gap_outline, SKY, 3), (caval, MINT, 3)],
        (-0.038, -0.042, 0.005, 0.002),
        [
            ("Dome aperture in superior projection", SKY),
            ("Thoracic inferior vena cava at 1254 mm", MINT),
        ],
        "Source atlas   •   aperture detail",
    ).save(out / "diaphragm-0.png")
    return {
        "bidirectionalMaxNearestVertexMm": float(error * 1000),
        "levels": receipt,
        "projectedPixelMm": 1000 / scale,
        "cavalCentreInsideProjectedAperture": True,
        "cavalCentreToProjectedHoleCentroidMm": float(
            np.linalg.norm(caval_center - center) * 1000
        ),
        "apertureCentroidMm": (center * 1000).tolist(),
    }


def cut_cast_and_tissues(matched, out):
    receipt = {}
    for key, coords in (("nose_sinuses", [-0.012, 0.145]), ("lymph", [0.3281, 0.3298])):
        files = {p.stem: np.load(p) for p in (matched / key).glob("*.npz")}
        colors = {
            "Yao-medulla-of-lymph-node": SKY,
            "Yao-paracortex": "#e297b5",
            "Yao-follicles": GOLD,
            "Yao-capsule-of-lymph-node": "#c9c8bc",
        }
        receipt[key] = {}
        for i, cut in enumerate(coords):
            data = []
            for name, m in files.items():
                s = segments(m, 2, cut)
                data.append((s, colors.get(name, SKY), 2))
                receipt[key].setdefault(name, []).append(
                    {"blenderZ": cut, "segments": len(s)}
                )
            if key == "lymph":
                labels = [
                    ("Capsule", "#c9c8bc"),
                    ("Medulla", SKY),
                    ("Paracortex", "#e297b5"),
                    ("Follicles", GOLD),
                ]
                bounds = (-0.0108, -0.0788, 0.009, -0.0645)
                title = f"Source tissue surfaces    z = {cut * 1000:.1f} mm"
            else:
                labels = [("Exact cast intersection", SKY)]
                bounds = (-0.343, -0.495, 0.343, 0.495)
                title = f"Cast plane    z = {cut:+.3f} display units"
            panel(data, bounds, labels, title).save(out / f"{key}-{i}.png")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("masks", "atlas", "matched", "output"):
        parser.add_argument(name, type=Path)
    a = parser.parse_args()
    a.output.mkdir(exist_ok=False)
    bindings = json.loads((a.matched / "render.json").read_text())
    atlas = json.loads((a.atlas / "atlas.json").read_text())
    for folder, pins in [
        (a.atlas, atlas["sectionInputs"]),
        *((a.matched / key, item["sectionInputs"]) for key, item in bindings.items()),
    ]:
        observed = {
            p.name: {
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in folder.glob("*.npz")
        }
        if observed != pins:
            raise ValueError(f"Section mesh identity mismatch in {folder.name}")
    result = cut_cast_and_tissues(a.matched, a.output)
    result["heart"] = register_case(
        "heart", {"heart": "Heart-source-surface.npz"}, a.masks, a.matched, a.output
    )
    result["anatomy-workshop-r1"] = register_case(
        "anatomy-workshop-r1",
        {
            "lung_lower_lobe_left": "Lung-Lower-Lobe-Left-source-surface.npz",
            "lung_lower_lobe_right": "Lung-Lower-Lobe-Right-source-surface.npz",
        },
        a.masks,
        a.matched,
        a.output,
    )
    result["diaphragm"] = diaphragm(a.atlas, a.output)
    result["inputs"] = {
        "atlas": atlas,
        "masksSha256": SOURCE_MASKS,
        "ctSha256": "5352376d8fd9c0ab582a7fca1443f28762a66b9782d59c645b976771587c0cfc",
        "sectionsSha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(a.output.glob("*.png"))
        },
    }
    (a.output / "sections.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
