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
            sibling = next(path for path in coverage.GAPS if "distal-sampling" in path)
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
            register.write_text(register.read_text().replace("| Left lung · s1233 |", "| Left lung · renamed |"))
            drift = self.run_report(repo, "--check", report)
            self.assertEqual(drift.returncode, 1)
            self.assertIn("Coverage report drift.", drift.stderr)
            self.assertIn("Renamed or regrouped", self.run_report(repo).stdout)


if __name__ == "__main__":
    unittest.main()
