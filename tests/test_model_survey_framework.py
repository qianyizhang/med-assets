"""Exercise dependency/overlay assembly and refusal paths through its public API."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

recipe = Path(__file__).resolve().parents[1] / 'sites/anatomy-gallery/tools/framework.py'
spec = importlib.util.spec_from_file_location('survey_framework', recipe)
framework = importlib.util.module_from_spec(spec)
spec.loader.exec_module(framework)


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.source, self.site, self.output = root/'source', root/'sites'/'gallery', root/'output'
        self.source.mkdir(); self.site.mkdir(parents=True)
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
        (self.site/'app/src/content').mkdir(parents=True)
        (self.site/'app/src/content/report.jsx').write_text('survey specific source')
        (self.site/'app/src/theme.css').write_text('survey theme')
        (self.site/'app/src/data.json').write_text('{"id":"report:test","queries":{"rows":[1,2,3]}}')
        self.save_reference()

    def command(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args], text=True).strip()

    def save_lock(self):
        (self.site/'framework.lock.json').write_text(json.dumps(self.lock))

    def save_reference(self):
        raw = (self.site / 'app/src/data.json').read_bytes()
        reference = {'artifactId': 'report:test', 'surveySeedPublication': {
            'sourceSeedSha256': hashlib.sha256(raw).hexdigest(), 'sourceSeedBytes': len(raw),
        }}
        (self.site / 'snapshot-reference.json').write_text(json.dumps(reference))

    def prepare(self):
        return framework.prepare(self.site, self.source, self.output)

    def test_unhydrated_lesson_image_fails_before_installing_the_app(self):
        image = self.site / 'app/src/content/lesson.webp'
        image.write_text('version https://git-lfs.github.com/spec/v1\n')
        with self.assertRaisesRegex(ValueError, 'hydrated WebP image'):
            self.prepare()
        self.assertFalse(self.output.exists())

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

    def test_gallery_assembly_supplies_the_pinned_worker_index(self):
        content = self.site / 'app/src/content'
        (content / 'gallery').mkdir()
        (content / 'gallery/catalog.js').write_text('export const studies = [];')
        index = content / 'assets/delivery-index.json'
        index.parent.mkdir()
        payload = b'{"assets": []}\n'
        index.write_bytes(payload)
        runtime = SimpleNamespace(prepare_gallery=lambda *_, **__: None)
        with patch.dict(sys.modules, {'gallery_runtime': runtime}), patch.object(framework, 'compile_library') as compile_library:
            self.prepare()
        compile_library.assert_called_once()
        generated = self.output / 'src/content/assets'
        self.assertEqual((generated / index.name).read_bytes(), payload)
        self.assertEqual((generated / 'r2-trial.json').read_bytes(), payload)
        self.assertFalse(index.with_name('r2-trial.json').exists())

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
        self.save_reference()
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.output.exists())

    def test_same_artifact_with_changed_source_seed_is_rejected(self):
        seed = self.site / 'app/src/data.json'
        seed.write_bytes(seed.read_bytes().replace(b'[1,2,3]', b'[0,2,3]'))
        with self.assertRaisesRegex(ValueError, 'Source seed differs from its recorded size or SHA-256'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_gallery_build_refuses_a_changed_review_export(self):
        # Exercise the normal command with a valid framework and a mismatched delivery row.
        site = self.site
        (site/'tools').mkdir()
        for name in ('tools/teaching_assessments.py', 'tools/assessment_identity.py', 'tools/maintained_teaching.py',
                     'transport/tools/lfs_transport.py', 'transport/tools/delivery_catalog.py',
                     'transport/tools/restore_snapshot.py'):
            shared = site.parents[1] / name
            shared.parent.mkdir(parents=True, exist_ok=True)
            shared.write_bytes((recipe.parents[3] / name).read_bytes())
        for name in ('framework.py', 'gallery_runtime.py'):
            (site/'tools'/name).write_bytes((recipe.parent/name).read_bytes())
        gallery = site/'app/src/content/gallery'
        gallery.mkdir()
        (gallery/'catalog.js').write_text('export const studies = [];')
        assets = site/'app/src/content/assets'
        assets.mkdir()
        reviewed = {'file': 'models/adrenal.glb', 'bytes': 4, 'sha256': 'a'*64}
        record = site.parents[1]/'reviews/adrenals/2026-10-23-bp3d-bounded-migration/bounded-record.json'
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps({'artifact': reviewed, 'evidence': []}))
        witness = {'path': 'reviews/salivary/crossing.webp', 'bytes': 4, 'sha256': 'c'*64}
        salivary = site.parents[1]/'reviews/salivary_glands/2026-10-26-native-scoped-r02/decision.json'
        salivary.parent.mkdir(parents=True)
        salivary.write_text(json.dumps({'media': [witness]}))
        adrenal_row = {**reviewed, 'path': reviewed['file']}
        for broken in (adrenal_row, witness):
            with self.subTest(path=broken['path']):
                (assets/'delivery-index.json').write_text(json.dumps({'assets': [
                    {**row, 'sha256': 'b'*64} if row == broken else row
                    for row in (adrenal_row, witness)
                ]}))
                result = subprocess.run([sys.executable, str(site/'tools/framework.py'),
                                         '--source', str(self.source), '--output', str(self.output)],
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"Delivery index differs from the pinned review: {broken['path']}", result.stderr)
                self.assertFalse(self.output.exists())

    def test_generated_display_preserves_pointer_only_checkout_and_rejects_corruption(self):
        spec = importlib.util.spec_from_file_location('gallery_runtime', recipe.with_name('gallery_runtime.py'))
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        source = self.site.resolve() / 'contact.png'
        target = self.site.resolve() / 'display/contact.webp'
        original = {'path': source.name, 'bytes': 8, 'sha256': 'a' * 64}
        display = {'path': target.name, 'bytes': 8, 'sha256': 'b' * 64}
        pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{original['sha256']}\nsize 8\n"
        with self.assertRaisesRegex(FileNotFoundError, source.name):
            runtime.generate_display(source, target, original, display)
        self.assertFalse(target.exists())
        source.write_text(pointer)
        runtime.generate_display(source, target, original, display)
        self.assertFalse(target.exists())
        source.write_bytes(b'corrupt!')
        with self.assertRaisesRegex(ValueError, source.name):
            runtime.generate_display(source, target, original, display)
        self.assertFalse(target.exists())
        target.parent.mkdir()
        target.write_bytes(b'my edit!')
        source.write_text(pointer)
        with self.assertRaisesRegex(ValueError, target.name):
            runtime.generate_display(source, target, original, display)
        self.assertEqual(target.read_bytes(), b'my edit!')

    def test_teaching_assessments_require_integer_scores_and_written_observations(self):
        runtime_spec = importlib.util.spec_from_file_location('gallery_runtime', recipe.with_name('gallery_runtime.py'))
        runtime = importlib.util.module_from_spec(runtime_spec)
        runtime_spec.loader.exec_module(runtime)
        repo = recipe.parents[3]
        review = json.loads((repo / runtime.TEACHING_REVIEW).read_text())
        index = repo / 'sites/anatomy-gallery/app/src/content/assets/delivery-index.json'
        record = self.site / runtime.TEACHING_REVIEW
        record.parent.mkdir(parents=True)
        self.output.mkdir()
        axis = review['assessments'][0]['axes'][0]
        for score, observation, error in [(True, 'checked', 'score'), (2.0, 'checked', 'score'),
                                          (3, '   ', 'observation')]:
            with self.subTest(score=score, observation=observation):
                axis.update(score=score, observation=observation)
                record.write_text(json.dumps(review))
                with self.assertRaisesRegex(ValueError, error):
                    runtime.prepare_teaching_assessments(self.site, index, self.output)
                self.assertFalse((self.output / 'teaching-assessments.json').exists())
        axis.update(score=0, observation='Assessed and absent.')
        record.write_text(json.dumps(review))
        with patch.object(runtime, 'prepare_campaign_reviews', return_value=[]):
            runtime.prepare_teaching_assessments(self.site, index, self.output)
        expected = {**review['assessments'][0], **{key: review[key] for key in ('evaluator', 'date', 'rubric')}}
        result = json.loads((self.output / 'teaching-assessments.json').read_text())
        self.assertEqual(result['assessments'][0], expected)

    def test_campaign_assessment_rejects_sibling_identity_and_unbound_teaching_view(self):
        spec = importlib.util.spec_from_file_location('gallery_runtime', recipe.with_name('gallery_runtime.py'))
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        repo = self.site
        from teaching_fixture import install_assessments
        (repo / 'reviews').mkdir()
        (repo / 'models').mkdir()
        (repo / 'models/control.glb').write_bytes(b'old')
        view = {'path': 'reviews/plate.jpg', 'bytes': 1, 'sha256': hashlib.sha256(b'v').hexdigest(),
                'label': 'Matched teaching view'}
        (repo / view['path']).write_bytes(b'v')
        export = {'path': 'models/control.glb', 'bytes': 3, 'sha256': hashlib.sha256(b'old').hexdigest()}
        index = repo / 'delivery-index.json'
        index.write_text(json.dumps({'assets': [export]}))
        index.with_name('local-delivery.json').write_text('{"assets":[]}')
        row = {'task': 'Trace the first fork.', 'export': dict(export), 'views': [view],
               'axes': [{'score': 3, 'observation': 'The fork is intact.'}] * 4,
               'sources': [{'path': view['path'], 'label': 'Control view'}], 'teachingView': view['path']}
        install_assessments(repo, [('first-fork', row)], selected_task='first-fork')
        result = runtime.prepare_campaign_reviews(repo, index)
        self.assertEqual(result[0]['views'][0]['url'], '/review-evidence/' + view['sha256'] + '/plate.jpg')
        self.assertEqual(result[0]['maintained']['taskId'], 'first-fork')
        self.assertEqual(result[0]['maintained']['familyId'], 'fixture-family')
        row['export']['sha256'] = 'b'*64
        install_assessments(repo, [('first-fork', row)], selected_task='first-fork')
        with self.assertRaisesRegex(ValueError, 'Identity mismatch'):
            runtime.prepare_campaign_reviews(repo, index)
        row['export'] = export
        row['teachingView'] = 'reviews/unrelated.jpg'
        install_assessments(repo, [('first-fork', row)], selected_task='first-fork')
        with self.assertRaisesRegex(ValueError, 'Teaching view is outside'):
            runtime.prepare_campaign_reviews(repo, index)
        row['teachingView'] = view['path']
        install_assessments(repo, [('first-fork', row)], selected_task='first-fork')
        (repo / view['path']).write_bytes(b'x')
        with self.assertRaisesRegex(ValueError, 'Identity mismatch'):
            runtime.prepare_campaign_reviews(repo, index)

    def test_refinement_download_uses_the_exact_maintained_export(self):
        spec = importlib.util.spec_from_file_location('gallery_runtime', recipe.with_name('gallery_runtime.py'))
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        repo = self.site
        from teaching_fixture import install_assessments
        for directory in ('models', 'reviews'):
            (repo / directory).mkdir(parents=True)
        (repo / 'models/selected.glb').write_bytes(b'new')
        (repo / 'models/control.glb').write_bytes(b'old')
        (repo / 'models/replay.py').write_text('# recipe\n')
        (repo / 'reviews/view.jpg').write_bytes(b'v')
        view = {'path': 'reviews/view.jpg', 'bytes': 1, 'sha256': hashlib.sha256(b'v').hexdigest()}
        selected = {'path': 'models/selected.glb', 'bytes': 3, 'sha256': hashlib.sha256(b'new').hexdigest()}
        control = {'path': 'models/control.glb', 'bytes': 3, 'sha256': hashlib.sha256(b'old').hexdigest()}
        index = repo / 'delivery-index.json'
        index.write_text(json.dumps({'assets': [control]}))
        index.with_name('local-delivery.json').write_text('{"assets":[]}')
        review = {'task': 'Trace the structure.', 'views': [view], 'sources': [view],
                  'axes': [{'score': 3, 'observation': 'The landmark is visible.'}] * 4}
        digest = selected['sha256']
        candidate = {'path': f'.artifacts/teaching-refinements/candidates/{digest}.glb',
                     'bytes': 3, 'sha256': digest, 'name': 'earlier-name.glb',
                     'recipe': 'models/replay.py', 'download': True}

        def prepared_download(item):
            comparison = {'candidate': item, 'before': view['path'], 'after': view['path']}
            rows = [('control-task', {**review, 'export': control, 'refinement': comparison}),
                    ('selected-task', {**review, 'export': selected})]
            install_assessments(repo, rows, selected_task='selected-task')
            return runtime.prepare_campaign_reviews(repo, index)[0]['refinement']['candidate']

        promoted = prepared_download(candidate)
        self.assertEqual(promoted['path'], selected['path'])
        self.assertEqual(promoted['url'], f'/assets/{digest}/selected.glb')
        self.assertEqual(promoted['name'], 'selected.glb')
        self.assertEqual(candidate['name'], 'earlier-name.glb')

        unmatched = prepared_download({**candidate, 'bytes': 4})
        self.assertEqual(unmatched['url'], f'/assets/{digest}/earlier-name.glb')
        self.assertEqual(unmatched['path'], candidate['path'])

    def test_teaching_assessment_discovery_preserves_batch_metadata_and_rejects_conflicts(self):
        runtime_spec = importlib.util.spec_from_file_location('gallery_runtime', recipe.with_name('gallery_runtime.py'))
        runtime = importlib.util.module_from_spec(runtime_spec)
        runtime_spec.loader.exec_module(runtime)
        repo = recipe.parents[3]
        index = repo / 'sites/anatomy-gallery/app/src/content/assets/delivery-index.json'
        pilot = self.site / runtime.TEACHING_REVIEW
        pilot.parent.mkdir(parents=True)
        original = (repo / runtime.TEACHING_REVIEW).read_bytes()
        pilot.write_bytes(original)
        batch = self.site / 'reviews/joints/scoped-review/teaching-assessment.json'
        batch.parent.mkdir(parents=True)
        review = json.loads(original)
        assessment = review['assessments'].pop()
        batch_data = {**review, 'evaluator': 'Second evaluator', 'date': '2026-11-22', 'assessments': [assessment]}
        self.output.mkdir()
        output = self.output / 'teaching-assessments.json'
        batch.write_text(json.dumps(batch_data))
        with self.assertRaisesRegex(ValueError, 'Duplicate teaching assessment'):
            runtime.prepare_teaching_assessments(self.site, index, self.output)
        self.assertFalse(output.exists())

        pilot.write_text(json.dumps(review))
        assessment['views'][0]['sha256'], correct = 'f'*64, assessment['views'][0]['sha256']
        batch.write_text(json.dumps(batch_data))
        with self.assertRaisesRegex(ValueError, 'Delivery index differs from the pinned review'):
            runtime.prepare_teaching_assessments(self.site, index, self.output)
        self.assertFalse(output.exists())

        assessment['views'][0]['sha256'] = correct
        batch.write_text(json.dumps(batch_data))
        with patch.object(runtime, 'prepare_campaign_reviews', return_value=[]):
            runtime.prepare_teaching_assessments(self.site, index, self.output)
        entries = json.loads(output.read_text())['assessments']
        self.assertEqual([entry['route'] for entry in entries],
                         [entry['route'] for entry in json.loads(original)['assessments']])
        self.assertEqual([entry['date'] for entry in entries], [review['date']] * 2 + [batch_data['date']])
        self.assertEqual(entries[-1]['evaluator'], batch_data['evaluator'])
        self.assertEqual(entries[-1]['rubric'], batch_data['rubric'])

    def test_airway_exports_must_match_their_independent_review_records(self):
        runtime_spec = importlib.util.spec_from_file_location('gallery_runtime', recipe.with_name('gallery_runtime.py'))
        runtime = importlib.util.module_from_spec(runtime_spec)
        runtime_spec.loader.exec_module(runtime)
        source = recipe.parents[1]/'app/src/content/assets/delivery-index.json'
        data = json.loads(source.read_text())
        index = self.output / 'index.json'
        self.output.mkdir()
        for name in ('bronchial_central_fairing.glb', 'nasal_airspace.glb',
                     'trachea_host_conforming_illustration.glb', 'trachea-open.glb', 'trachea-cutaway.glb'):
            with self.subTest(name=name):
                row = next(asset for asset in data['assets'] if asset['name'] == name)
                digest = row['sha256']
                row['sha256'] = '0' * 64
                index.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, 'Delivery index differs from the pinned review') as error:
                    runtime.check_review_delivery(recipe.parents[3], index)
                self.assertIn(row['path'], str(error.exception))
                row['sha256'] = digest

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
