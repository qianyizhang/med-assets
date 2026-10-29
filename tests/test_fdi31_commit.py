import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fdi31_commit', ROOT / 'ci/commit_fdi31_assets.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
MANIFEST = json.loads((ROOT / 'ci/fdi31-source/manifest.json').read_text())

class CommitTests(unittest.TestCase):
    def setup_request(self, branch=None, targets=None):
        request = Mock(side_effect=[{'object': {'sha': 'a' * 40}}, {'tree': {'sha': 'tree'}},
                                    {'tree': targets or [], 'truncated': False}, branch,
                                    {'sha': 'newtree'}, {'sha': 'newcommit'}, {}, {'html_url': 'PR'}])
        return request

    def test_exact_six_files_after_readback(self):
        request = self.setup_request()
        verified = Mock(return_value=[{'verified': True, 'oid': o['sha256'], 'bytes': o['bytes'], 'file': o['file']} for o in MANIFEST['objects']])
        result = m.prepare(MANIFEST, 'a' * 40, request, verified)
        self.assertEqual(result['pr'], 'PR')
        verified.assert_called_once_with(MANIFEST['objects'])
        writes = [call for call in request.call_args_list if call.args[0] == 'POST']
        self.assertEqual(len(writes), 4)
        self.assertEqual(len(writes[0].args[2]['tree']), 6)
        self.assertEqual({e['path'] for e in writes[0].args[2]['tree']},
                         {o['file'] for o in MANIFEST['objects']} | {m.PREFIX + 'README.md'})
        self.assertTrue(writes[-1].args[2]['draft'])

    def test_readback_failure_prevents_writes(self):
        request = self.setup_request()
        with self.assertRaises(m.Stop):
            m.prepare(MANIFEST, 'a' * 40, request, Mock(side_effect=m.Stop('missing object')))
        self.assertTrue(all(c.args[0] == 'GET' for c in request.call_args_list))

    def test_changed_main_stops(self):
        request = self.setup_request()
        with self.assertRaises(m.Stop):
            m.prepare(MANIFEST, 'b' * 40, request, Mock())
        self.assertEqual(request.call_count, 1)

    def test_existing_target_stops(self):
        request = self.setup_request(targets=[{'path': MANIFEST['objects'][0]['file']}])
        with self.assertRaises(m.Stop):
            m.prepare(MANIFEST, 'a' * 40, request, Mock())
        self.assertEqual(request.call_count, 3)

    def test_duplicate_pr_has_no_write_or_readback(self):
        request = self.setup_request(branch={'object': {'sha': 'existing'}})
        request.side_effect = list(request.side_effect)[:4] + [[{'html_url': 'existing PR'}]]
        verify = Mock()
        self.assertTrue(m.prepare(MANIFEST, 'a' * 40, request, verify)['unchanged'])
        verify.assert_not_called()
        self.assertTrue(all(c.args[0] == 'GET' for c in request.call_args_list))

    def test_branch_collision_stops(self):
        request = self.setup_request(branch={'object': {'sha': 'existing'}})
        request.side_effect = list(request.side_effect)[:4] + [[]]
        with self.assertRaises(m.Stop):
            m.prepare(MANIFEST, 'a' * 40, request, Mock())

    def test_wrong_readback_identity_prevents_writes(self):
        request = self.setup_request()
        with self.assertRaises(m.Stop):
            m.prepare(MANIFEST, 'a' * 40, request, Mock(return_value=[{'verified': True}] * 5))
        self.assertTrue(all(c.args[0] == 'GET' for c in request.call_args_list))

    def test_workflow_is_manual_opt_in_without_settings_change(self):
        workflow = (ROOT / '.github/workflows/bounded-lfs-transport.yml').read_text()
        self.assertIn('default: false', workflow)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.create_fdi31_pr && inputs.zero_cost_confirmed", workflow)
        self.assertIn('needs: transfer', workflow)
        self.assertNotIn('pull_request_target:', workflow)

    def test_manual_gate_precedes_any_io(self):
        with patch.dict(m.os.environ, {}, clear=True), patch.object(m, 'prepare') as prepare:
            with self.assertRaises(m.Stop):
                m.main()
            prepare.assert_not_called()

if __name__ == '__main__':
    unittest.main()
