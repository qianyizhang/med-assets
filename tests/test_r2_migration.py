import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import r2_migration as migration
import fetch_asset


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.payload = b'glTF-fixture'
        self.digest = hashlib.sha256(self.payload).hexdigest()
        self.pointer = f'version https://git-lfs.github.com/spec/v1\noid sha256:{self.digest}\nsize {len(self.payload)}\n'.encode()
        self.path = self.root/'model.glb'; self.path.write_bytes(self.pointer)
        (self.root/'large drawing.svg').write_bytes(b'x'*1_000_001)
        self.git('init','-q'); self.git('add','.')
        self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
        self.path.write_bytes(self.payload)

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.root),*args],text=True).strip()

    def test_lfs_and_large_git_blobs_bind_actual_bytes_to_one_revision(self):
        revision, payloads = migration.inventory(self.root,'HEAD')
        self.assertEqual(revision,self.git('rev-parse','HEAD'))
        by_path={p.path:p for p in payloads}
        self.assertEqual(by_path['model.glb'].sha256,self.digest)
        self.assertEqual(by_path['large drawing.svg'].name,'large_drawing.svg')
        self.assertEqual(by_path['large drawing.svg'].mediaType,'application/octet-stream')
        self.assertEqual(sum(p.bytes for p in payloads),1_000_001+len(self.payload))
        self.assertEqual(fetch_asset.pinned_asset(self.root,'HEAD','model.glb'),(self.digest,len(self.payload)))
        blob=by_path['large drawing.svg']
        self.assertEqual(fetch_asset.pinned_asset(self.root,'HEAD',blob.path),(blob.sha256,blob.bytes))

    def test_changed_unhydrated_or_linked_inputs_stop_before_any_transfer(self):
        for body in [b'x'*len(self.payload),self.pointer]:
            self.path.write_bytes(body)
            with self.assertRaises(ValueError): migration.inventory(self.root,'HEAD')
        self.path.unlink(); outside=self.root/'outside';outside.write_bytes(self.payload)
        self.path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'link'):migration.inventory(self.root,'HEAD')

    def test_unknown_large_formats_require_review(self):
        (self.root/'page.html').write_bytes(b'x'*1_000_001)
        self.git('add','page.html');self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','extra')
        with self.assertRaisesRegex(ValueError,'format needs review'):migration.inventory(self.root,'HEAD')

    def test_manifest_keeps_existing_backup_and_merges_content_aliases(self):
        prior={'assets':[{'sha256':'a'*64,'name':'backup.zip','bytes':7,'mediaType':'application/zip'}]}
        original=copy.deepcopy(prior)
        one=migration.Payload('a/model.glb',self.digest,len(self.payload),'model.glb','model/gltf-binary')
        two=migration.Payload('b/alias.glb',self.digest,len(self.payload),'alias.glb','model/gltf-binary')
        result=migration.extend_manifest(prior,'f'*40,[one,two])
        self.assertEqual(prior,original)
        self.assertEqual(result['assets'][0],prior['assets'][0])
        self.assertEqual(len(result['assets']),2)
        self.assertEqual(result['assets'][1]['paths'],['a/model.glb','b/alias.glb'])
        wrong=copy.deepcopy(prior);wrong['assets'].append({'sha256':self.digest,'name':'wrong.png','bytes':99,'mediaType':'image/png'})
        with self.assertRaises(ValueError):migration.extend_manifest(wrong,'f'*40,[one])
