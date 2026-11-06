import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'restore_snapshot', ROOT / 'sites/model-survey/tools/restore_snapshot.py')
restore = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(restore)
digest = lambda value: hashlib.sha256(value).hexdigest()


class SurveyRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'app/src/content/assets'
        self.directory.mkdir(parents=True)
        payload = b'preview-fixture'
        image_hash = digest(payload)
        inline = 'data:image/webp;base64,' + base64.b64encode(payload).decode()
        original = {'id': 'fixture', 'queries': {'one': {'rows': [{'value': 7}], 'source': {'label': 'retained'}}},
                    'previewGallery': {'view': {'image': inline, 'thumb': inline}}}
        self.original = json.dumps(original, ensure_ascii=False, indent=2).encode()
        current = copy.deepcopy(original)
        for kind in ('image', 'thumb'):
            current['previewGallery']['view'][kind] = f'https://example.org/assets/{image_hash}/preview.webp'
        self.immutable = json.dumps(current, ensure_ascii=False, separators=(',', ':')).encode()
        self.source = (json.dumps(current, ensure_ascii=False, indent=2) + '\n').encode()
        self.reference = {'artifactId': 'fixture', 'siteUrl': 'https://example.org',
                          'snapshot': {'sha256': digest(self.original)},
                          'livePublication': {'snapshotSha256': digest(self.immutable),
                                              'snapshotBytes': len(self.immutable),
                                              'sourceSeedSha256': digest(self.source),
                                              'sourceSeedBytes': len(self.source)}}
        (self.root / 'snapshot-reference.json').write_text(json.dumps(self.reference))
        (self.directory / 'r2-trial.json').write_text(json.dumps({'assets': [
            {'sha256': image_hash, 'bytes': len(payload), 'mediaType': 'image/webp', 'name': 'preview.webp'}]}))
        self.input = self.root / 'input.json'
        self.output = self.root / 'restored.json'
        self.scope = patch.object(restore, 'SITE', self.root)
        self.scope.start()
        self.addCleanup(self.scope.stop)

    def test_original_and_immutable_seed_restore_exact_source_without_reordering_queries(self):
        for raw in [self.original, self.immutable]:
            with self.subTest(source=digest(raw)):
                self.input.write_bytes(raw)
                restore.restore(self.input, self.output)
                self.assertEqual(self.output.read_bytes(), self.source)

    def test_equivalent_mutable_response_is_not_an_immutable_source(self):
        data = json.loads(self.immutable)
        queries = data.pop('queries')
        for query in queries.values():
            rows = query.pop('rows')
            query['rows'] = rows
        data['queries'] = queries
        self.input.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
        with self.assertRaises(ValueError):
            restore.restore(self.input, self.output)
        self.assertFalse(self.output.exists())

    def test_other_existing_data_is_not_overwritten(self):
        self.input.write_bytes(self.immutable)
        self.output.write_text('keep')
        with self.assertRaises(ValueError):
            restore.restore(self.input, self.output)
        self.assertEqual(self.output.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
