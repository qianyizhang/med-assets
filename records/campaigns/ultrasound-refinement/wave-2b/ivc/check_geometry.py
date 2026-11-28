"""Freeze and verify the paired s1233 inferior vena cava exteriors."""

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from build_study import AFFINE, CT_SHA, volume
from delivery import read_poses
from geometry import LENS_RADIUS_MM, SECTOR_HALF_ANGLE_DEG
from scipy import ndimage
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parents[1]
MASK_SHA = "44504ba513ec6292a4a030c097948f546054ea36fdfbca7b6896103cf1b488e0"
BASELINE_MESH = "scenes/inferior_vena_cava.mesh"
PREVIOUS = {
    "sha256": "87f643b1f05200d4d66d469e6791b13df3f26f08a35864035f1a10f10c8ef131",
    "bytes": 314600,
    "triangles": 17476,
}
SCOPES = ("ivc", "abdominal")
FRAME = 12
OFFSETS = (-1.5, 0.0, 1.5)
CROP = (140, 271)
AXIAL_VOXELS = (142.25, 209.25, 259.25, 270.25)


def helper(wave):
    path = CAMPAIGN / wave / "measure.py"
    spec = importlib.util.spec_from_file_location(f"{wave}_measure", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load measurement primitives from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def half_label(mask, geometry):
    points = np.argwhere(mask)
    lo, hi = points.min(0) - 1, points.max(0) + 2
    crop = mask[tuple(slice(a, b) for a, b in zip(lo, hi, strict=True))]
    verts, faces, _, _ = marching_cubes(crop, 0.5, allow_degenerate=False)
    xyz = geometry.ras(verts + lo)
    if signed_volume(xyz[faces]) < 0:
        faces = faces[:, ::-1]
    labeled, nlabels = ndimage.label(crop)
    return (
        xyz,
        faces,
        {
            "occupiedBoundsVoxel": [(lo + 1).tolist(), (hi - 2).tolist()],
            "componentVoxelCounts": np.bincount(labeled.ravel(), minlength=nlabels + 1)[
                1:
            ].tolist(),
            "enclosedBackgroundVoxels": int(
                np.count_nonzero(ndimage.binary_fill_holes(crop) & ~crop)
            ),
        },
    )


def signed_volume(triangles):
    a, b, c = (triangles - triangles.mean((0, 1))).transpose(1, 0, 2)
    return float(np.einsum("ij,ij->", a, np.cross(b, c)) / 6)


def export_identity(path, geometry):
    _, faces = geometry.mesh(path)
    return geometry.identity(path) | {"triangles": len(faces)}


def freeze(case, stage, baseline, output, geometry):
    previous = stage / BASELINE_MESH
    if export_identity(previous, geometry) != PREVIOUS:
        raise ValueError("The retained IVC sweep mesh differs from the selected baseline")
    served_mesh = baseline / "sweeps/liver" / BASELINE_MESH
    if export_identity(served_mesh, geometry) != PREVIOUS:
        raise ValueError("The retained compact study's shared IVC differs from staged sweep bytes")
    sweep = baseline / "sweeps/ivc"
    mask = volume(case / "segmentations/inferior_vena_cava.nii.gz", MASK_SHA, "u1").astype(bool)
    pose = read_poses(sweep / "sweep.js")[FRAME]
    origin = geometry.ras(np.asarray(pose["contact"]))
    normal = geometry.unit_vector(np.cross(pose["beam"], pose["width"]))
    poses = [(f"long-axis {offset:+g} mm", origin + offset * normal, normal) for offset in OFFSETS]
    axial_normal = np.array([0, 0, 1])
    poses += [
        (f"axial voxel z={level:g}", geometry.ras([0, 0, level]), axial_normal)
        for level in AXIAL_VOXELS
    ]
    output.mkdir(parents=True, exist_ok=False)
    refs, inventories = {}, {}
    for scope in SCOPES:
        grid = mask
        planes = poses
        if scope == "abdominal":
            grid = mask.copy()
            grid[:, :, : CROP[0]] = False
            grid[:, :, CROP[1] :] = False
        else:
            planes = [*poses, ("axial voxel z=276.25", geometry.ras([0, 0, 276.25]), axial_normal)]
        points, faces, stats = half_label(grid, geometry)
        cuts = [geometry.cut(points[faces], center, direction) for _, center, direction in planes]
        path = output / f"{scope}.npz"
        np.savez(
            path,
            vertices=points,
            faces=faces,
            affine=AFFINE,
            **{f"plane{index}": cut for index, cut in enumerate(cuts)},
        )
        refs[scope] = geometry.identity(path)
        inventories[scope] = stats | {
            "volumeMm3": signed_volume(points[faces]),
            "planes": [
                {
                    "name": name,
                    "originRasMm": center.tolist(),
                    "normalRas": direction.tolist(),
                    "segments": len(cut),
                }
                for (name, center, direction), cut in zip(planes, cuts, strict=True)
            ],
        }
    inputs = [
        "sweep.js",
        *(f"media/{kind}-{frame:02}.webp" for frame in (FRAME, 48) for kind in ("scan", "section")),
    ]
    for item in inputs:
        if geometry.identity(stage / item) != geometry.identity(sweep / item):
            raise ValueError(f"Staged sweep does not match saved study input {item}")
    receipt = {
        "organ": "inferior_vena_cava",
        "case": "s1233",
        "sweep": "ivc",
        "frame": FRAME,
        "chapter": "abdomen-survey/ivc-long",
        "pose": pose,
        "sourceRevision": "abe213c44df8",
        "previousSweep": PREVIOUS,
        "compactMeshPath": "sweeps/liver/" + BASELINE_MESH,
        "previousChapterPage": geometry.identity(
            baseline / "tours/abdomen/abdomen-survey-sweep.html"
        ),
        "savedFrameInputs": {item: geometry.identity(sweep / item) for item in inputs},
        "sector": {
            "depthMm": 166,
            "halfAngleDeg": SECTOR_HALF_ANGLE_DEG,
            "lensRadiusMm": LENS_RADIUS_MM,
        },
        "source": {
            "ctSha256": CT_SHA,
            "maskSha256": MASK_SHA,
            "shape": list(mask.shape),
            "rasMmFromVoxel": AFFINE.tolist(),
            "workingLabelGridSpacingMm": [1.5] * 3,
            "abdominalZVoxels": list(CROP),
        },
        "rawReferences": refs,
        "rawInventories": inventories,
        "limits": {
            "p95Mm": 1.5,
            "maxMm": 3.0,
            "volumePercent": 3.0,
            "silhouettePx": 1.0,
            "silhouetteViews": 24,
            "teachingZoomPxPerMm": 3.0,
            "triangleBand": [1500, 6000],
            "sampleStepMaxMm": 0.5,
            "endpointSpanDeltaMm": 1.5,
        },
    }
    write_json(output / "reference.json", receipt)


def compare(geometry, source, target):
    return {
        "referenceToMesh": geometry.compare(source, target),
        "meshToReference": geometry.compare(target, source),
    }


def cut_to_sector(segments, frozen, geometry):
    # Midpoint classification matches the liver comparison. Full cuts govern acceptance.
    pose = frozen["pose"]
    sector = frozen["sector"]
    local = segments.mean(axis=1) - geometry.ras(pose["contact"])
    x = np.einsum("vi,i->v", local, pose["width"])
    y = np.einsum("vi,i->v", local, pose["beam"]) + sector["lensRadiusMm"]
    depth = np.hypot(x, y) - sector["lensRadiusMm"]
    angle = abs(np.degrees(np.arctan2(x, y)))
    return segments[(depth >= 0) & (depth <= sector["depthMm"]) & (angle < sector["halfAngleDeg"])]


def worst_3d(point, triangles, geometry):
    positions = np.broadcast_to(point, (len(triangles), 3))
    return float(np.sqrt(geometry.squared_distance(positions, triangles).min()))


def assess(geometry, raw, target, arrays, frozen, scope):
    result = {"global": compare(geometry, raw, target), "protectedPlanes": []}
    cuts = {}
    for index, plane in enumerate(frozen["rawInventories"][scope]["planes"]):
        name = plane["name"]
        key = f"plane{index}"
        raw_cut = arrays[key]
        cut = geometry.cut(target, plane["originRasMm"], plane["normalRas"])
        cuts[key] = cut
        metrics = compare(geometry, raw_cut, cut)
        for direction, sampled, opposite in (
            ("referenceToMesh", raw_cut, target),
            ("meshToReference", cut, raw),
        ):
            data = metrics[direction]
            point = data["maxLocationRasMm"]
            data["oppositeSurfaceDistanceMm"] = worst_3d(point, opposite, geometry)
            data["maximumLoopPerimeterMm"] = section_loop_perimeter(sampled, point, geometry)
        if index < len(OFFSETS):
            field_raw = cut_to_sector(raw_cut, frozen, geometry)
            field_cut = cut_to_sector(cut, frozen, geometry)
            metrics["sectorMidpoints"] = compare(geometry, field_raw, field_cut)
        result["protectedPlanes"].append({"name": name, **metrics})
    result["endpointDeviationMm"] = {
        "inferior": float(target[:, :, 2].min() - raw[:, :, 2].min()),
        "superior": float(target[:, :, 2].max() - raw[:, :, 2].max()),
    }
    return result, cuts


def section_loop_perimeter(segments, point, geometry):
    _, inv = np.unique(segments.reshape(-1, 3).round(7), axis=0, return_inverse=True)
    edges = inv.reshape(-1, 2)
    _, labels = geometry.connectivity(edges)
    group = labels[edges[:, 0]]
    nearest = geometry.squared_distance(
        np.broadcast_to(point, (len(segments), 3)), segments
    ).argmin()
    lengths = np.linalg.norm(segments[:, 1] - segments[:, 0], axis=1)
    return float(lengths[group == group[nearest]].sum())


def evaluate(reference, stage, candidate, output, geometry):
    receipt_path = reference / "reference.json"
    frozen = json.loads(receipt_path.read_text())
    if frozen != json.loads((HERE / "reference.json").read_text()):
        raise ValueError("Scratch freeze differs from the committed protected inputs")
    if export_identity(stage / BASELINE_MESH, geometry) != frozen["previousSweep"]:
        raise ValueError("Previous delivered IVC differs from the freeze")
    output.mkdir(parents=True, exist_ok=False)
    decision = {}
    for scope in SCOPES:
        reference_path = reference / f"{scope}.npz"
        if geometry.identity(reference_path) != frozen["rawReferences"][scope]:
            raise ValueError(f"{scope} raw half-label or frozen cuts differ")
        packed = candidate / f"{scope}.mesh"
        points, faces = geometry.mesh(packed)
        target = points[faces]
        with np.load(reference_path, allow_pickle=False) as arrays:
            raw = arrays["vertices"][arrays["faces"]]
            metrics, cuts = assess(geometry, raw, target, arrays, frozen, scope)
            if scope == "abdominal":
                previous_points, previous_faces = geometry.mesh(stage / BASELINE_MESH)
                baseline, baseline_cuts = assess(
                    geometry, raw, previous_points[previous_faces], arrays, frozen, scope
                )
                cuts.update({f"previous_{key}": value for key, value in baseline_cuts.items()})
        topology = geometry.topology(points, faces)
        with np.load(candidate / f"{scope}.npz", allow_pickle=False) as dense:
            surface = dense["vertices"][dense["faces"]]
        silhouette = helper("wave-1b").silhouette(
            surface, target, frozen["limits"]["teachingZoomPxPerMm"]
        )
        volume_delta = 100 * (topology["signedVolumeMm3"] / signed_volume(raw) - 1)
        report = {
            "export": export_identity(packed, geometry),
            "rawVolumeMm3": signed_volume(raw),
            "volumeDeltaPercent": volume_delta,
            "candidate": metrics,
            "silhouette": silhouette,
            "topology": topology,
        }
        if scope == "abdominal":
            report["baseline"] = baseline
        report["failures"] = failures(report, frozen["limits"])
        decision[scope] = report
        np.savez(output / f"{scope}-sections.npz", **cuts)
        print(f"{scope}: {report['failures'] or 'pass'}", flush=True)
    write_json(output / "measurements.json", {"frozen": frozen, "exports": decision})
    return int(any(report["failures"] for report in decision.values()))


def failures(report, limits):
    result = []
    metrics = report["candidate"]
    for row in ({"name": "global", **metrics["global"]}, *metrics["protectedPlanes"]):
        for direction in ("referenceToMesh", "meshToReference"):
            for key in ("p95Mm", "maxMm"):
                if row[direction][key] > limits[key]:
                    value = row[direction][key]
                    result.append(
                        f"{row['name']} {direction} {key}: {value:.3f} > {limits[key]} mm"
                    )
    for endpoint, delta in metrics["endpointDeviationMm"].items():
        if abs(delta) > limits["endpointSpanDeltaMm"]:
            result.append(f"{endpoint} end deviation is {delta:.3f} mm")
    if abs(report["volumeDeltaPercent"]) > limits["volumePercent"]:
        result.append("Enclosed volume differs by over 3% from the raw half-label")
    if report["silhouette"]["maximumDeparturePx"] > limits["silhouettePx"]:
        result.append("Decimation silhouette differs by over one teaching pixel")
    if report["topology"]["signedVolumeMm3"] <= 0:
        result.append("The packed mesh winding is inward")
    expected = {
        "components": 1,
        "euler": 2,
        "openEdges": 0,
        "nonmanifoldEdges": 0,
        "misorientedSharedEdges": 0,
        "degenerateTriangles": 0,
        "intersectingNonincidentPairs": 0,
    }
    for key, value in expected.items():
        if report["topology"][key] != value:
            result.append(f"{key}: {report['topology'][key]} != {value}")
    if not limits["triangleBand"][0] <= report["export"]["triangles"] <= limits["triangleBand"][1]:
        result.append("Triangle count exceeds the frozen range")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command, paths in (
        ("freeze", ("case", "stage", "baseline", "output")),
        ("evaluate", ("reference", "stage", "candidate", "output")),
    ):
        child = sub.add_parser(command)
        for path in paths:
            child.add_argument(path, type=Path)
    args = vars(parser.parse_args())
    action = args.pop("command")
    geometry = helper("wave-1")
    if action == "freeze":
        freeze(**args, geometry=geometry)
        return 0
    return evaluate(**args, geometry=geometry)


if __name__ == "__main__":
    raise SystemExit(main())
