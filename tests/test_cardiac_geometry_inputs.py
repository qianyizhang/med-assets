import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / 'heart/Cardiac_Atlas'
module = importlib.util.spec_from_file_location('atlas_geometry_inputs', ATLAS / 'geometry_inputs.py')
geometry = importlib.util.module_from_spec(module)
module.loader.exec_module(geometry)


class CardiacInputTests(unittest.TestCase):
    def test_compressed_and_portable_layouts_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp).resolve()
            source = ATLAS / 'exports'
            contract = source / 'EXPORT_CONTRACT.json'
            (package / contract.name).write_bytes(contract.read_bytes())
            pins = json.loads(contract.read_text())['sha256']
            for name in geometry.GEOMETRY:
                (package / (name + '.gz')).write_bytes((source / (name + '.gz')).read_bytes())
            geometry.ensure_geometry_exports(package)
            for name in geometry.GEOMETRY:
                self.assertEqual(hashlib.sha256((package / name).read_bytes()).hexdigest(), pins[name])
                (package / (name + '.gz')).unlink()
            geometry.ensure_geometry_exports(package)
            (package / 'anatomy_details.json').write_bytes(b'edited')
            with self.assertRaisesRegex(ValueError, 'differs from its contract'):
                geometry.ensure_geometry_exports(package)
            self.assertEqual((package / 'anatomy_details.json').read_bytes(), b'edited')

    def test_bad_second_member_preserves_empty_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp).resolve()
            source = ATLAS / 'exports'
            for name in ['EXPORT_CONTRACT.json', 'anatomy_meshes.json.gz']:
                (package / name).write_bytes((source / name).read_bytes())
            (package / 'anatomy_details.json.gz').write_bytes(gzip.compress(b'incorrect'))
            with self.assertRaisesRegex(ValueError, 'differs from its contract'):
                geometry.ensure_geometry_exports(package)
            self.assertFalse((package / 'anatomy_meshes.json').exists())
