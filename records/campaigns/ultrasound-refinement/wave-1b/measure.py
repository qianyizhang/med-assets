"""Measure the reimported kidney against Wave 1's frozen source and saved acquisition."""

import argparse
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from geometry import RASTER_SIZE, SECTOR_DEPTH_MM, SECTOR_HALF_ANGLE_DEG
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
TRIAL = HERE.parent / "wave-1"
REPO = HERE.parents[3]
STUDY = REPO / "experiments/ultrasound-sweep"
REVIEW = STUDY / "development/asset-reviews/kidney-wave-1b/reviews.json"
SWEEP = "sweeps/kidney-right"
MESH = f"{SWEEP}/scenes/kidney_right.mesh"
SOURCE_VOXEL_MM = 1.5
MAX_DISTANCE_MM = 3.0


def wave_one():
    spec = importlib.util.spec_from_file_location("wave_one_measure", TRIAL / "measure.py")
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load the Wave 1 measurement methods")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bidirectional(helper, reference, candidate):
    return {
        "referenceToCandidate": helper.compare(reference, candidate),
        "candidateToReference": helper.compare(candidate, reference),
    }


def check_distances(region, metrics):
    for direction, values in metrics.items():
        if not (values["p95Mm"] <= SOURCE_VOXEL_MM and values["maxMm"] <= MAX_DISTANCE_MM):
            raise ValueError(f"{region}: {direction} exceeds the CT distance limits: {values}")


def check_chord(region, reference_mm, refined_mm):
    if not abs(refined_mm - reference_mm) <= SOURCE_VOXEL_MM:
        raise ValueError(
            f"{region}: pole-to-pole chord differs from the frozen reference by "
            f"{abs(refined_mm - reference_mm):.2f} mm (limit {SOURCE_VOXEL_MM} mm)"
        )


