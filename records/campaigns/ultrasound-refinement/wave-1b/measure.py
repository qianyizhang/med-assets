"""Measure the reimported kidney against Wave 1's frozen source and saved acquisition."""

import argparse
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
TRIAL = HERE.parent / "wave-1"


def wave_one():
    spec = importlib.util.spec_from_file_location("wave_one_measure", TRIAL / "measure.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bidirectional(helper, reference, candidate):
    return {
        "referenceToCandidate": helper.compare(reference, candidate),
        "candidateToReference": helper.compare(candidate, reference),
    }


def silhouette(dense, candidate, zoom):
    """Compare full projected masks in 24 orthographic views at teaching scale."""
    supersample = 4
    spacing = zoom * supersample
    departures = []
    for angle in np.linspace(0, 2 * np.pi, 12, endpoint=False):
        side = np.array([-np.sin(angle), np.cos(angle), 0])
        for elevation in (0, np.pi / 6):
            up = np.array(
                [
                    -np.cos(angle) * np.sin(elevation),
                    -np.sin(angle) * np.sin(elevation),
                    np.cos(elevation),
                ]
            )
            basis = np.array([side, up])
            projections = [
                np.einsum("tvi,ji->tvj", triangles, basis) * spacing
                for triangles in (dense, candidate)
            ]
            lower = np.floor(projections[0].min(axis=(0, 1))) - 4
            upper = np.ceil(projections[0].max(axis=(0, 1))) + 5
            outlines = []
            for projection in projections:
                raster = Image.new("1", tuple((upper - lower).astype(int)))
                draw = ImageDraw.Draw(raster)
                for triangle in np.rint(projection - lower).astype(int).tolist():
                    draw.polygon([tuple(point) for point in triangle], fill=1)
                mask = np.asarray(raster)
                outlines.append(np.argwhere(mask & ~ndimage.binary_erosion(mask)))
            a, b = outlines
            departures.append(max(cKDTree(a).query(b)[0].max(), cKDTree(b).query(a)[0].max()))
    return dict(
        views=len(departures),
        pixelsPerMm=zoom,
        supersample=supersample,
        maximumDeparturePx=float(max(departures) / supersample),
    )


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("reference_npz", type=Path)
    args.add_argument("replay", type=Path)
    args.add_argument("output", type=Path)
    config = args.parse_args()
    helper = wave_one()
    frozen = json.loads((TRIAL / "reference.json").read_text())
    with np.load(config.reference_npz, allow_pickle=False) as raw:
        raw_v, raw_f = raw["vertices"], raw["faces"]
    raw_identity = sha256(raw_v.astype("<f8").tobytes() + raw_f.astype("<u4").tobytes()).hexdigest()
    if raw_identity != frozen["referenceSurfaceSha256"]:
        raise ValueError("Frozen S1233 CT half-label surface differs from its pin")
    with np.load(config.replay / "smooth.npz", allow_pickle=False) as pre:
        dense_v, dense_f = pre["vertices"], pre["faces"]
    path = config.replay / "kidney-right.mesh"
    vertices, faces = helper.mesh(path)
    reference, candidate = raw_v[raw_f], vertices[faces]
    geometry = helper.topology(vertices, faces)
    if (
        geometry["euler"] != 2
        or geometry["components"] != 1
        or geometry["signedVolumeMm3"] <= 0
        or any(
            geometry[key]
            for key in (
                "openEdges",
                "nonmanifoldEdges",
                "misorientedSharedEdges",
                "degenerateTriangles",
                "intersectingNonincidentPairs",
            )
        )
        or len(np.unique(faces)) != len(vertices)
    ):
        raise ValueError("Export must be a single, closed, outward-oriented shell")
    reference_volume = abs(
        np.einsum("ij,ij->", reference[:, 0], np.cross(reference[:, 1], reference[:, 2])) / 6
    )
    normal = np.array(frozen["normal"])
    width, beam = (np.array(frozen["widths"][key]) for key in ("lateral", "beam"))
    center = np.array(frozen["originRasMm"])
    planes = []
    arrays = {}
    for index, section in enumerate(frozen["planeSections"]):
        origin = np.array(section["originRasMm"])
        a, b = [helper.cut(tris, origin, normal) for tris in (reference, candidate)]
        arrays[f"section{index}"] = b
        baseline, refined = [helper.poles(helper.outer_outline(contour)[0]) for contour in (a, b)]
        arrays[f"poles{index}"] = refined
        cap_axis = helper.unit_vector(baseline[0] - baseline[1])
        caps = [
            bidirectional(
                helper,
                *[contour[helper.dot(contour.mean(1) - pole, axis) > -5] for contour in (a, b)],
            )
            for pole, axis in zip(baseline, [cap_axis, -cap_axis], strict=True)
        ]
        planes.append(
            dict(
                offsetMm=section["offsetMm"],
                distances=bidirectional(helper, a, b),
                capDistances=caps,
                referenceChordMm=float(np.linalg.norm(baseline[0] - baseline[1])),
                refinedChordMm=float(np.linalg.norm(refined[0] - refined[1])),
                outsideChordMm=helper.chord_outside_outline(b, refined, normal),
            )
        )
    lateral = []
    for offset in (-15, -12, -9, -6, -3, 0, 3, 6, 9, 12, 15):
        try:
            outline, components = helper.outer_outline(
                helper.cut(reference, center + offset * normal, normal)
            )
        except (IndexError, ValueError):
            continue
        endpoints = helper.poles(outline)
        lateral.append(
            dict(
                offsetMm=offset,
                contours=int(components),
                chordMm=float(np.linalg.norm(endpoints[0] - endpoints[1])),
                outsideMm=helper.chord_outside_outline(outline, endpoints, normal),
            )
        )
    endpoints = arrays["poles1"]
    pitch = 0.41  # Kidney-right 133 mm convex sector at 500 × 350 px.
    xy = np.column_stack(
        (
            250 + helper.dot(endpoints - center, width) / pitch,
            12 + helper.dot(endpoints - center, beam) / pitch,
        )
    )
    axis = np.linalg.svd(raw_v - raw_v.mean(0), full_matrices=False)[2][0]
    raw_packed_bytes = 8 + 12 * (len(raw_v) + len(raw_f))
    global_distances = bidirectional(helper, reference, candidate)
    teaching_silhouette = silhouette(dense_v[dense_f], candidate, 3)
    volume_change = (geometry["signedVolumeMm3"] / reference_volume - 1) * 100
    for metrics in [global_distances, *(p["distances"] for p in planes)]:
        if any(m["p95Mm"] > 1.5 or m["maxMm"] > 3 for m in metrics.values()):
            raise ValueError(f"Surface exceeds the CT distance limits: {metrics}")
    if (
        abs(volume_change) > 3
        or teaching_silhouette["maximumDeparturePx"] > 1
        or not 2000 <= len(faces) <= 5000
    ):
        raise ValueError("Export exceeds the volume, silhouette or triangle budget")
    receipt = {
        "export": helper.identity(path) | {"triangles": len(faces)},
        "raw": {
            "triangles": len(raw_f),
            "packedBytes": raw_packed_bytes,
            "volumeMm3": reference_volume,
        },
        "smoothTriangles": len(dense_f),
        "topology": geometry,
        "volumeChangePct": volume_change,
        "principalSpanMm": {
            "reference": float(np.ptp(helper.dot(raw_v, axis))),
            "refined": float(np.ptp(helper.dot(vertices, axis))),
        },
        "global": global_distances,
        "planes": planes,
        "lateralReferenceSections": lateral,
        "silhouette": teaching_silhouette,
        "savedChord": {
            "frame": 12,
            "millimetres": planes[1]["refinedChordMm"],
            "endpointsPx": xy.tolist(),
        },
    }
    config.output.mkdir(parents=True, exist_ok=True)
    (config.output / "measurements.json").write_text(json.dumps(receipt, indent=2) + "\n")
    np.savez(config.output / "sections.npz", **arrays)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
