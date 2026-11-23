from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "records/campaigns/teaching-asset-review/coverage.py"
spec = importlib.util.spec_from_file_location("teaching_review_coverage", SCRIPT)
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)
from teaching_assessments import register_rows, register_selections
from med_assets.artifacts import declared_identity
from med_assets.derivatives import AssessmentIdentities, DISPLAY_DERIVATIVES
from med_assets.teaching import (
    ASSESSMENTS, PROMOTION_JOURNAL, REGISTER, SCORECARD, SELECTIONS,
    CurrentTeaching, assessment_digest, render_register, render_scorecard,
)
from med_assets import teaching_promotion
from med_assets.artifacts import install_verified, verify_payload
from teaching_fixture import install_assessments, write_fixture


class TeachingReviewCoverage(unittest.TestCase):
    def fixture(self, repo):
        """Mirror the assessed inputs as pointers so the gate works without hydration."""
        documents = [
            coverage.REGISTER, coverage.PILOT, SELECTIONS,
            *(family["owner"] for family in coverage.read_json(ROOT / SELECTIONS)["families"].values() if "owner" in family),
            DISPLAY_DERIVATIVES,
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
            digest, size = declared_identity(ROOT, path)
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
            with patch("teaching_assessments.CurrentTeaching", return_value=current):
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
            with patch("teaching_assessments.CurrentTeaching", return_value=current):
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

            digest, size = declared_identity(repo, sibling)
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
                digest, size = declared_identity(repo, path)
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
        recipe = DISPLAY_DERIVATIVES
        bindings = coverage.read_json(ROOT / recipe)
        witnesses = [item["before"] for item in outcomes
                     if "/display/" in item["before"]["path"] and item["before"]["path"].endswith(".webp")]
        self.assertEqual(len(witnesses), 2)
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary).resolve()
            destination = repo / recipe
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / recipe).read_bytes())
            for claim in witnesses:
                path = claim["path"]
                with self.subTest(witness=path):
                    binding = next(binding for binding in bindings["derivatives"] if binding["output"]["path"] == path)
                    source = binding["source"]["path"]
                    original = repo / source
                    original.parent.mkdir(parents=True, exist_ok=True)
                    digest, size = declared_identity(ROOT, source)
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
                    wrong = json.loads(json.dumps(bindings))
                    bound = next(binding for binding in wrong["derivatives"] if binding["output"]["path"] == path)
                    bound["source"]["path"] = "wrong-source.png"
                    (repo / "wrong-source.png").write_bytes(b"unrelated source")
                    (repo / recipe).write_text(json.dumps(wrong))
                    with self.assertRaisesRegex(ValueError, "Display source identity mismatch"):
                        AssessmentIdentities(repo).check(claim)
                    (repo / recipe).write_text(json.dumps(bindings))


class TeachingPromotionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve()
        view = self.claim("reviews/capture.jpg", b"reviewed view")
        self.row = {
            "task": "Trace the visible branch.",
            "export": self.claim("models/control.glb", b"reviewed model"),
            "views": [view],
            "sources": [{"path": view["path"]}],
            "axes": [{"score": 3, "observation": "The branch is visible."}] * 4,
        }
        install_assessments(self.repo, [("trace-branch", self.row)], selected_task="trace-branch")
        self.update_views()

    def claim(self, path, raw):
        output = self.repo / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(raw)
        return {"path": path, "sha256": sha256(raw).hexdigest(), "bytes": len(raw)}

    def update_views(self):
        current = CurrentTeaching(self.repo)
        (self.repo / REGISTER).write_text(render_register(current.selections))
        scorecard = self.repo / SCORECARD
        scorecard.parent.mkdir(parents=True, exist_ok=True)
        scorecard.write_text(render_scorecard(current))

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "tools/maintained_teaching.py"),
                               "--repo", str(self.repo), *args], text=True, capture_output=True, check=False)

    def replacement_review(self):
        row = {**self.row, "export": self.claim("models/replacement.glb", b"replacement model"),
               "route": "library/fixture-family/replacement-r02"}
        row["axes"] = [{"score": 4, "observation": "Both boundaries are sharp."}, *row["axes"][1:]]
        review = "reviews/fixture/owner-review.json"
        batch = {"schemaVersion": 1, "date": "2026-11-23", "evaluator": "Owner", "rubric": {"revision": "fixture"},
                 "assessments": [row]}
        write_fixture(self.repo, review, batch)
        return row, review

    def promotion_args(self, row, review, *, disposition="maintained"):
        args = ["promote", "--review", review, "--reviewed-sha256", assessment_digest(row),
                "--export", row["export"]["path"], "--task-id", "trace-branch",
                "--collection-id", "fixture", "--family-id", "fixture-family", "--disposition", disposition]
        if disposition == "maintained":
            args += ["--replaces", self.row["export"]["path"]]
        return args

    def test_offline_teaching_command_checks_hidden_task_and_alternative(self):
        hidden = {**self.row, "task": "Inspect both boundaries."}
        alternative = {**self.row, "export": self.claim("models/alternative.glb", b"alternative model")}
        for task, row in (("hidden", hidden), ("alternative", alternative)):
            install_assessments(self.repo, [("trace-branch", self.row), (task, row)], selected_task="trace-branch")
            self.assertEqual(self.cli("--check").returncode, 0)
            catalog = json.loads((self.repo / ASSESSMENTS).read_text())
            catalog["assessments"][1]["sha256"] = "b" * 64
            write_fixture(self.repo, ASSESSMENTS, catalog)
            result = self.cli("--check")
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(f"Accepted assessment pin differs: {row['export']['path']} and task {task}", result.stderr)

        install_assessments(self.repo, [("trace-branch", self.row)], selected_task="trace-branch")
        historical = self.repo / "reviews/older/campaign-assessments.json"
        historical.parent.mkdir()
        historical.write_text("malformed unused historical review")
        self.assertEqual(self.cli("--check").returncode, 0)
        third = {**alternative, "task": "Inspect its cross section."}
        install_assessments(self.repo, [("trace-branch", self.row), ("alternative", alternative), ("third", third)],
                            selected_task="trace-branch")
        self.assertIn("Several current tasks without a selected assessment", self.cli("--check").stderr)

    def test_promotion_updates_compiled_library_recommendation(self):
        runtime_path = ROOT / "sites/anatomy-gallery/tools/gallery_runtime.py"
        recipe = importlib.util.spec_from_file_location("retained_gallery_runtime", runtime_path)
        runtime = importlib.util.module_from_spec(recipe)
        recipe.loader.exec_module(runtime)
        index = self.repo / "release/delivery-index.json"
        for file in (index, index.with_name("local-delivery.json")):
            write_fixture(self.repo, file.relative_to(self.repo).as_posix(), {"assets": []})
        self.row["route"] = "library/fixture-family/control-r01"
        install_assessments(self.repo, [("trace-branch", self.row)], selected_task="trace-branch")
        self.update_views()

        def compile_candidate():
            campaign = runtime.prepare_campaign_reviews(self.repo, index)
            js = '''
                import { readFileSync } from 'node:fs';
                import { libraryRows } from './sites/anatomy-gallery/app/src/content/gallery/library-compiler.js';
                import { compileLibrary, checkMembership } from './sites/anatomy-gallery/app/src/content/gallery/library-model.js';
                import { decodeLibrary } from './sites/anatomy-gallery/app/src/content/gallery/decode-library.js';
                import { compileResources } from './sites/anatomy-gallery/app/src/content/shared/release-resources.js';

                const reviews = { assessments: [], campaign: JSON.parse(readFileSync(0, 'utf8')) };
                const packages = [{ id: 'fixture-family', label: 'Teaching fixture', media: [] }];
                const selected = libraryRows(reviews, { packages, selected: {} }).filter(row => row.id === 'fixture-family');
                const catalog = compileLibrary(selected, reviews);
                const publicIndex = { assets: [] };
                const resources = compileResources({ selection: 'candidate', publicIndex, reviews,
                  localDelivery: { assets: [], receipts: [] }, legacyDental: { assets: [] }, archive: [] });
                checkMembership(catalog, publicIndex, resources);
                const { rows: [row] } = decodeLibrary(catalog);
                console.log(JSON.stringify({
                  recommended: row.recommended.library, assessment: row.recommended.assessment,
                  history: row.history.map(revision => revision.library),
                  routes: resources.map(resource => resource.url),
                }));
            '''
            result = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT,
                                    input=json.dumps(campaign), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        self.assertEqual(compile_candidate()["recommended"], self.row["route"])
        row, review = self.replacement_review()
        row["task"] = "Find both sharp boundaries."
        batch = json.loads((self.repo / review).read_text())
        batch["assessments"] = [row]
        write_fixture(self.repo, review, batch)
        args = self.promotion_args(row, review)
        args[args.index("--task-id") + 1] = "locate-boundaries"
        dry_run = self.cli(*args)
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        applied = self.cli(*args, "--apply", "--expect-state", json.loads(dry_run.stdout)["planSha256"])
        self.assertEqual(applied.returncode, 0, applied.stderr)
        built = compile_candidate()
        self.assertEqual(built["recommended"], row["route"])
        self.assertEqual(built["assessment"]["taskId"], "locate-boundaries")
        self.assertEqual(built["assessment"]["export"], row["export"])
        self.assertEqual(built["assessment"]["axes"][0]["score"], 4)
        self.assertIn(self.row["route"], built["history"])
        for export in (self.row["export"], row["export"]):
            self.assertIn(f"/assets/{export['sha256']}/{Path(export['path']).name}", built["routes"])

    def test_promotion_dry_run_rejects_stale_plan_and_applies_idempotently(self):
        row, review = self.replacement_review()
        args = self.promotion_args(row, review)
        before = teaching_promotion.read_state(self.repo)
        dry_run = self.cli(*args)
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        plan = json.loads(dry_run.stdout)
        self.assertEqual(plan["disposition"], "maintained")
        self.assertEqual(plan["assessmentAfter"]["axes"][0]["score"], 4)
        self.assertEqual(plan["assessmentAfter"]["route"], "library/fixture-family/replacement-r02")
        self.assertEqual(plan["assessmentAfter"]["evidence"]["views"], self.row["views"])
        self.assertEqual(plan["selectionBefore"][0]["path"], self.row["export"]["path"])
        self.assertEqual(plan["selectionAfter"][0]["path"], row["export"]["path"])
        self.assertEqual(teaching_promotion.read_state(self.repo), before)

        register = json.loads((self.repo / SELECTIONS).read_text())
        register["families"]["fixture-family"]["label"] = "Renamed display label"
        write_fixture(self.repo, SELECTIONS, register)
        stale_state = teaching_promotion.read_state(self.repo)
        rejected = self.cli(*args, "--apply", "--expect-state", plan["planSha256"])
        self.assertIn("Promotion plan is stale", rejected.stderr)
        self.assertEqual(teaching_promotion.read_state(self.repo), stale_state)
        plan = json.loads(self.cli(*args).stdout)
        self.assertEqual(plan["assessmentAfter"]["taskId"], "trace-branch")

        applied = self.cli(*args, "--apply", "--expect-state", plan["planSha256"])
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual(self.cli("--check").returncode, 0)
        teaching = CurrentTeaching(self.repo)
        self.assertEqual(set(teaching.selections), {"models/replacement.glb"})
        self.assertEqual({record.row["export"]["path"] for record in teaching.gallery()},
                         {"models/control.glb", "models/replacement.glb"})
        repeated = self.cli(*args, "--apply", "--expect-state", plan["planSha256"])
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertEqual(json.loads(repeated.stdout)["changedFiles"], [])

    def test_invalid_review_does_not_mutate_and_alternative_keeps_selection(self):
        row, review = self.replacement_review()
        args = self.promotion_args(row, review, disposition="alternative")
        before = teaching_promotion.read_state(self.repo)
        wrong = args.copy()
        wrong[wrong.index("--export") + 1] = self.row["export"]["path"]
        self.assertIn("different export", self.cli(*wrong).stderr)
        stale = args.copy()
        stale[stale.index("--reviewed-sha256") + 1] = "e" * 64
        self.assertIn("assessment pin is stale", self.cli(*stale).stderr)
        view = self.repo / self.row["views"][0]["path"]
        raw = view.read_bytes()
        view.unlink()
        self.assertIn("Missing artifact file", self.cli(*args).stderr)
        self.assertEqual(teaching_promotion.read_state(self.repo), before)
        view.write_bytes(raw)

        plan = json.loads(self.cli(*args).stdout)
        self.assertEqual(plan["changedFiles"], [ASSESSMENTS])
        self.assertEqual(plan["selectionBefore"], plan["selectionAfter"])
        result = self.cli(*args, "--apply", "--expect-state", plan["planSha256"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.cli("--check").returncode, 0)

    def test_review_row_discovery_and_new_family(self):
        row, review = self.replacement_review()
        args = self.promotion_args(row, review)
        pin_index = args.index("--reviewed-sha256")
        del args[pin_index:pin_index + 2]
        del args[-2:]
        args[args.index("--family-id") + 1] = "replacement-family"
        args += ["--new-family-label", "Replacement family"]
        dry_run = self.cli(*args)
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        plan = json.loads(dry_run.stdout)
        self.assertEqual(plan["reviewedSha256"], assessment_digest(row))
        self.assertEqual(plan["familyId"], "replacement-family")
        self.assertTrue(plan["galleryMembership"])

        batch = json.loads((self.repo / review).read_text())
        competing = {**row, "decision": "Alternate interpretation of the same task."}
        batch["assessments"].append(competing)
        write_fixture(self.repo, review, batch)
        ambiguous = self.cli(*args)
        self.assertIn("several matching assessments", ambiguous.stderr)
        self.assertIn(assessment_digest(competing), ambiguous.stderr)
        args += ["--reviewed-sha256", assessment_digest(row)]
        pinned = self.cli(*args)
        self.assertEqual(pinned.returncode, 0, pinned.stderr)
        plan = json.loads(pinned.stdout)
        applied = self.cli(*args, "--apply", "--expect-state", plan["planSha256"])
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual(self.cli("--check").returncode, 0)
        self.assertEqual(json.loads((self.repo / SELECTIONS).read_text())["families"]["replacement-family"],
                         {"label": "Replacement family"})
        args[args.index("--new-family-label") + 1] = "Attempt to rename existing family"
        self.assertIn("distinct stable ID and label", self.cli(*args).stderr)

    def test_interrupted_promotion_recovers_and_refuses_conflicting_edits(self):
        row, review = self.replacement_review()
        promotion = teaching_promotion.Promotion(review, assessment_digest(row), row["export"]["path"],
                                                "trace-branch", "fixture", "fixture-family", "maintained",
                                                self.row["export"]["path"])
        plan = teaching_promotion.promote(self.repo, promotion)
        write_atomic = teaching_promotion.write_atomic

        def interrupt(path, content):
            if path == self.repo / SELECTIONS:
                raise OSError("simulated interruption")
            return write_atomic(path, content)

        with patch.object(teaching_promotion, "write_atomic", side_effect=interrupt):
            with self.assertRaisesRegex(OSError, "simulated interruption"):
                teaching_promotion.promote(self.repo, promotion, apply=True, expect_state=plan["planSha256"])
        self.assertTrue((self.repo / PROMOTION_JOURNAL).is_file())
        self.assertIn("Interrupted teaching promotion", self.cli("--check").stderr)
        path = self.repo / REGISTER
        original = path.read_text()
        path.write_text("independent edit")
        self.assertIn("Promotion conflicts with an edit".lower(), self.cli("recover").stderr.lower())
        self.assertEqual(path.read_text(), "independent edit")
        path.write_text(original)
        self.assertEqual(self.cli("recover").returncode, 0)
        self.assertFalse((self.repo / PROMOTION_JOURNAL).exists())
        self.assertEqual(self.cli("--check").returncode, 0)

    def test_verified_install_distinguishes_pointer_conflict_and_exact_replay(self):
        raw = b"known payload"
        claim = self.claim("models/staged.glb", raw)
        staged = self.repo / claim["path"]
        target = self.repo / "models/restored.glb"
        target.write_text(f"version https://git-lfs.github.com/spec/v1\noid sha256:{claim['sha256']}\nsize {len(raw)}\n")
        self.assertEqual(declared_identity(self.repo, "models/restored.glb"), (claim["sha256"], len(raw)))
        with self.assertRaisesRegex(ValueError, "Unresolved LFS pointer"):
            verify_payload(target, claim)
        with self.assertRaisesRegex(ValueError, "Unresolved LFS pointer"):
            install_verified(staged, target, claim)
        target.unlink()
        target.symlink_to(staged)
        with self.assertRaisesRegex(ValueError, "Linked artifact path"):
            install_verified(staged, target, claim)
        target.unlink()
        self.assertTrue(install_verified(staged, target, claim))
        self.assertFalse(install_verified(staged, target, claim))
        self.assertEqual(target.read_bytes(), raw)

    def test_concurrent_apply_serializes_and_reuses_the_result(self):
        row, review = self.replacement_review()
        args = self.promotion_args(row, review)
        plan = json.loads(self.cli(*args).stdout)
        apply = [*args, "--apply", "--expect-state", plan["planSha256"]]
        with ThreadPoolExecutor(max_workers=2) as workers:
            writes = [workers.submit(self.cli, *apply) for _ in range(2)]
        results = []
        for write in writes:
            result = write.result()
            self.assertEqual(result.returncode, 0, result.stderr)
            results.append(json.loads(result.stdout)["status"])
        self.assertCountEqual(results, ["applied", "unchanged"])
        self.assertEqual(self.cli("--check").returncode, 0)


if __name__ == "__main__":
    unittest.main()
