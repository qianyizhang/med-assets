"""Build same-scene teaching mesh trials from pinned GLBs and render clean imports."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.glb import decode, encode

# Reuse the verified local skin builder's edge-link and face checks.
SKIN = runpy.run_path(str(ROOT / "models/skin/recipes/navigation-trial/build.py"))
VIEWS = runpy.run_path(str(HERE.parent / "2026-11-22-body-cardiovascular-digestive-endocrine/render.py"))
TYPES = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
SIZE = VIEWS["SIZE"]


def identity(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def array(document, binary, index):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    if "sparse" in accessor or view.get("buffer", 0):
        raise ValueError("Selected accessor has sparse or external data")
    width = WIDTHS[accessor["type"]]
    dtype = np.dtype(TYPES[accessor["componentType"]])
    if view.get("byteStride", width * dtype.itemsize) != width * dtype.itemsize:
        raise ValueError("Selected accessor is interleaved")
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return np.frombuffer(binary, dtype=dtype, count=accessor["count"] * width,
                         offset=offset).reshape(-1, width)


def node_scales(document):
    """Largest world-space scale for each mesh, including ancestors and instances."""
    result = defaultdict(float)
    def visit(index, parent):
        node = document["nodes"][index]
        if "matrix" in node:
            local = np.array(node["matrix"]).reshape(4, 4).T[:3, :3]
            scale = float(np.linalg.norm(local, ord=2))
        else:
            scale = max(abs(x) for x in node.get("scale", [1, 1, 1]))
        scale *= parent
        if "mesh" in node:
            key = node["mesh"]
            result[key] = max(scale, result[key])
        for child in node.get("children", []):
            visit(child, scale)
    for scene in document["scenes"]:
        for root in scene.get("nodes", []):
            visit(root, 1.)
    return result


def seam_and_landmark_mask(positions, faces, extra, morph_region=None):
    links, uses = SKIN["edges"](faces)
    locked = np.zeros(len(positions), dtype=bool)
    locked[links[uses != 2].ravel()] = True
    _, inverse, counts = np.unique(positions, axis=0, return_inverse=True, return_counts=True)
    locked |= counts[inverse] > 1
    low, high = positions.min(axis=0), positions.max(axis=0)
    locked |= ((positions == low) | (positions == high)).any(axis=1)
    # Protect explicitly selected ends or a region along a glTF local axis.
    if extra:
        axis, lower, upper = extra
        normalized = (positions[:, axis] - low[axis]) / max(high[axis] - low[axis], 1e-30)
        locked |= (normalized >= lower) & (normalized <= upper)
    if morph_region is not None:
        locked |= morph_region
    protected_faces = faces[locked[faces].any(axis=1)]
    locked[protected_faces.ravel()] = True
    return locked, SKIN["oriented"](protected_faces)


def simplify(positions, triangles, locked, max_edge, ratio):
    mesh = bmesh.new()
    tag = mesh.verts.layers.int.new("source_index")
    try:
        vertices = []
        for index, point in enumerate(positions):
            vertex = mesh.verts.new(Vector(point))
            vertex[tag] = index
            vertices.append(vertex)
        for face in triangles:
            mesh.faces.new([vertices[index] for index in face])
        target = int((len(triangles) - int(ratio * len(triangles))) / 2)
        count = 0
        for _ in range(7):
            mesh.normal_update()
            options = []
            for edge in mesh.edges:
                a, b = edge.verts
                ia, ib = a[tag], b[tag]
                if locked[ia] or locked[ib] or not edge.is_manifold:
                    continue
                length = edge.calc_length()
                if length <= max_edge:
                    if ia > ib:
                        ia, ib, a, b = ib, ia, b, a
                    options.append((length, ia, ib, a, b, edge))

            mapping = {}
            occupied = set()
            for _, _, _, a, b, edge in sorted(options):
                if a in occupied or b in occupied:
                    continue
                opposite = {v for face in edge.link_faces for v in face.verts if v not in (a, b)}
                an = SKIN["neighbors"](a)
                bn = SKIN["neighbors"](b)
                # Edge contraction link condition. A contraction cannot join components
                # or open a handle. The disjoint stars keep simultaneous welds independent.
                if len(opposite) != 2 or an & bn != opposite:
                    continue
                if SKIN["preserves_faces"](a, b):
                    mapping[b] = a
                elif SKIN["preserves_faces"](b, a):
                    mapping[a] = b
                else:
                    continue
                occupied.update(an | bn | {a, b})
                if count + len(mapping) >= target:
                    break
            if not mapping:
                break
            bmesh.ops.weld_verts(mesh, targetmap=mapping)
            count += len(mapping)
            if count >= target:
                break
        result = np.asarray([[v[tag] for v in face.verts] for face in mesh.faces], dtype=np.int32)
    finally:
        mesh.free()
    if len(result) != len(triangles) - 2 * count:
        raise ValueError("A contraction changed face count outside the contracted links")
    return SKIN["oriented"](result)


def check_protected(after, protected):
    def packed(faces):
        return np.ascontiguousarray(faces, dtype=np.int32).view("V12").ravel()
    if not np.isin(packed(protected), packed(after)).all():
        raise ValueError("A protected seam, boundary, extremum or landmark face changed")


def samples(source, target, points):
    """Sample both vertex and face-center positions on the source topology."""
    tree = BVHTree.FromPolygons(points, target.tolist(), all_triangles=True)
    query = np.concatenate((points[np.unique(source)], points[source].mean(axis=1)))
    worst = (0., None)
    for point in query:
        _, _, _, distance = tree.find_nearest(Vector(point))
        if distance is None:
            raise ValueError("Missing a sampled target surface")
        if distance > worst[0]:
            worst = (distance, point.tolist())
    return worst


def sparse_rows(doc, binary, index):
    """Read the pinned zero-base sparse target without densifying its output."""
    accessor = doc["accessors"][index]
    sparse = accessor["sparse"]
    if "bufferView" in accessor:
        raise ValueError("Expected a zero-base sparse target")
    rows = {}
    for key, dtype, count in (
            ("indices", TYPES[sparse["indices"]["componentType"]], sparse["count"]),
            ("values", TYPES[accessor["componentType"]], sparse["count"] * WIDTHS[accessor["type"]])):
        entry = sparse[key]
        view = doc["bufferViews"][entry["bufferView"]]
        offset = view.get("byteOffset", 0) + entry.get("byteOffset", 0)
        rows[key] = np.frombuffer(binary, dtype=dtype, count=count, offset=offset)
    return rows["indices"], rows["values"].reshape(sparse["count"], -1)


def geometry_replacements(row, doc, binary, world_span):
    rules = [(re.compile(rule["match"], re.I), rule) for rule in row.get("rules", [])]
    ownership = Counter()
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            ownership.update([primitive["indices"], *primitive["attributes"].values()])
            for target in primitive.get("targets", []):
                ownership.update(target.values())
    scales = node_scales(doc)
    replacements, measurements, rebindings, sparse_targets = {}, [], {}, {}
    changed = 0
    preview_captured = False
    total = sum(doc["accessors"][p["indices"]]["count"] // 3
                for mesh in doc["meshes"] for p in mesh["primitives"])
    for mesh_index, mesh in enumerate(doc["meshes"]):
        for part_index, part in enumerate(mesh["primitives"]):
            name = mesh.get("name", str(mesh_index))
            accessor = doc["accessors"][part["indices"]]
            tri_count = accessor["count"] // 3
            qualified = f"{name} #{part_index}"
            rule = next((r for pattern, r in rules if pattern.search(qualified)
                         and tri_count >= r.get("minTriangles", 1800)), None)
            if rule is None:
                continue
            note = {"mesh": mesh_index, "primitive": part_index, "name": name,
                    "beforeTriangles": tri_count, "afterTriangles": tri_count, "attempts": []}
            measurements.append(note)
            try:
                attrs = part["attributes"]
                targets = part.get("targets", [])
                if part.get("mode", 4) != 4 or part.get("extensions") or len(targets) > 1:
                    raise ValueError("Unsupported triangle or morph primitive")
                target = targets[0] if targets else {}
                if not set(attrs) <= {"POSITION", "NORMAL", "TEXCOORD_0", "COLOR_0", "COLOR_1"}:
                    raise ValueError("Unverified vertex attributes")
                coords = array(doc, binary, attrs["POSITION"])
                faces = array(doc, binary, part["indices"]).reshape(-1, 3).astype(np.int32)
                if len(faces) != tri_count or not len(coords) or not np.isfinite(coords).all():
                    raise ValueError("Invalid selected geometry")
                if "NORMAL" in attrs and len(array(doc, binary, attrs["NORMAL"])) != len(coords):
                    raise ValueError("Invalid normal count")
                scale = scales[mesh_index]
                span = float(np.ptp(coords, axis=0).max()) * scale
                if not span or not scale:
                    raise ValueError("Invalid world-space bounds")
                unit = min(world_span, span * rule.get("featureZoom", 2.5)) / SIZE
                max_edge = unit * rule.get("edgePx", 30) / scale
                threshold = unit * rule.get("maxPx", 1.)
                deform = None
                sparse_target = None
                delta_position = target.get("POSITION")
                if delta_position is not None:
                    if "sparse" in doc["accessors"][delta_position]:
                        sparse_target = delta_position
                        vertices, values = sparse_rows(doc, binary, delta_position)
                        deform = np.zeros_like(coords)
                        deform[vertices] = values
                    else:
                        deform = array(doc, binary, delta_position)
                morph_region = np.any(deform != 0, axis=1) if sparse_target is not None else None
                locked, protected = seam_and_landmark_mask(coords, faces, rule.get("lockBand"), morph_region)
                note.update(vertices=len(coords), lockedVertices=int(locked.sum()), exactProtectedFaces=len(protected),
                            maximumSampleDistance=threshold, maximumEdge=scale * max_edge)
                preview = None
                accepted = False
                for edge_factor, relax in ((1., 0.), (.45, .17), (.20, .28)):
                    ratio = min(.94, rule["ratio"] + relax)
                    after = simplify(coords, faces, locked, max_edge * edge_factor, ratio)
                    removed = tri_count - len(after)
                    note["attempts"].append({"triangles": len(after), "edgeFactor": edge_factor,
                                             "requestedRatio": ratio})
                    if removed < max(6, tri_count * .04):
                        note["rejection"] = "Seams, boundaries or edge limits leave under 4% saving"
                        break
                    check_protected(after, protected)
                    forward = samples(faces, after, coords)
                    reverse = samples(after, faces, coords)
                    worst = max(forward, reverse)
                    bounds = dict(forward=scale * forward[0], reverse=scale * reverse[0],
                                  worstLocalPosition=worst[1], edgeFactor=edge_factor,
                                  worstSamplePixels=scale * worst[0] / unit, requestedRatio=ratio)
                    note.update(bounds)
                    note["attempts"][-1]["worstSamplePixels"] = bounds["worstSamplePixels"]
                    if scale * worst[0] > threshold:
                        note["rejection"] = "A sampled surface shifted beyond the screen-space allowance"
                        if preview is None:
                            preview = (after, bounds)
                        continue
                    if deform is not None:
                        morph_distances = []
                        for weight in (.5, 1.):
                            posed = coords + weight * deform
                            morph_distances.append(scale * max(samples(faces, after, posed)[0],
                                                               samples(after, faces, posed)[0]))
                        note["morphSampleDistances"] = morph_distances
                        if max(morph_distances) > threshold:
                            note["rejection"] = "Morph sample exceeded the screen-space allowance"
                            continue
                    accepted = True
                    note.pop("rejection", None)
                    break
                if not accepted:
                    if not (row.get("retainFailedPreview") and preview and not preview_captured):
                        continue
                    after, bounds = preview
                    note.update(bounds, rejectedPreview=True,
                                rejection="A sampled surface shifted beyond the screen-space allowance")
                    preview_captured = True
                    removed = tri_count - len(after)
                used, remapped = np.unique(after, return_inverse=True)
                part_replacements = {i: array(doc, binary, i)[used]
                                     for i in [*attrs.values(), *target.values()] if i != sparse_target}
                if any(ownership[i] != 1 for i in target.values()):
                    raise ValueError("Selected morph targets are shared")
                if sparse_target is not None:
                    rows, _ = sparse_rows(doc, binary, sparse_target)
                    new_rows = np.searchsorted(used, rows)
                    if np.any(new_rows >= len(used)) or not np.array_equal(used[new_rows], rows):
                        raise ValueError("Sparse motion landmark vertices changed")
                    sparse_targets[sparse_target] = (len(used), new_rows.astype(rows.dtype))
                index_type = "<u2" if len(used) <= 65_535 else "<u4"
                part_replacements[part["indices"]] = remapped.astype(index_type).reshape(-1, 1)
                unique = {}
                for i, values in part_replacements.items():
                    if ownership[i] > 1:
                        new = len(doc["accessors"]) + len(rebindings)
                        rebindings[new] = i
                        unique[i] = new
                    else:
                        unique[i] = i
                    replacements[unique[i]] = values
                part["indices"] = unique[part["indices"]]
                part["attributes"] = {key: unique[i] for key, i in attrs.items()}
                note["afterTriangles"] = len(after)
                changed += removed
            except ValueError as error:
                note["rejection"] = str(error)
    return replacements, rebindings, sparse_targets, measurements, total, total - changed


def lossless_budget(doc, binary):
    """Bound payload savings without changing any ordered, fully attributed triangle."""
    spaces = defaultdict(list)
    for index, accessor in enumerate(doc["accessors"]):
        begin = accessor.get("byteOffset", 0)
        spaces[accessor["bufferView"]].append((begin, begin + array(doc, binary, index).nbytes))
    for image in doc.get("images", []):
        if "bufferView" in image:
            index = image["bufferView"]
            spaces[index].append((0, doc["bufferViews"][index]["byteLength"]))
    gaps = 0
    for index, view in enumerate(doc["bufferViews"]):
        end = 0
        for left, right in sorted(spaces[index]):
            gaps += max(0, left - end)
            end = max(end, right)
        gaps += max(0, view["byteLength"] - end)

    unused, identical, narrow = 0, 0, 0
    for mesh in doc["meshes"]:
        for part in mesh["primitives"]:
            attr_ids = [*part["attributes"].values(),
                        *(i for target in part.get("targets", []) for i in target.values())]
            tuples = np.concatenate([array(doc, binary, i).copy().view(np.uint8) for i in attr_ids], axis=1)
            key = np.ascontiguousarray(tuples).view(f"V{tuples.shape[1]}").ravel()
            indices = array(doc, binary, part["indices"]).ravel()
            reachable = np.unique(indices)
            unique = len(np.unique(key[reachable]))
            unused += (len(key) - len(reachable)) * tuples.shape[1]
            identical += (len(reachable) - unique) * tuples.shape[1]
            narrow_width = 1 if unique <= 255 else 2 if unique <= 65_535 else 4
            narrow += max(0, indices.nbytes - narrow_width * len(indices))
    return {"binBytes": len(binary), "unusedVertexBytes": unused, "identicalVertexBytes": identical,
            "indexWidthBytes": narrow, "unusedViewBytes": gaps,
            "upperBoundBytes": unused + identical + narrow + gaps}


def update_accessor(accessor, array_data, offset):
    accessor.update(count=len(array_data), byteOffset=offset)
    if accessor["type"] == "SCALAR":
        accessor["componentType"] = {2: 5123, 4: 5125}[array_data.dtype.itemsize]
    for name, values in (("min", array_data.min(axis=0)), ("max", array_data.max(axis=0))):
        if name in accessor:
            accessor[name] = values.tolist()


def replace_accessors(doc, binary, replacements, rebindings, sparse_targets):
    views = defaultdict(list)
    for i, accessor in enumerate(doc["accessors"]):
        if "bufferView" in accessor:
            views[accessor["bufferView"]].append(i)
    edited = {doc["accessors"][i]["bufferView"] for i in replacements if i not in rebindings}
    # Other references need their entire view. Keep an explicit guard before compaction.
    referenced = {image["bufferView"] for image in doc.get("images", []) if "bufferView" in image}
    for accessor in doc["accessors"]:
        if "sparse" in accessor:
            referenced.update(part["bufferView"] for key, part in accessor["sparse"].items() if key != "count")
    if edited & referenced:
        raise ValueError("Selected buffer view also supplies an image or sparse payload")
    output = bytearray()
    for view_index, view in enumerate(doc["bufferViews"]):
        start = view.get("byteOffset", 0)
        content = binary[start:start + view["byteLength"]]
        view["byteOffset"] = len(output)
        if view_index in edited:
            packed = bytearray()
            last_end = 0
            for i in sorted(views[view_index], key=lambda j: doc["accessors"][j].get("byteOffset", 0)):
                accessor = doc["accessors"][i]
                old = accessor.get("byteOffset", 0)
                width = WIDTHS[accessor["type"]] * np.dtype(TYPES[accessor["componentType"]]).itemsize
                end = old + width * accessor["count"]
                if old < last_end or end > len(content) or view.get("byteStride", width) != width:
                    raise ValueError("Cannot compact overlapping or interleaved accessors")
                last_end = end
                if i in replacements:
                    array_data = replacements[i]
                    update_accessor(accessor, array_data, len(packed))
                    blob = array_data.tobytes()
                else:
                    accessor["byteOffset"] = len(packed)
                    blob = content[old:end]
                packed.extend(blob)
                packed.extend(bytes(-len(packed) % 4))
            content = packed
        view["byteLength"] = len(content)
        output.extend(content)
        output.extend(bytes(-len(output) % 4))
    for new, old in sorted(rebindings.items()):
        accessor = dict(doc["accessors"][old])
        if new != len(doc["accessors"]):
            raise ValueError("Invalid accessor rebinding")
        array_data = replacements[new]
        view = dict(doc["bufferViews"][accessor["bufferView"]])
        view.update(byteOffset=len(output), byteLength=array_data.nbytes)
        accessor["bufferView"] = len(doc["bufferViews"])
        update_accessor(accessor, array_data, 0)
        doc["bufferViews"].append(view)
        doc["accessors"].append(accessor)
        output.extend(array_data.tobytes())
        output.extend(bytes(-len(output) % 4))
    for index, (count, rows) in sparse_targets.items():
        accessor = doc["accessors"][index]
        entry = accessor["sparse"]["indices"]
        accessor["count"] = count
        view = dict(doc["bufferViews"][entry["bufferView"]])
        view.update(byteOffset=len(output), byteLength=rows.nbytes)
        entry.update(bufferView=len(doc["bufferViews"]), byteOffset=0)
        doc["bufferViews"].append(view)
        output.extend(rows.tobytes())
        output.extend(bytes(-len(output) % 4))
    doc["buffers"][0]["byteLength"] = len(output)
    return encode(doc, output)


def verify_streams(control, candidate, replacement_keys, rebindings):
    before, bbin = decode(control)
    after, abin = decode(candidate)
    allowed = {"accessors", "buffers", "bufferViews"}
    for mesh in after["meshes"]:
        for primitive in mesh["primitives"]:
            primitive["indices"] = rebindings.get(primitive["indices"], primitive["indices"])
            primitive["attributes"] = {k: rebindings.get(i, i) for k, i in primitive["attributes"].items()}
    if any(before[k] != after[k] for k in before.keys() - allowed):
        raise ValueError("Scene, mesh, material, attribute or animation bindings changed")
    changed_views = {before["accessors"][i]["bufferView"] for i in replacement_keys if i not in rebindings}
    for index in range(len(before["bufferViews"])):
        if index in changed_views:
            continue
        def payload(doc, buf):
            view = doc["bufferViews"][index]
            begin = view.get("byteOffset", 0)
            return buf[begin:begin + view["byteLength"]]
        if payload(before, bbin) != payload(after, abin):
            raise ValueError(f"Unselected bufferView {index} changed")
    for i, accessor in enumerate(before["accessors"]):
        if i not in replacement_keys and accessor.get("bufferView") in changed_views:
            if array(before, bbin, i).tobytes() != array(after, abin, i).tobytes():
                raise ValueError(f"Unselected accessor {i} changed")


def scene_import(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
    scene = bpy.context.scene
    objects = {o.name: o for o in scene.objects if o.type == "MESH"}
    if not objects:
        raise ValueError(f"No imported meshes for {path}")
    stats = {}
    for n, o in sorted(objects.items()):
        o.data.calc_loop_triangles()
        stats[n] = {
            "transform": [list(r) for r in o.matrix_world],
            "materials": [slot.name for slot in o.material_slots],
            "triangles": len(o.data.loop_triangles),
            "shapeKeys": [key.name for key in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],
        }
        for slot in o.material_slots:
            material = slot.material
            if material and material.node_tree:
                for shader in material.node_tree.nodes:
                    if shader.type == "BSDF_PRINCIPLED" and not shader.inputs["Base Color"].is_linked:
                        material.diffuse_color = shader.inputs["Base Color"].default_value
    return scene, objects, stats


def camera_views(row, scene, objects, folder, side, bindings):
    camera = VIEWS["configure"](scene)
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    result = []
    for index, view in enumerate(row["views"]):
        visible = [o for n, o in objects.items()
                   if not view.get("visible") or re.search(view["visible"], n, re.I)]
        framed = [o for n, o in objects.items()
                  if re.search(view["focus"], n, re.I)] if view.get("focus") else visible
        if not framed:
            raise ValueError(f"No matched focus for {row['name']} {view}")
        direction = view["direction"]
        if bindings is None:
            VIEWS["frame_camera"](camera, framed, direction)
            camera.data.ortho_scale *= view.get("zoom", 1.)
            if "offset" in view:
                camera.location += Vector(view["offset"])
        else:
            binding = bindings[index]
            camera.location = binding["location"]
            camera.rotation_mode = "QUATERNION"
            camera.rotation_quaternion = binding["rotation"]
            camera.data.clip_start = binding["clip"][0]
            camera.data.clip_end = binding["clip"][1]
            camera.data.ortho_scale = binding["ortho"]
        output = folder / f"{side}-{index}.png"
        info = VIEWS["shot"](scene, camera, list(objects.values()), direction, output,
                             view.get("palette", True), visible, fixed=True)
        result.append({"file": output.name, "sha256": info["sha256"], "camera": direction,
                       "location": list(camera.location), "rotation": list(camera.rotation_quaternion),
                       "clip": [camera.data.clip_start, camera.data.clip_end],
                       "ortho": camera.data.ortho_scale})
    return result


def run(row, folder, render):
    path = ROOT / row["path"]
    data = path.read_bytes()
    if identity(data) != {"sha256": row["sha256"], "bytes": row["bytes"]}:
        raise ValueError(f"Wrong or unhydrated control {path}")
    plan = row["plan"]
    candidate_path = folder / "candidate.glb"
    candidate = None
    doc, binary = decode(data)
    measurements = []
    budget = lossless_budget(doc, binary) if row.get("checkLossless") else None
    rebindings = {}
    sparse_targets = {}
    total = sum(doc["accessors"][p["indices"]]["count"] // 3
                for m in doc["meshes"] for p in m["primitives"])
    remaining = total
    if plan == "reuse":
        candidate_path = ROOT / row["candidate"]["path"]
        candidate = candidate_path.read_bytes()
        if identity(candidate) != {k: row["candidate"][k] for k in ("sha256", "bytes")}:
            raise ValueError(f"Wrong or missing recovered option {candidate_path}")
        remaining = row["candidate"]["triangles"]
    elif plan in ("static", "morph"):
        if doc.get("skins") or (plan == "static" and (doc.get("animations") or doc.get("textures"))):
            raise ValueError("Incompatible rig, animation or texture for selected plan")
        if plan == "morph":
            for animation in doc["animations"]:
                if any(c["target"]["path"] != "weights" for c in animation["channels"]):
                    raise ValueError("Expected shape-key-only animation")
                for sampler in animation["samplers"]:
                    weights = array(doc, binary, sampler["output"])
                    if sampler.get("interpolation", "LINEAR") != "LINEAR" or weights.min() < 0 or weights.max() > 1:
                        raise ValueError("Expected bounded scalar linear morph weights")
        replacements, rebindings, sparse_targets, measurements, _, remaining = geometry_replacements(
            row, doc, binary, row["worldSpan"])
    else:
        raise ValueError(f"Unknown plan {plan}")
    rejected_preview = any(note.get("rejectedPreview") for note in measurements)
    if rejected_preview:
        candidate_path = folder / "rejected-preview.glb"
    if plan != "reuse" and replacements:
        candidate = replace_accessors(doc, binary, replacements, rebindings, sparse_targets)
        verify_streams(data, candidate, replacements, rebindings)
        if len(candidate) >= len(data):
            raise ValueError("Candidate bytes did not decrease")
        candidate_path.write_bytes(candidate)

    scene, objects, before = scene_import(path)
    frames = {"control": camera_views(row, scene, objects, folder, "control", None)} if render else {}
    if candidate:
        scene, objects, after = scene_import(candidate_path)
        if before.keys() != after.keys():
            raise ValueError("Selectable mesh names changed on clean import")
        for name, props in before.items():
            if any(after[name][key] != value for key, value in props.items() if key != "triangles"):
                raise ValueError(f"Scene transform, material slots or shape keys changed for {name}")
        visible_triangles_before = sum(p["triangles"] for p in before.values())
        visible_triangles_after = sum(p["triangles"] for p in after.values())
        if visible_triangles_before - visible_triangles_after != total - remaining:
            # Import can collapse pre-existing duplicate faces on either side.
            if abs((visible_triangles_before - visible_triangles_after) - (total - remaining)) > 4:
                raise ValueError("Clean reimport triangle delta exceeds the encoded triangle delta")
        if render:
            frames["candidate"] = camera_views(row, scene, objects, folder, "candidate", frames["control"])
    result = {
        "name": row["name"], "control": {"path": row["path"], **identity(data), "triangles": total},
        "candidate": {"path": str(candidate_path.relative_to(ROOT)), **identity(candidate),
                      "triangles": remaining} if candidate else None,
        "parts": measurements, "bindings": frames, "selectableMeshes": len(before),
        "rejectedPreview": rejected_preview, "losslessBudget": budget,
        "blender": bpy.app.version_string, "build": bpy.app.build_hash.decode(),
    }
    (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--recovered", action="append", default=[], metavar="NAME=PATH")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    rows = json.loads((HERE / "trials.json").read_text())
    selected = [row for row in rows if not args.only or row["name"] in args.only]
    recovered = {}
    for argument in args.recovered:
        name, sep, path = argument.partition("=")
        if not sep or not path:
            parser.error("--recovered requires NAME=PATH")
        recovered[name] = path
    reuse_names = {row["name"] for row in selected if row["plan"] == "reuse"}
    if recovered.keys() - reuse_names:
        parser.error("A recovery path must name a selected owner trial")
    for row in selected:
        if row["name"] in recovered:
            path = Path(recovered[row["name"]]).resolve()
            if not path.is_relative_to(ROOT / ".artifacts"):
                parser.error("A recovered candidate must be in the ignored .artifacts directory")
            row["candidate"]["path"] = str(path.relative_to(ROOT))
    if args.only and set(args.only) != {row["name"] for row in selected}:
        parser.error("Unknown trial name")
    out = args.out.resolve()
    if not out.is_relative_to(ROOT / ".artifacts"):
        parser.error("Choose a new output directory under .artifacts")
    out.mkdir(exist_ok=False, parents=True)
    index = []
    for row in selected:
        folder = out / row["name"]
        folder.mkdir()
        print(f"START {row['name']}", flush=True)
        try:
            result = run(row, folder, not args.no_render)
            index.append(result)
            print(f"DONE {row['name']}", flush=True)
        except (OSError, ValueError) as error:
            index.append({"name": row["name"], "error": str(error)})
            print(f"FAILED {row['name']}: {error}", flush=True)
        (out / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    if any("error" in row for row in index):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
