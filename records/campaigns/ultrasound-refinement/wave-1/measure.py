"""Freeze and compare the right-kidney half-label surface in the saved s1233 acquisition."""

import argparse
import json
import struct
from hashlib import sha256
from pathlib import Path

import numpy as np
from build_study import AFFINE, CT_SHA, volume
from delivery import read_poses, validate_mesh
from geometry import LENS_RADIUS_MM
from scipy import ndimage
from scipy.sparse import coo_array
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes

MASK_SHA = "8ca7e6696b90cb1e7e39b14e5c8f7e92c59b9344bff8fd368009751335abc8b5"
MESH_SHA = "58d9a1d89b0fadbb6f2601e665d946b36bd44fc4e6cdc9ec1eb11b7ec0ffc833"
INVENTORY_SHA = "0f24450cc378ec5476131771c8e224387518e205aea391907dea5bb926c7ead8"
FRAME = 12
OFFSETS = (-1.5, 0, 1.5)
SPACING = 0.5


def identity(path):
    raw = path.read_bytes()
    return dict(sha256=sha256(raw).hexdigest(), bytes=len(raw))


def ras(vertices):
    affine = np.asarray(AFFINE)
    return np.einsum("...j,ij->...i", vertices, affine[:3, :3]) + affine[:3, 3]


def unit_vector(vector):
    return vector / np.linalg.norm(vector)


def cut(triangles, origin, normal):
    signed = (triangles - origin) @ normal
    crosses = (signed.min(axis=1) < 0) & (signed.max(axis=1) >= 0)
    triangles, signed = triangles[crosses], signed[crosses]
    flipped = (signed < 0) != (signed[:, [1, 2, 0]] < 0)
    row, edge = np.nonzero(flipped)
    other = (edge + 1) % 3
    a, b = triangles[row, edge], triangles[row, other]
    fraction = signed[row, edge] / (signed[row, edge] - signed[row, other])
    return (a + (b - a) * fraction[:, None]).reshape(-1, 2, 3)


def connectivity(edges):
    return connected_components(
        coo_array(
            (np.ones(len(edges)), (edges[:, 0], edges[:, 1])),
            shape=(int(edges.max()) + 1,) * 2,
        ).tocsr(),
        directed=False,
    )


def outer_outline(segments):
    points, inverse = np.unique(segments.reshape(-1, 3).round(7), axis=0, return_inverse=True)
    edges = inverse.reshape(-1, 2)
    _, labels = connectivity(edges)
    group = labels[edges[:, 0]]
    lengths = np.linalg.norm(segments[:, 1] - segments[:, 0], axis=1)
    selected = group == np.bincount(group, weights=lengths).argmax()
    degree = np.bincount(edges[selected].ravel(), minlength=len(points))
    if np.any((degree != 0) & (degree != 2)):
        raise ValueError("The largest section outline is not closed")
    return segments[selected], np.unique(group).size


def poles(segments):
    points = segments.reshape(-1, 3)

    # A plateau shares its extreme RAS Z. Use the vertex nearest the plateau midpoint.
    def extreme(z):
        tied = np.unique(points[np.isclose(points[:, 2], z, atol=1e-7, rtol=0)], axis=0)
        return tied[np.argmin(np.linalg.norm(tied - tied.mean(axis=0), axis=1))]

    return np.array([extreme(points[:, 2].max()), extreme(points[:, 2].min())])


def chord_outside_outline(outline, endpoints, normal):
    """Measure chord intervals outside its closed contour by parity along the chord ray."""
    start, end = endpoints
    axis = unit_vector(end - start)
    along = dot(outline - start, axis)
    transverse = dot(outline - start, np.cross(normal, axis))
    a, b = transverse.T
    crossed = (a < 0) != (b < 0)
    crossings = along[crossed, 0] + a[crossed] / (a[crossed] - b[crossed]) * (
        along[crossed, 1] - along[crossed, 0]
    )
    chord = np.linalg.norm(end - start)
    crossings = np.sort(crossings)
    knots = np.unique(np.r_[0, crossings[(crossings > 0) & (crossings < chord)], chord])
    midpoint = (knots[:-1] + knots[1:]) / 2
    inside = np.searchsorted(crossings, midpoint) % 2 == 1
    return float(np.diff(knots)[~inside].sum())


def field(points, origin, width, beam):
    relative = points - origin
    x, y = relative @ width, relative @ beam + LENS_RADIUS_MM
    return np.column_stack((np.hypot(x, y) - LENS_RADIUS_MM, np.rad2deg(np.arctan2(x, y))))


