"""Current viewer behavior and concurrent staging; no network, models or WebGL."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('viewer_run', ROOT / 'tests/viewer/run.py')
viewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viewer)


class CurrentViewerTests(unittest.TestCase):
    def test_complete_current_behavior(self):
        viewer.run()

    def test_changed_current_source_refused_before_staging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'tests/viewer').mkdir(parents=True)
            (root / 'tests/viewer/source.json').write_bytes(
                (ROOT / 'tests/viewer/source.json').read_bytes())
            (root / 'tests/viewer/candidate.js').write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError, 'Wrong exact viewer source'):
                with viewer.stage(root):
                    self.fail('Unbound source must not reach staging')

    def test_empty_required_node_suite_is_not_a_passing_file_placeholder(self):
        with viewer.stage() as target:
            (target / 'tests/candidate_lifecycle-lifecycle.test.mjs').write_text('')
            @contextmanager
            def existing_stage(*args):
                yield target
            with patch.object(viewer, 'stage', existing_stage):
                with self.assertRaisesRegex(RuntimeError, 'failed or incomplete'):
                    viewer.run(('lifecycle',))

    def test_concurrent_runs_have_private_stages_and_no_source_writes(self):
        original = viewer.read_sources()
        with viewer.stage() as first, viewer.stage() as second:
            self.assertNotEqual(first, second)
            (first / 'public/review/candidate.js').write_bytes(b'local refinement')
            self.assertEqual((second / 'public/review/candidate.js').read_bytes(), original['candidate.js'])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: viewer.run(('lifecycle',)), range(2)))
        self.assertEqual(len(results), 2)
        self.assertEqual(viewer.read_sources(), original)
