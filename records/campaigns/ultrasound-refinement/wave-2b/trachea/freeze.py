"""Freeze the s1127 trachea label, prior neck crops and saved sweep acquisitions."""

import argparse
import json
import runpy
import struct
from hashlib import sha256
from pathlib import Path

import numpy as np
from build_study import volume
from build_thyroid import AFFINE, CT_SHA, PINS, SHAPE
from delivery import read_poses
from scipy import ndimage
from skimage.measure import euler_number

HERE = Path(__file__).resolve().parent
CROPS = {"trachea": (0, 409), "thyroid": (344, 409), "carotid": (369, 407)}
CONTEXTS = {
    "thyroid": ("thyroid-right", "thyroid-left"),
    "carotid": ("carotid-right", "carotid-left"),
}
FRAMES = {"thyroid": (0, 12, 48), "carotid": (12, 48)}


def imaging_planes(helpers, track, frames, route):
    wave = helpers["wave"]
    ras = helpers["ras"]
    planes = []
    for frame in frames:
        pose = track[frame]
        origin = ras(pose["contact"])
        width, beam = (np.asarray(pose[key]) for key in ("width", "beam"))
        normal = wave.unit_vector(np.cross(width, beam))
        for offset in (-1.5, 0.0, 1.5):
            planes.append(
                {
                    "name": f"{route} frame {frame} offset {offset:+g} mm",
                    "frame": frame,
                    "offsetMm": offset,
                    "originRasMm": (origin + offset * normal).tolist(),
                    "width": width.tolist(),
                    "beam": beam.tolist(),
                    "normal": normal.tolist(),
                }
            )
    return planes


