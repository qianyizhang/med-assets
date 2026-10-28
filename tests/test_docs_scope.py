import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('docs_scope', Path(__file__).resolve().parents[1] / 'tools/docs_scope.py')
scope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope)


class ScopeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.getcwd()
        os.chdir(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        Path('CONTRIBUTING.md').write_text('Prose\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD')

    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', *args], text=True).strip()

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-qm', 'change')
        return self.git('rev-parse', 'HEAD')

    def test_prose(self):
        Path('CONTRIBUTING.md').write_text('Changed prose\n')
        self.assertTrue(scope.docs_only(self.base, self.commit()))

    def test_mixed_and_unknown(self):
        Path('CONTRIBUTING.md').write_text('Changed\n')
        Path('unknown.md').write_text('Unknown\n')
        self.assertFalse(scope.docs_only(self.base, self.commit()))

    def test_rename_and_delete(self):
        Path('CONTRIBUTING.md').rename('unknown.md')
        self.assertFalse(scope.docs_only(self.base, self.commit()))
        Path('unknown.md').unlink()
        self.assertFalse(scope.docs_only(self.base, self.commit()))

    def test_delete_allowed_and_missing_base(self):
        Path('CONTRIBUTING.md').unlink()
        head = self.commit()
        self.assertFalse(scope.docs_only(self.base, head))
        self.assertFalse(scope.docs_only('missing-base', head))
        self.assertFalse(scope.docs_only(head, head))

    def test_symlink_and_unsafe_paths_require_full(self):
        Path('CONTRIBUTING.md').unlink()
        Path('CONTRIBUTING.md').symlink_to('elsewhere')
        self.assertFalse(scope.docs_only(self.base, self.commit()))

    def test_executable_mode_requires_full(self):
        Path('CONTRIBUTING.md').chmod(0o755)
        self.assertFalse(scope.docs_only(self.base, self.commit()))

    def test_code_example_requires_full(self):
        Path('CONTRIBUTING.md').write_text('```sh\necho example\n```\n')
        self.assertFalse(scope.docs_only(self.base, self.commit()))

    def test_removing_code_example_requires_full(self):
        Path('CONTRIBUTING.md').write_text('```sh\necho example\n```\n')
        base = self.commit()
        Path('CONTRIBUTING.md').write_text('Prose\n')
        self.assertFalse(scope.docs_only(base, self.commit()))

    def test_removing_executable_mode_requires_full(self):
        Path('CONTRIBUTING.md').chmod(0o755)
        base = self.commit()
        Path('CONTRIBUTING.md').chmod(0o644)
        self.assertFalse(scope.docs_only(base, self.commit()))


if __name__ == '__main__':
    unittest.main()
