"""Freeze either s1127 carotid side's exact prior display, CT and target planes."""

import argparse
import importlib.util
import json
import struct
from hashlib import sha256
from pathlib import Path

import numpy as np
from build_study import volume
from build_thyroid import AFFINE, CT_SHA, PINS, SHAPE
from delivery import read_poses
from scipy import ndimage as nd
from skimage.measure import euler_number, marching_cubes

HERE = Path(__file__).resolve().parent
VOXEL_MM = 1.5
CROPS = {"native": (344, 409), "carotid": (371, 407)}
GATES = dict(
    p95Mm=1.5,
    maxMm=3.0,
    volumePercent=3.0,
    silhouettePx=1.0,
    silhouetteViews=24,
    teachingZoomPxPerMm=3.0,
    triangleBand=[1500, 6000],
    sampleSpacingMm=0.5,
    topology="One outward Euler-2 solid shell with two scan-cut closures; no introduced gaps, winding errors or intersections.",
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wave = load_module("wave_one", HERE.parent.parent / "wave-1/measure.py")


def ras(voxel):
    return np.einsum("...j,ij->...i", np.asarray(voxel), AFFINE[:3, :3]) + AFFINE[:3, 3]


def file_pin(root, relative):
    return {"path": str(relative), **wave.identity(root / relative)}


def axial(z, name):
    return dict(
        name=name,
        originRasMm=ras([0, 0, z]).tolist(),
        width=[1, 0, 0],
        beam=[0, 1, 0],
        normal=[0, 0, 1],
    )


def pose_planes(poses):
    planes = []
    for index in (12, 48):
        pose = poses[index]
        anchor = ras(pose["contact"])
        width, beam = [wave.unit_vector(AFFINE[:3, :3] @ pose[key]) for key in ("width", "beam")]
        normal = wave.unit_vector(np.cross(width, beam))
        for offset in (-1.5, 0.0, 1.5):
            planes.append(
                dict(
                    frame=index,
                    offsetMm=offset,
                    originRasMm=(anchor + offset * normal).tolist(),
                    width=width.tolist(),
                    beam=beam.tolist(),
                    normal=normal.tolist(),
                )
            )
    return planes


def reference(mask, occupied, crop):
    lower = np.maximum(occupied.min(0) - 2, 0)
    upper = np.minimum(occupied.max(0) + 3, mask.shape)
    lower[2], upper[2] = max(lower[2], crop[0]), min(upper[2], crop[1])
    source = np.pad(mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))], 1)
    vertices, faces, _, _ = marching_cubes(source, 0.5, allow_degenerate=False)
    return ras(vertices + lower - 1), faces, source


def bind_planes(vertices, faces, planes, ct, arrays):
    for i, plane in enumerate(planes):
        width, beam, normal, origin = (
            np.array(plane[key]) for key in ("width", "beam", "normal", "originRasMm")
        )
        cut = wave.cut(vertices[faces], origin, normal)
        if not len(cut):
            raise ValueError(f"Protected source plane is empty: {plane}")
        rel = cut.reshape(-1, 3) - origin
        projected = np.column_stack((wave.dot(rel, width), wave.dot(rel, beam)))
        lower, upper = np.floor(projected.min(0)) - 5, np.ceil(projected.max(0)) + 5
        plane["outlineSha256"] = sha256(cut.astype("<f8").tobytes()).hexdigest()
        plane["bounds"] = [lower.tolist(), upper.tolist()]
        plane["loops"] = int(wave.outer_outline(cut)[1])
        arrays[f"outline{i}"] = cut
        u, v = np.meshgrid(
            np.arange(lower[0], upper[0] + 0.25, 0.25), np.arange(lower[1], upper[1] + 0.25, 0.25)
        )
        xyz = origin + u[..., None] * width + v[..., None] * beam
        ijk = (xyz - AFFINE[:3, 3]) / VOXEL_MM
        arrays[f"ct{i}"] = nd.map_coordinates(ct, ijk.transpose(2, 0, 1), order=1, mode="nearest")


