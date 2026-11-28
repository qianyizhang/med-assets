"""Pin the prior aorta deliveries and raw half-label surface before shaping."""

import argparse
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from build_study import AFFINE, CT_SHA, SHAPE, volume
from scipy import ndimage as nd
from skimage.measure import euler_number, marching_cubes

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parents[4] / "experiments/ultrasound-sweep"
MASK_SHA = "c2751ba8bb12ed2091db7e0446f3f333acf47db5d35e8f75c96fab4c6564ab2e"
VOXEL_MM = 1.5
BOUNDS = {"aorta": None, "aorta-abdomen": (140, 271), "aorta-screening": (117, 237)}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wave = load_module("wave_one", HERE.parent.parent / "wave-1/measure.py")


def digest_arrays(vertices, faces):
    return sha256(vertices.astype("<f8").tobytes() + faces.astype("<u4").tobytes()).hexdigest()


def foreground(mask):
    _, counts = np.unique(nd.label(mask)[0], return_counts=True)
    return sorted(counts[1:].tolist(), reverse=True)


def scan_planes(stage, sweep, frames):
    poses = wave.read_poses(stage / "sweeps" / sweep / "sweep.js")
    planes = []
    for frame in frames:
        pose = poses[frame]
        anchor = wave.ras(np.array(pose["contact"]))
        width, beam = [wave.unit_vector(AFFINE[:3, :3] @ pose[key]) for key in ("width", "beam")]
        normal = wave.unit_vector(np.cross(width, beam))
        for offset in (-1.5, 0.0, 1.5):
            planes.append(
                dict(
                    frame=frame,
                    offsetMm=offset,
                    originRasMm=(anchor + offset * normal).tolist(),
                    width=width.tolist(),
                    beam=beam.tolist(),
                    normal=normal.tolist(),
                )
            )
    return planes


def axial_plane(z, name):
    return dict(
        name=name,
        originRasMm=wave.ras([0, 0, z]).tolist(),
        width=[1, 0, 0],
        beam=[0, 1, 0],
        normal=[0, 0, 1],
    )


def reference(mask, box, bounds):
    lower, upper = (v.copy() for v in box)
    if bounds:
        lower[2], upper[2] = max(lower[2], bounds[0]), min(upper[2], bounds[1])
    crop = np.pad(mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))], 1)
    vertices, faces, _, _ = marching_cubes(crop, 0.5, allow_degenerate=False)
    return wave.ras(vertices + lower - 1), faces, crop


def file_pin(root, relative):
    return dict(path=str(relative), **wave.identity(root / relative))


