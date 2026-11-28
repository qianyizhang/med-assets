"""Freeze and verify both s1127 thyroid lobes and their common isthmus."""

import argparse
import importlib.util
import json
import struct
from pathlib import Path

import numpy as np
from build_study import volume
from build_thyroid import AFFINE, CT_SHA, LOBE_DIVIDER_X, PINS, SHAPE
from delivery import read_poses, validate_mesh
from scipy import ndimage
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent
PRIMITIVES = HERE.parents[1] / "wave-1/measure.py"
_SPEC = importlib.util.spec_from_file_location("thyroid_geometry", PRIMITIVES)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Cannot load {PRIMITIVES}")
geometry = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(geometry)

LABEL = "thyroid_gland"
SIDES = ("right", "left")
FRAMES = (12, 48)
OFFSETS = (-1.5, 0.0, 1.5)
ISTHMUS_OFFSETS = (-3.0, -1.5, 0.0, 1.5, 3.0)
PREVIOUS = {
    "sha256": "73207b41254e7baff0bfaee4c0d65e0cb1533832b0dd476921994d13d7d89f25",
    "bytes": 112496,
    "triangles": 6248,
}
LIMITS = {
    "p95Mm": 1.5,
    "maxMm": 3.0,
    "volumePercent": 3.0,
    "silhouettePx": 1.0,
    "turningViews": 24,
    "teachingZoomPxPerMm": 3.0,
    "triangleBand": [1500, 6500],
    "boundsMm": 1.5,
}
TOPOLOGY = {
    "openEdges": 0,
    "nonmanifoldEdges": 0,
    "misorientedSharedEdges": 0,
    "degenerateTriangles": 0,
    "intersectingNonincidentPairs": 0,
}


def ras(points):
    return np.einsum("...j,ij->...i", points, AFFINE[:3, :3]) + AFFINE[:3, 3]


def mesh(path):
    data = path.read_bytes()
    validate_mesh(data, path)
    vertex_count, triangle_count = struct.unpack_from("<2I", data)
    points = np.frombuffer(data, "<f4", vertex_count * 3, 8).reshape(-1, 3)
    faces = np.frombuffer(data, "<u4", triangle_count * 3, 8 + 12 * vertex_count).reshape(-1, 3)
    return ras(points), faces


def write_json(path, payload):
    with path.open("x") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")


def previous_path(baseline, side):
    return baseline / "stage" / f"sweeps/thyroid-{side}/scenes/{LABEL}.mesh"


def check_previous(baseline):
    for path in (
        *(previous_path(baseline, side) for side in SIDES),
        baseline / "final" / f"sweeps/thyroid-right/scenes/{LABEL}.mesh",
    ):
        if geometry.identity(path) | {"triangles": len(mesh(path)[1])} != PREVIOUS:
            raise ValueError(f"Previous export changed: {path}")
    return previous_path(baseline, "right")


