"""Verify the two pinned r03 tunnel sections against the actual r04 triangles."""

from importlib.util import module_from_spec, spec_from_file_location
import argparse
from pathlib import Path
import sys

from mathutils import Vector
import numpy as np


# Both points lie on clear rays through their exact r03 surfaces. Coordinates
# are in the shared Blender frame. The triangle sections are below mask resolution.
WITNESSES = {
    "adrenal-gland-left": (
        (44.163101368272706, -14.187930489662628, -61.262660736449874),
        (-0.6209022837268127, -0.2942571794478066, 0.7265625),
    ),
    "adrenal-gland-right": (
        (-34.18013003469538, 3.7791910573273593, -73.15042030219932),
        (-0.30304178282469396, -0.8425333555451564, 0.4453125),
    ),
}

HERE = Path(__file__).resolve().parent
spec = spec_from_file_location("reference", HERE.parent / "adrenal-study-r03" / "build.py")
reference = module_from_spec(spec)
spec.loader.exec_module(reference)

def section(shell, normal, level):
    points, faces = shell
    signed = points @ normal
    distances = signed[faces] - level
    edges = faces[(distances.min(1) < 0) & (distances.max(1) > 0)]
    edge_locations, neighbors = {}, {}
    for triangle in edges:
        crosses = []
        for a, b in zip(triangle, np.roll(triangle, -1), strict=True):
            if (signed[a] > level) == (signed[b] > level):
                continue
            edge = tuple(sorted((a, b)))
            crosses.append(edge)
            if edge not in edge_locations:
                t = (level - signed[a]) / (signed[b] - signed[a])
                edge_locations[edge] = points[a] + t * (points[b] - points[a])
        if len(crosses) != 2:
            raise ValueError("Unstable ring section")
        a, b = crosses
        neighbors.setdefault(a, []).append(b)
        neighbors.setdefault(b, []).append(a)
    unseen = set(neighbors)
    rings = []
    while unseen:
        start = unseen.pop()
        prev, point = start, neighbors[start][0]
        ring = [edge_locations[start]]
        while point != start:
            if point not in unseen or len(neighbors[point]) != 2:
                raise ValueError("Unexpected open contour")
            unseen.remove(point)
            ring.append(edge_locations[point])
            prev, point = point, next(p for p in neighbors[point] if p != prev)
        rings.append(np.array(ring))
    return rings



def compare(before, after, position_mm, direction):
    position = np.array(position_mm) / 1000
    normal = np.array(direction)
    u = np.cross(normal, np.eye(3)[np.argmin(np.abs(normal))])
    u /= np.linalg.norm(u)
    axes = np.stack([u, np.cross(normal, u)])
    level = position @ normal
    a, b = (section(shell, normal, level) for shell in (before, after))
    original, candidate = reference.tree(before), reference.tree(after)
    ray_open = all(original.ray_cast(position, v)[0] is None for v in (normal, -normal))
    nearest, outward, _, depth = candidate.find_nearest(position)
    if len(a) != 2 or len(b) != 1 or not ray_open or outward.dot(Vector(position) - nearest) >= 0:
        raise ValueError(f"Section did not verify the through-opening at {position_mm}")
    return {
        "normal": normal.tolist(),
        "axisU": axes[0].tolist(),
        "axisV": axes[1].tolist(),
        "pointMm": list(position_mm),
        "r03SectionLoopsMm": [(1000 * ((ring - position) @ axes.T)).tolist() for ring in a],
        "r04SectionLoopsMm": [(1000 * ((ring - position) @ axes.T)).tolist() for ring in b],
        "straightRayOpenInBothDirections": ray_open,
        "candidateInteriorDepthMm": depth * 1000,
        "sourceSurfaceDistanceMm": original.find_nearest(position)[3] * 1000,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--updated", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source = HERE.parent / "adrenal-study-r03" / "s1233-adrenals-teaching.glb"
    old, new = [
        {label: reference.parts(obj)[0] for label, obj in reference.load(path).items() if label in WITNESSES}
        for path in (source, args.updated)
    ]
    locations = {
        label: compare(old[label], new[label], position, direction)
        for label, (position, direction) in WITNESSES.items()
    }
    reference.write_json(args.output, {
        "sourceSha256": reference.sha256(source),
        "updatedSha256": reference.sha256(args.updated),
        "recipeSha256": reference.sha256(Path(__file__)),
        "locations": locations,
    })


if __name__ == "__main__":
    main()
