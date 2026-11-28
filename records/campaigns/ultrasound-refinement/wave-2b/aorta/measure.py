"""Gate each packed aorta export against its frozen raw half-label."""

import argparse
import json
import struct
from hashlib import sha256
from pathlib import Path

import numpy as np
from freeze import HERE, digest_arrays, load_module, wave

later = load_module("wave_one_b", HERE.parent.parent / "wave-1b/measure.py")
ERROR_KEYS = (
    "openEdges",
    "nonmanifoldEdges",
    "misorientedSharedEdges",
    "degenerateTriangles",
    "intersectingNonincidentPairs",
)


def mesh_in_ras(path, affine):
    """Decode the packed renderer format and place it on the recorded native grid."""
    raw = path.read_bytes()
    wave.validate_mesh(raw, path)
    vertices, triangles = struct.unpack_from("<2I", raw)
    points = np.frombuffer(raw, "<f4", vertices * 3, 8).reshape(-1, 3).astype(float)
    faces = np.frombuffer(raw, "<u4", triangles * 3, 8 + vertices * 12).reshape(-1, 3)
    return np.einsum("...j,ij->...i", points, affine[:3, :3]) + affine[:3, 3], faces


def distances(reference, candidate):
    if not len(reference) or not len(candidate):
        return {}
    return later.bidirectional(wave, reference, candidate)


def distance_errors(result, limits):
    return not result or any(
        v["maxMm"] > limits["maxMm"] or v["p95Mm"] > limits["p95Mm"] for v in result.values()
    )


def point_surface_distance(point, triangles):
    point = np.broadcast_to(point, (len(triangles), 3))
    return float(np.sqrt(wave.squared_distance(point, triangles).min()))


def loop_count(outline):
    if not len(outline):
        return 0
    try:
        return int(wave.outer_outline(outline)[1])
    except ValueError:
        return None


def section(row, reference, raw_triangles, candidate, limits):
    origin, normal = (np.asarray(row[key]) for key in ("originRasMm", "normal"))
    contour = wave.cut(candidate, origin, normal)
    result = dict(
        distances=distances(reference, contour),
        referenceLoops=row["loops"],
        exportedLoops=loop_count(contour),
    )
    if distance_errors(result["distances"], limits):
        diagnostics = {}
        if len(contour) and len(reference):
            for direction, target in zip(
                result["distances"], (candidate, raw_triangles), strict=True
            ):
                point = result["distances"][direction]["maxLocationRasMm"]
                diagnostics[direction] = point_surface_distance(point, target)
        neighbors = []
        for offset in (-3, -1.5, -0.75, 0.75, 1.5, 3):
            cuts = [
                wave.cut(surface, origin + offset * normal, normal)
                for surface in (raw_triangles, candidate)
            ]
            neighbors.append(
                dict(
                    offsetMm=offset,
                    referenceLoops=loop_count(cuts[0]),
                    candidateLoops=loop_count(cuts[1]),
                    distances=distances(*cuts),
                )
            )
        result["diagnostics"] = dict(
            distanceTo3dSurfaceAtWorstSectionPointMm=diagnostics, parallelCuts=neighbors
        )
    return contour, result