def freeze(case, delivery, output):
    inventory = identity(delivery / "development/asset-inventory.json")
    if inventory["sha256"] != INVENTORY_SHA:
        raise ValueError("Wave 0 delivery inventory does not match the seal")
    sweep = delivery / "sweeps/kidney-right"
    poses_path = sweep / "sweep.js"
    pose = read_poses(poses_path)[FRAME]
    affine = np.asarray(AFFINE)
    origin = ras(np.array(pose["contact"]))
    width, beam = [unit_vector(affine[:3, :3] @ pose[key]) for key in ("width", "beam")]
    normal = unit_vector(np.cross(width, beam))
    ct = volume(case / "ct.nii.gz", CT_SHA, "<i2")
    mask = volume(case / "segmentations/kidney_right.nii.gz", MASK_SHA, "u1")
    nonzero = np.array(np.where(mask))
    lower, upper = nonzero.min(axis=1) - 2, nonzero.max(axis=1) + 3
    cropped = mask[tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))]
    vertices_voxel, faces, _, _ = marching_cubes(cropped, 0.5, allow_degenerate=False)
    vertices = ras(vertices_voxel + lower)
    triangles = vertices[faces]

    arrays = dict(vertices=vertices, faces=faces)
    receipt = dict(
        inventory=inventory,
        baseline=dict(
            case="abdomen-survey",
            chapter="abd-right-kidney",
            frame=FRAME,
            chordMm=107,
            page=identity(delivery / "tours/abdomen/abdomen-survey.html"),
            plate=identity(delivery / "cases/organs/images/abd-right-kidney.svg"),
        ),
        source=dict(
            case="s1233",
            ctSha256=CT_SHA,
            maskSha256=MASK_SHA,
            shape=mask.shape,
            rasMmFromVoxel=affine.tolist(),
            context=identity(sweep / "scenes/torso.mesh"),
        ),
        candidateMeshSha256=MESH_SHA,
        savedPose=pose,
        poseScript=identity(poses_path),
        widths=dict(lateral=width.tolist(), beam=beam.tolist()),
        originRasMm=origin.tolist(),
        normal=normal.tolist(),
        sampleSpacingMm=SPACING,
        planeSections=[],
    )
    # Sample CT in the same rectilinear coordinates as the projected reference.
    lo, hi = np.array([-70, 35]), np.array([70, 140])
    x, y = np.meshgrid(np.arange(lo[0], hi[0] + 0.25, 0.25), np.arange(lo[1], hi[1] + 0.25, 0.25))
    inverse = np.linalg.inv(affine)
    for index, offset in enumerate(OFFSETS):
        plane = origin + offset * normal
        contour = cut(triangles, plane, normal)
        outline, components = outer_outline(contour)
        endpoints = poles(outline)
        projected = field(endpoints, plane, width, beam)
        scan_points = plane + x[..., None] * width + y[..., None] * beam
        scan_voxels = scan_points @ inverse[:3, :3].T + inverse[:3, 3]
        arrays[f"ct{index}"] = ndimage.map_coordinates(ct, scan_voxels.transpose(2, 0, 1), order=1)
        arrays[f"outline{index}"] = contour
        arrays[f"poles{index}"] = endpoints
        receipt["planeSections"].append(
            dict(
                offsetMm=offset,
                originRasMm=plane.tolist(),
                contours=components,
                polesRasMm=endpoints.tolist(),
                poleDepthAngle=projected.tolist(),
                chordMm=float(np.linalg.norm(endpoints[0] - endpoints[1])),
            )
        )
    # Hash the canonical little-endian geometry. NPZ is a local convenience for the next step.
    receipt["referenceSurfaceSha256"] = sha256(
        vertices.astype("<f8").tobytes() + faces.astype("<u4").tobytes()
    ).hexdigest()
    np.savez_compressed(output / "reference.npz", **arrays)
    with (output / "reference.json").open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps(receipt, indent=2))


def mesh(path):
    raw = path.read_bytes()
    validate_mesh(raw, path)
    vertices, triangles = struct.unpack_from("<II", raw)
    points = np.frombuffer(raw, "<f4", vertices * 3, 8).reshape(-1, 3).astype(float)
    faces = np.frombuffer(raw, "<u4", triangles * 3, 8 + vertices * 12).reshape(-1, 3)
    return ras(points), faces


def samples(primitives):
    """Uniform barycentric lattices whose longest step is at most SPACING."""
    edge = primitives - np.roll(primitives, 1, axis=1)
    steps = np.maximum(1, np.ceil(np.linalg.norm(edge, axis=2).max(axis=1) / SPACING).astype(int))
    groups = []
    for n in np.unique(steps):
        ij = (
            [(i, j) for i in range(n + 1) for j in range(n + 1 - i)]
            if primitives.shape[1] == 3
            else [(i, 0) for i in range(n + 1)]
        )
        i, j = np.asarray(ij).T / n
        weights = np.array([1 - i - j, i, j]).T[:, : primitives.shape[1]]
        groups.append(np.einsum("sv,pvc->psc", weights, primitives[steps == n]).reshape(-1, 3))
    return np.unique(np.concatenate(groups).round(9), axis=0)


