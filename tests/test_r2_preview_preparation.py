import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'prepare_r2_assets', ROOT / 'transport/tools/prepare_r2_assets.py')
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class PreviewPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root / 'app'
        (self.app / 'src/content/assets').mkdir(parents=True)
        self.index = self.app / 'src/content/assets/delivery-index.json'
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
        self.assertEqual(data['thumbnail'], 'https://example.org/assets/' +
                         hashlib.sha256(b'preview-fixture').hexdigest() + '/preview.png')
        self.assertEqual(data['review'], {'anatomy': 'unreviewed', 'source': 'retained'})
        self.assertEqual(json.loads(self.index.read_text())['assets'][0],
                         {'sha256': 'retained-old-object'})

    def test_existing_names_keep_their_routes_and_serve_the_prepared_preview(self):
        raw = b'preview-fixture'
        digest = hashlib.sha256(raw).hexdigest()
        assets = [dict(name=name, sha256=digest, bytes=len(raw), mediaType='image/png')
                  for name in ('original.png', 'alias.png')]
        manifest = {'assets': assets}
        self.index.write_text(json.dumps(manifest))
        self.snapshot.write_text(json.dumps({'thumbnail': 'data:image/png;base64,' + base64.b64encode(raw).decode()}))
        output = self.root / 'objects'
        prepare.prepare(self.app, output, 'https://example.org')
        module = ROOT / 'sites/anatomy-gallery/app/src/content/shared/asset-delivery.js'
        result = subprocess.run(['node', '--input-type=module', '-e', '''
            import assert from 'node:assert/strict';
            import { readFile } from 'node:fs/promises';
            const [module, index, snapshot, payloadPath] = process.argv.slice(1);
            const { createAssetDelivery } = await import(module);
            const manifest = JSON.parse(await readFile(index, 'utf8'));
            const { thumbnail } = JSON.parse(await readFile(snapshot, 'utf8'));
            const [asset] = manifest.assets;
            const bytes = await readFile(payloadPath);
            const env = { BUCKET: {
                head: async () => ({ size: bytes.byteLength, customMetadata: { sha256: asset.sha256 } }),
                get: async () => ({ body: bytes }),
            }};
            const respond = createAssetDelivery(manifest, async () => false);
            const response = await respond(new Request(thumbnail), env);
            assert.equal(response.status, 200);
            assert.deepEqual(Buffer.from(await response.arrayBuffer()), bytes);
        ''', module.as_uri(), str(self.index), str(self.snapshot), str(output / digest)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.index.read_text()), manifest)

    def test_conflicting_catalog_identity_fails_before_preparation(self):
        raw = b'preview-fixture'
        digest = hashlib.sha256(raw).hexdigest()
        asset = dict(name='original.png', sha256=digest, bytes=len(raw) + 1, mediaType='image/png')
        self.index.write_text(json.dumps({'assets': [asset]}))
        self.snapshot.write_text(json.dumps({'thumbnail': 'data:image/png;base64,' + base64.b64encode(raw).decode()}))
        before = self.snapshot.read_bytes(), self.index.read_bytes()
        with self.assertRaisesRegex(ValueError, 'Conflicting delivery size'):
            prepare.prepare(self.app, self.root / 'objects', 'https://example.org')
        self.assertEqual((self.snapshot.read_bytes(), self.index.read_bytes()), before)
        self.assertFalse((self.root / 'objects').exists())

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