def freeze_planes(wave, vertices, faces, planes, ct, arrays):
    for index, plane in enumerate(planes):
        width, beam, normal, origin = (
            np.asarray(plane[key]) for key in ("width", "beam", "normal", "originRasMm")
        )
        fragments = wave.cut(vertices[faces], origin, normal)
        # The saved transverse cut crosses vertices and edges shared by several raw
        # triangles. Stitch their coincident endpoints and count each line once.
        pts, inverse = np.unique(fragments.reshape(-1, 3).round(7), axis=0, return_inverse=True)
        edges = np.unique(np.sort(inverse.reshape(-1, 2), axis=1), axis=0)
        outline = pts[edges[edges[:, 0] != edges[:, 1]]]
        relative = outline.reshape(-1, 3) - origin
        xy = np.column_stack((wave.dot(relative, width), wave.dot(relative, beam)))
        lower, upper = np.floor(xy.min(0)) - 5, np.ceil(xy.max(0)) + 5
        plane["outlineSha256"] = sha256(outline.astype("<f8").tobytes()).hexdigest()
        plane["bounds"] = [lower.tolist(), upper.tolist()]
        plane["loops"] = int(wave.outer_outline(outline)[1])
        arrays[f"outline{index}"] = outline
        u, v = np.meshgrid(
            np.arange(lower[0], upper[0] + 0.25, 0.25),
            np.arange(lower[1], upper[1] + 0.25, 0.25),
        )
        voxel = (origin + u[..., None] * width + v[..., None] * beam - AFFINE[:3, 3]) / 1.5
        arrays[f"ct{index}"] = ndimage.map_coordinates(
            ct, voxel.transpose(2, 0, 1), order=1, mode="nearest"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("case", "baseline", "scratch"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    helpers = runpy.run_path(str(HERE.parent / "carotid/freeze_carotid.py"))
    wave = helpers["wave"]
    hash_arrays = helpers["sha256"]
    axial = helpers["axial"]
    image = args.case / "ct.nii.gz"
    label = args.case / "segmentations/trachea.nii.gz"
    ct = volume(image, CT_SHA, "<i2", SHAPE, AFFINE)
    mask = volume(label, PINS["trachea"], "u1", SHAPE, AFFINE) > 0
    occupied = np.argwhere(mask)
    stage, compact = (args.baseline / name for name in ("stage", "final"))
    catalogue, _ = json.JSONDecoder().raw_decode(
        (compact / "abdomen-tours.js").read_text().split("=", 1)[1].lstrip()
    )
    tracks = {row["id"]: row for row in catalogue}
    file_pin = helpers["file_pin"]
    receipt = {
        "baselineRevision": "abe213c44df81a1510558b5595b2d14ffed74d78",
        "baselineAssembly": str(args.baseline),
        "compactIndex": file_pin(compact, "abdomen-tours.js"),
        "scope": "Orient the tracheal air-column exterior as a midline landmark deep to the thyroid isthmus on a separate s1127 case.",
        "chapter": {
            "case": "thyroid-normal",
            "chapter": "thyroid-axial",
            "workedFrame": 12,
            "companionFrame": 0,
            "page": file_pin(compact, "tours/thyroid/thyroid-normal-sweep.html"),
        },
        "source": {
            "case": "s1127",
            "ctSha256": CT_SHA,
            "mask": wave.identity(label),
            "shape": list(SHAPE),
            "rasMmFromVoxel": AFFINE.tolist(),
            "label": "trachea",
            "acquisitionSliceNormalRas": [0, 0, 1],
            "workingSpacingMm": [1.5] * 3,
            "license": "TotalSegmentator v2.0.1, CC BY 4.0. Retain label-source notice.",
        },
        "gates": helpers["GATES"]
        | {
            "topology": "One outward Euler-2 solid exterior in each scope. Full label preserves the inferior bifurcation. No introduced gaps, winding errors or intersections.",
        },
        "exports": {},
    }
    args.scratch.mkdir(parents=True, exist_ok=False)
    for name, crop in CROPS.items():
        vertices, faces, raw = helpers["reference"](mask, occupied, crop)
        cap_low, cap_high = (
            max(crop[0], int(occupied[:, 2].min())) - 0.5,
            min(crop[1] - 1, int(occupied[:, 2].max())) + 0.5,
        )
        planes = [
            axial(cap_low + 0.76, "Just inside inferior cap"),
            axial(cap_high - 0.74, "Just inside superior cap"),
        ]
        if name == "trachea":
            planes += [
                axial(324.25, "Distal branches"),
                axial(335.25, "Inferior transition"),
                axial(353.25, "Lower trunk"),
                axial(384.25, "Upper trunk"),
            ]
        outside = [
            axial(cap_low - 0.25, "Below source or crop"),
            axial(cap_high + 0.25, "Above source"),
        ]
        row = {
            "halfLabelSurfaceSha256": hash_arrays(
                vertices.astype("<f8").tobytes() + faces.astype("<u4").tobytes()
            ).hexdigest(),
            "cropZVoxelHalfOpen": list(crop),
            "lowerCapZVoxel": cap_low,
            "capZVoxel": cap_high,
            "rawLabel": {
                "components": ndimage.label(raw)[1],
                "euler": euler_number(raw, connectivity=1),
                "voxels": int(np.count_nonzero(raw)),
                "enclosedBackgroundVoxels": int(
                    np.count_nonzero(ndimage.binary_fill_holes(raw) & ~raw)
                ),
            },
            "planes": planes,
            "expectedEmptyPlanes": outside,
            "contextTracks": {},
        }
        for index, route in enumerate(CONTEXTS.get(name, ())):
            sub = Path("sweeps") / route
            path = sub / "scenes/trachea.mesh"
            pose_script = sub / "sweep.js"
            prior_staged = file_pin(stage, path)
            compact_path = tracks[route].get("meshPaths", {}).get("trachea", str(path))
            prior_compact = file_pin(compact, compact_path)
            assert prior_staged["sha256"] == prior_compact["sha256"]
            assert wave.identity(stage / pose_script) == wave.identity(compact / pose_script)
            poses = read_poses(stage / pose_script)
            context = {
                "prior": {
                    "stage": prior_staged,
                    "compact": prior_compact,
                    "triangles": struct.unpack_from("<2I", (stage / path).read_bytes())[1],
                },
                "savedPoseScript": file_pin(compact, pose_script),
                "savedFrames": {
                    str(frame): {
                        "pose": {
                            key: poses[frame][key]
                            for key in ("contact", "width", "beam", "degrees")
                        },
                        **{
                            kind: file_pin(compact, sub / f"media/{kind}-{frame:02}.webp")
                            for kind in ("scan", "section")
                        },
                    }
                    for frame in FRAMES[name]
                },
            }
            row["contextTracks"][route] = context
            if index == 0:
                row.update(sweep=route, **context)
            cuts = imaging_planes(helpers, poses, FRAMES[name], route)
            if name == "thyroid":
                planes.extend(cut for cut in cuts if index == 0 or cut["frame"] != 0)
            else:
                outside.extend(cuts)
        if any(len(wave.cut(vertices[faces], p["originRasMm"], p["normal"])) for p in outside):
            raise ValueError(f"{name}: expected empty source cut intersects the label")
        arrays = dict(vertices=vertices, faces=faces)
        freeze_planes(wave, vertices, faces, planes, ct, arrays)
        np.savez_compressed(args.scratch / f"{name}-reference.npz", **arrays)
        print(name, row["rawLabel"], [(p["name"], p["loops"]) for p in planes])
        receipt["exports"][name] = row
    with (args.scratch / "reference.json").open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
