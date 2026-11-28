"""Measure both clean-imported liver exports against the frozen s1233 half-label."""

import argparse
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from build_study import AFFINE, volume
from geometry import LENS_RADIUS_MM, SECTOR_HALF_ANGLE_DEG
from scipy import ndimage
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent


def load_helper(path):
    spec = importlib.util.spec_from_file_location(path.parent.name, path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clipped(segments, bounds, axes):
    """Restrict segments to an axis-aligned rectangular region in their plane."""
    start, stop = segments.transpose(1, 0, 2)
    delta = stop - start
    begins, ends = np.zeros(len(start)), np.ones(len(start))
    for axis, (low, high) in zip(axes, bounds, strict=True):
        offset = start[:, axis]
        direction = delta[:, axis]
        parallel = abs(direction) < 1e-10
        reciprocal = np.divide(1, direction, out=np.zeros_like(direction), where=~parallel)
        a, b = (low - offset) * reciprocal, (high - offset) * reciprocal
        begins = np.where(parallel, begins, np.maximum(begins, np.minimum(a, b)))
        ends = np.where(parallel & ((offset < low) | (offset > high)), -1, ends)
        ends = np.where(parallel, ends, np.minimum(ends, np.maximum(a, b)))
    keep = begins < ends - 1e-9
    return np.stack([start[keep] + t[keep, None] * delta[keep] for t in (begins, ends)], axis=1)


def volume_mm3(vertices, faces):
    a, b, c = (vertices[faces] - vertices.mean(axis=0)).transpose(1, 0, 2)
    return abs(float(np.einsum("ij,ij->", a, np.cross(b, c)) / 6))


def field_diagnostics(helper, triangles, pose):
    origin = helper.ras(np.array(pose["contact"]))
    width, beam = (np.array(pose[key]) for key in ("width", "beam"))
    normal = np.cross(width, beam)
    sections = {label: helper.cut(t, origin, normal) for label, t in triangles.items()}

    def crop(segments):
        midpoint = segments.mean(axis=1) - origin
        lateral = np.einsum("ij,j->i", midpoint, width)
        deep = np.einsum("ij,j->i", midpoint, beam) + LENS_RADIUS_MM
        if not np.isfinite(lateral).all() or not np.isfinite(deep).all():
            raise ValueError("Saved frame contains a non-finite section projection")
        depth = np.hypot(lateral, deep) - LENS_RADIUS_MM
        angle = abs(np.rad2deg(np.arctan2(lateral, deep)))
        return segments[(depth >= 0) & (depth <= 166) & (angle < SECTOR_HALF_ANGLE_DEG)]

    return sections, {label: crop(s) for label, s in sections.items()}


def roof_diagnostics(mask, points, faces):
    # Intersect vertical rays on integer columns in the same superior ROI used in the pretrial.
    columns = np.argwhere(np.any(mask, axis=2))
    top = mask.shape[2] - 1 - np.argmax(mask[:, :, ::-1], axis=2)
    local_range = ndimage.maximum_filter(top, 5) - ndimage.minimum_filter(top, 5)
    chosen = (top[tuple(columns.T)] >= 249) & (local_range[tuple(columns.T)] <= 5)
    roi = columns[chosen]
    vertices = (points - AFFINE[:3, 3]) / AFFINE[0, 0]
    roof = np.full(mask.shape[:2], -np.inf)
    triangles = vertices[faces]
    for a, b, c in triangles[triangles[:, :, 2].max(axis=1) >= 238]:
        low = np.ceil(np.minimum(np.minimum(a[:2], b[:2]), c[:2]) - 1e-9).astype(int)
        high = np.floor(np.maximum(np.maximum(a[:2], b[:2]), c[:2]) + 1e-9).astype(int)
        if np.any(high < low):
            continue
        xy = np.column_stack(np.mgrid[low[0] : high[0] + 1, low[1] : high[1] + 1].reshape(2, -1))
        ab, ac = b - a, c - a
        den = ab[0] * ac[1] - ac[0] * ab[1]
        if abs(den) <= 1e-10:
            continue
        rel = xy - a[:2]
        u = (ac[1] * rel[:, 0] - ac[0] * rel[:, 1]) / den
        v = (ab[0] * rel[:, 1] - ab[1] * rel[:, 0]) / den
        inside = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        idx = tuple(xy[inside].T)
        heights = a[2] + u[inside] * ab[2] + v[inside] * ac[2]
        roof[idx] = np.maximum(roof[idx], heights)
    missing = ~np.isfinite(roof)
    roof = roof[
        tuple(ndimage.distance_transform_edt(missing, return_distances=False, return_indices=True))
    ]
    error = (roof - ndimage.gaussian_filter(roof, 1.25))[tuple(roi.T)] * 1.5
    return {"columns": len(roi), "rmsMm": float(np.sqrt(np.mean(error**2)))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True, help="Retained compact study")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--dense", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Fresh scratch directory")
    args = parser.parse_args()
    freeze = json.loads((HERE / "frozen.json").read_text())
    rules = freeze["thresholds"]
    campaign = HERE.parents[1]
    geometry = load_helper(campaign / "wave-1/measure.py")
    raster = load_helper(campaign / "wave-1b/measure.py")
    for path, expected in freeze["baseline"].items():
        if geometry.identity(args.baseline / path) != expected:
            raise ValueError(f"Frozen baseline identity differs: {path}")

    source = freeze["source"]
    mask = volume(args.case / source["segmentation"], source["sha256"], "u1")
    occupied = np.argwhere(mask)
    low, high = occupied.min(axis=0) - 6, occupied.max(axis=0) + 7
    crop = mask[tuple(slice(lo, hi) for lo, hi in zip(low, high, strict=True))]
    raw_v, raw_f, _, _ = marching_cubes(
        crop.astype(np.float32), 0.5, gradient_direction="ascent", allow_degenerate=False
    )
    raw_v = geometry.ras(raw_v.astype(float) + low)
    digest = sha256(raw_v.astype("<f8").tobytes() + raw_f.astype("<u4").tobytes()).hexdigest()
    if digest != source["halfLabelSha256"]:
        raise ValueError("Frozen half-label identity differs")

    previous = args.baseline / "sweeps/liver/scenes/liver.mesh"
    decoded = {"previous": geometry.mesh(previous), "candidate": geometry.mesh(args.candidate)}
    triangles = {"reference": raw_v[raw_f]} | {label: v[f] for label, (v, f) in decoded.items()}
    topology = geometry.topology(*decoded["candidate"])
    reference_volume = volume_mm3(raw_v, raw_f)
    changes = {
        label: (volume_mm3(v, f) / reference_volume - 1) * 100 for label, (v, f) in decoded.items()
    }
    args.output.mkdir(parents=True)
    np.savez(args.output / "reference.npz", vertices=raw_v, faces=raw_f)
    with np.load(args.dense, allow_pickle=False) as raw:
        dense = raw["vertices"][raw["faces"]]
    print("Topology and volume", topology, changes, flush=True)

    def distances(regions):
        return {
            name: raster.bidirectional(geometry, regions["reference"], regions[name])
            for name in decoded
        }

    def passed(comparison):
        return all(
            values["p95Mm"] <= rules["p95Mm"] and values["maxMm"] <= rules["maxMm"]
            for values in comparison.values()
        )

    whole = distances(triangles)
    print("Global", json.dumps(whole), flush=True)
    planes = []
    contours = {}
    crop_xy = np.array(freeze["protectedPlanes"]["cleftCropVoxelXY"])
    crop_ras = crop_xy * 1.5 + AFFINE[:2, 3, None]
    for z, offset in zip(
        freeze["protectedPlanes"]["sourceVoxelZ"],
        freeze["protectedPlanes"]["offsetsMm"],
        strict=True,
    ):
        center = geometry.ras(np.array([0, 0, z]))
        cuts = {
            label: geometry.cut(t, center, np.array([0, 0, 1])) for label, t in triangles.items()
        }
        cleft = {label: clipped(segments, crop_ras, (0, 1)) for label, segments in cuts.items()}
        planes.append(
            {"zVoxel": z, "offsetMm": offset, "full": distances(cuts), "cleft": distances(cleft)}
        )
        for label, segments in cuts.items():
            contours[f"{z}-{label}"] = segments
        for label, segments in cleft.items():
            contours[f"{z}-cleft-{label}"] = segments

    unclipped, sector = field_diagnostics(geometry, triangles, freeze["acquisition"]["poseVoxel"])
    silhouette = raster.silhouette(dense, triangles["candidate"], rules["zoomPxPerMm"])
    print("Silhouette", silhouette, flush=True)
    candidate_vertices, candidate_faces = decoded["candidate"]
    gates = {
        "global": passed(whole["candidate"]),
        "protectedPlanes": all(
            passed(p[region]["candidate"]) for p in planes for region in ("full", "cleft")
        ),
        "volume": abs(changes["candidate"]) <= rules["absoluteVolumePct"],
        "topology": (
            topology["euler"] == rules["euler"]
            and topology["components"] == rules["components"]
            and topology["signedVolumeMm3"] > 0
            and len(np.unique(candidate_faces)) == len(candidate_vertices)
            and not any(
                topology[key]
                for key in (
                    "openEdges",
                    "nonmanifoldEdges",
                    "misorientedSharedEdges",
                    "degenerateTriangles",
                    "intersectingNonincidentPairs",
                )
            )
        ),
        "silhouette": (
            silhouette["views"] == rules["orthographicViews"]
            and silhouette["maximumDeparturePx"] <= rules["maxSilhouettePx"]
        ),
        "triangleBudget": rules["triangleBand"][0]
        <= len(candidate_faces)
        <= rules["triangleBand"][1],
    }
    out = {
        "export": geometry.identity(args.candidate) | {"triangles": len(candidate_faces)},
        "previousSweep": geometry.identity(previous) | {"triangles": len(decoded["previous"][1])},
        "reference": {"sha256": digest, "triangles": len(raw_f), "volumeMm3": reference_volume},
        "method": "Bidirectional samples with maximum 0.5 mm spacing to exact nearest target triangles or cut segments. Silhouette compares reimport and dense SDF precursor.",
        "global": whole,
        "topology": topology,
        "volumeChangePct": changes,
        "protectedPlanes": planes,
        "frame12Diagnostic": {
            "method": "The sector includes cut segments with midpoints inside the saved image field.",
            "unclipped": distances(unclipped),
            "sector": distances(sector),
        },
        "domeDiagnostic": {
            label: roof_diagnostics(mask, v, f) for label, (v, f) in decoded.items()
        },
        "silhouette": silhouette,
        "gates": gates,
    }
    np.savez(args.output / "contours.npz", **contours)
    (args.output / "measurements.json").write_text(json.dumps(out, indent=2) + "\n")
    print("Gates", json.dumps(gates), flush=True)
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
