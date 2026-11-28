"""Freeze and check s1233 spleen and pancreas replay against half-label surfaces."""

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from build_study import AFFINE, CT_SHA, volume
from delivery import read_poses
from scipy import ndimage
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent
FRAME = 12
OFFSETS_MM = (-1.5, 0.0, 1.5)
ZOOM_PX_PER_MM = 3.0
P95_MM = 1.5
MAX_MM = 3.0
VOLUME_PERCENT = 3.0
SILHOUETTE_PX = 1.0
INPUTS = {
    "spleen": {
        "mask": "760eb489a2f6821ce25e7565e4d73709cab5a1ef0af6537d193b2ce036213573",
        "previous": "6c5ecf67f894ceb581bfc4a64be704cb6bd0b1c3ab8d588bbebe47e0396a99c9",
        "bytes": 346208,
        "triangles": 19232,
        "band": (2500, 5000),
    },
    "pancreas": {
        "mask": "9f11083652d059e85514d419c90124911953dbbce2018ccc549eaa2c73b0968b",
        "previous": "7ba31afffdffbed4d60c5834ab86f3eefb6f784261b519b8bb2f093103a40045",
        "bytes": 299240,
        "triangles": 16620,
        "band": (2500, 6000),
    },
}


def wave_module(wave):
    path = HERE.parents[1] / wave / "measure.py"
    spec = importlib.util.spec_from_file_location(wave + "_measure", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load the retained {wave} measurement primitives")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def mesh_path(baseline, organ):
    return baseline / "sweeps" / organ / "scenes" / f"{organ}.mesh"


def freeze(args, geometry):
    organ = args.organ
    frozen = INPUTS[organ]
    mask_file = args.case / "segmentations" / f"{organ}.nii.gz"
    mask = volume(mask_file, frozen["mask"], "u1")
    args.output.mkdir(parents=True, exist_ok=True)
    sweep = args.baseline / "sweeps" / organ
    previous = mesh_path(args.baseline, organ)
    identity = geometry.identity(previous)
    _, previous_faces = geometry.mesh(previous)
    if (
        identity != {"sha256": frozen["previous"], "bytes": frozen["bytes"]}
        or len(previous_faces) != frozen["triangles"]
    ):
        raise ValueError("Previous delivered mesh differs from the prescribed baseline")
    pose_file = sweep / "sweep.js"
    pose = read_poses(pose_file)[FRAME]
    origin = geometry.ras(np.array(pose["contact"]))
    width, beam = (np.array(pose[key]) for key in ("width", "beam"))
    normal = geometry.unit_vector(np.cross(beam, width))
    points = np.argwhere(mask)
    lo, hi = points.min(0) - 1, points.max(0) + 2
    cropped = mask[tuple(slice(a, b) for a, b in zip(lo, hi, strict=True))]
    verts, faces, _, _ = marching_cubes(cropped, 0.5, allow_degenerate=False)
    verts = geometry.ras(verts + lo)
    a, b, c = verts[faces].transpose(1, 0, 2)
    if geometry.dot(a, np.cross(b, c)).sum() < 0:
        faces = faces[:, ::-1]
    labels, _ = ndimage.label(cropped)
    sizes = np.bincount(labels.ravel())[1:]
    both = {
        "vertices": verts,
        "faces": faces,
        "affine": AFFINE,
        "origin": origin,
        "normal": normal,
        "width": width,
        "beam": beam,
    }
    planes = []
    for index, offset in enumerate(OFFSETS_MM):
        anchor = origin + offset * normal
        segments = geometry.cut(verts[faces], anchor, normal)
        both[f"plane{index}"] = segments
        planes.append(
            {"offsetMm": offset, "originRasMm": anchor.tolist(), "segments": len(segments)}
        )
    np.savez(args.output / "reference.npz", **both)
    receipt = {
        "organ": organ,
        "frame": FRAME,
        "pose": pose,
        "normalRas": normal.tolist(),
        "protectedPlanes": planes,
        "reference": geometry.identity(args.output / "reference.npz"),
        "source": {
            "case": "s1233",
            "ctSha256": CT_SHA,
            "maskSha256": frozen["mask"],
            "shape": list(mask.shape),
            "rasMmFromVoxel": AFFINE.tolist(),
            "workingLabelGridSpacingMm": [1.5, 1.5, 1.5],
            "maskComponents6ConnectedVoxels": sorted(sizes.tolist(), reverse=True),
            "enclosedBackgroundVoxels": int(
                (ndimage.binary_fill_holes(cropped) & ~cropped.astype(bool)).sum()
            ),
        },
        "previousSweep": identity | {"triangles": len(previous_faces)},
        "savedFrameInputs": {
            "sweep.js": geometry.identity(pose_file),
            **{
                f"media/{kind}-{FRAME:02}.webp": geometry.identity(
                    sweep / f"media/{kind}-{FRAME:02}.webp"
                )
                for kind in ("scan", "section")
            },
        },
        "limits": {
            "p95Mm": P95_MM,
            "maxMm": MAX_MM,
            "volumePercent": VOLUME_PERCENT,
            "silhouettePx": SILHOUETTE_PX,
            "silhouetteViews": 24,
            "teachingZoomPxPerMm": ZOOM_PX_PER_MM,
            "triangleBand": list(frozen["band"]),
        },
    }
    write_json(args.output / "reference.json", receipt)


def compare(reference, surface, arrays, geometry):
    vertices, faces = surface
    triangles = vertices[faces]
    bidirectional = {
        "referenceToMesh": geometry.compare(reference, triangles),
        "meshToReference": geometry.compare(triangles, reference),
    }
    planes = []
    cuts = {}
    for index, offset in enumerate(OFFSETS_MM):
        origin = arrays["origin"] + offset * arrays["normal"]
        cut = geometry.cut(triangles, origin, arrays["normal"])
        ct_cut = arrays[f"plane{index}"]
        cuts[f"plane{index}"] = cut
        planes.append(
            {
                "offsetMm": offset,
                "referenceToMesh": geometry.compare(ct_cut, cut),
                "meshToReference": geometry.compare(cut, ct_cut),
            }
        )
    return {"global": bidirectional, "protectedPlanes": planes}, cuts


def section_loop_size(segments, point, geometry):
    """Perimeter of the connected contour that contains the worst sampled point."""
    _, inverse = np.unique(segments.reshape(-1, 3).round(7), axis=0, return_inverse=True)
    edges = inverse.reshape(-1, 2)
    _, labels = geometry.connectivity(edges)
    group = labels[edges[:, 0]]
    distances = geometry.squared_distance(np.broadcast_to(point, (len(segments), 3)), segments)
    segment_lengths = np.linalg.norm(segments[:, 1] - segments[:, 0], axis=1)
    return float(np.bincount(group, weights=segment_lengths)[group[distances.argmin()]])


def pancreas_exterior(case, mesh_file, frozen, reference, geometry):
    """Measure the filled-label exterior as a diagnostic with the raw gate retained."""
    source = case / "segmentations/pancreas.nii.gz"
    mask = volume(source, frozen["source"]["maskSha256"], "u1").astype(bool)
    occupied = np.argwhere(mask)
    lower, upper = occupied.min(0) - 1, occupied.max(0) + 2
    cropped = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    filled = ndimage.binary_fill_holes(cropped)
    pockets, count = ndimage.label(filled & ~cropped)
    locations = []
    for label in range(1, count + 1):
        ras = geometry.ras(np.argwhere(pockets == label) + lower)
        locations.append(
            {
                "voxels": len(ras),
                "centroidRasMm": ras.mean(0).tolist(),
                "minCenterRasMm": ras.min(0).tolist(),
                "maxCenterRasMm": ras.max(0).tolist(),
            }
        )
    points, faces, _, _ = marching_cubes(filled, 0.5, allow_degenerate=False)
    vertices = geometry.ras(points + lower)
    exterior = vertices[faces]
    candidate = geometry.mesh(mesh_file)
    candidate_triangles = candidate[0][candidate[1]]
    with np.load(reference, allow_pickle=False) as arrays:
        protected = {"origin": arrays["origin"], "normal": arrays["normal"]}
        for index, offset in enumerate(OFFSETS_MM):
            origin = arrays["origin"] + offset * arrays["normal"]
            protected[f"plane{index}"] = geometry.cut(exterior, origin, arrays["normal"])
    scores, candidate_cuts = compare(exterior, candidate, protected, geometry)
    main_contours = []
    for index, row in enumerate(scores["protectedPlanes"]):
        key = f"plane{index}"
        source_cut, mesh_cut = protected[key], candidate_cuts[key]
        largest_source, _ = geometry.outer_outline(source_cut)
        largest_mesh, _ = geometry.outer_outline(mesh_cut)
        worst = row["referenceToMesh"]["maxLocationRasMm"]
        main_contours.append(
            {
                "offsetMm": row["offsetMm"],
                "filledReferenceWorstContourPerimeterMm": section_loop_size(
                    source_cut, worst, geometry
                ),
                "referenceToMesh": geometry.compare(largest_source, mesh_cut),
                "meshToReference": geometry.compare(largest_mesh, source_cut),
            }
        )
    local = {}
    for region, criteria in {
        "tailSuperiorTo370mm": lambda xyz: xyz[:, 2] >= 370,
        "neckRasXMinus8To4AndZ340To357mm": lambda xyz: (
            (xyz[:, 0] >= -8) & (xyz[:, 0] <= 4) & (xyz[:, 2] >= 340) & (xyz[:, 2] <= 357)
        ),
        "uncinateInferiorTo312mm": lambda xyz: xyz[:, 2] <= 312,
    }.items():
        local[region] = {
            "referenceToMesh": geometry.compare(
                exterior[criteria(exterior.mean(axis=1))], candidate_triangles
            ),
            "meshToReference": geometry.compare(
                candidate_triangles[criteria(candidate_triangles.mean(axis=1))], exterior
            ),
        }
    return {
        "scope": "Diagnostic half-label after filling native-mask enclosed background. Full raw gate above is unchanged.",
        "excludedEnclosedMaskPockets": locations,
        "delineation": scores,
        "dominantContourDiagnostic": main_contours,
        "localExterior": local,
    }, {f"filled_plane{i}": protected[f"plane{i}"] for i in range(len(OFFSETS_MM))}


def gate_failures(receipt):
    result = []
    for region, metrics in (
        ("global", receipt["candidate"]["global"]),
        *((f"plane {row['offsetMm']} mm", row) for row in receipt["candidate"]["protectedPlanes"]),
    ):
        for direction in ("referenceToMesh", "meshToReference"):
            for measure, limit in (("p95Mm", P95_MM), ("maxMm", MAX_MM)):
                value = metrics[direction][measure]
                if value > limit:
                    result.append(f"{region} {direction} {measure} {value:.3f} > {limit:g} mm")
    if abs(receipt["volumeDeltaPercent"]) > VOLUME_PERCENT:
        result.append("Enclosed volume differs by over 3% from the half-label surface")
    if receipt["silhouette"]["maximumDeparturePx"] > SILHOUETTE_PX:
        result.append("Turning-silhouette departure exceeds one teaching pixel")
    topology = receipt["topology"]
    for key, expected in {
        "components": 1,
        "euler": 2,
        "openEdges": 0,
        "nonmanifoldEdges": 0,
        "misorientedSharedEdges": 0,
        "degenerateTriangles": 0,
        "intersectingNonincidentPairs": 0,
    }.items():
        if topology[key] != expected:
            result.append(f"{key} {topology[key]} differs from expected {expected}")
    if topology["signedVolumeMm3"] <= 0:
        result.append("Packed mesh winding is not outward")
    lo, hi = receipt["frozen"]["limits"]["triangleBand"]
    if not lo <= receipt["export"]["triangles"] <= hi:
        result.append(f"Triangle count lies outside frozen {lo}–{hi} band")
    return result


def evaluate(args, geometry):
    frozen = json.loads((args.reference / "reference.json").read_text())
    previous = mesh_path(args.baseline, frozen["organ"])
    if geometry.identity(previous) != {k: frozen["previousSweep"][k] for k in ("sha256", "bytes")}:
        raise ValueError("Previous delivered mesh identity differs")
    reference = args.reference / "reference.npz"
    if geometry.identity(reference) != frozen["reference"]:
        raise ValueError("Half-label and section reference arrays differ from the freeze")
    with np.load(reference, allow_pickle=False) as arrays:
        ref = arrays["vertices"][arrays["faces"]]
        a, b, c = ref.transpose(1, 0, 2)
        volume = geometry.dot(a, np.cross(b, c)).sum() / 6
        vertices, faces = geometry.mesh(args.mesh)
        candidate, cuts = compare(ref, (vertices, faces), arrays, geometry)
        baseline, previous_cuts = compare(ref, geometry.mesh(previous), arrays, geometry)
    topology = geometry.topology(vertices, faces)
    with np.load(args.smooth, allow_pickle=False) as smooth:
        silhouette = wave_module("wave-1b").silhouette(
            smooth["vertices"][smooth["faces"]], vertices[faces], ZOOM_PX_PER_MM
        )
    report = {
        "frozen": frozen,
        "export": geometry.identity(args.mesh) | {"triangles": len(faces)},
        "previousSweep": frozen["previousSweep"],
        "referenceVolumeMm3": float(volume),
        "volumeDeltaPercent": float((topology["signedVolumeMm3"] / volume - 1) * 100),
        "candidate": candidate,
        "baseline": baseline,
        "silhouette": silhouette,
        "topology": topology,
    }
    failures = gate_failures(report)
    supplemental_cuts = {}
    if args.pancreas_case:
        if frozen["organ"] != "pancreas":
            raise ValueError("The filled-envelope diagnostic applies to the pancreas")
        report["pancreasExteriorDiagnostic"], supplemental_cuts = pancreas_exterior(
            args.pancreas_case, args.mesh, frozen, reference, geometry
        )
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "measurements.json", report | {"failures": failures})
    np.savez(
        args.output / "sections.npz",
        **{f"candidate_{k}": v for k, v in cuts.items()},
        **{f"previous_{k}": v for k, v in previous_cuts.items()},
        **supplemental_cuts,
    )
    for failure in failures:
        print(failure)
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    cmd_freeze = subcommands.add_parser("freeze")
    cmd_freeze.add_argument("organ", choices=INPUTS)
    for arg in ("case", "baseline", "output"):
        cmd_freeze.add_argument(arg, type=Path)
    cmd_evaluate = subcommands.add_parser("evaluate")
    for arg in ("reference", "baseline", "mesh", "smooth", "output"):
        cmd_evaluate.add_argument(arg, type=Path)
    cmd_evaluate.add_argument("--pancreas-case", type=Path)
    args = parser.parse_args()
    geometry = wave_module("wave-1")
    if args.command == "freeze":
        freeze(args, geometry)
        return 0
    return evaluate(args, geometry)


if __name__ == "__main__":
    raise SystemExit(main())
