"""Demand & packaging context: Consumers, RuntimeBundles, Resolution, Economy, and Impact."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, computed_field

from .curation import Adoption, CurationStore, Qualification, Review, Selection
from .discovery import manifests
from .errors import AssetKitError
from .models import AssetModel
from .registry import REGISTRATION_STATES, AssetRegistry, ExportRef, Part
from .vocab import ConceptGraph

CONSUMER_KINDS = frozenset(
    {
        "lesson-stop",
        "ultrasound-sweep",
        "ultrasound-tour",
        "ultrasound-case",
        "scene",
        "site",
        "other",
    }
)
REQUIREMENT_STATUSES = frozenset({"satisfied", "provisional", "open-gap", "rebuild-required"})


class Requirement(AssetModel):
    """Machine-readable statement of what a Consumer needs."""

    id: str
    description: str
    status: str = "open-gap"
    concepts: tuple[str, ...] = ()
    parts: tuple[str, ...] = ()
    variant: str | None = None
    subject: str | None = None
    capabilities: tuple[str, ...] = ()

    def validate_invariants(self, consumer_id: str) -> None:
        if not self.id.strip():
            raise AssetKitError(f"Requirement requires non-empty id in '{consumer_id}'")
        if self.status not in REQUIREMENT_STATUSES:
            raise AssetKitError(
                f"Invalid requirement status '{self.status}' in {consumer_id}:{self.id}"
            )


class Pin(AssetModel):
    """Explicit Consumer dependency on an exact Asset Export / Parts."""

    asset_id: str
    revision_id: str
    export_id: str
    requirement_id: str | None = None
    parts: tuple[str, ...] = ()
    sha256: str | None = None
    registration: str = "unknown"
    transform: tuple[float, ...] | None = None
    limits: tuple[str, ...] = ()

    def validate_invariants(self, consumer_id: str) -> None:
        if not self.asset_id.strip() or not self.revision_id.strip() or not self.export_id.strip():
            raise AssetKitError(f"Incomplete pin in consumer '{consumer_id}': {self}")
        if self.registration not in REGISTRATION_STATES:
            raise AssetKitError(
                f"Invalid pin registration '{self.registration}' in consumer '{consumer_id}'"
            )
        if self.transform is not None and len(self.transform) != 16:
            raise AssetKitError(f"Pin transform must have 16 values in '{consumer_id}'")


class Consumer(AssetModel):
    """An authored teaching experience or delivery surface."""

    id: str
    title: str
    kind: str
    owner_path: str
    requirements: tuple[Requirement, ...] = ()
    pins: tuple[Pin, ...] = ()
    local_files: tuple[str, ...] = ()

    def validate_invariants(self) -> None:
        if not self.id.strip() or not self.owner_path.strip():
            raise AssetKitError(f"Consumer requires non-empty id and owner_path: {self}")
        if self.kind not in CONSUMER_KINDS:
            raise AssetKitError(f"Invalid consumer kind '{self.kind}' on '{self.id}'")
        req_ids: set[str] = set()
        for req in self.requirements:
            if req.id in req_ids:
                raise AssetKitError(f"Duplicate requirement '{req.id}' in '{self.id}'")
            req_ids.add(req.id)
            req.validate_invariants(self.id)
        for pin in self.pins:
            pin.validate_invariants(self.id)
            if pin.requirement_id is not None and pin.requirement_id not in req_ids:
                raise AssetKitError(
                    f"Pin references unknown requirement '{pin.requirement_id}' in '{self.id}'"
                )


class BudgetPolicy(AssetModel):
    """Soft and hard caps governing delivery economy."""

    export_bytes_soft: int = 1_500_000
    export_bytes_hard: int = 4_000_000
    export_tris_soft: int = 50_000
    export_tris_hard: int = 150_000
    consumer_bytes_soft: int = 5_000_000
    consumer_bytes_hard: int = 12_000_000
    consumer_loads_soft: int = 5
    consumer_loads_hard: int = 12
    min_utilization: float = 0.35


class UseCaseMetrics(AssetModel):
    consumer_id: str
    title: str
    loads: int
    total_bytes: int
    total_triangles: int
    part_utilization: float | None = None
    byte_utilization: float | None = None
    open_gaps: int = 0
    budget_flags: tuple[str, ...] = ()


class Recommendation(AssetModel):
    action: Literal["split-export", "merge-bundle", "over-budget"]
    target: str
    severity: Literal["warn", "hard"]
    reason: str
    metrics: dict[str, Any] = Field(default_factory=dict)


class EconomySummary(AssetModel):
    consumers_evaluated: int
    assets_reused: int
    recommendations: int
    hard_violations: int


class EconomyReport(AssetModel):
    policy: BudgetPolicy
    consumer_metrics: tuple[UseCaseMetrics, ...]
    asset_reuse: dict[str, int]
    export_reuse: dict[str, int]
    recommendations: tuple[Recommendation, ...]

    @computed_field
    @property
    def summary(self) -> EconomySummary:
        return EconomySummary(
            consumers_evaluated=len(self.consumer_metrics),
            assets_reused=sum(1 for v in self.asset_reuse.values() if v > 1),
            recommendations=len(self.recommendations),
            hard_violations=sum(1 for r in self.recommendations if r.severity == "hard"),
        )


class OpenGap(AssetModel):
    consumer_id: str | None = None
    consumer_title: str | None = None
    requirement_id: str
    status: str
    description: str
    concepts: tuple[str, ...] = ()
    parts: tuple[str, ...] = ()
    subject: str | None = None


class BundleItem(AssetModel):
    asset_id: str
    revision_id: str
    export_id: str
    path: str
    format: str
    variant: str
    sha256: str | None = None
    bytes: int | None = None
    triangles: int | None = None
    storage_status: str
    registration: str = "unknown"
    transform: tuple[float, ...] | None = None
    license: str | None = None
    subject: str | None = None
    limits: tuple[str, ...] = ()
    parts: tuple[Part, ...] = ()


class RuntimeBundle(AssetModel):
    """Resolved load list for a Consumer (exact files, parts, provenance, and limits)."""

    consumer_id: str
    title: str
    items: tuple[BundleItem, ...]
    total_bytes: int
    total_triangles: int
    open_gaps: tuple[OpenGap, ...] = ()


class AffectedConsumer(AssetModel):
    consumer_id: str
    title: str
    kind: str
    pins: tuple[Pin, ...]
    owner_path: str


class ImpactResult(AssetModel):
    target: str
    found: bool
    status: Literal["ok", "unknown-target"]
    matched_assets: tuple[str, ...] = ()
    matched_export_paths: tuple[str, ...] = ()
    consumers: tuple[AffectedConsumer, ...] = ()
    adoptions: tuple[Adoption, ...] = ()
    reviews: tuple[Review, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    selections: tuple[Selection, ...] = ()


class ResolveCandidate(AssetModel):
    asset_id: str
    revision_id: str
    export_id: str
    export_path: str
    part_id: str | None = None
    label: str
    variant: str
    subject: str | None = None
    registration: str = "unknown"
    review_statuses: tuple[str, ...] = ()
    qualification_decisions: tuple[str, ...] = ()
    adoption_statuses: tuple[str, ...] = ()
    qualified: bool = False
    match_basis: str | None = None
    note: str | None = None


class RequirementResolution(AssetModel):
    requirement_id: str
    status: Literal["exact-candidate", "concept-candidate", "foreign-subject-only", "unmatched"]
    exact_candidates: tuple[ResolveCandidate, ...] = ()
    concept_candidates: tuple[ResolveCandidate, ...] = ()
    foreign_subject_candidates: tuple[ResolveCandidate, ...] = ()


class ResolveResult(AssetModel):
    consumer_id: str
    requirements: tuple[RequirementResolution, ...]


@dataclass(frozen=True)
class DeliveryGraph:
    """Owns all Consumers, their Requirements/Pins, and delivery analysis."""

    consumers: tuple[Consumer, ...] = ()

    @classmethod
    def load(cls, repo: Path, *, include_legacy_adapters: bool = True) -> DeliveryGraph:
        root = repo.resolve()
        consumers = _load_native_consumers(root)
        existing_ids = {c.id for c in consumers}
        consumers.extend(_load_ultrasound_sweep_consumers(root, existing_ids, pinned_only=True))
        if include_legacy_adapters:
            consumers.extend(_project_legacy_consumers(root, existing_ids))
        return cls(consumers=tuple(consumers))

    def get(self, consumer_id: str) -> Consumer | None:
        return next((c for c in self.consumers if c.id == consumer_id), None)

    def validate(self, registry: AssetRegistry) -> list[str]:
        warnings: list[str] = []
        seen: set[str] = set()
        for consumer in self.consumers:
            if consumer.id in seen:
                raise AssetKitError(f"Duplicate consumer id '{consumer.id}'")
            seen.add(consumer.id)
            consumer.validate_invariants()
            for pin in consumer.pins:
                resolved = registry.resolve_export(pin.asset_id, pin.revision_id, pin.export_id)
                if resolved is None:
                    warnings.append(
                        f"Consumer '{consumer.id}' pin references unknown export "
                        f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}"
                    )
                    continue
                _, _, exp = resolved
                if pin.sha256 and exp.sha256 and pin.sha256 != exp.sha256:
                    raise AssetKitError(
                        f"Pin sha256 mismatch for {consumer.id} -> "
                        f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}: "
                        f"{pin.sha256} != {exp.sha256}"
                    )
                if pin.parts:
                    known = {p.id for p in exp.parts}
                    if known:
                        missing = [p for p in pin.parts if p not in known]
                        if missing:
                            warnings.append(
                                f"Consumer '{consumer.id}' pin requests unknown parts "
                                f"{missing} on {pin.asset_id}@{pin.revision_id}:{pin.export_id}"
                            )
        return warnings

    def bundle_for(self, consumer_id: str, registry: AssetRegistry) -> RuntimeBundle:
        consumer = self.get(consumer_id)
        if consumer is None:
            raise AssetKitError(f"Unknown consumer '{consumer_id}'")
        items: list[BundleItem] = []
        total_bytes = 0
        total_tris = 0
        counted: set[tuple[str, str, str]] = set()
        for pin in consumer.pins:
            resolved = registry.resolve_export(pin.asset_id, pin.revision_id, pin.export_id)
            if resolved is None:
                raise AssetKitError(
                    f"Consumer '{consumer_id}' references missing export "
                    f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}"
                )
            asset, rev, exp = resolved
            if pin.sha256 and pin.sha256 != exp.sha256:
                raise AssetKitError(f"Pin sha256 mismatch for {consumer_id} -> {exp.path}")
            if set(pin.parts) - {p.id for p in exp.parts}:
                raise AssetKitError(f"Pin requests unknown parts for {consumer_id} -> {exp.path}")
            key = (asset.id, rev.id, exp.id)
            if key not in counted:
                counted.add(key)
                total_bytes += exp.bytes or 0
                total_tris += exp.triangles or 0
            selected_parts = tuple(p for p in exp.parts if not pin.parts or p.id in pin.parts)
            items.append(
                BundleItem(
                    asset_id=asset.id,
                    revision_id=rev.id,
                    export_id=exp.id,
                    path=exp.path,
                    format=exp.format,
                    variant=exp.variant,
                    sha256=exp.sha256,
                    bytes=exp.bytes,
                    triangles=exp.triangles,
                    storage_status=exp.storage_status,
                    registration=pin.registration,
                    transform=pin.transform,
                    license=rev.provenance.license,
                    subject=rev.provenance.subject,
                    limits=pin.limits or rev.provenance.limits,
                    parts=selected_parts,
                )
            )
        gaps = tuple(
            OpenGap(
                requirement_id=r.id,
                description=r.description,
                status=r.status,
                concepts=r.concepts,
            )
            for r in consumer.requirements
            if r.status in {"open-gap", "rebuild-required"}
        )
        return RuntimeBundle(
            consumer_id=consumer.id,
            title=consumer.title,
            items=tuple(items),
            total_bytes=total_bytes,
            total_triangles=total_tris,
            open_gaps=gaps,
        )

    def open_gaps(self, prefix: str | None = None) -> list[OpenGap]:
        gaps: list[OpenGap] = []
        for consumer in self.consumers:
            if prefix and not consumer.id.startswith(prefix):
                continue
            for req in consumer.requirements:
                if req.status in {"open-gap", "rebuild-required"}:
                    gaps.append(
                        OpenGap(
                            consumer_id=consumer.id,
                            consumer_title=consumer.title,
                            requirement_id=req.id,
                            status=req.status,
                            description=req.description,
                            concepts=req.concepts,
                            parts=req.parts,
                            subject=req.subject,
                        )
                    )
        return gaps

    def economy(self, registry: AssetRegistry, policy: BudgetPolicy | None = None) -> EconomyReport:
        policy = policy or BudgetPolicy()
        asset_reuse: dict[str, set[str]] = {a.id: set() for a in registry.assets}
        export_reuse: dict[str, set[str]] = {
            f"{a.id}@{r.id}:{e.id}": set() for a, r, e in registry.iter_exports()
        }
        metrics: list[UseCaseMetrics] = []
        recs: list[Recommendation] = []

        for asset, rev, exp in registry.iter_exports():
            if exp.role == "editable-master":
                continue
            key = f"{asset.id}@{rev.id}:{exp.id}"
            if exp.bytes is not None:
                if exp.bytes > policy.export_bytes_hard:
                    recs.append(
                        Recommendation(
                            action="split-export",
                            target=key,
                            severity="hard",
                            reason=f"Export exceeds hard byte cap ({exp.bytes} > {policy.export_bytes_hard})",
                            metrics={"bytes": exp.bytes, "hardCap": policy.export_bytes_hard},
                        )
                    )
                elif exp.bytes > policy.export_bytes_soft:
                    recs.append(
                        Recommendation(
                            action="split-export",
                            target=key,
                            severity="warn",
                            reason=f"Export exceeds soft byte cap ({exp.bytes} > {policy.export_bytes_soft})",
                            metrics={"bytes": exp.bytes, "softCap": policy.export_bytes_soft},
                        )
                    )
            if exp.triangles is not None:
                if exp.triangles > policy.export_tris_hard:
                    recs.append(
                        Recommendation(
                            action="over-budget",
                            target=key,
                            severity="hard",
                            reason=f"Export exceeds hard triangle cap ({exp.triangles} > {policy.export_tris_hard})",
                            metrics={
                                "triangles": exp.triangles,
                                "hardCap": policy.export_tris_hard,
                            },
                        )
                    )
                elif exp.triangles > policy.export_tris_soft:
                    recs.append(
                        Recommendation(
                            action="over-budget",
                            target=key,
                            severity="warn",
                            reason=f"Export exceeds soft triangle cap ({exp.triangles} > {policy.export_tris_soft})",
                            metrics={
                                "triangles": exp.triangles,
                                "softCap": policy.export_tris_soft,
                            },
                        )
                    )

        for consumer in self.consumers:
            loaded_keys: dict[tuple[str, str, str], set[str]] = {}
            whole_exports = set()
            for pin in consumer.pins:
                key = (pin.asset_id, pin.revision_id, pin.export_id)
                if not pin.parts:
                    whole_exports.add(key)
                loaded_keys.setdefault(key, set()).update(pin.parts)
                asset_reuse.setdefault(pin.asset_id, set()).add(consumer.id)
                export_reuse.setdefault(
                    f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}", set()
                ).add(consumer.id)

            total_bytes = 0
            total_tris = 0
            used_parts_count = 0
            total_parts_count = 0
            used_part_bytes = 0
            complete_weights = True

            for (aid, rid, eid), used_parts in loaded_keys.items():
                resolved = registry.resolve_export(aid, rid, eid)
                if resolved is None:
                    complete_weights = False
                    continue
                _, _, exp = resolved
                if exp.bytes is not None:
                    total_bytes += exp.bytes
                if exp.triangles is not None:
                    total_tris += exp.triangles
                total_parts_count += len(exp.parts)
                if (aid, rid, eid) in whole_exports:
                    used_parts_count += len(exp.parts)
                    used_part_bytes += exp.bytes or 0
                    complete_weights &= exp.bytes is not None
                else:
                    selected = [p for p in exp.parts if p.id in used_parts]
                    used_parts_count += len(selected)
                    complete_weights &= (
                        exp.bytes is not None
                        and len(selected) == len(used_parts)
                        and all(p.bytes is not None for p in selected)
                    )
                    used_part_bytes += sum(p.bytes or 0 for p in selected)

            loads = len(loaded_keys)
            part_util = (
                round(used_parts_count / total_parts_count, 4) if total_parts_count > 0 else None
            )
            byte_util = (
                round(used_part_bytes / total_bytes, 4)
                if complete_weights and total_bytes > 0 and used_part_bytes <= total_bytes
                else None
            )
            open_gaps = sum(
                1 for r in consumer.requirements if r.status in {"open-gap", "rebuild-required"}
            )
            flags: list[str] = []
            if loads > policy.consumer_loads_hard:
                flags.append("loads-over-hard-cap")
                recs.append(
                    Recommendation(
                        action="merge-bundle",
                        target=consumer.id,
                        severity="hard",
                        reason=f"Consumer loads {loads} exports (hard cap {policy.consumer_loads_hard})",
                        metrics={"loads": loads, "hardCap": policy.consumer_loads_hard},
                    )
                )
            elif loads > policy.consumer_loads_soft:
                flags.append("loads-over-soft-cap")
                recs.append(
                    Recommendation(
                        action="merge-bundle",
                        target=consumer.id,
                        severity="warn",
                        reason=f"Consumer loads {loads} exports (soft cap {policy.consumer_loads_soft})",
                        metrics={"loads": loads, "softCap": policy.consumer_loads_soft},
                    )
                )
            if total_bytes > policy.consumer_bytes_hard:
                flags.append("bytes-over-hard-cap")
                recs.append(
                    Recommendation(
                        action="over-budget",
                        target=consumer.id,
                        severity="hard",
                        reason=f"Consumer loads {total_bytes} bytes (hard cap {policy.consumer_bytes_hard})",
                        metrics={"bytes": total_bytes, "hardCap": policy.consumer_bytes_hard},
                    )
                )
            elif total_bytes > policy.consumer_bytes_soft:
                flags.append("bytes-over-soft-cap")
            if (
                part_util is not None
                and total_parts_count > 1
                and part_util < policy.min_utilization
            ):
                flags.append("low-part-utilization")
                recs.append(
                    Recommendation(
                        action="split-export",
                        target=consumer.id,
                        severity="warn",
                        reason=(
                            f"Consumer uses only {part_util:.0%} of loaded parts "
                            f"({used_parts_count}/{total_parts_count}); consider a lighter base export + overlay"
                        ),
                        metrics={
                            "partUtilization": part_util,
                            "usedParts": used_parts_count,
                            "totalParts": total_parts_count,
                        },
                    )
                )
            if byte_util is not None and byte_util < policy.min_utilization:
                flags.append("low-byte-utilization")

            metrics.append(
                UseCaseMetrics(
                    consumer_id=consumer.id,
                    title=consumer.title,
                    loads=loads,
                    total_bytes=total_bytes,
                    total_triangles=total_tris,
                    part_utilization=part_util,
                    byte_utilization=byte_util,
                    open_gaps=open_gaps,
                    budget_flags=tuple(flags),
                )
            )

        return EconomyReport(
            policy=policy,
            consumer_metrics=tuple(metrics),
            asset_reuse={k: len(v) for k, v in asset_reuse.items()},
            export_reuse={k: len(v) for k, v in export_reuse.items()},
            recommendations=tuple(recs),
        )

    def impact(self, target: str, registry: AssetRegistry, curation: CurationStore) -> ImpactResult:
        matched_assets, matched_paths = registry.match_target(target)
        if not matched_assets and not matched_paths:
            return ImpactResult(target=target, found=False, status="unknown-target")

        whole_assets = {a.id for a in registry.assets if target in {a.id, a.owner_dir}}
        export_keys = {
            (asset.id, rev.id, exp.id)
            for asset, rev, exp in registry.iter_exports()
            if target == exp.path or target == f"{asset.id}@{rev.id}:{exp.id}"
        }
        affected_consumers = []
        for consumer in self.consumers:
            pins = tuple(
                pin
                for pin in consumer.pins
                if pin.asset_id in whole_assets
                or (pin.asset_id, pin.revision_id, pin.export_id) in export_keys
            )
            if pins:
                affected_consumers.append(
                    AffectedConsumer(
                        consumer_id=consumer.id,
                        title=consumer.title,
                        kind=consumer.kind,
                        pins=pins,
                        owner_path=consumer.owner_path,
                    )
                )
        return ImpactResult(
            target=target,
            found=True,
            status="ok",
            matched_assets=tuple(sorted(matched_assets)),
            matched_export_paths=tuple(sorted(matched_paths)),
            consumers=tuple(affected_consumers),
            adoptions=curation.adoptions_for(matched_paths, whole_assets),
            reviews=curation.reviews_for(matched_paths, whole_assets),
            qualifications=curation.qualifications_for(matched_paths, whole_assets),
            selections=curation.selections_for(matched_paths, whole_assets),
        )

    def resolve(
        self,
        consumer_id: str,
        registry: AssetRegistry,
        vocab: ConceptGraph,
        curation: CurationStore,
        requirement_id: str | None = None,
    ) -> ResolveResult:
        consumer = self.get(consumer_id)
        if consumer is None:
            raise AssetKitError(f"Unknown consumer: {consumer_id}")
        reqs = (
            [r for r in consumer.requirements if r.id == requirement_id]
            if requirement_id is not None
            else list(consumer.requirements)
        )
        if requirement_id is not None and not reqs:
            raise AssetKitError(f"Unknown requirement '{requirement_id}' on '{consumer_id}'")

        results: list[RequirementResolution] = []
        for req in reqs:
            expanded = vocab.expand(req.concepts)
            exact_candidates: list[ResolveCandidate] = []
            concept_candidates: list[ResolveCandidate] = []
            foreign_subject: list[ResolveCandidate] = []

            for asset, rev, exp in registry.iter_exports():
                if req.variant and exp.variant != req.variant:
                    continue
                exp_qual = curation.qualification_for(
                    exp.path,
                    exp.sha256,
                    asset_id=asset.id,
                    revision_id=rev.id,
                    consumer_id=consumer.id,
                    task_id=req.id,
                )
                for part in exp.parts:
                    prov = part.provenance or rev.provenance
                    tokens = {part.id, *part.selectors}
                    selector_hit = bool(req.parts and (set(req.parts) & tokens))
                    concept_hit = bool(expanded and (set(part.concepts) & expanded))
                    if not selector_hit and not concept_hit:
                        continue
                    part_qual = curation.qualification_for(
                        exp.path,
                        exp.sha256,
                        part_id=part.id,
                        consumer_id=consumer.id,
                        task_id=req.id,
                        asset_id=asset.id,
                        revision_id=rev.id,
                    )
                    if req.subject and prov.subject and prov.subject != req.subject:
                        foreign_subject.append(
                            ResolveCandidate(
                                asset_id=asset.id,
                                revision_id=rev.id,
                                export_id=exp.id,
                                export_path=exp.path,
                                part_id=part.id,
                                label=part.label,
                                variant=exp.variant,
                                subject=prov.subject,
                                registration=prov.registration,
                                review_statuses=part_qual.statuses,
                                qualification_decisions=part_qual.qualification_decisions,
                                adoption_statuses=part_qual.adoption_statuses,
                                qualified=part_qual.qualified,
                                note=(
                                    f"Foreign subject '{prov.subject}' != required '{req.subject}'; "
                                    "requires explicit registration/illustrative pin if reused."
                                ),
                            )
                        )
                    elif selector_hit and (not req.subject or prov.subject == req.subject):
                        exact_candidates.append(
                            ResolveCandidate(
                                asset_id=asset.id,
                                revision_id=rev.id,
                                export_id=exp.id,
                                export_path=exp.path,
                                part_id=part.id,
                                label=part.label,
                                variant=exp.variant,
                                subject=prov.subject,
                                registration=prov.registration,
                                review_statuses=part_qual.statuses,
                                qualification_decisions=part_qual.qualification_decisions,
                                adoption_statuses=part_qual.adoption_statuses,
                                qualified=part_qual.qualified,
                                match_basis="exact-selector",
                            )
                        )
                    else:
                        concept_candidates.append(
                            ResolveCandidate(
                                asset_id=asset.id,
                                revision_id=rev.id,
                                export_id=exp.id,
                                export_path=exp.path,
                                part_id=part.id,
                                label=part.label,
                                variant=exp.variant,
                                subject=prov.subject,
                                registration=prov.registration,
                                review_statuses=part_qual.statuses,
                                qualification_decisions=part_qual.qualification_decisions,
                                adoption_statuses=part_qual.adoption_statuses,
                                qualified=part_qual.qualified,
                                match_basis=(
                                    "concept-hierarchy"
                                    if concept_hit
                                    else "selector-unverified-subject"
                                ),
                            )
                        )

                if expanded and (set(asset.concepts) & expanded):
                    prov = rev.provenance
                    is_foreign = bool(req.subject and prov.subject and prov.subject != req.subject)
                    cand = ResolveCandidate(
                        asset_id=asset.id,
                        revision_id=rev.id,
                        export_id=exp.id,
                        export_path=exp.path,
                        part_id=None,
                        label=asset.title,
                        variant=exp.variant,
                        subject=prov.subject,
                        registration=prov.registration,
                        review_statuses=exp_qual.statuses,
                        qualification_decisions=exp_qual.qualification_decisions,
                        adoption_statuses=exp_qual.adoption_statuses,
                        qualified=exp_qual.qualified,
                        match_basis="asset-concept",
                        note=(
                            f"Foreign subject '{prov.subject}' != required '{req.subject}'."
                            if is_foreign
                            else None
                        ),
                    )
                    if is_foreign:
                        foreign_subject.append(cand)
                    else:
                        concept_candidates.append(cand)

            status: Literal[
                "exact-candidate", "concept-candidate", "foreign-subject-only", "unmatched"
            ] = (
                "exact-candidate"
                if exact_candidates
                else "concept-candidate"
                if concept_candidates
                else "foreign-subject-only"
                if foreign_subject
                else "unmatched"
            )
            results.append(
                RequirementResolution(
                    requirement_id=req.id,
                    status=status,
                    exact_candidates=tuple(exact_candidates),
                    concept_candidates=tuple(concept_candidates),
                    foreign_subject_candidates=tuple(foreign_subject),
                )
            )
        return ResolveResult(consumer_id=consumer.id, requirements=tuple(results))

    def counts(self) -> dict[str, int]:
        return {
            "consumers": len(self.consumers),
            "requirements": sum(len(c.requirements) for c in self.consumers),
            "openGaps": sum(
                1
                for c in self.consumers
                for r in c.requirements
                if r.status in {"open-gap", "rebuild-required"}
            ),
            "pins": sum(len(c.pins) for c in self.consumers),
        }

    def to_dict(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.consumers]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetKitError(f"Invalid JSON in {path}: {exc}") from exc


def _load_native_consumers(repo: Path) -> list[Consumer]:
    consumers: list[Consumer] = []
    for manifest in manifests(repo, "consumer.json"):
        owner_path = manifest.resolve().relative_to(repo).as_posix()
        doc = _read_json(manifest)
        for row in doc.get("consumers", []):
            reqs = tuple(
                Requirement(
                    id=r["id"],
                    description=r.get("description", r["id"]),
                    status=r.get("status", "open-gap"),
                    concepts=tuple(r.get("concepts", (r["concept"],) if r.get("concept") else ())),
                    parts=tuple(r.get("parts", ())),
                    variant=r.get("variant"),
                    subject=r.get("subject"),
                    capabilities=tuple(r.get("capabilities", ())),
                )
                for r in row.get("requirements", [])
            )
            pins = tuple(
                Pin(
                    asset_id=p["asset"],
                    revision_id=p["revision"],
                    export_id=p["export"],
                    requirement_id=p.get("requirement"),
                    parts=tuple(p.get("parts", ())),
                    sha256=p.get("sha256"),
                    registration=p.get("registration", "unknown"),
                    transform=tuple(float(v) for v in p["transform"])
                    if p.get("transform") is not None
                    else None,
                    limits=tuple(p.get("limits", ())),
                )
                for p in row.get("pins", [])
            )
            consumers.append(
                Consumer(
                    id=row["id"],
                    title=row.get("title", row["id"]),
                    kind=row.get("kind", "other"),
                    owner_path=owner_path,
                    requirements=reqs,
                    pins=pins,
                    local_files=tuple(row.get("localFiles", ())),
                )
            )
    return consumers


def _project_legacy_consumers(repo: Path, existing_ids: set[str]) -> list[Consumer]:
    consumers: list[Consumer] = []
    stops_path = repo / "lessons/body-systems/reviewed-stops.json"
    if stops_path.is_file():
        doc = _read_json(stops_path)
        owner = stops_path.resolve().relative_to(repo).as_posix()
        for row in doc.get("stops", []):
            cid = f"body-systems:{row['system']}:{row['detail']}"
            if cid in existing_ids:
                continue
            existing_ids.add(cid)
            consumers.append(
                Consumer(
                    id=cid,
                    title=f"{str(row['system']).title()} · {row['detail']}",
                    kind="lesson-stop",
                    owner_path=owner,
                    requirements=(
                        Requirement(
                            id=row["detail"],
                            description=row["action"],
                            status="satisfied" if row.get("status") == "passed" else "provisional",
                        ),
                    ),
                )
            )

    consumers.extend(_load_ultrasound_sweep_consumers(repo, existing_ids, pinned_only=False))
    return consumers


def _load_ultrasound_sweep_consumers(
    repo: Path, existing_ids: set[str], *, pinned_only: bool
) -> list[Consumer]:
    consumers: list[Consumer] = []
    us_dir = repo / "experiments/ultrasound-sweep"
    if not us_dir.is_dir():
        return consumers
    for track_file in sorted(us_dir.glob("*-track*.json")):
        doc = _read_json(track_file)
        common = doc.get("common", {})
        owner = track_file.resolve().relative_to(repo).as_posix()
        for sweep in doc.get("sweeps", []):
            if not isinstance(sweep, dict) or not sweep.get("id"):
                continue
            scene_assets = sweep.get("sceneAssets", {})
            if pinned_only and not scene_assets:
                continue
            cid = f"ultrasound:sweep:{track_file.stem}:{sweep['id']}"
            if cid in existing_ids:
                continue
            existing_ids.add(cid)
            case = sweep.get("case", common.get("case"))
            parts = tuple(
                p for p in sweep.get("parts", common.get("parts", [])) if isinstance(p, str)
            )
            reqs = tuple(
                Requirement(
                    id=f"part:{p}",
                    description=f"Ultrasound sweep anatomy part '{p}'",
                    status="provisional",
                    parts=(p,),
                    subject=case,
                )
                for p in parts
            )
            pins = tuple(
                Pin(
                    asset_id=ref.asset,
                    revision_id=ref.revision,
                    export_id=ref.export,
                    requirement_id=f"part:{part}",
                )
                for part, raw in scene_assets.items()
                for ref in (ExportRef.model_validate(raw),)
            )
            consumers.append(
                Consumer(
                    id=cid,
                    title=sweep.get("title", sweep["id"]),
                    kind="ultrasound-sweep",
                    owner_path=owner,
                    requirements=reqs,
                    pins=pins,
                )
            )
    return consumers
