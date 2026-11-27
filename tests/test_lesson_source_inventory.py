"""Verify author-owned lesson coverage without hydrating playback media."""

import json
import subprocess
import unittest
from collections import Counter
from hashlib import sha256
from pathlib import Path

from med_assets.artifacts import repo_file

ROOT = Path(__file__).resolve().parents[1]
ULTRASOUND = ROOT / "experiments/ultrasound-sweep"


def load(path):
    return json.loads(path.read_bytes())


class LessonSourceInventoryTest(unittest.TestCase):
    def test_body_systems_reviewed_stops_and_display_inventory(self):
        owner = ROOT / "lessons/body-systems"
        index = (owner / "display/index.json").read_bytes()
        review = load(owner / "reviewed-stops.json")
        self.assertEqual(sha256(index).hexdigest(), review["displayIndexSha256"])
        rows = json.loads(index)
        systems = {row["id"]: row["plates"] for row in rows}
        stops = {row["system"]: row for row in review["stops"]}
        self.assertEqual(len(rows), 11)
        self.assertEqual(len(review["stops"]), 11)
        self.assertEqual(len(systems), 11)
        self.assertEqual(len(stops), 11)
        self.assertEqual(systems.keys(), stops.keys())
        details = 0
        for system, plates in systems.items():
            keys = {(plate["kind"], plate["id"]) for plate in plates}
            self.assertEqual(len(keys), len(plates), system)
            self.assertTrue(any(kind == "assembly" for kind, _ in keys), system)
            self.assertIn(("detail", stops[system]["detail"]), keys, system)
            for plate in plates:
                self.assertTrue(plate["frames"], plate["id"])
                for frame in plate["frames"]:
                    self.assertTrue(repo_file(ROOT, frame["path"]).is_file(), frame["path"])
            details += sum(kind == "detail" for kind, _ in keys)
        self.assertGreaterEqual(details, 30)

    def test_ultrasound_case_tours_and_reference_inventory(self):
        visits = [
            {"owner": path.parent.name, "record": record}
            for path in sorted((ULTRASOUND / "cases").glob("*/cases.json"))
            for record in load(path)
        ]
        case_ids = {visit["record"]["id"] for visit in visits}
        self.assertEqual(len(case_ids), len(visits))
        self.assertEqual(len(case_ids), 32)
        views = [view for visit in visits for view in visit["record"]["views"]]
        self.assertEqual(len(views), 163)
        chapters = json.loads(
            subprocess.run(
                ["node", str(ULTRASOUND / "tours/case-evidence.mjs")],
                input=json.dumps(visits),
                text=True,
                stdout=subprocess.PIPE,
                check=True,
            ).stdout
        )
        self.assertEqual(chapters.keys(), case_ids)
        self.assertEqual(sum(map(len, chapters.values())), 410)

        sweeps = [
            sweep["id"]
            for path in sorted(ULTRASOUND.glob("*-track*.json"))
            for sweep in load(path).get("sweeps", [])
        ]
        self.assertEqual(len(sweeps), 16)
        self.assertEqual(len(set(sweeps)), len(sweeps))

        reference_ids = Counter(
            key
            for path in sorted((ULTRASOUND / "research").glob("*.json"))
            for key, row in load(path).items()
            if isinstance(row, dict)
            and {"path", "sourceMedia", "url", "sha256", "sourceSha256"} & row.keys()
        )
        for name in ("carotid-survey/sources.json", "cases/acquired/references.json"):
            reference_ids.update(load(ULTRASOUND / name).keys())
        cardiac = load(ULTRASOUND / "cardiac/reference/sources.json")
        reference_ids.update(
            f"bse-{row['number']}" for panels in cardiac["panels"].values() for row in panels
        )
        reference_ids.update(f"cine-{name}" for name in cardiac["cine"])
        self.assertTrue(load(ULTRASOUND / "cardiac/acquisition.json")["file"])
        reference_ids.update(["cardiac-a4c"])
        self.assertGreaterEqual(sum(reference_ids.values()), 100)
        used = {ref for view in views for ref in view.get("referenceIds", [])}
        self.assertTrue(used)
        self.assertEqual({ref: reference_ids[ref] for ref in used if reference_ids[ref] != 1}, {})

    def test_structured_ovary_lesson_has_both_asset_references(self):
        lesson = load(ROOT / "lessons/ovary-tubal-context/lesson.json")
        for path in (lesson["localization"]["export"], lesson["source"]["model"]):
            self.assertTrue(repo_file(ROOT, path).is_file(), path)
