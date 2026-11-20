"""Projection and fixed-plane measurements on the reimported s1233 surfaces."""

import json
import struct
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = spec_from_file_location("r04_section", HERE.parent / "adrenal-study-r04" / "section.py")
sections = module_from_spec(spec)
spec.loader.exec_module(sections)
ref = sections.reference


def clear_projection(groups, key, direction):
    """Estimate clear projected area using centroids of visible facing triangles."""
    direction = np.array(direction, dtype=float)
    direction /= np.linalg.norm(direction)
    shell = groups[key][0]
    own = ref.tree(shell)
    others = [ref.tree(part) for label, parts in groups.items() if label != key for part in parts]
    tri = shell[0][shell[1]]
    weight = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]) @ direction
    clear, visible = 0.0, 0.0
    for center, area in zip(tri[weight > 0].mean(1), weight[weight > 0], strict=True):
        if own.ray_cast(center + direction * 1e-6, direction)[0] is not None:
            continue
        visible += area
        if all(tree.ray_cast(center, d)[0] is None for tree in others for d in (direction, -direction)):
            clear += area
    return float(clear / visible)


def regional_measurements(groups, key, front):
    side = key.rsplit("-", 1)[-1]
    gland, kidney = groups[key][0], groups["kidney-" + side][0]
    g, k = (np.array(ref.shell_stats(s)["areaCentroidMm"]) for s in (gland, kidney))
    return {
        "glandCentroidSuperiorToIpsilateralKidneyMm": float(g[2] - k[2]),
        "glandCentroidMedialToIpsilateralKidneyMm": float(abs(k[0]) - abs(g[0])),
        "clearProjectedAreaFraction": {
            "default": clear_projection(groups, key, front),
            "straightPosterior": clear_projection(groups, key, (0, 1, 0)),
        },
    }


def axial_sections(case, previous, updated):
    result = []
    for key, level in (
        ("adrenal-gland-left", -87.0),
        ("adrenal-gland-right", -67.35),
        ("adrenal-gland-right", -74.0),
    ):
        planes = {}
        for name, groups in (("r02", case), ("r04", previous), ("r05", updated)):
            rings = sections.section(groups[key][0], np.array([0, 0, 1]), level / 1000)
            planes[name] = [(ring[:, :2] * 1000).tolist() for ring in rings]
        result.append({"part": key, "zMm": level, "contoursXYMm": planes})
    return result


def cleft_sections(case, previous, updated):
    """Inspect the diagonal return at review planes and neighboring label-grid centers."""
    anchor = np.array([-49.0, 27.3])
    direction = np.array([1.0, -1.0]) / np.sqrt(2)
    results = []
    for z in (-68.10, -67.80, -67.35, -66.60, -66.30, -65.85, -65.10, -64.80, -64.35):
        contours = {}
        for key, groups in (("r02", case), ("r04", previous), ("r05", updated)):
            rings = sections.section(groups["adrenal-gland-right"][0], np.array([0, 0, 1]), z / 1000)
            edges = (
                np.concatenate([np.stack([r[:, :2], np.roll(r[:, :2], -1, axis=0)], axis=1) for r in rings])
                * 1000
            )
            contours[key] = edges
        points = contours["r02"][:, 0]
        points = points[(points[:, 0] > -38) & (points[:, 0] < -25) & (points[:, 1] > 3) & (points[:, 1] < 19)]
        if not len(points):
            raise ValueError(f"No traced right cleft vertices at z={z}")
        station, residual = {}, {}
        for key, edges in contours.items():
            start, end = edges[:, 0], edges[:, 1]
            d = end - start
            # The ray normal is parallel to (+1,+1). Intersect only edges
            # crossing that line, then report the nearest forward intersection.
            side0, side1 = (start - anchor).sum(1), (end - anchor).sum(1)
            cross = (side0 > 0) != (side1 > 0)
            t = side0[cross] / (side0[cross] - side1[cross])
            hits = (start[cross] + t[:, None] * d[cross] - anchor) @ direction
            station[key] = float(hits[hits >= 0].min())
            if key == "r02":
                continue
            delta = points[:, None, :] - start[None, :, :]
            fraction = np.clip(np.sum(delta * d, axis=2) / np.sum(d * d, axis=1), 0, 1)
            nearest = start + fraction[:, :, None] * d
            distances = np.linalg.norm(points[:, None, :] - nearest, axis=2)
            i = np.argmax(distances.min(1))
            j = np.argmin(distances[i])
            residual[key] = {
                "maxMm": float(distances[i, j]),
                "caseXYMm": points[i].tolist(),
                "nearestXYMm": nearest[i, j].tolist(),
                "caseVertices": len(points),
            }
        results.append({"zMm": z, "rayFirstHitMm": station, "caseVertexToContour": residual})
    return {
        "part": "adrenal-gland-right",
        "windowXYMm": [[-38, 3], [-25, 19]],
        "rayAnchorXYMm": anchor.tolist(),
        "rayInwardDirectionXY": direction.tolist(),
        "labelGridCenterZMm": [-67.80, -66.30, -64.80],
        "planes": results,
    }


def portable_capsule(path, gland_keys):
    with path.open("rb") as stream:
        header = stream.read(20)
        _, _, _, length, _ = struct.unpack("<4sIII4s", header)
        gltf = json.loads(stream.read(length))
    targets = [node for node in gltf["nodes"] if node.get("extras", {}).get("anatomy_id") in gland_keys]
    primitives = [gltf["meshes"][node["mesh"]]["primitives"][0] for node in targets]
    materials = {prim["material"] for prim in primitives}
    if (
        len(targets) != 2
        or len(materials) != 1
        or any({"COLOR_0", "TEXCOORD_0"} - prim["attributes"].keys() for prim in primitives)
    ):
        raise ValueError("GLB lost gland palette, surface coordinates or shared material")
    material = gltf["materials"][materials.pop()]
    pbr = material["pbrMetallicRoughness"]
    texture = gltf["textures"][pbr["metallicRoughnessTexture"]["index"]]
    image = gltf["images"][texture["source"]]
    coat = material["extensions"]["KHR_materials_clearcoat"]
    if "bufferView" not in image or image["mimeType"] != "image/png" or pbr.get("baseColorFactor") is None:
        raise ValueError("GLB must contain a warm base factor and embedded roughness lookup")
    return {
        "name": material["name"],
        "baseColorFactor": pbr["baseColorFactor"],
        "coat": coat,
        "roughnessImage": image["name"],
    }
