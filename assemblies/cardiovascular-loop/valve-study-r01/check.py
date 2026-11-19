"""Verify source geometry, reuse grouping, illustrative offsets and render bindings."""
import argparse
from collections import Counter
import json
from pathlib import Path

from build import LIFT_MM, MITRAL, SEPTAL_NAME, SEPTAL_SOURCE, SOURCE, SOURCE_SHA, STUDY, decode, digest

EXPECTED_VALVES = {"Tricuspid": 3, "Pulmonary": 3, "Mitral": 2, "Aortic": 3}
TRANSFORMS = {"matrix", "rotation", "scale", "translation"}


def require(value, problem):
    if not value:
        raise ValueError(problem)


def parts(document, *, grouped=False, offsets=None):
    nodes = document["nodes"]
    root_id, = document["scenes"][document["scene"]]["nodes"]
    root = nodes[root_id]
    require(root["scale"] == [0.025] * 3 and TRANSFORMS.intersection(root) == {"scale"},
            "Atlas metre conversion changed")
    counts = Counter()
    positions = []
    groups = [nodes[idx] for idx in root["children"]] if grouped else []
    if grouped:
        require(all("mesh" not in node and not TRANSFORMS.intersection(node) for node in groups),
                "Unexpected transform or geometry on a teaching group")
        part_ids = [idx for group in groups for idx in group["children"]]
        mitral, = (group for group in groups if group["name"] == MITRAL)
        members = {nodes[idx]["name"] for idx in mitral["children"]}
        require(len(members) == 25 and sum(name.startswith("LV chordae | ") for name in members) == 20,
                "Reusable mitral set must include 20 chordae, two papillary muscles, two leaflets and annulus")
    else:
        part_ids = root["children"]
    require(len(set(part_ids)) == len(part_ids), "Part has multiple parents")
    for idx in part_ids:
        node = nodes[idx]
        name = node["name"]
        expected = {"translation": offsets[name]} if offsets and name in offsets else {}
        require({key: node[key] for key in TRANSFORMS & node.keys()} == expected,
                f"Unexpected part transform for {name}")
        counts[name] += 1
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            material = document["materials"][primitive["material"]]["name"]
            owner = "LV | anterior section" if name == SEPTAL_NAME else name
            if name == SEPTAL_NAME:
                require(material in {SEPTAL_SOURCE, "Interventricular septal region"},
                        "Septal mesh must use its source region or derivative material")
            positions.append((owner, json.dumps(
                {key: value for key, value in primitive.items() if key != "material"},
                sort_keys=True,
            )))
    require(all(count == 1 for count in counts.values()), "Duplicate anatomical mesh name")
    for valve, count in EXPECTED_VALVES.items():
        require(
            f"{valve} valve | annulus" in counts
            and sum(name.startswith(f"{valve} valve | leaflet ") for name in counts) == count,
            f"Valve set differs for {valve}",
        )
    return Counter(positions)


def checked_views(folder, asset):
    receipt = json.loads((folder / "renders.json").read_text())
    require(receipt["glb"] == asset.name and receipt["sha256"] == digest(asset)
            and receipt["viewsSha256"] == digest(Path(__file__).with_name("views.json")),
            f"Inputs differ from {folder.name} receipt")
    views = {}
    for view in receipt["views"]:
        require(view["id"] not in views, f"Repeated view in {folder.name}")
        views[view["id"]] = view
        images = view["images"]
        require([entry["file"] for entry in images] == [
            f"{view['id']}-iso.png", f"{view['id']}-ortho.png"], "Wrong render filenames")
        for entry in images:
            require(digest(folder / entry["file"]) == entry["sha256"], f"Image changed: {entry['file']}")
    return views


def camera(view):
    return (view["orthographicScale"], [(p["camera"], p["direction"]) for p in view["images"]])


def check(work):
    build = work / "build"
    require(digest(SOURCE) == SOURCE_SHA, "Atlas source identity changed")
    source, binary = decode(SOURCE.read_bytes())
    original = parts(source)
    variants = [
        ("renders", f"{STUDY}.glb", None),
        ("matched-source", "matched-source.glb", None),
        ("displaced", "mitral-lift-evidence.glb", {
            f"Mitral valve | leaflet {i}": [value / 25 for value in offset]
            for i, offset in enumerate(LIFT_MM, 1)
        }),
    ]
    receipts = []
    for folder, filename, offsets in variants:
        path = build / filename
        model, payload = decode(path.read_bytes())
        require(payload == binary and all(model[key] == source[key] for key in ("accessors", "bufferViews", "buffers")),
                f"Changed geometry payload in {filename}")
        require(parts(model, grouped=True, offsets=offsets) == original, f"Source primitives changed in {filename}")
        receipts.append(checked_views(work / folder, path))
    updated, baseline, displaced = receipts
    ids = {row["id"] for row in json.loads(Path(__file__).with_name("views.json").read_text())}
    require(set(updated) == set(baseline) == ids and set(displaced) == {"mitral-displaced"},
            "Expected comparison views missing")
    for key in updated:
        require(camera(updated[key]) == camera(baseline[key])
                and updated[key]["visible"] == baseline[key]["visible"]
                and updated[key]["bounds"] == baseline[key]["bounds"],
                f"Control framing or selection changed for {key}")
    require(camera(updated["mitral-seated"]) == camera(displaced["mitral-displaced"])
            and updated["mitral-seated"]["visible"] == displaced["mitral-displaced"]["visible"],
            "Leaflet lift must use the seated camera and group")
    print(f"{sum(original.values())} exact source primitives, four valve sets, 25-part mitral group, "
          "two deliberate evidence-only offsets and 18 clean-import image identities verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    check(parser.parse_args().work)