def dot(a, b):
    return np.einsum("...i,...i->...", a, b)


def segment_delta(points, a, b):
    edge = b - a
    distance = dot(edge, edge)
    fraction = np.divide(
        dot(points - a, edge), distance, out=np.zeros_like(distance), where=distance > 0
    )
    return points - (a + np.clip(fraction, 0, 1)[:, None] * edge)


def squared_distance(points, targets):
    a, b = targets[:, 0], targets[:, 1]
    delta = segment_delta(points, a, b)
    edge_distance = dot(delta, delta)
    if targets.shape[1] == 2:
        return edge_distance
    c = targets[:, 2]
    for start, end in ((b, c), (c, a)):
        delta = segment_delta(points, start, end)
        edge_distance = np.minimum(edge_distance, dot(delta, delta))
    ab, ac = b - a, c - a
    normal = np.cross(ab, ac)
    normal2 = dot(normal, normal)
    ap = points - a
    u = dot(np.cross(ap, ac), normal)
    v = dot(np.cross(ab, ap), normal)
    inside = (normal2 > 0) & (u >= 0) & (v >= 0) & (u + v <= normal2)
    edge_distance[inside] = dot(ap[inside], normal[inside]) ** 2 / normal2[inside]
    return edge_distance


def compare(source, target):
    points = samples(source)
    centers = target.mean(axis=1)
    radii = np.linalg.norm(target - centers[:, None, :], axis=2).max(axis=1)
    tree = cKDTree(centers)
    vertex_tree = cKDTree(np.unique(target.reshape(-1, 3), axis=0))
    chunks = []
    for begin in range(0, len(points), 4096):
        batch = points[begin : begin + 4096]
        upper, _ = vertex_tree.query(batch)
        # A closer primitive must be within its bounding sphere plus the vertex bound.
        candidate = tree.query_ball_point(batch, upper + radii.max() + 1e-8)
        count = np.array([len(ids) for ids in candidate])
        row = np.repeat(np.arange(len(batch)), count)
        ids = np.concatenate(candidate).astype(int)
        distances = squared_distance(batch[row], target[ids])
        minima = np.minimum.reduceat(distances, np.r_[0, np.cumsum(count)[:-1]])
        chunks.append(np.sqrt(minima))
    distances = np.concatenate(chunks)
    worst = distances.argmax()
    return dict(
        p95Mm=float(np.percentile(distances, 95)),
        maxMm=float(distances[worst]),
        maxLocationRasMm=points[worst].tolist(),
        samples=len(points),
    )


def self_intersections(vertices, faces):
    """Test nonincident pairs using triangle separating axes after sphere and AABB culling."""
    triangles = vertices[faces]
    centers = triangles.mean(axis=1)
    radii = np.linalg.norm(triangles - centers[:, None, :], axis=2).max(axis=1)
    pairs = cKDTree(centers).query_pairs(2 * radii.max() + 1e-8, output_type="ndarray")
    low, high = triangles.min(axis=1), triangles.max(axis=1)
    left, right = pairs.T
    overlaps = (
        np.maximum(low[left], low[right]) <= np.minimum(high[left], high[right]) + 1e-8
    ).all(axis=1)
    left, right = pairs[overlaps].T
    incident = (faces[left, :, None] == faces[right, None, :]).any(axis=(1, 2))
    a, b = triangles[left[~incident]], triangles[right[~incident]]
    edge_a, edge_b = np.roll(a, -1, axis=1) - a, np.roll(b, -1, axis=1) - b
    normal_a = np.cross(edge_a[:, 0], edge_a[:, 1])
    normal_b = np.cross(edge_b[:, 0], edge_b[:, 1])
    axes = np.concatenate(
        (
            normal_a[:, None, :],
            normal_b[:, None, :],
            np.cross(edge_a[:, :, None], edge_b[:, None, :]).reshape(-1, 9, 3),
            np.cross(normal_a[:, None, :], edge_a),
            np.cross(normal_b[:, None, :], edge_b),
        ),
        axis=1,
    )
    tolerance = 1e-8 * np.linalg.norm(axes, axis=2)
    proj_a = np.einsum("pvc,pac->pav", a - a[:, :1], axes)
    proj_b = np.einsum("pvc,pac->pav", b - a[:, :1], axes)
    separated = (proj_a.max(axis=2) < proj_b.min(axis=2) - tolerance) | (
        proj_b.max(axis=2) < proj_a.min(axis=2) - tolerance
    )
    return int((~separated.any(axis=1)).sum())