def measurement(frozen, name, reference, path, dense, output, prior):
    limits = frozen["gates"]
    use = frozen["exports"][name]
    affine = np.asarray(frozen["source"]["rasMmFromVoxel"])
    failures = []
    v, f = mesh_in_ras(path, affine)
    export = v[f]
    raw_v, raw_f = reference["vertices"], reference["faces"]
    if digest_arrays(raw_v, raw_f) != use["halfLabelSurfaceSha256"]:
        raise ValueError("Frozen raw mesh identity mismatch")
    raw_triangles = raw_v[raw_f]
    topology = wave.topology(v, f)
    a, b, c = (raw_triangles - raw_v.mean(0)).transpose(1, 0, 2)
    raw_volume = float(abs(wave.dot(a, np.cross(b, c)).sum()) / 6)
    volume = 100 * (abs(topology["signedVolumeMm3"]) / raw_volume - 1)
    global_distances = distances(raw_triangles, export)
    if distance_errors(global_distances, limits):
        failures.append("Global raw half-label distance exceeds limits")
    sections, outlines = [], {}
    for i, row in enumerate(use["planes"]):
        raw_contour = reference[f"outline{i}"]
        if sha256(raw_contour.astype("<f8").tobytes()).hexdigest() != row["outlineSha256"]:
            raise ValueError("Frozen raw outline identity mismatch")
        outline, result = section(row, raw_contour, raw_triangles, export, limits)
        outlines[f"outline{i}"] = outline
        label = row.get("name", f"Frame {row.get('frame')} offset {row.get('offsetMm', 0):+g} mm")
        if distance_errors(result["distances"], limits):
            failures.append(f"{label} contour distance exceeds limits")
        sections.append({"plane": label, **result})
    result = dict(
        export=wave.identity(path) | dict(triangles=len(f), vertices=len(v)),
        topology=topology,
        referenceVolumeMm3=raw_volume,
        volumeDeltaPercent=volume,
        globalDistances=global_distances,
        protectedPlanes=sections,
    )
    result["protectedEmptyPlanes"] = []
    for plane in use.get("expectedEmptyPlanes", []):
        origin, normal = (np.asarray(plane[key]) for key in ("originRasMm", "normal"))
        segments = len(wave.cut(export, origin, normal))
        result["protectedEmptyPlanes"].append(dict(plane=plane["name"], segments=segments))
        if segments:
            failures.append(f"{plane['name']}: expected no geometry")
    if not prior:
        expected_low, expected_high = limits["triangleBand"]
        if not expected_low <= len(f) <= expected_high:
            failures.append("Triangle count outside frozen band")
        if (
            topology["components"] != 1
            or topology["euler"] != 2
            or topology["signedVolumeMm3"] <= 0
        ):
            failures.append("Expected one closed Euler-2 outward shell")
        if any(topology[key] for key in ERROR_KEYS):
            failures.append(
                "Found open, nonmanifold, inconsistent, degenerate or intersecting faces"
            )
        if abs(volume) > limits["volumePercent"]:
            failures.append("Absolute volume change exceeds limit")
        silhouette = later.silhouette(
            dense["vertices"][dense["faces"]], export, limits["teachingZoomPxPerMm"]
        )
        result["turningSilhouette"] = silhouette
        if silhouette["maximumDeparturePx"] > limits["silhouettePx"]:
            failures.append("Turning silhouette exceeds limit")
        if use["capZVoxel"] is not None:
            cap_z = use["capZVoxel"] * affine[2, 2] + affine[2, 3]
            result["upperCapDeltaMm"] = float(v[:, 2].max() - cap_z)
            if abs(result["upperCapDeltaMm"]) > limits["maxMm"]:
                failures.append("Route cap departs from its frozen raw crop")
        if use.get("lowerCapZVoxel") is not None:
            cap_z = use["lowerCapZVoxel"] * affine[2, 2] + affine[2, 3]
            result["lowerCapDeltaMm"] = float(v[:, 2].min() - cap_z)
            if abs(result["lowerCapDeltaMm"]) > limits["maxMm"]:
                failures.append("Lower route cap departs from its frozen raw crop")
        result["failures"] = failures
    np.savez_compressed(output.with_suffix(".npz"), **outlines)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        name,
        "prior" if prior else "candidate",
        global_distances,
        [
            (row["plane"], max((d["maxMm"] for d in row["distances"].values()), default=None))
            for row in sections
        ],
        result.get("turningSilhouette"),
        result.get("failures"),
    )
    return bool(result.get("failures"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export")
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("dense", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prior", action="store_true")
    parser.add_argument("--frozen", type=Path, default=HERE / "frozen.json")
    parser.add_argument("--distort", type=Path, help="Write and check a 6 mm leftward shift")
    args = parser.parse_args()
    frozen = json.loads(args.frozen.read_text())
    path = args.candidate
    if args.prior and (
        wave.identity(path)["sha256"] != frozen["exports"][args.export]["prior"]["stage"]["sha256"]
    ):
        raise ValueError("Incorrect prior mesh bytes")
    if args.distort:
        payload = bytearray(path.read_bytes())
        vertices, _ = struct.unpack_from("<2I", payload)
        coordinates = np.frombuffer(payload, "<f4", vertices * 3, 8).reshape(-1, 3)
        coordinates[:, 0] += 4
        with args.distort.open("xb") as stream:
            stream.write(payload)
        path = args.distort
    with (
        np.load(args.reference, allow_pickle=False) as raw,
        np.load(args.dense, allow_pickle=False) as dense,
    ):
        return measurement(frozen, args.export, raw, path, dense, args.output, args.prior)


if __name__ == "__main__":
    raise SystemExit(main())
