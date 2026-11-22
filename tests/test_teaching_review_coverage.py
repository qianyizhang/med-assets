import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "records/campaigns/teaching-asset-review/coverage.py"
spec = importlib.util.spec_from_file_location("teaching_review_coverage", SCRIPT)
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)


class TeachingReviewCoverage(unittest.TestCase):
    def fixture(self, repo):
        """Mirror the assessed inputs as pointers so the gate works without hydration."""
        documents = [
            coverage.REGISTER, coverage.PILOT,
            *(path.relative_to(ROOT).as_posix()
              for path in (ROOT / "reviews").glob("*/*/teaching-assessment.json")),
            coverage.GALLERY + "reviewed-entries.json", coverage.GALLERY + "adrenal-study.js",
            coverage.SURFACES + "/README.md",
            *(coverage.SURFACES + f"/views/{key}/renders.json" for key in ("airspaces", "nail", "adrenal")),
            *(f"reviews/endocrine-locator/adrenal-study-{revision}/{file}"
              for revision in ("r04", "r05") for file in ("README.md", "renders.json")),
        ]
        raw_register = (ROOT / coverage.REGISTER).read_text()
        inputs = set(coverage.register_rows(raw_register))
        for assessment in (*coverage.records(ROOT), *coverage.historical(ROOT)):
            inputs.add(assessment["export"]["path"])
            inputs.update(claim["path"] for claim in assessment["views"])
        for path in documents:
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / path).read_bytes())
        for path in inputs:
            if not (ROOT / path).is_file():
                continue
            digest, size = coverage.identity(ROOT, path)
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {size}\n")

    def run_report(self, repo, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(repo), *map(str, args)],
            cwd=repo, text=True, check=False, capture_output=True,
        )

    def test_candidate_collection_verifies_identity_and_preserves_conflicts(self):
        from hashlib import sha256
        from unittest.mock import patch
        from teaching_assessments import collect_candidates
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            recovered = repo / "replay.glb"
            recovered.write_bytes(b"verified teaching geometry")
            digest = sha256(recovered.read_bytes()).hexdigest()
            relative = f".artifacts/teaching-refinements/candidates/{digest}.glb"
            candidate = {"path": relative, "sha256": digest, "bytes": recovered.stat().st_size, "download": True}
            register = repo / coverage.REGISTER
            register.parent.mkdir(parents=True)
            register.write_text("## Test\n| Selected | [selected.glb](../../models/selected.glb) |\n")
            control = {"path": "models/control.glb", "sha256": "a" * 64, "bytes": 1}
            rows = [(None, None, {"export": control, "refinement": {"candidate": candidate}})]
            with patch("teaching_assessments.campaign_rows", return_value=rows):
                self.assertEqual(collect_candidates(repo, [recovered]), (1, []))
                self.assertEqual(collect_candidates(repo, []), (1, []))
                target = repo / relative
                self.assertEqual(target.read_bytes(), recovered.read_bytes())
                target.write_bytes(b"concurrent change")
                with self.assertRaisesRegex(ValueError, "Existing candidate differs"):
                    collect_candidates(repo, [recovered])
                self.assertEqual(target.read_bytes(), b"concurrent change")

            promoted = {"path": "models/selected.glb", "sha256": digest, "bytes": candidate["bytes"]}
            with patch("teaching_assessments.campaign_rows", return_value=[*rows, (None, None, {"export": promoted})]):
                self.assertEqual(collect_candidates(repo, []), (0, []))

    def test_refinement_requires_exact_original_assessment_and_views(self):
        from teaching_assessments import assessment_digest, campaign_rows
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            folder = repo / "reviews/teaching-assessments/trial"
            folder.mkdir(parents=True)
            original = json.loads((ROOT / coverage.PILOT).read_text())["assessments"][0]
            control = folder / "campaign-assessments.json"
            control.write_text(json.dumps({"schemaVersion": 1, "assessments": [original]}))
            first = original["views"][0]
            change = {"path": original["export"]["path"], "sha256": original["export"]["sha256"],
                      "controlAssessmentSha256": assessment_digest(original), "family": "Test",
                      "before": first, "after": first, "finding": "Matched witness.", "decision": "Keep.",
                      "axisChanges": {}, "limits": "Original task."}
            accepted = folder / "accepted.json"
            accepted.write_text(json.dumps({"schemaVersion": 1, "group": "Form", "outcomes": [change]}))
            self.assertEqual(list(campaign_rows(repo))[0][2]["axes"], original["axes"])
            original["task"] += " A different task."
            control.write_text(json.dumps({"schemaVersion": 1, "assessments": [original]}))
            with self.assertRaisesRegex(ValueError, "does not match its control"):
                list(campaign_rows(repo))
            change["controlAssessmentSha256"] = assessment_digest(original)
            change["after"] = {**first, "sha256": "d"*64}
            accepted.write_text(json.dumps({"schemaVersion": 1, "group": "Form", "outcomes": [change]}))
            with self.assertRaisesRegex(ValueError, "changes an existing view identity"):
                list(campaign_rows(repo))

    def test_target_requires_bound_original_and_individual_exemptions(self):
        from teaching_assessments import assessment_digest, campaign_rows
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            folder = repo / 'reviews/teaching-assessments/target-test'
            folder.mkdir(parents=True)
            entry = json.loads((ROOT / coverage.PILOT).read_text())['assessments'][0]
            entry['axes'] = [{'score': s, 'observation': 'Inspected.'} for s in (3, 2, 3, 3)]
            batch = {'schemaVersion': 1, 'assessments': [entry]}
            (folder / 'campaign-assessments.json').write_text(json.dumps(batch))
            (folder.parent / 'target-standard.json').write_text('{"schemaVersion": 1}')
            digest = assessment_digest(entry)
            view = entry['views'][0]
            decision = {'family': 'Test', 'baseline': entry['export']['path'], 'path': entry['export']['path'],
                        'controlAssessmentSha256': digest, 'assessmentSha256': digest, 'taskCheck': 'Found both landmarks.',
                        'before': view, 'after': view, 'status': 'passed', 'evidence': ['witness.md'], 'exemptions': {}}
            (repo / 'witness.md').write_text('Witness')
            path = folder / 'decisions.json'
            path.write_text(json.dumps([decision]))
            with self.assertRaisesRegex(ValueError, 'Unresolved teaching target axes'):
                list(campaign_rows(repo))
            decision['exemptions']['1'] = {'reason': 'Visible corner.', 'permittedUse': 'Localization.', 'reopen': 'Source section.'}
            path.write_text(json.dumps([decision]))
            prior = list(campaign_rows(repo))[0][2]
            self.assertEqual(prior['axes'][1]['score'], 2)
            second = folder.parent / 'reopen-test/decisions.json'
            second.parent.mkdir()
            reopened = {**decision, 'controlAssessmentSha256': assessment_digest(prior),
                        'assessmentSha256': assessment_digest(prior), 'reviewedAxes': ['1'], 'exemptions': {},
                        'axisChanges': {'1': {'score': 3, 'observation': 'Registered source section explains the contour.'}}}
            second.write_text(json.dumps([reopened]))
            current = list(campaign_rows(repo))[0][2]
            self.assertEqual(current['axes'][1]['score'], 3)
            self.assertEqual(current['target']['beforeScores'], [3, 2, 3, 3])
            reopened['reviewedAxes'] = ['3']
            second.write_text(json.dumps([reopened]))
            with self.assertRaisesRegex(ValueError, 'preceding exemptions'):
                list(campaign_rows(repo))
            second.unlink()
            decision['controlAssessmentSha256'] = 'a' * 64
            path.write_text(json.dumps([decision]))
            with self.assertRaisesRegex(ValueError, 'differs from its reviewed file or task'):
                list(campaign_rows(repo))

    def test_exact_native_and_wrong_or_ambiguous_export(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp).resolve()
            git_directory = subprocess.check_output(
                ["git", "rev-parse", "--absolute-git-dir"], cwd=ROOT, text=True,
            ).strip()
            (repo / ".git").write_text(f"gitdir: {git_directory}\n")
            self.fixture(repo)
            normal = self.run_report(repo)
            self.assertEqual(normal.returncode, 0, normal.stderr)
            rows = normal.stdout.splitlines()
            for name, state in (
                ("Terminal airspace study", "Full"),
                ("Bronchial tree · first fork", "Unrated"),
                ("Breathing collection", "Unrated"),
            ):
                self.assertIn(f"| {state} |", next(line for line in rows if f"| {name} |" in line))

            pilot = coverage.read_json(repo / coverage.PILOT)
            control = next(item for item in pilot["assessments"] if "bronchial_tree" in item["route"])
            sibling = next(path for path, (_, family) in coverage.register_rows((repo / coverage.REGISTER).read_text()).items()
                           if family == "Bronchial tree · first fork")
            original_digest = control["export"]["sha256"]
            suspect = {**control, "export": {**control["export"], "path": sibling}}
            injected = repo / "reviews/teaching-assessments/test/campaign-assessments.json"
            injected.parent.mkdir(parents=True)
            injected.write_text(json.dumps({**pilot, "assessments": [suspect]}))
            wrong = self.run_report(repo)
            self.assertEqual(wrong.returncode, 0, wrong.stderr)
            self.assertIn(f"Identity mismatch for {sibling}", wrong.stdout)
            self.assertIn("| Unrated |", next(line for line in wrong.stdout.splitlines()
                                              if "| Bronchial tree · first fork |" in line))
            self.assertIn(original_digest, wrong.stdout)

            digest, size = coverage.identity(repo, sibling)
            suspect["export"].update(sha256=digest, bytes=size)
            competing = {**suspect, "task": "A second task for the same file", "route": "distinct-claim"}
            injected.write_text(json.dumps({**pilot, "assessments": [suspect, competing]}))
            ambiguous = self.run_report(repo)
            self.assertEqual(ambiguous.returncode, 0, ambiguous.stderr)
            row = next(line for line in ambiguous.stdout.splitlines() if "| Bronchial tree · first fork |" in line)
            self.assertIn("| Unrated |", row)
            self.assertIn("Several campaign assessments share the newest date", row)

            injected.unlink()
            report = repo / "saved-report.md"
            report.write_text(normal.stdout)
            self.assertEqual(self.run_report(repo, "--check", report).returncode, 0)
            register = repo / coverage.REGISTER
            register.write_text(register.read_text().replace("| Right lung · s1233 |", "| Right lung · renamed |"))
            drift = self.run_report(repo, "--check", report)
            self.assertEqual(drift.returncode, 1)
            self.assertIn("Coverage report drift.", drift.stderr)
            self.assertIn("Renamed or regrouped", self.run_report(repo).stdout)


if __name__ == "__main__":
    unittest.main()
