"""Read exact mesh and recipe reviews from the ultrasound workbench."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from med_assets.artifacts import repo_file, unique_keys
from med_assets.ultrasound_review import (
    AXES,
    MAX_AXIS_SCORE,
    RUBRIC_PATH,
    recipe_hashes,
    review_images,
    validate_reviews,
)
from pydantic import Field

from .blobs import HEX64, safe_path, verify
from .errors import AssetKitError
from .models import AssetModel
from .registry import RecordExportRef
from .ultrasound import SweepSceneAssetRef

if TYPE_CHECKING:
    from .registry import Asset, AssetRegistry, Export, Revision

SWEEP_ROOT = "experiments/ultrasound-sweep"
REVIEW_ROOT = f"{SWEEP_ROOT}/development/asset-reviews"
LIVER_TRACK = f"{SWEEP_ROOT}/abdomen-tracks.json"
ECHO_CASES = f"{SWEEP_ROOT}/cases/echo/cases.json"
LIVER_REVIEW_ASSET = "anatomy:s1233:liver-window"
LIVER_REVIEW_ID = "ultrasound:sweep:liver:liver"
ECHO_REVIEW_ID = "ultrasound:case:echo-aortic-stenosis:psax-av-section:aortic-valve-cusp-1"


class ReviewImage(AssetModel):
    path: str
    sha256: str


class UltrasoundReview(AssetModel):
    """A reviewed learner task on a packed mesh or a worked-case recipe."""

    id: str
    kind: Literal["mesh", "recipe"]
    binding_status: Literal["recorded", "verified"]
    owner_path: str
    binding_owner: str
    case: str
    chapter: str | None = None
    part: str
    task: str
    reviewer: str
    reviewed_on: str
    reviewed_revision: str
    rubric: str
    rubric_sha256: str
    scores: dict[str, int | None] = Field(default_factory=dict)
    score_evidence: dict[str, str] = Field(default_factory=dict)
    score_total: int | None = None
    score_maximum: int | None = None
    scope: str
    limits: tuple[str, ...]
    images: tuple[ReviewImage, ...]
    export_ref: RecordExportRef | None = None
    export_path: str | None = None
    mesh_sha256: str | None = None
    chapter_sha256: str | None = None
    recipe_sha256: str | None = None


def _read_json(path: Path) -> Any:
    return json.loads(path.read_bytes(), object_pairs_hook=unique_keys)


def _select(records, source: str, case: str, chapter: str | None, part: str):
    matches = [
        record
        for record in records
        if (record.get("source"), record.get("case"), record.get("chapter"), record.get("part"))
        == (source, case, chapter, part)
    ]
    if len(matches) > 1:
        raise AssetKitError(f"Ambiguous ultrasound review for {case} / {chapter} / {part}")
    return matches[0] if matches else None


def _review_fields(repo: Path, path: Path, package, record) -> dict[str, Any]:
    scores = record.get("scores", {})
    score_evidence = record.get("scoreEvidence", {})
    complete = scores.keys() == AXES and all(value is not None for value in scores.values())
    images = tuple(
        ReviewImage(
            path=(path.parents[2] / image).relative_to(repo).as_posix(),
            sha256=package["evidenceSha256"][
                (path.parents[2] / image).relative_to(path.parent).as_posix()
            ],
        )
        for image in review_images(record)
    )
    return dict(
        owner_path=path.relative_to(repo).as_posix(),
        case=record["case"],
        chapter=record.get("chapter"),
        part=record["part"],
        task=record["task"],
        reviewer=record["reviewer"],
        reviewed_on=record["reviewedOn"],
        reviewed_revision=record["revision"],
        rubric=record["rubric"],
        rubric_sha256=package["rubricHash"],
        scores=scores,
        score_evidence=score_evidence,
        score_total=sum(scores.values()) if complete else None,
        score_maximum=len(AXES) * MAX_AXIS_SCORE if complete else None,
        scope="Retained ultrasound workbench evidence for the stated task.",
        limits=(record["note"],) if record.get("note") else (),
        images=images,
    )


def _mesh_review_id(record) -> str:
    return ":".join(
        field
        for field in (
            "ultrasound",
            record["source"],
            record["case"],
            record.get("chapter"),
            record["part"],
        )
        if field
    )


def _liver_binding(repo: Path, package, record) -> SweepSceneAssetRef | None:
    """Retain the pilot's original track and rubric check for its digest-only review."""
    track_file = safe_path(repo, LIVER_TRACK)
    rubric = safe_path(repo, RUBRIC_PATH)
    if not track_file.is_file() or not rubric.is_file():
        return None
    if sha256(rubric.read_bytes()).hexdigest() != package["rubricHash"]:
        return None
    tracks = [
        track for track in _read_json(track_file)["sweeps"] if track.get("id") == record["case"]
    ]
    if len(tracks) != 1:
        return None
    raw_ref = tracks[0].get("sceneAssets", {}).get(record["part"])
    if not raw_ref or record["part"] not in tracks[0].get("parts", []):
        return None
    ref = SweepSceneAssetRef.model_validate(raw_ref)
    return ref if ref.asset == LIVER_REVIEW_ASSET else None


