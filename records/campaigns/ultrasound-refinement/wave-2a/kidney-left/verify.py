"""Check the reimported candidate against frozen source and previous delivery."""

import argparse
import importlib.util
import json
import struct
from hashlib import sha256
from pathlib import Path

import numpy as np

ROOT = Path.cwd()
CAMPAIGN = ROOT / "records/campaigns/ultrasound-refinement"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wave = load("wave_one", CAMPAIGN / "wave-1/measure.py")
later = load("wave_one_b", CAMPAIGN / "wave-1b/measure.py")


def measure(geometry, reference, dense, receipt, start, destination, include_silhouette):
    vertices, faces = geometry
    triangles = vertices[faces]
    structure = wave.topology(vertices, faces)
    raw_v, raw_f = reference["vertices"], reference["faces"]
    raw_triangles = raw_v[raw_f]
    origin = raw_v.mean(0)
    a, b, c = (raw_triangles - origin).transpose(1, 0, 2)
    raw_volume = float(abs(wave.dot(a, np.cross(b, c)).sum()) / 6)
    measure = dict(
        export=wave.identity(start) | dict(triangles=len(faces), vertices=len(vertices)),
        topology=structure,
        referenceVolumeMm3=raw_volume,
        volumeDeltaPercent=100 * (abs(structure["signedVolumeMm3"]) / raw_volume - 1),
        globalDistances=later.bidirectional(wave, raw_triangles, triangles),
        planes=[],
    )
    frame = receipt["savedAcquisition"]
    width, beam, normal = (np.array(frame[key]) for key in ("width", "beam", "normal"))
    arrays = {}
    for i, plane in enumerate(receipt["protectedPlanes"]):
        point = np.array(plane["originRasMm"])
        outline = wave.cut(triangles, point, normal)
        ref = reference[f"outline{i}"]
        if sha256(ref.astype("<f8").tobytes()).hexdigest() != plane["referenceOutlineSha256"]:
            raise ValueError("Frozen plane differs from its pin")
        arrays[f"outline{i}"] = outline
        relative = outline.reshape(-1, 3) - point
        lateral = wave.dot(relative, width)
        depth = wave.dot(relative, beam) + wave.LENS_RADIUS_MM
        projection = np.column_stack(
            (
                np.hypot(lateral, depth) - wave.LENS_RADIUS_MM,
                np.rad2deg(np.arctan2(lateral, depth)),
            )
        )
        sector = (
            (projection[:, 0] >= 0)
            & (projection[:, 0] <= frame["sectorDepthMm"])
            & (abs(projection[:, 1]) <= frame["sectorHalfAngleDeg"])
        )
        measure["planes"].append(
            dict(
                offsetMm=plane["offsetMm"],
                distances=later.bidirectional(wave, ref, outline),
                verticesInAcquisitionSector=int(np.count_nonzero(sector)),
                projectedVertices=len(projection),
                zSpanMm=float(np.ptp(outline[..., 2])),
            )
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(destination.with_suffix(".npz"), **arrays)
    if include_silhouette:
        dense_triangles = dense["vertices"][dense["faces"]]
        measure["turningSilhouette"] = later.silhouette(dense_triangles, triangles, 3.0)
    return measure


def violations(result, limits):
    failures = []
    export, topology = result["export"], result["topology"]
    if not limits["triangles"][0] <= export["triangles"] <= limits["triangles"][1]:
        failures.append("Triangle count outside frozen band")
    if topology["components"] != 1 or topology["euler"] != 2 or topology["signedVolumeMm3"] <= 0:
        failures.append("Candidate must use one Euler 2 outward shell")
    for key in (
        "openEdges",
        "nonmanifoldEdges",
        "misorientedSharedEdges",
        "degenerateTriangles",
        "intersectingNonincidentPairs",
    ):
        if topology[key] != 0:
            failures.append(f"{key} must be zero")
    if abs(result["volumeDeltaPercent"]) > limits["maxAbsVolumePercent"]:
        failures.append("Volume change exceeds 3%")
    for label, scores in [
        ("global", result["globalDistances"]),
        *((f"{row['offsetMm']:+g} mm plane", row["distances"]) for row in result["planes"]),
    ]:
        for direction, values in scores.items():
            if values["p95Mm"] > limits["maxP95Mm"] or values["maxMm"] > limits["maxMm"]:
                failures.append(
                    f"{label}, {direction}: p95 {values['p95Mm']:.3f} mm, max {values['maxMm']:.3f} mm"
                )
    if result["turningSilhouette"]["maximumDeparturePx"] > limits["maxTurningSilhouettePx"]:
        failures.append("Silhouette differs by more than 1 teaching pixel")
    return failures


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("organ")
parser.add_argument("candidate", type=Path)
parser.add_argument("dense", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument(
    "--distort", type=Path, help="Write and check a disposable copy displaced 6 mm superiorly"
)
parser.add_argument(
    "--prior", action="store_true", help="Measure the previous sweep for comparison"
)
args = parser.parse_args()
frozen = json.loads((CAMPAIGN / f"wave-2a/{args.organ}/frozen.json").read_text())
archive = ROOT / ".artifacts/us-wave2a" / args.organ / "reference.npz"
with np.load(archive, allow_pickle=False) as ref, np.load(args.dense, allow_pickle=False) as dense:
    surface_digest = sha256(
        ref["vertices"].astype("<f8").tobytes() + ref["faces"].astype("<u4").tobytes()
    ).hexdigest()
    if surface_digest != frozen["source"]["halfLabelSurfaceSha256"]:
        raise ValueError("Frozen half-label surface differs from its pin")
    path = args.candidate
    if args.distort:
        payload = bytearray(path.read_bytes())
        vertices, _ = struct.unpack_from("<2I", payload)
        positions = np.frombuffer(payload, "<f4", vertices * 3, 8).reshape(-1, 3)
        positions[:, 2] += 4
        with args.distort.open("xb") as stream:
            stream.write(payload)
        path = args.distort
    if args.prior and wave.identity(path)["sha256"] != frozen["priorMesh"]["sha256"]:
        raise ValueError("Previous sweep bytes differ from frozen baseline")
    geometry = wave.mesh(path)
    result = measure(geometry, ref, dense, frozen, path, args.output, not args.prior)
    if not args.prior:
        result["failures"] = violations(result, frozen["gates"])
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
if result.get("failures"):
    raise SystemExit(1)
