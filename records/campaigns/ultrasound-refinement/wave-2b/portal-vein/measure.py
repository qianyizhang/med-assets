"""Freeze and compare the combined s1233 portal and splenic vein in its saved sweep."""

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
CAMPAIGN = HERE.parents[1]
ORGAN = "portal_vein_and_splenic_vein"
SWEEP = Path("sweeps/portal-vein")
TARGET = SWEEP / "scenes" / f"{ORGAN}.mesh"
FINAL_TARGET = Path("sweeps/liver/scenes") / TARGET.name
PREVIOUS = {
    "sha256": "5a511af3ac51d413b92bd58c49f68cc7bfaf6c1b897468a8786b5a5c7c116c77",
    "bytes": 203720,
}
MASK_SHA = "b1437b7058628669a6bc9e3b2e142dd019f1a2eeee88307e141f8f7d37e17e60"
FRAME = 12
OFFSETS = (-1.5, 0.0, 1.5)
LIMITS = {
    "p95Mm": 1.5,
    "maxMm": 3.0,
    "volumePercent": 3.0,
    "silhouettePx": 1.0,
    "silhouetteViews": 24,
    "teachingZoomPxPerMm": 3.0,
    "triangleBand": [1500, 6000],
    "extentMm": 1.5,
}
TOPOLOGY = {
    "components": 1,
    "euler": 0,
    "openEdges": 0,
    "nonmanifoldEdges": 0,
    "misorientedSharedEdges": 0,
    "degenerateTriangles": 0,
    "intersectingNonincidentPairs": 0,
}


def load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


geometry = load_module(CAMPAIGN / "wave-1" / "measure.py")
metrics = load_module(CAMPAIGN / "wave-2a" / "spleen" / "measure.py")


def freeze(case, baseline, output):
    previous, final = baseline / "stage" / TARGET, baseline / "final"
    if any(geometry.identity(path) != PREVIOUS for path in (previous, final / FINAL_TARGET)):
        raise ValueError("The stage and compact route do not match the exact previous export")
    mask = volume(case / "segmentations" / f"{ORGAN}.nii.gz", MASK_SHA, "u1").astype(bool)
    points = np.argwhere(mask)
    minimum, maximum = points.min(axis=0), points.max(axis=0)
    lower, upper = minimum - 2, maximum + 3
    cropped = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    labels, _ = ndimage.label(cropped)
    vertices, faces, _, _ = marching_cubes(cropped, 0.5, allow_degenerate=False)
    vertices = geometry.ras(vertices.astype(float) + lower)
    if (
        geometry.dot(
            vertices[faces[:, 0]], np.cross(vertices[faces[:, 1]], vertices[faces[:, 2]])
        ).sum()
        < 0
    ):
        faces = faces[:, ::-1]
    raw = vertices[faces]
    topology = geometry.topology(vertices, faces)
    for key, expected in TOPOLOGY.items():
        if topology[key] != expected:
            raise ValueError(f"Unexpected raw half-label topology {key}: {topology[key]}")

    sweep = final / SWEEP
    saved = ("sweep.js", "media/scan-12.webp", "media/section-12.webp")
    pins = {path: geometry.identity(sweep / path) for path in saved}
    if any(
        geometry.identity(baseline / "stage" / SWEEP / path) != pin for path, pin in pins.items()
    ):
        raise ValueError("The stage and compact frame-12 inputs differ")
    pose = read_poses(sweep / "sweep.js")[FRAME]
    origin = geometry.ras(np.array(pose["contact"]))
    width, beam = (np.array(pose[key]) for key in ("width", "beam"))
    normal = geometry.unit_vector(np.cross(beam, width))
    planes = [origin + offset * normal for offset in OFFSETS]
    sections = {f"plane{i}": geometry.cut(raw, point, normal) for i, point in enumerate(planes)}

    output.mkdir(parents=True)
    reference = output / "reference.npz"
    np.savez(
        reference,
        vertices=vertices,
        faces=faces,
        affine=AFFINE,
        origin=origin,
        normal=normal,
        width=width,
        beam=beam,
        **sections,
    )
    frozen = {
        "organ": "portal-vein",
        "label": ORGAN,
        "frame": FRAME,
        "pose": pose,
        "normalRas": normal.tolist(),
        "protectedPlanes": [
            {
                "offsetMm": offset,
                "originRasMm": point.tolist(),
                "segments": len(sections[f"plane{i}"]),
            }
            for i, (offset, point) in enumerate(zip(OFFSETS, planes, strict=True))
        ],
        "reference": geometry.identity(reference),
        "source": {
            "case": "s1233",
            "ctSha256": CT_SHA,
            "maskSha256": MASK_SHA,
            "shape": list(mask.shape),
            "rasMmFromVoxel": AFFINE.tolist(),
            "workingLabelGridSpacingMm": [1.5, 1.5, 1.5],
            "maskComponents6ConnectedVoxels": np.bincount(labels.ravel())[1:].tolist(),
            "enclosedBackgroundVoxels": int((ndimage.binary_fill_holes(cropped) & ~cropped).sum()),
            "occupiedGridMin": minimum.tolist(),
            "occupiedGridMax": maximum.tolist(),
            "minDistanceToCTBoundaryVoxels": int(
                min(minimum.min(), (np.array(mask.shape) - maximum - 1).min())
            ),
            "referenceTopology": topology,
        },
        "previousSweep": PREVIOUS | {"triangles": len(geometry.mesh(previous)[1])},
        "previousStageMesh": str(TARGET),
        "previousCompactMesh": str(FINAL_TARGET),
        "savedFrameInputs": pins,
        "workedChapterBaseline": {
            path: geometry.identity(final / path)
            for path in ("cases/abdomen-survey.html", "cases/organs/playable-abdomen.js")
        },
        "limits": LIMITS,
        "topologyExpected": TOPOLOGY,
    }
    metrics.write_json(output / "reference.json", frozen)


