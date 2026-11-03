"""Stdlib guards for pinned editorial replay; no media download or anatomy claim."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools/dental/replay_alignment.py'
spec = importlib.util.spec_from_file_location('replay_alignment', SCRIPT)
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)
IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def glb(doc, tail):
    data = json.dumps(doc, separators=(',', ':')).encode()
    data += b' ' * (-len(data) % 4)
    return (struct.pack('<III', 0x46546C67, 2, 20 + len(data) + len(tail))
            + struct.pack('<II', len(data), 0x4E4F534A) + data + tail)


def fixture():
    doc = {'asset': {'version': '2.0'}, 'scenes': [{'nodes': [0]}],
           'nodes': [{'name': 'Original tooth', 'translation': [1, 2, 3]}]}
    tail = struct.pack('<II', 4, 0x004E4942) + b'abcd'
    source = glb(doc, tail)
    target = copy.deepcopy(doc)
    target['nodes'].append({'name': 'test root', 'matrix': [1, 0, 0, 0, 0, 1, 0, 0,
                                                         0, 0, 1, 0, 0, 0, 0, 1],
                           'children': [0], 'extras': {
                               'role': 'Editorial cross-source placement only; not anatomical registration',
                               'original_sha256': replay.sha(source)}})
    target['scenes'][0]['nodes'] = [1]
    expected = glb(target, tail)
    preset = {'input_sha256': replay.sha(source), 'output_sha256': replay.sha(expected),
              'root_name': 'test root', 'matrix_row_major': IDENTITY}
    return source, preset, expected


class AlignmentReplayTests(unittest.TestCase):
    def test_exact_wrapper_and_binary_preservation(self):
        source, preset, expected = fixture()
        self.assertEqual(replay.align_bytes(source, preset), expected)
        self.assertEqual(source[-12:], expected[-12:])

    def test_matrix_is_serialized_column_major(self):
        source, preset, expected = fixture()
        preset = copy.deepcopy(preset)
        preset['matrix_row_major'][0][3] = 0.25
        length = struct.unpack_from('<I', expected, 12)[0]
        doc = json.loads(expected[20:20 + length])
        doc['nodes'][-1]['matrix'][12] = 0.25
        expected = glb(doc, expected[20 + length:])
        preset['output_sha256'] = replay.sha(expected)
        self.assertEqual(replay.align_bytes(source, preset), expected)

    def test_changed_output_hash_is_rejected(self):
        source, preset, _ = fixture()
        preset = dict(preset, output_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'reviewed placement'):
            replay.align_bytes(source, preset)

    def test_wrong_source_is_rejected(self):
        source, preset, _ = fixture()
        with self.assertRaisesRegex(ValueError, 'Input SHA-256'):
            replay.align_bytes(source[:-1] + b'x', preset)

    def test_lfs_pointer_is_not_geometry(self):
        with self.assertRaisesRegex(ValueError, 'LFS pointer'):
            replay.align_bytes(b'version https://git-lfs.github.com/spec/v1\n', {})

    def test_reflection_shear_nonuniform_and_nan_are_rejected(self):
        for i, j, value in [(0, 0, -1), (0, 1, .2), (1, 1, 2), (2, 2, float('nan'))]:
            matrix = copy.deepcopy(IDENTITY)
            matrix[i][j] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                replay.proper_similarity(matrix)

    def test_bad_header_and_chunks_are_rejected(self):
        source, preset, _ = fixture()
        for bad in [b'bad', source[:-1], source[:12] + struct.pack('<II', 4000, 0x4E4F534A) + source[20:]]:
            test = dict(preset, input_sha256=replay.sha(bad))
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                replay.align_bytes(bad, test)

    def test_presets_share_support_transform_and_exclude_uff(self):
        data = json.loads(replay.PRESETS.read_text())
        presets = data['presets']
        self.assertEqual(set(presets), {'fdi31', 'support35-37', 'pdl35-37'})
        self.assertEqual(presets['support35-37']['matrix_row_major'], presets['pdl35-37']['matrix_row_major'])
        self.assertIn('unknown', data['uff'])
        for preset in presets.values():
            replay.proper_similarity(preset['matrix_row_major'])
            self.assertEqual(len(preset['input_sha256']), 64)
            self.assertEqual(len(preset['output_sha256']), 64)

    def test_cli_never_overwrites_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'keep.glb'
            target.write_bytes(b'keep original')
            run = subprocess.run([sys.executable, str(SCRIPT), 'fdi31', 'absent.glb', str(target)],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('Output already exists', run.stderr)
            self.assertEqual(target.read_bytes(), b'keep original')

    def test_cli_rejects_already_aligned_or_wrong_file_without_output(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'wrong.glb'
            target = Path(d) / 'new.glb'
            source.write_bytes(fixture()[0])
            run = subprocess.run([sys.executable, str(SCRIPT), 'fdi31', str(source), str(target)],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('Input SHA-256', run.stderr)
            self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
