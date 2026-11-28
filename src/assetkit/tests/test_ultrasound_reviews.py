from __future__ import annotations

import json
import shutil
from hashlib import sha256
from pathlib import Path

import pytest
from med_assets.artifacts import declared_identity
from med_assets.ultrasound_review import RUBRIC_PATH, recipe_hashes, validate_reviews

from assetkit import AssetKitError, AssetRegistry
from assetkit.ultrasound_reviews import (
    ECHO_CASES,
    ECHO_REVIEW_ID,
    LIVER_REVIEW_ID,
    LIVER_TRACK,
    REVIEW_ROOT,
    load_ultrasound_reviews,
)

REPO = Path(__file__).resolve().parents[3]
LIVER_RECORD = "models/liver_s1233/asset.record.json"
LIVER_MESH = "models/liver_s1233/exports/r01/liver.mesh"
LIVER_HASH = "27862cad9d34d1d7a7b86a1ce8d92014f5d7db534788c45cb4ef9fd1cce20089"
ECHO_HASH = "80f5885a9577c09534edc72958c58941e6da5c419de85dc430fa0e3a3ff0bf95"
RUBRIC_HASH = "a38e552869511cd5bceacaa5ea4456f4d0530e58e7dce2bc6855587a98b0e684"


def test_pilot_reads_existing_workbench_reviews_without_generated_delivery() -> None:
    registry = AssetRegistry.load_records(REPO, (LIVER_RECORD,))
    liver, echo = load_ultrasound_reviews(REPO, registry)
    assert liver.id == LIVER_REVIEW_ID
    assert liver.owner_path == f"{REVIEW_ROOT}/originals/reviews.json"
    assert liver.binding_owner == LIVER_TRACK
    assert liver.export_ref is not None
    assert liver.export_ref.record == LIVER_RECORD
    assert liver.export_ref.revision == "r01"
    assert liver.export_ref.export == "liver"
    assert liver.export_path == LIVER_MESH
    assert liver.mesh_sha256 == LIVER_HASH
    assert (liver.case, liver.chapter, liver.part) == ("liver", None, "liver")
    assert liver.score_total == 14 and liver.score_maximum == 16
    assert liver.scores == {"fidelity": 3, "form": 3, "readability": 4, "economy": 4}
    assert "0.66 mm" in liver.score_evidence["fidelity"]
    assert "broad right lobe" in liver.task
    assert liver.reviewer == "Codex · agent assessment"
    assert liver.reviewed_on == "2026-11-26"
    assert liver.rubric == f"{RUBRIC_PATH} @ 964ad706"
    assert liver.rubric_sha256 == RUBRIC_HASH
    assert all("liver-" in image.path for image in liver.images)
    assert liver.recipe_sha256 is None

    assert echo.id == ECHO_REVIEW_ID
    assert echo.owner_path == f"{REVIEW_ROOT}/echo/reviews.json"
    assert echo.binding_owner == ECHO_CASES
    assert (echo.case, echo.chapter, echo.part) == (
        "echo-aortic-stenosis",
        "psax-av-section",
        "Aortic valve cusp 1",
    )
    assert echo.binding_status == "recorded"
    assert echo.recipe_sha256 == ECHO_HASH
    assert echo.export_ref is echo.export_path is echo.mesh_sha256 is None
    assert echo.score_total == 15 and echo.score_maximum == 16
    assert "Trace the free edge" in echo.task and "216 triangles" in echo.score_evidence["economy"]
    assert echo.reviewer == "Codex agent review" and echo.reviewed_on == "2026-11-26"
    assert echo.rubric == RUBRIC_PATH and echo.rubric_sha256 == RUBRIC_HASH
    assert "modeled leaflet" in echo.limits[0] and "without assigning clinical" in echo.limits[0]
    assert "stated task" in echo.scope
    assert {Path(image.path).name for image in echo.images} >= {
        "candidate-oblique.webp",
        "candidate-closed.webp",
    }


def copy_file(root: Path, relative: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO / relative, path)
    return path


