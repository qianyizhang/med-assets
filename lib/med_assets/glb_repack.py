"""Repack GLB streams while checking the supported encodings and preserved data."""

from collections import Counter
from copy import deepcopy
import hashlib
from io import BytesIO
import math
import struct

from .glb import buffer_view_bytes, decode, encode, pack_buffer_view
from .glb_selection import identity


def optimize_png(data, metadata):
    from PIL import Image

    with Image.open(BytesIO(data), formats=["PNG"]) as image:
        output = BytesIO()
        image.save(output, format="PNG", optimize=True, **metadata)
        return output.getvalue()


def compact_normals(source, max_degrees=.4):
    doc, original = decode(source)
    result = deepcopy(doc)
    attr_views = Counter(a.get("bufferView") for a in doc["accessors"])
    normals = {}
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            index = primitive["attributes"]["NORMAL"]
            accessor = doc["accessors"][index]
            view = accessor["bufferView"]
            if (attr_views[view] != 1 or accessor["componentType"] != 5126 or
                    accessor["type"] != "VEC3" or set(accessor) - {"type", "componentType", "count", "bufferView", "name"}):
                raise ValueError(f"Unsupported normal accessor for {mesh['name']}")
            normals[view] = index, mesh["name"]
    if "extensionsRequired" in doc or "extensionsUsed" in doc:
        raise ValueError("Unexpected existing extension")
    result["extensionsUsed"] = result["extensionsRequired"] = ["KHR_mesh_quantization"]
    payload = bytearray()
    for i, view in enumerate(doc["bufferViews"]):
        data = buffer_view_bytes(original, view)
        new_view = dict(view)
        if i in normals:
            index, _ = normals[i]
            accessor = result["accessors"][index]
            if len(data) != 12 * accessor["count"] or view.get("byteStride", 12) != 12:
                raise ValueError("Unsupported source normal packing")
            packed = bytearray()
            for xyz in struct.iter_unpack("<3f", data):
                if any(not math.isfinite(x) or abs(x) > 1.0001 for x in xyz):
                    raise ValueError("Invalid source normal")
                packed.extend(struct.pack("<3bx", *(round(x * 127) for x in xyz)))
            data = bytes(packed)
            accessor.update(componentType=5120, normalized=True)
            new_view.update(byteStride=4, target=34962)
        result["bufferViews"][i] = pack_buffer_view(payload, new_view, data)
    result["buffers"][0]["byteLength"] = len(payload)
    encoded = encode(result, payload)

    # Decode the actual exported normal streams, including their padding and sign.
    checked, binary = decode(encoded)
    angles = []
    zero_count = 0
    vertex_count = 0
    for i, before in enumerate(doc["bufferViews"]):
        after = checked["bufferViews"][i]
        left = buffer_view_bytes(original, before)
        right = buffer_view_bytes(binary, after)
        if i not in normals:
            if left != right:
                raise ValueError(f"Original geometry or support data changed in view {i}")
            continue
        index, name = normals[i]
        if (checked["accessors"][index]["componentType"] != 5120 or
                checked["accessors"][index].get("normalized") is not True or after["byteStride"] != 4):
            raise ValueError("Incorrect decoded normal declaration")
        worst_angle = 0.
        for a, b in zip(struct.iter_unpack("<3f", left), struct.iter_unpack("<3bx", right), strict=True):
            vertex_count += 1
            if a == (0., 0., 0.) and b == (0, 0, 0):
                zero_count += 1
                continue
            length = math.hypot(*a) * math.hypot(*b)
            if not length:
                raise ValueError("A normal vanished during packing")
            cosine = sum(x * y for x, y in zip(a, b)) / length
            worst_angle = max(worst_angle, math.degrees(math.acos(max(-1., min(1., cosine)))))
        angles.append((worst_angle, name))
    if max(angles)[0] > max_degrees or len(encoded) >= len(source):
        raise ValueError("Angular error or size limit exceeded")
    return encoded, {"normalCount": vertex_count, "sourceZeroNormalsRetained": zero_count,
                     "maxNormalDegrees": round(max(angles)[0], 6), "worstMesh": max(angles)[1],
                     "exactNonNormalViews": len(doc["bufferViews"]) - len(normals)}


def image_data(data, expected_size):
    from PIL import Image

    with Image.open(BytesIO(data), formats=["PNG"]) as image:
        if image.mode not in {"RGB", "RGBA"} or image.size != expected_size:
            raise ValueError("Expected sized RGB or RGBA source texture")
        if set(image.info) - {"exif", "dpi"}:
            raise ValueError("Unexpected PNG metadata requires a color-space check")
        return image.mode, image.tobytes(), image.info.copy()


