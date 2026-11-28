"""Native curation uses the current exact identity while legacy workspaces remain usable."""

from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path

import pytest
from med_assets.teaching import ASSESSMENTS, SELECTIONS
from typer.testing import CliRunner

from assetkit import Workspace
from assetkit.cli import app
from assetkit.curation import Review
from assetkit.workspace import ShowAssetResult

ASSET = "anatomy:fixture:review"
MAIN = "models/fixture/main.glb"
SIBLING = "models/fixture/sibling.glb"
MANIFEST = "models/fixture/assets.json"


def _write(repo: Path, relative: str, contents: bytes) -> dict:
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(contents)
    return {
        "path": relative,
        "sha256": hashlib.sha256(contents).hexdigest(),
        "bytes": len(contents),
    }


def _write_json(repo: Path, relative: str, value: dict) -> None:
    _write(repo, relative, json.dumps(value).encode())


def _fixture(repo: Path, *, score: int | None = 0) -> None:
    pin = _write(repo, MAIN, b"fixture export")
    sibling = _write(repo, SIBLING, b"fixture export")
    _write_json(
        repo,
        MANIFEST,
        {
            "schemaVersion": 1,
            "assets": [
                {
                    "id": ASSET,
                    "title": "Review fixture",
                    "kind": "model",
                    "revisions": [
                        {
                            "id": "r01",
                            "exports": [{"id": "main", **pin}, {"id": "sibling", **sibling}],
                        },
                    ],
                },
            ],
        },
    )
    first_view = _write(repo, "reviews/fixture/main.webp", b"main view")
    sibling_view = _write(repo, "reviews/fixture/sibling.webp", b"sibling view")
    source = _write(repo, "reviews/fixture/README.md", b"Fixture source")
    row = {
        "export": pin,
        "task": "Find main feature",
        "views": [first_view],
        "axes": [
            {"score": value, "observation": "Fixture observation"} for value in (score, 3, 3, 4)
        ],
        "sources": [{"path": source["path"]}],
    }
    other = {**row, "export": sibling, "task": "Find sibling feature", "views": [sibling_view]}
    fixture = Path(__file__).resolve().parents[3] / "tests/teaching_fixture.py"
    install_assessments = runpy.run_path(str(fixture))["install_assessments"]
    install_assessments(
        repo, [("main-task", row), ("sibling-task", other)], selected_task="main-task"
    )


@pytest.mark.parametrize("score", [0, None])
def test_review_matches_exact_export_and_preserves_original_scores(
    tmp_path: Path, score: int | None
) -> None:
    _fixture(tmp_path, score=score)
    workspace = Workspace.load(tmp_path, include_legacy_adapters=False)
    shown = workspace.show(f"{ASSET}@r01:main")
    assert isinstance(shown, ShowAssetResult)
    assert [exp.path for rev in shown.revisions for exp in rev.exports] == [MAIN]
    (review,) = shown.reviews
    assert isinstance(review, Review)
    assert review.task_id == "main-task"
    assert review.rubric == {"revision": "fixture"}
    assert review.scores["axis1"] is score
    if score is None:
        assert "scoreTotal" not in review.to_dict()
    else:
        assert review.score_total == 10
    assert not shown.qualifications and not shown.revisions[0].exports[0].qualification.qualified
    assert [selection.review_id for selection in shown.selections] == [review.id]
    assert workspace.impact(MAIN).reviews == (review,)
    (sibling_review,) = workspace.impact(SIBLING).reviews
    assert isinstance(sibling_review, Review) and sibling_review.task_id == "sibling-task"
    assert not workspace.impact(SIBLING).selections


@pytest.mark.parametrize("field", ["sha256", "bytes"])
def test_record_pin_mismatch_cannot_attach_current_review_or_selection(
    tmp_path: Path, field: str
) -> None:
    _fixture(tmp_path)
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    export = manifest["assets"][0]["revisions"][0]["exports"][0]
    export[field] = "f" * 64 if field == "sha256" else export["bytes"] + 1
    _write_json(tmp_path, MANIFEST, manifest)
    for include_legacy in (False, True):
        workspace = Workspace.load(tmp_path, include_legacy_adapters=include_legacy)
        shown = workspace.show(MAIN)
        assert isinstance(shown, ShowAssetResult)
        assert not shown.reviews and not shown.selections
        assert not shown.revisions[0].exports[0].qualification.review_ids
        assert not workspace.impact(MAIN).reviews and not workspace.impact(MAIN).selections


def test_legacy_discovery_is_scoped_and_incomplete_current_store_fails_closed(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    (tmp_path / SELECTIONS).unlink()
    assert not Workspace.load(tmp_path, include_legacy_adapters=False).impact(MAIN).reviews
    with pytest.raises(ValueError, match="Missing artifact file.*maintained-selections.json"):
        Workspace.load(tmp_path)

    (tmp_path / ASSESSMENTS).unlink()
    old = json.loads((tmp_path / "reviews/fixture/assessment.json").read_bytes())
    _write_json(tmp_path, "reviews/teaching-assessments/old.json", old)
    assert not Workspace.load(tmp_path, include_legacy_adapters=False).impact(MAIN).reviews
    (review,) = Workspace.load(tmp_path).impact(MAIN).reviews
    assert review.kind == "legacy-assessment"


def test_targeted_native_load_skips_unrelated_review_evidence(tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / "reviews/fixture/sibling.webp").unlink()
    for command in ("show", "impact"):
        result = CliRunner().invoke(app, ["--repo", str(tmp_path), "--native-only", command, MAIN])
        assert result.exit_code == 0, result.output
        (review,) = json.loads(result.output)["reviews"]
        assert review["taskId"] == "main-task"
    with pytest.raises(ValueError, match="Missing artifact file.*sibling.webp"):
        Workspace.load(tmp_path, include_legacy_adapters=False)
