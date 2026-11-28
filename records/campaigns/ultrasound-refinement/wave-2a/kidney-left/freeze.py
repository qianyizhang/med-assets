"""Freeze the exact prior mesh and source acquisition before shaping."""

import argparse
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from scipy import ndimage
from skimage.measure import euler_number, marching_cubes

ROOT = Path.cwd()
spec = importlib.util.spec_from_file_location(
    "wave_one", ROOT / "records/campaigns/ultrasound-refinement/wave-1/measure.py"
)
wave = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wave)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("case", type=Path)
parser.add_argument("organ", choices=["kidney-left", "gallbladder"])
args = parser.parse_args()
kidney = args.organ == "kidney-left"
slug = args.organ
part = slug.replace("-", "_")
prior = Path(".artifacts/us-wave1b/delivery")
sweep = prior / "sweeps/kidney-left" if kidney else prior
prior_mesh = (
    Path(".artifacts/us-wave1b/stage/sweeps/kidney-left/scenes/kidney_left.mesh")
    if kidney
    else prior / "scenes/gallbladder.mesh"
)
mask_digest = (
    "e0c7e53f00a20cedbe3e13d687ffc6d5e03a33824d4e4c7124f25335179b794e"
    if kidney
    else "c5dd1e8886ed87d29dac8225acbac49dfc308c0ead9116690c818e49b1addcc7"
)
prior_digest = (
    "c863c681ee3b6ea9ce42944292c205a097eceeb46d28c6cdaeaf7c6650b0eb69"
    if kidney
    else "6509c00826a818036d690192e98cb2f8e14aeb8786f9c699b2c8d5fb95ea1de9"
)
chapter = "abd-left-kidney" if kidney else "abd-gb"
if wave.identity(prior_mesh)["sha256"] != prior_digest:
    raise ValueError("Unexpected prior export identity")