def freeze(case, baseline, scratch):
    source = case / "segmentations/aorta.nii.gz"
    mask = volume(source, MASK_SHA, "u1") > 0
    ct = volume(case / "ct.nii.gz", CT_SHA, "<i2")
    occupied = np.column_stack(np.nonzero(mask))
    low, high = (occupied.min(0), occupied.max(0))
    box = (np.maximum(low - 4, 0), np.minimum(high + 5, SHAPE))
    stage, final = baseline / "stage", baseline / "final"
    manifest = final / "abdomen-tours.js"
    rows, _ = json.JSONDecoder().raw_decode(manifest.read_text().split("=", 1)[1].lstrip())
    tracks = {e["id"]: e for e in rows}
    review_planes = {
        "aorta": [
            axial_plane(z, name)
            for z, name in [
                (148, "distal label end"),
                (270.26, "abdominal transition"),
                (329.26, "upper thoracic limb"),
                (342.26, "aortic arch transition"),
                (348.26, "superior label end"),
            ]
        ],
        "aorta-abdomen": scan_planes(stage, "aorta", (12,))
        + [axial_plane(148.26, "distal label end"), axial_plane(270.26, "abdominal cap rim")],
        "aorta-screening": scan_planes(stage, "aortic-screening", (12, 30, 48))
        + [axial_plane(148.26, "distal label end"), axial_plane(236.26, "screening cap rim")],
    }
    receipt = {
        "baselineRevision": "abe213c44df81a1510558b5595b2d14ffed74d78",
        "baselineAssembly": str(baseline),
        "compactIndex": file_pin(final, "abdomen-tours.js"),
        "source": dict(
            case="s1233",
            ctSha256=CT_SHA,
            mask=wave.identity(source),
            shape=list(SHAPE),
            rasMmFromVoxel=AFFINE.tolist(),
            acquisitionSliceNormalRas=[0, 0, 1],
            workingSpacingMm=[1.5] * 3,
            occupiedVoxelBounds=[low.tolist(), high.tolist()],
            license="TotalSegmentator v2.0.1, CC BY 4.0. Retain the label-source notice.",
            sourceUrl="https://zenodo.org/records/10047263",
        ),
        "tasks": {
            "aorta": "Orient the single connected source-labeled aorta from distal trunk through the arch and the two source terminations.",
            "aorta-abdomen": "Follow abdominal aortic exterior in 3D and rotate from the long-axis field to the transverse field alongside the cava. For the survey chapter aorta-long, relate the frame-12 source exemplar to the same exterior.",
            "aorta-screening": "Orient the aortic trunk anterior to the vertebrae through the proximal, mid and distal transverse stations. The saved simulated scan and mask-derived AP chord retain their own evidence.",
            "aaa-negative/mid-aorta": "Keep the separate worked model and its measured wall/lumen report. A native s1233 exterior would need a separately identified and bound exemplar.",
        },
        "anatomy": "One 6-connected solid aortic label, no separate components or enclosed voids. Distal bifurcation and adjacent branches have independent masks. Each legacy crop cuts only the superior end because the first occupied aorta voxel is z=147. Visual and protected sections distinguish the source endpoint from the artificial crop cap. Exterior orientation is the supported task.",
        "method": "Smooth one CT mask in physical signed-distance space with heavier filtering along RAS superior, taper it at the distal end and thoracic arch/end, and derive separate crop caps from that one field. Preserve raw topology and registration.",
        "gates": dict(
            p95Mm=1.5,
            maxMm=3.0,
            volumePercent=3.0,
            silhouettePx=1.0,
            silhouetteViews=24,
            teachingZoomPxPerMm=3.0,
            triangleBand=[1500, 6000],
            sampleSpacingMm=0.5,
            topology="one outward Euler-2 shell with no boundary, nonmanifold edges, degeneracy or nonincident self-intersections",
            dose="No clinical AP-caliper measurement is derived from the exterior.",
        ),
        "exports": {},
        "proceduralChapter": file_pin(final, "tours/abdomen/abdomen-survey.html"),
        "aaaChapter": {
            "page": file_pin(final, "tours/aaa/aaa-negative.html"),
            "scene": file_pin(stage, "aaa-acquisitions/aaa-negative.scene.json"),
            "modelWall": file_pin(stage, "aaa-acquisitions/assets/normal/wall.mesh"),
        },
    }
    scratch.mkdir(parents=True, exist_ok=True)
    for export, bounds in BOUNDS.items():
        vertices, faces, raw = reference(mask, box, bounds)
        triangles = vertices[faces]
        row = dict(
            cropZVoxelHalfOpen=bounds,
            halfLabelSurfaceSha256=digest_arrays(vertices, faces),
            labelEuler=int(euler_number(raw, connectivity=1)),
            componentVoxels=foreground(raw),
            enclosedVoidVoxels=foreground(nd.binary_fill_holes(raw) & ~raw),
            capZVoxel=(bounds[1] - 0.5) if bounds else None,
        )
        arrays = dict(vertices=vertices, faces=faces)
        if bounds:
            sweep = "aorta" if export == "aorta-abdomen" else "aortic-screening"
            track = tracks[sweep]
            base = Path("sweeps") / sweep
            mesh = base / "scenes/aorta.mesh"
            compact = track.get("meshPaths", {}).get("aorta", str(mesh))
            stage_pin = file_pin(stage, mesh)
            final_pin = file_pin(final, compact)
            assert stage_pin["sha256"] == final_pin["sha256"]
            pose_script = stage / base / "sweep.js"
            assert wave.identity(pose_script) == wave.identity(final / base / "sweep.js")
            row["sweep"] = sweep
            row["prior"] = dict(
                stage=stage_pin, compact=final_pin, triangles=len(wave.mesh(stage / mesh)[1])
            )
            row["savedPoseScript"] = file_pin(final, base / "sweep.js")
            row["savedFrames"] = {}
            poses = wave.read_poses(pose_script)
            for frame in [12, 48] if sweep == "aorta" else [12, 30, 48]:
                files = {}
                for kind in ("scan", "section"):
                    path = base / f"media/{kind}-{frame:02}.webp"
                    files[kind] = file_pin(final, path)
                    assert wave.identity(stage / path)["sha256"] == files[kind]["sha256"]
                row["savedFrames"][str(frame)] = {"pose": poses[frame], **files}
        for i, plane in enumerate(review_planes[export]):
            width, beam, normal, origin = (
                np.array(plane[key]) for key in ("width", "beam", "normal", "originRasMm")
            )
            cut = wave.cut(triangles, origin, normal)
            relative = cut.reshape(-1, 3) - origin
            projected = np.column_stack((wave.dot(relative, width), wave.dot(relative, beam)))
            lower = np.floor(projected.min(0)) - 5
            upper = np.ceil(projected.max(0)) + 5
            plane["outlineSha256"] = sha256(cut.astype("<f8").tobytes()).hexdigest()
            plane["bounds"] = [lower.tolist(), upper.tolist()]
            try:
                _, loops = wave.outer_outline(cut)
            except ValueError:
                loops = None
            plane["loops"] = loops
            arrays[f"outline{i}"] = cut
            lateral, depth = np.meshgrid(
                np.arange(lower[0], upper[0] + 0.5, 0.5), np.arange(lower[1], upper[1] + 0.5, 0.5)
            )
            xyz = origin + lateral[..., None] * width + depth[..., None] * beam
            indices = (xyz - AFFINE[:3, 3]) / VOXEL_MM
            arrays[f"ct{i}"] = nd.map_coordinates(ct, indices.transpose(2, 0, 1), order=1)
        row["planes"] = review_planes[export]
        receipt["exports"][export] = row
        np.savez_compressed(scratch / f"{export}-reference.npz", **arrays)
    pin = HERE / "frozen.json"
    if pin.exists():
        if json.loads(json.dumps(receipt)) != json.loads(pin.read_text()):
            raise ValueError("Frozen source, delivery or protected geometry changed")
    else:
        with pin.open("x") as file:
            file.write(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: {k: row[k] for k in ("componentVoxels", "enclosedVoidVoxels", "labelEuler")}
                for key, row in receipt["exports"].items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    freeze(args.case, args.baseline, args.scratch)