def freeze(case, baseline, output):
    check_previous(baseline)
    mask = volume(case / "segmentations" / f"{LABEL}.nii.gz", PINS[LABEL], "u1", SHAPE, AFFINE)
    occupied = np.argwhere(mask)
    minimum, maximum = occupied.min(0), occupied.max(0)
    lower, upper = minimum - 2, maximum + 3
    crop = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    labels, _ = ndimage.label(crop)
    vertices, faces, _, _ = marching_cubes(crop, 0.5, allow_degenerate=False)
    points = ras(vertices + lower)
    a, b, c = points[faces].transpose(1, 0, 2)
    if geometry.dot(a, np.cross(b, c)).sum() < 0:
        faces = faces[:, ::-1]
    raw = points[faces]
    topology = geometry.topology(points, faces)
    planes = []
    arrays = {"vertices": points, "faces": faces, "affine": AFFINE}

    def pin_cut(name, origin, normal, **meta):
        cut = geometry.cut(raw, origin, normal)
        if not len(cut):
            raise ValueError(f"The protected cut is empty: {name}")
        arrays[name] = cut
        planes.append(
            {
                "name": name,
                "originRasMm": origin.tolist(),
                "normal": normal.tolist(),
                "segments": len(cut),
                **meta,
            }
        )

    pins = {}
    for side in SIDES:
        route = f"thyroid-{side}"
        directories = [baseline / name / "sweeps" / route for name in ("stage", "final")]
        pose_file = directories[1] / "sweep.js"
        poses = read_poses(pose_file)
        frame_files = [
            f"media/{kind}-{frame:02}.webp"
            for frame in (0, *FRAMES)
            for kind in ("scan", "section")
        ]
        saved = {
            path: geometry.identity(directories[1] / path) for path in ("sweep.js", *frame_files)
        }
        if any(pin != geometry.identity(directories[0] / path) for path, pin in saved.items()):
            raise ValueError(f"The stage and compact saved files differ: {route}")
        pins[side] = {"files": saved, "poses": {frame: poses[frame] for frame in (0, *FRAMES)}}
        for frame in FRAMES:
            pose = poses[frame]
            origin = ras(np.array(pose["contact"]))
            width, beam = [np.array(pose[axis]) for axis in ("width", "beam")]
            normal = geometry.unit_vector(np.cross(beam, width))
            for index, offset in enumerate(OFFSETS):
                pin_cut(
                    f"{side}_{frame}_{index}",
                    origin + offset * normal,
                    normal,
                    side=side,
                    frame=frame,
                    offsetMm=offset,
                    width=width.tolist(),
                    beam=beam.tolist(),
                )

    # Sweep entry shows the isthmus transversely. The sagittal series tests the
    # tissue bridge separately at its divider and two neighboring slices each side.
    entry_pose = pins["right"]["poses"][0]
    entry_origin = ras(np.array(entry_pose["contact"]))
    width, beam = [np.array(entry_pose[axis]) for axis in ("width", "beam")]
    pin_cut(
        "entry",
        entry_origin,
        geometry.unit_vector(np.cross(beam, width)),
        frame=0,
        width=width.tolist(),
        beam=beam.tolist(),
    )
    x0 = float(ras(np.array([LOBE_DIVIDER_X, 0, 0]))[0])
    for i, offset in enumerate(ISTHMUS_OFFSETS):
        pin_cut(
            f"isthmus_{i}",
            np.array([x0 + offset, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0]),
            offsetMm=offset,
        )

    output.mkdir(parents=True)
    reference = output / "reference.npz"
    np.savez(reference, **arrays)
    frozen = {
        "source": {
            "case": "s1127",
            "maskSha256": PINS[LABEL],
            "ctSha256": CT_SHA,
            "shape": list(SHAPE),
            "rasMmFromVoxel": AFFINE.tolist(),
            "voxelSpacingMm": [1.5, 1.5, 1.5],
            "minDistanceToCTBoundaryVoxels": int(
                min(minimum.min(), (np.array(SHAPE) - maximum - 1).min())
            ),
            "connectedComponentsVoxels": np.bincount(labels.ravel())[1:].tolist(),
            "enclosedBackgroundVoxels": int(
                (ndimage.binary_fill_holes(crop) & ~crop.astype(bool)).sum()
            ),
            "referenceTopology": topology,
        },
        "reference": geometry.identity(reference),
        "previousSweep": PREVIOUS,
        "savedFrameInputs": pins,
        "workedChapterBaseline": {
            "file": "cases/thyroid-normal.html",
            "identity": geometry.identity(baseline / "final/cases/thyroid-normal.html"),
            "rightChapter": "thyroid-right-long",
            "leftChapter": "thyroid-left-long",
            "evidenceFrame": 12,
        },
        "protectedPlanes": planes,
        "limits": LIMITS,
        "topologyExpected": TOPOLOGY | {k: topology[k] for k in ("components", "euler")},
    }
    write_json(output / "reference.json", frozen)


def compare(source, target):
    return {
        "referenceToMesh": geometry.compare(source, target),
        "meshToReference": geometry.compare(target, source),
    }