pose_path = sweep / "sweep.js"
pose = wave.read_poses(pose_path)[12]
origin = wave.ras(np.array(pose["contact"]))
width, beam = [wave.unit_vector(wave.AFFINE[:3, :3] @ pose[key]) for key in ("width", "beam")]
normal = wave.unit_vector(np.cross(width, beam))
ct = wave.volume(args.case / "ct.nii.gz", wave.CT_SHA, "<i2")
mask = wave.volume(args.case / f"segmentations/{part}.nii.gz", mask_digest, "u1")
occupied = np.column_stack(np.nonzero(mask))
lower, upper = occupied.min(0) - 3, occupied.max(0) + 4
crop = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
labels, n = ndimage.label(crop)
counts = np.bincount(labels.ravel())[1:]
mesh, faces, _, _ = marching_cubes(crop, 0.5, allow_degenerate=False)
vertices = wave.ras(mesh + lower)
triangles = vertices[faces]
previous_v, previous_f = wave.mesh(prior_mesh)
arrays = dict(
    vertices=vertices, faces=faces, previous_vertices=previous_v, previous_faces=previous_f
)
receipt = dict(
    case="s1233",
    chapter=f"abdomen-survey / {chapter}",
    sweep=slug,
    part=part,
    frame=12,
    learnerAction=(
        "Relate both poles and the medial hilar recess in the s1233 exterior to the saved left flank long-axis field."
        if kidney
        else "Trace the broad fundus and body as they taper into the neck in the saved long-axis field."
    ),
    priorMesh=wave.identity(prior_mesh) | {"path": str(prior_mesh), "triangles": len(previous_f)},
    priorProceduralChapter=wave.identity(prior / "tours/abdomen/abdomen-survey.html"),
    priorSchematicPlate=wave.identity(prior / f"cases/organs/images/{chapter}.svg"),
    source=dict(
        ctSha256=wave.CT_SHA,
        maskSha256=mask_digest,
        shape=list(mask.shape),
        rasMmFromVoxel=wave.AFFINE.tolist(),
        sourceUrl="https://zenodo.org/records/10047263",
        license="CC BY 4.0",
        occupiedVoxels=len(occupied),
        components=n,
        componentSizes=sorted(counts.tolist(), reverse=True),
        enclosedBackgroundVoxels=int(
            np.count_nonzero(ndimage.binary_fill_holes(crop) & (crop == 0))
        ),
        labelEuler=int(euler_number(crop, connectivity=1)),
        halfLabelSurfaceSha256=sha256(
            vertices.astype("<f8").tobytes() + faces.astype("<u4").tobytes()
        ).hexdigest(),
        acquisitionSliceNormalRas=[0, 0, 1],
    ),
    savedAcquisition=dict(
        pose=pose,
        script=wave.identity(pose_path) | {"path": str(pose_path)},
        scans={
            kind: wave.identity(sweep / f"media/{kind}-12.webp") for kind in ("scan", "section")
        },
        originRasMm=origin.tolist(),
        width=width.tolist(),
        beam=beam.tolist(),
        normal=normal.tolist(),
        sectorDepthMm=133,
        sectorHalfAngleDeg=36,
    ),
    gates=dict(
        maxP95Mm=1.5,
        maxMm=3.0,
        maxAbsVolumePercent=3,
        topology="One Euler 2 closed outward manifold",
        triangles=[2500, 5000] if kidney else [1500, 3000],
        maxDegenerateFaces=0,
        maxIntersectingNonincidentPairs=0,
        maxTurningSilhouettePx=1,
        orthographicViews=24,
        silhouetteZoomPxPerMm=3,
        sampleSpacingMm=0.5,
    ),
    protectedPlanes=[],
    protectedLandmarks=(
        ["Superior and inferior poles", "Medial hilar depression"]
        if kidney
        else ["Broad fundus and body", "Tapering neck"]
    ),
    referenceLimit=(
        "The s1233 label resolves the renal exterior and medial recess. A left renal length or internal tissue/collecting-system claim requires its own acquisition evidence."
        if kidney
        else "The case label describes the external gallbladder form. Wall thickness, a cystic duct junction and stone motion require their own evidence."
    ),
    observedDefect=(
        "The exact previous export shows stacked horizontal bands on the inferior convex surface."
        if kidney
        else "The exact previous sweep loses contour at the narrow terminal end."
    ),
    method=(
        "Use mirrored adaptive signed-distance smoothing and Blender quadric decimation. Finer field samples interpolate the 1.5 mm label. Aim for one closed exterior without editorial repairs to components or holes."
        if kidney
        else "Use adaptive signed-distance smoothing and Blender quadric decimation. Preserve the taper with a narrower filter in thin regions. Aim for one closed exterior without editorial repairs to components or holes."
    ),
)
inverse = np.linalg.inv(wave.AFFINE)
for index, offset in enumerate((-1.5, 0.0, 1.5)):
    point = origin + offset * normal
    outline = wave.cut(triangles, point, normal)
    rel = outline.reshape(-1, 3) - point
    with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
        projected = np.column_stack((rel @ width, rel @ beam))
    lo, hi = np.floor(projected.min(0)) - 5, np.ceil(projected.max(0)) + 5
    x, y = np.meshgrid(np.arange(lo[0], hi[0] + 0.25, 0.25), np.arange(lo[1], hi[1] + 0.25, 0.25))
    physical = point + x[..., None] * width + y[..., None] * beam
    image_index = physical @ inverse[:3, :3].T + inverse[:3, 3]
    arrays[f"ct{index}"] = ndimage.map_coordinates(ct, image_index.transpose(2, 0, 1), order=1)
    arrays[f"outline{index}"] = outline
    receipt["protectedPlanes"].append(
        dict(
            offsetMm=offset,
            originRasMm=point.tolist(),
            sampleExtentMm=[lo.tolist(), hi.tolist()],
            referenceOutlineSha256=sha256(outline.astype("<f8").tobytes()).hexdigest(),
            referenceBoundsInPlaneMm=[projected.min(0).tolist(), projected.max(0).tolist()],
        )
    )
scratch = ROOT / ".artifacts/us-wave2a" / slug
packet = ROOT / "records/campaigns/ultrasound-refinement/wave-2a" / slug
scratch.mkdir(parents=True, exist_ok=True)
packet.mkdir(parents=True, exist_ok=True)
pin = packet / "frozen.json"
if pin.is_file():
    if json.loads(pin.read_text()) != receipt:
        raise ValueError(
            "Recomputed reference, prior delivery or pose differs from the frozen packet"
        )
else:
    with pin.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
np.savez_compressed(scratch / "reference.npz", **arrays)
print(json.dumps(receipt["source"], indent=2))
