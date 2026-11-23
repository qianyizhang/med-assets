import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "records/campaigns/teaching-asset-review/coverage.py"
spec = importlib.util.spec_from_file_location("teaching_review_coverage", SCRIPT)
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)
from teaching_assessments import register_rows, register_selections
from assessment_identity import (AssessmentIdentities, DELIVERY_INDEX, DISPLAY_RECIPE,
                                 GALLERY_SITE, file_identity)
from maintained_teaching import ASSESSMENTS, SELECTIONS, CurrentTeaching, render_register
from teaching_fixture import install_assessments


class TeachingReviewCoverage(unittest.TestCase):
    def fixture(self, repo):
        """Mirror the assessed inputs as pointers so the gate works without hydration."""
        documents = [
            coverage.REGISTER, coverage.PILOT, SELECTIONS,
            *(family["owner"] for family in coverage.read_json(ROOT / SELECTIONS)["families"].values() if "owner" in family),
            str(DELIVERY_INDEX), str(GALLERY_SITE / DISPLAY_RECIPE),
            *(path.relative_to(ROOT).as_posix()
              for path in (ROOT / "reviews").glob("*/*/teaching-assessment.json")),
            coverage.GALLERY + "reviewed-entries.json", coverage.GALLERY + "adrenal-study.js",
            coverage.SURFACES + "/README.md",
            *(coverage.SURFACES + f"/views/{key}/renders.json" for key in ("airspaces", "nail", "adrenal")),
            *(f"reviews/endocrine-locator/adrenal-study-{revision}/{file}"
              for revision in ("r04", "r05") for file in ("README.md", "renders.json")),
        ]
        raw_register = (ROOT / coverage.REGISTER).read_text()
        inputs = set(register_rows(raw_register))
        for assessment in (*coverage.read_json(ROOT / coverage.PILOT)["assessments"], *coverage.historical(ROOT)):
            inputs.add(assessment["export"]["path"])
            inputs.update(claim["path"] for claim in assessment["views"])
        for path in documents:
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / path).read_bytes())
        for path in inputs:
            if not (ROOT / path).is_file():
                continue
            digest, size = file_identity(ROOT, path)
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {size}\n")

    def run_report(self, repo, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(repo), *map(str, args)],
            cwd=repo, text=True, check=False, capture_output=True,
        )

    def test_shared_family_declares_each_selected_export_once(self):
        first = "[full.glb](../../heart/study/full.glb)"
        second = "[wall.glb](../../heart/study/wall.glb)"
        row = f"## Cardiovascular\n| Cardiac Atlas | {first}<br>{second} |"
        selections = register_rows(row)
        self.assertEqual(len(selections), 2)
        self.assertEqual(set(selections.values()), {("Cardiovascular", "Cardiac Atlas")})
        shared = "[Pelvis](../../assemblies/pelvis/README.md)"
        cross_list = f"## Urinary\n| Bladder · {shared} | {first} |\n## Reproductive\n| Cervix · {shared} | {second} |"
        pelvic = register_selections(cross_list).values()
        self.assertEqual({item.family for item in pelvic}, {"Pelvis"})
        self.assertEqual({item.label for item in pelvic}, {"Bladder", "Cervix"})
        self.assertEqual({item.shared_owner for item in pelvic}, {"assemblies/pelvis/README.md"})
        with self.assertRaisesRegex(ValueError, "Duplicate maintained selection"):
            register_rows(row.replace(second, first))
        with self.assertRaisesRegex(ValueError, "Ambiguous maintained row"):
            register_rows(row + f"\n| Cardiac Atlas | {second} |")

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
            control = {"path": "models/control.glb", "sha256": "a" * 64, "bytes": 1}
            record = SimpleNamespace(row={"export": control, "refinement": {"candidate": candidate}})
            current = SimpleNamespace(gallery=lambda: [record], maintained_exports=lambda: {})
            with patch("maintained_teaching.CurrentTeaching", return_value=current):
                self.assertEqual(collect_candidates(repo, [recovered]), (1, []))
                self.assertEqual(collect_candidates(repo, []), (1, []))
                target = repo / relative
                self.assertEqual(target.read_bytes(), recovered.read_bytes())
                target.write_bytes(b"concurrent change")
                with self.assertRaisesRegex(ValueError, "Existing candidate differs"):
                    collect_candidates(repo, [recovered])
                self.assertEqual(target.read_bytes(), b"concurrent change")

            promoted = {"path": "models/selected.glb", "sha256": digest, "bytes": candidate["bytes"]}
            current.maintained_exports = lambda: {(digest, candidate["bytes"]): promoted["path"]}
            with patch("maintained_teaching.CurrentTeaching", return_value=current):
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
            self.fixture(repo)
            self.assertIn("must be supplied together", self.run_report(repo, "--audit").stderr)
            register = repo / coverage.REGISTER
            env = dict(os.environ)
            env.pop("GIT_INDEX_FILE", None)
            for command in (("init", "-q"), ("add", coverage.REGISTER),
                            ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                             "commit", "-qm", "Test baseline")):
                subprocess.run(["git", *command], cwd=repo, env=env, check=True)
            audit_args = ("--audit", "--baseline", "HEAD")
            normal = self.run_report(repo, *audit_args)
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
            sibling = next(path for path, (_, family) in register_rows((repo / coverage.REGISTER).read_text()).items()
                           if family == "Bronchial tree · first fork")
            original_digest = control["export"]["sha256"]
            suspect = {**control, "export": {**control["export"], "path": sibling}}
            injected = repo / "reviews/teaching-assessments/test/campaign-assessments.json"
            injected.parent.mkdir(parents=True)
            injected.write_text(json.dumps({**pilot, "assessments": [suspect]}))
            wrong = self.run_report(repo, *audit_args)
            self.assertEqual(wrong.returncode, 0, wrong.stderr)
            self.assertIn(f"Identity mismatch for {sibling}", wrong.stdout)
            self.assertIn("| Unrated |", next(line for line in wrong.stdout.splitlines()
                                              if "| Bronchial tree · first fork |" in line))
            self.assertIn(original_digest, wrong.stdout)

            digest, size = file_identity(repo, sibling)
            suspect["export"].update(sha256=digest, bytes=size)
            competing = {**suspect, "task": "A second task for the same file", "route": "distinct-claim"}
            injected.write_text(json.dumps({**pilot, "assessments": [suspect, competing]}))
            ambiguous = self.run_report(repo, *audit_args)
            self.assertEqual(ambiguous.returncode, 0, ambiguous.stderr)
            row = next(line for line in ambiguous.stdout.splitlines() if "| Bronchial tree · first fork |" in line)
            self.assertIn("| Unrated |", row)
            self.assertIn("Several campaign assessments share the newest date", row)

            injected.unlink()
            report = repo / "saved-report.md"
            report.write_text(normal.stdout)
            self.assertEqual(self.run_report(repo, *audit_args, "--check", report).returncode, 0)
            register.write_text("Editorial formatting cannot change the current selections.")
            self.assertEqual(self.run_report(repo, *audit_args, "--check", report).returncode, 0)
            config = repo / SELECTIONS
            changed = coverage.read_json(config)
            family = next(family for family in changed["families"].values() if family["label"] == "Right lung · s1233")
            family["label"] = "Right lung · renamed"
            config.write_text(json.dumps(changed))
            drift = self.run_report(repo, *audit_args, "--check", report)
            self.assertEqual(drift.returncode, 1)
            self.assertIn("Coverage report drift.", drift.stderr)
            audit = self.run_report(repo, *audit_args)
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("Renamed or regrouped", audit.stdout)
            self.assertIn("| Full |", next(line for line in audit.stdout.splitlines()
                                           if "| Terminal airspace study |" in line))

    def test_current_selection_binds_task_and_review_without_historical_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp).resolve()
            (repo / "models").mkdir()
            export, view = "models/control.glb", "models/view.jpg"
            for path, data in ((export, b"test3d"), (view, b"test image")):
                (repo / path).write_bytes(data)
            identities = {}
            for path in (export, view):
                digest, size = file_identity(repo, path)
                identities[path] = {"path": path, "sha256": digest, "bytes": size}
            row = {"export": identities[export], "task": "Locate the branches.",
                   "axes": [{"score": 3, "observation": "Both branches visible."}] * 4,
                   "sources": [{"path": view, "label": "Inspected view"}], "views": [identities[view]]}
            alternate = {**row, "task": "Explain the parent trunk."}
            install_assessments(repo, [("branches", row), ("trunk", alternate)], selected_task="branches")
            history = repo / "reviews/teaching-assessments/refinement-historical/accepted.json"
            history.parent.mkdir(parents=True)
            history.write_text("An unrelated legacy decision can be unreadable.")
            base = repo / "reviews/fixture/assessment.json"
            owner = coverage.read_json(base)
            owner["assessments"].extend([{"unused": "Historical control"}] * 2)
            base.write_text(json.dumps(owner))
            current = CurrentTeaching(repo)
            selection, selected = next(current.selected())
            self.assertEqual(selected.row, row)
            self.assertEqual(list(current.gallery()), [selected])
            self.assertEqual(current.resolve(export, "trunk").row, alternate)
            report = self.run_report(repo)
            self.assertEqual(report.returncode, 0, report.stderr)

            catalog = coverage.read_json(repo / SELECTIONS)
            catalog["families"]["fixture-family"]["label"] = "Renamed [family] | *example*"
            (repo / SELECTIONS).write_text(json.dumps(catalog))
            current = CurrentTeaching(repo)
            self.assertEqual(next(current.selected())[0].family_id, selection.family_id)
            register = render_register(current.selections)
            self.assertIn("| Renamed &#91;family&#93; &#124; &#42;example&#42; |", register)
            self.assertEqual(register_selections(register)[export].family, "Renamed [family] | *example*")
            pin = catalog["collections"][0]["families"][0]["exports"][0]
            pin["taskId"] = "trunk"
            (repo / SELECTIONS).write_text(json.dumps(catalog))
            self.assertIn("Stale maintained assessment pin", self.run_report(repo).stderr)

            pin["taskId"] = "branches"
            (repo / SELECTIONS).write_text(json.dumps(catalog))
            records = coverage.read_json(repo / ASSESSMENTS)
            records["assessments"][0]["review"] = "reviews/fixture/missing-review.json"
            (repo / ASSESSMENTS).write_text(json.dumps(records))
            self.assertIn("Missing or linked accepted review", self.run_report(repo).stderr)
            del records["assessments"][0]["review"]
            (repo / ASSESSMENTS).write_text(json.dumps(records))
            owner["assessments"][0]["task"] = "A different task."
            base.write_text(json.dumps(owner))
            self.assertIn("Base assessment pin differs", self.run_report(repo).stderr)

            records["assessments"].append(records["assessments"][0])
            (repo / ASSESSMENTS).write_text(json.dumps(records))
            self.assertIn("Duplicate assessment", self.run_report(repo).stderr)

    def test_generated_witnesses_bind_source_and_derivative_without_cache(self):
        accepted = "reviews/teaching-assessments/refinement-risk/accepted.json"
        outcomes = coverage.read_json(ROOT / accepted)["outcomes"]
        recipe = GALLERY_SITE / DISPLAY_RECIPE
        bindings = coverage.read_json(ROOT / recipe)
        witnesses = [item["before"] for item in outcomes
                     if "/display/" in item["before"]["path"] and item["before"]["path"].endswith(".webp")]
        self.assertEqual(len(witnesses), 2)
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary).resolve()
            for relative in (recipe, DELIVERY_INDEX):
                destination = repo / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            for claim in witnesses:
                path = claim["path"]
                with self.subTest(witness=path):
                    source = next(source for pairs in bindings.values() for source, target in pairs if target == path)
                    original = repo / source
                    original.parent.mkdir(parents=True, exist_ok=True)
                    digest, size = file_identity(ROOT, source)
                    pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {size}\n"
                    original.write_text(pointer)
                    target = repo / path
                    self.assertFalse(target.exists())
                    identities = AssessmentIdentities(repo)
                    self.assertEqual(identities.check(claim), (claim["sha256"], claim["bytes"]))

                    original.write_text(pointer.replace(digest, "0" * 64))
                    with self.assertRaisesRegex(ValueError, "Display source identity mismatch"):
                        identities.check(claim)
                    original.write_text(pointer)
                    with self.assertRaisesRegex(ValueError, "Identity mismatch"):
                        identities.check({**claim, "sha256": "0" * 64})

                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(b"unused display cache")
                    self.assertEqual(identities.check(claim), (claim["sha256"], claim["bytes"]))
                    wrong = {version: [pair for pair in pairs if pair[1] != path]
                             for version, pairs in bindings.items()}
                    (repo / recipe).write_text(json.dumps(wrong))
                    with self.assertRaisesRegex(ValueError, "Invalid display source binding"):
                        AssessmentIdentities(repo).check(claim)
                    (repo / recipe).write_text(json.dumps(bindings))


if __name__ == "__main__":
    unittest.main()
