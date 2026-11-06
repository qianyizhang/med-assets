import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'prepare_r2_assets', ROOT / 'sites/model-survey/tools/prepare_r2_assets.py')
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class PreviewPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root / 'app'
        (self.app / 'src/content/assets').mkdir(parents=True)
        self.index = self.app / 'src/content/assets/r2-trial.json'
        self.snapshot = self.app / 'src/data.json'
        self.index.write_text('{"assets": [{"sha256": "retained-old-object"}]}')

    def test_shared_preview_bytes_are_deduplicated_without_changing_review_metadata(self):
        inline = 'data:image/png;base64,' + base64.b64encode(b'preview-fixture').decode()
        self.snapshot.write_text(json.dumps({'thumbnail': inline, 'gallery': [inline],
                                            'review': {'anatomy': 'unreviewed', 'source': 'retained'}}))
        result = prepare.prepare(self.app, self.root / 'objects', 'https://example.org')
        self.assertEqual(result['preparedObjects'], 1)
        self.assertFalse(result['transferred'])
        files = list((self.root / 'objects').iterdir())
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].read_bytes(), b'preview-fixture')
        data = json.loads(self.snapshot.read_text())
        self.assertEqual(data['thumbnail'], data['gallery'][0])
        self.assertEqual(data['review'], {'anatomy': 'unreviewed', 'source': 'retained'})
        self.assertEqual(json.loads(self.index.read_text())['assets'][0],
                         {'sha256': 'retained-old-object'})

    def test_malformed_image_leaves_source_and_existing_manifest_intact(self):
        self.snapshot.write_text('{"image": "data:image/png;base64,invalid!"}')
        before = self.snapshot.read_bytes(), self.index.read_bytes()
        with self.assertRaises(ValueError):
            prepare.prepare(self.app, self.root / 'objects', 'https://example.org')
        self.assertEqual((self.snapshot.read_bytes(), self.index.read_bytes()), before)
        self.assertFalse((self.root / 'objects').exists())

    def test_existing_output_directory_is_not_reused_or_overwritten(self):
        self.snapshot.write_text('{"review": "retained"}')
        output = self.root / 'objects'
        output.mkdir()
        (output / 'retained-file').write_text('keep')
        before = self.snapshot.read_bytes(), self.index.read_bytes()
        with self.assertRaises(FileExistsError):
            prepare.prepare(self.app, output, 'https://example.org')
        self.assertEqual((self.snapshot.read_bytes(), self.index.read_bytes()), before)
        self.assertEqual((output / 'retained-file').read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