def compact_png(control, expected_images=3, expected_size=(1024, 1024)):
    doc, binary = decode(control)
    changed = deepcopy(doc)
    if len(doc["buffers"]) != 1 or len(doc["images"]) != expected_images:
        raise ValueError("Unexpected exact source structure")
    image_views = {image["bufferView"]: image for image in doc["images"]}
    payload = bytearray()
    measurements = {}
    for i, view in enumerate(changed["bufferViews"]):
        original = buffer_view_bytes(binary, view)
        data = original
        if i in image_views:
            image_record = image_views[i]
            if image_record["mimeType"] != "image/png":
                raise ValueError("Repack accepts PNG only")
            expected = image_data(original, expected_size)
            data = optimize_png(original, expected[2])
            if image_data(data, expected_size) != expected or len(data) >= len(original):
                raise ValueError("Texture metadata, decoded pixels or encoded saving failed")
            measurements[image_record["name"]] = {
                "original": identity(original),
                "updated": identity(data),
                "decoded": {"mode": expected[0], "size": list(expected_size), **identity(expected[1])},
            }
        changed["bufferViews"][i] = pack_buffer_view(payload, view, data)
    changed["buffers"][0]["byteLength"] = len(payload)
    output = encode(changed, payload)

    result, packed = decode(output)
    if {k: v for k, v in doc.items() if k not in {"buffers", "bufferViews"}} != {
            k: v for k, v in result.items() if k not in {"buffers", "bufferViews"}}:
        raise ValueError("Scene declarations changed")
    for i, (prior, current) in enumerate(zip(doc["bufferViews"], result["bufferViews"], strict=True)):
        if i not in image_views and buffer_view_bytes(binary, prior) != buffer_view_bytes(packed, current):
            raise ValueError(f"Non-image stream {i} changed")
        if i in image_views and image_data(buffer_view_bytes(binary, prior), expected_size) != image_data(buffer_view_bytes(packed, current), expected_size):
            raise ValueError(f"Texture stream {i} changed")
    return output, measurements


def repack(doc, source, edits):
    result = bytearray()
    for index, view in enumerate(doc["bufferViews"]):
        payload = edits.get(index, buffer_view_bytes(source, view))
        doc["bufferViews"][index] = pack_buffer_view(result, view, payload)
    doc["buffers"][0]["byteLength"] = len(result)
    return encode(doc, result)


def png_streams(doc, binary):
    from PIL import Image

    edits, metrics = {}, []
    for image in doc["images"]:
        view = image["bufferView"]
        source = Image.open(
            BytesIO(buffer_view_bytes(binary, doc["bufferViews"][view]))
        )
        packed = optimize_png(buffer_view_bytes(binary, doc["bufferViews"][view]),
                              {"exif": source.info.get("exif", b""), "dpi": source.info["dpi"]})
        candidate = Image.open(BytesIO(packed))
        if (
            source.tobytes() != candidate.tobytes()
            or source.mode != candidate.mode
            or source.info != candidate.info
        ):
            raise ValueError("Image sample or metadata changed")
        edits[view] = packed
        decoded = identity(source.tobytes())
        metrics.append({"name": image["name"], "decoded": {"bytes": decoded["bytes"], "sha256": decoded["sha256"]}})
    return repack(doc, binary, edits), {"identicalPixels": metrics}


def colors(doc, binary):
    edits = {}
    for mesh in doc["meshes"]:
        accessor = doc["accessors"][mesh["primitives"][0]["attributes"]["COLOR_0"]]
        index = accessor["bufferView"]
        data = buffer_view_bytes(binary, doc["bufferViews"][index])
        if data != struct.pack("<4f", 1, 1, 1, 1) * accessor["count"]:
            raise ValueError("Expected four constant 1.0 color components")
        accessor.update(componentType=5121, normalized=True)
        edits[index] = b"\xff" * (4 * accessor["count"])
    return repack(doc, binary, edits), {"normalizedColorsExact": True}


