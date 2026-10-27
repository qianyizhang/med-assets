"""Exercise the shared metadata patch CLI with synthetic GLBs, without LFS."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'tools/patch_scene_metadata.py'


def glb(extras):
    document = {'asset': {'version': '2.0'}, 'scenes': [{'extras': extras, 'nodes': [0]}],
                'nodes': [{'name': 'Unchanged node'}], 'buffers': [{'byteLength': 8}]}
    data = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode()
    data += b' ' * (-len(data) % 4)
    chunks = struct.pack('<II', len(data), 0x4e4f534a) + data
    chunks += struct.pack('<II', 8, 0x004e4942) + b'BIN-data'
    return struct.pack('<4sII', b'glTF', 2, 12 + len(chunks)) + chunks


class SceneMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.glb'
        self.output = self.root / 'new/output.glb'
        self.patch_file = self.root / 'patch.json'
        self.before = glb({f'field{i}': 'old' for i in range(6)})
        self.after = glb({f'field{i}': '新' for i in range(3)})
        self.source.write_bytes(self.before)
        self.patch = {
            'sourceBytes': len(self.before), 'sourceSha256': hashlib.sha256(self.before).hexdigest(),
            'targetBytes': len(self.after), 'targetSha256': hashlib.sha256(self.after).hexdigest(),
            'jsonPointerPatch': [
                dict(op='replace' if i < 3 else 'remove', path=f'/scenes/0/extras/field{i}',
                     oldValue='old', **({'value': '新'} if i < 3 else {})) for i in range(6)]}

    def run_cli(self, optimized=False):
        self.patch_file.write_text(json.dumps(self.patch))
        return subprocess.run([sys.executable, *(['-O'] if optimized else []), str(TOOL),
                               '--patch', str(self.patch_file), str(self.source), str(self.output)],
                              capture_output=True, text=True)

    def assert_rejected(self, message, optimized=False):
        result = self.run_cli(optimized)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr)
        self.assertFalse(self.output.parent.exists())
        self.assertEqual(self.source.read_bytes(), self.before)

    def test_exact_output_preserves_nonmetadata_bytes(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_bytes(), self.after)
        self.assertEqual(json.loads(result.stdout)['sha256'], self.patch['targetSha256'])
        self.assertEqual(self.source.read_bytes(), self.before)

    def test_wrong_source_rejected_even_with_optimization(self):
        self.patch['sourceSha256'] = '0' * 64
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                self.assert_rejected('Source size/SHA-256 mismatch', optimized)

    def test_wrong_old_value_rejected(self):
        self.patch['jsonPointerPatch'][0]['oldValue'] = 'unexpected'
        self.assert_rejected('Old value mismatch')

    def test_outside_extras_rejected(self):
        self.patch['jsonPointerPatch'][0]['path'] = '/nodes/0/name'
        self.assert_rejected('Patch must stay within scene-zero extras')

    def test_unsupported_operation_rejected(self):
        self.patch['jsonPointerPatch'][0]['op'] = 'add'
        self.assert_rejected('Only replace/remove allowed')

    def test_wrong_target_rejected_before_output(self):
        self.patch['targetSha256'] = '0' * 64
        self.assert_rejected('Target size/SHA-256 mismatch')

    def test_existing_output_is_preserved(self):
        self.output.parent.mkdir()
        self.output.write_bytes(b'keep existing output')
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_bytes(), b'keep existing output')
        self.assertEqual(self.source.read_bytes(), self.before)


if __name__ == '__main__':
    unittest.main()
