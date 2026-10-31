"""Offline safety and matched-view checks; no media download or browser claim."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("brain_source_cut_build", ROOT / "tools/brain_source_cut/build.py")
build = importlib.util.module_from_spec(loader)
loader.loader.exec_module(build)
SVG = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}href"


class BrainSourceCutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        spec = copy.deepcopy(build.SPEC)
        doc = {"meshes": [{} for _ in range(49)], "nodes": [
            {"name": "medulla oblongata | FJ1769"}, {"name": "medulla oblongata | FJ1831"}]}
        payload = json.dumps(doc).encode()
        glb = struct.pack("<4sIIII", b"glTF", 2, 20 + len(payload), len(payload), 0x4E4F534A) + payload
        # This fixture exercises identity/shape gates, not PNG decoding. Actual
        # retained PNG decoding/rendering is the separate native evidence check.
        png = b"\x89PNG\r\n\x1a\n" + b"\0" * 8 + struct.pack(">II", 2100, 1586)
        for kind, data in [("model", glb), ("image", png)]:
            p = self.root / spec[kind]["file"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            spec[kind].update(bytes=len(data), sha256=build.sha(data))
        self.spec = spec
        self.patch = patch.object(build, "SPEC", spec)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_altered_inputs_fail_before_output(self):
        for kind in ("model", "image"):
            with self.subTest(kind=kind):
                path = self.root / self.spec[kind]["file"]
                original = path.read_bytes()
                path.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
                output = self.root / ("bad-" + kind)
                with self.assertRaisesRegex(ValueError, "identity mismatch"):
                    build.build(self.root, output)
                self.assertFalse(output.exists())
                path.write_bytes(original)

    def test_missing_source_does_not_create_partial_presentation(self):
        (self.root / self.spec["image"]["file"]).unlink()
        with self.assertRaises(FileNotFoundError):
            build.build(self.root, self.root / "missing")
        self.assertFalse((self.root / "missing").exists())

    def test_replay_and_input_preservation(self):
        before = {k: (self.root / self.spec[k]["file"]).read_bytes() for k in ("model", "image")}
        first = build.build(self.root, self.root / "first", embed=True)
        second = build.build(self.root, self.root / "second", embed=True)
        self.assertEqual(first, second)
        self.assertTrue(first["modelBytesUnchanged"])
        for kind, data in before.items():
            self.assertEqual(data, (self.root / self.spec[kind]["file"]).read_bytes())

    def test_existing_output_is_retained(self):
        output = self.root / "retained"
        output.mkdir()
        (output / "trial.txt").write_text("keep failed trials")
        with self.assertRaises(FileExistsError):
            build.build(self.root, output)
        self.assertEqual((output / "trial.txt").read_text(), "keep failed trials")

    def test_matched_pairs_share_one_image_and_crop_transform(self):
        for view in self.spec["views"]:
            svg = ET.fromstring(build.comparison("source.png", view))
            self.assertEqual(len(svg.findall(".//" + SVG + "image")), 1)
            panels = [g for g in svg.findall(".//" + SVG + "g") if "data-crop" in g.attrib]
            self.assertEqual(len(panels), 4)
            for kind in ("overview", "detail"):
                pair = [g for g in panels if g.get("data-crop") == kind]
                self.assertEqual([g.get("data-variant") for g in pair], ["original", "updated"])
                transforms = [g.find(SVG + "g").get("transform").split("scale", 1)[1] for g in pair]
                self.assertEqual(*transforms)
                for panel in pair:
                    self.assertTrue(panel.get("clip-path").startswith("url(#clip-"))
                    self.assertEqual(panel.find(".//" + SVG + "use").get(XLINK), "#source")
                    cues = [g for g in panel.iter(SVG + "g") if g.get("data-editorial")]
                    self.assertEqual(len(cues), int(panel.get("data-variant") == "updated"))

    def test_both_medulla_nodes_are_required(self):
        p = self.root / self.spec["model"]["file"]
        data = p.read_bytes().replace(b"FJ1831", b"FJ0000")
        p.write_bytes(data)
        self.spec["model"]["sha256"] = build.sha(data)
        with self.assertRaisesRegex(ValueError, "both retained medulla"):
            build.verify_inputs(self.root)


if __name__ == "__main__":
    unittest.main()
