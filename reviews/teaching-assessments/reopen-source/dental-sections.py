"""Compare exact GLB plane intersections and registered public dental source sections.

Supply the SHA-pinned FDI31 NRRD and extracted UFF members 0965–0975 alongside
one another in a scratch directory. All slice indices below follow file names
for UFF and zero-based native voxel indices for the SWIRendo label volume.
"""

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from skimage.measure import find_contours

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from glb import decode

BG = (245, 245, 239)
INK = (30, 43, 47)
COLORS = [(39, 46, 51), (225, 217, 192), (200, 161, 110), (151, 126, 115), (194, 119, 134)]


def font(size):
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except OSError:
        return ImageFont.truetype(
            ROOT / "sources/fonts/dejavu/DejaVuSans.ttf", size
        )


def title(im, xy, label, size=22):
    ImageDraw.Draw(im).text(xy, label, fill=INK, font=font(size))


def verified(path, digest):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"Unverified input {path.name}")
    return raw


def arrays(path, digest):
    doc, binary = decode(verified(path, digest))

    def read(i):
        a = doc["accessors"][i]
        view = doc["bufferViews"][a["bufferView"]]
        if view.get("byteStride"):
            raise ValueError("Unexpected interleaving")
        n = a["count"] * {"VEC3": 3, "SCALAR": 1}[a["type"]]
        return np.frombuffer(
            binary,
            {5123: "<u2", 5125: "<u4", 5126: "<f4"}[a["componentType"]],
            count=n,
            offset=view.get("byteOffset", 0) + a.get("byteOffset", 0),
        ).reshape(-1, 3)

    result = {}
    for n in doc["nodes"]:
        if "mesh" not in n:
            continue
        (p,) = doc["meshes"][n["mesh"]]["primitives"]
        result[n["name"].split("/")[-1].lower()] = (
            read(p["attributes"]["POSITION"]).astype(float) * 1000,
            read(p["indices"]),
        )
    return result


def intersections(points, faces, y):
    tri = points[faces]
    # Count each edge once at the shared vertex under a half-open convention.
    cross = (tri[:, :, 1] <= y) != (np.roll(tri[:, :, 1], -1, axis=1) <= y)
    idx, corner = np.where(cross)
    a, b = tri[idx, corner], tri[idx, (corner + 1) % 3]
    p = a + (b - a) * ((y - a[:, 1]) / (b[:, 1] - a[:, 1]))[:, None]
    return p[:, [0, 2]].reshape(-1, 2, 2)


def sample(lines, pitch=0.5):
    # Distances measured in native-index units. Half a voxel between probes.
    return np.concatenate(
        [np.linspace(a, b, max(2, int(np.ceil(np.linalg.norm(b - a) / pitch)) + 1)) for a, b in lines]
    )


def fdi(inputs, out):
    control = "models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb"
    fine = "reviews/swirendo_fdi31/2026-10-27-interface-locked/media/A_1_31_T2_SEG_na__layered.glb"
    paths = [control, fine]
    digests = [
        "90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7",
        "c0884a6bcc8fc6175dd97a99f50e53334024b4eb5e033063c7602358f6da1014",
    ]
    models = [arrays(ROOT / p, h) for p, h in zip(paths, digests, strict=True)]
    source_hash = "f4eda9fe91b60d78ece366d6f32532862775a1725c664067da5a20aae3c142fe"
    raw = verified(inputs / "fdi31.nrrd", source_hash).split(b"\n\n", 1)[1]
    volume = np.frombuffer(gzip.decompress(raw), np.uint8).reshape(679, 500, 500)
    ys = [176, 195, 214]
    plate = Image.new("RGB", (1144, 930), BG)
    title(plate, (18, 12), "Prepared FDI31  |  Bone edge and root seat", 32)
    title(
        plate,
        (18, 55),
        "Same 40 µm T2 label grid. Cyan lines trace actual GLB intersections in the source plane.",
        19,
    )
    title(
        plate,
        (18, 82),
        "Left: source segmentation     Center: Balanced     Right: interface-locked detail",
        19,
    )
    measurements = {}
    pal = np.array(COLORS, dtype=np.uint8)
    for i, y in enumerate(ys):
        s = volume[:, y, :]
        # Three matched scale/crop transverse-to-Y views show the high-index truncated margin.
        roi = (48, 375, 342, 679)
        images = [
            Image.fromarray(pal[s]).resize((1000, 1358), Image.Resampling.NEAREST) for _ in range(3)
        ]
        row = {}
        for j, ms in enumerate(models):
            matches = [name for name in ms if name.endswith("bone")]
            if len(matches) != 1:
                raise ValueError(f"Need one bone layer: {list(ms)}")
            v, f = ms[matches[0]]
            lines = intersections(v, f, y * 0.04) / 0.04
            draw = ImageDraw.Draw(images[j + 1])
            for a, b in lines:
                draw.line([tuple((a + 0.5) * 2), tuple((b + 0.5) * 2)], fill=(82, 245, 247), width=1)
            # Include the label's contact with the cropped acquisition edge.
            contours = find_contours(np.pad((s == 3).astype(float), 1), 0.5)
            true = np.concatenate([a[:, ::-1] - 1 for a in contours])
            approx = sample(lines)
            distances = [cKDTree(true).query(approx)[0] * 0.04, cKDTree(approx).query(true)[0] * 0.04]
            row[paths[j]] = {
                "boneSourceGridP95Mm": [float(np.percentile(x, 95)) for x in distances],
                "boneSourceGridMaxMm": [float(x.max()) for x in distances],
                "boneSegments": len(lines),
            }
        measurements[str(y)] = row
        title(plate, (20, 121 + 253 * i), f"y = {y}    ({y * 0.04:.2f} mm)", 18)
        for j, im in enumerate(images):
            # Keep the source square pixel aspect ratio.
            cut = im.crop(tuple(v * 2 for v in roi)).resize((220, 228), Image.Resampling.LANCZOS)
            plate.paste(cut, (70 + j * 374, 146 + i * 253))
    title(
        plate,
        (18, 891),
        "Bone touches the acquisition limit. Local chipped contours and islands occur in the source labels.",
        18,
    )
    plate.save(out / "fdi31.webp", quality=92)
    return dict(
        sourceSha256=source_hash,
        paths=paths,
        sha256=digests,
        sourceSpacingMm=0.04,
        sectionYIndex=ys,
        comparison="Sampled 2D distances in both directions. The full-field maximum uses the padded raster's artificial closing line at z=678.5. Interior witnesses and nearest 3D distances are recorded in fdi-bone-trial.json.",
        sections=measurements,
    )