def _mesh_review(
    repo: Path, path: Path, package, record, match: tuple[Asset, Revision, Export]
) -> UltrasoundReview | None:
    asset, revision, export = match
    mesh_hash = record["meshSha256"]
    owner = asset.source_manifest
    if owner is None or export.bytes is None:
        return None
    ref = RecordExportRef(asset=asset.id, revision=revision.id, export=export.id, record=owner)
    export_key = f"{ref.asset}@{ref.revision}:{ref.export}"
    if "@" in record["revision"] and record["revision"] != export_key:
        return None
    review_id = _mesh_review_id(record)
    binding_owner = path.relative_to(repo).as_posix()
    if path.parent.name == "originals" and review_id == LIVER_REVIEW_ID:
        track_ref = _liver_binding(repo, package, record)
        if (
            track_ref is None
            or Path(owner).name != "asset.record.json"
            or (track_ref.asset, track_ref.revision, track_ref.export)
            != (ref.asset, ref.revision, ref.export)
            or record["revision"] != mesh_hash
            or record["part"] not in {part.id for part in export.parts}
        ):
            return None
        binding_owner = LIVER_TRACK
    blob = verify(repo, export.path, mesh_hash, export.bytes)
    if blob.status not in ("verified", "pointer-match"):
        return None
    return UltrasoundReview(
        **_review_fields(repo, path, package, record),
        id=review_id,
        kind="mesh",
        binding_status="verified" if blob.status == "verified" else "recorded",
        binding_owner=binding_owner,
        export_ref=ref,
        export_path=export.path,
        mesh_sha256=mesh_hash,
        chapter_sha256=record.get("chapterSha256"),
    )


def _verify_echo_delivery(delivery: Path, package, record) -> None:
    manifest = _read_json(repo_file(delivery, "development/asset-inventory.json"))
    rubric = repo_file(delivery, "development/asset-rubric.md")
    if (
        manifest.get("version") != 1
        or manifest.get("rubricHash") != package["rubricHash"]
        or sha256(rubric.read_bytes()).hexdigest() != package["rubricHash"]
    ):
        raise AssetKitError("Supplied ultrasound delivery has a different workbench rubric")
    rows = [row for row in manifest["cases"] if row.get("owner") == "echo"]
    matches = [
        row
        for row in rows
        if row.get("id") == record["case"]
        and row.get("family") == "echo"
        and row["record"].get("id") == record["case"]
        and row["record"].get("family") == "echo"
    ]
    if len(matches) != 1 or not any(
        chapter["id"] == record["chapter"] for chapter in matches[0]["chapters"]
    ):
        raise AssetKitError("Supplied ultrasound delivery lacks the reviewed echo case and chapter")
    digest = recipe_hashes(delivery, {"echo"}, rows, rubric=rubric)["echo"]
    if digest != package["recipeHash"] or manifest["recipeHashes"].get("echo") != digest:
        raise AssetKitError("Supplied ultrasound delivery differs from the reviewed echo recipe")


def _echo_review(repo: Path, path: Path, package, delivery: Path | None) -> UltrasoundReview | None:
    record = _select(
        package["records"], "case", "echo-aortic-stenosis", "psax-av-section", "Aortic valve cusp 1"
    )
    if record is None:
        return None
    cases = safe_path(repo, ECHO_CASES)
    if not cases.is_file() or not any(
        row.get("id") == record["case"] and row.get("family") == "echo" for row in _read_json(cases)
    ):
        return None
    if delivery is not None:
        _verify_echo_delivery(delivery, package, record)
    return UltrasoundReview(
        **_review_fields(repo, path, package, record),
        id=ECHO_REVIEW_ID,
        kind="recipe",
        binding_status="verified" if delivery is not None else "recorded",
        binding_owner=ECHO_CASES,
        recipe_sha256=package["recipeHash"],
    )


def load_ultrasound_reviews(
    repo: Path,
    registry: AssetRegistry,
    *,
    delivery: Path | None = None,
    target: str | None = None,
    exports: Iterable[tuple[Asset, Revision, Export]] | None = None,
) -> tuple[UltrasoundReview, ...]:
    """Project exact evidence, optionally restricted to the exports being inspected."""
    repo = repo.resolve()
    by_digest = defaultdict(list)
    if target != ECHO_REVIEW_ID:
        for asset, revision, export in registry.iter_exports() if exports is None else exports:
            owner = asset.source_manifest
            if (
                owner
                and Path(owner).name in {"asset.record.json", "assets.json"}
                and export.format == "mesh"
                and export.sha256
            ):
                by_digest[export.sha256].append((asset, revision, export))

    include_echo = exports is None and target in (None, ECHO_REVIEW_ID)
    if not by_digest and not include_echo:
        return ()
    root = safe_path(repo, REVIEW_ROOT)
    echo_path = root / "echo/reviews.json"
    paths = sorted(root.glob("*/reviews.json")) if by_digest else []
    if include_echo and not by_digest and echo_path.is_file():
        paths.append(echo_path)

    reviews = []
    echo = None
    for path in paths:
        relative = path.relative_to(repo).as_posix()
        path = safe_path(repo, relative)
        try:
            read_echo = path == echo_path and include_echo
            if not read_echo and not any(
                record.get("meshSha256") in by_digest
                and (target is None or _mesh_review_id(record) == target)
                for record in _read_json(path)["records"]
            ):
                continue
            package = validate_reviews(path, allow_lfs_pointers=True)
            if not HEX64.fullmatch(package["rubricHash"]):
                raise ValueError("Invalid workbench rubric identity")
            for record in package["records"]:
                meshes = by_digest.get(record.get("meshSha256"), ())
                if not meshes or (target is not None and _mesh_review_id(record) != target):
                    continue
                for match in meshes:
                    review = _mesh_review(repo, path, package, record, match)
                    if review is not None:
                        reviews.append(review)
            if read_echo:
                if not HEX64.fullmatch(package["recipeHash"]):
                    raise ValueError("Invalid workbench recipe identity")
                echo = _echo_review(repo, path, package, delivery)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            raise AssetKitError(f"Invalid ultrasound workbench review {relative}: {exc}") from exc
    if echo is not None:
        reviews.append(echo)
    return tuple(reviews)
