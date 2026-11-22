"""Build five teaching editions from exact historical owners into a fresh directory."""

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.glb import buffer_view_bytes, decode, encode, pack_buffer_view

CONTROLS = json.loads((HERE.parent / "refinement-form/controls.json").read_text())
CONTROLS["lymph"] = {
    "path": "models/lymph_node/exports/hra-tissue-layers-r01/lymph-node-tissue-layers.glb",
    "sha256": "bf4ffa85c96459f2666949196915244697f3f5e33ebf485482c8223ba1fcb23e",
}
EDITION = {
    "anatomy-workshop-r1": "body/anatomy-workshop-r1/Anatomy_Workshop_compact.blend",
    "heart": "models/heart/exports/texture-pack-r02/heart.glb",
    "diaphragm": "models/diaphragm/exports/normal-pack-r02/diaphragm.glb",
    "lymph": "models/lymph_node/exports/tissue-color-pack-r02/lymph-node.glb",
    "nose_sinuses": "models/nose_sinuses/exports/index-pack-r02/nasal_airspace.glb",
}


def identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def repack(doc, source, edits):
    result = bytearray()
    for index, view in enumerate(doc["bufferViews"]):
        payload = edits.get(index, buffer_view_bytes(source, view))
        doc["bufferViews"][index] = pack_buffer_view(result, view, payload)
    doc["buffers"][0]["byteLength"] = len(result)
    return encode(doc, result)


def png_streams(doc, binary):
    edits, metrics = {}, []
    for image in doc["images"]:
        view = image["bufferView"]
        source = Image.open(
            io.BytesIO(buffer_view_bytes(binary, doc["bufferViews"][view]))
        )
        out = io.BytesIO()
        source.save(
            out,
            format="PNG",
            optimize=True,
            exif=source.info.get("exif", b""),
            dpi=source.info["dpi"],
        )
        candidate = Image.open(io.BytesIO(out.getvalue()))
        if (
            source.tobytes() != candidate.tobytes()
            or source.mode != candidate.mode
            or source.info != candidate.info
        ):
            raise ValueError("Image sample or metadata changed")
        edits[view] = out.getvalue()
        metrics.append({"name": image["name"], "decoded": identity(source.tobytes())})
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


def normals(doc, binary):
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
    if worst > 0.003:
        raise ValueError("Directional error exceeds 0.003 degrees")
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


def build(key, dest):
    control = CONTROLS[key]
    data = (ROOT / control["path"]).read_bytes()
    if identity(data)["sha256"] != control["sha256"]:
        raise ValueError(f"Wrong source for {key}")
    if key == "anatomy-workshop-r1":
        unpacked = subprocess.check_output(["zstd", "-qdc"], input=data)
        candidate = subprocess.check_output(
            ["zstd", "-q", "-17", "-T1", "-c"], input=unpacked
        )
        if subprocess.check_output(["zstd", "-qdc"], input=candidate) != unpacked:
            raise ValueError("Native Blender stream changed")
        metrics = {"decodedNativeFile": identity(unpacked)}
    else:
        doc, binary = decode(data)
        operation = {
            "heart": png_streams,
            "diaphragm": normals,
            "lymph": colors,
            "nose_sinuses": index_blocks,
        }[key]
        candidate, metrics = operation(doc, binary)
        if key == "nose_sinuses":
            metrics["orderedCornerAttributesSha256"] = verify_triangles(data, candidate)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("xb") as handle:
        handle.write(candidate)
    return {
        "source": {"path": control["path"], **identity(data)},
        "edition": {"path": EDITION[key], **identity(candidate)},
        **metrics,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records = {key: build(key, args.output / path) for key, path in EDITION.items()}
    (args.output / "build.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