def freeze(side, case, baseline, packet, scratch):
    part = "common_carotid_artery_" + side
    route = "carotid-" + side
    source = case / f"segmentations/{part}.nii.gz"
    mask = volume(source, PINS[part], "u1", SHAPE, AFFINE) > 0
    ct = volume(case / "ct.nii.gz", CT_SHA, "<i2", SHAPE, AFFINE)
    occupied = np.column_stack(np.nonzero(mask))
    stage, final = baseline / "stage", baseline / "final"
    tracks, _ = json.JSONDecoder().raw_decode(
        (final / "abdomen-tours.js").read_text().split("=", 1)[1].lstrip()
    )
    tracks = {e["id"]: e for e in tracks}
    scratch.mkdir(parents=True, exist_ok=True)
    packet.mkdir(parents=True, exist_ok=True)
    receipt = dict(
        baselineRevision="abe213c44df81a1510558b5595b2d14ffed74d78",
        baselineAssembly=str(baseline),
        compactIndex=file_pin(final, "abdomen-tours.js"),
        scope=f"Orient the {side} common carotid exterior in 3D and relate it to the transverse and longitudinal s1127 acquisitions.",
        chapter=dict(
            case="carotid-normal",
            chapter=f"{side}-cca-gray",
            workedFrame=14,
            companionFrame=48,
            page=file_pin(final, "tours/carotid/carotid-normal.html"),
        ),
        source=dict(
            case="s1127",
            ctSha256=CT_SHA,
            mask=wave.identity(source),
            shape=list(SHAPE),
            rasMmFromVoxel=AFFINE.tolist(),
            acquisitionSliceNormalRas=[0, 0, 1],
            workingSpacingMm=[VOXEL_MM] * 3,
            occupiedVoxelBounds=[occupied.min(0).tolist(), occupied.max(0).tolist()],
            label=part,
            license="TotalSegmentator v2.0.1, CC BY 4.0. Retain label-source notice.",
        ),
        gates=GATES,
        exports={},
    )
    for kind, crop in CROPS.items():
        export = route if kind == "carotid" else f"{route}-full"
        use = route if kind == "carotid" else "thyroid-right"
        directory = Path("sweeps") / use
        pose_script = directory / "sweep.js"
        stage_prior = directory / f"scenes/{part}.mesh"
        mesh_path = tracks[use].get("meshPaths", {}).get(part, str(stage_prior))
        staged = file_pin(stage, stage_prior)
        compact = file_pin(final, mesh_path)
        assert staged["sha256"] == compact["sha256"]
        assert wave.identity(stage / pose_script) == wave.identity(final / pose_script)
        poses = read_poses(stage / pose_script)
        frames = {
            str(i): dict(
                pose={k: poses[i][k] for k in ("contact", "width", "beam", "degrees")},
                **{
                    name: file_pin(final, directory / f"media/{name}-{i:02}.webp")
                    for name in ("scan", "section")
                },
            )
            for i in ((12, 48) if kind == "carotid" else (12,))
        }
        raw_v, raw_f, raw = reference(mask, occupied, crop)
        cap_high = crop[1] - 0.5
        cap_low = max(crop[0], occupied[:, 2].min()) - 0.5
        planes = pose_planes(poses) if kind == "carotid" else []
        planes += [
            axial(cap_low + 0.76, "Just inside inferior cap"),
            axial(cap_high - 0.74, "Just inside superior cap"),
        ]
        outside = [axial(cap_high + 0.25, "Above superior crop or source image")]
        assert all(
            not len(wave.cut(raw_v[raw_f], np.asarray(p["originRasMm"]), np.asarray(p["normal"])))
            for p in outside
        )
        arrays = dict(vertices=raw_v, faces=raw_f)
        bind_planes(raw_v, raw_f, planes, ct, arrays)
        labels, _ = nd.label(raw)
        result = dict(
            sweep=use,
            halfLabelSurfaceSha256=sha256(
                raw_v.astype("<f8").tobytes() + raw_f.astype("<u4").tobytes()
            ).hexdigest(),
            cropZVoxelHalfOpen=list(crop),
            capZVoxel=cap_high,
            lowerCapZVoxel=cap_low,
            labelEuler=int(euler_number(raw, connectivity=1)),
            componentVoxels=np.bincount(labels.ravel())[1:].tolist(),
            enclosedVoidVoxels=int(np.count_nonzero(nd.binary_fill_holes(raw) & ~raw)),
            prior=dict(
                stage=staged,
                compact=compact,
                triangles=struct.unpack_from("<II", (stage / stage_prior).read_bytes())[1],
            ),
            savedPoseScript=file_pin(final, pose_script),
            savedFrames=frames,
            planes=planes,
            expectedEmptyPlanes=outside,
        )
        receipt["exports"][export] = result
        np.savez_compressed(scratch / f"{export}-reference.npz", **arrays)

    path = packet / "frozen.json"
    if path.exists():
        if json.loads(path.read_text()) != receipt:
            raise ValueError("Frozen carotid inputs changed")
    else:
        with path.open("x") as stream:
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
    for name, result in receipt["exports"].items():
        print(
            name,
            result["componentVoxels"],
            result["enclosedVoidVoxels"],
            [
                (p.get("frame", p.get("name")), p.get("offsetMm", 0), p["loops"])
                for p in result["planes"]
            ],
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("side", choices=("left", "right"))
    parser.add_argument("case", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("packet", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    freeze(args.side, args.case, args.baseline, args.packet, args.scratch)
