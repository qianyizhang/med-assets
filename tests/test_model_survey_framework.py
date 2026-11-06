"""Exercise dependency/overlay assembly and refusal paths through its public API."""
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

recipe = Path(__file__).resolve().parents[1] / 'sites/model-survey/tools/framework.py'
spec = importlib.util.spec_from_file_location('survey_framework', recipe)
framework = importlib.util.module_from_spec(spec)
spec.loader.exec_module(framework)


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.source, self.site, self.output = root/'source', root/'site', root/'output'
        self.source.mkdir(); self.site.mkdir()
        hosting = {'project_id': 'existing-site', 'd1': 'DB', 'r2': 'BUCKET'}
        for base in (self.source, self.site/'app'):
            (base/'.openai').mkdir(parents=True)
            (base/'.openai/hosting.json').write_text(json.dumps(hosting))
        (self.source/'runtime.js').write_text('export const framework = 1;')
        (self.source/'src/content').mkdir(parents=True)
        (self.source/'src/content/report.jsx').write_text('old survey must not leak back')
        manifest = b'{"version":1,"files":{}}'
        (self.source/'protected-runtime.json').write_bytes(manifest)
        self.command('init', '-q')
        self.command('add', '.')
        self.command('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        self.lock = {'projectId': 'existing-site', 'commit': self.command('rev-parse', 'HEAD'),
                     'tree': self.command('rev-parse', 'HEAD^{tree}'),
                     'runtimeManifestSha256': hashlib.sha256(manifest).hexdigest()}
        self.save_lock()
        (self.site/'snapshot-reference.json').write_text('{"artifactId":"report:test"}')
        (self.site/'app/src/content').mkdir(parents=True)
        (self.site/'app/src/content/report.jsx').write_text('survey specific source')
        (self.site/'app/src/theme.css').write_text('survey theme')
        (self.site/'app/src/data.json').write_text('{"id":"report:test","queries":{"rows":[1,2,3]}}')

    def command(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args], text=True).strip()

    def save_lock(self):
        (self.site/'framework.lock.json').write_text(json.dumps(self.lock))

    def prepare(self):
        return framework.prepare(self.site, self.source, self.output)

    def test_fresh_project_combines_pinned_runtime_overlay_and_complete_seed(self):
        self.prepare()
        self.assertEqual((self.output/'runtime.js').read_bytes(), (self.source/'runtime.js').read_bytes())
        for relative in ('.openai/hosting.json', 'src/content/report.jsx', 'src/theme.css', 'src/data.json'):
            self.assertEqual((self.output/relative).read_bytes(), (self.site/'app'/relative).read_bytes())
        self.assertFalse((self.output/'.git').exists())

    def test_removed_survey_content_is_not_restored_from_dependency(self):
        (self.site/'app/src/content/report.jsx').unlink()
        self.prepare()
        self.assertFalse((self.output/'src/content/report.jsx').exists())

    def test_wrong_or_unavailable_dependency_leaves_no_output(self):
        for key, value in [('tree', '0'*40), ('runtimeManifestSha256', '0'*64), ('commit', '0'*40)]:
            original = self.lock[key]; self.lock[key] = value; self.save_lock()
            with self.assertRaises(ValueError): self.prepare()
            self.assertFalse(self.output.exists())
            self.lock[key] = original

    def test_other_site_and_other_artifact_are_rejected(self):
        file = self.site/'app/.openai/hosting.json'
        old = file.read_bytes(); file.write_text('{"project_id":"another-site"}')
        with self.assertRaises(ValueError): self.prepare()
        file.write_bytes(old)
        (self.site/'app/src/data.json').write_text('{"id":"another-artifact"}')
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.output.exists())

    def test_existing_destination_is_preserved(self):
        self.output.mkdir(); (self.output/'edits').write_text('keep')
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual((self.output/'edits').read_text(), 'keep')

    def test_links_are_refused_before_writing(self):
        (self.site/'app/src/content/link').symlink_to(self.site/'app/src/theme.css')
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.output.exists())
        (self.site/'app/src/content/link').unlink()
        (self.source/'link').symlink_to('/outside-project')
        self.command('add', 'link')
        self.command('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'link')
        self.lock['commit'] = self.command('rev-parse', 'HEAD')
        self.lock['tree'] = self.command('rev-parse', 'HEAD^{tree}'); self.save_lock()
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.output.exists())