def normals(doc, binary, max_degrees=.003):
    accessor = doc["accessors"][
        doc["meshes"][0]["primitives"][0]["attributes"]["NORMAL"]
    ]
    view_index = accessor["bufferView"]
    view = doc["bufferViews"][view_index]
    data = buffer_view_bytes(binary, view)
    packed = bytearray()
    worst = 0.0
    for vector in struct.iter_unpack("<3f", data):
        coded = [round(v * 32767) for v in vector]
        packed.extend(struct.pack("<3h2x", *coded))
        cosine = sum(v * q for v, q in zip(vector, coded)) / (
            math.hypot(*vector) * math.hypot(*coded)
        )
        worst = max(worst, math.degrees(math.acos(max(-1.0, min(1.0, cosine)))))
    if worst > max_degrees:
        raise ValueError(f"Directional error exceeds {max_degrees} degrees")
    accessor.update(componentType=5122, normalized=True)
    view.update(byteStride=8)
    doc["extensionsUsed"] = list(
        dict.fromkeys([*doc.get("extensionsUsed", []), "KHR_mesh_quantization"])
    )
    doc["extensionsRequired"] = list(
        dict.fromkeys([*doc.get("extensionsRequired", []), "KHR_mesh_quantization"])
    )
    return repack(doc, binary, {view_index: bytes(packed)}), {
        "maxNormalAngleDegrees": worst
    }


def index_blocks(doc, binary):
    """Split the ordered triangle stream before an index needs the reserved ushort 65535."""
    mesh = doc["meshes"][0]
    (original,) = mesh["primitives"]
    indices = doc["accessors"][original["indices"]]
    source_indices = buffer_view_bytes(
        binary, doc["bufferViews"][indices["bufferView"]]
    )
    attributes = {}
    for name, index in original["attributes"].items():
        accessor = doc["accessors"][index]
        if accessor["type"] != "VEC3" or accessor["componentType"] != 5126:
            raise ValueError("Unexpected cast attribute")
        attributes[name] = buffer_view_bytes(
            binary, doc["bufferViews"][accessor["bufferView"]]
        )
    doc["accessors"], doc["bufferViews"], mesh["primitives"] = [], [], []
    result, order, faces = bytearray(), {}, []
    copies = []

    def accessor(values, component_type, kind, count, target, lower, upper):
        index = len(doc["bufferViews"])
        doc["bufferViews"].append(
            pack_buffer_view(result, {"buffer": 0, "target": target}, values)
        )
        doc["accessors"].append(
            {
                "bufferView": index,
                "componentType": component_type,
                "type": kind,
                "count": count,
                "min": lower,
                "max": upper,
            }
        )
        return index

    def flush():
        mapped = {}
        for name, values in attributes.items():
            local = b"".join(values[i * 12 : i * 12 + 12] for i in order)
            points = list(struct.iter_unpack("<3f", local))
            mapped[name] = accessor(
                local,
                5126,
                "VEC3",
                len(order),
                34962,
                list(map(min, zip(*points))),
                list(map(max, zip(*points))),
            )
        index = accessor(
            struct.pack(f"<{len(faces)}H", *faces),
            5123,
            "SCALAR",
            len(faces),
            34963,
            [min(faces)],
            [max(faces)],
        )
        mesh["primitives"].append({**original, "attributes": mapped, "indices": index})
        copies.append(len(order))
        order.clear()
        faces.clear()

    for triangle in struct.iter_unpack("<3I", source_indices):
        if len(order) + len(set(triangle) - order.keys()) > 65535:
            flush()
        for vertex in triangle:
            faces.append(order.setdefault(vertex, len(order)))
    flush()
    doc["buffers"][0]["byteLength"] = len(result)
    return encode(doc, result), {"verticesPerDraw": copies}


def verify_triangles(before, after):
    def fingerprint(data):
        doc, binary = decode(data)
        stream = hashlib.sha256()
        for prim in doc["meshes"][0]["primitives"]:
            attrs = [
                doc["accessors"][prim["attributes"][key]]
                for key in ("POSITION", "NORMAL")
            ]
            arrays = [
                buffer_view_bytes(binary, doc["bufferViews"][a["bufferView"]])
                for a in attrs
            ]
            indices = doc["accessors"][prim["indices"]]
            encoded = buffer_view_bytes(
                binary, doc["bufferViews"][indices["bufferView"]]
            )
            for (i,) in struct.iter_unpack(
                {5123: "<H", 5125: "<I"}[indices["componentType"]], encoded
            ):
                for array in arrays:
                    stream.update(array[i * 12 : i * 12 + 12])
        return stream.hexdigest()

    digest = fingerprint(before)
    if fingerprint(after) != digest:
        raise ValueError("Ordered triangle corners changed")
    return digest
