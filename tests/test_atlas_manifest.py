"""The atlas's current image contract must resolve without generated thumbnails."""
import hashlib
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


PACKAGE = Path(__file__).resolve().parents[1] / 'body/2d-v4/whole-body-anatomy-v4-spatial'
SVG = 'http://www.w3.org/2000/svg'


class AtlasManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((PACKAGE / 'manifest.json').read_text())

    def test_current_sources_and_exports_match_manifest(self):
        entries = [self.manifest['atlas'], self.manifest['overview'],
                   *self.manifest['sources'].values()]
        for family in ('parts', 'variants', 'overlays', 'regions'):
            entries.extend(self.manifest[family])
        for entry in entries:
            with self.subTest(file=entry['file']):
                path = (PACKAGE / entry['file']).resolve()
                self.assertTrue(path.is_relative_to(PACKAGE.resolve()))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'])

    def test_every_preview_is_a_self_contained_image(self):
        for family in ('parts', 'variants', 'overlays', 'regions'):
            for entry in self.manifest[family]:
                with self.subTest(family=family, id=entry['id']):
                    preview = entry['preview']
                    self.assertFalse(urlsplit(preview).scheme)
                    path = (PACKAGE / preview).resolve()
                    self.assertTrue(path.is_relative_to(PACKAGE.resolve()))
                    root = ET.fromstring(path.read_bytes())
                    self.assertEqual(root.tag, '{' + SVG + '}svg')
                    bounds = [float(v) for v in root.attrib['viewBox'].split()]
                    self.assertEqual(len(bounds), 4)
                    self.assertGreater(bounds[2], 0)
                    self.assertGreater(bounds[3], 0)
                    ids = {node.attrib['id'] for node in root.iter() if 'id' in node.attrib}
                    for node in root.iter():
                        self.assertNotIn(node.tag, ('{' + SVG + '}script', '{' + SVG + '}foreignObject'))
                        for key, value in node.attrib.items():
                            if key.rsplit('}', 1)[-1] == 'href':
                                self.assertTrue(value.startswith('#'), value)
                                self.assertIn(value[1:], ids)
                            for target in re.findall(r'url\([\s\"\']*([^\)\s\"\']+)', value):
                                self.assertTrue(target.startswith('#'), target)
                                self.assertIn(target[1:], ids)

    def test_selection_ids_and_primary_mapping_are_consistent(self):
        parts = self.manifest['parts']
        ids = [entry['id'] for entry in parts]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), set(self.manifest['canonical_ids']))
        for entry in parts:
            self.assertEqual(self.manifest['canonical_to_assets'][entry['id']]['primary'], entry['file'])


if __name__ == '__main__':
    unittest.main()
