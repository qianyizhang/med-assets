import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'transport/tools'))
from delivery_catalog import DELIVERY_INDEX, assets_by_path
import fetch_asset
import r2_migration as migration


class MigrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.payload = b'glTF-fixture'
        self.digest = hashlib.sha256(self.payload).hexdigest()
        self.pointer = (f'version https://git-lfs.github.com/spec/v1\noid sha256:{self.digest}\n'
                        f'size {len(self.payload)}\n').encode()
        self.path = self.root / 'model.glb'
        self.path.write_bytes(self.pointer)
        (self.root / 'large drawing.svg').write_bytes(b'x' * 1_000_001)
        self.git('init', '-q')
        self.commit()
        self.path.write_bytes(self.payload)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')

    def plan(self, *paths):
        return migration.plan_upload(self.root, 'HEAD', {'assets': []}, list(paths), [])

    def test_lfs_and_large_git_blobs_bind_actual_bytes_to_one_revision(self):
        plan, catalog = self.plan('model.glb', 'large drawing.svg')
        self.assertEqual(plan['revision'], self.git('rev-parse', 'HEAD'))
        self.assertEqual(plan['objectCount'], 2)
        self.assertEqual(plan['totalBytes'], 1_000_001 + len(self.payload))
        by_path = assets_by_path(catalog)
        selected = {item['sourcePath']: item for item in plan['objects']}
        self.assertEqual(by_path['model.glb']['sha256'], self.digest)
        blob = by_path['large drawing.svg']
        self.assertEqual(blob['name'], 'large_drawing.svg')
        self.assertEqual(blob['mediaType'], 'application/octet-stream')
        for name, item in selected.items():
            self.assertEqual(fetch_asset.pinned_asset(self.root, 'HEAD', name), (item['sha256'], item['bytes']))

    def test_changed_unhydrated_or_linked_inputs_are_refused(self):
        for body in [b'x' * len(self.payload), self.pointer]:
            self.path.write_bytes(body)
            with self.assertRaises(ValueError):
                self.plan('model.glb')
        self.path.unlink()
        outside = self.root / 'outside'
        outside.write_bytes(self.payload)
        self.path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'link'):
            self.plan('model.glb')

    def test_select_before_inspecting_unselected_payloads(self):
        unknown = self.root / 'page.html'
        unknown.write_bytes(b'x' * 1_000_001)
        self.path.write_bytes(self.pointer)
        self.commit()
        unknown.unlink()
        self.path.write_bytes(self.payload)
        plan, _ = self.plan('model.glb')
        self.assertEqual(plan['objectCount'], 1)
        with self.assertRaisesRegex(ValueError, 'format needs review'):
            self.plan('page.html')

    def test_catalog_keeps_original_address_and_git_pinned_recovery(self):
        old_revision = self.git('rev-parse', 'HEAD')
        old_url_name = 'approved_original_filename.glb'
        old = {'path': 'model.glb', 'name': old_url_name, 'sha256': self.digest,
               'bytes': len(self.payload), 'mediaType': 'model/gltf-binary'}
        alternate = {**old, 'name': 'alternate.glb', 'path': 'alternate.glb'}
        original = {'assets': [alternate, old], 'repositoryPayloads': {'count': 694}}
        self.path.write_bytes(b'glTF-changed')
        self.commit()
        plan, updates = migration.plan_upload(self.root, 'HEAD', original, ['model.glb'], [])
        self.assertEqual(len(updates['assets']), 3)
        self.assertEqual(updates['repositoryPayloads'], original['repositoryPayloads'])
        self.assertEqual(updates['assets'][0], alternate)
        self.assertEqual(updates['assets'][1]['name'], old_url_name)
        self.assertEqual(updates['assets'][1]['historicalPaths'], ['model.glb'])
        manifest = self.root / DELIVERY_INDEX
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps(updates))
        digest, size = fetch_asset.pinned_asset(self.root, old_revision, 'model.glb')
        self.assertEqual(fetch_asset.route_name(self.root, digest, size, 'model.glb'), old_url_name)
        new = plan['objects'][0]
        self.assertEqual(fetch_asset.route_name(self.root, new['sha256'], new['bytes'], 'model.glb'), 'model.glb')

    def test_plan_rejects_unbounded_selection_stale_commit_and_retiring_live_paths(self):
        with self.assertRaisesRegex(ValueError, 'distinct'):
            self.plan(*(f'{index}.glb' for index in range(33)))
        with self.assertRaisesRegex(ValueError, 'repository-relative'):
            self.plan('../model.glb')
        self.path.write_bytes(self.pointer)
        plan, catalog = self.plan('large drawing.svg')
        with self.assertRaisesRegex(ValueError, 'absent from Git HEAD'):
            migration.plan_upload(self.root, 'HEAD', catalog, [], ['large drawing.svg'])
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--allow-empty', '-qm', 'new revision')
        with self.assertRaisesRegex(ValueError, 'revision differs'):
            migration.plan_upload(self.root, plan['revision'], catalog, ['large drawing.svg'], [])

    def test_oversized_committed_lfs_pointer_stops_before_reading_any_working_bytes(self):
        (self.root / 'huge.glb').write_bytes(self.pointer.replace(f'size {len(self.payload)}'.encode(), b'size 64000001'))
        self.path.write_bytes(self.pointer)
        self.commit()
        self.path.unlink()
        with self.assertRaisesRegex(ValueError, 'byte bound'):
            self.plan('model.glb', 'huge.glb')
