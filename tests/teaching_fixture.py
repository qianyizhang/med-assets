"""Small on-disk fixtures for the current teaching record contract."""
import json

from assessment_identity import DELIVERY_INDEX, DISPLAY_RECIPE, GALLERY_SITE
from maintained_teaching import ASSESSMENTS, SELECTIONS
from teaching_assessments import assessment_digest


def write_fixture(repo, relative, value):
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def install_assessments(repo, rows, *, selected_task):
    owner = "reviews/fixture/assessment.json"
    attribution = {"date": "2026-11-22", "evaluator": "Fixture reviewer", "rubric": {"revision": "fixture"}}
    write_fixture(repo, owner, {"schemaVersion": 1, **attribution, "assessments": [row for _, row in rows]})
    records = []
    for task_id, row in rows:
        record = {
            "path": row["export"]["path"], "taskId": task_id,
            "base": {"path": owner, "sha256": assessment_digest(row)},
            "sha256": assessment_digest({"owner": owner, "attribution": attribution, "assessment": row, "taskId": task_id}),
        }
        records.append(record)
    selected = next(row for row in records if row["taskId"] == selected_task)
    write_fixture(repo, ASSESSMENTS, {"schemaVersion": 1, "attributions": {}, "assessments": records})
    write_fixture(repo, SELECTIONS, {
        "schemaVersion": 1, "families": {"fixture-family": {"label": "Fixture family"}},
        "collections": [{"id": "fixture", "label": "Fixture", "families": [{"id": "fixture-family", "exports": [
            {"path": selected["path"], "taskId": selected_task, "assessmentSha256": selected["sha256"]},
        ]}]}],
    })
    write_fixture(repo, DELIVERY_INDEX, {"assets": []})
    write_fixture(repo, GALLERY_SITE / DISPLAY_RECIPE, {})