def evaluate(reference, baseline, candidate, output, dense, previous_revision=None):
    frozen = json.loads((HERE / "reference.json").read_text())
    previous = check_previous(baseline)
    if previous_revision is not None:
        repo = HERE.parents[4]
        record = json.loads((repo / "models/thyroid_s1127/asset.record.json").read_bytes())
        revision, = (r for r in record["revisions"] if r["revisionId"] == previous_revision)
        export, = revision["exports"]
        previous = repo / export["path"]
        if geometry.identity(previous) != {key: export[key] for key in ("sha256", "bytes")}:
            raise ValueError("Previous thyroid export differs from its registration")
    if geometry.identity(reference) != frozen["reference"]:
        raise ValueError("Frozen half-label array identity changed")
    vertices, faces = mesh(candidate)
    trials = vertices[faces]
    before_vertices, before_faces = mesh(previous)
    before = before_vertices[before_faces]
    v1 = geometry.topology(vertices, faces)
    previous_same = geometry.identity(candidate) == geometry.identity(previous)
    failures = []
    diagnostics = []
    with np.load(reference, allow_pickle=False) as arrays:
        raw = arrays["vertices"][arrays["faces"]]
        global_result = compare(raw, trials)
        before_result = global_result if previous_same else compare(raw, before)
        cuts = {}
        protected = []
        for spec in frozen["protectedPlanes"]:
            name = spec["name"]
            origin, normal = np.array(spec["originRasMm"]), np.array(spec["normal"])
            source_cut = arrays[name]
            trial_cut = geometry.cut(trials, origin, normal)
            previous_cut = trial_cut if previous_same else geometry.cut(before, origin, normal)
            if not len(trial_cut):
                failures.append(f"{name}: candidate cut missing")
                continue
            result = compare(source_cut, trial_cut)
            baseline_cut = result if previous_same else compare(source_cut, previous_cut)
            for key, target in (("referenceToMesh", trials), ("meshToReference", raw)):
                point = np.array(result[key]["maxLocationRasMm"])
                if result[key]["maxMm"] > LIMITS["maxMm"]:
                    distances = geometry.squared_distance(
                        np.broadcast_to(point, (len(target), 3)), target
                    )
                    diagnostics.append(
                        {
                            "name": name,
                            "direction": key,
                            "locationRasMm": point.tolist(),
                            "sectionMm": result[key]["maxMm"],
                            "distanceTo3dSurfaceMm": float(np.sqrt(distances.min())),
                        }
                    )
            protected.append({"name": name, "candidate": result, "baseline": baseline_cut})
            cuts[f"{name}_candidate"] = trial_cut
            cuts[f"{name}_previous"] = previous_cut
        bounds_delta = float(
            np.maximum(
                np.abs(vertices.min(0) - raw.min((0, 1))), np.abs(vertices.max(0) - raw.max((0, 1)))
            ).max()
        )
    volume_delta = (
        v1["signedVolumeMm3"] / frozen["source"]["referenceTopology"]["signedVolumeMm3"] - 1
    ) * 100
    silhouette = {
        "views": 24,
        "pixelsPerMm": LIMITS["teachingZoomPxPerMm"],
        "maximumDeparturePx": 0.0,
    }
    if not previous_same:
        # In a byte-equivalent admission the masks are exactly identical in all views.
        if dense is None:
            raise ValueError(
                "A shaped candidate needs its dense surface for the turning silhouettes"
            )
        path = HERE.parents[1] / "wave-1b/measure.py"
        spec = importlib.util.spec_from_file_location("thyroid_silhouette", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with np.load(dense, allow_pickle=False) as surface:
            shaped = surface["vertices"][surface["faces"]]
        silhouette = module.silhouette(shaped, trials, LIMITS["teachingZoomPxPerMm"])

    for name, metrics in (
        ("global", global_result),
        *((r["name"], r["candidate"]) for r in protected),
    ):
        for direction, values in metrics.items():
            for key in ("p95Mm", "maxMm"):
                if values[key] > LIMITS[key]:
                    failures.append(
                        f"{name} {direction} {key}: {values[key]:.3f} > {LIMITS[key]} mm"
                    )
    for key, expected in frozen["topologyExpected"].items():
        if v1[key] != expected:
            failures.append(f"{key}: {v1[key]} differs from expected {expected}")
    for name, value, limit in (
        ("absolute volume change (%)", abs(volume_delta), LIMITS["volumePercent"]),
        ("turning silhouette (px)", silhouette["maximumDeparturePx"], LIMITS["silhouettePx"]),
        ("RAS bounds change (mm)", bounds_delta, LIMITS["boundsMm"]),
    ):
        if value > limit:
            failures.append(f"{name}: {value:.3f} > {limit}")
    if not LIMITS["triangleBand"][0] <= len(faces) <= LIMITS["triangleBand"][1]:
        failures.append("Triangles outside the frozen unchanged-admission band")
    if v1["signedVolumeMm3"] <= 0:
        failures.append("Packed mesh winding is not outward")
    output.mkdir(parents=True)
    write_json(
        output / "measurements.json",
        {
            "frozen": frozen,
            "export": geometry.identity(candidate) | {"triangles": len(faces)},
            "previousSweep": geometry.identity(previous) | {"triangles": len(before_faces)},
            "candidateGlobal": global_result,
            "baselineGlobal": before_result,
            "protectedPlanes": protected,
            "topology": v1,
            "volumeDeltaPercent": volume_delta,
            "silhouette": silhouette,
            "largestRasBoundsChangeMm": bounds_delta,
            "cutDiagnostics": diagnostics,
            "failures": failures,
        },
    )
    np.savez(output / "sections.npz", **cuts)
    for failure in failures:
        print(failure)
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, fields in (
        ("freeze", ("case", "baseline", "output")),
        ("evaluate", ("reference", "baseline", "mesh", "output")),
    ):
        command = commands.add_parser(name)
        for field in fields:
            command.add_argument(field, type=Path)
        if name == "evaluate":
            command.add_argument("--dense", type=Path)
            command.add_argument("--previous-revision", help="Registered thyroid export to use as the comparison control")
    args = parser.parse_args()
    if args.command == "freeze":
        freeze(args.case, args.baseline, args.output)
        return 0
    return evaluate(args.reference, args.baseline, args.mesh, args.output, args.dense, args.previous_revision)


if __name__ == "__main__":
    raise SystemExit(main())
