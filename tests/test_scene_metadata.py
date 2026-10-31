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
ROOT = TOOL.parent.parent
HEART_PATCH = ROOT / 'tests/scene_metadata/heart/approved-patch.json'


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


class HeartMetadataContractTests(unittest.TestCase):
    """Bind the additive correction in an offline text/pointer checkout."""

    def test_exact_source_and_derivative_pointer_identities(self):
        patch = json.loads(HEART_PATCH.read_text())
        expected = (
            ('source', 'body/breathing/heart_breathing.glb', 2037364,
             '3894d51df42a6e5941f0d2b076992d5359279f5e3ddb3b6d4ff6c00f58328086'),
            ('target', 'models/heart/exports/metadata-cleanup-r01/heart.glb', 2037228,
             '50c86dcab55701ca1418e16cd269ded70027663d58d02270ec6df0c8afd488fb'),
        )
        for prefix, path, size, digest in expected:
            with self.subTest(artifact=prefix):
                self.assertEqual((patch[prefix+'Bytes'], patch[prefix+'Sha256']), (size, digest))
                pointer = subprocess.check_output(['git', 'show', ':'+path], cwd=ROOT)
                self.assertEqual(pointer, (
                    f'version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {size}\n'
                ).encode())
        manifest = json.loads((ROOT / 'body/breathing/animation-manifest.json').read_text())
        heart = next(row for row in manifest['assets'] if row['id'] == 'heart')
        self.assertEqual((heart['bytes'], heart['sha256']), expected[0][2:])
        self.assertFalse(heart['cutawaySupport'])
        self.assertEqual(heart['animation']['durationSeconds'], 4)

    def test_reviewed_seven_field_scope_and_retained_attribution(self):
        patch = json.loads(HEART_PATCH.read_text())
        operations = patch['jsonPointerPatch']
        self.assertEqual(len(operations), 7)
        expected = {'README': 'replace', 'coordinates': 'remove',
                    'clinical_status': 'replace', 'reference_phase': 'remove',
                    'material_set_names': 'remove', 'animation_model': 'replace',
                    'pericardial_layers': 'remove'}
        self.assertEqual({op['path']: op['op'] for op in operations},
                         {'/scenes/0/extras/'+key: value for key, value in expected.items()})
        # Shared inherited fields match the earlier reviewed source-derived correction.
        prior = json.loads((ROOT / 'tests/scene_metadata/stomach/approved-patch.json').read_text())
        self.assertEqual({op['path']: op['oldValue'] for op in operations},
                         {op['path']: op['oldValue'] for op in prior['jsonPointerPatch']})
        source_dir = ROOT / 'body/anatomy-workshop-r1/body-3d-source/tb3/presentation/task-explorer/anatomy'
        source = (source_dir / 'heart.json').read_bytes()
        manifest = json.loads((source_dir / 'manifest.json').read_text())['assets']['heart']
        self.assertEqual((len(source), hashlib.sha256(source).hexdigest()),
                         (manifest['bytes'], manifest['asset_sha256']))
        self.assertEqual(json.loads(source)['source_case'], 's1233')
        receipt = json.loads((ROOT / 'body/anatomy-workshop-r1/docs/source-receipts.json').read_text())
        retained = next(row for row in receipt['files'] if row['path'].endswith('/heart.json'))
        self.assertEqual(retained['ref'], '75ec4e6530abe4d434b07958e90bdc9dec062bef')
        blob = b'blob '+str(len(source)).encode()+b'\0'+source
        self.assertEqual(hashlib.sha1(blob).hexdigest(), retained['sha'])


if __name__ == '__main__':
    unittest.main()
