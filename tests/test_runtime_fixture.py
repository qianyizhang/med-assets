"""Fixture preparation and rejection checks; no download or browser execution."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ci'))
import glb_runtime_fixture as fixture
import glb_runtime_probe as runtime


class RuntimeFixtureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config_path = self.root / 'ci/glb-runtime-fixture.json'
        self.config_path.parent.mkdir()
        self.config = json.loads((ROOT / 'ci/glb-runtime-fixture.json').read_text())
        self.source = self.root / self.config['heart']['tracksSource']['file']
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes((ROOT / self.config['heart']['tracksSource']['file']).read_bytes())
        self.write_config()

    def write_config(self):
        self.config_path.write_text(json.dumps(self.config))

    def test_served_fixture_preserves_all_pre_cleanup_bytes(self):
        # Exact /fixture.json body at main 45bcb95, including the esophagus extension.
        expected = 'ee2d705a82681680d1a68d4ecc6ec5b8c5bfe19075a6da9fb78f4e9b42248f33'
        for _ in range(2):
            raw = json.dumps(runtime.load_fixture()).encode()
            self.assertEqual(len(raw), 38076)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)

    def test_fresh_checkout_load_preserves_every_track_and_count(self):
        resolved = fixture.load_fixture(self.root)
        heart = resolved['heart']
        self.assertEqual(heart['tracks'], json.loads(self.source.read_text())['tracks'])
        self.assertEqual(len({t['node'] for t in heart['tracks']}), 228)
        self.assertEqual(sum(len(t['values']) for t in heart['tracks']), 912)
        self.assertEqual(sum(t['renderPrimitives'] for t in heart['tracks']), 232)
        self.assertNotIn('tracksSource', heart)
        self.assertEqual(json.loads(self.config_path.read_text()), self.config)
        heart['tracks'][0]['values'][0] = -1
        self.assertNotEqual(fixture.load_fixture(self.root), resolved)

    def test_missing_and_changed_source_fail(self):
        self.source.write_bytes(self.source.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            fixture.load_fixture(self.root)
        self.source.unlink()
        with self.assertRaises(FileNotFoundError):
            fixture.load_fixture(self.root)

    def test_different_asset_animation_or_counts_fail(self):
        heart_resource = next(r for r in self.config['resources'] if r.get('id') == 'heart')
        for target, key, changed in (
            (heart_resource, 'sha256', '0' * 64), (heart_resource, 'bytes', 1),
            (self.config['heart'], 'animationName', 'different'),
            (self.config['heart'], 'duration', 1), (self.config['heart'], 'times', [0]),
            (self.config['heart'], 'channels', 227),
            (self.config['heart'], 'morphRenderMeshes', 231),
        ):
            with self.subTest(key=key):
                original = target[key]
                target[key] = changed
                self.write_config()
                with self.assertRaises(ValueError):
                    fixture.load_fixture(self.root)
                target[key] = original

    def test_duplicate_tracks_or_external_source_fail(self):
        self.config['heart']['tracks'] = []
        self.write_config()
        with self.assertRaisesRegex(ValueError, 'only in the retained source'):
            fixture.load_fixture(self.root)
        del self.config['heart']['tracks']
        self.config['heart']['tracksSource']['file'] = '../outside.json'
        self.write_config()
        with self.assertRaisesRegex(ValueError, 'inside the repository'):
            fixture.load_fixture(self.root)


if __name__ == '__main__':
    unittest.main()
