"""Offline backup checker safety and behavior, using synthetic bytes only."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import backup_check as b


class BackupCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.backup = Path(self.temp.name) / 'backup'
        self.backup.mkdir()
        self.payload = b'synthetic payload\0' * 80000
        digest = hashlib.sha256(self.payload).hexdigest()
        self.pointer = (f'version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\n'
                        f'size {len(self.payload)}\n').encode()
        self.contents = {'.gitattributes': b'*.bin filter=lfs -text\n',
                         'README.md': b'ordinary text mentions oid sha256: literally\n',
                         'nested/asset.bin': self.pointer, 'other.bin': self.pointer,
                         'run.sh': b'#!/bin/sh\nexit 0\n'}
        self.command('init', '-q')
        for name, data in self.contents.items():
            self.stage(name, data, '100755' if name == 'run.sh' else '100644')
        self.commit = self.commit_index()
        self.inventory = b.expected_tree(self.root, self.commit)
        for name, data in self.contents.items():
            path = self.backup / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.payload if name.endswith('.bin') else data)

    def command(self, *args, data=None):
        return subprocess.run(['git', *args], cwd=self.root, input=data,
                              env=dict(os.environ, GIT_AUTHOR_NAME='Fixture',
                                       GIT_AUTHOR_EMAIL='fixture@example.invalid',
                                       GIT_COMMITTER_NAME='Fixture',
                                       GIT_COMMITTER_EMAIL='fixture@example.invalid'),
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def stage(self, name, data, mode='100644'):
        oid = self.command('hash-object', '-w', '--stdin', data=data).decode().strip()
        self.command('update-index', '--add', '--cacheinfo', mode, oid, name)

    def commit_index(self):
        tree = self.command('write-tree').decode().strip()
        return self.command('commit-tree', tree, data=b'fixture\n').decode().strip()

    def check(self):
        return b.check(self.inventory, b.Tree(self.backup))

    def status(self, path):
        return {row['path']: row['status'] for row in self.check()['files']}[path]

    def test_exact_commit_and_duplicate_lfs_objects(self):
        self.assertEqual(self.inventory['commit'], self.commit)
        self.assertEqual(self.inventory['lfsPathCount'], 2)
        self.assertEqual(self.inventory['lfsUniqueObjectCount'], 1)
        self.assertEqual(self.inventory['lfsUniqueObjectBytes'], len(self.payload))
        self.assertEqual(len(self.inventory['files']), 5)
        self.assertTrue(self.check()['completeCurrentTree'])
        self.assertEqual(self.check()['plannedCopyBytes'], 0)

    def test_working_tree_index_and_attributes_cannot_change_expectations(self):
        (self.root / '.gitattributes').write_text('* filter=lfs\n')
        (self.root / 'README.md').write_text('dirty\n')
        self.stage('nested/asset.bin', b'broken staged pointer')
        self.stage('.gitattributes', b'* filter=lfs\n')
        self.assertEqual(b.expected_tree(self.root, self.commit), self.inventory)

    def test_missing_text_is_a_gap_even_when_all_media_match(self):
        (self.backup / 'README.md').unlink()
        result = self.check()
        self.assertFalse(result['completeCurrentTree'])
        self.assertEqual(result['counts'], {'verified': 4, 'missing': 1})
        row = next(r for r in result['files'] if r['path'] == 'README.md')
        self.assertEqual(row['action'], 'needs_copy')
        self.assertEqual(result['plannedCopyBytes'], len(self.contents['README.md']))

    def test_pointer_only_and_malformed_pointer_never_pass(self):
        for data in (self.pointer, self.pointer.replace(b'size ', b'malformed ')):
            (self.backup / 'other.bin').write_bytes(data)
            self.assertEqual(self.status('other.bin'), 'pointer_only')
            self.assertFalse(self.check()['completeCurrentTree'])

    def test_same_size_corruption_beyond_prefix_and_size_mismatch(self):
        damaged = bytearray(self.payload)
        damaged[100000] ^= 1
        for data in (damaged, self.payload[:-1], self.payload + b'x'):
            (self.backup / 'other.bin').write_bytes(data)
            self.assertEqual(self.status('other.bin'), 'mismatched')

    def test_missing_parent_and_nonregular_file(self):
        (self.backup / 'nested/asset.bin').unlink()
        (self.backup / 'nested').rmdir()
        self.assertEqual(self.status('nested/asset.bin'), 'missing')
        (self.backup / 'other.bin').unlink()
        os.mkfifo(self.backup / 'other.bin')
        self.assertEqual(self.status('other.bin'), 'unverifiable')

    def test_file_and_parent_symlinks_are_unverifiable(self):
        (self.backup / 'other.bin').unlink()
        (self.backup / 'other.bin').symlink_to(self.backup / 'nested/asset.bin')
        self.assertEqual(self.status('other.bin'), 'unverifiable')
        (self.backup / 'nested/asset.bin').unlink()
        (self.backup / 'nested').rmdir()
        (self.backup / 'nested').symlink_to(self.root, target_is_directory=True)
        self.assertEqual(self.status('nested/asset.bin'), 'unverifiable')

    def zip_bytes(self, extra=()):
        data = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as archive:
                for path in self.backup.rglob('*'):
                    if path.is_file():
                        archive.write(path, path.relative_to(self.backup).as_posix())
                for name, payload in extra:
                    archive.writestr(name, payload)
        data.seek(0)
        return data

    def test_zip_reads_actual_bytes_without_extracting(self):
        before = sorted(str(p) for p in Path(self.temp.name).rglob('*'))
        with zipfile.ZipFile(self.zip_bytes()) as archive:
            result = b.check(self.inventory, b.Zip(archive))
        self.assertTrue(result['completeCurrentTree'])
        self.assertEqual(before, sorted(str(p) for p in Path(self.temp.name).rglob('*')))

    def test_zip_pointer_corruption_and_root_prefix_fail(self):
        (self.backup / 'other.bin').write_bytes(self.pointer)
        (self.backup / 'README.md').write_bytes(b'corrupted')
        with zipfile.ZipFile(self.zip_bytes()) as archive:
            result = b.check(self.inventory, b.Zip(archive))
        statuses = {r['path']: r['status'] for r in result['files']}
        self.assertEqual(statuses['other.bin'], 'pointer_only')
        self.assertEqual(statuses['README.md'], 'mismatched')
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('prefix/README.md', self.contents['README.md'])
        with zipfile.ZipFile(data) as archive:
            self.assertEqual(b.check(self.inventory, b.Zip(archive))['counts'], {'missing': 5})

    def test_zip_traversal_absolute_alias_and_duplicate_refused(self):
        for name in ('../escape', '/absolute', 'a/../b', 'a//b', 'a\\b', 'C:/b',
                     './alias', 'README.md'):
            with self.subTest(name=name), zipfile.ZipFile(self.zip_bytes([(name, b'x')])) as archive:
                with self.assertRaises(ValueError):
                    b.Zip(archive)

    def test_zip_symlink_and_bad_crc_unverifiable(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            entry = zipfile.ZipInfo('other.bin')
            entry.create_system = 3
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(entry, 'target')
        with zipfile.ZipFile(data) as archive:
            expected = next(r for r in self.inventory['files'] if r['path'] == 'other.bin')
            self.assertEqual(b.inspect(b.Zip(archive), expected), 'unverifiable')
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, 'w') as archive:
            archive.writestr('README.md', self.contents['README.md'])
        damaged = raw.getvalue().replace(self.contents['README.md'], b'X' * len(self.contents['README.md']), 1)
        with zipfile.ZipFile(io.BytesIO(damaged)) as archive:
            expected = next(r for r in self.inventory['files'] if r['path'] == 'README.md')
            self.assertEqual(b.inspect(b.Zip(archive), expected), 'unverifiable')
        compressed = io.BytesIO()
        with zipfile.ZipFile(compressed, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('README.md', self.contents['README.md'])
        damaged = bytearray(compressed.getvalue())
        name_length, extra_length = struct.unpack_from('<HH', damaged, 26)
        offset = 30 + name_length + extra_length
        damaged[offset] = (damaged[offset] & ~7) | 7  # Invalid DEFLATE block type.
        with zipfile.ZipFile(io.BytesIO(damaged)) as archive:
            self.assertEqual(b.inspect(b.Zip(archive), expected), 'unverifiable')

    def test_commit_id_required_and_unsupported_git_entries_fail(self):
        for revision in ('HEAD', 'main', self.commit[:7], '-' + self.commit):
            with self.assertRaises(ValueError):
                b.expected_tree(self.root, revision)
        self.stage('link', b'README.md', '120000')
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            b.expected_tree(self.root, self.commit_index())

    def test_malformed_committed_lfs_pointer_fails_closed(self):
        for data in (self.pointer.replace(b'size ', b'broken '), b'not a pointer'):
            self.stage('other.bin', data)
            with self.assertRaisesRegex(ValueError, 'Malformed LFS pointer'):
                b.expected_tree(self.root, self.commit_index())

    def test_local_attribute_override_refused(self):
        (self.root / '.git/info/attributes').write_text('* filter=other\n')
        with self.assertRaisesRegex(ValueError, 'override'):
            b.expected_tree(self.root, self.commit)

    def test_every_git_process_denies_fetch_even_with_permissive_environment(self):
        with patch.dict(os.environ, GIT_ALLOW_PROTOCOL='https:file', GIT_NO_LAZY_FETCH='0'):
            with patch.object(b.subprocess, 'Popen', wraps=subprocess.Popen) as processes:
                self.assertEqual(b.expected_tree(self.root, self.commit), self.inventory)
        self.assertGreaterEqual(len(processes.call_args_list), 5)
        for call in processes.call_args_list:
            self.assertIn('--no-lazy-fetch', call.args[0])
            self.assertEqual(call.kwargs['env']['GIT_ALLOW_PROTOCOL'], '')
            self.assertEqual(call.kwargs['env']['GIT_NO_LAZY_FETCH'], '1')

    def test_older_git_rejects_option_before_any_object_read_or_fetch(self):
        fake_bin = Path(self.temp.name) / 'fake-bin'
        fake_bin.mkdir()
        marker = fake_bin / 'unsafe-object-read'
        executable = fake_bin / 'git'
        executable.write_text(
            '#!' + sys.executable + '\nimport pathlib,sys\n'
            'if "--no-lazy-fetch" in sys.argv:\n'
            '    sys.stderr.write("unknown option: --no-lazy-fetch\\n")\n'
            '    sys.exit(129)\n'
            'pathlib.Path(__file__).with_name("unsafe-object-read").touch()\n'
            'sys.exit(1)\n')
        executable.chmod(0o700)
        args = ['--repo', str(self.root), '--commit', self.commit, '--inventory']
        with patch.dict(os.environ, PATH=str(fake_bin) + os.pathsep + os.environ['PATH']):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(b.main(args), 2)
        self.assertEqual(out.getvalue(), '')
        self.assertFalse(marker.exists())

    def test_missing_promisor_blob_does_not_start_remote_helper(self):
        helper_dir = Path(self.temp.name) / 'remote-helper'
        helper_dir.mkdir()
        marker = helper_dir / 'invoked'
        helper = helper_dir / 'git-remote-backup-test'
        helper.write_text('#!' + sys.executable + '\nimport pathlib,sys\n'
                          'pathlib.Path(__file__).with_name("invoked").touch()\n'
                          'sys.exit(1)\n')
        helper.chmod(0o700)
        self.command('config', 'remote.origin.url', 'backup-test::offline')
        self.command('config', 'remote.origin.promisor', 'true')
        self.command('config', 'protocol.backup-test.allow', 'always')
        oid = self.command('rev-parse', self.commit + ':README.md').decode().strip()
        (self.root / '.git/objects' / oid[:2] / oid[2:]).unlink()
        with patch.dict(os.environ, PATH=str(helper_dir) + os.pathsep + os.environ['PATH']):
            with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                b.expected_tree(self.root, self.commit)
        self.assertFalse(marker.exists())

    def test_cli_inventory_pass_gap_and_error_exit_codes(self):
        base = ['--repo', str(self.root), '--commit', self.commit]
        for args, code in ((['--inventory'], 0), (['--backup-tree', str(self.backup)], 0)):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(b.main(base + args), code)
            self.assertEqual(json.loads(out.getvalue())['commit'], self.commit)
        (self.backup / 'README.md').unlink()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(b.main(base + ['--backup-tree', str(self.backup)]), 1)
        self.assertFalse(json.loads(out.getvalue())['completeCurrentTree'])
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(b.main(base + ['--backup-zip', str(self.backup / 'absent.zip')]), 2)


if __name__ == '__main__':
    unittest.main()