def uff(inputs, out):
    catalogue = ROOT / "sources/datasets/uff-ds-uct-002/selected-members.csv"
    index = {Path(row["member"]).name: row for row in csv.DictReader(catalogue.open())}
    roi = (slice(360, 688), slice(308, 664))
    plate = Image.new("RGB", (1024, 750), BG)
    title(plate, (20, 12), "UFF Tomo1B  |  What happens when the channel opens?", 32)
    title(
        plate,
        (20, 60),
        "Source slices at 20.002 µm. Same crop, intensity and source coordinates in each column.",
        19,
    )
    shown = (969, 970, 971, 972)
    results = {}
    for i in range(965, 976):
        filename = f"{i:04}.tiff"
        row = index[filename]
        verified(inputs / filename, row["sha256"])
        a = np.asarray(Image.open(inputs / filename))[roi]
        hard = a > 80
        lbl, _ = ndi.label(hard)
        hard = lbl == (np.bincount(lbl.ravel())[1:].argmax() + 1)
        closed = ndi.binary_fill_holes(hard) & ~hard
        # Fixed seed from the centroid of the last enclosed space (member 0970).
        background, _ = ndi.label(~hard)
        seed = (146, 229)
        value = background[seed]
        if value == 0:
            raise ValueError("Source seed has entered the mineralized boundary")
        flood = background == value
        fill = closed & flood
        border = bool(flood[0].any() or flood[-1].any() or flood[:, 0].any() or flood[:, -1].any())
        results[str(i)] = dict(
            sourceMemberSha256=row["sha256"],
            selectedByEnclosure=int(fill.sum()),
            seededConnectedPixels=int(flood.sum()),
            touchesRoiBorder=border,
        )
        if i not in shown:
            continue
        x = 20 + shown.index(i) * 250
        title(plate, (x, 101), f"{i:04}", 20)
        for j, mask in enumerate([fill, flood]):
            crop = np.repeat(a[..., None], 3, axis=2)
            color = np.array([62, 193, 197] if j == 0 else [219, 135, 67])
            crop[mask] = np.round(0.52 * crop[mask] + 0.48 * color)
            picture = Image.fromarray(crop[108:180, 193:265]).resize(
                (232, 232), Image.Resampling.NEAREST
            )
            plate.paste(picture, (x, 136 + j * 274))
            title(plate, (x, 373 + j * 274), str(int(mask.sum())) + " ROI pixels", 17)
    title(
        plate,
        (20, 683),
        "Top: per-plane enclosure at the seed. Bottom: connected dark region at the same fixed seed.",
        18,
    )
    title(
        plate,
        (20, 711),
        "At 0971 the seeded region reaches the ROI border. The apparent 3D cap marks the extraction rule.",
        18,
    )
    plate.save(out / "uff.webp", quality=92)
    return dict(
        seedSourceRowColumn=[506, 537],
        threshold=80,
        sourceRoiOriginRowColumn=[360, 308],
        roiShape=[328, 356],
        sections=results,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    results = {"uff": uff(args.inputs, args.output), "fdi31": fdi(args.inputs, args.output)}
    (args.output / "dental-sections.json").write_text(json.dumps(results, indent=2) + "\n")