def test_liver_requires_an_exact_governed_mesh_and_accepts_pointer_identity(tmp_path: Path) -> None:
    root = tmp_path
    for relative in (LIVER_RECORD, LIVER_TRACK, RUBRIC_PATH):
        copy_file(root, relative)
    folder = f"{REVIEW_ROOT}/originals"
    shutil.copytree(REPO / folder, root / folder)
    witness = f"{folder}/liver-native-oblique.webp"
    for relative in (LIVER_MESH, witness):
        digest, length = declared_identity(REPO, relative)
        blob = root / relative
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_text(
            f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {length}\n"
        )
    registry = AssetRegistry.load_records(root, (LIVER_RECORD,))
    (result,) = load_ultrasound_reviews(root, registry, target=LIVER_REVIEW_ID)
    assert result.binding_status == "recorded" and result.mesh_sha256 == LIVER_HASH
    track_path = root / LIVER_TRACK
    text = track_path.read_text()
    track_path.write_text(text.replace("anatomy:s1233:liver-window", "anatomy:hra:liver"))
    assert load_ultrasound_reviews(root, registry, target=LIVER_REVIEW_ID) == ()
    track_path.write_text(text)
    (root / LIVER_MESH).write_bytes(b"different mesh")
    assert load_ultrasound_reviews(root, registry, target=LIVER_REVIEW_ID) == ()
    (root / witness).write_bytes(b"different reviewed image")
    with pytest.raises(AssetKitError, match="review evidence identity mismatch"):
        load_ultrasound_reviews(root, registry, target=LIVER_REVIEW_ID)
    assert load_ultrasound_reviews(root, registry, target=ECHO_REVIEW_ID) == ()


def test_supplied_echo_delivery_recomputes_the_recipe_before_verifying(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    cases = copy_file(repo, ECHO_CASES)
    owner = f"{REVIEW_ROOT}/echo"
    shutil.copytree(REPO / owner, repo / owner)
    delivery = tmp_path / "delivery"
    rubric = delivery / "development/asset-rubric.md"
    rubric.parent.mkdir(parents=True)
    shutil.copyfile(REPO / RUBRIC_PATH, rubric)
    scene = delivery / "case-scene.js"
    scene.write_text("export const scene = 'fixture';")
    (delivery / "scene.js").write_text("export const common = 'fixture';")
    case = next(row for row in json.loads(cases.read_text()) if row["id"] == "echo-aortic-stenosis")
    manifest_cases = [
        {
            "id": case["id"],
            "family": "echo",
            "owner": "echo",
            "record": case,
            "chapters": [{"id": "psax-av-section"}],
        }
    ]
    manifest = {
        "version": 1,
        "cases": manifest_cases,
        "rubricHash": sha256(rubric.read_bytes()).hexdigest(),
        "recipeHashes": recipe_hashes(delivery, {"echo"}, manifest_cases, rubric=rubric),
    }
    index = delivery / "development/asset-inventory.json"
    index.write_text(json.dumps(manifest))
    review_path = repo / owner / "reviews.json"
    review = json.loads(review_path.read_text())
    review["recipeHash"] = manifest["recipeHashes"]["echo"]
    review_path.write_text(json.dumps(review))
    registry = AssetRegistry()
    (echo,) = load_ultrasound_reviews(repo, registry, delivery=delivery, target=ECHO_REVIEW_ID)
    assert echo.binding_status == "verified" and echo.export_ref is None
    manifest_cases[0]["chapters"][0]["id"] = "different-chapter"
    index.write_text(json.dumps(manifest))
    with pytest.raises(AssetKitError, match="lacks the reviewed echo case and chapter"):
        load_ultrasound_reviews(repo, registry, delivery=delivery, target=ECHO_REVIEW_ID)
    manifest_cases[0]["chapters"][0]["id"] = "psax-av-section"
    case["id"] = "different-cardiac-episode"
    index.write_text(json.dumps(manifest))
    with pytest.raises(AssetKitError, match="lacks the reviewed echo case and chapter"):
        load_ultrasound_reviews(repo, registry, delivery=delivery, target=ECHO_REVIEW_ID)
    case["id"] = "echo-aortic-stenosis"
    index.write_text(json.dumps(manifest))
    scene.write_text("export const scene = 'another';")
    with pytest.raises(AssetKitError, match="differs from the reviewed echo recipe"):
        load_ultrasound_reviews(repo, registry, delivery=delivery, target=ECHO_REVIEW_ID)
    (recorded,) = load_ultrasound_reviews(repo, registry, target=ECHO_REVIEW_ID)
    assert recorded.binding_status == "recorded"


def test_malformed_workbench_witness_remains_a_missing_image_error(tmp_path: Path) -> None:
    path = tmp_path / "asset-reviews/pilot/reviews.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "records": [
                    {
                        "case": "fixture",
                        "part": "rim",
                        "task": "Trace the rim",
                        "revision": "fixture",
                        "rubric": "fixture",
                        "reviewer": "fixture",
                        "reviewedOn": "fixture",
                        "comparison": {"candidate": "asset-reviews/pilot/missing.webp"},
                    }
                ],
            }
        )
    )
    with pytest.raises(ValueError, match="Missing or unbound asset review image"):
        validate_reviews(path)