def evaluate(reference, baseline, mesh, smooth, output):
    frozen = json.loads((HERE / "reference.json").read_text())
    previous = baseline / "stage" / TARGET
    if (
        geometry.identity(previous) != PREVIOUS
        or geometry.identity(reference) != frozen["reference"]
    ):
        raise ValueError("Previous mesh or half-label reference differs from the freeze")

    with np.load(reference, allow_pickle=False) as arrays:
        raw = arrays["vertices"][arrays["faces"]]
        vertices, faces = geometry.mesh(mesh)
        candidate_triangles = vertices[faces]
        candidate, cuts = metrics.compare(raw, (vertices, faces), arrays, geometry)
        before, previous_cuts = metrics.compare(raw, geometry.mesh(previous), arrays, geometry)
        extent_error = np.max(
            np.abs(
                np.array([vertices.min(0), vertices.max(0)])
                - np.array([raw.min((0, 1)), raw.max((0, 1))])
            )
        )
        diagnostics = []
        for index, plane in enumerate(candidate["protectedPlanes"]):
            for key, target in (("referenceToMesh", candidate_triangles), ("meshToReference", raw)):
                direction = plane[key]
                if direction["maxMm"] > LIMITS["maxMm"]:
                    point = np.array(direction["maxLocationRasMm"])
                    distance = geometry.squared_distance(
                        np.broadcast_to(point, (len(target), 3)), target
                    )
                    source_cut = (
                        arrays[f"plane{index}"]
                        if key == "referenceToMesh"
                        else cuts[f"plane{index}"]
                    )
                    diagnostics.append(
                        {
                            "planeOffsetMm": plane["offsetMm"],
                            "direction": key,
                            "locationRasMm": point.tolist(),
                            "sectionDistanceMm": direction["maxMm"],
                            "distanceTo3dSurfaceMm": float(np.sqrt(distance.min())),
                            "sourceLoopPerimeterMm": metrics.section_loop_size(
                                source_cut, point, geometry
                            ),
                        }
                    )
    topology = geometry.topology(vertices, faces)
    with np.load(smooth, allow_pickle=False) as dense:
        silhouette = metrics.wave_module("wave-1b").silhouette(
            dense["vertices"][dense["faces"]], candidate_triangles, LIMITS["teachingZoomPxPerMm"]
        )
    reference_volume = frozen["source"]["referenceTopology"]["signedVolumeMm3"]
    report = {
        "frozen": frozen,
        "export": geometry.identity(mesh) | {"triangles": len(faces)},
        "previousSweep": frozen["previousSweep"],
        "volumeDeltaPercent": (topology["signedVolumeMm3"] / reference_volume - 1) * 100,
        "candidate": candidate,
        "baseline": before,
        "silhouette": silhouette,
        "topology": topology,
        "largestRasBoundsChangeMm": float(extent_error),
        "failedCutDiagnostics": diagnostics,
    }
    failures = [
        f"{region} {key} {measure} {row[key][measure]:.3f} > {LIMITS[measure]} mm"
        for region, row in (
            ("global", candidate["global"]),
            *((f"plane {p['offsetMm']:+g} mm", p) for p in candidate["protectedPlanes"]),
        )
        for key in ("referenceToMesh", "meshToReference")
        for measure in ("p95Mm", "maxMm")
        if row[key][measure] > LIMITS[measure]
    ]
    failures.extend(
        f"{key}: {topology[key]} differs from expected {expected}"
        for key, expected in TOPOLOGY.items()
        if topology[key] != expected
    )
    for result, value, limit in (
        ("absolute volume change (%)", abs(report["volumeDeltaPercent"]), LIMITS["volumePercent"]),
        ("turning silhouette (px)", silhouette["maximumDeparturePx"], LIMITS["silhouettePx"]),
        ("RAS bounds change (mm)", extent_error, LIMITS["extentMm"]),
    ):
        if value > limit:
            failures.append(f"{result}: {value:.3f} > {limit}")
    if not LIMITS["triangleBand"][0] <= len(faces) <= LIMITS["triangleBand"][1]:
        failures.append("Triangles outside the frozen band")
    if topology["signedVolumeMm3"] <= 0:
        failures.append("Packed mesh does not have outward winding")

    output.mkdir(parents=True)
    metrics.write_json(output / "measurements.json", report | {"failures": failures})
    np.savez(
        output / "sections.npz",
        **{f"candidate_{k}": v for k, v in cuts.items()},
        **{f"previous_{k}": v for k, v in previous_cuts.items()},
    )
    for failure in failures:
        print(failure)
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, arguments in (
        ("freeze", ("case", "baseline", "output")),
        ("evaluate", ("reference", "baseline", "mesh", "smooth", "output")),
    ):
        subparser = subcommands.add_parser(command)
        for arg in arguments:
            subparser.add_argument(arg, type=Path)
    args = parser.parse_args()
    if args.command == "freeze":
        freeze(args.case, args.baseline, args.output)
        return 0
    return evaluate(args.reference, args.baseline, args.mesh, args.smooth, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