def topology(vertices, faces):
    directed = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    edges, ix, counts = np.unique(
        np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True
    )
    direction = np.bincount(ix, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
    a, b, c = vertices[faces].transpose(1, 0, 2)
    return dict(
        components=connectivity(edges)[0],
        euler=len(vertices) - len(edges) + len(faces),
        openEdges=int(np.sum(counts == 1)),
        nonmanifoldEdges=int(np.sum(counts > 2)),
        misorientedSharedEdges=int(np.sum((counts == 2) & (direction != 0))),
        degenerateTriangles=int(np.sum(np.linalg.norm(np.cross(b - a, c - a), axis=1) < 1e-12)),
        signedVolumeMm3=float(dot(a, np.cross(b, c)).sum() / 6),
        intersectingNonincidentPairs=self_intersections(vertices, faces),
    )


def contact_error(torso, origin, beam):
    vertices, faces = mesh(torso)
    a, b, c = (vertices[faces] - origin).transpose(1, 0, 2)
    ab, ac = b - a, c - a
    normal = np.cross(ab, ac)
    den = dot(normal, beam)
    valid = abs(den) > 1e-10
    a, ab, ac, normal, den = a[valid], ab[valid], ac[valid], normal[valid], den[valid]
    hit = (dot(a, normal) / den)[:, None] * beam
    u = dot(np.cross(hit - a, ac), normal)
    v = dot(np.cross(ab, hit - a), normal)
    intersects = (u >= 0) & (v >= 0) & (u + v <= dot(normal, normal))
    # Start on the incoming ray well outside the torso.
    return float((hit[intersects] @ beam).min())


def verify_grid_mismatch(case):
    wrong_affine = AFFINE.copy()
    wrong_affine[0, 3] += 1.5
    try:
        volume(
            case / "segmentations/kidney_right.nii.gz",
            MASK_SHA,
            "u1",
            ras_mm_from_voxel=wrong_affine,
        )
    except ValueError as error:
        if str(error) == "Unexpected grid: kidney_right.nii.gz":
            print(f"Correct mask bytes with a mismatched grid rejected: {error}")
            return
        raise
    raise AssertionError("Incorrect voxel-to-RAS affine was accepted")


def evaluate(delivery, output):
    receipt = json.loads((output / "reference.json").read_text())
    reference = np.load(output / "reference.npz")
    vertices, faces = reference["vertices"], reference["faces"]
    if (
        sha256(vertices.astype("<f8").tobytes() + faces.astype("<u4").tobytes()).hexdigest()
        != receipt["referenceSurfaceSha256"]
    ):
        raise ValueError("Frozen half-label surface identity changed")
    sweep = delivery / "sweeps/kidney-right"
    candidate = sweep / "scenes/kidney_right.mesh"
    if identity(candidate) != {"sha256": MESH_SHA, "bytes": 416840}:
        raise ValueError("Wave 0 kidney does not match its exact packed identity")
    points, indices = mesh(candidate)
    triangles = points[indices]
    assert len(indices) == 23156
    result = dict(
        mesh=identity(candidate),
        triangles=len(indices),
        topology=topology(points, indices),
        sections=[],
    )
    normal, beam = np.array(receipt["normal"]), np.array(receipt["widths"]["beam"])
    result["contactOffsetMm"] = contact_error(
        sweep / "scenes/torso.mesh", receipt["originRasMm"], beam
    )
    geometry = {}
    for index, plane in enumerate(receipt["planeSections"]):
        origin = np.array(plane["originRasMm"])
        gold, cyan = reference[f"outline{index}"], cut(triangles, origin, normal)
        reference_outer, _ = outer_outline(gold)
        geometry[f"candidate{index}"] = cyan
        outer, components = outer_outline(cyan)
        endpoints = poles(outer)
        chord = float(np.linalg.norm(endpoints[0] - endpoints[1]))
        result["sections"].append(
            dict(
                offsetMm=plane["offsetMm"],
                referenceToMesh=compare(gold, cyan),
                meshToReference=compare(cyan, gold),
                candidateContours=components,
                meshPolesRasMm=endpoints.tolist(),
                poleDisplacementMm=np.linalg.norm(
                    endpoints - reference[f"poles{index}"], axis=1
                ).tolist(),
                meshChordMm=chord,
                chordErrorMm=abs(chord - plane["chordMm"]),
                referenceChordOutsideOutlineMm=chord_outside_outline(
                    reference_outer, reference[f"poles{index}"], normal
                ),
            )
        )
    result["surface"] = dict(
        referenceToMesh=compare(vertices[faces], triangles),
        meshToReference=compare(triangles, vertices[faces]),
    )
    np.savez_compressed(output / "candidate-sections.npz", **geometry)
    (output / "measurements.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "evaluate"))
    parser.add_argument("case", type=Path)
    parser.add_argument("delivery", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze(args.case, args.delivery, args.output)
    else:
        verify_grid_mismatch(args.case)
        evaluate(args.delivery, args.output)


if __name__ == "__main__":
    main()
