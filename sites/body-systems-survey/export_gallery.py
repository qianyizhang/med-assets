"""Export the authored system plates into the maintained Body Systems collection. Requires Pillow."""
import argparse
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO
import json
import xml.etree.ElementTree as ET

from gallery_plan import GALLERY, REPO, SOURCE, WORKSHOP_ASSEMBLIES, WORKSHOP_CONFIG, core_scenes, study_records
from report import presentation, workshop_presentation

DISPLAY = REPO / "lessons/body-systems/display"
DISPLAY_INDEX = DISPLAY / "index.json"
REPLAY_BINDINGS = DISPLAY / "replay-bindings.json"


class SystemSections(HTMLParser):
    """Collect the report's published system sections and their captions."""
    def __init__(self):
        super().__init__()
        self.root = ET.Element("systems")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if len(self.stack) == 1 and (tag, attrs.get("class")) != ("section", "system"):
            return
        elem = ET.SubElement(self.stack[-1], tag, attrs)
        if tag not in {"img", "br", "input", "hr", "source"}:
            self.stack.append(elem)

    def handle_data(self, data):
        elem = self.stack[-1]
        if len(elem):
            elem[-1].tail = (elem[-1].tail or "") + data
        else:
            elem.text = (elem.text or "") + data

    def handle_endtag(self, tag):
        if len(self.stack) > 1 and self.stack[-1].tag == tag:
            self.stack.pop()


def words(node):
    return " ".join("".join(node.itertext()).split())


def replay_bindings(index_bytes):
    """Capture the exact proof without making local survey files a Site dependency."""
    previous = json.loads(REPLAY_BINDINGS.read_text())
    known_inputs = {source["path"]: source for source in previous["inputs"]}
    verified = presentation(list(core_scenes()))
    workshop_jobs, workshop_views, _, _ = workshop_presentation()
    verified.update(workshop_views)
    by_pair = {}
    for (scene, view), (folder, data) in verified.items():
        pair = tuple(item["sha256"] for item in data["images"])
        if pair in by_pair:
            raise ValueError(f"Ambiguous Body Systems render pair: {scene}/{view}")
        by_pair[pair] = scene, view, folder, data

    owner = {
        system["id"] + ("-" + prefix.rstrip("/") if prefix else ""): receipt
        for system in json.loads((SOURCE / "systems.json").read_text())
        for receipt, _, _, prefix in study_records(system)
    }
    owner.update({job["id"]: WORKSHOP_CONFIG for job in workshop_jobs})
    scenes, inputs, plates = {}, {}, []
    for system in json.loads(index_bytes):
        for plate in system["plates"]:
            pair = tuple(frame["sourceSha256"] for frame in plate["frames"])
            if pair not in by_pair:
                raise ValueError(f"Body Systems plate has no reviewed render pair: {plate['id']}")
            scene, view, folder, data = by_pair[pair]
            if scene not in scenes:
                receipt = folder / "renders.json"
                pins = json.loads(receipt.read_text())["inputs"]
                scenes[scene] = {
                    "receipt": receipt_identity(receipt),
                    "owner": owner.get(scene, SOURCE / "jobs.json").relative_to(REPO).as_posix(),
                    "inputs": pins,
                    "views": {},
                }
                for pin in pins:
                    path = pin["path"]
                    known = known_inputs.get(path)
                    if known is None or (known["sha256"], known["bytes"]) != (
                        pin["sha256"], (REPO / path).stat().st_size
                    ):
                        raise ValueError(f"Bind the reviewed Body Systems replay input first: {path}")
                    inputs[path] = known
            scenes[scene]["views"][view] = [
                {field: item[field] for field in ("file", "sha256")} for item in data["images"]
            ]
            plates.append({
                "system": system["id"], "kind": plate["kind"], "id": plate["id"],
                "scene": scene, "view": view,
            })

    workshop = previous["workshop"]
    if workshop_jobs:
        workshop = {
            "config": receipt_identity(WORKSHOP_CONFIG),
            "receipt": receipt_identity(WORKSHOP_ASSEMBLIES / "assemblies.json"),
            "maskAudit": receipt_identity(WORKSHOP_ASSEMBLIES / "mask-audit.json"),
        }
    return json.dumps({
        "schemaVersion": 1, "displayIndexSha256": sha256(index_bytes).hexdigest(),
        "inputs": list(inputs.values()), "workshop": workshop, "scenes": scenes, "plates": plates,
    }, ensure_ascii=False, indent=2) + "\n"


def receipt_identity(path):
    return {"path": path.relative_to(REPO).as_posix(), "sha256": sha256(path.read_bytes()).hexdigest()}


def encode_webp(source):
    from PIL import Image

    with Image.open(source) as image, BytesIO() as buffer:
        image.save(buffer, format="WEBP", quality=82, method=6)
        return buffer.getvalue()


def display_bytes(source, destination, approved):
    if approved is not None and destination.is_file():
        data = destination.read_bytes()
        if (sha256(data).hexdigest(), len(data)) == approved:
            return data
    data = encode_webp(source)
    if approved is not None and (sha256(data).hexdigest(), len(data)) != approved:
        raise ValueError(f"Encoder did not reproduce the approved Body Systems WebP: {destination.name}")
    return data