def verify_delivery(helper, config, frozen, receipt):
    """Derive the comparison identity and bind the browser receipt to the delivered files."""
    previous = json.loads((TRIAL / "live-identity.json").read_text())["paths"]
    baseline_mesh = config.baseline_delivery / MESH
    previous_identity = helper.identity(baseline_mesh)
    if previous_identity != previous[f"/{MESH}"]:
        raise ValueError("Previous sweep mesh differs from the frozen Wave 1 identity")
    _, previous_faces = helper.mesh(baseline_mesh)
    for key, relative in (
        ("page", "tours/abdomen/abdomen-survey.html"),
        ("plate", "cases/organs/images/abd-right-kidney.svg"),
    ):
        if helper.identity(config.baseline_delivery / relative) != frozen["baseline"][key]:
            raise ValueError(f"Baseline {key} differs from the frozen Wave 1 identity")

    pose = config.study_delivery / SWEEP / "sweep.js"
    if helper.identity(pose) != frozen["poseScript"]:
        raise ValueError("Delivered sweep pose differs from the frozen Wave 1 acquisition")
    torso = config.study_delivery / SWEEP / "scenes/torso.mesh"
    contact = helper.contact_error(torso, frozen["originRasMm"], frozen["widths"]["beam"])
    if not abs(contact) <= SOURCE_VOXEL_MM:
        raise ValueError(f"Delivered first skin hit is {contact:.2f} mm from the saved contact")
    if helper.identity(torso) != frozen["source"]["context"]:
        raise ValueError("Delivered torso differs from the frozen Wave 1 context")

    export = {key: receipt["export"][key] for key in ("sha256", "bytes")}
    frame = receipt["savedChord"]["frame"]
    served = {f"/{MESH}": export}
    for kind in ("scan", "section"):
        path = f"{SWEEP}/media/{kind}-{frame:02}.webp"
        served[f"/{path}"] = previous[f"/{path}"]
    for url, expected in served.items():
        if helper.identity(config.study_delivery / url.removeprefix("/")) != expected:
            raise ValueError(f"Delivery identity mismatch for {url}")

    browser = json.loads(config.live_identity.read_text())
    if browser["served"] != served:
        raise ValueError("Browser did not serve the exact replay mesh and frozen saved scans")
    if browser["currency"] != {"current": False, "sibling": False, "placement": True}:
        raise ValueError("Browser review-currency checks did not pass")

    (consumer,) = json.loads((STUDY / "cases/organs/consumer.json").read_text())["consumers"]
    if consumer["savedChord"] != receipt["savedChord"]:
        raise ValueError("Authored saved calipers differ from the reimported pole-to-pole chord")

    receipt["previousSweep"] = previous_identity | {"triangles": len(previous_faces)}
    receipt["liveBrowser"] = served


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
            lower = np.floor(np.min([p.min(axis=(0, 1)) for p in projections], axis=0)) - 4
            upper = np.ceil(np.max([p.max(axis=(0, 1)) for p in projections], axis=0)) + 5
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
    args.add_argument("--baseline-delivery", type=Path, required=True)
    args.add_argument("--study-delivery", type=Path, required=True)
    args.add_argument("--live-identity", type=Path, required=True)
    config = args.parse_args()
    if config.output.exists():
        args.error("output must be a fresh scratch directory")
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
        region = f"Plane at {section['offsetMm']:+g} mm"
        reference_chord = float(np.linalg.norm(baseline[0] - baseline[1]))
        refined_chord = float(np.linalg.norm(refined[0] - refined[1]))
        check_chord(region, section["chordMm"], refined_chord)
        arrays[f"poles{index}"] = refined
        cap_axis = helper.unit_vector(baseline[0] - baseline[1])
        caps = [
            bidirectional(
                helper,
                *[contour[helper.dot(contour.mean(1) - pole, axis) > -5] for contour in (a, b)],
            )
            for pole, axis in zip(baseline, [cap_axis, -cap_axis], strict=True)
        ]
        distances = bidirectional(helper, a, b)
        check_distances(region, distances)
        # Apply the existing section limits to the two cap regions as a retrospective guard.
        for pole, metrics in zip(("superior cap", "inferior cap"), caps, strict=True):
            check_distances(f"{region}, {pole}", metrics)
        planes.append(
            dict(
                offsetMm=section["offsetMm"],
                distances=distances,
                capDistances=caps,
                referenceChordMm=reference_chord,
                refinedChordMm=refined_chord,
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
    saved_plane = next(i for i, plane in enumerate(planes) if plane["offsetMm"] == 0)
    endpoints = arrays[f"poles{saved_plane}"]
    depth, angle = helper.field(endpoints, center, width, beam).T
    if not np.all((depth >= 0) & (depth <= SECTOR_DEPTH_MM) & (abs(angle) < SECTOR_HALF_ANGLE_DEG)):
        raise ValueError("A refined pole leaves the saved acquisition sector")
    raster_width, raster_height = RASTER_SIZE
    pitch = max(0.41, SECTOR_DEPTH_MM / (raster_height - 21))
    xy = np.column_stack(
        (
            raster_width / 2 + helper.dot(endpoints - center, width) / pitch,
            12 + helper.dot(endpoints - center, beam) / pitch,
        )
    )
    if not np.all((xy >= 0) & (xy < RASTER_SIZE)):
        raise ValueError("A refined pole leaves the saved acquisition raster")
    axis = np.linalg.svd(raw_v - raw_v.mean(0), full_matrices=False)[2][0]
    raw_packed_bytes = 8 + 12 * (len(raw_v) + len(raw_f))
    global_distances = bidirectional(helper, reference, candidate)
    check_distances("Whole surface", global_distances)
    teaching_silhouette = silhouette(dense_v[dense_f], candidate, 3)
    volume_change = (geometry["signedVolumeMm3"] / reference_volume - 1) * 100
    if not abs(volume_change) <= 3:
        raise ValueError(f"Export volume changes by {volume_change:.2f}% (limit ±3%)")
    if not teaching_silhouette["maximumDeparturePx"] <= 1:
        raise ValueError("Export silhouette departs by more than one pixel at teaching scale")
    if not 2000 <= len(faces) <= 5000:
        raise ValueError(f"Export has {len(faces)} triangles (expected 2,000–5,000)")
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
            "frame": frozen["baseline"]["frame"],
            "millimetres": planes[saved_plane]["refinedChordMm"],
            "endpointsPx": xy.tolist(),
        },
    }
    verify_delivery(helper, config, frozen, receipt)
    payload = (json.dumps(receipt, indent=2) + "\n").encode()
    expected = json.loads(REVIEW.read_text())["measurementsSha256"]
    digest = sha256(payload).hexdigest()
    if digest != expected:
        raise ValueError(
            f"Regenerated receipt SHA-256 {digest} differs from the review pin {expected}"
        )
    config.output.mkdir(parents=True)
    np.savez(config.output / "sections.npz", **arrays)
    (config.output / "measurements.json").write_bytes(payload)
    print(f"Verified and reproduced {config.output / 'measurements.json'} ({digest})")


if __name__ == "__main__":
    main()
