"""Governance & release context: Reviews, Selections, and downstream publication projections."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import Field

from .blobs import HEX64
from .discovery import manifests
from .errors import AssetKitError
from .models import AssetModel

if TYPE_CHECKING:
    from .delivery import DeliveryGraph
    from .registry import AssetRegistry

REVIEW_STATUSES = frozenset({"accepted", "provisional", "blocked", "rejected"})
QUALIFICATION_DECISIONS = frozenset({"qualified", "provisional", "blocked", "rejected"})
ADOPTION_STATUSES = frozenset({"provisional", "qualified", "deprecated", "retired"})
SELECTION_KINDS = frozenset({"teaching-default", "recommended-revision", "release-admitted"})


class Review(AssetModel):
    """Dated, immutable assessment evidence bound to an exact Export or Part."""

    id: str
    export_path: str
    task_id: str
    task: str
    status: str
    owner_path: str
    sha256: str | None = None
    asset_id: str | None = None
    part_id: str | None = None
    scores: dict[str, Any] = Field(default_factory=dict)
    limits: tuple[str, ...] = ()

    def validate_invariants(self) -> None:
        if not self.id.strip() or not self.export_path.strip():
            raise AssetKitError(f"Review requires non-empty id and export_path: {self}")
        if self.status not in REVIEW_STATUSES:
            raise AssetKitError(f"Invalid review status '{self.status}' on '{self.id}'")


class Selection(AssetModel):
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

    def validate_invariants(self) -> None:
        if not self.id.strip() or not self.export_path.strip():
            raise AssetKitError(f"Selection requires non-empty id and export_path: {self}")
        if self.kind not in SELECTION_KINDS:
            raise AssetKitError(f"Invalid selection kind '{self.kind}' on '{self.id}'")


class Qualification(AssetModel):
    """Explicit task- or scope-specific qualification decision bound to an exact revision/export."""

    id: str
    asset_id: str
    revision_id: str
    scope: str
    decision: str
    owner_path: str
    export_path: str | None = None
    sha256: str | None = None
    use_id: str | None = None
    task_id: str | None = None
    part_ids: tuple[str, ...] = ()
    reviewer: str | None = None
    assessed_at: str | None = None
    evidence: tuple[dict[str, Any], ...] = ()

    def validate_invariants(self) -> None:
        if not self.id.strip() or not self.asset_id.strip() or not self.revision_id.strip():
            raise AssetKitError(
                f"Qualification requires non-empty id, asset_id, revision_id: {self}"
            )
        if self.decision not in QUALIFICATION_DECISIONS:
            raise AssetKitError(f"Invalid qualification decision '{self.decision}' on '{self.id}'")


class Adoption(AssetModel):
    """Owner-declared consumer adoption/use pin recorded in an asset.record.json."""

    use_id: str
    consumer_id: str
    asset_id: str
    revision_id: str
    export_path: str
    status: str
    owner_path: str
    sha256: str | None = None
    bytes: int | None = None
    part_ids: tuple[str, ...] = ()
    requirement_ids: tuple[str, ...] = ()

    def validate_invariants(self) -> None:
        if not self.use_id.strip() or not self.export_path.strip():
            raise AssetKitError(f"Adoption requires non-empty use_id and export_path: {self}")
        if self.status not in ADOPTION_STATUSES:
            raise AssetKitError(f"Invalid adoption status '{self.status}' on '{self.use_id}'")


class QualificationStatus(AssetModel):
    export_path: str
    qualified: bool
    statuses: tuple[str, ...] = ()
    review_ids: tuple[str, ...] = ()
    qualification_decisions: tuple[str, ...] = ()
    qualification_ids: tuple[str, ...] = ()
    adoption_statuses: tuple[str, ...] = ()
    adoption_ids: tuple[str, ...] = ()


class GalleryExportView(AssetModel):
    id: str
    path: str
    role: str
    variant: str
    format: str
    sha256: str | None = None
    bytes: int | None = None
    triangles: int | None = None
    storage_status: str
    qualified: bool
    review_statuses: tuple[str, ...] = ()
    qualification_decisions: tuple[str, ...] = ()
    adoption_statuses: tuple[str, ...] = ()
    parts: tuple[str, ...] = ()


class GalleryRevisionView(AssetModel):
    id: str
    status: str
    subject: str | None = None
    registration: str = "unknown"
    capabilities: tuple[str, ...] = ()
    exports: tuple[GalleryExportView, ...] = ()


class GalleryAssetView(AssetModel):
    id: str
    title: str
    kind: str
    owner_dir: str
    families: tuple[str, ...] = ()
    concepts: tuple[str, ...] = ()
    revisions: tuple[GalleryRevisionView, ...] = ()


class GalleryProjection(AssetModel):
    schema_version: int = 1
    assets: tuple[GalleryAssetView, ...] = ()
    selections: tuple[Selection, ...] = ()
    open_gaps: tuple[Any, ...] = ()


class R2SyncItem(AssetModel):
    asset_id: str
    revision_id: str
    export_id: str
    path: str
    sha256: str | None = None
    bytes: int | None = None
    storage_status: str


@dataclass(frozen=True)
class CurationStore:
    """Owns assessment evidence, qualifications, adoptions, selections, and release views."""

    reviews: tuple[Review, ...] = ()
    selections: tuple[Selection, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    adoptions: tuple[Adoption, ...] = ()

    @classmethod
    def load(cls, repo: Path, *, include_legacy_adapters: bool = True) -> CurationStore:
        root = repo.resolve()
        reviews: list[Review] = []
        selections: list[Selection] = []
        qualifications, adoptions = _load_record_curation(root)
        if include_legacy_adapters:
            if (root / "reviews/teaching-assessments/current-assessments.json").is_file():
                reviews, selections = _load_current_teaching(root)
            else:
                reviews = _load_teaching_assessments(root)
                selections = _load_maintained_selections(root)
        return cls(
            reviews=tuple(reviews),
            selections=tuple(selections),
            qualifications=tuple(qualifications),
            adoptions=tuple(adoptions),
        )

    def validate(self) -> None:
        seen_reviews: set[str] = set()
        for rev in self.reviews:
            if rev.id in seen_reviews:
                raise AssetKitError(f"Duplicate review id '{rev.id}'")
            seen_reviews.add(rev.id)
            rev.validate_invariants()

        seen_sel: set[str] = set()
        for sel in self.selections:
            if sel.id in seen_sel:
                raise AssetKitError(f"Duplicate selection id '{sel.id}'")
            seen_sel.add(sel.id)
            sel.validate_invariants()

        seen_quals: set[str] = set()
        for qual in self.qualifications:
            if qual.id in seen_quals:
                raise AssetKitError(f"Duplicate qualification id '{qual.id}'")
            seen_quals.add(qual.id)
            qual.validate_invariants()

        seen_adoptions: set[str] = set()
        for adop in self.adoptions:
            if adop.use_id in seen_adoptions:
                raise AssetKitError(f"Duplicate adoption use_id '{adop.use_id}'")
            seen_adoptions.add(adop.use_id)
            adop.validate_invariants()

    def qualification_for(
        self,
        export_path: str,
        sha256: str | None = None,
        *,
        task_id: str | None = None,
        consumer_id: str | None = None,
        use_id: str | None = None,
        part_id: str | None = None,
        asset_id: str | None = None,
        revision_id: str | None = None,
    ) -> QualificationStatus:
        """Compute exact-digest assessment evidence, qualification decisions, and adoption state."""
        if not sha256 or not HEX64.fullmatch(sha256):
            return QualificationStatus(
                export_path=export_path,
                qualified=False,
                statuses=(),
                review_ids=(),
            )

        task = task_id.removeprefix("teaching-task:") if task_id else None
        matched_adoptions = [
            a
            for a in self.adoptions
            if a.export_path == export_path
            and a.sha256 == sha256
            and (asset_id is None or a.asset_id == asset_id)
            and (revision_id is None or a.revision_id == revision_id)
            and (consumer_id is None or a.consumer_id == consumer_id)
            and (use_id is None or a.use_id == use_id)
            and (
                task is None
                or task in a.requirement_ids
                or f"teaching-task:{task}" in a.requirement_ids
            )
            and (part_id is None or part_id in a.part_ids)
        ]
        adoption_use_ids = {a.use_id for a in matched_adoptions}
        use_tasks = {
            r.removeprefix("teaching-task:") for a in matched_adoptions for r in a.requirement_ids
        }
        use_parts = {p for a in matched_adoptions for p in a.part_ids}
        matched_reviews = [
            r
            for r in self.reviews
            if r.export_path == export_path
            and r.sha256 == sha256
            and (r.asset_id is None or asset_id is None or r.asset_id == asset_id)
            and (task is None or r.task_id == task)
            and (part_id is None or r.part_id is None or r.part_id == part_id)
            and (
                use_id is None
                or (r.task_id in use_tasks and (r.part_id is None or r.part_id in use_parts))
            )
        ]

        def scope_covers_parts(parts: tuple[str, ...]) -> bool:
            if part_id is not None:
                return part_id in parts
            if use_id is not None:
                return bool(use_parts) and use_parts.issubset(parts)
            # An export overview summarizes scoped decisions. A task query asks
            # about the whole export unless a specific part was requested.
            return task is None

        matched_quals = [
            q
            for q in self.qualifications
            if q.export_path == export_path
            and q.sha256 == sha256
            and (asset_id is None or q.asset_id == asset_id)
            and (revision_id is None or q.revision_id == revision_id)
            and (q.use_id is None or q.use_id in adoption_use_ids)
            and (task is None or q.task_id is None or q.task_id == task)
            and (
                use_id is None
                or (use_id in adoption_use_ids and (q.task_id is None or q.task_id in use_tasks))
            )
            and (not q.part_ids or scope_covers_parts(q.part_ids))
        ]

        review_statuses = tuple(sorted({r.status for r in matched_reviews}))
        qual_decisions = tuple(sorted({q.decision for q in matched_quals}))
        adoption_statuses = tuple(sorted({a.status for a in matched_adoptions}))
        return QualificationStatus(
            export_path=export_path,
            qualified="qualified" in qual_decisions,
            statuses=review_statuses,
            review_ids=tuple(r.id for r in matched_reviews),
            qualification_decisions=qual_decisions,
            qualification_ids=tuple(q.id for q in matched_quals),
            adoption_statuses=adoption_statuses,
            adoption_ids=tuple(a.use_id for a in matched_adoptions),
        )

    def reviews_for(self, export_paths: set[str], asset_ids: set[str]) -> tuple[Review, ...]:
        return tuple(
            r
            for r in self.reviews
            if r.export_path in export_paths or (r.asset_id in asset_ids if r.asset_id else False)
        )

    def qualifications_for(
        self, export_paths: set[str], asset_ids: set[str]
    ) -> tuple[Qualification, ...]:
        return tuple(
            q
            for q in self.qualifications
            if (q.export_path in export_paths if q.export_path else False)
            or q.asset_id in asset_ids
        )

    def adoptions_for(self, export_paths: set[str], asset_ids: set[str]) -> tuple[Adoption, ...]:
        return tuple(
            a for a in self.adoptions if a.export_path in export_paths or a.asset_id in asset_ids
        )

    def selections_for(self, export_paths: set[str], asset_ids: set[str]) -> tuple[Selection, ...]:
        return tuple(
            s
            for s in self.selections
            if s.export_path in export_paths or (s.asset_id in asset_ids if s.asset_id else False)
        )

    def compile_gallery(
        self, registry: AssetRegistry, delivery: DeliveryGraph
    ) -> GalleryProjection:
        """Compile a deterministic, read-only Gallery index projection."""
        entries: list[GalleryAssetView] = []
        for asset in registry.assets:
            revs: list[GalleryRevisionView] = []
            for rev in asset.revisions:
                exps: list[GalleryExportView] = []
                for exp in rev.exports:
                    qual = self.qualification_for(
                        exp.path, exp.sha256, asset_id=asset.id, revision_id=rev.id
                    )
                    exps.append(
                        GalleryExportView(
                            id=exp.id,
                            path=exp.path,
                            role=exp.role,
                            variant=exp.variant,
                            format=exp.format,
                            sha256=exp.sha256,
                            bytes=exp.bytes,
                            triangles=exp.triangles,
                            storage_status=exp.storage_status,
                            qualified=qual.qualified,
                            review_statuses=qual.statuses,
                            qualification_decisions=qual.qualification_decisions,
                            adoption_statuses=qual.adoption_statuses,
                            parts=tuple(p.id for p in exp.parts),
                        )
                    )
                revs.append(
                    GalleryRevisionView(
                        id=rev.id,
                        status=rev.status,
                        subject=rev.provenance.subject,
                        registration=rev.provenance.registration,
                        capabilities=rev.capabilities,
                        exports=tuple(exps),
                    )
                )
            entries.append(
                GalleryAssetView(
                    id=asset.id,
                    title=asset.title,
                    kind=asset.kind,
                    owner_dir=asset.owner_dir,
                    families=asset.families,
                    concepts=asset.concepts,
                    revisions=tuple(revs),
                )
            )
        return GalleryProjection(
            assets=tuple(entries),
            selections=self.selections,
            open_gaps=tuple(delivery.open_gaps()),
        )

    def plan_r2_sync(self, registry: AssetRegistry, delivery: DeliveryGraph) -> list[R2SyncItem]:
        """List exact runtime delivery exports referenced by Selections or Consumer pins."""
        needed_paths = {s.export_path for s in self.selections}
        for consumer in delivery.consumers:
            for pin in consumer.pins:
                resolved = registry.resolve_export(pin.asset_id, pin.revision_id, pin.export_id)
                if resolved is not None:
                    needed_paths.add(resolved[2].path)

        items: list[R2SyncItem] = []
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
                        R2SyncItem(
                            asset_id=asset.id,
                            revision_id=rev.id,
                            export_id=exp.id,
                            path=exp.path,
                            sha256=exp.sha256,
                            bytes=exp.bytes,
                            storage_status=exp.storage_status,
                        )
                    )
        return sorted(items, key=lambda x: x.path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviews": [r.to_dict() for r in self.reviews],
            "qualifications": [q.to_dict() for q in self.qualifications],
            "adoptions": [a.to_dict() for a in self.adoptions],
            "selections": [s.to_dict() for s in self.selections],
        }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetKitError(f"Invalid JSON in {path}: {exc}") from exc


def _load_record_curation(repo: Path) -> tuple[list[Qualification], list[Adoption]]:
    qualifications: list[Qualification] = []
    adoptions: list[Adoption] = []
    for record_path in manifests(repo, "asset.record.json"):
        doc = _read_json(record_path)
        if not isinstance(doc, dict) or not doc.get("assetId"):
            continue
        asset_id = str(doc["assetId"])
        rel_owner = record_path.resolve().relative_to(repo).as_posix()

        for rev in doc.get("revisions", []):
            if not isinstance(rev, dict) or not rev.get("revisionId"):
                continue
            rev_id = str(rev["revisionId"])
            for idx, qrow in enumerate(rev.get("qualifications", []), 1):
                if not isinstance(qrow, dict):
                    continue
                qid = str(
                    qrow.get("qualificationId") or qrow.get("id") or f"{asset_id}:{rev_id}:q{idx}"
                )
                decision = str(qrow.get("decision", "provisional"))
                if decision not in QUALIFICATION_DECISIONS:
                    decision = "provisional"
                qualifications.append(
                    Qualification(
                        id=qid,
                        asset_id=asset_id,
                        revision_id=rev_id,
                        scope=str(qrow.get("scope", "general")),
                        decision=decision,
                        owner_path=rel_owner,
                        export_path=qrow.get("exportPath"),
                        sha256=qrow.get("sha256"),
                        use_id=qrow.get("useId"),
                        task_id=qrow.get("taskId"),
                        part_ids=tuple(
                            str(p) for p in qrow.get("partIds", []) if isinstance(p, str)
                        ),
                        reviewer=qrow.get("reviewer"),
                        assessed_at=qrow.get("assessedAt"),
                        evidence=tuple(e for e in qrow.get("evidence", []) if isinstance(e, dict)),
                    )
                )

        for use in doc.get("uses", []):
            if not isinstance(use, dict) or not use.get("useId") or not use.get("exportPath"):
                continue
            use_id = str(use["useId"])
            status = str(use.get("status", "provisional"))
            if status not in ADOPTION_STATUSES:
                status = "provisional"
            rev_id = str(use.get("revisionId", ""))
            adoptions.append(
                Adoption(
                    use_id=use_id,
                    consumer_id=str(use.get("consumerId", use_id)),
                    asset_id=asset_id,
                    revision_id=rev_id,
                    export_path=str(use["exportPath"]),
                    status=status,
                    owner_path=rel_owner,
                    sha256=use.get("sha256"),
                    bytes=use.get("bytes"),
                    part_ids=tuple(str(p) for p in use.get("partIds", []) if isinstance(p, str)),
                    requirement_ids=tuple(
                        str(r) for r in use.get("requirementIds", []) if isinstance(r, str)
                    ),
                )
            )
            for idx, qrow in enumerate(use.get("qualifications", []), 1):
                if not isinstance(qrow, dict):
                    continue
                qid = str(qrow.get("qualificationId") or qrow.get("id") or f"{use_id}:q{idx}")
                decision = str(qrow.get("decision", "provisional"))
                if decision not in QUALIFICATION_DECISIONS:
                    decision = "provisional"
                qualifications.append(
                    Qualification(
                        id=qid,
                        asset_id=asset_id,
                        revision_id=rev_id,
                        scope=str(qrow.get("scope", "task")),
                        decision=decision,
                        owner_path=rel_owner,
                        export_path=str(use["exportPath"]),
                        sha256=qrow.get("sha256") or use.get("sha256"),
                        use_id=use_id,
                        task_id=qrow.get("taskId"),
                        part_ids=tuple(
                            str(p)
                            for p in (qrow.get("partIds") or use.get("partIds") or [])
                            if isinstance(p, str)
                        ),
                        reviewer=qrow.get("reviewer"),
                        assessed_at=qrow.get("assessedAt"),
                        evidence=tuple(e for e in qrow.get("evidence", []) if isinstance(e, dict)),
                    )
                )
    return qualifications, adoptions


def _load_current_teaching(repo: Path) -> tuple[list[Review], list[Selection]]:
    # Import the repository adapter only when reading its maintained register.
    from med_assets.teaching import SELECTIONS, CurrentTeaching

    current = CurrentTeaching(repo)
    reviews = []
    for path, task_id in current.entries:
        assessment = current.resolve(path, task_id)
        row = assessment.row
        reviews.append(
            Review(
                id=assessment.sha256,
                export_path=path,
                task_id=task_id,
                task=row["task"],
                status="blocked"
                if row.get("target", {}).get("status") == "blocked"
                else "accepted",
                owner_path=assessment.owner.relative_to(repo).as_posix(),
                sha256=row["export"]["sha256"],
                scores={f"axis{i}": axis["score"] for i, axis in enumerate(row["axes"], 1)},
            )
        )
    selections = [
        Selection(
            id=f"selection:{selection.collection_id}:{selection.family_id}:{selection.path}",
            kind="teaching-default",
            export_path=selection.path,
            owner_path=SELECTIONS,
            collection_id=selection.collection_id,
            family_id=selection.family_id,
            task_id=selection.task_id,
            review_id=assessment.sha256,
        )
        for selection, assessment in current.selected()
    ]
    return reviews, selections


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