def export():
    DISPLAY.mkdir(exist_ok=True)
    parser = SystemSections()
    parser.feed((GALLERY / "index.html").read_text())
    systems = json.loads((SOURCE / "systems.json").read_text())
    sections = {s.attrib["id"]: s for s in parser.root}
    if set(sections) != {s["id"] for s in systems}:
        raise ValueError("Rebuild the complete Body Systems report first.")
    manifest_path = REPO / "sites/anatomy-gallery/app/src/content/assets/delivery-index.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    prefix = DISPLAY.relative_to(REPO).as_posix() + "/"
    previous_index = DISPLAY_INDEX.read_bytes()
    previous = json.loads(previous_index)
    previous_sources = {
        frame["path"]: frame["sourceSha256"]
        for system in previous for plate in system["plates"] for frame in plate["frames"]
    }
    previous_displays = {
        asset["path"]: (asset["sha256"], asset["bytes"])
        for asset in manifest["assets"] if asset.get("path", "").startswith(prefix)
    }
    assets = [a for a in manifest["assets"] if not a.get("path", "").startswith(prefix)]
    by_hash = {a["sha256"]: a for a in assets}
    output = []
    encoded = {}
    for system in systems:
        key = system["id"]
        section = sections[key]
        entry = dict(id=key, name=system["name"], function=system["function"],
                     status=words(section.find(".//span[@class]")),
                     overview=words(section.find("./p[@class='verdict']")),
                     detail=words(section.find("./details[@class='asset-detail']/p")),
                     limit=words(section.find("./div[@class='gap']/p")),
                     sources=system["sources"], plates=[])
        source_revision = (SOURCE / "revision.txt").read_text().strip()
        owner = system["study"]["owner"]
        owner_url = f"https://github.com/qianyizhang/med-assets/tree/{source_revision}/{owner}"
        for figure in section.findall(".//figure[@data-plate]"):
            kind = figure.attrib["data-plate"]
            caption = figure.find("figcaption")
            plate = dict(kind=kind, title=words(caption[0]), frames=[], legend=[])
            width = caption.find("p[@class='picture-width']")
            if width is not None:
                plate["scale"] = words(width)
            for legend in caption.findall("ul/li"):
                plate["legend"].append([words(legend), legend.find("span").attrib["style"].split(":")[1]])
            for anchor in figure.findall("./div/a[@class='view']"):
                img = anchor.find("img")
                source = GALLERY / img.attrib["src"]
                receipt = json.loads((source.parent / "renders.json").read_text())
                expected = next(i["sha256"] for v in receipt["views"] for i in v["images"] if i["file"] == source.name)
                if sha256(source.read_bytes()).hexdigest() != expected:
                    raise ValueError(f"Changed plate: {source}")
                dest = DISPLAY / (source.parent.name + "-" + source.stem + ".webp")
                path = dest.relative_to(REPO).as_posix()
                if dest not in encoded:
                    approved = previous_displays.get(path) if previous_sources.get(path) == expected else None
                    encoded[dest] = display_bytes(source, dest, approved)
                if not plate["frames"]:
                    plate["id"] = dest.stem.removesuffix("-iso")
                data = encoded[dest]
                digest = sha256(data).hexdigest()
                if digest not in by_hash:
                    asset = dict(path=path, name=dest.name, sha256=digest, bytes=len(data),
                                 mediaType="image/webp", paths=[path])
                    asset["source"] = owner_url
                    asset["attribution"] = "Body Systems teaching render. See the source package and individual model credits."
                    assets.append(asset)
                    by_hash[digest] = asset
                elif path not in by_hash[digest].get("paths", []):
                    raise ValueError(f"Duplicate output at another path: {path}")
                plate["frames"].append(dict(path=path, angle=words(anchor.find("span")), sourceSha256=expected))
            if len(plate["frames"]) != 2:
                raise ValueError("Expected a matched view pair.")
            entry["plates"].append(plate)
        output.append(entry)
    index_bytes = previous_index if output == previous else (
        json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    ).encode()
    replay = replay_bindings(index_bytes)
    compiled_displays = {
        asset["path"]: asset for asset in assets if asset.get("path", "").startswith(prefix)
    }
    ordered_assets = []
    for asset in manifest["assets"]:
        path = asset.get("path", "")
        if path.startswith(prefix):
            if path in compiled_displays:
                ordered_assets.append(compiled_displays.pop(path))
        else:
            ordered_assets.append(asset)
    ordered_assets.extend(compiled_displays.values())
    for dest, data in encoded.items():
        if not dest.is_file() or dest.read_bytes() != data:
            dest.write_bytes(data)
    if index_bytes != previous_index:
        DISPLAY_INDEX.write_bytes(index_bytes)
    if ordered_assets != manifest["assets"]:
        manifest["assets"] = ordered_assets
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    if replay != REPLAY_BINDINGS.read_text():
        REPLAY_BINDINGS.write_text(replay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-replay-bindings", action="store_true",
                        help="Compare the maintained bindings to the local reviewed survey receipts")
    args = parser.parse_args()
    if args.check_replay_bindings:
        expected = replay_bindings(DISPLAY_INDEX.read_bytes())
        if json.loads(expected) != json.loads(REPLAY_BINDINGS.read_text()):
            raise ValueError("Body Systems replay bindings differ from the reviewed survey receipts.")
        print("Body Systems replay bindings match the reviewed survey receipts.")
    else:
        export()
