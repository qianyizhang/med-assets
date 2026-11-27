"""Governance & release context: Reviews, Selections, and downstream publication projections."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .errors import AssetKitError

if TYPE_CHECKING:
    from .delivery import DeliveryGraph
    from .registry import AssetRegistry

REVIEW_STATUSES = frozenset({"accepted", "provisional", "blocked", "rejected"})
SELECTION_KINDS = frozenset({"teaching-default", "recommended-revision", "release-admitted"})


@dataclass(frozen=True)
class Review:
    """Dated, immutable qualification evidence bound to an exact Export or Part."""

    id: str
    export_path: str
    task_id: str
    task: str
    status: str
    owner_path: str
    sha256: str | None = None
    asset_id: str | None = None
    part_id: str | None = None
    scores: dict[str, Any] = field(default_factory=dict)
    limits: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.id.strip() or not self.export_path.strip():
            raise AssetKitError(f"Review requires non-empty id and export_path: {self}")
        if self.status not in REVIEW_STATUSES:
            raise AssetKitError(f"Invalid review status '{self.status}' on '{self.id}'")


@dataclass(frozen=True)
class Selection:
    """Explicit editorial/release choice separating curation from qualification."""

    id: str
    kind: str
    export_path: str
    owner_path: str
    collection_id: str | None = None
    family_id: str | None = None
    task_id: str | None = None
    review_id: str | None = None
    asset_id: str | None = None
    revision_id: str | None = None

    def validate(self) -> None:
        if not self.id.strip() or not self.export_path.strip():
            raise AssetKitError(f"Selection requires non-empty id and export_path: {self}")
        if self.kind not in SELECTION_KINDS:
            raise AssetKitError(f"Invalid selection kind '{self.kind}' on '{self.id}'")


@dataclass(frozen=True)
class QualificationStatus:
    export_path: str
    qualified: bool
    statuses: tuple[str, ...]
    review_ids: tuple[str, ...]


@dataclass(frozen=True)
class CurationStore:
    """Owns qualification evidence, editorial selections, and compiled release views."""

    reviews: tuple[Review, ...] = ()
    selections: tuple[Selection, ...] = ()

    @classmethod
    def load(cls, repo: Path, *, include_legacy_adapters: bool = True) -> CurationStore:
        root = repo.resolve()
        reviews: list[Review] = []
        selections: list[Selection] = []
        if include_legacy_adapters:
            reviews.extend(_load_teaching_assessments(root))
            selections.extend(_load_maintained_selections(root))
        return cls(tuple(reviews), tuple(selections))

    def validate(self) -> None:
        seen_reviews: set[str] = set()
        for rev in self.reviews:
            if rev.id in seen_reviews:
                raise AssetKitError(f"Duplicate review id '{rev.id}'")
            seen_reviews.add(rev.id)
            rev.validate()

        seen_sel: set[str] = set()
        for sel in self.selections:
            if sel.id in seen_sel:
                raise AssetKitError(f"Duplicate selection id '{sel.id}'")
            seen_sel.add(sel.id)
            sel.validate()

    def qualification_for(self, export_path: str, sha256: str | None = None) -> QualificationStatus:
        matched = [
            r
            for r in self.reviews
            if r.export_path == export_path
            and (sha256 is None or r.sha256 is None or r.sha256 == sha256)
        ]
        statuses = tuple(sorted({r.status for r in matched}))
        return QualificationStatus(
            export_path=export_path,
            qualified="accepted" in statuses,
            statuses=statuses,
            review_ids=tuple(r.id for r in matched),
        )

    def reviews_for(self, export_paths: set[str], asset_ids: set[str]) -> tuple[Review, ...]:
        return tuple(
            r
            for r in self.reviews
            if r.export_path in export_paths or (r.asset_id in asset_ids if r.asset_id else False)
        )

    def selections_for(self, export_paths: set[str], asset_ids: set[str]) -> tuple[Selection, ...]:
        return tuple(
            s
            for s in self.selections
            if s.export_path in export_paths or (s.asset_id in asset_ids if s.asset_id else False)
        )

    def compile_gallery(self, registry: AssetRegistry, delivery: DeliveryGraph) -> dict[str, Any]:
        """Compile a deterministic, read-only Gallery index projection."""
        entries = []
        for asset in registry.assets:
            revs = []
            for rev in asset.revisions:
                exps = []
                for exp in rev.exports:
                    qual = self.qualification_for(exp.path, exp.sha256)
                    exps.append(
                        {
                            "id": exp.id,
                            "path": exp.path,
                            "role": exp.role,
                            "variant": exp.variant,
                            "format": exp.format,
                            "sha256": exp.sha256,
                            "bytes": exp.bytes,
                            "triangles": exp.triangles,
                            "storageStatus": exp.storage_status,
                            "qualified": qual.qualified,
                            "reviewStatuses": list(qual.statuses),
                            "parts": [p.id for p in exp.parts],
                        }
                    )
                revs.append(
                    {
                        "id": rev.id,
                        "status": rev.status,
                        "subject": rev.provenance.subject,
                        "registration": rev.provenance.registration,
                        "capabilities": list(rev.capabilities),
                        "exports": exps,
                    }
                )
            entries.append(
                {
                    "id": asset.id,
                    "title": asset.title,
                    "kind": asset.kind,
                    "ownerDir": asset.owner_dir,
                    "families": list(asset.families),
                    "concepts": list(asset.concepts),
                    "revisions": revs,
                }
            )
        return {
            "schemaVersion": 1,
            "assets": entries,
            "selections": [asdict(s) for s in self.selections],
            "openGaps": delivery.open_gaps(),
        }

    def plan_r2_sync(
        self, registry: AssetRegistry, delivery: DeliveryGraph
    ) -> list[dict[str, Any]]:
        """List exact runtime delivery exports referenced by Selections or Consumer pins."""
        needed_paths = {s.export_path for s in self.selections}
        for consumer in delivery.consumers:
            for pin in consumer.pins:
                resolved = registry.resolve_export(pin.asset_id, pin.revision_id, pin.export_id)
                if resolved is not None:
                    needed_paths.add(resolved[2].path)

        items: list[dict[str, Any]] = []
        seen: set[str] = set()
        for asset in registry.assets:
            for rev in asset.revisions:
                for exp in rev.exports:
                    if exp.role == "editable-master" or exp.path not in needed_paths:
                        continue
                    if exp.path in seen:
                        continue
                    seen.add(exp.path)
                    items.append(
                        {
                            "assetId": asset.id,
                            "revisionId": rev.id,
                            "exportId": exp.id,
                            "path": exp.path,
                            "sha256": exp.sha256,
                            "bytes": exp.bytes,
                            "storageStatus": exp.storage_status,
                        }
                    )
        return sorted(items, key=lambda x: x["path"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviews": [asdict(r) for r in self.reviews],
            "selections": [asdict(s) for s in self.selections],
        }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetKitError(f"Invalid JSON in {path}: {exc}") from exc


def _load_teaching_assessments(repo: Path) -> list[Review]:
    reviews: list[Review] = []
    review_dir = repo / "reviews/teaching-assessments"
    if not review_dir.is_dir():
        return reviews
    for path in sorted(review_dir.rglob("*.json")):
        doc = _read_json(path)
        if not isinstance(doc, dict):
            continue
        rows = doc.get("assessments")
        if not isinstance(rows, list):
            rows = [doc] if "export" in doc and "task" in doc else []
        rel_owner = path.resolve().relative_to(repo).as_posix()
        for idx, row in enumerate(rows, 1):
            if not isinstance(row, dict) or "export" not in row or "task" not in row:
                continue
            exp = row["export"]
            exp_path = exp.get("path") if isinstance(exp, dict) else None
            if not isinstance(exp_path, str):
                continue
            task_id = str(row.get("taskId") or row.get("id") or f"{path.stem}:{idx}")
            target_status = (row.get("target") or {}).get("status", "accepted")
            status = "blocked" if target_status == "blocked" else "accepted"
            axes = row.get("axes")
            scores = (
                {f"axis{i + 1}": a.get("score") for i, a in enumerate(axes) if isinstance(a, dict)}
                if isinstance(axes, list)
                else (axes if isinstance(axes, dict) else {})
            )
            reviews.append(
                Review(
                    id=f"review:{rel_owner}#{idx}",
                    export_path=exp_path,
                    task_id=task_id,
                    task=str(row["task"]),
                    status=status,
                    owner_path=rel_owner,
                    sha256=exp.get("sha256"),
                    scores=scores,
                )
            )
    return reviews


def _load_maintained_selections(repo: Path) -> list[Selection]:
    selections: list[Selection] = []
    sel_path = repo / "docs/gallery/maintained-selections.json"
    if not sel_path.is_file():
        return selections
    doc = _read_json(sel_path)
    rel_owner = sel_path.resolve().relative_to(repo).as_posix()
    seq = 0
    for col in doc.get("collections", []):
        if not isinstance(col, dict):
            continue
        col_id = col.get("id")
        for fam in col.get("families", []):
            if not isinstance(fam, dict):
                continue
            fam_id = fam.get("id")
            for exp in fam.get("exports", []):
                if not isinstance(exp, dict) or not exp.get("path"):
                    continue
                seq += 1
                selections.append(
                    Selection(
                        id=f"selection:{seq}:{col_id}:{fam_id}",
                        kind="teaching-default",
                        export_path=str(exp["path"]),
                        owner_path=rel_owner,
                        collection_id=col_id,
                        family_id=fam_id,
                        task_id=exp.get("taskId"),
                        review_id=exp.get("assessmentSha256"),
                    )
                )
    return selections
