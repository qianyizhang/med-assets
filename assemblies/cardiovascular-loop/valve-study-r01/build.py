"""Derive a static, selectable valve cutaway from the pinned Atlas export."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from glb import decode, encode

SOURCE = ROOT / "heart/Cardiac_Atlas/exports/Cardiac_Atlas_Clinical_Cutaway_ED.glb"
SOURCE_SHA = "ca35a510737041d538a43cb24f494a1463605bf6b9bd511a01abf52c15bed12a"
STUDY = "heart-valve-cutaway"
SEPTAL_SOURCE = "GLTF Septa • muscular amber"
SEPTAL_NAME = "LV | interventricular septal surface"
MITRAL = "Mitral apparatus"
LIFT_MM = (-5, 12, 0), (5, 12, 0)  # glTF axes; lateral spacing and superior lift

# Linear RGB. Vessels use teaching colors. The chamber walls use tissue cues.
PALETTE = {
    "Epicardium": (0.42, 0.13, 0.14),
    "Endocardium": (0.30, 0.09, 0.095),
    "Cut myocardium": (0.63, 0.25, 0.23),
    "Interventricular septal region": (0.54, 0.28, 0.17),
    "Annular connective tissue": (0.58, 0.30, 0.082),
    "Valve leaflet": (0.86, 0.72, 0.46),
    "Valve leaflet alternate": (0.78, 0.60, 0.36),
    "Chordae tendineae": (0.66, 0.54, 0.33),
    "Papillary muscle": (0.47, 0.16, 0.16),
    "Aortic outflow": (0.57, 0.18, 0.09),
    "Pulmonary outflow": (0.09, 0.32, 0.34),
    "Caval return": (0.07, 0.20, 0.40),
    "Pulmonary venous return": (0.49, 0.16, 0.20),
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def group_for(name):
    if name.startswith(("Mitral valve | ", "LV papillary muscle ", "LV chordae | ")):
        return MITRAL
    if name.startswith(("Tricuspid valve | ", "RV papillary muscle ", "RV chordae | ")):
        return "Tricuspid apparatus"
    if name.startswith("Aortic valve | "):
        return "Aortic valve"
    if name.startswith("Pulmonary valve | "):
        return "Pulmonary valve"
    if name[:2] in {"RA", "RV", "LA", "LV"}:
        return {"RA": "Right atrium", "RV": "Right ventricle",
                "LA": "Left atrium", "LV": "Left ventricle"}[name[:2]]
    if name.endswith("pulmonary vein"):
        return "Pulmonary venous return"
    if name.endswith("vena cava"):
        return "Caval return"
    if name.startswith("Pulmonary trunk") or name.endswith("pulmonary artery"):
        return "Pulmonary outflow"
    if name.startswith(("Aorta | ", "Brachiocephalic trunk")) or name.endswith(
        ("common carotid", "subclavian")
    ):
        return "Aortic outflow"
    raise ValueError(f"No teaching group for {name!r}")


def material_for(source_material, part_name):
    if "papillary muscle" in part_name:
        return "Papillary muscle"
    if part_name.endswith("leaflet 2"):
        return "Valve leaflet alternate"
    owner, _, role = source_material.removeprefix("GLTF ").partition(" • ")
    if role == "low oxygen":
        return {"Pulmonary artery": "Pulmonary outflow", "Vena cava": "Caval return"}[owner]
    return {
        "epicardium": "Epicardium",
        "endocardium": "Endocardium",
        "myocardium": "Cut myocardium",
        "muscular amber": "Interventricular septal region",
        "fibrous ivory": "Valve leaflet",
        "collagen": "Chordae tendineae",
        "systemic arterial": "Aortic outflow",
        "oxygenated": "Pulmonary venous return",
        "Annular connective tissue": "Annular connective tissue",
    }[role or owner]


def organize(document):
    nodes = document["nodes"]
    meshes = document["meshes"]
    root_id, = document["scenes"][document["scene"]]["nodes"]
    root = nodes[root_id]
    wall_id = next(idx for idx in root["children"] if nodes[idx]["name"] == "LV | anterior section")
    wall = nodes[wall_id]
    mesh = meshes[wall["mesh"]]
    names = document["materials"]
    septal_primitive, = (
        p for p in mesh["primitives"] if names[p["material"]]["name"] == SEPTAL_SOURCE
    )
    mesh["primitives"].remove(septal_primitive)
    meshes.append({"name": SEPTAL_NAME, "primitives": [septal_primitive]})
    septum_id = len(nodes)
    nodes.append({
        "name": SEPTAL_NAME,
        "mesh": len(meshes) - 1,
        "extras": {
            "anatomy_id": "cutaway_LV_septal_surface",
            "view_role": "septal surface",
            "source_part": wall["name"],
            "derivation": "Existing septal color region of the anterior LV section",
        },
    })
    groups = {}
    for idx in [*root["children"], septum_id]:
        part = nodes[idx]
        group = group_for(part["name"])
        groups.setdefault(group, []).append(idx)
        extras = part.setdefault("extras", {})
        extras["teaching_group"] = group
        extras["source"] = SOURCE.name
        if idx != septum_id:
            extras["derivation"] = "Source surface at assembled Atlas ED placement"
    root["children"] = []
    for name, children in groups.items():
        root["children"].append(len(nodes))
        nodes.append({"name": name, "children": children,
                      "extras": {"view_role": "reusable anatomy group"}})
    document["asset"]["extras"]["source_cutaway_sha256"] = SOURCE_SHA
    return nodes


def matte(document):
    original = document["materials"]
    document["materials"] = [
        {"name": name, "doubleSided": True,
         "pbrMetallicRoughness": {"baseColorFactor": [*rgb, 1],
                                  "metallicFactor": 0, "roughnessFactor": 0.68}}
        for name, rgb in PALETTE.items()
    ]
    document.pop("extensionsUsed", None)
    index = {name: idx for idx, name in enumerate(PALETTE)}
    for node in document["nodes"]:
        if "mesh" not in node:
            continue
        for p in document["meshes"][node["mesh"]]["primitives"]:
            p["material"] = index[material_for(original[p["material"]]["name"], node["name"])]


def build(out, source=SOURCE):
    if digest(source) != SOURCE_SHA:
        raise ValueError(f"Cardiac Atlas cutaway input identity mismatch for {source.name}")
    document, binary = decode(source.read_bytes())
    nodes = organize(document)
    out.mkdir(parents=True, exist_ok=False)
    (out / "matched-source.glb").write_bytes(encode(document, binary))
    matte(document)
    (out / f"{STUDY}.glb").write_bytes(encode(document, binary))
    for idx, offset in enumerate(LIFT_MM, 1):
        node = next(n for n in nodes if n["name"] == f"Mitral valve | leaflet {idx}")
        node["translation"] = [value / 25 for value in offset]
        node["extras"]["displacement_mm_gltf"] = list(offset)
        node["extras"]["derivation"] = "Illustrative leaflet lift for the comparison plate"
    (out / "mitral-lift-evidence.glb").write_bytes(encode(document, binary))
    print(f"Wrote assembled cutaway, matched palette control and leaflet lift to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=SOURCE, help="Pin-equivalent cutaway source")
    args = parser.parse_args()
    build(args.output, args.source)
