"""Export the authored system plates into the maintained Body Systems collection. Requires Pillow."""
from hashlib import sha256
from html.parser import HTMLParser
import json
import xml.etree.ElementTree as ET

from PIL import Image
from gallery_plan import GALLERY, SOURCE, REPO


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


def export():
    display = REPO / "lessons/body-systems/display"
    display.mkdir(exist_ok=True)
    parser = SystemSections()
    parser.feed((GALLERY / "index.html").read_text())
    systems = json.loads((SOURCE / "systems.json").read_text())
    sections = {s.attrib["id"]: s for s in parser.root}
    if set(sections) != {s["id"] for s in systems}:
        raise ValueError("Rebuild the complete Body Systems report first.")
    manifest_path = REPO / "sites/anatomy-gallery/app/src/content/assets/delivery-index.json"
    manifest = json.loads(manifest_path.read_text())
    prefix = display.relative_to(REPO).as_posix() + "/"
    assets = [a for a in manifest["assets"] if not a.get("path", "").startswith(prefix)]
    by_hash = {a["sha256"]: a for a in assets}
    output = []
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
                dest = display / (source.parent.name + "-" + source.stem + ".webp")
                with Image.open(source) as image:
                    image.save(dest, format="WEBP", quality=82, method=6)
                if not plate["frames"]:
                    plate["id"] = dest.stem.removesuffix("-iso")
                data = dest.read_bytes()
                digest = sha256(data).hexdigest()
                path = dest.relative_to(REPO).as_posix()
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
    (display / "index.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    manifest["assets"] = assets
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    export()
